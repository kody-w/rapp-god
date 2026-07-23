import * as THREE from '../../vendor/three.module.js';

import { clamp, normalizeLocation, offsetLocation } from '../lib/geo.js';
import { animateCreatureModel, createCreatureModel } from './creature-renderer.js';

const TILE_SIZE = 256;
const MAX_LATITUDE = 85.05112878;
const METERS_PER_LATITUDE_DEGREE = 110_540;

function mercator(location, zoom) {
  const scale = TILE_SIZE * 2 ** zoom;
  const latitude = clamp(location.lat, -MAX_LATITUDE, MAX_LATITUDE) * Math.PI / 180;
  return {
    x: (location.lng + 180) / 360 * scale,
    y: (1 - Math.log(Math.tan(latitude) + 1 / Math.cos(latitude)) / Math.PI) / 2 * scale
  };
}

function localMeters(location, center) {
  return {
    east: (location.lng - center.lng) * 111_320 * Math.cos(center.lat * Math.PI / 180),
    north: (location.lat - center.lat) * METERS_PER_LATITUDE_DEGREE
  };
}

function disposeObject(root, { textures = false } = {}) {
  root.traverse((object) => {
    object.geometry?.dispose?.();
    const materials = Array.isArray(object.material) ? object.material : object.material ? [object.material] : [];
    for (const material of materials) {
      if (textures) material.map?.dispose?.();
      material.dispose?.();
    }
  });
}

function colorForPlace(kind) {
  return { water: 0x48a9c5, nature: 0x4f9c69, landmark: 0x9b78c6, civic: 0x527da8, rest: 0x79858d }[kind] || 0x79858d;
}

function placeTotem(place) {
  const group = new THREE.Group();
  const color = colorForPlace(place.kind);
  const material = new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.08, emissive: color, emissiveIntensity: 0.045 });
  const pale = new THREE.MeshStandardMaterial({ color: 0xf4fbf7, roughness: 0.72 });
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.28, 0.12, 18), pale);
  base.position.y = 0.06;
  group.add(base);
  let symbol;
  if (place.kind === 'water') {
    symbol = new THREE.Mesh(new THREE.TorusGeometry(0.19, 0.055, 8, 20), material);
    symbol.rotation.x = Math.PI / 2;
  } else if (place.kind === 'nature') {
    symbol = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.54, 7), material);
  } else if (place.kind === 'landmark') {
    symbol = new THREE.Mesh(new THREE.OctahedronGeometry(0.23, 1), material);
  } else if (place.kind === 'civic') {
    symbol = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.38, 0.32), material);
  } else {
    symbol = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.2, 0.34, 10), material);
  }
  symbol.position.y = place.kind === 'nature' ? 0.42 : 0.34;
  group.add(symbol);
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.31, 0.36, 32),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.72, side: THREE.DoubleSide })
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.012;
  group.add(ring);
  group.userData.ring = ring;
  return group;
}

function playerMarker() {
  const group = new THREE.Group();
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(0.22, 0.31, 36),
    new THREE.MeshBasicMaterial({ color: 0x4b86ff, transparent: true, opacity: 0.68, side: THREE.DoubleSide })
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.022;
  const core = new THREE.Mesh(
    new THREE.SphereGeometry(0.13, 18, 12),
    new THREE.MeshStandardMaterial({ color: 0x4b86ff, emissive: 0x4b86ff, emissiveIntensity: 0.16, roughness: 0.3 })
  );
  core.position.y = 0.16;
  group.add(ring, core);
  group.userData.ring = ring;
  group.userData.core = core;
  return group;
}

export class CanvasMap {
  constructor(canvas, { center, zoom = 16.4, theme = 'light', onMarker = null } = {}) {
    this.canvas = canvas;
    this.center = normalizeLocation(center || { lat: 40.7128, lng: -74.006 });
    this.home = this.center;
    this.location = null;
    this.zoom = zoom;
    this.theme = theme;
    this.onMarker = onMarker;
    this.markers = [];
    this.markerObjects = new Map();
    this.pointers = new Map();
    this.gesture = null;
    this.sceneScale = 0.022;
    this.frame = null;
    this.tileMeshes = [];

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.03;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 120);
    this.raycaster = new THREE.Raycaster();
    this.pointerVector = new THREE.Vector2();
    this.groundGroup = new THREE.Group();
    this.markerGroup = new THREE.Group();
    this.scene.add(this.groundGroup, this.markerGroup);

