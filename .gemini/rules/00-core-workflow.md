# Core Workflow: Plan -> Exec -> Validate

For every feature or significant change, you MUST follow this cycle:

1.  **PLAN**:
    *   Update `implementation_plan.md` first.
    *   Define the goal, changes, and specifically the **Verification Plan**.
    *   Get user approval if the change is architectural.

2.  **EXECUTE**:
    *   Implement the code changes.
    *   Update `task.md` to track progress.

3.  **VALIDATE**:
    *   **Backend**: Use scripts (`curl`, `python`, `node`) to verify logic in isolation.
    *   **Frontend**: Use `browser_subagent` to verify UI flows against `localhost`.
    *   You MUST prove the feature works before marking it done.
