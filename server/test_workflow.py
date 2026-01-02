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
    
    for result_json in flow.run(prompt):
        result = json.loads(result_json)
        msg_type = result["type"]
        msg_payload = result["payload"]
        
        if msg_type == "log":
            print(f"[LOG] {msg_payload}")
        elif msg_type == "manifest":
            manifest = json.loads(msg_payload)
            print(f"[MANIFEST] Title: {manifest['title']}, URL: {manifest['url']}")
            
            # Verify files exist
            base_dir = os.path.dirname(os.path.abspath(__file__))
            generated_dir = os.path.join(base_dir, "generated")
            html_path = os.path.join(base_dir, manifest["url"].lstrip("/"))
            js_path = os.path.join(os.path.dirname(html_path), "index.js")
            jsx_path = os.path.join(os.path.dirname(html_path), "index.jsx")
            
            print(f"Checking files for widget: {manifest['id']}")
            print(f"HTML exists: {os.path.exists(html_path)} at {html_path}")
            print(f"JS exists: {os.path.exists(js_path)} at {js_path}")
            print(f"JSX exists: {os.path.exists(jsx_path)} at {jsx_path}")
            
            if os.path.exists(html_path):
                print("Test Passed: Files generated.")
            else:
                print("Test Failed: HTML file not found.")
        elif msg_type == "error":
            print(f"[ERROR] {msg_payload}")

if __name__ == "__main__":
    asyncio.run(test_workflow())
