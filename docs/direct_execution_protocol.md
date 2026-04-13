# Direct Execution Protocol (Root Agent Mode)

This protocol defines how the Pickle Rick root agent handles the entire engineering lifecycle directly, without spawning sub-agents (Mortys).

## 1. Overview
Direct Execution Mode is triggered when the `no_spawning` flag is set to `true` in the session state. In this mode, Pickle Rick acts as both Manager and Implementer within the same continuous session.

## 2. Phase Transitions
Even without spawning, the strict phase boundaries must be maintained. Each phase must result in the required artifacts before moving to the next.

| Phase | Artifact(s) | Action |
| :--- | :--- | :--- |
| **PRD** | `prd.md` | Define scope and requirements. |
| **Breakdown** | `linear_ticket_*.md` | Create atomic implementation tasks. |
| **Research** | `research_*.md` | Document existing code and patterns. |
| **Research Review** | `research_review.md` | Audit research for objectivity. |
| **Plan** | `plan_*.md` | Draft technical implementation plan. |
| **Plan Review** | `plan_review.md` | Audit plan for safety and soundness. |
| **Implement** | Code Changes | Execute plan with TDD. |
| **Verify** | Test Results | Run automated tests and build. |

## 3. Direct Implementation Flow
When a ticket is selected for implementation in Direct Mode:
1.  **Manager Transition**: Pickle Rick announces the switch from Manager to Implementer role.
2.  **Skill Activation**: Implementation skills (`code-researcher`, `implementation-planner`, `code-implementer`) are activated directly in the root session.
3.  **Context Management**: The agent must use aggressive summarization after each phase to keep the context window lean.
4.  **Verification**: The root agent must explicitly run tests and builds before marking a ticket as 'Done'.

## 4. Documentation Mandatory
The following files MUST exist in the ticket directory (`${SESSION_ROOT}/[ticket_id]/`) before a ticket can be closed:
- `research_YYYY-MM-DD.md`
- `research_review.md`
- `plan_YYYY-MM-DD.md`
- `plan_review.md`

## 5. Exit Criteria
A session is only complete when ALL tickets in the breakdown are marked as 'Done' and all lifecycle documentation is present.
