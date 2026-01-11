import os
import re
import asyncio
import json
import time
import logging
from typing import Optional, AsyncIterator
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, BaseMessageChunk, AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk

from agent import create_skilled_deep_agent

class ChatDeepSeekCompatible(ChatOpenAI):
    """
    Custom ChatOpenAI subclass to handle DeepSeek/Z.ai style reasoning_content.
    LangChain's default ChatOpenAI implementation ignores unrecognized fields in the delta.
    """
    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ) -> ChatGenerationChunk | None:
        # DEBUG: Print raw chunk
        # print(f"[DEBUG] Raw LC Chunk: {chunk}", flush=True)

        # Let parent do the heavy lifting
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )

        if generation_chunk is None:
            return None
        
        # Manually extract reasoning_content from the raw delta
        try:
            choice = chunk["choices"][0]
            delta = choice.get("delta", {})
            reasoning = delta.get("reasoning_content")
            if reasoning:
                generation_chunk.message.additional_kwargs["reasoning_content"] = reasoning
        except (KeyError, IndexError, AttributeError):
            pass
            
        return generation_chunk

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



async def broadcast_event(session_id: str, event_type: str, payload: dict):
    """
    Broadcast an event to the session's event stream.
    """
    if session_id in SESSION_STORE:
        queue = SESSION_STORE[session_id].get("event_queue")
        if queue:
            await queue.put({"type": event_type, "payload": payload})
            print(f"[DEBUG] Broadcasted {event_type} to session {session_id}", flush=True)

# Static bundle_project removed - now created dynamically in run() to capture workspace_path

@tool
async def preview_widget(title: str, width: int = 2, height: int = 2) -> str:
    """
    Notify that the widget files have been created and are ready for preview.
    Call this AFTER you have written 'widget.jsx' (and optionally bundled it) and 'widget.json'.
    
    Args:
        title: Title of the widget.
        width: Width in grid units (1-4).
        height: Height in grid units (1-4).
    """
    # Simply return success. The actual file reading happens in the event loop hook
    # where we check for widget.bundled.js or widget.jsx
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
- **Use `bundle_project`** to compile disparate files into a single bundle.

### Workflow
1. Write `widget.jsx` (and any other component files) using `write`.
2. check if write succeeded.
3. Call `bundle_project` to compile everything into `widget.bundled.js`.
4. Check if bundling succeeded.
5. Write `widget.json` using `write`.
6. Call `preview_widget` to show it to the user.

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
        model = ChatDeepSeekCompatible(
            model=self.model_id,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            streaming=True,
            temperature=0.6,
            model_kwargs={"reasoning_effort": "high"}
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
                
                # Define bound tool for bundling that knows the CWD
                @tool
                async def bundle_project() -> str:
                    """
                    Bundle the current project (widget.jsx) into a single file (widget.bundled.js).
                    Call this BEFORE preview_widget if you have multiple files or dependencies.
                    """
                    try:
                        # Run esbuild in the correct workspace directory
                        process = await asyncio.create_subprocess_exec(
                            ESBUILD_PATH,
                            "widget.jsx",
                            "--bundle",
                            "--outfile=widget.bundled.js",
                            "--format=esm",
                            "--jsx=automatic", 
                            "--loader:.js=jsx",
                            "--loader:.jsx=jsx",
                            "--external:react",
                            "--external:react/jsx-runtime",
                            "--external:lucide-react",
                            "--external:framer-motion",
                            cwd=str(workspace_path),  # CRITICAL FIX: Use workspace_path
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        if process.returncode != 0:
                            return f"Bundling failed: {stderr.decode()}"
                        
                        return "Bundling successful: widget.bundled.js created."
                    except Exception as e:
                        return f"Bundling error: {str(e)}"

                # Initialize Agent pointing to workspace
                agent = create_skilled_deep_agent(
                    model=model,
                    root_dir=workspace_path,
                    skills_registry_path=str(skills_dir),
                    tools=[preview_widget, bundle_project],
                    name="deep-conversation-agent"
                )
                
                SESSION_STORE[session_id] = {
                    "agent": agent,
                    "history": [],
                    "workspace_path": workspace_path,
                    "event_queue": asyncio.Queue()
                }
                history = SESSION_STORE[session_id]["history"]
        else:
             # Temp workspace
            workspace_path = Path(WORKSPACES_DIR) / f"temp_{int(time.time())}" # We need a real ID for events

            # Create a temp session ID if none provided, to support events
            # But the caller usually provides one.
            pass
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
            
            # Use astream_events for granular token streaming with high recursion limit
            async for event in agent.astream_events(input_payload, config={"configurable": {"session_id": session_id}, "recursion_limit": 100}, version="v2"):
                kind = event["event"]
                name = event.get("name")
                
                # Stream Tokens
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    
                    # DEBUG: Print chunk structure to find where reasoning lives
                    # print(f"[DEBUG] Chunk kwargs: {chunk.additional_kwargs}", flush=True) 

                    # Extract reasoning content (if supported by model, e.g. DeepSeek)
                    reasoning = chunk.additional_kwargs.get("reasoning_content")
                    
                    if reasoning:
                        yield json.dumps({"type": "reasoning", "payload": reasoning})

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
                        
                        # GENERATE index.html for Iframe execution
                        try:
                            # We need to create an index.html that loads the module
                            # and provides the dependencies via Import Map
                            
                            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Widget Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: transparent; margin: 0; padding: 0; overflow: hidden; }
        #root { width: 100%; height: 100%; display: flex; flex-direction: column; }
    </style>
    <script type="importmap">
    {
        "imports": {
            "react": "https://esm.sh/react@18.2.0",
            "react/jsx-runtime": "https://esm.sh/react@18.2.0/jsx-runtime",
            "react-dom/client": "https://esm.sh/react-dom@18.2.0/client",
            "lucide-react": "https://esm.sh/lucide-react@0.263.1",
            "framer-motion": "https://esm.sh/framer-motion@10.12.16"
        }
    }
    </script>
</head>
<body>
    <div id="root"></div>
    <script type="module">
        import React from 'react';
        import { createRoot } from 'react-dom/client';
        import Widget from './widget.bundled.js';

        const root = createRoot(document.getElementById('root'));
        root.render(React.createElement(Widget));
    </script>
</body>
</html>"""
                            
                            with open(workspace_path / "index.html", "w") as f:
                                f.write(html_content)
                                
                            print(f"[DEBUG] Generated index.html at {workspace_path / 'index.html'}", flush=True)

                        except Exception as e:
                             print(f"[DEBUG] Failed to generate index.html: {e}", flush=True)

                        # Standard metadata reading logic
                        code = ""
                        title = "Generated Component"
                        
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
                        
                        # Construct URL path based on workspace location relative to GENERATED_DIR
                        # server.py mounts GENERATED_DIR as /generated
                        # workspace_path is .../generated/workspaces/session_id
                        # So relative path is workspaces/session_id/index.html
                        
                        try:
                            rel_path = workspace_path.relative_to(GENERATED_DIR)
                            preview_url = f"/generated/{rel_path}/index.html"
                        except ValueError:
                             # Fallback if path manipulation fails
                             preview_url = None
    
                        preview_manifest = {
                            "id": widget_id,
                            "title": title,
                            "dimensions": {"w": 2, "h": 2},
                            "code": None, # Signal to use URL
                            "url": preview_url,
                            "projectPath": str(workspace_path)
                        }
                        
                        # Emit preview via broadcast_event (to the event stream)
                        if session_id:
                             await broadcast_event(session_id, "preview", preview_manifest)


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
    
    # Explicitly signal completion
    yield ("done", "[DONE]")


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
