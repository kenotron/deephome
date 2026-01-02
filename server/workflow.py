import os
import re
import json
import time
import subprocess
import logging
from typing import Optional, Iterator
from agno.workflow import Workflow
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from schema import WidgetManifest, WidgetDimensions

GENERATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
ESBUILD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "node_modules", ".bin", "esbuild")

class WidgetFlow(Workflow):
    model_id: str = os.getenv("OPENAI_MODEL_NAME", "glm-4.7")
    
    def __init__(self, **kwargs):
        if "model_id" in kwargs:
            self.model_id = kwargs.pop("model_id")
        super().__init__(**kwargs)
        if not os.path.exists(GENERATED_DIR):
            os.makedirs(GENERATED_DIR)

    def run(self, prompt: str) -> Iterator[str]:
        # This workflow will yield status updates and finally the manifest
        yield json.dumps({"type": "log", "payload": f"Starting WidgetFlow for: {prompt}"})
        
        # Step 1: Generate JSX using Agent
        yield json.dumps({"type": "log", "payload": "Generating JSX code..."})
        
        widget_data = self.generate_jsx(prompt)
        if not widget_data:
            yield json.dumps({"type": "error", "payload": "Failed to generate JSX code."})
            return

        title = widget_data.get("title", "Generated Widget")
        code = widget_data.get("code", "")
        width = widget_data.get("width", 2)
        height = widget_data.get("height", 2)

        yield json.dumps({"type": "log", "payload": f"JSX generated for '{title}'. Bundling..."})

        # Step 2: Bundle using esbuild
        manifest = self.bundle_widget(title, code, width, height)
        
        if manifest:
            yield json.dumps({"type": "manifest", "payload": json.dumps(manifest)})
            yield json.dumps({"type": "log", "payload": "Widget bundled and ready."})
        else:
            yield json.dumps({"type": "error", "payload": "Failed to bundle widget."})

    def generate_jsx(self, prompt: str) -> Optional[dict]:
        from agent import INSTRUCTIONS
        
        # We'll use a local queue/storage to capture the tool call from the agent
        captured_data = {}

        def create_widget_tool(title: str, code: str, width: int = 2, height: int = 2):
            captured_data["title"] = title
            captured_data["code"] = code
            captured_data["width"] = width
            captured_data["height"] = height
            return "Success: Widget captured for bundling."

        agent = Agent(
            model=OpenAIChat(id=self.model_id),
            tools=[DuckDuckGoTools(), create_widget_tool],
            debug_mode=True,
            markdown=False
        )

        full_prompt = f"{INSTRUCTIONS}\n\nUser Request: {prompt}"
        response = agent.run(full_prompt)
        
        # If the tool wasn't called, try to extract code from response content
        if not captured_data and response.content:
            # Simple regex to extract JSX from code blocks
            match = re.search(r"```jsx\n(.*?)\n```", response.content, re.DOTALL)
            if match:
                captured_data["code"] = match.group(1)
                captured_data["title"] = "Generated Widget"
            else:
                captured_data["code"] = response.content
                captured_data["title"] = "Generated Widget"
        
        return captured_data if "code" in captured_data else None

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

            # Write JSX with React import if missing
            if "import React" not in code and "from 'react'" not in code:
                code = "import React from 'react';\n" + code
            
            # Ensure there is a default export if we are bundling
            if "export default" not in code:
                # Try to find a component name
                comp_match = re.search(r"(?:const|function)\s+([A-Z]\w+)", code)
                if comp_match:
                    code += f"\nexport default {comp_match.group(1)};"
                else:
                    # Fallback or error? Let's hope the agent follows instructions.
                    pass

            with open(jsx_file, "w") as f:
                f.write(code)

            # Run esbuild
            # We treat 'react' and 'react-dom' as globals provided by the HTML host
            cmd = [
                ESBUILD_PATH,
                jsx_file,
                "--bundle",
                "--minify",
                "--format=iife",
                "--global-name=WidgetComponent",
                "--outfile=" + js_file,
                "--external:react",
                "--external:react-dom",
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
    <script src="https://unpkg.com/react@19/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@19/umd/react-dom.production.min.js"></script>
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
        // esbuild configured with --global-name=WidgetComponent
        // The bundle will be an IIFE that sets window.WidgetComponent to the default export
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
