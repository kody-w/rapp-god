import * as THREE from '../../vendor/three.module.js';

const TAU = Math.PI * 2;
const UP = new THREE.Vector3(0, 1, 0);
let snapshotRenderer = null;
let snapshotCanvas = null;

function traitsOf(creature) {
  return {
    form: creature.genome.form || {},
    surface: creature.genome.surface || {},
    motion: creature.genome.motion || {}
  };
}

function material(color, options = {}) {
  return new THREE.MeshStandardMaterial({
    color: new THREE.Color(color),
    roughness: options.roughness ?? 0.56,
    metalness: options.metalness ?? 0.035,
    flatShading: options.flatShading ?? true,
    emissive: new THREE.Color(options.emissive || color),
    emissiveIntensity: options.emissiveIntensity ?? 0.025,
    transparent: options.transparent ?? false,
    opacity: options.opacity ?? 1,
    side: options.side ?? THREE.FrontSide
  });
}

function makeMesh(geometry, meshMaterial, options = {}) {
  const value = new THREE.Mesh(geometry, meshMaterial);
  if (options.position) value.position.set(...options.position);
  if (options.rotation) value.rotation.set(...options.rotation);
  if (options.scale) value.scale.set(...options.scale);
  return value;
}

function profileScale(profile, roundness = 0.72) {
  const profiles = {
    round: [1, roundness, 0.88],
    long: [1.28, roundness * 0.72, 0.7],
    pear: [0.9, roundness * 1.16, 0.82],
    diamond: [0.92, roundness * 0.92, 0.9],
    stacked: [0.76, roundness * 1.28, 0.74]
  };
  return profiles[profile] || profiles.round;
}

function partsFor(root) {
  root.userData.parts = {
    body: [], legs: [], arms: [], wings: [], tails: [], segments: [], petals: [],
    orbiters: [], pupils: [], eyes: [], ears: [], fins: [], antennae: []
  };
  return root.userData.parts;
}

function register(parts, type, value, data = {}) {
  Object.assign(value.userData, data);
  parts[type].push(value);
  return value;
}

function boneBetween(from, to, radius, color, options = {}) {
  const a = new THREE.Vector3(...from);
  const b = new THREE.Vector3(...to);
  const direction = b.clone().sub(a);
  const length = direction.length();
  const value = makeMesh(
    new THREE.CylinderGeometry(radius * (options.tipScale ?? 0.68), radius, length, options.sides || 7),
    material(color, { roughness: options.roughness ?? 0.62 })
  );
  value.position.copy(a.add(b).multiplyScalar(0.5));
  value.quaternion.setFromUnitVectors(UP, direction.normalize());
  return value;
}

function makeHead(form, palette, size = 0.5) {
  const head = new THREE.Group();
  let geometry;
  if (form.headStyle === 'wedge') geometry = new THREE.ConeGeometry(size * 0.74, size * 1.18, 5);
  else if (form.headStyle === 'mask') geometry = new THREE.DodecahedronGeometry(size * 0.72, 1);
  else if (form.headStyle === 'bud') geometry = new THREE.OctahedronGeometry(size * 0.72, 2);
  else if (form.headStyle === 'lantern') geometry = new THREE.CylinderGeometry(size * 0.58, size * 0.72, size * 1.05, 7);
  else geometry = new THREE.IcosahedronGeometry(size * 0.72, 2);
  const face = makeMesh(geometry, material(palette[0], { emissiveIntensity: 0.035 }));
  if (form.headStyle === 'wedge') face.rotation.z = -Math.PI / 2;
  face.scale.set(1, form.headStyle === 'mask' ? 0.82 : 1, form.headStyle === 'mask' ? 0.58 : 0.88);
  head.add(face);

  const muzzle = makeMesh(
    new THREE.SphereGeometry(size * 0.28, 14, 9),
    material(palette[2], { flatShading: false, roughness: 0.7, transparent: true, opacity: 0.76 }),
    { position: [0, -size * 0.13, size * 0.5], scale: [1.2, 0.62, 0.55] }
  );
  head.add(muzzle);
  return head;
}

function addEyes(head, form, palette, parts, scale = 1) {
  scale *= Number(form.eyeScale || 1);
  const count = Math.max(1, Math.min(4, Math.round(form.eyes || 2)));
  const positions = count === 1
    ? [[0, 0.1]]
    : count === 2
      ? [[-0.16, 0.09], [0.16, 0.09]]
      : count === 3
        ? [[-0.18, 0.1], [0.18, 0.1], [0, -0.11]]
        : [[-0.17, 0.15], [0.17, 0.15], [-0.17, -0.08], [0.17, -0.08]];
  for (const [x, y] of positions) {
    const eye = new THREE.Group();
    eye.position.set(x * scale, y * scale, 0.48 * scale);
    const white = makeMesh(
      new THREE.SphereGeometry(0.12 * scale, 16, 11),
      material('#fff9e9', { flatShading: false, roughness: 0.25 }),
      { scale: [0.82, 1.04, 0.56] }
    );
    const pupil = makeMesh(
      new THREE.SphereGeometry(0.061 * scale, 12, 8),
      material('#152720', { flatShading: false, roughness: 0.34 }),
      { position: [0, -0.006 * scale, 0.073 * scale], scale: [0.76, 0.9, 0.48] }
    );
    eye.add(white, pupil);
    head.add(eye);
    register(parts, 'eyes', eye, { baseScaleY: 1 });
    register(parts, 'pupils', pupil, { phase: x * 7 + y * 4 });
  }
}

function addEars(head, form, palette, parts, scale = 1) {
  if (!form.earStyle || form.earStyle === 'none') return;
  for (const side of [-1, 1]) {
    let ear;
    if (form.earStyle === 'round') {
      ear = makeMesh(new THREE.SphereGeometry(0.19 * scale, 12, 8), material(palette[1]), {
        position: [side * 0.39 * scale, 0.26 * scale, -0.03], scale: [0.75, 1, 0.48]
      });
    } else if (form.earStyle === 'fin') {
      ear = makeMesh(new THREE.ConeGeometry(0.2 * scale, 0.48 * scale, 3), material(palette[1], { side: THREE.DoubleSide }), {
        position: [side * 0.4 * scale, 0.19 * scale, 0], rotation: [0, 0, -side * 1.1], scale: [0.45, 1, 0.65]
      });
    } else {
      ear = makeMesh(new THREE.ConeGeometry(0.18 * scale, 0.5 * scale, form.earStyle === 'leaf' ? 6 : 4), material(palette[1]), {
        position: [side * 0.31 * scale, 0.4 * scale, -0.03], rotation: [0, 0, -side * 0.25], scale: [form.earStyle === 'leaf' ? 0.62 : 1, 1, 0.56]
      });
    }
    head.add(ear);
    register(parts, 'ears', ear, { side, restZ: ear.rotation.z });
  }
}

