import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from langchain_core.tools import tool

load_dotenv()

@tool
def dummy_tool(arg: str) -> str:
    """Dummy tool."""
    return "done"

async def inspect():
    model = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "glm-4.7"), streaming=True)
    agent = create_deep_agent(
        model=model,
        tools=[dummy_tool],
        system_prompt="You are a helper.",
        name="debug_agent"
    )
    
    print(f"Agent Type: {type(agent)}")
    print(f"Agent Dir: {dir(agent)}")
    
    # Try running it once
    print("\n--- Run 1 ---")
    async for chunk in agent.astream({"messages": [{"role": "user", "content": "My name is DEBUG."}]}):
        pass

    # Try running it again (reusing object)
    print("\n--- Run 2 ---")
    messages = []
    found_name = False
    async for chunk in agent.astream({"messages": [{"role": "user", "content": "What is my name?"}]}):
        if hasattr(chunk, "messages"):
            for m in chunk["messages"]:
                if hasattr(m, "content") and m.content:
                    print(f"Chunk: {m.content}")
                    if "DEBUG" in m.content:
                        found_name = True
    
    if found_name:
        print("native object reuse works locally?")
    else:
        print("native object reuse failed locally.")

    # Check for state attributes
    if hasattr(agent, "get_state"):
        print("Has get_state")
    if hasattr(agent, "checkpointer"):
        print("Has checkpointer")

if __name__ == "__main__":
    asyncio.run(inspect())
