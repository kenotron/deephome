# Technology Stack

This document records the official technology stack choices for the project, combining a modern "Local-First" application architecture with a high-performance "native" development toolchain.

## 1. Core Application Stack

### Frontend Framework
*   **Core**: **React** (Latest)
*   **Build Tool**: **Vite** (Fast, ESM-based build tool)
*   **Styling**: **Tailwind CSS** (Utility-first CSS framework)
*   **Animation**: **Framer Motion** (For fluid, "constructed" UI animations)

### App Shell & Architecture
*   **Shell**: **Tauri v2** (Desktop/Mobile cross-platform shell)
*   **Architecture**: Local-First, Generative OS

### Data & State
*   **Local Database**: **RxDB** (Reactive Database)
    *   **Storage Engine**: IndexedDB / OPFS (Origin Private File System) for speed.
*   **Cloud Sync**: **IBM Cloudant** (Lite Tier)
    *   **Role**: CouchDB-compliant hub for multi-device synchronization.
*   **Authentication**: **Supabase** (Free Tier)

## 2. AI & Backend

### Embedded Agent
*   **Framework**: **Agno** or **PydanticAI**
*   **Integration**: **PyTauri** / **PyO3**
    *   **Role**: Embeds a Python interpreter directly within the Tauri Rust backend to run agents locally.

## 3. Development Environment

Prioritizing high-performance tools written in Rust or Go.

### JavaScript / TypeScript
*   **Runtime & Package Manager**: `bun`
    *   *Purpose*: All-in-one fast JavaScript runtime and package manager.
*   **Compiler**: `@typescript/native-preview` (executable: `tsgo`)
    *   *Purpose*: Native Go-based TypeScript compiler for fast type checking.
*   **Linting**: `oxlint`
    *   *Purpose*: High-performance Rust-based linter.
*   **Formatting**: `oxfmt`
    *   *Purpose*: High-performance Rust-based formatter (Prettier compatible).

### Python
*   **Package Management**: `uv`
    *   *Purpose*: Fast Rust-based package installer and resolver.
*   **Linting & Formatting**: `ruff`
    *   *Purpose*: Fast Rust-based linter and formatter.
