# In-memory session store
SESSION_STORE = {}

async def broadcast_event(session_id: str, event_type: str, payload: dict):
    """
    Broadcast an event to the session's event stream.
    """
    if session_id in SESSION_STORE:
        queue = SESSION_STORE[session_id].get("event_queue")
        if queue:
            await queue.put({"type": event_type, "payload": payload})
            print(f"[DEBUG] Broadcasted {event_type} to session {session_id}", flush=True)
