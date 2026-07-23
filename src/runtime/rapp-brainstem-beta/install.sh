#!/usr/bin/env bash
# RAPP Brainstem — BETA channel installer (brainstem + brain surgeon).
#   curl -fsSL https://raw.githubusercontent.com/kody-w/rapp-brainstem-beta/beta/install.sh | bash
#
# Fresh-installs the BETA brainstem (engine + the scalpel/brain-surgeon) and PRESERVES your
# local state — your custom agents, .env, Copilot tokens, and .brainstem_data are backed up
# and restored. Nothing of yours is lost. The stable production install is not used.
set -euo pipefail

BETA_HOME="${BETA_HOME:-$HOME/.brainstem}"          # brainstem home (override for testing)
SRC="$BETA_HOME/src/rapp_brainstem"                  # where the engine lives (production layout)
SURGEON_HOME="$BETA_HOME/surgeon"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HOME/.brainstem-backup-$TS"
DEFAULT_AGENTS="basic_agent.py context_memory_agent.py manage_memory_agent.py hacker_news_agent.py"

# Locate the beta checkout (this script's dir if cloned; else clone it).
if [ -n "${BETA_SRC:-}" ] && [ -d "$BETA_SRC/brainstem" ]; then
  REPO_DIR="$BETA_SRC"
elif [ -f "${BASH_SOURCE[0]:-}" ] && [ -d "$(dirname "${BASH_SOURCE[0]}")/brainstem" ]; then
  REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  REPO_DIR="$HOME/.rapp-brainstem-beta"
  echo "Fetching the beta…"
  if [ -d "$REPO_DIR/.git" ]; then git -C "$REPO_DIR" fetch -q origin beta && git -C "$REPO_DIR" reset -q --hard origin/beta
  else git clone -q --branch beta https://github.com/kody-w/rapp-brainstem-beta.git "$REPO_DIR"; fi
fi

PY="$(command -v python3.11 || command -v python3.12 || command -v python3 || true)"
[ -n "$PY" ] || { echo "Python 3.11+ required"; exit 1; }

echo "RAPP Brainstem BETA - $BETA_HOME"

# ── 1. PRESERVE your local state ──────────────────────────────────────────────
if [ -d "$SRC" ]; then
  echo "- backing up your local state to $BACKUP"
  mkdir -p "$BACKUP/agents"
  for f in "$SRC"/agents/*_agent.py; do
    [ -f "$f" ] || continue
    b="$(basename "$f")"
    case " $DEFAULT_AGENTS " in *" $b "*) : ;; *) cp "$f" "$BACKUP/agents/" ;; esac
  done
  for p in .env .copilot_token .copilot_session voice.json voice.zip; do
    [ -f "$SRC/$p" ] && cp "$SRC/$p" "$BACKUP/" || true
  done
  [ -d "$SRC/.brainstem_data" ] && cp -R "$SRC/.brainstem_data" "$BACKUP/" || true
  n="$(ls "$BACKUP/agents" 2>/dev/null | wc -l | tr -d ' ')"
  echo "   preserved $n custom agent(s) + secrets + memory"
fi

# ── 2. FRESH brainstem from the beta bundle ───────────────────────────────────
echo "- installing the beta brainstem engine"
rm -rf "$SRC"; mkdir -p "$SRC/agents"
cp -R "$REPO_DIR/brainstem/." "$SRC/"
# Recreate the venv if it's missing OR broken (a dangling symlink passes -f but won't run).
"$BETA_HOME/venv/bin/python" -c "" 2>/dev/null || { rm -rf "$BETA_HOME/venv"; "$PY" -m venv "$BETA_HOME/venv"; }
# --no-cache-dir dodges a corrupt pip HTTP cache ("Cache entry deserialization failed" -> OSError).
"$BETA_HOME/venv/bin/pip" install -q --no-cache-dir --upgrade pip >/dev/null
"$BETA_HOME/venv/bin/pip" install -q --no-cache-dir -r "$SRC/requirements.txt"
[ -f "$SRC/.env" ] || { [ -f "$SRC/.env.example" ] && cp "$SRC/.env.example" "$SRC/.env"; } || true

# ── 3. RESTORE your state ─────────────────────────────────────────────────────
if [ -d "$BACKUP" ]; then
  echo "- restoring your custom agents + secrets + memory"
  cp "$BACKUP"/agents/*.py "$SRC/agents/" 2>/dev/null || true
  for p in .env .copilot_token .copilot_session voice.json voice.zip; do
    [ -f "$BACKUP/$p" ] && cp "$BACKUP/$p" "$SRC/" || true
  done
  [ -d "$BACKUP/.brainstem_data" ] && cp -R "$BACKUP/.brainstem_data" "$SRC/" || true
fi

# ── 4. BRAIN SURGEON sidecar ──────────────────────────────────────────────────
echo "- installing the brain surgeon sidecar"
rm -rf "$SURGEON_HOME"; mkdir -p "$SURGEON_HOME"
cp -R "$REPO_DIR/surgeon/." "$SURGEON_HOME/"
"$SURGEON_HOME/venv/bin/python" -c "" 2>/dev/null || { rm -rf "$SURGEON_HOME/venv"; "$PY" -m venv "$SURGEON_HOME/venv"; }
"$SURGEON_HOME/venv/bin/pip" install -q --no-cache-dir --upgrade pip >/dev/null
"$SURGEON_HOME/venv/bin/pip" install -q --no-cache-dir -r "$SURGEON_HOME/requirements.txt"

# ── 5. one-command launcher (brainstem must run from its own dir) ─────────────
cat > "$BETA_HOME/start-all.sh" <<LAUNCH
#!/usr/bin/env bash
# Launch the beta brainstem (patient, :7071) + the brain surgeon (sidecar, :7072).
set -e
( cd "$SRC" && PORT=\${PORT:-7071} "$BETA_HOME/venv/bin/python" brainstem.py ) &
BS_PID=\$!
trap 'kill \$BS_PID 2>/dev/null' EXIT
BRAINSTEM_AGENTS="$SRC/agents" SURGEON_PORT=\${SURGEON_PORT:-7072} "$SURGEON_HOME/start.sh"
LAUNCH
chmod +x "$BETA_HOME/start-all.sh"

cat <<EOF

Beta installed (old state preserved at: ${BACKUP:-none}; your agents are also in your private RAR).

Launch the patient + surgeon together:
   "$BETA_HOME/start-all.sh"

Then open http://localhost:7071 and click the scalpel beside the chat. The grail
(brainstem.py) is OS-confined and cannot be touched. The stable production install was not used.
EOF
