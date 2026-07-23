#!/bin/bash
# claim.sh <id> [--steal] — atomic, git-enforced claim of a brain node so two
# parallel Opuses never crawl the same one. Prints CLAIMED or TAKEN.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
STEAL=""; ID=""
for a in "$@"; do [ "$a" = "--steal" ] && STEAL=1 || ID="$a"; done
[ -n "$ID" ] || { echo "usage: claim.sh <id> [--steal]" >&2; exit 2; }
SAFE=$(printf '%s' "$ID" | tr '/:@ ' '____')
ME="${RAPP_WRITER_ID:-$(git config user.email 2>/dev/null || echo opus)-$$}"
CLAIM="brain/claims/$SAFE.txt"; mkdir -p brain/claims

for attempt in 1 2 3 4 5; do
  git pull --rebase --autostash -q 2>/dev/null || true
  if [ -f "$CLAIM" ]; then
    owner=$(head -1 "$CLAIM"); when=$(sed -n '2p' "$CLAIM")
    if [ "$owner" = "$ME" ]; then echo "CLAIMED (already yours): $ID"; exit 0; fi
    if [ -z "$STEAL" ]; then echo "TAKEN by $owner since $when: $ID"; exit 1; fi
    echo "steal $ME $(date -u +%FT%TZ) (was $owner)" >> "$CLAIM"
  fi
  printf '%s\n%s\n' "$ME" "$(date -u +%FT%TZ)" > "$CLAIM"
  git add "$CLAIM" && git commit -q -m "claim: $ID by $ME" 2>/dev/null || true
  if git push -q 2>/dev/null; then echo "CLAIMED: $ID"; exit 0; fi
done
echo "TAKEN (lost push race): $ID"; exit 1
