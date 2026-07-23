# RAPP Plant Smoke Test

> A RAPP front door on the public internet. Real estate, not software.

- **Address:** `kody-w.github.io/rapp-plant-smoke-20260505-233637`
- **Rappid:** `rappid:@kody-w/rapp-plant-smoke-20260505-233637:d71b8068a192c1050c3a032c207abda38dbbfd5fe0c97a6e564e8b85c20f86bd`
- **Kernel:** v0.6.0 (byte-identical to the grail at `kody-w/rapp-installer`)
- **Planted by:** [@kody-w](https://github.com/kody-w)


## What's behind this door

The kernel files in `rapp_brainstem/` are kernel-compliant per the
[Mirror Spec](https://kody-w.github.io/RAPP/pages/vault/Architecture/Mirror%20Spec.md).
Everything else — `agents/`, the soul, the UI surfaces — is what the
operator chose to put inside.

## Visit the front door

Open the URL in any browser:

```
https://kody-w.github.io/rapp-plant-smoke-20260505-233637
```

## Install this front door's brainstem locally

```
curl -fsSL https://kody-w.github.io/rapp-plant-smoke-20260505-233637/installer/install.sh | bash
```

That installer is a thin wrapper that re-fetches the canonical kernel
installer from the grail on every run — this front door cannot drift
from the kernel.

## Plant your own front door

```
curl -fsSL https://kody-w.github.io/RAPP/installer/plant.sh | bash
```

## Verify this front door has not drifted from the grail

```bash
for f in rapp_brainstem/brainstem.py rapp_brainstem/VERSION rapp_brainstem/agents/basic_agent.py; do
  diff <(curl -fsSL "https://raw.githubusercontent.com/kody-w/rapp-installer/main/$f") "$f" \
    || echo "DRIFT: $f"
done
```

Three empty diffs = compliant. Anything else = not a valid mirror.