function addCrest(head, form, palette, parts, scale = 1) {
  const style = form.crestStyle;
  if (!style || style === 'none') return;
  if (style === 'horns' || style === 'antlers') {
    for (const side of [-1, 1]) {
      const horn = makeMesh(new THREE.ConeGeometry(0.1 * scale, 0.5 * scale, style === 'antlers' ? 5 : 7), material(palette[2], { roughness: 0.38 }), {
        position: [side * 0.22 * scale, 0.46 * scale, -0.05], rotation: [0, 0, -side * 0.2]
      });
      head.add(horn);
      register(parts, 'antennae', horn, { side, restZ: horn.rotation.z });
      if (style === 'antlers') {
        const branch = boneBetween([side * 0.21 * scale, 0.54 * scale, 0], [side * 0.4 * scale, 0.72 * scale, 0], 0.035 * scale, palette[2]);
        head.add(branch);
      }
    }
  } else if (style === 'crystal') {
    for (let index = 0; index < 3; index += 1) {
      head.add(makeMesh(new THREE.ConeGeometry(0.1 * scale, (0.35 + index * 0.08) * scale, 5), material(palette[(index + 1) % 3], { metalness: 0.14 }), {
        position: [(index - 1) * 0.14 * scale, (0.43 + index % 2 * 0.08) * scale, -0.05], rotation: [0, 0, (index - 1) * -0.17]
      }));
    }
  } else if (style === 'petals') {
    for (let index = 0; index < 6; index += 1) {
      const angle = index / 6 * TAU;
      const petal = makeMesh(new THREE.SphereGeometry(0.16 * scale, 12, 7), material(palette[(index + 1) % 3]), {
        position: [Math.cos(angle) * 0.25 * scale, 0.42 * scale + Math.sin(angle) * 0.12 * scale, -0.05],
        rotation: [0, 0, -angle], scale: [0.45, 1.3, 0.35]
      });
      head.add(petal);
      register(parts, 'petals', petal, { phase: angle, restY: petal.position.y });
    }
  } else if (style === 'cap') {
    head.add(makeMesh(new THREE.SphereGeometry(0.42 * scale, 16, 9), material(palette[1]), {
      position: [0, 0.4 * scale, -0.04], scale: [1.15, 0.35, 0.9]
    }));
  }
}

function addSurfaceMarks(parent, surface, palette, radius = 0.72) {
  if (['plain', 'solid'].includes(surface.pattern)) return;
  const amount = surface.pattern === 'constellation' || surface.pattern === 'glow' ? 8 : 5;
  for (let index = 0; index < amount; index += 1) {
    const angle = index / amount * TAU + 0.23;
    parent.add(makeMesh(
      new THREE.SphereGeometry(0.045 + index % 3 * 0.012, 9, 6),
      material(palette[2], { flatShading: false, emissiveIntensity: surface.pattern === 'glow' ? 0.2 : 0.06 }),
      { position: [Math.cos(angle) * radius * 0.55, Math.sin(angle) * radius * 0.4, radius * 0.68] }
    ));
  }
}

function makeLimb(color, length = 0.62, radius = 0.1) {
  return makeMesh(new THREE.CapsuleGeometry(radius, length, 5, 9), material(color, { roughness: 0.7 }));
}

function addTail(root, form, palette, parts, anchor = [0.62, 0, -0.2]) {
  if (!form.tailStyle || form.tailStyle === 'none') return;
  const count = form.tailStyle === 'whip' ? 6 : 4;
  const tailRoot = new THREE.Group();
  tailRoot.position.set(...anchor);
  root.add(tailRoot);
  for (let index = 0; index < count; index += 1) {
    const scale = 1 - index * 0.1;
    const segment = makeMesh(new THREE.IcosahedronGeometry(0.15 * scale, 1), material(index % 2 ? palette[0] : palette[1]), {
      position: [0.2 + index * 0.17, index * 0.035, -index * 0.05]
    });
    tailRoot.add(segment);
    register(parts, 'tails', segment, { phase: index * 0.52, baseY: segment.position.y, baseZ: segment.position.z });
  }
  if (form.tailStyle === 'fan' || form.tailStyle === 'leaf') {
    const end = makeMesh(new THREE.SphereGeometry(0.3, 14, 8), material(palette[2], { side: THREE.DoubleSide }), {
      position: [0.2 + count * 0.17, 0.1, -0.2], scale: [form.tailStyle === 'leaf' ? 0.45 : 0.28, 1, 0.18]
    });
    tailRoot.add(end);
    register(parts, 'tails', end, { phase: 3, baseY: end.position.y, baseZ: end.position.z });
  } else if (form.tailStyle === 'orb') {
    const orb = makeMesh(new THREE.IcosahedronGeometry(0.24, 2), material(palette[2], { emissiveIntensity: 0.18 }), {
      position: [0.2 + count * 0.17, 0.07, -0.2]
    });
    tailRoot.add(orb);
    register(parts, 'tails', orb, { phase: 3, baseY: orb.position.y, baseZ: orb.position.z });
  }
}

function addWings(root, form, palette, parts, anchorY = 0.12, size = 0.82) {
  if (!form.wingStyle || form.wingStyle === 'none') return;
  for (const side of [-1, 1]) {
    const wingGroup = new THREE.Group();
    wingGroup.position.set(side * 0.55, anchorY, -0.12);
    const geometry = form.wingStyle === 'membrane'
      ? new THREE.CircleGeometry(size, 5)
      : new THREE.SphereGeometry(size * 0.72, 16, 9);
    const wing = makeMesh(geometry, material(palette[1], {
      flatShading: form.wingStyle === 'membrane', transparent: true, opacity: form.wingStyle === 'veil' ? 0.62 : 0.82,
      emissiveIntensity: 0.07, side: THREE.DoubleSide
    }), {
      position: [side * size * 0.48, 0, 0],
      rotation: [form.wingStyle === 'membrane' ? -0.2 : 0, side * 0.16, side * 0.18],
      scale: [1.15, form.wingStyle === 'leaf' ? 0.32 : 0.48, form.wingStyle === 'membrane' ? 1 : 0.45]
    });
    wingGroup.add(wing);
    root.add(wingGroup);
    register(parts, 'wings', wingGroup, { side, restZ: wingGroup.rotation.z, restY: wingGroup.rotation.y });
  }
}

