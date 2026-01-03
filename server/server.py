import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from agent import generate_widget_stream
from workflow import SESSION_STORE

from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Ensure generated directory exists
GENERATED_DIR = "generated"
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

from fastapi import Request

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
        # SSE format: data: <payload>\n\n
        # We need to serialize our (event_type, payload) tuple into SSE format
        # Common pattern: event: type \n data: payload \n\n
        async for event_type, payload in generate_widget_stream(prompt, session_id):
             # payload is a string (JSON or text)
             # We wrap it in a JSON object for the SSE 'data' field
             data = json.dumps({"type": event_type, "payload": payload})
             yield f"data: {data}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/agent/history/{session_id}")
async def get_agent_history(session_id: str):
    if session_id in SESSION_STORE:
        return JSONResponse(content=SESSION_STORE[session_id]["history"])
    return JSONResponse(content=[])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
