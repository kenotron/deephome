# Project Specification: DeepHome (v1.0)
**Concept:** A "Generative OS" home screen where users "demand" apps/widgets that are built in real-time by local agents.

---

## 1. Core Vision & UX Strategy
- **User Personas:** Non-technical "Creators" who describe what they want rather than coding it.
- **Design Language:** Modern, glassmorphic, and minimal.
- **Primary Interaction:** A "Manus-style" floating dock/pill at the bottom center.
- **Manifestation:** Widgets don't just "load"; they are "constructed" on the grid with streaming code previews and fluid animations (Framer Motion).

---

## 2. Technical Stack (The "Cheap-as-Free" Stack)
- **App Shell:** Tauri v2 (Desktop/Mobile) or standard Web (React/Vue).
- **Embedded Agent:** Python-based agents (Agno or PydanticAI) embedded via **PyTauri/PyO3**.
- **Local Database:** **RxDB (Core)** using IndexedDB/OPFS for local-first speed and observability.
- **Cloud Sync:** **IBM Cloudant (Lite Tier)** acting as a CouchDB hub for multi-device sync.
- **Authentication:** Supabase (Free Tier).
- **Execution:** Sandboxed Iframes/Shadow DOM for rendering agent-generated components.

---

## 3. System Architecture
- **Local-First Sync:** RxDB handles all UI state. When the agent updates a widget, the UI reacts instantly; Cloudant handles background sync to other devices.
- **The "Data Bridge":** Tauri native HTTP plugins bypass CORS, allowing widgets to fetch external data (GitHub, Spotify, Weather) securely using keys stored in Tauri Stronghold.
- **Streaming Logic:**
    1. Frontend `invokes` a Tauri command.
    2. Rust calls the **Embedded Python Interpreter**.
    3. The Agent (Agno) streams tokens back to the UI via **Tauri Events**.
    4. On completion, a **Widget Manifest** is saved to RxDB.

---

## 4. The Widget Manifest Schema
Widgets are defined as portable JSON blobs:
- **Metadata:** Name, icon, dimensions.
- **View:** React/Tailwind code string to be compiled in-browser (e.g., via Sucrase).
- **DataModel:** A defined RxDB schema for the widget's own local persistence.
- **Capabilities:** Permissions for external API access.

---

## 5. Implementation Milestones
1. **The Shell:** Setup Tauri + React + RxDB (Local).
2. **The Bridge:** Embed Python using `python-build-standalone` and PyO3.
3. **The Agent:** Implement an Agno agent with "Tool Use" for file/web access.
4. **The Dock:** Build the streaming "Pill" UI for real-time widget generation.
5. **The Marketplace:** A discovery view where `is_public` manifests are synced from Cloudant.

---

## 6. Development Tools (Gemini AI Pro)
- **Primary IDE:** VS Code with **Gemini Code Assist** (1M+ context window).
- **Agentic Work:** **Google Antigravity** & **Jules** for autonomous multi-file refactoring.
- **Prototyping:** **Vibe Code** in Google AI Studio for rapid component testing.