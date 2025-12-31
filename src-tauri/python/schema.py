from pydantic import BaseModel, Field
from typing import Literal

class WidgetDimensions(BaseModel):
    w: int = Field(2, description="Width of the widget in grid units (min 1, max 4)")
    h: int = Field(2, description="Height of the widget in grid units (min 1, max 4)")

class WidgetManifest(BaseModel):
    id: str = Field(..., description="Unique identifier for the widget")
    title: str = Field(..., description="Display title of the widget")
    dimensions: WidgetDimensions = Field(default_factory=WidgetDimensions)
    code: str = Field(..., description="The complete React component code string")

class AgentResponse(BaseModel):
    manifest: WidgetManifest
    status_updates: list[str] = Field(default_factory=list)
