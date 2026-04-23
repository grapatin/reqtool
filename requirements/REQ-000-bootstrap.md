---
id: REQ-000
title: Bootstrap project structure
status: implemented
created: 2026-04-23
test_file: null
test_commit: null
impl_commits: []
depends_on: []
---

# REQ-000: Bootstrap project structure

## Intent
Establish the minimum scaffolding needed to begin using the requirement-driven development workflow. This is the only requirement allowed to exist without following the Phase 1 → 2 → 3 workflow, because the workflow itself depends on this scaffolding existing.

## Acceptance criteria
- The repository has `requirements/`, `tests/`, and `src/reqtool/` directories
- `AGENTS.md` documents the workflow that all subsequent requirements must follow
- `pyproject.toml` declares the project and its console script entry point
- A README explains the project's purpose and current status
- The `reqtool` package is installable in development mode

## Out of scope
- Any actual `reqtool` functionality (deferred to REQ-001 onwards)
- Tests (there is nothing to test yet)
- CI configuration
- Packaging for distribution
