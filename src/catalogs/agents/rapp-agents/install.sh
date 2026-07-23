#!/usr/bin/env bash
# Install this RAPP agent stack into a local brainstem.
#
# What it does:
#   1. Creates ~/.rapp/workspace/ as the brainstem's agents workspace.
#   2. Copies basic_agent.py + rapp_loader_agent.py into the workspace.
#   3. Rewrites ~/.brainstem/src/rapp_brainstem/.env to set
#      AGENTS_PATH=~/.rapp/workspace.
#   4. Tells you to restart the brainstem.
#
# Idempotent — safe to re-run.
set -euo pipefail

SACRED_DIR="${HOME}/.brainstem/src/rapp_brainstem"
WORKSPACE="${HOME}/.rapp/workspace"
THIS_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${WORKSPACE}"

cp "${THIS_REPO}/agents/basic_agent.py" "${WORKSPACE}/basic_agent.py"
cp "${THIS_REPO}/agents/rapp_loader_agent.py" "${WORKSPACE}/rapp_loader_agent.py"

ENV_FILE="${SACRED_DIR}/.env"
if [[ -f "${ENV_FILE}" ]]; then
    if grep -q "^AGENTS_PATH=" "${ENV_FILE}"; then
        # Replace in place (BSD sed compatible — uses tmpfile dance)
        tmp="$(mktemp)"
        sed "s|^AGENTS_PATH=.*|AGENTS_PATH=${WORKSPACE}|" "${ENV_FILE}" > "${tmp}"
        mv "${tmp}" "${ENV_FILE}"
    else
        echo "AGENTS_PATH=${WORKSPACE}" >> "${ENV_FILE}"
    fi
else
    cat > "${ENV_FILE}" <<EOF
SOUL_PATH=./soul.md
AGENTS_PATH=${WORKSPACE}
PORT=7071
EOF
fi

echo "✓ Installed RAPP agent stack from: ${THIS_REPO}"
echo "✓ Workspace:   ${WORKSPACE}"
echo "✓ Loader at:   ${WORKSPACE}/rapp_loader_agent.py"
echo "✓ AGENTS_PATH set in: ${ENV_FILE}"
echo ""
echo "Restart your brainstem:"
echo "   cd ${SACRED_DIR} && ./start.sh"
echo ""
echo "Then in chat:  'what agents do I have available?'"
