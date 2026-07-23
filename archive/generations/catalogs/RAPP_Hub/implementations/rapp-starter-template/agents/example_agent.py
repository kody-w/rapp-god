"""
Example Agent - A simple starter agent to demonstrate the pattern

Replace this with your own agents or install from RAPP Store:
  rapp-hub deps add pdf_processor_agent
  rapp-hub deps add email_assistant_agent
"""

from agents.basic_agent import BasicAgent


class ExampleAgent(BasicAgent):
    """
    A simple example agent to demonstrate the RAPP agent pattern.

    This agent shows the basic structure - replace it with your own logic
    or install real agents from RAPP Store.
    """

    def __init__(self):
        self.name = 'Example'
        self.metadata = {
            "name": self.name,
            "description": "A simple example agent demonstrating the RAPP pattern. Replace with real agents from RAPP Store.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform: 'greet', 'help', 'echo'",
                        "enum": ["greet", "help", "echo"]
                    },
                    "message": {
                        "type": "string",
                        "description": "Message to echo (for 'echo' action)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name to greet (for 'greet' action)"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute the example agent action."""
        action = kwargs.get('action', 'help')

        if action == 'greet':
            name = kwargs.get('name', 'World')
            return f"Hello, {name}! Welcome to RAPP."

        elif action == 'echo':
            message = kwargs.get('message', '')
            if not message:
                return "Error: 'message' is required for echo action"
            return f"Echo: {message}"

        elif action == 'help':
            return """🚀 Example Agent Help

This is a starter agent to demonstrate the RAPP pattern.

**Available Actions:**
• greet - Say hello (optional: name parameter)
• echo - Echo back a message (required: message parameter)
• help - Show this help message

**Next Steps:**
1. Install real agents from RAPP Store:
   rapp-hub deps add pdf_processor_agent

2. Create your own agent:
   - Copy this file as a template
   - Implement your own perform() method
   - Add to the agents/ directory

**RAPP Store:** https://kody-w.github.io/RAPP_Store/
"""

        return f"Unknown action: {action}"