function buildQuadruped(root, form, surface, parts, palette) {
  const body = makeMesh(new THREE.IcosahedronGeometry(0.82, 3), material(palette[0]), {
    scale: [1.15, form.roundness * 0.82, 0.72]
  });
  root.add(body); register(parts, 'body', body, { baseScale: body.scale.clone() });
  for (const [index, x] of [-0.43, 0.43].entries()) for (const z of [-0.28, 0.28]) {
    const leg = makeLimb(index % 2 ? palette[1] : palette[0], 0.55 * form.limbScale, 0.095);
    leg.position.set(x, -0.62, z);
    root.add(leg); register(parts, 'legs', leg, { phase: (index + (z > 0 ? 1 : 0)) * Math.PI, restX: leg.rotation.x });
  }
  const head = makeHead(form, palette, 0.68 * form.headRatio);
  head.position.set(0, 0.45, 0.56);
  root.add(head);
  addEyes(head, form, palette, parts, 0.88 * form.headRatio);
  addEars(head, form, palette, parts, form.headRatio);
  addCrest(head, form, palette, parts, form.headRatio);
  addTail(root, form, palette, parts, [0.58, -0.03, -0.24]);
  addSurfaceMarks(body, surface, palette, 0.72);
}

function buildBiped(root, form, surface, parts, palette) {
  const body = makeMesh(new THREE.DodecahedronGeometry(0.68, 2), material(palette[0]), {
    position: [0, 0.05, 0], scale: profileScale(form.bodyProfile, form.roundness)
  });
  root.add(body); register(parts, 'body', body, { baseScale: body.scale.clone() });
  for (const side of [-1, 1]) {
    const leg = makeLimb(palette[1], 0.66 * form.limbScale, 0.11);
    leg.position.set(side * 0.25, -0.7, 0);
    root.add(leg); register(parts, 'legs', leg, { phase: side > 0 ? 0 : Math.PI, restX: 0 });
    const arm = makeLimb(palette[1], 0.48 * form.limbScale, 0.075);
    arm.position.set(side * 0.72, 0.05, 0);
    arm.rotation.z = side * -0.35;
    root.add(arm); register(parts, 'arms', arm, { side, restZ: arm.rotation.z });
  }
  const head = makeHead(form, palette, 0.68 * form.headRatio);
  head.position.set(0, 0.85, 0.08);
  root.add(head);
  addEyes(head, form, palette, parts, 0.88 * form.headRatio);
  addEars(head, form, palette, parts, form.headRatio);
  addCrest(head, form, palette, parts, form.headRatio);
  addTail(root, form, palette, parts, [0.42, -0.02, -0.25]);
  addSurfaceMarks(body, surface, palette, 0.62);
}

function buildSerpent(root, form, surface, parts, palette) {
  const count = Math.max(7, form.segments || 9);
  for (let index = 0; index < count; index += 1) {
    const fraction = index / (count - 1);
    const radius = 0.38 - fraction * 0.18;
    const segment = makeMesh(new THREE.IcosahedronGeometry(radius, 2), material(palette[index % 2 ? 1 : 0]), {
      position: [-0.8 + fraction * 1.45, Math.sin(fraction * Math.PI) * 0.1 - 0.12, -fraction * 0.14],
      scale: [1.2, 0.86, 0.9]
    });
    root.add(segment);
    register(parts, 'segments', segment, { phase: index * 0.48, base: segment.position.clone() });
    if (index === 0) register(parts, 'body', segment, { baseScale: segment.scale.clone() });
  }
  const head = makeHead(form, palette, 0.58 * form.headRatio);
  head.position.set(0.82, 0.13, 0.03);
  root.add(head);
  addEyes(head, form, palette, parts, 0.74 * form.headRatio);
  addCrest(head, form, palette, parts, form.headRatio * 0.8);
  if (form.wingStyle !== 'none') addWings(root, form, palette, parts, 0.1, 0.52);
}

function buildRay(root, form, surface, parts, palette) {
  const body = makeMesh(new THREE.SphereGeometry(0.82, 22, 12), material(palette[0]), {
    scale: [0.95, 0.28, 0.72]
  });
  root.add(body); register(parts, 'body', body, { baseScale: body.scale.clone() });
  form.wingStyle = form.wingStyle === 'none' ? 'veil' : form.wingStyle;
  addWings(root, form, palette, parts, 0, 0.88);
  const head = new THREE.Group();
  head.position.set(0, 0.12, 0.57);
  root.add(head);
  addEyes(head, form, palette, parts, 0.85);
  addCrest(head, form, palette, parts, 0.72);
  addTail(root, { ...form, tailStyle: form.tailStyle === 'none' ? 'whip' : form.tailStyle }, palette, parts, [0, 0, -0.58]);
  addSurfaceMarks(body, surface, palette, 0.58);
}

function buildMoth(root, form, surface, parts, palette) {
  const thorax = makeMesh(new THREE.IcosahedronGeometry(0.48, 2), material(palette[0]), { scale: [0.7, 1.15, 0.66] });
  const abdomen = makeMesh(new THREE.SphereGeometry(0.42, 16, 10), material(palette[1]), {
    position: [0, -0.5, -0.16], scale: [0.62, 1.35, 0.62]
  });
  root.add(thorax, abdomen);
  register(parts, 'body', thorax, { baseScale: thorax.scale.clone() });
  register(parts, 'body', abdomen, { baseScale: abdomen.scale.clone() });
  form.wingStyle = form.wingStyle === 'none' ? 'membrane' : form.wingStyle;
  addWings(root, form, palette, parts, 0.08, 0.9);
  const head = makeHead(form, palette, 0.43 * form.headRatio);
  head.position.set(0, 0.57, 0.1);
  root.add(head);
  addEyes(head, form, palette, parts, 0.62 * form.headRatio);
  for (const side of [-1, 1]) {
    const antenna = boneBetween([side * 0.12, 0.26, 0], [side * 0.32, 0.66, 0.02], 0.022, palette[2]);
    head.add(antenna); register(parts, 'antennae', antenna, { side, restZ: antenna.rotation.z });
  }
  for (let pair = 0; pair < 3; pair += 1) for (const side of [-1, 1]) {
    const leg = boneBetween([side * 0.28, 0.2 - pair * 0.23, 0], [side * (0.68 + pair * 0.05), -0.05 - pair * 0.23, 0.08], 0.035, palette[1]);
    root.add(leg); register(parts, 'legs', leg, { phase: pair * 0.8 + (side > 0 ? 0 : Math.PI), restX: leg.rotation.x });
  }
}

