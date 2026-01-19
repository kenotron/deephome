import logging
import yaml
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path

from langchain_core.messages import SystemMessage
from langchain.agents.middleware.types import AgentMiddleware

@dataclass
class SkillMetadata:
    name: str 
    description: str
    registry: str = "unknown"
    path: str = ""
    instructions: str = ""

def load_skill_from_path(skill_path: Path, registry_name: str = "user") -> Optional[SkillMetadata]:
    """
    Parses a SKILL.md file. 
    Expects YAML frontmatter + Markdown content.
    """
    if not skill_path.exists():
        logging.warning(f"Skill path not found: {skill_path}")
        return None
        
    try:
        with open(skill_path, "r") as f:
            content = f.read()
            
        # Basic Frontmatter parsing
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_yaml = parts[1]
                markdown_body = parts[2].strip()
                
                meta = yaml.safe_load(frontmatter_yaml)
                
                return SkillMetadata(
                    name=meta.get("name", skill_path.parent.name),
                    description=meta.get("description", ""),
                    registry=registry_name,
                    path=str(skill_path),
                    instructions=markdown_body
                )
    except Exception as e:
        logging.error(f"Error loading skill at {skill_path}: {e}")
    
    return None

def load_skills_instructions(registry_path: str, registry_name: str = "user") -> str:
    """Loads all skills from a registry and returns the combined system prompt instructions."""
    skills_text = ""
    base_path = Path(registry_path)
    if not base_path.exists():
        return ""
        
    # Iterate over subdirectories looking for SKILL.md
    found_skills = []
    for item in base_path.iterdir():
        if item.is_dir():
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                skill = load_skill_from_path(skill_md, registry_name)
                if skill:
                    found_skills.append(skill)
    
    if found_skills:
        skills_text += "\n\n## AGENT SKILLS"
        for skill in found_skills:
            skills_text += f"\n\n### {skill.name}\n{skill.description}\n\n{skill.instructions}"
            
    logging.info(f"Loaded {len(found_skills)} skills from {registry_path}")
    return skills_text

class SkillsMiddleware(AgentMiddleware):
    """
    Middleware that loads skills from a registry and injects them into the agent's system prompt
    at the start of execution.
    """
    def __init__(self, registry_path: Optional[str]):
        self.instructions = ""
        if registry_path:
            self.instructions = load_skills_instructions(registry_path)
        
    def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Injects skills instructions into the messages list."""
        if not self.instructions:
            return state
            
        messages = state.get("messages", [])
        if not messages:
            messages = []
            
        # Create SystemMessage
        skill_msg = SystemMessage(content=self.instructions)
        
        # We append to ensure it's present. 
        # Ideally, we'd merge with existing system prompt, but appending works for most models.
        messages = list(messages) + [skill_msg]
        
        state["messages"] = messages
        return state