    const hemisphere = new THREE.HemisphereLight(0xf2fff8, 0x43565f, 2.25);
    const sun = new THREE.DirectionalLight(0xfff3d7, 3.15);
    sun.position.set(-6, 10, 8);
    this.scene.add(hemisphere, sun);
    this.playerObject = playerMarker();
    this.scene.add(this.playerObject);

    this.textureLoader = new THREE.TextureLoader();
    this.textureLoader.setCrossOrigin('anonymous');
    this.resizeObserver = typeof ResizeObserver === 'function' ? new ResizeObserver(() => this.resize()) : null;
    this.resizeObserver?.observe(canvas);
    globalThis.addEventListener?.('resize', () => this.resize());
    this.bindEvents();
    this.setTheme(theme);
    this.resize();
    this.refreshGround();
    this.start();
  }

  worldScale() {
    return 0.022 * 2 ** (this.zoom - 16.4);
  }

  tileUrl(zoom, x, y) {
    const style = this.theme === 'dark' ? 'dark_all' : 'light_all';
    const subdomain = ['a', 'b', 'c', 'd'][Math.abs(x + y) % 4];
    return `https://${subdomain}.basemaps.cartocdn.com/${style}/${zoom}/${x}/${y}.png`;
  }

  setTheme(theme) {
    this.theme = theme === 'dark' ? 'dark' : 'light';
    const background = this.theme === 'dark' ? 0x101a20 : 0xdce8df;
    this.scene.background = new THREE.Color(background);
    this.scene.fog = new THREE.Fog(background, 12, 32);
    if (this.groundGroup) this.refreshGround();
  }

  refreshGround() {
    for (const mesh of this.tileMeshes) {
      this.groundGroup.remove(mesh);
      disposeObject(mesh, { textures: true });
    }
    this.tileMeshes = [];
    const zoom = Math.floor(clamp(this.zoom, 14, 18));
    this.tileZoom = zoom;
    const centerWorld = mercator(this.center, zoom);
    const centerTileX = centerWorld.x / TILE_SIZE;
    const centerTileY = centerWorld.y / TILE_SIZE;
    const baseX = Math.floor(centerTileX);
    const baseY = Math.floor(centerTileY);
    const tileCount = 2 ** zoom;
    const metersPerTile = 40_075_016.686 * Math.cos(this.center.lat * Math.PI / 180) / tileCount;
    const tileWorldSize = metersPerTile * this.worldScale();

    const underlay = new THREE.Mesh(
      new THREE.PlaneGeometry(tileWorldSize * 7, tileWorldSize * 7),
      new THREE.MeshStandardMaterial({ color: this.theme === 'dark' ? 0x18252a : 0xd9e5dc, roughness: 1 })
    );
    underlay.rotation.x = -Math.PI / 2;
    underlay.position.y = -0.035;
    this.groundGroup.add(underlay);
    this.tileMeshes.push(underlay);

    for (let offsetX = -2; offsetX <= 2; offsetX += 1) for (let offsetY = -2; offsetY <= 2; offsetY += 1) {
      const tileX = baseX + offsetX;
      const tileY = baseY + offsetY;
      if (tileY < 0 || tileY >= tileCount) continue;
      const wrappedX = ((tileX % tileCount) + tileCount) % tileCount;
      const mapMaterial = new THREE.MeshBasicMaterial({ color: this.theme === 'dark' ? 0x26343a : 0xf0f5ef });
      const mesh = new THREE.Mesh(new THREE.PlaneGeometry(tileWorldSize * 1.006, tileWorldSize * 1.006), mapMaterial);
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.set(
        (tileX + 0.5 - centerTileX) * tileWorldSize,
        0,
        (tileY + 0.5 - centerTileY) * tileWorldSize
      );
      mesh.userData.tile = { x: tileX, y: tileY, zoom, metersPerTile };
      this.groundGroup.add(mesh);
      this.tileMeshes.push(mesh);
      this.textureLoader.load(
        this.tileUrl(zoom, wrappedX, tileY),
        (texture) => {
          texture.colorSpace = THREE.SRGBColorSpace;
          texture.anisotropy = Math.min(4, this.renderer.capabilities.getMaxAnisotropy());
          mapMaterial.map = texture;
          mapMaterial.color.setHex(0xffffff);
          mapMaterial.needsUpdate = true;
        },
        undefined,
        () => {}
      );
    }
  }

  updateGroundPositions() {
    if (!this.tileZoom) return;
    const centerWorld = mercator(this.center, this.tileZoom);
    const centerTileX = centerWorld.x / TILE_SIZE;
    const centerTileY = centerWorld.y / TILE_SIZE;
    const tileCount = 2 ** this.tileZoom;
    const metersPerTile = 40_075_016.686 * Math.cos(this.center.lat * Math.PI / 180) / tileCount;
    const tileWorldSize = metersPerTile * this.worldScale();
    for (const mesh of this.tileMeshes) {
      if (!mesh.userData.tile) {
        mesh.scale.setScalar(tileWorldSize / Math.max(0.001, mesh.geometry.parameters.width / 7));
        continue;
      }
      mesh.position.x = (mesh.userData.tile.x + 0.5 - centerTileX) * tileWorldSize;
      mesh.position.z = (mesh.userData.tile.y + 0.5 - centerTileY) * tileWorldSize;
    }
  }

  bindEvents() {
    this.canvas.style.touchAction = 'none';
    this.canvas.addEventListener('pointerdown', (event) => {
      this.canvas.setPointerCapture(event.pointerId);
      this.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY, startX: event.clientX, startY: event.clientY });
      this.beginGesture();
    });
    this.canvas.addEventListener('pointermove', (event) => {
      const pointer = this.pointers.get(event.pointerId);
      if (!pointer) return;
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      this.updateGesture();
    });
    const end = (event) => {
      const pointer = this.pointers.get(event.pointerId);
      const wasTap = pointer && Math.hypot(pointer.x - pointer.startX, pointer.y - pointer.startY) < 8 && this.pointers.size === 1;
      this.pointers.delete(event.pointerId);
      if (wasTap) this.hitTest(event.clientX, event.clientY);
      if (!this.pointers.size) this.refreshGround();
      this.beginGesture();
    };
    this.canvas.addEventListener('pointerup', end);
    this.canvas.addEventListener('pointercancel', end);
    this.canvas.addEventListener('wheel', (event) => {
      event.preventDefault();
      this.zoomBy(event.deltaY > 0 ? -0.35 : 0.35);
    }, { passive: false });
    this.canvas.addEventListener('dblclick', (event) => {
      event.preventDefault();
      this.zoomBy(0.65);
    });
  }

  beginGesture() {
    const pointers = [...this.pointers.values()];
    if (!pointers.length) {
      this.gesture = null;
      return;
    }
    if (pointers.length === 1) {
      this.gesture = { type: 'pan', x: pointers[0].x, y: pointers[0].y, center: { ...this.center } };
    } else {
      this.gesture = {
        type: 'pinch',
        distance: Math.hypot(pointers[0].x - pointers[1].x, pointers[0].y - pointers[1].y),
        zoom: this.zoom
      };
    }
  }

  updateGesture() {
    if (!this.gesture) return;
    const pointers = [...this.pointers.values()];
    if (this.gesture.type === 'pan' && pointers.length === 1) {
      const eastMeters = -(pointers[0].x - this.gesture.x) / this.worldScale() * 0.78;
      const northMeters = (pointers[0].y - this.gesture.y) / this.worldScale() * 0.7;
      this.center = offsetLocation(this.gesture.center, eastMeters, northMeters);
      this.updateMarkerPositions();
      this.updateGroundPositions();
    } else if (this.gesture.type === 'pinch' && pointers.length >= 2) {
      const distance = Math.max(20, Math.hypot(pointers[0].x - pointers[1].x, pointers[0].y - pointers[1].y));
      this.zoom = clamp(this.gesture.zoom + Math.log2(distance / Math.max(20, this.gesture.distance)), 14.2, 18.6);
      this.updateMarkerPositions();
      this.updateGroundPositions();
    }
  }

  hitTest(clientX, clientY) {
    const bounds = this.canvas.getBoundingClientRect();
    this.pointerVector.x = (clientX - bounds.left) / bounds.width * 2 - 1;
    this.pointerVector.y = -(clientY - bounds.top) / bounds.height * 2 + 1;
    this.raycaster.setFromCamera(this.pointerVector, this.camera);
    const intersections = this.raycaster.intersectObjects([...this.markerObjects.values()], true);
    for (const intersection of intersections) {
      let object = intersection.object;
      while (object && !object.userData.marker) object = object.parent;
      if (object?.userData.marker) {
        this.onMarker?.(object.userData.marker);
        return;
      }
    }
  }

  resize() {
    const bounds = this.canvas.getBoundingClientRect();
    const width = Math.max(1, bounds.width);
    const height = Math.max(1, bounds.height);
    this.renderer.setPixelRatio(Math.min(2, globalThis.devicePixelRatio || 1));
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  setCenter(center, { remember = false } = {}) {
    this.center = normalizeLocation(center);
    if (remember) this.home = this.center;
    this.updateMarkerPositions();
    this.refreshGround();
  }

  setLocation(location) {
    this.location = { ...normalizeLocation(location), accuracy: location.accuracy };
    this.setCenter(location, { remember: true });
  }

  setMarkers(markers) {
    for (const object of this.markerObjects.values()) {
      this.markerGroup.remove(object);
      disposeObject(object);
    }
    this.markerObjects.clear();
    this.markers = markers;
    for (const marker of markers) {
      let object;
      if (marker.type === 'creature') {
        object = createCreatureModel(marker.creature);
        object.scale.multiplyScalar(0.42);
        object.updateMatrixWorld(true);
        const bounds = new THREE.Box3().setFromObject(object);
        object.userData.groundOffset = -bounds.min.y + 0.06;
        object.userData.creature = marker.creature;
      } else {
        object = placeTotem(marker.place);
        object.userData.groundOffset = 0;
      }
      object.userData.marker = marker;
      object.userData.phase = marker.phase || 0;
      this.markerGroup.add(object);
      this.markerObjects.set(marker.id, object);
    }
    this.updateMarkerPositions();
  }

  updateMarkerPositions() {
    const scale = this.worldScale();
    for (const marker of this.markers) {
      const object = this.markerObjects.get(marker.id);
      if (!object) continue;
      const meters = localMeters(marker, this.center);
      object.position.x = meters.east * scale;
      object.position.z = -meters.north * scale;
      object.position.y = object.userData.groundOffset || 0;
    }
    if (this.location) {
      const meters = localMeters(this.location, this.center);
      this.playerObject.position.set(meters.east * scale, 0.02, -meters.north * scale);
    }
  }

  recenter() {
    this.center = this.location || this.home;
    this.zoom = Math.max(this.zoom, 16.2);
    this.updateMarkerPositions();
    this.refreshGround();
  }

  zoomBy(amount) {
    const before = Math.floor(this.zoom);
    this.zoom = clamp(this.zoom + amount, 14.2, 18.6);
    this.updateMarkerPositions();
    if (Math.floor(this.zoom) !== before) this.refreshGround();
    else this.updateGroundPositions();
  }

  updateCamera() {
    const distance = 8.6 * 2 ** ((16.4 - this.zoom) * 0.34);
    this.camera.position.set(0, distance * 0.58, distance);
    this.camera.lookAt(0, 0.08, -distance * 0.18);
    this.camera.updateProjectionMatrix();
  }

  render = (time) => {
    const obscured = document.hidden || this.canvas.offsetParent === null || Boolean(document.querySelector('dialog[open]'));
    const frameInterval = obscured ? 90 : 32;
    if (this.lastRenderTime != null && time - this.lastRenderTime < frameInterval) {
      this.frame = requestAnimationFrame(this.render);
      return;
    }
    this.lastRenderTime = time;
    this.updateCamera();
    for (const [id, object] of this.markerObjects) {
      const marker = object.userData.marker;
      if (marker.type === 'creature') {
        animateCreatureModel(object, marker.creature, time + object.userData.phase * 700);
      } else if (object.userData.ring) {
        const pulse = 1 + Math.sin(time * 0.002 + object.userData.phase) * 0.08;
        object.userData.ring.scale.setScalar(pulse);
        object.rotation.y = Math.sin(time * 0.0004 + object.userData.phase) * 0.08;
      }
      object.visible = object.position.length() < 40;
      this.markerObjects.set(id, object);
    }
    const playerPulse = 1 + Math.sin(time * 0.0022) * 0.08;
    this.playerObject.userData.ring.scale.setScalar(playerPulse);
    this.renderer.render(this.scene, this.camera);
    this.frame = requestAnimationFrame(this.render);
  };

  start() {
    if (this.frame == null) this.frame = requestAnimationFrame(this.render);
  }

  destroy() {
    if (this.frame != null) cancelAnimationFrame(this.frame);
    this.frame = null;
    this.resizeObserver?.disconnect();
    disposeObject(this.scene, { textures: true });
    this.renderer.dispose();
  }
}
