import os
import re
import asyncio
import json
import time
import logging
from typing import Optional, AsyncIterator
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage

from server.core.llm.adapters import ChatDeepSeekCompatible
from server.agent.factory import create_skilled_deep_agent
from server.agent.tools import preview_widget
from server.agent.constants import CREATION_SKILL_MD, PREVIEW_HTML_TEMPLATE
from server.session.store import SESSION_STORE, broadcast_event

load_dotenv()

# Constants moved or re-defined
GENERATED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "generated")
WORKSPACES_DIR = os.path.join(GENERATED_DIR, "workspaces")
# Assume ESBuild path is relative to root
ESBUILD_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "node_modules", ".bin", "esbuild")


# Ensure dirs
for d in [GENERATED_DIR, WORKSPACES_DIR]:
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except OSError:
            pass

class ConversationFlow:
    model_id: str = os.getenv("OPENAI_MODEL_NAME", "glm-4.7")
    
    def __init__(self, **kwargs):
        if "model_id" in kwargs:
            self.model_id = kwargs.pop("model_id")

    async def run(self, prompt: str, session_id: Optional[str] = None) -> AsyncIterator[str]:
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
                # WE MUST IMPORT tool here to bind it or keep it local?
                # Keeping it local captures workspace_path
                from langchain_core.tools import tool
                
                @tool
                async def bundle_project() -> str:
                    """
                    Bundle the current project (widget.jsx) into a single file (widget.bundled.js).
                    Call this BEFORE preview_widget if you have multiple files or dependencies.
                    """
                    try:
                        # Run esbuild
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
                            cwd=str(workspace_path),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        
                        if process.returncode != 0:
                            return f"Bundling failed: {stderr.decode()}"
                        
                        # Generate index.html from template
                        with open(workspace_path / "index.html", "w") as f:
                            f.write(PREVIEW_HTML_TEMPLATE)

                        return "Bundling successful: widget.bundled.js and index.html created."
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
             # Temp workspace logic ignored for now as session_id is mandatory in new flow
             # But keeping fallback just in case
            workspace_path = Path(WORKSPACES_DIR) / f"temp_{int(time.time())}"
            workspace_path.mkdir(parents=True, exist_ok=True)
            # ... (Minimal setup for stateless request) ...
            return

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
            async for event in agent.astream_events(input_payload, config={"configurable": {"session_id": session_id}, "recursion_limit": 100}, version="v2"):
                kind = event["event"]
                name = event.get("name")
                
                # Stream Tokens
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    reasoning = chunk.additional_kwargs.get("reasoning_content")
                    
                    if reasoning:
                        yield json.dumps({"type": "reasoning", "payload": reasoning})

                    if chunk.content:
                        yield json.dumps({"type": "chunk", "payload": chunk.content})
                
                # Tool Execution Hints
                elif kind == "on_tool_start":
                    if name and name != "create_deep_agent" and name != "DeepAgent" and not name.startswith("LangGraph"): 
                        args = event["data"].get("input")
                        arg_str = ""
                        if args and isinstance(args, dict):
                            if "file_path" in args:
                                arg_str = f'"{args["file_path"]}"'
                            else:
                                # Simple sanitization to avoid dumping huge file content
                                safe_args = {}
                                for k, v in args.items():
                                    if k in ["code", "content", "file_content", "data"] and isinstance(v, str) and len(v) > 50:
                                        safe_args[k] = "..."
                                    else:
                                        safe_args[k] = v
                                arg_str = json.dumps(safe_args)
                        
                        yield json.dumps({"type": "chunk", "payload": f"\n\n> 🛠️  Running {name} {arg_str}...\n\n"})
                
                # Check for Preview Trigger
                elif kind == "on_tool_end":
                    if name == "preview_widget":
                        # Generate index.html
                        # ... (Simplified for this file View) ...
                        # In refactor we should probably move this index.html generation to a helper in server/modules/preview?
                        # For now keeping it inline to preserve behavior.
                        
                        # LOGIC: Generate index.html, create Manifest, Broadcast 'preview' event.
                        
                        # Note: index.html is now generated mainly by bundle_project, but we could ensure it exists here too if needed.
                        # For now, assuming bundle_project was called.
                        # If simple widget.jsx usage without bundle becomes allowed, we might need fallback here.
                        # But current skill requires bundle.

                        
                        code = ""
                        title = "Generated Component"
                        try:
                            with open(workspace_path / "widget.json", "r") as f:
                                meta = json.load(f)
                                title = meta.get("title", title)
                        except: pass
                            
                        slug = re.sub(r'[^a-z0-9]', '', title.lower()[:20])
                        widget_id = f"{int(time.time())}_{slug}"
                        
                        try:
                            # Relative path logic needs to be robust
                            rel_path = workspace_path.relative_to(GENERATED_DIR)
                            preview_url = f"/generated/{rel_path}/index.html"
                        except: preview_url = None
    
                        preview_manifest = {
                            "id": widget_id,
                            "title": title,
                            "dimensions": {"w": 2, "h": 2},
                            "code": None,
                            "url": preview_url,
                            "projectPath": str(workspace_path)
                        }
                        
                        if session_id:
                             await broadcast_event(session_id, "preview", preview_manifest)


                # History Persistence
                elif kind == "on_chat_model_end":
                     msg = event["data"]["output"]
                     if isinstance(msg, AIMessage):
                        history.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

        except Exception as e:
            logging.error(f"DeepAgent Error: {e}")
            yield json.dumps({"type": "error", "payload": str(e)})


async def stream_conversation(prompt: str, session_id: Optional[str] = None):
    if not os.getenv("OPENAI_API_KEY"):
        yield ("error", "OPENAI_API_KEY not found.")
        return

    flow = ConversationFlow(model_id=os.getenv("OPENAI_MODEL_NAME", "glm-4.7"))

    async for result_json in flow.run(prompt, session_id=session_id):
        try:
            result = json.loads(result_json)
            yield (result["type"], result["payload"])
        except json.JSONDecodeError:
            yield ("error", "Internal JSON error")
    
    yield ("done", "[DONE]")
