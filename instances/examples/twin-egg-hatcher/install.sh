#!/usr/bin/env bash
set -e

# twin-egg-hatcher installer (public mirror, no auth required)
# Downloads the generic single-file hatcher into the current folder.
#
#   curl -fsSL https://raw.githubusercontent.com/kody-w/twin-egg-hatcher/main/install.sh | bash
#
# Then hatch any twin:
#
#   python ./twin_egg_hatcher_agent.py hatch --source kody-w/heimdall
#   python ./twin_egg_hatcher_agent.py hatch --egg ~/Downloads/twin.egg
#   cd <cloned twin repo> && python ./twin_egg_hatcher_agent.py hatch

REPO_BRANCH="${TWIN_EGG_HATCHER_BRANCH:-main}"
HATCHER_NAME="twin_egg_hatcher_agent.py"
RAW_URL="https://raw.githubusercontent.com/kody-w/twin-egg-hatcher/${REPO_BRANCH}/${HATCHER_NAME}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo ""
echo -e "${CYAN}🧬 twin-egg-hatcher${NC}"
echo "   Generic single-file twin egg hatcher"
echo ""

# Sanity: brainstem present?
BRAINSTEM_HOME="${BRAINSTEM_HOME:-$HOME/.brainstem}"
if [ ! -f "$BRAINSTEM_HOME/brainstem.py" ]; then
    echo -e "${YELLOW}!${NC} No grail brainstem found at $BRAINSTEM_HOME"
    echo "  Install it first:"
    echo "    curl -fsSL https://kody-w.github.io/RAPP/installer/install.sh | bash"
    echo ""
fi

echo "   Fetching ${HATCHER_NAME}..."
if ! curl -fsSL "$RAW_URL" -o "$HATCHER_NAME"; then
    echo -e "${RED}✗${NC} Download failed."
    echo "  Fallback: gh repo clone kody-w/twin-egg-hatcher"
    exit 1
fi

chmod +x "$HATCHER_NAME"
echo -e "${GREEN}✓${NC} Saved to ./${HATCHER_NAME}"
echo ""
echo "   Hatch any twin (cwd, public repo, or .egg):"
echo -e "     ${CYAN}python ./${HATCHER_NAME} hatch --source kody-w/heimdall${NC}"
echo -e "     ${CYAN}python ./${HATCHER_NAME} hatch --egg ~/Downloads/twin.egg${NC}"
echo -e "     ${CYAN}cd <cloned twin repo> && python ./${HATCHER_NAME} hatch${NC}"
echo ""
echo "   Then from the global brainstem:"
echo -e "     ${CYAN}Twin(action='list')${NC}"
echo -e "     ${CYAN}Twin(action='boot', rappid_uuid='<rappid>')${NC}"
echo -e "     ${CYAN}Twin(action='chat', rappid_uuid='<rappid>', message='hello')${NC}"
echo ""
echo -e "${GREEN}🧬 ready.${NC}"