function buildBotanical(root, form, surface, parts, palette) {
  const stem = makeLimb(palette[0], 0.92, 0.22);
  stem.position.y = -0.15;
  root.add(stem); register(parts, 'body', stem, { baseScale: stem.scale.clone() });
  const head = makeHead({ ...form, headStyle: 'bud' }, palette, 0.64 * form.headRatio);
  head.position.set(0, 0.62, 0.05);
  root.add(head);
  addEyes(head, form, palette, parts, 0.72 * form.headRatio);
  addCrest(head, { ...form, crestStyle: form.crestStyle === 'none' ? 'petals' : form.crestStyle }, palette, parts, form.headRatio);
  for (const side of [-1, 1]) {
    const leaf = makeMesh(new THREE.SphereGeometry(0.34, 14, 8), material(palette[1]), {
      position: [side * 0.5, 0.08, 0], rotation: [0, 0, side * -0.65], scale: [0.38, 1.2, 0.28]
    });
    root.add(leaf); register(parts, 'arms', leaf, { side, restZ: leaf.rotation.z });
  }
  for (let index = 0; index < 3; index += 1) {
    const rootLeg = boneBetween([0, -0.57, 0], [(index - 1) * 0.48, -0.98, index % 2 ? 0.16 : -0.12], 0.07, palette[1]);
    root.add(rootLeg); register(parts, 'legs', rootLeg, { phase: index / 3 * TAU, restX: rootLeg.rotation.x });
  }
}

function buildCrystal(root, form, surface, parts, palette) {
  const core = makeMesh(new THREE.DodecahedronGeometry(0.72, 1), material(palette[0], { metalness: 0.18, roughness: 0.28 }), {
    scale: profileScale(form.bodyProfile, form.roundness)
  });
  root.add(core); register(parts, 'body', core, { baseScale: core.scale.clone() });
  const count = 6 + form.lobes;
  for (let index = 0; index < count; index += 1) {
    const angle = index / count * TAU;
    const shard = makeMesh(new THREE.ConeGeometry(0.12, 0.65 + index % 3 * 0.12, 5), material(palette[(index + 1) % 3], { metalness: 0.23, roughness: 0.22 }), {
      position: [Math.cos(angle) * 0.72, Math.sin(angle) * 0.55, -0.12], rotation: [0, 0, angle - Math.PI / 2]
    });
    root.add(shard); register(parts, 'petals', shard, { phase: angle, restY: shard.position.y });
  }
  const head = new THREE.Group();
  head.position.set(0, 0.1, 0.7);
  root.add(head);
  addEyes(head, form, palette, parts, 0.9);
  addTail(root, form, palette, parts, [0.5, -0.05, -0.3]);
  addSurfaceMarks(core, surface, palette, 0.68);
}

function buildShell(root, form, surface, parts, palette) {
  const body = makeMesh(new THREE.SphereGeometry(0.63, 18, 11), material(palette[1]), {
    position: [0, -0.14, 0.12], scale: [1.22, 0.52, 0.72]
  });
  const shell = makeMesh(new THREE.IcosahedronGeometry(0.72, 2), material(palette[0], { roughness: 0.74 }), {
    position: [0, 0.18, -0.18], scale: [0.92, 0.82, 0.55]
  });
  root.add(body, shell);
  register(parts, 'body', shell, { baseScale: shell.scale.clone() });
  const spiral = makeMesh(new THREE.TorusGeometry(0.27, 0.055, 8, 24), material(palette[2]), {
    position: [0, 0.2, 0.31], rotation: [0, 0, 0]
  });
  root.add(spiral);
  const head = makeHead(form, palette, 0.42 * form.headRatio);
  head.position.set(0, 0.04, 0.67);
  root.add(head);
  addEyes(head, form, palette, parts, 0.58 * form.headRatio);
  addEars(head, form, palette, parts, form.headRatio * 0.65);
  for (const side of [-1, 1]) for (const z of [-0.18, 0.22]) {
    const leg = makeLimb(palette[1], 0.28, 0.08);
    leg.position.set(side * 0.38, -0.55, z);
    root.add(leg); register(parts, 'legs', leg, { phase: side + z * 5, restX: 0 });
  }
}

function buildAquatic(root, form, surface, parts, palette) {
  const body = makeMesh(new THREE.SphereGeometry(0.78, 20, 12), material(palette[0]), {
    scale: [1.28, 0.58, 0.65]
  });
  root.add(body); register(parts, 'body', body, { baseScale: body.scale.clone() });
  const head = new THREE.Group();
  head.position.set(0.48, 0.1, 0.52);
  root.add(head);
  addEyes(head, form, palette, parts, 0.72);
  for (const side of [-1, 1]) {
    const fin = makeMesh(new THREE.ConeGeometry(0.28, 0.62, 3), material(palette[1], { side: THREE.DoubleSide }), {
      position: [side * 0.65, -0.18, 0], rotation: [Math.PI / 2, 0, side * -0.55], scale: [0.52, 1, 0.72]
    });
    root.add(fin); register(parts, 'fins', fin, { side, restZ: fin.rotation.z });
  }
  const tail = new THREE.Group();
  tail.position.set(-0.9, 0, 0);
  for (const side of [-1, 1]) {
    tail.add(makeMesh(new THREE.ConeGeometry(0.38, 0.7, 3), material(palette[2], { side: THREE.DoubleSide }), {
      position: [-0.22, side * 0.22, 0], rotation: [0, 0, side > 0 ? Math.PI / 2 : -Math.PI / 2], scale: [0.5, 1, 0.28]
    }));
  }
  root.add(tail); register(parts, 'tails', tail, { phase: 0, baseY: 0, baseZ: 0 });
  addSurfaceMarks(body, surface, palette, 0.66);
}

