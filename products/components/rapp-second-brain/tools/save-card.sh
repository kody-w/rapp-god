#!/bin/bash
# save-card.sh <card.json> — commit a single card with pull-rebase-push and
# bounded retry. Safe under many parallel writers: cards are per-node files,
# so rebases merge cleanly. NEVER touches INDEX.md / graph.json (CI derives
# those). Runs the tower guard over the card first, if present.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
CARD="${1:?usage: save-card.sh <brain/cards/x.json>}"
[ -f "$CARD" ] || { echo "no such card: $CARD" >&2; exit 2; }
python3 -c "import json;json.load(open('$CARD'))" || { echo "card is not valid JSON: $CARD" >&2; exit 2; }

GUARD="$HOME/Documents/GitHub/rapp-tower/tools/guard.sh"
[ -x "$GUARD" ] && { "$GUARD" "$CARD" || { echo "GUARD BLOCKED $CARD — do not override" >&2; exit 1; }; }

for attempt in 1 2 3 4 5 6; do
  git add "$CARD"
  git commit -q -m "card: $(basename "$CARD" .json)" 2>/dev/null || true
  git pull --rebase --autostash -q 2>/dev/null || true
  if git push -q 2>/dev/null; then echo "saved: $CARD"; exit 0; fi
  sleep $((attempt))   # bounded backoff on a transient race
done
echo "save failed after retries (unusual — check for a same-card writer): $CARD" >&2; exit 1
