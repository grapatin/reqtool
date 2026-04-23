# reqtool

A CLI for managing software requirements as flat markdown files with YAML frontmatter, tightly coupled to git commits.

## Philosophy

Requirements and tests are the primary asset. Code is generated to satisfy them.

Each requirement records the git commit that added its tests and the commits that implemented it. The workflow is: agree on a requirement → write and commit tests → write and commit implementation.

## Status

Bootstrap phase. No features implemented yet. REQ-001 will add `reqtool new`.

## Install (development)

Once there is something to run, install in development mode:

```
pip install -e .
```

## Workflow

See [AGENTS.md](AGENTS.md) for the requirement-driven development workflow that all changes to this project follow.