function buildMushroom(root, form, surface, parts, palette) {
  const stem = makeMesh(new THREE.CapsuleGeometry(0.27, 0.72, 7, 12), material(palette[2], { flatShading: false, roughness: 0.78 }), {
    position: [0, -0.15, 0], scale: [1, 1, 0.82]
  });
  const cap = makeMesh(new THREE.SphereGeometry(0.78, 20, 11), material(palette[0]), {
    position: [0, 0.56, 0], scale: [1.15, 0.42, 0.86]
  });
  root.add(stem, cap);
  register(parts, 'body', stem, { baseScale: stem.scale.clone() });
  register(parts, 'body', cap, { baseScale: cap.scale.clone() });
  const face = new THREE.Group();
  face.position.set(0, 0.08, 0.32);
  root.add(face);
  addEyes(face, form, palette, parts, 0.72);
  for (const side of [-1, 1]) {
    const arm = makeLimb(palette[1], 0.38, 0.065);
    arm.position.set(side * 0.4, -0.12, 0);
    arm.rotation.z = side * -0.75;
    root.add(arm); register(parts, 'arms', arm, { side, restZ: arm.rotation.z });
    const foot = makeMesh(new THREE.SphereGeometry(0.18, 12, 8), material(palette[1]), {
      position: [side * 0.22, -0.75, 0.08], scale: [1.25, 0.48, 0.75]
    });
    root.add(foot); register(parts, 'legs', foot, { phase: side > 0 ? 0 : Math.PI, restX: 0 });
  }
  addSurfaceMarks(cap, surface, palette, 0.64);
}

function buildCrawler(root, form, surface, parts, palette) {
  const body = makeMesh(new THREE.DodecahedronGeometry(0.68, 2), material(palette[0], { roughness: 0.7 }), {
    position: [0, -0.06, 0], scale: [1.18, form.roundness * 0.68, 0.76]
  });
  root.add(body); register(parts, 'body', body, { baseScale: body.scale.clone() });
  const pairs = Math.max(3, Math.min(4, form.legPairs || 3));
  for (let pair = 0; pair < pairs; pair += 1) for (const side of [-1, 1]) {
    const x = pairs === 1 ? 0 : -0.48 + pair / (pairs - 1) * 0.96;
    const leg = boneBetween(
      [x, -0.22, side * 0.28],
      [x + (pair - (pairs - 1) / 2) * 0.06, -0.72, side * (0.72 + pair % 2 * 0.06)],
      0.05,
      palette[1]
    );
    root.add(leg);
    register(parts, 'legs', leg, { phase: pair * 0.7 + (side > 0 ? 0 : Math.PI), restX: leg.rotation.x });
  }
  const head = makeHead(form, palette, 0.52 * form.headRatio);
  head.position.set(0, 0.08, 0.64);
  root.add(head);
  addEyes(head, form, palette, parts, 0.68 * form.headRatio);
  addEars(head, form, palette, parts, form.headRatio * 0.68);
  addCrest(head, form, palette, parts, form.headRatio * 0.7);
  addTail(root, form, palette, parts, [0.48, -0.1, -0.35]);
  addSurfaceMarks(body, surface, palette, 0.6);
}

function buildTripod(root, form, surface, parts, palette) {
  const body = makeMesh(new THREE.OctahedronGeometry(0.72, 2), material(palette[0]), {
    position: [0, 0.28, 0], scale: profileScale(form.bodyProfile, form.roundness)
  });
  root.add(body); register(parts, 'body', body, { baseScale: body.scale.clone() });
  for (let index = 0; index < 3; index += 1) {
    const angle = index / 3 * TAU - Math.PI / 2;
    const leg = boneBetween(
      [Math.cos(angle) * 0.32, -0.08, Math.sin(angle) * 0.26],
      [Math.cos(angle) * 0.76, -1.0, Math.sin(angle) * 0.5],
      0.085,
      palette[1]
    );
    root.add(leg); register(parts, 'legs', leg, { phase: angle, restX: leg.rotation.x });
  }
  const face = new THREE.Group();
  face.position.set(0, 0.35, 0.64);
  root.add(face);
  addEyes(face, form, palette, parts, 0.82);
  addCrest(face, form, palette, parts, 0.82);
  if (form.wingStyle !== 'none') addWings(root, form, palette, parts, 0.28, 0.58);
  addSurfaceMarks(body, surface, palette, 0.62);
}

function addSecondaryTrait(root, form, surface, parts, palette) {
  const secondary = form.secondaryArchetype;
  if (['ray', 'moth'].includes(secondary) && !parts.wings.length) {
    addWings(root, { ...form, wingStyle: form.wingStyle === 'none' ? 'leaf' : form.wingStyle }, palette, parts, 0.14, 0.52);
  } else if (secondary === 'crystal' && form.archetype !== 'crystal') {
    for (let index = 0; index < 3; index += 1) {
      root.add(makeMesh(new THREE.ConeGeometry(0.09, 0.45, 5), material(palette[2], { metalness: 0.16 }), {
        position: [(index - 1) * 0.23, 0.65 + index % 2 * 0.08, -0.18], rotation: [0, 0, (index - 1) * -0.14]
      }));
    }
  } else if (secondary === 'botanical' && form.archetype !== 'botanical') {
    for (let index = 0; index < 4; index += 1) {
      const angle = index / 4 * TAU;
      const petal = makeMesh(new THREE.SphereGeometry(0.15, 12, 7), material(palette[1]), {
        position: [Math.cos(angle) * 0.3, 0.7 + Math.sin(angle) * 0.12, -0.1], rotation: [0, 0, -angle], scale: [0.42, 1.2, 0.3]
      });
      root.add(petal); register(parts, 'petals', petal, { phase: angle, restY: petal.position.y });
    }
  } else if (secondary === 'shell' && form.archetype !== 'shell') {
    root.add(makeMesh(new THREE.IcosahedronGeometry(0.46, 2), material(palette[1], { roughness: 0.8 }), {
      position: [0, 0.2, -0.48], scale: [1, 0.85, 0.38]
    }));
  } else if (secondary === 'serpent' && !parts.tails.length) {
    addTail(root, { ...form, tailStyle: 'whip' }, palette, parts, [0.48, -0.05, -0.26]);
  } else if (secondary === 'aquatic') {
    for (const side of [-1, 1]) {
      const fin = makeMesh(new THREE.ConeGeometry(0.18, 0.4, 3), material(palette[2], { side: THREE.DoubleSide }), {
        position: [side * 0.62, -0.1, 0], rotation: [Math.PI / 2, 0, side * -0.5], scale: [0.5, 1, 0.5]
      });
      root.add(fin); register(parts, 'fins', fin, { side, restZ: fin.rotation.z });
    }
  } else if (secondary === 'crawler' && form.archetype !== 'crawler') {
    for (const side of [-1, 1]) {
      const feeler = boneBetween([side * 0.18, 0.38, 0.32], [side * 0.48, 0.62, 0.48], 0.024, palette[2]);
      root.add(feeler); register(parts, 'antennae', feeler, { side, restZ: feeler.rotation.z });
    }
  }
}

