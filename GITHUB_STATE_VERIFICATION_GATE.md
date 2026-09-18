# GitHub State Verification Gate

**STATUS: LOCKED / NON-NEGOTIABLE**

This repository follows a **GitHub State Verification Before Progression** rule.

## Mandatory rule

After **every repository change** and **before starting the next project step**, the project lead must verify the live GitHub state of the authorized repository:

1. Confirm the latest `main` commit SHA.
2. Confirm the relevant GitHub Actions workflow run was triggered for that exact SHA.
3. Wait for the run to reach a terminal state before declaring the step validated.
4. Inspect the job/check result and identify the failed step if unsuccessful.
5. A `failure`, `cancelled`, `timed_out`, `action_required`, `startup_failure`, or otherwise non-success validation blocks progression.
6. If a failure occurs, diagnose and repair it first. Do not stack new feature work on top of an unverified/broken state.
7. Re-run validation after the repair and continue only from a green state.
8. Never infer that GitHub is green from a screenshot, commit existence, local reasoning, or a previous run. The check must correspond to the current commit being promoted.
9. If the workflow is still `queued` or `in_progress`, the state is **NOT YET VERIFIED** and the next implementation gate is blocked.
10. The final project status must record the verified commit SHA and workflow result.

## Required progression protocol

`CHANGE -> PUSH -> GITHUB STATE CHECK -> CI TERMINAL RESULT -> FAILURE FORENSICS IF NEEDED -> GREEN GATE -> NEXT CHANGE`

For project-driving commands such as **next**, this gate is applied automatically.

## Scope

This rule applies to:
- source-code changes
- tests
- configuration
- workflows
- documentation that records project state
- architecture changes
- integration changes
- any commit intended to become the new project baseline

Live trading remains independently gated by the project's safety and execution controls. A green CI result does **not** authorize live capital deployment.

## Evidence standard

A GitHub Actions run is authoritative for CI validation only when its `head_sha` exactly matches the commit being promoted and its relevant test job has completed successfully. GitHub documents that workflow runs expose status/conclusion and job-level results through Actions/Checks.