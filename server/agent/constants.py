# Creation Skill Content (Standard SKILL.md format)
CREATION_SKILL_MD = """---
name: creation-skill
description: Capability to create interactive React components/apps by writing code to the filesystem.
---

# Creation Skill

## When to Use
- User asks for a Visual, UI, Interface, Dashboard, Component, App, or "Widget".
- Visual representation is the best way to answer.

## Instructions
To create a visual component, you must write TWO files to the current directory:
1. `widget.jsx`: The React component code.
2. `widget.json`: Metadata (title, width, height).

### Technical Rules
- Use `lucide-react` for icons.
- Use `tailwindcss` for styling.
- **ALWAYS include a background color** (e.g., `bg-slate-50`, `bg-white`).
- Use rounded corners (`rounded-xl`) and padding.
- `widget.jsx` MUST export a default component (`export default function Widget() ...`).
- **Use the `write` tool** to create files.
- **CRITICALLY IMPORTANT**: **DO NOT use leading slashes** in file paths.
  - ✅ CORRECT: `widget.jsx`
  - ❌ WRONG: `/widget.jsx` (This will fail with Read-only file system error)
- `widget.jsx` MUST export a default component (`export default function Widget() ...`).
- **Use `bundle_project`** to compile disparate files into a single bundle.

### Workflow
1. Write `widget.jsx` (and any other component files) using `write`.
2. check if write succeeded.
3. Call `bundle_project` to compile everything into `widget.bundled.js`.
4. Check if bundling succeeded.
5. Write `widget.json` using `write`.
6. Call `preview_widget` to show it to the user.

### layout Best Practices
- Calendars/Calculators: Use `grid` layout.
- Container: `w-full h-full flex flex-col`.
"""

PREVIEW_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Widget Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; }
        #root { width: 100%; height: 100%; }
    </style>
    <script type="importmap">
    {
        "imports": {
            "react": "https://esm.sh/react@18.2.0",
            "react/jsx-runtime": "https://esm.sh/react@18.2.0/jsx-runtime",
            "react-dom/client": "https://esm.sh/react-dom@18.2.0/client",
            "lucide-react": "https://esm.sh/lucide-react@0.263.1",
            "recharts": "https://esm.sh/recharts",
            "framer-motion": "https://esm.sh/framer-motion"
        }
    }
    </script>
</head>
<body>
    <div id="root"></div>
    <script type="module">
        import React from 'react';
        import { createRoot } from 'react-dom/client';
        import Widget from './widget.bundled.js';

        const root = createRoot(document.getElementById('root'));
        root.render(React.createElement(Widget));
    </script>
</body>
</html>"""
