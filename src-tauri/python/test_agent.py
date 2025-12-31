import pytest
import json
from unittest.mock import MagicMock
from agent import run_agent

def test_run_agent_flow():
    # Mock callback
    mock_callback = MagicMock()
    
    # Run agent
    run_agent("Test Prompt", mock_callback)
    
    # Check calls
    # Should have status updates
    mock_callback.assert_any_call("status", "Agent received: Test Prompt")
    mock_callback.assert_any_call("status", "Analyzing intent...")
    
    # Should have token streaming
    mock_callback.assert_any_call("token", "funct") # First chunk of "function"
    
    # Should have completion
    # We check if complete was called with a JSON string
    complete_calls = [args for args in mock_callback.call_args_list if args[0][0] == "complete"]
    assert len(complete_calls) == 1
    
    payload = complete_calls[0][0][1]
    data = json.loads(payload)
    assert data["title"] == "Test Prompt"
    assert "code" in data
