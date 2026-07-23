#!/usr/bin/env python3
"""
RAPP Hub CLI - Command line interface for RAPP ecosystem

Commands:
  rapp-hub init <name>       - Initialize new RAPP project from template
  rapp-hub deps install      - Install RAPP Store dependencies
  rapp-hub deps add <id>     - Add agent/skill from RAPP Store
  rapp-hub publish           - Register your implementation in RAPP Hub
  rapp-hub browse            - Browse RAPP Hub implementations
  rapp-hub search <query>    - Search implementations
  rapp-hub install <id>      - Clone and setup an implementation
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

# Try to import httpx, fall back to urllib
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_HTTPX = False


# URLs
RAPP_HUB_MANIFEST = "https://raw.githubusercontent.com/kody-w/RAPP_Hub/main/manifest.json"
RAPP_STORE_MANIFEST = "https://raw.githubusercontent.com/kody-w/RAPP_Store/main/manifest.json"
RAPP_HUB_REPO = "https://github.com/kody-w/RAPP_Hub"
STARTER_TEMPLATE_PATH = "implementations/rapp-starter-template"


def fetch_url(url: str) -> str:
    """Fetch content from URL."""
    if HAS_HTTPX:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    else:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode('utf-8')


def fetch_json(url: str) -> dict:
    """Fetch and parse JSON from URL."""
    return json.loads(fetch_url(url))


class RAPPHubCLI:
    """RAPP Hub Command Line Interface."""

    def __init__(self):
        self.hub_manifest = None
        self.store_manifest = None

    def _load_hub_manifest(self):
        """Load RAPP Hub manifest."""
        if not self.hub_manifest:
            self.hub_manifest = fetch_json(RAPP_HUB_MANIFEST)
        return self.hub_manifest

    def _load_store_manifest(self):
        """Load RAPP Store manifest."""
        if not self.store_manifest:
            self.store_manifest = fetch_json(RAPP_STORE_MANIFEST)
        return self.store_manifest

    def _load_local_rapp_json(self) -> Optional[dict]:
        """Load local rapp.json if exists."""
        rapp_json_path = Path.cwd() / "rapp.json"
        if rapp_json_path.exists():
            with open(rapp_json_path) as f:
                return json.load(f)
        return None

    def _save_local_rapp_json(self, data: dict):
        """Save local rapp.json."""
        rapp_json_path = Path.cwd() / "rapp.json"
        with open(rapp_json_path, 'w') as f:
            json.dump(data, f, indent=2)

    # =========================================================================
    # INIT - Create new project from template
    # =========================================================================
    def init(self, name: str, template: str = "starter"):
        """Initialize a new RAPP project from template."""
        print(f"🚀 Initializing new RAPP project: {name}")

        target_dir = Path.cwd() / name

        if target_dir.exists():
            print(f"❌ Error: Directory '{name}' already exists")
            return False

        # Clone RAPP Hub repo to get template
        print("📥 Downloading template...")
        temp_dir = Path.cwd() / f".rapp_temp_{datetime.now().timestamp()}"

        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", RAPP_HUB_REPO, str(temp_dir)],
                check=True,
                capture_output=True
            )

            # Copy template to target
            template_source = temp_dir / STARTER_TEMPLATE_PATH
            if not template_source.exists():
                print(f"❌ Error: Template not found at {STARTER_TEMPLATE_PATH}")
                return False

            shutil.copytree(template_source, target_dir)

            # Update rapp.json with project name
            rapp_json_path = target_dir / "rapp.json"
            if rapp_json_path.exists():
                with open(rapp_json_path) as f:
                    rapp_data = json.load(f)

                rapp_data["name"] = name
                rapp_data["description"] = f"RAPP implementation: {name}"
                rapp_data["repository"] = ""  # User will fill in
                rapp_data["author"] = os.getenv("USER", "")

                with open(rapp_json_path, 'w') as f:
                    json.dump(rapp_data, f, indent=2)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=target_dir, capture_output=True)

            print(f"✅ Project created: {target_dir}")
            print(f"\nNext steps:")
            print(f"  cd {name}")
            print(f"  pip install -r requirements.txt")
            print(f"  python main.py")
            print(f"\nAdd agents from RAPP Store:")
            print(f"  rapp-hub deps add pdf_processor_agent")
            print(f"\nWhen ready to publish:")
            print(f"  1. Push to GitHub")
            print(f"  2. Run: rapp-hub publish")

            return True

        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    # =========================================================================
    # DEPS - Dependency management
    # =========================================================================
    def deps_install(self):
        """Install all dependencies from rapp.json."""
        rapp_data = self._load_local_rapp_json()
        if not rapp_data:
            print("❌ No rapp.json found. Run 'rapp-hub init <name>' first.")
            return False

        deps = rapp_data.get("dependencies", {})
        rapp_store_deps = deps.get("rapp_store", {})
        agents = rapp_store_deps.get("agents", [])
        skills = rapp_store_deps.get("skills", [])
        python_deps = deps.get("python", [])

        print("📦 Installing dependencies...")

        # Install Python packages
        if python_deps:
            print(f"\n🐍 Python packages: {', '.join(python_deps)}")
            subprocess.run([sys.executable, "-m", "pip", "install"] + python_deps)

        # Install RAPP Store agents
        if agents:
            print(f"\n🤖 RAPP Store agents:")
            for agent in agents:
                agent_id = agent.split("@")[0]  # Remove version
                self.deps_add(agent_id, "agent")

        # Install RAPP Store skills
        if skills:
            print(f"\n✨ RAPP Store skills:")
            for skill in skills:
                skill_id = skill.split("@")[0]  # Remove version
                self.deps_add(skill_id, "skill")

        print("\n✅ Dependencies installed!")
        return True

    def deps_add(self, item_id: str, item_type: str = "agent"):
        """Add an agent or skill from RAPP Store."""
        store = self._load_store_manifest()

        # Find item in store
        if item_type == "agent":
            items = store.get("agents", [])
            target_dir = Path.cwd() / "agents"
        else:
            items = store.get("skills", [])
            target_dir = Path.cwd() / "skills"

        item = next((i for i in items if i["id"] == item_id), None)

        if not item:
            print(f"❌ {item_type.capitalize()} '{item_id}' not found in RAPP Store")
            return False

        print(f"📥 Installing {item['name']}...")

        # Fetch the item
        raw_base = store["protocol"]["raw_base"]

        try:
            if item_type == "agent":
                url = f"{raw_base}/{item['path']}/{item['filename']}"
                content = fetch_url(url)

                target_dir.mkdir(parents=True, exist_ok=True)
                target_file = target_dir / item["filename"]

                with open(target_file, 'w') as f:
                    f.write(content)

                print(f"✅ Installed: {target_file}")

            else:  # skill
                skill_dir = target_dir / item_id
                skill_dir.mkdir(parents=True, exist_ok=True)

                # Fetch SKILL.md
                url = f"{raw_base}/{item['path']}/SKILL.md"
                content = fetch_url(url)

                with open(skill_dir / "SKILL.md", 'w') as f:
                    f.write(content)

                print(f"✅ Installed: {skill_dir}/SKILL.md")

            # Update rapp.json
            rapp_data = self._load_local_rapp_json()
            if rapp_data:
                if "dependencies" not in rapp_data:
                    rapp_data["dependencies"] = {}
                if "rapp_store" not in rapp_data["dependencies"]:
                    rapp_data["dependencies"]["rapp_store"] = {"agents": [], "skills": []}

                list_key = "agents" if item_type == "agent" else "skills"
                if item_id not in rapp_data["dependencies"]["rapp_store"][list_key]:
                    rapp_data["dependencies"]["rapp_store"][list_key].append(item_id)
                    self._save_local_rapp_json(rapp_data)
                    print(f"📝 Updated rapp.json")

            return True

        except Exception as e:
            print(f"❌ Error installing {item_id}: {e}")
            return False

    # =========================================================================
    # PUBLISH - Register implementation in RAPP Hub
    # =========================================================================
    def publish(self):
        """Generate registration entry for RAPP Hub."""
        rapp_data = self._load_local_rapp_json()
        if not rapp_data:
            print("❌ No rapp.json found. Run 'rapp-hub init <name>' first.")
            return False

        # Validate required fields
        required = ["name", "description", "repository"]
        missing = [f for f in required if not rapp_data.get(f)]
        if missing:
            print(f"❌ Missing required fields in rapp.json: {', '.join(missing)}")
            print("\nPlease update your rapp.json with:")
            for field in missing:
                print(f'  "{field}": "your-value"')
            return False

        if not rapp_data.get("repository"):
            print("❌ Please set 'repository' in rapp.json to your GitHub repo URL")
            return False

        # Generate RAPP Hub entry
        entry = {
            "id": rapp_data["name"].lower().replace(" ", "-"),
            "name": rapp_data["name"],
            "description": rapp_data["description"],
            "version": rapp_data.get("version", "1.0.0"),
            "category": rapp_data.get("category", "starter"),
            "author": rapp_data.get("author", ""),
            "license": rapp_data.get("license", "Apache-2.0"),
            "repo": rapp_data["repository"],
            "path": ".",
            "branch": "main",
            "icon": rapp_data.get("icon", "🤖"),
            "tags": rapp_data.get("tags", []),
            "features": rapp_data.get("features", []),
            "stack": rapp_data.get("stack", {
                "runtime": "python",
                "version": "3.11",
                "platform": "standalone",
                "ai": "openai"
            }),
            "dependencies": rapp_data.get("dependencies", {}),
            "quickstart": rapp_data.get("scripts", {
                "clone": f"git clone {rapp_data['repository']}",
                "setup": "pip install -r requirements.txt",
                "run": "python main.py"
            })
        }

        print("✅ Generated RAPP Hub entry:\n")
        print(json.dumps(entry, indent=2))

        print("\n" + "="*60)
        print("📋 TO REGISTER YOUR IMPLEMENTATION:")
        print("="*60)
        print("""
