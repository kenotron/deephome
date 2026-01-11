import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add current dir to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow import WidgetFlow

async def test_workflow():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
        return

    print("Starting WidgetFlow test...")
    flow = WidgetFlow()
    prompt = "Create a simple sage green clock widget"
    
    async for result_json in flow.run(prompt):
        result = json.loads(result_json)
        msg_type = result["type"]
        msg_payload = result["payload"]
        
        if msg_type == "log":
            print(f"[LOG] {msg_payload}")
        elif msg_type == "chunk":
            # Check for preview manifest emitted as a standard chunk
            preview_prefix = 'Preview ready: '
            if isinstance(msg_payload, str) and msg_payload.startswith(preview_prefix):
                preview = json.loads(msg_payload[len(preview_prefix):])
                print(f"[PREVIEW] Title: {preview['title']} (id: {preview['id']})")

                # Verify files exist in the generated workspace path
                project_path = preview.get('projectPath') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
                widget_jsx = os.path.join(project_path, 'widget.jsx')
                widget_json = os.path.join(project_path, 'widget.json')

                print(f"Checking files for widget: {preview['id']}")
                print(f"widget.jsx exists: {os.path.exists(widget_jsx)} at {widget_jsx}")
                print(f"widget.json exists: {os.path.exists(widget_json)} at {widget_json}")

                if os.path.exists(widget_jsx) and os.path.exists(widget_json):
                    print("Test Passed: Files generated.")
                else:
                    print("Test Failed: Generated widget files not found.")
        elif msg_type == "error":
            print(f"[ERROR] {msg_payload}")

if __name__ == "__main__":
    asyncio.run(test_workflow())
