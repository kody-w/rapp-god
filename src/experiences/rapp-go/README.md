# rapp·go

[![rapp·go v2](https://img.shields.io/endpoint?url=https://kody-w.github.io/rapp-go/api/v1/badge.json)](https://kody-w.github.io/rapp-go/)

A private, no-backend moment field. A thought, picture, sound, place, time, or sky becomes a living 3D being; caught moments can lend traits to one permanent companion without replacing its identity.

- **Live app:** https://kody-w.github.io/rapp-go/
- **Deterministic demo:** https://kody-w.github.io/rapp-go/?demo=1&reset=1

## What was rebuilt

Version 2.1 is a from-scratch, standalone implementation. It preserves the original moment/genome/companion idea while removing every monorepo-relative dependency.

The new repository includes:

- a low-angle, perspective Three.js world that keeps real CARTO/OpenStreetMap streets as its geographic ground
- actual animated 3D creature rigs standing at geographic positions on the map—no flat creature markers
- deterministic moment genomes derived from any combination of thought, picture, sound, time, place, mood, and weather
- a private memory ceremony that creates one permanent companion; raw image/audio bytes are reduced to traits and released
- trait-wise companion evolution: captured beings can splice form, surface, and/or motion into the current body
- an append-only, content-hashed evolution history with non-destructive reversion and a stable companion id
- real-time Three.js/WebGL geometry with perspective, flat-shaded meshes, dynamic lights, ground shadows, orbit controls, breathing, gait, and articulated parts
- **151 original starting species** across twelve grounded body plans, each with a stable field-guide number and animation rig
- moment-derived individual traits—proportions, markings, finish, asymmetry, crest, tail, ears, gait, and a hallmark feature—so same-species catches are not clones
- a three-wobble catch model with vessel, offering, rarity, and flee modifiers
- public OpenStreetMap Overpass places with range checks, cooldowns, deterministic drops, and lures
- an IndexedDB field journal plus local-only satchel and preferences
- content-addressed creature links that are verified before import
- `hologram-cartridge/1.0` export into [rapp-lantern](https://github.com/kody-w/rapp-lantern)
- deterministic demo, fixed-coordinate, and live-geolocation modes
- service-worker offline shell caching and an installable web manifest
- unit and browser-level end-to-end coverage in CI

The deployed machine-readable field guide is available at [`api/v1/species.json`](https://kody-w.github.io/rapp-go/api/v1/species.json).

## Privacy model

Exact GPS is used only in the browser for distance and map placement. Weather requests use the center of a precision-5 geohash; place requests use a precision-6 geohash cell. There is no app backend, account, telemetry, ad system, or server inventory. See [PRIVACY.md](PRIVACY.md).

## Run locally

Requires Node.js 20 or later.

```sh
npm install
npx playwright install chromium
npm run serve
```

Open http://127.0.0.1:4173/?demo=1&reset=1.

## Validate

```sh
npm test
npm run test:e2e
npm run build
```

`npm run check` runs all three stages. GitHub Actions repeats the same checks before deploying `dist/` to Pages.

## Test modes

| URL option | Behavior |
| --- | --- |
| `?demo=1` | Fixed weather, location, places, time, and guaranteed first demo catch |
| `?fix=LAT,LNG` | Use a desktop-friendly fixed coordinate after onboarding |
| `?t=EPOCH_MS` | Pin the 30-minute creature field bucket |
| `?reset=1` | Clear only rapp·go's local browser state before boot |

## Architecture

```text
src/
  app.js                  UI state machine and complete journey
  companion/              stable identity, evolution frames, splice/revert
  data/                   151 deterministic species blueprints
  game/                   catch, economy, and spawn rules
  lib/                    moment signals, geo, RNG, identity, sharing, Lantern export
  services/               local storage, weather, and place adapters
  ui/                     tilted WebGL map and shared procedural 3D anatomy engine
tests/
  unit/                   deterministic rule tests
  e2e/                    mobile and desktop browser journeys
```

Map tiles are © OpenStreetMap contributors and © CARTO. Public place data is © OpenStreetMap contributors. Code is available under the [MIT License](LICENSE).
