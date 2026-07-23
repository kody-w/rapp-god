#!/bin/sh
# Spawn the real Copilot CLI confined by an sandbox-exec profile so the surgeon
# (and ANY child shell it spawns) physically cannot write outside agents/.
# Env: SURGEON_SBPROFILE = profile path, SURGEON_REAL_CLI = bundled copilot binary.
exec /usr/bin/sandbox-exec -f "$SURGEON_SBPROFILE" "$SURGEON_REAL_CLI" "$@"
