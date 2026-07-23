#!/bin/bash
# sweep.sh — clone every public kody-w repo (shallow) and run the shared
# rapp-drift-lint across all of them, emitting a per-repo violation tally.
#
# Usage: sweep.sh <workdir> [lint-path]
#   workdir    where clones live (reused/updated on re-run)
#   lint-path  path to rapp-drift-lint/lint.mjs (default: clones it)
#
# Output: a report to stdout — "<repo>: <N> violations" for every dirty repo,
# then a total. Fixing is a judgment step you do after reading the report.
set -euo pipefail
WORK="${1:?usage: sweep.sh <workdir> [lint-path]}"
LINT="${2:-}"
mkdir -p "$WORK"; cd "$WORK"

# ensure gh is the personal account (kody-w repos 403 under the work alias)
ACTIVE=$(gh auth status 2>/dev/null | awk '/Logged in to github.com account/{a=$7}/Active account: true/{print a;exit}')
[ "$ACTIVE" != "kody-w" ] && { echo "WARN: gh active account is '$ACTIVE', not kody-w — run: gh auth switch --user kody-w"; }

if [ -z "$LINT" ]; then
  [ -d rapp-drift-lint ] || git clone -q --depth 1 https://github.com/kody-w/rapp-drift-lint.git
  LINT="$WORK/rapp-drift-lint/lint.mjs"
fi

echo "# cloning/refreshing public kody-w repos ..." >&2
gh repo list kody-w --limit 300 --no-archived --json name,isPrivate \
  --jq '.[] | select(.isPrivate==false).name' > .repos.txt
# REPO_LIMIT=N caps the sweep for smoke runs (0/unset = full estate)
if [ "${REPO_LIMIT:-0}" -gt 0 ] 2>/dev/null; then
  head -n "$REPO_LIMIT" .repos.txt > .repos.lim && mv .repos.lim .repos.txt
fi
while read -r r; do
  [ -z "$r" ] && continue
  if [ -d "$r/.git" ]; then git -C "$r" pull -q --ff-only 2>/dev/null || true
  else git clone -q --depth 1 "https://github.com/kody-w/$r.git" "$r" 2>/dev/null || echo "CLONE-FAIL $r" >&2; fi
done < .repos.txt

echo "# linting ..." >&2
total=0; dirty=0
for d in */; do
  [ -d "$d/.git" ] || continue
  [ "${d%/}" = "rapp-drift-lint" ] && continue  # don't lint the lint
  out=$(node "$LINT" --path "$d" 2>&1 || true)
  if ! grep -q "clean" <<<"$out"; then
    n=$(grep -oE '[0-9]+ violation' <<<"$out" | grep -oE '[0-9]+' | head -1); n=${n:-?}
    echo "${d%/}: $n violations"
    dirty=$((dirty+1)); [ "$n" != "?" ] && total=$((total+n))
  fi
done
echo "---"
echo "$dirty repos dirty, $total total violations"
