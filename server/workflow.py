import os
import re
import json
import time
import subprocess
import logging
import asyncio
from typing import Optional, Iterator, AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent

GENERATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
ESBUILD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "node_modules", ".bin", "esbuild")

# Store captured data during tool calls
_captured_data = {}

# In-memory session store: session_id -> agent_instance
ACTIVE_SESSIONS = {}

@tool
def create_widget(title: str, code: str, width: int = 2, height: int = 2) -> str:
    """
    Creates and deploys a web widget. Use this tool to build apps, dashboards, or visualizations.
    
    Args:
        title: The display title of the widget.
        code: The complete React component code string.
        width: Width in grid units (1-4, default 2).
        height: Height in grid units (1-4, default 2).
    """
    global _captured_data
    _captured_data["title"] = title
    _captured_data["code"] = code
    _captured_data["width"] = width
    _captured_data["height"] = height
    return "Success: Widget captured for bundling."

class WidgetFlow:
    model_id: str = os.getenv("OPENAI_MODEL_NAME", "glm-4.7")
    
    def __init__(self, **kwargs):
        if "model_id" in kwargs:
            self.model_id = kwargs.pop("model_id")
        
        if not os.path.exists(GENERATED_DIR):
            os.makedirs(GENERATED_DIR)

    async def run(self, prompt: str, session_id: str = None) -> AsyncIterator[str]:
        # Reset capture
        global _captured_data
        _captured_data = {}

        yield json.dumps({"type": "log", "payload": f"Starting DeepAgent Flow for: {prompt}"})
        
        # Initialize LangChain Model
        # GLM API Compatibility
        model = ChatOpenAI(
            model=self.model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            streaming=True
        )

        from agent import INSTRUCTIONS
        
        # Session Persistence Logic
        agent = None
        if session_id and session_id in ACTIVE_SESSIONS:
            agent = ACTIVE_SESSIONS[session_id]
            yield json.dumps({"type": "log", "payload": f"Restored session: {session_id}"})
        else:
            # Initialize DeepAgent
            agent = create_deep_agent(
                model=model,
                tools=[create_widget],
                system_prompt=INSTRUCTIONS,
                name="deep-widget-agent"
            )
            if session_id:
                ACTIVE_SESSIONS[session_id] = agent
                yield json.dumps({"type": "log", "payload": f"Created new session: {session_id}"})
        
        yield json.dumps({"type": "log", "payload": "Agent initialized. Streaming response..."})

        try:
            # Run the agent stream
            async for chunk in agent.astream({"messages": [{"role": "user", "content": prompt}]}):
                # Handle Messages (Tokens/Text)
                if hasattr(chunk, "messages") and chunk["messages"]:
                    for msg in chunk["messages"]:
                        # We might get full message objects or deltas depending on DeepAgent version
                        # Check content
                        if hasattr(msg, "content") and msg.content:
                             yield json.dumps({"type": "chunk", "payload": msg.content})
                
                # Handle Todos/Logs
                if "todos" in chunk and chunk["todos"]:
                    for todo in chunk["todos"]:
                        yield json.dumps({"type": "log", "payload": f"Plan: {todo}"})

            # Check capture
            if _captured_data:
                yield json.dumps({"type": "log", "payload": "Widget tool called. Bundling..."})
                manifest = self.bundle_widget(
                    _captured_data.get("title", "Generated Widget"),
                    _captured_data.get("code", ""),
                    _captured_data.get("width", 2),
                    _captured_data.get("height", 2)
                )
                if manifest:
                    yield json.dumps({"type": "manifest", "payload": json.dumps(manifest)})
                    yield json.dumps({"type": "log", "payload": "Widget bundled successfully."})
                else:
                    yield json.dumps({"type": "error", "payload": "Bundling failed."})
            else:
                 yield json.dumps({"type": "log", "payload": "No widget generated."})
                 
        except Exception as e:
            logging.error(f"DeepAgent Error: {e}")
            yield json.dumps({"type": "error", "payload": str(e)})


    def bundle_widget(self, title: str, code: str, width: int, height: int) -> Optional[dict]:
        try:
            slug = re.sub(r'[^a-z0-9]', '', title.lower()[:20])
            timestamp = int(time.time())
            widget_id = f"{timestamp}_{slug}"
            
            # Create a widget-specific directory
            widget_dir = os.path.join(GENERATED_DIR, widget_id)
            if not os.path.exists(widget_dir):
                os.makedirs(widget_dir)
            
            jsx_file = os.path.join(widget_dir, "index.jsx")
            js_file = os.path.join(widget_dir, "index.js")
            html_file = os.path.join(widget_dir, "index.html")

            # Strip React imports to rely on Global React from CDN
            code = re.sub(r"import\s+.*?from\s+['\"]react['\"];?", "", code)
            code = re.sub(r"import\s+.*?from\s+['\"]react-dom['\"];?", "", code)
            
            # Ensure there is a default export if we are bundling
            if "export default" not in code:
                # Try to find a component name
                comp_match = re.search(r"(?:const|function)\s+([A-Z]\w+)", code)
                if comp_match:
                    code += f"\nexport default {comp_match.group(1)};"
                else:
                    pass

            with open(jsx_file, "w") as f:
                f.write(code)

            # Run esbuild
            cmd = [
                ESBUILD_PATH,
                jsx_file,
                "--bundle",
                "--minify",
                "--format=iife",
                "--global-name=WidgetComponent",
                "--outfile=" + js_file,
                "--loader:.jsx=jsx"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"esbuild error: {result.stderr}")
                return None

            # Generate HTML Host
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <title>{title}</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: transparent; }}
        #root {{ width: 100vw; height: 100vh; }}
    </style>
</head>
<body>
    <div id="root"></div>
    <script src="./index.js"></script>
    <script>
        const root = ReactDOM.createRoot(document.getElementById('root'));
        const Component = window.WidgetComponent.default || window.WidgetComponent;
        root.render(React.createElement(Component));
    </script>
</body>
</html>
"""
            with open(html_file, "w") as f:
                f.write(html_content)

            return {
                "id": widget_id,
                "title": title,
                "dimensions": {"w": width, "h": height},
                "code": code,
                "url": f"/generated/{widget_id}/index.html"
            }

        except Exception as e:
            logging.error(f"Bundling error: {str(e)}")
            return None
