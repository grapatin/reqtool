# reqtool

A CLI for managing software requirements as flat markdown files with YAML frontmatter, tightly coupled to git commits.

## Philosophy

Requirements and tests are the primary asset. Code is generated to satisfy them.

The workflow is: agree on a requirement → write and commit tests → write and commit implementation. Each commit carries `Requirement: REQ-NNN` and `Phase:` trailers, so the full history of a requirement is one `git log --grep` away.

## Commands

- `reqtool new <slug>` — create a new requirement file in `requirements/` with auto-incremented REQ number.
- `reqtool list` — list all requirements as tab-separated `id`, `status`, `title`, sorted by numeric ID.

## Status

`reqtool new` and `reqtool list` are implemented. See `requirements/` for the running list of requirements and their statuses.

## Install (development)

Once there is something to run, install in development mode:

```
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Workflow

See [AGENTS.md](AGENTS.md) for the requirement-driven development workflow that all changes to this project follow.
