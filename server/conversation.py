import os
import re
import json
import time
import logging
from typing import Optional, AsyncIterator
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

from agent import create_skilled_deep_agent

load_dotenv()

# Constants
GENERATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
WORKSPACES_DIR = os.path.join(GENERATED_DIR, "workspaces")
ESBUILD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "node_modules", ".bin", "esbuild")

# In-memory session store
SESSION_STORE = {}

# Ensure dirs exist
for d in [GENERATED_DIR, WORKSPACES_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Global capture for preview trigger
_preview_event = {}

@tool
def preview_widget(title: str, width: int = 2, height: int = 2) -> str:
    """
    Notify that the widget files have been created and are ready for preview.
    Call this AFTER you have written 'widget.jsx' and 'widget.json'.
    
    Args:
        title: Title of the widget.
        width: Width in grid units (1-4).
        height: Height in grid units (1-4).
    """
    global _preview_event
    _preview_event["title"] = title
    _preview_event["width"] = width
    _preview_event["height"] = height
    return "Success: Preview triggered."


# Creation Skill Content (Standard SKILL.md format)
CREATION_SKILL_MD = """---
name: creation-skill
description: Capability to create interactive React components/apps by writing code to the filesystem.
---

# Creation Skill

## When to Use
- User asks for a Visual, UI, Interface, Dashboard, Component, App, or "Widget".
- Visual representation is the best way to answer.

## Instructions
To create a visual component, you must write TWO files to the current directory:
1. `widget.jsx`: The React component code.
2. `widget.json`: Metadata (title, width, height).

### Technical Rules
- Use `lucide-react` for icons.
- Use `tailwindcss` for styling.
- **ALWAYS include a background color** (e.g., `bg-slate-50`, `bg-white`).
- Use rounded corners (`rounded-xl`) and padding.
- `widget.jsx` MUST export a default component (`export default function Widget() ...`).
- **Use the `write` tool** to create files.
- **CRITICALLY IMPORTANT**: **DO NOT use leading slashes** in file paths.
  - ✅ CORRECT: `widget.jsx`
  - ❌ WRONG: `/widget.jsx` (This will fail with Read-only file system error)
- `widget.jsx` MUST export a default component (`export default function Widget() ...`).

### Workflow
1. Write `widget.jsx` using `write` (file_path="widget.jsx", content="...").
2. Check if write succeeded.
3. Write `widget.json` using `write` (file_path="widget.json", content="...").
4. Call `preview_widget` to show it to the user.

### layout Best Practices
- Calendars/Calculators: Use `grid` layout.
- Container: `w-full h-full flex flex-col`.
"""

class ConversationFlow:
    model_id: str = os.getenv("OPENAI_MODEL_NAME", "glm-4.7")
    
    def __init__(self, **kwargs):
        if "model_id" in kwargs:
            self.model_id = kwargs.pop("model_id")

    async def run(self, prompt: str, session_id: Optional[str] = None) -> AsyncIterator[str]:
        # Reset capture
        global _preview_event
        _preview_event = {}

        # Initialize Model
        model = ChatOpenAI(
            model=self.model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            streaming=True,
        )

        # Session / Workspace Setup
        history = []
        workspace_path = None

        if session_id:
            if session_id in SESSION_STORE:
                data = SESSION_STORE[session_id]
                agent = data["agent"]
                history = data["history"]
                workspace_path = data["workspace_path"]
            else:
                # Create Workspace
                workspace_path = Path(WORKSPACES_DIR) / f"session_{session_id}"
                workspace_path.mkdir(parents=True, exist_ok=True)
                
                # Install Skill
                skills_dir = workspace_path / "skills" / "user"
                skills_dir.mkdir(parents=True, exist_ok=True)
                
                skill_dir = skills_dir / "creation-skill"
                skill_dir.mkdir(parents=True, exist_ok=True)
                
                with open(skill_dir / "SKILL.md", "w") as f:
                    f.write(CREATION_SKILL_MD)
                
                # Initialize Agent pointing to workspace
                agent = create_skilled_deep_agent(
                    model=model,
                    root_dir=workspace_path,
                    skills_registry_path=str(skills_dir),
                    tools=[preview_widget],
                    name="deep-conversation-agent"
                )
                
                SESSION_STORE[session_id] = {
                    "agent": agent,
                    "history": [],
                    "workspace_path": workspace_path
                }
                history = SESSION_STORE[session_id]["history"]
        else:
             # Temp workspace
            workspace_path = Path(WORKSPACES_DIR) / f"temp_{int(time.time())}"
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Install Skill
            skills_dir = workspace_path / "skills" / "user"
            skills_dir.mkdir(parents=True, exist_ok=True)
            skill_dir = skills_dir / "creation-skill"
            skill_dir.mkdir(parents=True, exist_ok=True)
            with open(skill_dir / "SKILL.md", "w") as f:
                f.write(CREATION_SKILL_MD)

            agent = create_skilled_deep_agent(
                model=model,
                root_dir=workspace_path,
                skills_registry_path=str(skills_dir),
                tools=[preview_widget],
                name="deep-conversation-agent"
            )

        # Standard Execution Loop
        user_msg = {"role": "user", "content": prompt}
        history.append(user_msg)
        
        formatted_history = []
        for msg in history:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_history.append(AIMessage(content=msg["content"], tool_calls=msg.get("tool_calls", [])))
            elif msg["role"] == "tool":
                 pass

        try:
            print(f"[DEBUG] Starting stream for {session_id}.", flush=True)
            input_payload = {"messages": formatted_history}
            
            # Use astream_events for granular token streaming
            async for event in agent.astream_events(input_payload, version="v2"):
                kind = event["event"]
                name = event.get("name")
                
                # Stream Tokens
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield json.dumps({"type": "chunk", "payload": chunk.content})
                
                # Tool Execution Hints
                elif kind == "on_tool_start":
                    # Determine if it's a user-visible tool or internal
                    if name and name != "create_deep_agent" and name != "DeepAgent" and not name.startswith("LangGraph"): 
                         # Simple heuristic to show relevant tools
                        yield json.dumps({"type": "chunk", "payload": f"\n\n> 🛠️  Running {name}...\n\n"})
                
                # Check for Preview Trigger (when tool call completes/starts)
                elif kind == "on_tool_end":
                    # Debug tool output
                    print(f"[DEBUG] Tool {name} finished. Output: {event['data'].get('output')}", flush=True)

                    if name == "preview_widget":
                        # The agent called preview_widget, meaning files are ready.
                        # Retrieve files from disk
                        code = ""
                        title = "Generated Component"
                        
                        try:
                            # Debug check file existence
                            fpath = workspace_path / "widget.jsx"
                            print(f"[DEBUG] Checking file {fpath}: {fpath.exists()}", flush=True)
                            with open(fpath, "r") as f:
                                code = f.read()
                        except Exception as e:
                            print(f"[DEBUG] Read failed: {e}", flush=True)
                            code = f"// Error reading widget.jsx: {e}"
                        
                        # Try to read title from widget.json if available
                        try:
                            with open(workspace_path / "widget.json", "r") as f:
                                meta = json.load(f)
                                title = meta.get("title", title)
                        except Exception as e:
                            print(f"[DEBUG] Failed to read widget.json: {e}", flush=True)
                            
                        slug = re.sub(r'[^a-z0-9]', '', title.lower()[:20])
                        timestamp = int(time.time())
                        widget_id = f"{timestamp}_{slug}"
    
                        preview_manifest = {
                            "id": widget_id,
                            "title": title,
                            "dimensions": {"w": 2, "h": 2},
                            "code": code,
                            "url": None,
                            "projectPath": str(workspace_path)
                        }
                        # Emit preview as a normal assistant content chunk to follow OpenAI Chat Completion streaming spec
                        yield json.dumps({"type": "chunk", "payload": f"Preview ready: {json.dumps(preview_manifest)}"})

                # History Persistence
                elif kind == "on_chat_model_end":
                     msg = event["data"]["output"]
                     # We store the AIMessage
                     if isinstance(msg, AIMessage):
                        history.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

        except Exception as e:
            logging.error(f"DeepAgent Error: {e}")
            yield json.dumps({"type": "error", "payload": str(e)})


async def stream_conversation(prompt: str, session_id: Optional[str] = None):
    if not os.getenv("OPENAI_API_KEY"):
        yield ("error", "OPENAI_API_KEY not found.")
        return

    model_id = os.getenv("OPENAI_MODEL_NAME", "glm-4.7")
    flow = ConversationFlow(model_id=model_id)

    async for result_json in flow.run(prompt, session_id=session_id):
        try:
            result = json.loads(result_json)
            yield (result["type"], result["payload"])
        except json.JSONDecodeError:
            yield ("error", "Internal JSON error")


async def stream_openai_conversation(request_body: dict):
    """
    Stream events in OpenAI Chat Completion format (SSE).
    """
    import time
    import uuid
    
    model = request_body.get("model", "deep-agent")
    messages = request_body.get("messages", [])
    session_id = None
    
    # Extract session_id from last message or system prompt if strictly needed, 
    # but for now we'll generate a temp one or use a header if passed elsewhere.
    # Actually, standard OpenAI API doesn't have session_id. 
    # We will treat each request as a continuing session if 'user' identifier is consistent? 
    # Or just use a param?
    # For compatibility, let's assume specific "user" field in body is session_id, or just stateless for now.
    user_id = request_body.get("user", f"user_{int(time.time())}")
    session_id = user_id 

    # Extract prompt from last user message
    last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
    if not last_user_msg:
        yield f"data: {json.dumps({'error': 'No user message found'})}\n\n"
        return

    prompt = last_user_msg["content"]
    
    completion_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())

    # Helper to yield chunk
    def make_chunk(delta, finish_reason=None):
        return json.dumps({
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason
            }]
        })

    # 1. Start Stream
    yield f"data: {make_chunk({'role': 'assistant', 'content': ''})}\n\n"

    # 2. Run Flow
    if not os.getenv("OPENAI_API_KEY"):
         yield f"data: {make_chunk({'content': 'Error: OPENAI_API_KEY not found.'})}\n\n"
         yield "data: [DONE]\n\n"
         return

    flow = ConversationFlow(model_id=os.getenv("OPENAI_MODEL_NAME", "glm-4.7"))

    async for result_json in flow.run(prompt, session_id=session_id):
        try:
            result = json.loads(result_json)
            etype = result["type"]
            payload = result["payload"]

            if etype == "chunk":
                yield f"data: {make_chunk({'content': payload})}\n\n"
            
            elif etype == "error":
                 yield f"data: {make_chunk({'content': f'\nErrors: {payload}'})}\n\n"

        except json.JSONDecodeError:
            pass

    # 3. Finish
    yield f"data: {make_chunk({}, finish_reason='stop')}\n\n"
    yield "data: [DONE]\n\n"
