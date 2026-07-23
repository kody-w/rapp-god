#!/usr/bin/env python3
"""
RAPP Starter Template - Main Entry Point

A minimal boilerplate for building RAPP AI implementations.
Add your own agents and business logic to customize.
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Optional

# Ensure agents directory is in path
AGENTS_DIR = Path(__file__).parent / "agents"
sys.path.insert(0, str(AGENTS_DIR.parent))


class RAPPApplication:
    """
    Main RAPP Application class.

    Handles agent loading, conversation management, and AI orchestration.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or self._load_config()
        self.agents = {}
        self._load_agents()

    def _load_config(self) -> dict:
        """Load configuration from environment or config file."""
        return {
            "app_name": os.getenv("RAPP_APP_NAME", "RAPP Starter"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "debug": os.getenv("RAPP_DEBUG", "false").lower() == "true"
        }

    def _load_agents(self):
        """Dynamically load all agents from the agents directory."""
        if not AGENTS_DIR.exists():
            print(f"Creating agents directory: {AGENTS_DIR}")
            AGENTS_DIR.mkdir(parents=True, exist_ok=True)
            return

        for agent_file in AGENTS_DIR.glob("*_agent.py"):
            if agent_file.name.startswith("_") or agent_file.name == "basic_agent.py":
                continue

            try:
                self._load_agent_file(agent_file)
            except Exception as e:
                print(f"Warning: Failed to load {agent_file.name}: {e}")

    def _load_agent_file(self, agent_file: Path):
        """Load a single agent file."""
        spec = importlib.util.spec_from_file_location(
            agent_file.stem,
            agent_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find agent class in module
        for name, obj in module.__dict__.items():
            if (isinstance(obj, type) and
                name.endswith("Agent") and
                name != "BasicAgent" and
                hasattr(obj, "perform")):
                agent_instance = obj()
                self.agents[agent_instance.name] = agent_instance
                print(f"  Loaded: {agent_instance.name}")

    def get_agent_definitions(self) -> list:
        """Get function definitions for all loaded agents."""
        return [
            agent.get_function_definition()
            for agent in self.agents.values()
        ]

    def execute_agent(self, agent_name: str, **kwargs) -> str:
        """Execute a specific agent with given parameters."""
        if agent_name not in self.agents:
            return f"Error: Agent '{agent_name}' not found"

        return self.agents[agent_name].perform(**kwargs)

    def list_agents(self) -> list:
        """List all loaded agents."""
        return [
            {
                "name": agent.name,
                "description": agent.metadata.get("description", "")
            }
            for agent in self.agents.values()
        ]

    def run_interactive(self):
        """Run interactive chat loop."""
        print(f"\n{'='*50}")
        print(f"  {self.config['app_name']}")
        print(f"  Loaded {len(self.agents)} agent(s)")
        print(f"{'='*50}\n")

        if not self.agents:
            print("No agents loaded. Add agents to the 'agents/' directory.")
            print("Example: Copy agents from RAPP Store using 'rapp-hub deps add <agent_id>'")
            return

        print("Available agents:")
        for agent in self.list_agents():
            print(f"  - {agent['name']}: {agent['description'][:50]}...")

        print("\nType 'quit' to exit, 'agents' to list agents\n")

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() == 'quit':
                    print("Goodbye!")
                    break

                if user_input.lower() == 'agents':
                    for agent in self.list_agents():
                        print(f"  {agent['name']}: {agent['description']}")
                    continue

                # Simple agent routing - extend this with AI for production
                response = self._route_request(user_input)
                print(f"\nAssistant: {response}\n")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def _route_request(self, user_input: str) -> str:
        """Route user request to appropriate agent."""
        # Simple keyword-based routing - replace with AI in production
        user_lower = user_input.lower()

        for agent in self.agents.values():
            agent_name_lower = agent.name.lower()
            if agent_name_lower in user_lower:
                return agent.perform(action="help", request=user_input)

        # Default response
        agent_names = ", ".join(self.agents.keys())
        return f"I have these agents available: {agent_names}. Try mentioning one by name!"


def main():
    """Main entry point."""
    print("Starting RAPP Application...")

    app = RAPPApplication()
    app.run_interactive()


if __name__ == "__main__":
    main()