function addIndividualTrait(root, form, surface, parts, palette) {
  const trait = form.signatureTrait;
  const accent = palette[(root.userData.accentIndex || 2) % palette.length] || palette[2];
  if (trait === 'back sail') {
    for (let index = 0; index < 5; index += 1) {
      root.add(makeMesh(new THREE.ConeGeometry(0.1, 0.42 + index % 2 * 0.13, 3), material(accent, { side: THREE.DoubleSide }), {
        position: [(index - 2) * 0.24, 0.55 + index % 2 * 0.08, -0.34], rotation: [0.45, 0, 0]
      }));
    }
  } else if (trait === 'chest gem' || trait === 'luminous throat') {
    root.add(makeMesh(new THREE.OctahedronGeometry(trait === 'chest gem' ? 0.2 : 0.15, 1), material(accent, { metalness: 0.18, emissiveIntensity: 0.3 }), {
      position: [0, trait === 'chest gem' ? 0.03 : 0.38, 0.78]
    }));
  } else if (trait === 'split tail') {
    addTail(root, { ...form, tailStyle: form.tailStyle === 'none' ? 'whip' : form.tailStyle }, palette, parts, [-0.48, -0.08, -0.28]);
  } else if (trait === 'shoulder plates') {
    for (const side of [-1, 1]) root.add(makeMesh(new THREE.DodecahedronGeometry(0.24, 1), material(accent, { roughness: 0.74 }), {
      position: [side * 0.68, 0.22, 0.05], scale: [1, 0.65, 0.72]
    }));
  } else if (trait === 'crown buds') {
    for (let index = 0; index < 5; index += 1) root.add(makeMesh(new THREE.IcosahedronGeometry(0.11 + index % 2 * 0.03, 1), material(palette[index % palette.length]), {
      position: [(index - 2) * 0.15, 0.8 + index % 2 * 0.08, -0.04]
    }));
  } else if (trait === 'long whiskers') {
    for (const side of [-1, 1]) for (const rise of [-0.06, 0.08]) {
      root.add(boneBetween([side * 0.12, 0.16 + rise, 0.65], [side * 0.84, 0.2 + rise * 2, 0.74], 0.012, accent, { sides: 5, tipScale: 0.3 }));
    }
  } else if (trait === 'ankle tufts' || trait === 'stone knees') {
    for (const side of [-1, 1]) root.add(makeMesh(
      trait === 'stone knees' ? new THREE.DodecahedronGeometry(0.16, 1) : new THREE.ConeGeometry(0.14, 0.28, 6),
      material(accent),
      { position: [side * 0.34, -0.7, 0.18], rotation: [trait === 'ankle tufts' ? Math.PI : 0, 0, 0] }
    ));
  } else if (trait === 'side crest' || trait === 'brow horns') {
    const side = Number(form.asymmetry || 0) >= 0 ? 1 : -1;
    for (let index = 0; index < (trait === 'side crest' ? 3 : 2); index += 1) root.add(makeMesh(new THREE.ConeGeometry(0.09, 0.36 + index * 0.07, 5), material(accent), {
      position: [side * (0.26 + index * 0.13), 0.58 + index * 0.08, 0.34], rotation: [0, 0, -side * 0.3]
    }));
  } else if (trait === 'shell ridges' || trait === 'ring markings') {
    const count = trait === 'shell ridges' ? 3 : 2;
    for (let index = 0; index < count; index += 1) root.add(makeMesh(new THREE.TorusGeometry(0.34 + index * 0.13, 0.035, 7, 24), material(accent), {
      position: [0, 0.14, 0.56 - index * 0.08], rotation: [0, 0, 0], scale: [1, 0.82, 1]
    }));
  } else if (trait === 'mask freckles') {
    const count = 5 + Math.round((surface.markingDensity || 0.5) * 7);
    for (let index = 0; index < count; index += 1) {
      const angle = index / count * TAU;
      root.add(makeMesh(new THREE.SphereGeometry(0.028 + index % 2 * 0.012, 7, 5), material(accent, { emissiveIntensity: 0.08 }), {
        position: [Math.cos(angle) * 0.32, 0.2 + Math.sin(angle) * 0.18, 0.79]
      }));
    }
  } else if (trait === 'elbow fins' || trait === 'ribbon ears' || trait === 'leaf mane' || trait === 'fan crest') {
    const count = trait === 'leaf mane' ? 6 : trait === 'fan crest' ? 5 : 2;
    for (let index = 0; index < count; index += 1) {
      const side = count === 2 ? (index ? 1 : -1) : index / Math.max(1, count - 1) * 2 - 1;
      const fin = makeMesh(new THREE.ConeGeometry(0.13, 0.42, trait === 'ribbon ears' ? 6 : 3), material(accent, { side: THREE.DoubleSide }), {
        position: [side * (trait === 'elbow fins' ? 0.72 : 0.44), trait === 'elbow fins' ? -0.05 : 0.64 + (1 - Math.abs(side)) * 0.15, 0.08],
        rotation: [0, 0, -side * 0.8], scale: [0.5, 1, 0.5]
      });
      root.add(fin); register(parts, 'fins', fin, { side: side || 1, restZ: fin.rotation.z });
    }
  } else if (trait === 'glass spines') {
    for (let index = 0; index < 7; index += 1) root.add(makeMesh(new THREE.ConeGeometry(0.07, 0.38 + index % 3 * 0.1, 5), material(accent, { metalness: 0.2, transparent: true, opacity: 0.88 }), {
      position: [(index - 3) * 0.19, 0.58 + index % 2 * 0.07, -0.25], rotation: [0.25, 0, 0]
    }));
  } else if (trait === 'moss collar') {
    for (let index = 0; index < 9; index += 1) {
      const angle = index / 9 * TAU;
      root.add(makeMesh(new THREE.IcosahedronGeometry(0.11 + index % 2 * 0.025, 1), material(accent, { roughness: 0.94 }), {
        position: [Math.cos(angle) * 0.47, 0.38 + Math.sin(angle) * 0.1, Math.sin(angle) * 0.28]
      }));
    }
  }
}

