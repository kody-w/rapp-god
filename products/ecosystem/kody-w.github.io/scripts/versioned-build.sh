#!/bin/bash
set -euo pipefail

# ── Versioned Static Build System ──
#
# Every build creates an immutable snapshot. Roll back by pointing
# to a different version. Infinite canary builds per branch.
#
# Structure:
#   builds/
#   ├── manifest.json          ← index of all versions
#   ├── latest/                ← symlink to current production version
#   ├── v1.0.0/               ← immutable snapshot
#   ├── v1.0.1/               ← immutable snapshot
#   ├── canary/
#   │   ├── feature-x/        ← branch canary build
#   │   └── fix-layout/       ← branch canary build
#   └── snapshots/
#       ├── 2026-03-28T17-00/ ← timestamped snapshot
#       └── 2026-03-28T19-30/ ← timestamped snapshot
#
# Usage:
#   ./scripts/versioned-build.sh                    # auto-version from git
#   ./scripts/versioned-build.sh --version 1.2.0    # explicit version
#   ./scripts/versioned-build.sh --canary            # branch canary build
#   ./scripts/versioned-build.sh --snapshot          # timestamped snapshot
#   ./scripts/versioned-build.sh --rollback v1.0.0   # rollback to version
#   ./scripts/versioned-build.sh --list              # list all versions
#   ./scripts/versioned-build.sh --serve v1.0.0      # serve a specific version
#   ./scripts/versioned-build.sh --diff v1.0.0 v1.1.0 # diff two versions
#   ./scripts/versioned-build.sh --pull-data         # pull production data first

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUILDS_DIR="$PROJECT_DIR/builds"
MANIFEST="$BUILDS_DIR/manifest.json"
PROD_BASE="https://raw.githubusercontent.com/kody-w"

mkdir -p "$BUILDS_DIR/canary" "$BUILDS_DIR/snapshots"

# ── Helpers ──

