
import os
import logging
from typing import List, Optional
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.graph.state import CompiledStateGraph

from .middleware import SkillsMiddleware

# Setup Logging
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_debug.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(message)s')

class SafeFilesystemBackend(FilesystemBackend):
    """
    A wrapper around FilesystemBackend that strictly enforces relative paths
    to prevent escaping the sandbox (root_dir).
    """
    def write(self, file_path: str, content: str, *args, **kwargs):
        # Strip leading slashes to ensure path is relative to root_dir
        safe_path = file_path.lstrip("/")
        logging.debug(f"SafeFilesystemBackend: writing to {safe_path} (orig: {file_path})")
        # Swallow extra args to avoid "unexpected argument" in base class
        return super().write(safe_path, content)
        
    # Also override read just in case
    def read(self, file_path: str, *args, **kwargs):
        safe_path = file_path.lstrip("/")
        # Swallow extra args
        return super().read(safe_path)

def create_skilled_deep_agent(
    model: BaseChatModel,
    root_dir: Path,
    skills_registry_path: Optional[str] = None,
    tools: Optional[List[BaseTool]] = None,
    system_prompt: str = "",
    name: str = "DeepAgent"
) -> CompiledStateGraph:
    """
    Creates a Deep Agent equipped with Skills via Middleware and Filesystem Backend.
    """
    
    # 1. Setup Backend (Safe Filesystem)
    backend = SafeFilesystemBackend(root_dir=root_dir)
    
    # 2. Setup Middleware
    skills_middleware = SkillsMiddleware(skills_registry_path)
            
    # 3. Create Agent using Library
    agent = create_deep_agent(
        model=model,
        backend=backend,
        tools=tools, 
        system_prompt=system_prompt, # Passed prompt + middleware prompt
        middleware=[skills_middleware]
    )
    
    logging.info(f"Created Skilled DeepAgent via library with skills from {skills_registry_path}")
    
    return agent
