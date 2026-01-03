import asyncio
import json
import os
import logging
from typing import Callable
from dotenv import load_dotenv
from workflow import WidgetFlow

load_dotenv()

# Setup Logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_debug.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(message)s')

# Design instructions are now imported by workflow.py
# But we keep a reference here if needed, or we can move them.
# For now, let's keep them here as a single source of truth for the system prompt.
INSTRUCTIONS = """
You are a helpful and friendly AI assistant for the home.
You have a specific skill: Generating interactive React widgets ("artifacts") to help the user.

CORE BEHAVIOR:
1. **Chat Naturally**: You can engage in normal conversation, answer questions, and help with tasks textually.
2. **Widget Skill**: ONLY generate a widget (use `create_widget`) when the user explicitly asks for a:
   - Visual, UI, Interface, Dashboard, Component, App, Tool, or "Widget".
   - Or when a visual representation is clearly the best way to answer (e.g. "show me a timer").
   - DO NOT generate a widget for simple text questions (e.g. "what is python?").

TECHNICAL RULES (for Widgets):
- Use `lucide-react` for icons.
- Use `tailwindcss` for styling.
- Components must be functional and interactive.

DESIGN REQUIREMENTS:
- **ALWAYS include a background color** - widgets sit directly on the canvas
- Use warm, earthy colors: sage green (#a3b18a), terracotta (#bc6c4b), mustard yellow, coral, etc.
- Add rounded corners (`rounded-xl` or `rounded-2xl`)
- Include subtle padding (`p-4` to `p-6`)
- NO borders, NO white backgrounds, NO shadows on the main container
- Each widget should have its own distinctive color scheme

LAYOUT BEST PRACTICES:
- **Calendars/Grids**: ALWAYS use CSS Grid.
  - Example: `<div className="grid grid-cols-7 gap-1">` for calendar days.
  - Example: `<div className="grid grid-cols-4 gap-2">` for calculator keys.
  - NEVER render these as a vertical list (`flex-col`).
- **Containers**: Use `w-full h-full flex flex-col` for the main wrapper.
- **Spacing**: Use adequate padding (`p-4` or `p-6`) to let the design breathe.
"""

async def generate_widget_stream(prompt: str, session_id: str = None):
    if not os.getenv("OPENAI_API_KEY"):
        yield ("error", "OPENAI_API_KEY not found.")
        return

    model_id = os.getenv("OPENAI_MODEL_NAME", "glm-4.7")
    flow = WidgetFlow(model_id=model_id)

    # Run the workflow
    async for result_json in flow.run(prompt, session_id=session_id):
        try:
            result = json.loads(result_json)
            yield (result["type"], result["payload"])
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON: {result_json}")
            yield ("error", "Internal JSON error")

    yield ("done", "stop")

def run_agent(prompt: str, callback: Callable[[str, str], None]):
    try:
        asyncio.run(_run_agent_sync_wrapper(prompt, callback))
    except Exception as e:
        callback("error", str(e))
        callback("done", "stop")

async def _run_agent_sync_wrapper(prompt: str, callback: Callable[[str, str], None]):
    async for event_type, payload in generate_widget_stream(prompt):
        callback(event_type, payload)