get_branch() { git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || echo "detached"; }
get_commit() { git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown"; }
get_timestamp() { date -u +"%Y-%m-%dT%H-%M-%S"; }

auto_version() {
  # Count existing versioned builds to auto-increment
  local count=$(ls -d "$BUILDS_DIR"/v*.*.* 2>/dev/null | wc -l | tr -d ' ')
  local major=1
  local minor=0
  local patch=$count
  echo "${major}.${minor}.${patch}"
}

pull_production_data() {
  local data_dir="$PROJECT_DIR/_data/production"
  mkdir -p "$data_dir"
  echo "📥 Pulling production data..."
  curl -sL "$PROD_BASE/rappterbook/main/data/agents.json" -o "$data_dir/rappterbook_agents.json" 2>/dev/null || true
  curl -sL "$PROD_BASE/rappterbook/main/data/social-graph.json" -o "$data_dir/rappterbook_social.json" 2>/dev/null || true
  curl -sL "$PROD_BASE/openrappter/main/docs/blog/ai-2-0-the-moment-agents-stopped-asking-permission.md" -o "$data_dir/blog_ai_2_0.md" 2>/dev/null || true
  echo "✅ Production data refreshed"
}

build_jekyll() {
  local dest="$1"
  echo "🔨 Building Jekyll → $dest"
  cd "$PROJECT_DIR"

  if command -v bundle &>/dev/null && [ -f Gemfile ]; then
    JEKYLL_ENV=staging bundle exec jekyll build -d "$dest" --strict_front_matter 2>&1 || \
    jekyll build -d "$dest" 2>&1
  else
    jekyll build -d "$dest" 2>&1
  fi

  local count=$(find "$dest" -name '*.html' 2>/dev/null | wc -l | tr -d ' ')
  echo "   → $count HTML files"
}

pii_scan() {
  local dir="$1"
  echo "🔒 PII scan..."
  local found=$(grep -rlE '[a-zA-Z0-9._%+-]+@(icloud|me|mac)\.com' "$dir" --include='*.html' 2>/dev/null | grep -v 'example\|test' | wc -l | tr -d ' ')
  if [ "$found" -gt 0 ]; then
    echo "⚠️  $found files may contain PII"
  else
    echo "✅ Clean"
  fi
}

update_manifest() {
  local version="$1"
  local type="$2"  # release, canary, snapshot
  local path="$3"
  local branch=$(get_branch)
  local commit=$(get_commit)
  local timestamp=$(get_timestamp)
  local html_count=$(find "$path" -name '*.html' 2>/dev/null | wc -l | tr -d ' ')

  # Read existing manifest or create new
  if [ -f "$MANIFEST" ]; then
    local existing=$(cat "$MANIFEST")
  else
    local existing='{"versions":[]}'
  fi

  # Append new version entry using node (available on all dev machines)
  node -e "
    const m = $existing;
    m.versions.push({
      version: '$version',
      type: '$type',
      branch: '$branch',
      commit: '$commit',
      timestamp: '$timestamp',
      path: '$(basename "$path")',
      htmlFiles: $html_count,
      current: false
    });
    // Mark latest release as current
    if ('$type' === 'release') {
      m.versions.forEach(v => v.current = false);
      m.versions[m.versions.length - 1].current = true;
      m.latest = '$version';
    }
    m.updatedAt = '$timestamp';
    process.stdout.write(JSON.stringify(m, null, 2));
  " > "$MANIFEST"

  echo "📋 Manifest updated: $version ($type)"
}

# ── Commands ──

cmd_build() {
  local version="${1:-$(auto_version)}"
  local dest="$BUILDS_DIR/v${version}"

  if [ -d "$dest" ]; then
    echo "❌ Version v${version} already exists. Use a different version or --snapshot."
    exit 1
  fi

  build_jekyll "$dest"
  pii_scan "$dest"
  update_manifest "v${version}" "release" "$dest"

  # Update latest symlink
  rm -f "$BUILDS_DIR/latest"
  ln -sf "v${version}" "$BUILDS_DIR/latest"
  echo ""
  echo "✅ v${version} built and set as latest"
  echo "   Path: $dest"
  echo "   Serve: ./scripts/versioned-build.sh --serve v${version}"
}

cmd_canary() {
  local branch=$(get_branch | sed 's/[^a-zA-Z0-9._-]/-/g')
  local dest="$BUILDS_DIR/canary/${branch}"

  # Remove old canary for this branch
  rm -rf "$dest"

  build_jekyll "$dest"
  pii_scan "$dest"
  update_manifest "canary/${branch}" "canary" "$dest"
  echo ""
  echo "✅ Canary build for branch '${branch}'"
  echo "   Path: $dest"
  echo "   Serve: ./scripts/versioned-build.sh --serve canary/${branch}"
}

cmd_snapshot() {
  local ts=$(get_timestamp)
  local dest="$BUILDS_DIR/snapshots/${ts}"

  build_jekyll "$dest"
  pii_scan "$dest"
  update_manifest "snapshot/${ts}" "snapshot" "$dest"
  echo ""
  echo "✅ Snapshot: $ts"
  echo "   Path: $dest"
}

cmd_rollback() {
  local version="$1"
  local target="$BUILDS_DIR/${version}"

  if [ ! -d "$target" ]; then
    echo "❌ Version $version not found"
    echo "   Available: $(ls -d "$BUILDS_DIR"/v*.*.* 2>/dev/null | xargs -I{} basename {} | tr '\n' ' ')"
    exit 1
  fi

  rm -f "$BUILDS_DIR/latest"
  ln -sf "${version}" "$BUILDS_DIR/latest"

  # Update manifest
  node -e "
    const m = $(cat "$MANIFEST");
    m.versions.forEach(v => v.current = (v.path === '${version}'));
    m.latest = '${version}';
    m.updatedAt = '$(get_timestamp)';
    m.lastRollback = { to: '${version}', at: '$(get_timestamp)' };
    process.stdout.write(JSON.stringify(m, null, 2));
  " > "$MANIFEST"

  echo "✅ Rolled back to ${version}"
  echo "   latest → ${version}"
}

cmd_list() {
  echo "📦 Available builds:"
  echo ""

  if [ -f "$MANIFEST" ]; then
    node -e "
      const m = $(cat "$MANIFEST");
      const current = m.latest || '';
      for (const v of m.versions) {
        const marker = v.current ? ' ← CURRENT' : '';
        const type = v.type.padEnd(8);
        console.log('  ' + type + ' ' + v.version.padEnd(24) + v.commit + '  ' + v.timestamp + marker);
      }
      console.log('');
      console.log('Total: ' + m.versions.length + ' builds');
      if (current) console.log('Current: ' + current);
    "
  else
    echo "  (no builds yet)"
  fi
}

cmd_serve() {
  local version="$1"
  local target="$BUILDS_DIR/${version}"

  if [ ! -d "$target" ]; then
    echo "❌ Version $version not found"
    exit 1
  fi

  local port="${2:-4000}"
  echo "🌐 Serving ${version} at http://localhost:${port}"
  echo "   Press Ctrl+C to stop"
  cd "$target"

  if command -v python3 &>/dev/null; then
    python3 -m http.server "$port"
  elif command -v npx &>/dev/null; then
    npx serve -p "$port" .
  else
    echo "Install python3 or npx to serve locally"
    exit 1
  fi
}

cmd_diff() {
  local v1="$1"
  local v2="$2"
  echo "📊 Diff: $v1 ↔ $v2"
  echo ""

  local d1="$BUILDS_DIR/$v1"
  local d2="$BUILDS_DIR/$v2"

  if [ ! -d "$d1" ] || [ ! -d "$d2" ]; then
    echo "❌ Both versions must exist"
    exit 1
  fi

  # Compare file counts
  local c1=$(find "$d1" -name '*.html' | wc -l | tr -d ' ')
  local c2=$(find "$d2" -name '*.html' | wc -l | tr -d ' ')
  echo "  HTML files: $v1=$c1, $v2=$c2 (delta: $((c2 - c1)))"

  # Compare file lists
  local added=$(diff <(cd "$d1" && find . -name '*.html' | sort) <(cd "$d2" && find . -name '*.html' | sort) | grep '^>' | wc -l | tr -d ' ')
  local removed=$(diff <(cd "$d1" && find . -name '*.html' | sort) <(cd "$d2" && find . -name '*.html' | sort) | grep '^<' | wc -l | tr -d ' ')
  echo "  Added: $added, Removed: $removed"

  # Size comparison
  local s1=$(du -sh "$d1" 2>/dev/null | cut -f1)
  local s2=$(du -sh "$d2" 2>/dev/null | cut -f1)
  echo "  Size: $v1=$s1, $v2=$s2"
}

# ── Main ──

cd "$PROJECT_DIR"

case "${1:-}" in
  --version)   cmd_build "${2:?Usage: --version X.Y.Z}" ;;
  --canary)    cmd_canary ;;
  --snapshot)  cmd_snapshot ;;
  --rollback)  cmd_rollback "${2:?Usage: --rollback vX.Y.Z}" ;;
  --list)      cmd_list ;;
  --serve)     cmd_serve "${2:?Usage: --serve vX.Y.Z}" "${3:-4000}" ;;
  --diff)      cmd_diff "${2:?Usage: --diff v1 v2}" "${3:?}" ;;
  --pull-data) pull_production_data; cmd_build "${2:-$(auto_version)}" ;;
  --help|-h)
    echo "Usage: versioned-build.sh [command]"
    echo ""
    echo "Commands:"
    echo "  (no args)         Auto-version build"
    echo "  --version X.Y.Z   Build with explicit version"
    echo "  --canary           Build canary for current branch"
    echo "  --snapshot         Timestamped snapshot"
    echo "  --rollback vX.Y.Z Point latest to a previous version"
    echo "  --list             List all builds"
    echo "  --serve vX.Y.Z    Serve a specific version locally"
    echo "  --diff v1 v2      Compare two versions"
    echo "  --pull-data        Pull production data then build"
    echo "  --help             This help"
    ;;
  *)           cmd_build "${1:-$(auto_version)}" ;;
esac
