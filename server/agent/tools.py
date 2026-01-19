from langchain_core.tools import tool

@tool
async def preview_widget(title: str, width: int = 2, height: int = 2) -> str:
    """
    Notify that the widget files have been created and are ready for preview.
    Call this AFTER you have written 'widget.jsx' (and optionally bundled it) and 'widget.json'.
    
    Args:
        title: Title of the widget.
        width: Width in grid units (1-4).
        height: Height in grid units (1-4).
    """
    # Simply return success. The actual file reading happens in the event loop hook
    # where we check for widget.bundled.js or widget.jsx
    return "Success: Preview triggered."
