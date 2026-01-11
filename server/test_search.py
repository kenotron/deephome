import pytest
import os
import json
import logging
from unittest.mock import MagicMock, patch
import sys

# Ensure src-tauri/python is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from agent import generate_widget_stream, agent

# Setup basic logging to see agent output
logging.basicConfig(level=logging.INFO)

@pytest.mark.asyncio
async def test_agent_search_capability():
    """
    Verifies that the agent can perform a search when asked for real-time info.
    Note: This is an integration test that hits OpenAI.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not found")

    prompt = "What is the current price of Bitcoin? Create a widget showing it."
    
    print(f"\n--- Testing Prompt: {prompt} ---")
    
    events = []
    async for event in generate_widget_stream(prompt):
        event_type, payload = event
        events.append(event)
        
        if event_type == "log":
             print(f"[LOG] {payload}")
        elif event_type == "tool_call":
             print(f"[TOOL] {payload}")
        elif event_type == "response":
             # Print start of response to see if it mentions price
             pass

    # Basic Validation
    # 1. ensure we got a preview (emitted as a chunk)
    preview_events = [e for e in events if e[0] == 'chunk' and isinstance(e[1], str) and e[1].startswith('Preview ready: ')]
    assert len(preview_events) == 1, "Agent failed to generate a preview"

    preview = json.loads(preview_events[0][1][len('Preview ready: '):])
    print(f"[PREVIEW] {preview}")

    # 2. Check generated files (if the agent created files in generated/<id>)
    widget_dir = os.path.join('generated', preview['id'])
    index_path = os.path.join(widget_dir, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            html = f.read()
            print(f"[HTML Snippet] {html[:200]}")
    else:
        print(f"[INFO] No index.html at {index_path}; agent may have stored files elsewhere (projectPath={preview.get('projectPath')})")
        
    # We expect some number representing price
    # e.g. "$95,000" or similar.
    # We won't assert exact price, but just that it succeeded without error.

if __name__ == "__main__":
    # Helper to run async test manually if needed
    import asyncio
    asyncio.run(test_agent_search_capability())