function applyFinish(root, surface) {
  const settings = {
    velvet: { roughness: 0.96, metalness: 0 }, matte: { roughness: 0.8, metalness: 0 },
    pearl: { roughness: 0.3, metalness: 0.16 }, stone: { roughness: 0.9, metalness: 0.01 },
    glass: { roughness: 0.18, metalness: 0.2 }, bark: { roughness: 1, metalness: 0 },
    satin: { roughness: 0.4, metalness: 0.06 }, speckled: { roughness: 0.68, metalness: 0.02 }
  }[surface.finish] || { roughness: 0.58, metalness: 0.03 };
  root.traverse((object) => {
    if (!(object.material instanceof THREE.MeshStandardMaterial)) return;
    const { h, s, l } = object.material.color.getHSL({ h: 0, s: 0, l: 0 });
    if (l > 0.88 || l < 0.07) return;
    object.material.roughness = settings.roughness;
    object.material.metalness = settings.metalness;
    object.material.color.setHSL(h, s, l);
  });
}

export function createCreatureModel(creature) {
  const root = new THREE.Group();
  root.name = creature.id;
  const parts = partsFor(root);
  const { form, surface } = traitsOf(creature);
  const palette = surface.palette?.length ? surface.palette : ['#7cc8a4', '#4f83c2', '#f5ead0'];
  const builders = {
    quadruped: buildQuadruped,
    biped: buildBiped,
    serpent: buildSerpent,
    ray: buildRay,
    moth: buildMoth,
    botanical: buildBotanical,
    crystal: buildCrystal,
    shell: buildShell,
    aquatic: buildAquatic,
    mushroom: buildMushroom,
    crawler: buildCrawler,
    tripod: buildTripod
  };
  (builders[form.archetype] || buildCrawler)(root, form, surface, parts, palette);
  addSecondaryTrait(root, form, surface, parts, palette);
  root.userData.accentIndex = creature.genome.individual?.accentIndex || 2;
  addIndividualTrait(root, form, surface, parts, palette);
  applyFinish(root, surface);
  root.scale.setScalar(creature.genome.individual?.stature || 1);
  root.userData.form = form;
  root.userData.baseRotation = (Number.parseInt(creature.id.slice(0, 5), 16) / 0xfffff - 0.5) * 0.28;
  return root;
}

function stageFor(creature) {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(31, 1, 0.1, 100);
  camera.position.set(0, 0.12, 5.25);
  camera.lookAt(0, -0.02, 0);
  const palette = creature.genome.surface?.palette || ['#7cc8a4', '#4f83c2', '#f5ead0'];
  const hemisphere = new THREE.HemisphereLight(0xf2fff8, 0x35485a, 2.25);
  const key = new THREE.DirectionalLight(0xfff1d7, 3.75);
  key.position.set(-3.4, 5, 5);
  const rim = new THREE.PointLight(new THREE.Color(palette[1]), 6, 10);
  rim.position.set(3.2, 1.6, 2.4);
  const fill = new THREE.PointLight(new THREE.Color(palette[2]), 3.2, 8);
  fill.position.set(-2.6, -1, 2.2);
  scene.add(hemisphere, key, rim, fill);
  const model = createCreatureModel(creature);
  scene.add(model);
  const shadow = makeMesh(
    new THREE.CircleGeometry(1.38, 48),
    new THREE.MeshBasicMaterial({ color: 0x14271f, transparent: true, opacity: 0.12, depthWrite: false }),
    { position: [0, -1.13, 0.08], rotation: [-Math.PI / 2, 0, 0], scale: [1, 0.7, 1] }
  );
  scene.add(shadow);
  return { scene, camera, model };
}

function animationWeight(name, target) {
  return name === target ? 1 : 0;
}

function animateModel(model, creature, milliseconds, dragRotation = 0) {
  const seconds = milliseconds / 1000;
  const { form, motion } = traitsOf(creature);
  const parts = model.userData.parts;
  const signature = form.animation || 'amble';
  const tempo = Math.max(0.45, Number(motion.pulse || 1.8) * 0.58);
  const hover = Math.sin(seconds * Math.max(0.5, motion.bob || 1));
  const hop = Math.max(0, Math.sin(seconds * tempo * 1.45));
  model.position.y = hover * 0.055
    + hop ** 3 * 0.18 * (animationWeight(signature, 'hop') + animationWeight(signature, 'bound'));
  model.rotation.y = model.userData.baseRotation + Math.sin(seconds * Math.max(0.24, motion.sway || 0.7) * 0.38) * 0.24 + dragRotation;
  model.rotation.z = Math.sin(seconds * 0.42) * 0.025 * (signature === 'sway' ? 3 : 1);

  const breathe = 1 + Math.sin(seconds * tempo) * (signature === 'pulse' ? 0.055 : 0.022);
  for (const body of parts.body) {
    if (!body.userData.baseScale) body.userData.baseScale = body.scale.clone();
    body.scale.copy(body.userData.baseScale).multiplyScalar(breathe);
  }
  const gaitSpeed = signature === 'scuttle' ? 5.4 : signature === 'stalk' ? 1.3 : 2.7;
  for (const leg of parts.legs) {
    leg.rotation.x = (leg.userData.restX || 0) + Math.sin(seconds * gaitSpeed + leg.userData.phase) * (signature === 'amble' ? 0.14 : 0.24);
  }
  for (const arm of parts.arms) {
    arm.rotation.z = arm.userData.restZ + arm.userData.side * Math.sin(seconds * 1.8) * 0.12;
  }
  const wingSpeed = signature === 'glide' ? 1.2 : signature === 'flutter' ? 4.8 : 3.1;
  for (const wing of parts.wings) {
    wing.rotation.y = (wing.userData.restY || 0) + wing.userData.side * Math.sin(seconds * wingSpeed) * (signature === 'glide' ? 0.18 : 0.48);
    wing.rotation.z = (wing.userData.restZ || 0) + wing.userData.side * Math.sin(seconds * wingSpeed * 0.7) * 0.13;
  }
  for (const [index, segment] of parts.segments.entries()) {
    segment.position.y = segment.userData.base.y + Math.sin(seconds * (signature === 'coil' ? 2.5 : 1.5) + segment.userData.phase) * 0.12;
    segment.position.z = segment.userData.base.z + Math.cos(seconds * 1.4 + segment.userData.phase) * 0.06;
    segment.rotation.z = Math.sin(seconds * 1.7 + index * 0.5) * 0.12;
  }
  for (const tail of parts.tails) {
    if (Number.isFinite(tail.userData.baseY)) tail.position.y = tail.userData.baseY + Math.sin(seconds * 2 + tail.userData.phase) * 0.055;
    tail.rotation.y = Math.sin(seconds * 1.7 + tail.userData.phase) * 0.16;
  }
  for (const petal of parts.petals) {
    petal.position.y = petal.userData.restY + Math.sin(seconds * (signature === 'bloom' ? 2.1 : 1.1) + petal.userData.phase) * 0.045;
    petal.rotation.y = Math.sin(seconds * 1.2 + petal.userData.phase) * 0.08;
  }
  for (const fin of parts.fins) {
    fin.rotation.z = fin.userData.restZ + fin.userData.side * Math.sin(seconds * 2.2) * 0.12;
  }
  for (const ear of parts.ears) {
    ear.rotation.z = ear.userData.restZ + ear.userData.side * Math.sin(seconds * 0.8 + 0.4) * 0.035;
  }
  for (const antenna of parts.antennae) {
    antenna.rotation.z = (antenna.userData.restZ || 0) + antenna.userData.side * Math.sin(seconds * 1.4) * 0.055;
  }
  const blinkPhase = (seconds * 0.37 + Number.parseInt(creature.id.slice(-3), 16) * 0.001) % 1;
  const blink = blinkPhase > 0.94 ? Math.max(0.12, Math.abs(blinkPhase - 0.97) * 25) : 1;
  for (const eye of parts.eyes) eye.scale.y = blink;
  for (const pupil of parts.pupils) {
    pupil.position.x = Math.sin(seconds * 0.55 + pupil.userData.phase) * 0.018;
    pupil.position.y = Math.cos(seconds * 0.4 + pupil.userData.phase) * 0.008;
  }
}

