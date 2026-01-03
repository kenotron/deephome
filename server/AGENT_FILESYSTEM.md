# Agent Filesystem Capabilities

Each widget now has a **real project directory** on disk where the agent can work like a developer!

## Directory Structure

```
server/
  projects/
    session_1234567890/      # One directory per session
      widget.jsx             # Main widget code (auto-created by create_widget)
      widget.json            # Widget metadata (auto-created)
      README.md              # Project README (auto-created)
      # ... plus any files the agent creates with write_file
      styles.css             # Example: agent can create additional files
      utils.js               # Example: helper functions
      config.json            # Example: configuration
```

### Auto-Generated Files

When `create_widget()` is called, these files are automatically created:

- **widget.jsx** - The React component code
- **widget.json** - Metadata (title, width, height, created_at)
- **README.md** - Project documentation (created once)

## What the Agent Can Do

With filesystem access, the agent has these tools:

1. **write_file** - Create new files
2. **read_file** - Read existing files
3. **edit_file** - Modify files with search/replace
4. **ls** - List directory contents
5. **glob** - Find files by pattern (e.g., `*.jsx`)
6. **grep** - Search file contents

## Example Conversation

**User**: "Create a calculator widget with clean separation of concerns"

**Agent**:
- Uses `write_file("/Calculator.jsx", ...)` to create main component
- Uses `write_file("/styles.css", ...)` for styling
- Uses `write_file("/operations.js", ...)` for calculator logic
- Calls `create_widget("Calculator", component_code, 2, 2)` to deploy
  - This auto-creates: `widget.jsx`, `widget.json`, `README.md`

**User** (later, clicks Edit): "Add a history feature"

**Agent** (session restored):
- Uses `read_file("/widget.jsx")` to see current code
- Uses `read_file("/operations.js")` to understand logic
- Uses `write_file("/History.jsx", ...)` to create history component
- Uses `edit_file("/widget.jsx", old_code, new_code)` to integrate history
- Calls `create_widget()` again to redeploy with updates

## Virtual Paths

The agent sees paths as:
- `/component.jsx`
- `/styles.css`

But they're actually stored in:
- `projects/session_1234567890/component.jsx`
- `projects/session_1234567890/styles.css`

This keeps sessions isolated and secure!

## Persistence

- **Project files**: Persist on disk across server restarts
- **Session history**: In-memory (lost on restart, but files remain)
- **Widget metadata**: Saved in RxDB with `projectPath` reference
