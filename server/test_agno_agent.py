import pytest
import json
from unittest.mock import MagicMock
from agent import run_agent

def test_pydantic_agent_execution():
    # Mock callback
    mock_callback = MagicMock()
    
    # Run agent
    prompt = "Create a clock"
    run_agent(prompt, mock_callback)
    
    # Verify Status Updates
    # We expect "Agent received...", "Initializing...", "Streaming code..."
    status_calls = [args[0][1] for args in mock_callback.call_args_list if args[0][0] == "status"]
    assert len(status_calls) >= 3
    assert f"Agent received: {prompt}" in status_calls
    # assert "Initializing Pydantic Agent..." in status_calls
    assert "Initializing Agno Agent..." in status_calls
    
    # Verify Token Streaming
    # Should have called "token" many times
    status_calls = [args[0][1] for args in mock_callback.call_args_list if args[0][0] == "status"] 
    # print(f"DEBUG STATUSES: {status_calls}")
    
    assert "Initializing Agno Agent..." in status_calls

    token_calls = [args[0][1] for args in mock_callback.call_args_list if args[0][0] == "token"]
    assert len(token_calls) > 10
    full_code = "".join(token_calls)
    assert "Agno Time" in full_code
    
    # Verify Completion
    complete_calls = [json.loads(args[0][1]) for args in mock_callback.call_args_list if args[0][0] == "complete"]
    assert len(complete_calls) == 1
    manifest = complete_calls[0]
    
    assert manifest["title"] == "Agno AI Clock"
    assert manifest["dimensions"]["w"] == 2
    assert "code" in manifest