export function animateCreatureModel(model, creature, milliseconds, dragRotation = 0) {
  animateModel(model, creature, milliseconds, dragRotation);
}

function configureRenderer(renderer) {
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.08;
}

function disposeTree(root) {
  root.traverse((value) => {
    value.geometry?.dispose?.();
    if (Array.isArray(value.material)) value.material.forEach((entry) => entry.dispose());
    else value.material?.dispose?.();
  });
}

function canvasDimensions(canvas) {
  const fallbackWidth = Number(canvas.getAttribute('width')) || 280;
  const fallbackHeight = Number(canvas.getAttribute('height')) || fallbackWidth;
  return {
    width: Math.max(32, Math.round(canvas.clientWidth || fallbackWidth)),
    height: Math.max(32, Math.round(canvas.clientHeight || fallbackHeight))
  };
}

export function drawCreatureFrame(canvas, creature, time = 0) {
  if (!canvas || !creature) return;
  if (!snapshotRenderer) {
    snapshotCanvas = document.createElement('canvas');
    snapshotRenderer = new THREE.WebGLRenderer({ canvas: snapshotCanvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
    configureRenderer(snapshotRenderer);
  }
  const { width, height } = canvasDimensions(canvas);
  const dpr = Math.min(2, globalThis.devicePixelRatio || 1);
  const pixelWidth = Math.min(720, Math.round(width * dpr));
  const pixelHeight = Math.min(720, Math.round(height * dpr));
  snapshotRenderer.setSize(pixelWidth, pixelHeight, false);
  const stage = stageFor(creature);
  stage.camera.aspect = pixelWidth / pixelHeight;
  stage.camera.updateProjectionMatrix();
  animateModel(stage.model, creature, Number(time) || 0);
  snapshotRenderer.render(stage.scene, stage.camera);
  canvas.width = pixelWidth;
  canvas.height = pixelHeight;
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, pixelWidth, pixelHeight);
  context.drawImage(snapshotCanvas, 0, 0, pixelWidth, pixelHeight);
  disposeTree(stage.scene);
  snapshotRenderer.renderLists.dispose();
}

export class CreatureRenderer {
  constructor(canvas, creature, { interactive = true } = {}) {
    this.canvas = canvas;
    this.creature = creature;
    this.interactive = interactive;
    this.frame = null;
    this.dragRotation = 0;
    this.dragging = null;
    this.reducedMotion = globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    this.renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
    configureRenderer(this.renderer);
    this.stage = stageFor(creature);
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas);
    this.resize();
    this.bindInteraction();
  }

  bindInteraction() {
    if (!this.interactive) return;
    this.canvas.style.touchAction = 'none';
    this.canvas.addEventListener('pointerdown', (event) => {
      this.dragging = { id: event.pointerId, x: event.clientX, rotation: this.dragRotation };
      this.canvas.setPointerCapture(event.pointerId);
    });
    this.canvas.addEventListener('pointermove', (event) => {
      if (this.dragging?.id !== event.pointerId) return;
      this.dragRotation = this.dragging.rotation + (event.clientX - this.dragging.x) * 0.012;
    });
    const end = (event) => {
      if (this.dragging?.id === event.pointerId) this.dragging = null;
    };
    this.canvas.addEventListener('pointerup', end);
    this.canvas.addEventListener('pointercancel', end);
  }

  resize() {
    if (this.disposed) return;
    const { width, height } = canvasDimensions(this.canvas);
    this.renderer.setPixelRatio(Math.min(2, globalThis.devicePixelRatio || 1));
    this.renderer.setSize(width, height, false);
    this.stage.camera.aspect = width / height;
    this.stage.camera.updateProjectionMatrix();
    this.render(performance.now());
  }

  setCreature(creature) {
    this.stop();
    disposeTree(this.stage.scene);
    this.creature = creature;
    this.stage = stageFor(creature);
    this.dragRotation = 0;
    this.resize();
  }

  render = (time) => {
    if (this.disposed) return;
    if (this.frame != null && this.lastRenderTime != null && time - this.lastRenderTime < 32) {
      this.frame = requestAnimationFrame(this.render);
      return;
    }
    this.lastRenderTime = time;
    animateModel(this.stage.model, this.creature, this.reducedMotion ? 0 : time, this.dragRotation);
    this.renderer.render(this.stage.scene, this.stage.camera);
    if (this.frame != null && !this.reducedMotion) this.frame = requestAnimationFrame(this.render);
  };

  start() {
    this.stop();
    if (this.reducedMotion) this.render(0);
    else this.frame = requestAnimationFrame(this.render);
  }

  stop() {
    if (this.frame != null) cancelAnimationFrame(this.frame);
    this.frame = null;
  }

  dispose() {
    this.disposed = true;
    this.stop();
    this.resizeObserver.disconnect();
    disposeTree(this.stage.scene);
    this.renderer.dispose();
  }
}
