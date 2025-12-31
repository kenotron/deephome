import pytest
import os
import json
import shutil
import asyncio
from unittest.mock import MagicMock, patch
from schema import WidgetManifest

# Import the module to test
# We need to make sure sys.path is correct if running from root
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from agent import generate_widget_stream, agent

MOCK_HTML_CODE = "<html><body><h1>Test Widget</h1></body></html>"
MOCK_MANIFEST = WidgetManifest(
    id="test-id",
    title="Test Widget",
    dimensions={"w": 2, "h": 2},
    code=MOCK_HTML_CODE
)

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
        yield

@pytest.fixture
def cleanup_generated():
    yield
    if os.path.exists("generated"):
        shutil.rmtree("generated")

@pytest.mark.asyncio
async def test_generate_widget_creates_file(mock_env, cleanup_generated):
    # Mock the Agent.run method
    # Agno's Agent.run returns a RunResponse usually, which has .content
    mock_response = MagicMock()
    mock_response.content = MOCK_MANIFEST
    
    # We need to mock the agent instance used in agent.py
    # Since 'agent' is imported from agent.py, we can construct a mock for it.
    # But agent.py instantiates 'agent' at module level.
    # We can patch 'agent.run' on the imported instance.
    
    # The agent.run is called in a loop.run_in_executor
    # So we simply patch agent.run
    
    with patch.object(agent, 'run', return_value=mock_response) as mock_run:
        prompt = "Create a test widget"
        events = []
        async for event in generate_widget_stream(prompt):
            events.append(event)
            
        # Check if we got status and complete
        status_events = [e for e in events if e[0] == 'status']
        complete_events = [e for e in events if e[0] == 'complete']
        
        assert len(complete_events) == 1
        
        # Verify Manifest
        manifest_json = complete_events[0][1]
        manifest = json.loads(manifest_json)
        
        assert manifest["title"] == "Test Widget"
        assert "url" in manifest
        assert manifest["url"].startswith("/generated/")
        assert manifest["url"].endswith(".html")
        
        # Verify File Creation
        generated_url = manifest["url"]
        # The URL is /generated/..., so file path is generated/... relative to CWD
        file_path = generated_url.lstrip("/")
        
        assert os.path.exists(file_path)
        with open(file_path, "r") as f:
            content = f.read()
            assert content == MOCK_HTML_CODE

@pytest.mark.asyncio
async def test_missing_api_key():
    with patch.dict(os.environ, {}, clear=True):
        events = []
        async for event in generate_widget_stream("foo"):
            events.append(event)
            
        complete_events = [e for e in events if e[0] == 'complete']
        assert len(complete_events) == 1
        result = json.loads(complete_events[0][1])
        assert "error" in result
        assert "OPENAI_API_KEY" in result["error"]
