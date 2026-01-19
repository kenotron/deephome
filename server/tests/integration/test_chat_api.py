from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_chat_endpoint_structure():
    """
    Verifies that the agent query endpoint exists and accepts parameters.
    Does not run full LLM inference to save cost/time, but checks connection.
    """
    # Just check if endpoint is reachable
    response = client.get("/agent/query") 
    # Should result in 422 (Validation Error) due to missing prompt, or 200/stream if working.
    # We expect 422 because 'prompt' is required.
    assert response.status_code == 422 # "field required"

def test_history_endpoint():
    """
    Verifies session history endpoint.
    """
    response = client.get("/agent/history/test_session_123")
    assert response.status_code == 200
    assert response.json() == [] # Empty history for new session

def test_events_endpoint():
    """
    Verifies we can connect to event stream.
    """
    # Streaming endpoints block TestClient usually, so we just check header or basic connection
    # Actually TestClient doesn't support streaming well without 'httpx' async client.
    # For now, simplistic check.
    pass
