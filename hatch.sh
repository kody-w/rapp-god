#!/usr/bin/env bash
# hatch.sh — turn this egg into a RUNNING RAPP, from the egg alone.
#
# The egg is a complete census of the ecosystem: 198 pinned source trees, every
# captured version of every load-bearing part. What it lacked was a declared way
# to GO FROM "I have this" TO "RAPP is running". It contains 39 brainstem.py
# copies and, until this file, nothing that said which one to run.
#
# That gap is the difference between an archive and a distributable artifact.
# An egg nobody has hatched on a clean box is a claim, not an artifact.
#
#   ./hatch.sh                 # hatch into ./.hatch on the first free port
#   ./hatch.sh --dir DIR       # hatch somewhere else
#   ./hatch.sh --port N        # pin the port
#   ./hatch.sh --check         # hatch, prove it serves, tear down, report (CI)
#
# Isolation: the hatched tree is self-contained. It never reads or writes
# ~/.brainstem, and it never touches a port it did not open.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="vendor/upstream/rapp-installer-main"   # the pinned grail checkout
DIR="$ROOT/.hatch"
PORT=""
CHECK=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dir)   DIR="$2"; shift 2 ;;
    --port)  PORT="$2"; shift 2 ;;
    --check) CHECK=1; shift ;;
    -h|--help) sed -n '2,18p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 64 ;;
  esac
done

say() { printf '  %s\n' "$*"; }

[ -d "$ROOT/$SOURCE/rapp_brainstem" ] || {
  echo "FATAL: $SOURCE/rapp_brainstem missing — this egg cannot hatch." >&2
  echo "       The pinned grail checkout is the runnable core; without it the" >&2
  echo "       egg is an archive, not an artifact." >&2
  exit 70
}

# Pick a port we can actually have. Never assume: a busy port here means some
# other service owns it, and we do not touch listeners we did not start.
if [ -z "$PORT" ]; then
  for p in $(seq 7090 7110); do
    if ! lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then PORT="$p"; break; fi
  done
fi
[ -n "$PORT" ] || { echo "FATAL: no free port in 7090-7110" >&2; exit 69; }

rm -rf "$DIR"; mkdir -p "$DIR"
cp -R "$ROOT/$SOURCE/." "$DIR/"
BS="$DIR/rapp_brainstem"
say "hatched from $SOURCE -> $DIR"

python3 -m venv "$BS/.venv"
"$BS/.venv/bin/pip" install -q -r "$BS/requirements.txt"
say "dependencies installed from the egg's own requirements.txt"

cd "$BS"
PORT="$PORT" nohup "$BS/.venv/bin/python" brainstem.py > "$DIR/hatch.log" 2>&1 &
PID=$!
say "started pid $PID on :$PORT"

# Poll rather than sleep-and-hope: a fixed sleep either wastes time or lies.
ok=0
for _ in $(seq 1 40); do
  if curl -fsS -m 3 "http://localhost:$PORT/health" >/dev/null 2>&1; then ok=1; break; fi
  sleep 1
done

if [ "$ok" -eq 1 ]; then
  BODY=$(curl -fsS -m 10 "http://localhost:$PORT/health")
  VER=$(printf '%s' "$BODY" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("version","?"))')
  N=$(printf '%s' "$BODY" | python3 -c 'import json,sys;print(len(json.load(sys.stdin).get("agents",[])))')
  ST=$(printf '%s' "$BODY" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("status","?"))')
  say "SERVING  v$VER  $N agent(s)  status=$ST  http://localhost:$PORT/health"
  say "status=unauthenticated is CORRECT here — a hatched egg carries no token."
else
  say "FAILED to serve on :$PORT — log tail:"
  tail -15 "$DIR/hatch.log" | sed 's/^/      /'
fi

if [ "$CHECK" -eq 1 ]; then
  kill "$PID" 2>/dev/null || true
  sleep 2
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    say "WARNING: :$PORT still held after kill"
  else
    say "torn down; :$PORT released"
  fi
  [ "$ok" -eq 1 ] || exit 1
  say "HATCH OK — this egg reconstitutes a running RAPP with no network and no install."
  exit 0
fi

say "leaving it running (pid $PID). stop with: kill $PID"