Option 1: Pull Request (Recommended)
  1. Fork https://github.com/kody-w/RAPP_Hub
  2. Add this entry to manifest.json 'implementations' array
  3. Submit a Pull Request

Option 2: Self-Registration
  1. Create a file: .rapp-hub.json in your repo root
  2. Paste this entry into it
  3. Your repo will be discoverable via direct URL

Option 3: Issue Request
  1. Open an issue at https://github.com/kody-w/RAPP_Hub/issues
  2. Paste this entry and request registration
""")

        # Also save to local file for easy copy
        with open(".rapp-hub-entry.json", 'w') as f:
            json.dump(entry, f, indent=2)
        print("💾 Entry saved to: .rapp-hub-entry.json")

        return True

    # =========================================================================
    # BROWSE - List implementations
    # =========================================================================
    def browse(self, category: str = None):
        """Browse RAPP Hub implementations."""
        hub = self._load_hub_manifest()
        implementations = hub.get("implementations", [])

        if category:
            implementations = [i for i in implementations if i.get("category") == category]

        print(f"\n🏠 RAPP Hub - {len(implementations)} implementation(s)\n")

        for impl in implementations:
            deps = impl.get("dependencies", {}).get("rapp_store", {})
            agent_count = len(deps.get("agents", []))
            skill_count = len(deps.get("skills", []))
            dep_info = f"({agent_count} agents, {skill_count} skills)" if agent_count or skill_count else ""

            print(f"{impl.get('icon', '🤖')} {impl['name']} (v{impl.get('version', '1.0.0')}) {dep_info}")
            print(f"   {impl['description'][:70]}...")
            print(f"   ID: {impl['id']} | Category: {impl.get('category', 'N/A')}")
            print()

        print(f"Install with: rapp-hub install <id>")
        print(f"Web UI: https://kody-w.github.io/RAPP_Hub/")

    # =========================================================================
    # SEARCH - Search implementations
    # =========================================================================
    def search(self, query: str):
        """Search RAPP Hub implementations."""
        hub = self._load_hub_manifest()
        implementations = hub.get("implementations", [])
        query_lower = query.lower()

        matches = []
        for impl in implementations:
            score = 0
            if query_lower in impl["name"].lower():
                score += 3
            if query_lower in impl["description"].lower():
                score += 1
            if any(query_lower in tag.lower() for tag in impl.get("tags", [])):
                score += 2
            if score > 0:
                matches.append((impl, score))

        matches.sort(key=lambda x: x[1], reverse=True)

        print(f"\n🔍 Search results for '{query}': {len(matches)} found\n")

        for impl, _ in matches:
            print(f"{impl.get('icon', '🤖')} {impl['name']}")
            print(f"   {impl['description'][:70]}...")
            print(f"   ID: {impl['id']}")
            print()

    # =========================================================================
    # INSTALL - Clone and setup implementation
    # =========================================================================
    def install(self, impl_id: str):
        """Clone and setup a RAPP Hub implementation."""
        hub = self._load_hub_manifest()
        implementations = hub.get("implementations", [])

        impl = next((i for i in implementations if i["id"] == impl_id), None)
        if not impl:
            print(f"❌ Implementation '{impl_id}' not found")
            return False

        print(f"📥 Installing {impl['name']}...")

        # Clone repo
        repo_url = impl["repo"]
        target_dir = impl_id

        if Path(target_dir).exists():
            print(f"❌ Directory '{target_dir}' already exists")
            return False

        subprocess.run(["git", "clone", repo_url, target_dir], check=True)

        # Navigate to implementation path if specified
        impl_path = Path(target_dir) / impl.get("path", ".")

        # Install dependencies
        print("\n📦 Installing dependencies...")
        os.chdir(impl_path)
        self.deps_install()

        print(f"\n✅ Installed: {impl['name']}")
        print(f"\nTo run:")
        print(f"  cd {impl_path}")
        if impl.get("quickstart", {}).get("run"):
            print(f"  {impl['quickstart']['run']}")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="RAPP Hub CLI - Manage RAPP AI implementations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rapp-hub init my-project          Create new project from template
  rapp-hub deps install             Install all dependencies
  rapp-hub deps add pdf_processor   Add agent from RAPP Store
  rapp-hub publish                  Generate RAPP Hub registration
  rapp-hub browse                   List all implementations
  rapp-hub search copilot           Search implementations
  rapp-hub install copilot-entra    Clone and setup implementation

Web UI: https://kody-w.github.io/RAPP_Hub/
Agents: https://kody-w.github.io/RAPP_Store/
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize new RAPP project")
    init_parser.add_argument("name", help="Project name")
    init_parser.add_argument("--template", default="starter", help="Template to use")

    # deps
    deps_parser = subparsers.add_parser("deps", help="Dependency management")
    deps_sub = deps_parser.add_subparsers(dest="deps_command")

    deps_install = deps_sub.add_parser("install", help="Install all dependencies")
    deps_add = deps_sub.add_parser("add", help="Add dependency from RAPP Store")
    deps_add.add_argument("item_id", help="Agent or skill ID")
    deps_add.add_argument("--type", choices=["agent", "skill"], default="agent")

    # publish
    subparsers.add_parser("publish", help="Generate RAPP Hub registration")

    # browse
    browse_parser = subparsers.add_parser("browse", help="Browse implementations")
    browse_parser.add_argument("--category", help="Filter by category")

    # search
    search_parser = subparsers.add_parser("search", help="Search implementations")
    search_parser.add_argument("query", help="Search query")

    # install
    install_parser = subparsers.add_parser("install", help="Clone and setup implementation")
    install_parser.add_argument("impl_id", help="Implementation ID")

    args = parser.parse_args()
    cli = RAPPHubCLI()

    if args.command == "init":
        cli.init(args.name, args.template)
    elif args.command == "deps":
        if args.deps_command == "install":
            cli.deps_install()
        elif args.deps_command == "add":
            cli.deps_add(args.item_id, args.type)
        else:
            deps_parser.print_help()
    elif args.command == "publish":
        cli.publish()
    elif args.command == "browse":
        cli.browse(args.category)
    elif args.command == "search":
        cli.search(args.query)
    elif args.command == "install":
        cli.install(args.impl_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
