# openrappter-nightly

Ring **nightly** (rank 1) of the OpenRappter release train.

    canary -> nightly -> alpha -> beta -> stable

- **Publishes to:** `openrappter-nightly` on npm — and nothing else.
- **Promotes to:** `alpha`
- **Cut by:** daily, promoted from canary

## Install this ring

```sh
curl -fsSL https://kody-w.github.io/openrappter/install.sh | bash -s -- --channel nightly
```

or directly:

```sh
npm install -g openrappter-nightly
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
