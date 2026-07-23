#!/bin/bash
set -euo pipefail

# ── Local Near-Prod Build ──
#
# Builds the Jekyll site locally with production data pulled from GitHub.
# Tests your local branch changes against real live data without
# touching production.
#
# Architecture:
#   Local branch (your changes) + GitHub raw (production data) → static build
#   ├── Your changes are tested against real data
#   ├── Production data is read-only (fetched, not modified)
#   └── Nothing pushes to production
#
# Usage:
#   ./scripts/local-build.sh              # build + serve
#   ./scripts/local-build.sh --build-only # build without serving
#   ./scripts/local-build.sh --pull-data  # pull fresh production data then build

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_DIR/_site"
DATA_DIR="$PROJECT_DIR/_data/production"
PROD_BASE="https://raw.githubusercontent.com/kody-w"

echo "🦖 Digital Twin Local Build"
echo "   Branch: $(git branch --show-current)"
echo "   Mode: near-prod testing"
echo ""

# ── Pull production data from GitHub raw ──
pull_production_data() {
  echo "📥 Pulling production data from GitHub..."
  mkdir -p "$DATA_DIR"

  # Rappterbook agent data (public production data)
  echo "   → rappterbook agents..."
  curl -sL "$PROD_BASE/rappterbook/main/data/agents.json" -o "$DATA_DIR/rappterbook_agents.json" 2>/dev/null || echo "     (skipped — not available)"

  # Rappterbook social graph
  echo "   → rappterbook social graph..."
  curl -sL "$PROD_BASE/rappterbook/main/data/social-graph.json" -o "$DATA_DIR/rappterbook_social.json" 2>/dev/null || echo "     (skipped)"

  # OpenRappter blog posts (production versions)
  echo "   → openrappter blog posts..."
  curl -sL "$PROD_BASE/openrappter/main/docs/blog/ai-2-0-the-moment-agents-stopped-asking-permission.md" -o "$DATA_DIR/blog_ai_2_0.md" 2>/dev/null || echo "     (skipped)"

  # Edge sync manifest (if published)
  echo "   → edge sync manifest..."
  curl -sL "$PROD_BASE/openrappter/main/docs/edge/manifest.json" -o "$DATA_DIR/edge_manifest.json" 2>/dev/null || echo "     (skipped)"

  echo "✅ Production data pulled to _data/production/"
  echo ""
}

# ── Build Jekyll locally ──
build_site() {
  echo "🔨 Building Jekyll site..."

  # Set environment to distinguish local builds
  export JEKYLL_ENV=local-neartest

  # Build with strict front matter to catch errors early
  if command -v bundle &>/dev/null; then
    bundle exec jekyll build --strict_front_matter 2>&1
  else
    jekyll build 2>&1
  fi

  # Count output
  HTML_COUNT=$(find "$BUILD_DIR" -name '*.html' | wc -l | tr -d ' ')
  echo "✅ Built: $HTML_COUNT HTML files in _site/"
  echo ""

  # Safety check: scan for PII
  echo "🔒 PII scan..."
  PII_FOUND=0
  if grep -rE '[a-zA-Z0-9._%+-]+@(icloud|me|mac)\.com' "$BUILD_DIR" --include='*.html' -l 2>/dev/null | grep -v 'example\|test' | head -3; then
    echo "⚠️  Possible PII found in built files (check above)"
    PII_FOUND=1
  fi
  if [ $PII_FOUND -eq 0 ]; then
    echo "✅ No PII detected"
  fi
  echo ""
}

# ── Serve locally ──
serve_site() {
  echo "🌐 Serving at http://localhost:4000"
  echo "   Press Ctrl+C to stop"
  echo ""

  if command -v bundle &>/dev/null; then
    bundle exec jekyll serve --livereload 2>&1
  else
    jekyll serve --livereload 2>&1
  fi
}

# ── Main ──
cd "$PROJECT_DIR"

case "${1:-}" in
  --pull-data)
    pull_production_data
    build_site
    serve_site
    ;;
  --build-only)
    build_site
    ;;
  *)
    build_site
    serve_site
    ;;
esac
