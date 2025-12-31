# Agent Development Workflow

This document records the mandatory workflow for all feature development in this project. The Agent must strictly follow this cycle for every task.

## 1. Plan
**Before writing code**, the Agent must:
*   Create or update `implementation_plan.md`.
*   Define the goal, technical changes, and specifically the **Verification Plan**.
*   Request user review if there are significant architectural decisions.

## 2. Execute
*   Implement the changes defined in the plan.
*   Update `task.md` to track progress (mark as in-progress `[/]`).
*   Keep changes atomic and compile-able.

## 3. Validate (CRITICAL)
The Agent must **autonomously verify** the work before handing it off to the user.

### A. Frontend / App Logic
*   **Tool**: `browser_subagent` (Playwright MCP).
*   **Target**: `http://localhost:5173` (Vite Dev Server).
*   **Action**:
    *   Spin up the dev server (`bun run dev`).
    *   Instruct the browser agent to perform specific user actions (click, type, navigate).
    *   Verify the expected UI states (elements appear, text changes, console logs).
*   **Note**: For Tauri verification in the browser, rely on the **Mock Mode** logic implemented in `App.tsx` if native APIs are unavailable.

### B. Backend / Internal Logic
*   **Tool**: Scripts (`curl`, `node`, `python`, `bun`).
*   **Action**:
    *   Write temporary or permanent test scripts (e.g., `src-tauri/python/test_agent.py`).
    *   Execute them in the terminal.
    *   Verify exit codes and output.

## 4. Document
*   Update `walkthrough.md` with the results of the verification.
*   Mark the task as completed `[x]` in `task.md`.
*   Notify the user with a summary of the validation results.
