# DeepHome Development Roadmap

This document breaks down the [PRD](./PRD.md) into systematic implementation phases to ensure reliability and incremental value.

## Phase 1: Foundation (Canvas & Generation Core)
**Goal:** A stable dashboard where widgets can be generated, previewed, placed, and persisted reliably.

- [ ] **Canvas Repair (`Grid.tsx`)**
    - [ ] Fix GridStack initialization and layout thrashing.
    - [ ] Ensure drag-and-drop state is correctly saved to RxDB.
    - [ ] Add "Layout Lock" vs "Edit Mode" toggle.
- [ ] **Widget Generation Pipeline**
    - [ ] Verify `agent.py` -> Frontend streaming pipeline.
    - [ ] Ensure widget assets (HTML/JS/CSS) are served correctly from `generated/`.
    - [ ] Fix `AgentConsole` preview iframe loading.
- [ ] **Persistence Loop**
    - [ ] "Confirm Widget" action must reliably add to RxDB and appear on Grid immediately.
    - [ ] Ensure persistence survives page refresh.

## Phase 2: Agent Capabilities & Smart Widgets
**Goal:** Move from static HTML widgets to dynamic React widgets with local state.

- [ ] **Dynamic Widget Engine**
    - [ ] Implement browser-side compilation (Sucrase/Babel) for `DynamicWidget.tsx`.
    - [ ] Update `agent.py` to generate React components instead of vanilla HTML.
- [ ] **Manifest V2 Implementation**
    - [ ] Enforce strict JSON Schema for manifests (View, DataModel, Capabilities).
    - [ ] Update RxDB schema to support widget-specific local storage.

## Phase 3: The Data Bridge & Security
**Goal:** Allow widgets to consume external APIs securely.

- [ ] **Tauri Data Bridge**
    - [ ] Implement Tauri Command for HTTP requests (bypassing CORS).
    - [ ] Create `useDeepHome` hook for widgets to access the bridge.
- [ ] **Security Sandbox**
    - [ ] Harden Iframe CSP (Content Security Policy).
    - [ ] Implement permission prompts for API access.

## Phase 4: Ecosystem (Sync & Scale)
**Goal:** Multi-device sync and community sharing.

- [ ] **Cloudant Sync**
    - [ ] Connect App to IBM Cloudant (or compatible CouchDB).
    - [ ] Verify real-time sync across two local instances.
- [ ] **Marketplace/Discovery**
    - [ ] Create "Explore" UI for public widgets.
    - [ ] Implement "Install" flow from Marketplace.
