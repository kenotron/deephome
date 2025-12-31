import asyncio
import os
import sys

# Add current dir to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import generate_widget_stream

async def main():
    print("Starting local debug...")
    prompt = "Create a simple calculator widget"
    async for event, payload in generate_widget_stream(prompt):
        print(f"EVENT: {event} | PAYLOAD: {payload[:100]}...")
        if event == "error":
            print("ERROR DETECTED")

if __name__ == "__main__":
    asyncio.run(main())
