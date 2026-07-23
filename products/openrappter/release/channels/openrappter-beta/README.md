# openrappter-beta

Ring **beta** (rank 3) of the OpenRappter release train.

    canary -> nightly -> alpha -> beta -> stable

- **Publishes to:** `openrappter-beta` on npm — and nothing else.
- **Promotes to:** `stable`
- **Cut by:** hand-promoted from alpha

## Install this ring

```sh
curl -fsSL https://kody-w.github.io/openrappter/install.sh | bash -s -- --channel beta
```

or directly:

```sh
npm install -g openrappter-beta
```

## Why a separate repo and package

Production is **unreachable** from this repo, not merely guarded. This repo has
no credentials for and no code path to the production `openrappter` package.
Deleting this repo and its npm package outright would have zero effect on
anyone running the released build.

Promotion republishes the *identical tarball* under the next ring's package
name — it never rebuilds, mirroring the exact-commit promotion rule of the rapp
release train.

Dashboard: https://kody-w.github.io/openrappter-release-train/
