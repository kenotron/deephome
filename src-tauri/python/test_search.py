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
    # 1. ensure we got a manifest
    manifest_events = [e for e in events if e[0] == 'manifest']
    assert len(manifest_events) == 1, "Agent failed to generate a manifest"
    
    manifest = json.loads(manifest_events[0][1])
    print(f"[MANIFEST] {manifest}")
    
    # 2. Check if we saw any tool usage logs (heuristic)
    # The 'log' events from the agent might contain "Using tool..." or similar depending on verbose level
    # But explicitly, our agent code yields "tool_call" if Agno streams it effectively.
    # Note: Agno's `stream=True` behavior with built-in tools might vary.
    
    # Let's inspect the files content to see if it looks like it has real data
    # (Checking for a number in the title or HTML)
    
    widget_dir = "generated/" + manifest["id"]
    with open(f"{widget_dir}/index.html", "r") as f:
        html = f.read()
        print(f"[HTML Snippet] {html[:200]}")
        
    # We expect some number representing price
    # e.g. "$95,000" or similar.
    # We won't assert exact price, but just that it succeeded without error.

if __name__ == "__main__":
    # Helper to run async test manually if needed
    import asyncio
    asyncio.run(test_agent_search_capability())
