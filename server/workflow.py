import os
import re
import json
import time
import subprocess
import logging
import asyncio
from typing import Optional, Iterator, AsyncIterator
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

GENERATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
ESBUILD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "node_modules", ".bin", "esbuild")
PROJECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects")

# In-memory session store: session_id -> { "history": [messages], "agent": agent, "project_path": str }
SESSION_STORE = {}

# Ensure projects directory exists
if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)

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

        # Initialize LangChain Model
        model = ChatOpenAI(
            model=self.model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            streaming=True,
        )

        from agent import INSTRUCTIONS

        # Session Persistence Logic
        agent = None
        history = []
        project_path = None

        if session_id:
            if session_id in SESSION_STORE:
                data = SESSION_STORE[session_id]
                agent = data["agent"]
                history = data["history"]
                project_path = data["project_path"]
            else:
                # Create a project directory for this session
                project_path = os.path.join(PROJECTS_DIR, f"session_{session_id}")
                if not os.path.exists(project_path):
                    os.makedirs(project_path)

                # Create agent with filesystem backend pointing to project directory
                backend = FilesystemBackend(root_dir=project_path, virtual_mode=True)

                agent = create_deep_agent(
                    model=model,
                    tools=[create_widget],
                    backend=backend,
                    # system_prompt=INSTRUCTIONS,
                    name="deep-widget-agent"
                )
                SESSION_STORE[session_id] = {
                    "agent": agent,
                    "history": [],
                    "project_path": project_path
                }
                history = SESSION_STORE[session_id]["history"]
        else:
            # No session - create temporary agent without persistence
            agent = create_deep_agent(
                model=model,
                tools=[create_widget],
                #system_prompt=INSTRUCTIONS,
                name="deep-widget-agent"
            )

        # Append User Message to History
        user_msg = {"role": "user", "content": prompt}
        history.append(user_msg)
        
        # Track Assistant Response for History
        assistant_content = ""
        assistant_tool_calls = []

        from langchain_core.messages import HumanMessage, AIMessage

        # Convert dict history to LangChain Message objects
        formatted_history = []
        for msg in history:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_history.append(AIMessage(content=msg["content"], tool_calls=msg.get("tool_calls", [])))

        try:
            # Run the agent stream with FULL HISTORY
            input_payload = {"messages": formatted_history}
            print(f"[DEBUG] Starting stream for {session_id}. History len: {len(history)}", flush=True)
            # print(f"[DEBUG] History content: {history}", flush=True)

            async for chunk in agent.astream(input_payload):
                # LangGraph/DeepAgents yields node updates.
                # Key "model" contains the LLM output.
                # Key "PatchToolCallsMiddleware..." contains input echo (ignore).

                # Check for model output (AIMessage)
                if isinstance(chunk, dict) and "model" in chunk:
                    model_data = chunk["model"]
                    if "messages" in model_data:
                        msgs = model_data["messages"]
                        for msg in msgs:
                            try:
                                # Check for content_blocks (structured content)
                                content_blocks = getattr(msg, "content_blocks", None)
                                tool_calls = getattr(msg, "tool_calls", [])

                                # Process content blocks separately
                                if content_blocks:
                                    for block in content_blocks:
                                        block_type = block.get("type")

                                        # Handle reasoning blocks
                                        if block_type == "reasoning":
                                            reasoning_text = block.get("reasoning", "")
                                            if reasoning_text:
                                                yield json.dumps({"type": "reasoning", "payload": reasoning_text})

                                        # Handle text blocks
                                        elif block_type == "text":
                                            text_content = block.get("text", "")
                                            if text_content:
                                                yield json.dumps({"type": "chunk", "payload": text_content})
                                                assistant_content += text_content

                                # Fallback to raw content if content_blocks not available
                                elif hasattr(msg, "content") and msg.content:
                                    content = msg.content
                                    yield json.dumps({"type": "chunk", "payload": content})
                                    assistant_content += content

                                # Yield Tool Calls
                                if tool_calls:
                                    print(f"[DEBUG] Tool Calls Detected: {tool_calls}", flush=True)
                                    assistant_tool_calls.extend(tool_calls)
                                    for tool in tool_calls:
                                        # tool is dict: {'name': '...', 'args': {}, 'id': '...'}
                                        yield json.dumps({
                                            "type": "tool_call",
                                            "payload": json.dumps({
                                                "name": tool["name"],
                                                "args": tool["args"],
                                                "id": tool.get("id")
                                            })
                                        })

                            except Exception as e:
                                print(f"[DEBUG] Error extracting message: {e}", flush=True)
                
                # Check for Todos/Logs in any node output (if generic)
                # If todos appear, they might be in a specific node or root.
                if isinstance(chunk, dict):
                     for key, val in chunk.items():
                         if isinstance(val, dict) and "todos" in val and val["todos"]:
                            for todo in val["todos"]:
                                yield json.dumps({"type": "log", "payload": f"Plan: {todo}"})
            
            # Append Assistant Response to History
            if assistant_content or assistant_tool_calls:
                new_msg = {"role": "assistant", "content": assistant_content}
                if assistant_tool_calls:
                    new_msg["tool_calls"] = assistant_tool_calls
                history.append(new_msg)
                
                # Update Session Store
                if session_id:
                    SESSION_STORE[session_id]["history"] = history

            # Check capture
            if _captured_data:
                title = _captured_data.get("title", "Generated Widget")
                code = _captured_data.get("code", "")
                width = _captured_data.get("width", 2)
                height = _captured_data.get("height", 2)

                # Generate widget ID for consistency
                slug = re.sub(r'[^a-z0-9]', '', title.lower()[:20])
                timestamp = int(time.time())
                widget_id = f"{timestamp}_{slug}"

                # Send preview IMMEDIATELY with code (before bundling)
                preview_manifest = {
                    "id": widget_id,
                    "title": title,
                    "dimensions": {"w": width, "h": height},
                    "code": code,
                    "url": None,  # Will be set after bundling
                    "projectPath": project_path
                }
                yield json.dumps({"type": "manifest", "payload": json.dumps(preview_manifest)})

                # Write widget files to project directory
                if project_path:
                    try:
                        # Save the main widget code
                        component_file = os.path.join(project_path, "widget.jsx")
                        with open(component_file, "w") as f:
                            f.write(code)

                        # Save widget metadata
                        metadata_file = os.path.join(project_path, "widget.json")
                        metadata = {
                            "title": title,
                            "width": width,
                            "height": height,
                            "created_at": time.time()
                        }
                        with open(metadata_file, "w") as f:
                            json.dump(metadata, f, indent=2)

                        # Create a README for the project
                        readme_file = os.path.join(project_path, "README.md")
                        if not os.path.exists(readme_file):
                            readme_content = f"""# {title}

This is an AI-generated widget project.

## Files
- `widget.jsx` - Main React component
- `widget.json` - Widget metadata
- `README.md` - This file

## Development
This project is managed by the Deephome AI agent.
You can ask the agent to modify files or add new features.
"""
                            with open(readme_file, "w") as f:
                                f.write(readme_content)

                        print(f"[INFO] Wrote widget files to {project_path}", flush=True)
                    except Exception as e:
                        print(f"[ERROR] Failed to write project files: {e}", flush=True)

                # Bundle the widget for deployment (in background)
                try:
                    bundled_url = self.bundle_widget_simple(widget_id, title, code, width, height)
                    if bundled_url:
                        print(f"[INFO] Widget bundled successfully: {bundled_url}", flush=True)
                    else:
                        print(f"[WARN] Bundling failed, but preview still works with code", flush=True)
                except Exception as e:
                    print(f"[ERROR] Bundling error: {e}", flush=True)
                 
        except Exception as e:
            logging.error(f"DeepAgent Error: {e}")
            yield json.dumps({"type": "error", "payload": str(e)})


    def bundle_widget_simple(self, widget_id: str, title: str, code: str, width: int, height: int) -> Optional[str]:
        """Bundle widget and return URL (or None if failed). Does not return full manifest."""
        try:
            # Create a widget-specific directory
            widget_dir = os.path.join(GENERATED_DIR, widget_id)
            if not os.path.exists(widget_dir):
                os.makedirs(widget_dir)

            jsx_file = os.path.join(widget_dir, "index.jsx")
            js_file = os.path.join(widget_dir, "index.js")
            html_file = os.path.join(widget_dir, "index.html")

            # Strip React imports to rely on Global React from CDN
            code_clean = re.sub(r"import\s+.*?from\s+['\"]react['\"];?", "", code)
            code_clean = re.sub(r"import\s+.*?from\s+['\"]react-dom['\"];?", "", code_clean)

            # Ensure there is a default export if we are bundling
            if "export default" not in code_clean:
                # Try to find a component name
                comp_match = re.search(r"(?:const|function)\s+([A-Z]\w+)", code_clean)
                if comp_match:
                    code_clean += f"\nexport default {comp_match.group(1)};"

            with open(jsx_file, "w") as f:
                f.write(code_clean)

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

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
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

            return f"/generated/{widget_id}/index.html"

        except Exception as e:
            logging.error(f"Bundling error: {str(e)}")
            return None
