"""Test script to verify reasoning and text content are streamed separately."""

import asyncio
import json
from workflow import WidgetFlow
import os
from dotenv import load_dotenv

load_dotenv()

async def test_reasoning_stream():
    """Test that reasoning and text content are properly separated in the stream."""

    model_id = os.getenv("OPENAI_MODEL_NAME", "glm-4.7")
    flow = WidgetFlow(model_id=model_id)

    # Use a prompt that should trigger thinking
    prompt = "Create a simple calculator widget"

    print("=" * 60)
    print("Testing Reasoning Stream Separation")
    print("=" * 60)

    reasoning_chunks = []
    text_chunks = []
    other_events = []

    async for result_json in flow.run(prompt, session_id="test_session"):
        try:
            result = json.loads(result_json)
            event_type = result["type"]
            payload = result["payload"]

            if event_type == "reasoning":
                reasoning_chunks.append(payload)
                print(f"\n[REASONING] {payload[:100]}...")

            elif event_type == "chunk":
                text_chunks.append(payload)
                print(f"\n[TEXT CHUNK] {payload[:100]}...")

            elif event_type == "log":
                other_events.append(("log", payload))
                print(f"\n[LOG] {payload}")

            elif event_type == "tool_call":
                other_events.append(("tool_call", payload))
                print(f"\n[TOOL_CALL] {payload}")

            elif event_type == "manifest":
                other_events.append(("manifest", payload))
                print(f"\n[MANIFEST] Generated")

            elif event_type == "done":
                print(f"\n[DONE]")

        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Reasoning chunks: {len(reasoning_chunks)}")
    print(f"  Text chunks: {len(text_chunks)}")
    print(f"  Other events: {len(other_events)}")
    print("=" * 60)

    # Verify we got both types of content
    if reasoning_chunks:
        print("\n✅ SUCCESS: Reasoning content detected separately!")
    else:
        print("\n⚠️  WARNING: No reasoning content detected (model may not support it)")

    if text_chunks:
        print("✅ SUCCESS: Text content detected separately!")
    else:
        print("❌ ERROR: No text content detected")

if __name__ == "__main__":
    asyncio.run(test_reasoning_stream())
