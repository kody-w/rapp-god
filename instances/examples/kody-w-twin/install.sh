#!/usr/bin/env bash
set -e

# kody-w-twin installer
# Drops you into a state where you can hatch @kody-w's twin locally.
#
# This repo holds the twin's IDENTITY (rappid + soul + agents).
# The HATCHER lives in a separate canonical repo so every twin shares
# one tool: https://github.com/kody-w/twin-egg-hatcher
#
#   curl -fsSL https://raw.githubusercontent.com/kody-w/kody-w-twin/main/install.sh | bash
#
# What you get:
#   1. ./twin_egg_hatcher_agent.py  (fetched from the public mirror)
#   2. A printed command to run to materialize the twin

MIRROR_BRANCH="${TWIN_EGG_HATCHER_BRANCH:-main}"
HATCHER_NAME="twin_egg_hatcher_agent.py"
MIRROR_URL="https://raw.githubusercontent.com/kody-w/twin-egg-hatcher/${MIRROR_BRANCH}/${HATCHER_NAME}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo ""
echo -e "${CYAN}🧬 kody-w-twin${NC}"
echo "   @kody-w's operator twin · install via public hatcher mirror"
echo ""

# Sanity: brainstem present?
BRAINSTEM_HOME="${BRAINSTEM_HOME:-$HOME/.brainstem}"
if [ ! -f "$BRAINSTEM_HOME/brainstem.py" ]; then
    echo -e "${YELLOW}!${NC} No grail brainstem found at $BRAINSTEM_HOME"
    echo "  Install it first:"
    echo "    curl -fsSL https://kody-w.github.io/RAPP/installer/install.sh | bash"
    echo ""
fi

echo "   Fetching the generic hatcher from kody-w/twin-egg-hatcher..."
if ! curl -fsSL "$MIRROR_URL" -o "$HATCHER_NAME"; then
    echo -e "${RED}✗${NC} Download failed."
    echo "  Fallback: gh repo clone kody-w/twin-egg-hatcher"
    exit 1
fi
chmod +x "$HATCHER_NAME"
echo -e "${GREEN}✓${NC} Saved ${HATCHER_NAME}"
echo ""
echo "   Hatch @kody-w's twin (pulls identity from this repo on GitHub):"
echo -e "     ${CYAN}python ./${HATCHER_NAME} hatch --source kody-w/kody-w-twin${NC}"
echo ""
echo "   Or, if you cloned this repo, hatch from cwd:"
echo -e "     ${CYAN}python ./${HATCHER_NAME} hatch${NC}"
echo ""
echo "   Then from the global brainstem:"
echo -e "     ${CYAN}Twin(action='list')${NC}"
echo -e "     ${CYAN}Twin(action='boot', rappid_uuid='<rappid>')${NC}"
echo -e "     ${CYAN}Twin(action='chat', rappid_uuid='<rappid>', message='hi Kody')${NC}"
echo ""
echo -e "${GREEN}🧬 ready.${NC}"
