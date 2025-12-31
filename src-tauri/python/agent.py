import asyncio
import json
import time
import os
import re
import logging
from typing import Callable, Optional
from functools import partial
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

load_dotenv()

# Setup Logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_debug.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(message)s')

# Updated System Prompt for Tool-Based Agent
INSTRUCTIONS = """
You are a "Master UI Designer" AI. Your goal is to generate React widgets that feel like premium, hand-crafted "Family OS" components.

### 🚫 ABSOLUTE PROHIBITIONS
1.  **NO SOLID ROOT BACKGROUNDS**: Your root `div` MUST be transparent. NEVER use `bg-black`, `bg-white`, or `bg-slate-900` as the outermost container color. The host provides the glassmorphic shell.
2.  **NO STRETCHED BUTTONS**: For calculators or numeric inputs, NEVER use full-width buttons in a vertical list. Always use a `grid grid-cols-4` or similar.
3.  **NO MARGINS ON ROOT**: Trust the host shell's padding. Use `w-full h-full flex flex-col`.

### 🎨 Design System: "Digital Craft"
-   **Color Palette**: 
    -   Sage (#a3b18a), Terracotta (#bc6c4b), Mustard (#dda15e), Charcoal (#4a4e4d).
-   **Internal Glass**: If you need a section, use: `bg-white/40 border border-black/5 rounded-2xl shadow-sm`.
-   **Typography**:
    -   Level 1: `text-2xl font-black tracking-tight text-[#4a4e4d]`.
    -   Labels: `text-[10px] font-bold uppercase tracking-widest text-[#bc6c4b]`.
-   **Interactivity**: Buttons should be `hover:bg-black/5 active:scale-95 transition-all`.

### 🌟 Blueprint Example (High-End Calculator)
```jsx
const FamilyCalc = () => {
    const [val, setVal] = React.useState('0');
    return (
        <div className="w-full h-full flex flex-col p-1 font-sans text-[#4a4e4d]">
            {/* Display */}
            <div className="flex flex-col items-end justify-center h-20 px-2 mb-4 bg-white/20 rounded-2xl border border-black/5">
                <span className="text-[10px] font-bold text-[#bc6c4b] uppercase tracking-widest">Calculated Result</span>
                <span className="text-4xl font-black tracking-tighter tabular-nums truncate">{val}</span>
            </div>
            
            {/* Keypad */}
            <div className="grid grid-cols-4 gap-2 flex-1">
                {['C', '±', '%', '÷', '7', '8', '9', '×', '4', '5', '6', '-', '1', '2', '3', '+', '0', '.', '='].map((btn) => (
                    <button 
                        key={btn}
                        className={`flex items-center justify-center rounded-xl font-black text-sm transition-all active:scale-90
                            ${['÷', '×', '-', '+', '='].includes(btn) ? 'bg-[#bc6c4b] text-white shadow-md' : 'bg-white/60 hover:bg-white/80 border border-black/5'}
                            ${btn === '0' ? 'col-span-2' : ''}
                        `}
                        onClick={() => setVal(v => v === '0' ? btn : v + btn)}
                    >
                        {btn}
                    </button>
                ))}
            </div>
        </div>
    );
};
export default FamilyCalc;
```

Produce only the JavaScript code for the widget.
"""

def create_widget_impl(q, title: str, code: str, width: int = 2, height: int = 2):
    """
    Creates a React-based widget. 
    """
    try:
        logging.info(f"Tool called: create_widget('{title}')")
        q.put(("log", f"Tool called: create_widget('{title}')"))
        
        slug = re.sub(r'[^a-z0-9]', '', title.lower()[:20])
        timestamp = int(time.time())
        widget_id = f"{timestamp}_{slug}"
                
        manifest = {
            "id": widget_id,
            "title": title,
            "dimensions": {"w": width, "h": height},
            "code": code,
            "url": None
        }
        
        q.put(("manifest", json.dumps(manifest)))
        q.put(("log", f"Widget '{title}' generated successfully."))
        return f"Success: Widget '{title}' generated."
        
    except Exception as e:
        error_msg = f"Failed to create widget: {str(e)}"
        logging.error(error_msg)
        q.put(("error", error_msg))
        return error_msg

async def generate_widget_stream(prompt: str):
    yield ("log", f"Agent received: {prompt}")
    if not os.getenv("OPENAI_API_KEY"):
        yield ("error", "OPENAI_API_KEY not found.")
        return

    model_id = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
    loop = asyncio.get_event_loop()
    import queue
    q = queue.Queue()
    
    def create_widget(title: str, code: str, width: int = 2, height: int = 2):
        return create_widget_impl(q, title, code, width, height)

    agent = Agent(
        model=OpenAIChat(id=model_id),
        tools=[DuckDuckGoTools(), create_widget],
        debug_mode=True,
        markdown=False
    )

    def run_agent_thread():
        try:
            full_prompt = f"{INSTRUCTIONS}\n\nUser Request: {prompt}"
            response_stream = agent.run(full_prompt, stream=True)
            for chunk in response_stream:
                q.put(("chunk", chunk))
            q.put(("done", None))
        except Exception as e:
            q.put(("error", str(e)))

    import threading
    t = threading.Thread(target=run_agent_thread)
    t.start()
    
    while True:
        try:
            msg_type, msg_data = await loop.run_in_executor(None, q.get, True, 0.1)
        except queue.Empty:
            if not t.is_alive():
                break
            await asyncio.sleep(0.01)
            continue
            
        if msg_type == "done":
            break
        elif msg_type == "error":
            yield ("error", msg_data)
            return
        elif msg_type == "log":
             yield ("log", msg_data)
        elif msg_type == "manifest":
             yield ("manifest", msg_data)
        elif msg_type == "chunk":
            chunk = msg_data
            if hasattr(chunk, "content") and chunk.content:
                 yield ("response", chunk.content)
            if hasattr(chunk, "tools") and chunk.tools:
                for tool in chunk.tools:
                    yield ("tool_call", json.dumps({"name": tool.name, "args": tool.args}))

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
