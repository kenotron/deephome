import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

from conversation import stream_conversation, stream_openai_conversation, broadcast_event
from conversation import SESSION_STORE

app = FastAPI()

# Ensure generated directory exists
GENERATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
if not os.path.exists(GENERATED_DIR):
    os.makedirs(GENERATED_DIR)

app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI Pydantic Models
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "deep-agent"
    messages: List[Message]
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    user: Optional[str] = None # We will use this as session_id if provided

@app.middleware("http")
async def add_frame_headers(request: Request, call_next):
    response = await call_next(request)
    # Explicitly allow iframe embedding
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    # Remove X-Frame-Options if present (default is strictly blocking in some setups)
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]
    return response

@app.get("/agent/query")
async def stream_agent_query(prompt: str, session_id: str = None):
    async def event_generator():
        # Backward compatibility endpoint
        async for event_type, payload in stream_conversation(prompt, session_id):
             data = json.dumps({"type": event_type, "payload": payload})
             yield f"data: {data}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/agent/events/{session_id}")
async def stream_agent_events(session_id: str):
    """
    Dedicated persistent event stream for a session.
    """
    async def event_generator():
        if session_id not in SESSION_STORE:
            # Wait a bit or error? Let's verify existence or create placeholder?
            # For now, if session doesn't exist, we just wait until it might? 
            # Or simpler: return 404? 
            # Better: yield a 'waiting' status.
            yield f"data: {json.dumps({'type': 'status', 'payload': 'Session not found. Waiting...'})}\n\n"
            # In a real app we might create it.
            # Here we just return to avoid complex connection logic if the user hasn't messaged yet.
            # But client `useEventStream` will retry.
            return

        queue = SESSION_STORE[session_id].get("event_queue")
        if not queue:
            # Should not happen if session exists
            yield f"data: {json.dumps({'type': 'error', 'payload': 'No event queue.'})}\n\n"
            return
        
        print(f"[DEBUG] Event stream connected for {session_id}")
        
        try:
            while True:
                # Wait for next event
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            print(f"[DEBUG] Event stream disconnected for {session_id}: {e}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible Chat Completion Endpoint (Streaming only for now).
    """
    if not request.stream:
        # TODO: Implement blocking mode if needed. For now, force validation error or just stream?
        # A compliant API should handle non-stream, but we are optimizing for Agent streaming.
        # We'll just stream and let the client handle it, or return a 400.
        # Ideally, we buffer and return full response.
        return JSONResponse(status_code=400, content={"error": "Only streaming is supported. Set stream=true."})

    # Prepare request dict for the adapter
    req_dict = request.model_dump()
    
    return StreamingResponse(
        stream_openai_conversation(req_dict), 
        media_type="text/event-stream"
    )

@app.get("/agent/history/{session_id}")
async def get_agent_history(session_id: str):
    if session_id in SESSION_STORE:
        return JSONResponse(content=SESSION_STORE[session_id]["history"])
    return JSONResponse(content=[])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
