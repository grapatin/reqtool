# reqtool

A CLI for managing software requirements as flat markdown files with YAML frontmatter, tightly coupled to git commits.

## Philosophy

Requirements and tests are the primary asset. Code is generated to satisfy them.

The workflow is: agree on a requirement → write and commit tests → write and commit implementation. Each commit carries `Requirement: REQ-NNN` and `Phase:` trailers, so the full history of a requirement is one `git log --grep` away.

## Commands

- `reqtool init` — bootstrap the current directory for the workflow: creates `requirements/`, `tests/`, `AGENTS.md`, and a Claude Code skill at `.claude/skills/reqtool-workflow/SKILL.md`. Existing files are left untouched.
- `reqtool new <slug>` — create a new requirement file in `requirements/` with auto-incremented REQ number.
- `reqtool list` — list all requirements as tab-separated `id`, `status`, `title`, sorted by numeric ID.
- `reqtool show REQ-NNN` — print a requirement file followed by a `## Commits` section listing the git commits that reference it (via `Requirement:` / `Phase:` trailers).

## Getting started

Adopt the workflow in any project with one command:

```
cd path/to/your/project
reqtool init
reqtool new my-first-feature
```

`reqtool init` is idempotent and never overwrites existing files, so it's safe to re-run.

## Install (development)

```
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Workflow

See [AGENTS.md](AGENTS.md) for the requirement-driven development workflow that all changes to this project follow.
