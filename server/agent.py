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

async def generate_widget_stream(prompt: str, session_id: str = None):
    yield ("log", f"Agent received: {prompt} (Session: {session_id})")
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
