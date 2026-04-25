# reqtool

A CLI for managing software requirements as flat markdown files with YAML frontmatter, tightly coupled to git commits.

## Philosophy

Requirements and tests are the primary asset. Code is generated to satisfy them.

The workflow is: agree on a requirement → write and commit tests → write and commit implementation. Each commit carries `Requirement: REQ-NNN` and `Phase:` trailers, so the full history of a requirement is one `git log --grep` away.

## Working with an AI agent

reqtool's three-phase workflow is structured tightly enough that an AI agent can drive it autonomously while the human stays in the loop where it matters — drafting and approving the requirement.

`reqtool init` installs an Agent Skills file at `.claude/skills/reqtool-workflow/SKILL.md`. Claude Code and other Skills-compatible clients activate this skill automatically when you ask the agent to add a feature, fix a bug, or change behaviour in the project. The skill instructs the agent to use `reqtool new` to draft a requirement, **stop for human review**, then proceed to tests and implementation only after approval — each phase committed with the appropriate `Phase:` trailer.

A typical session looks like this:

```
You:    Add a `reqtool show` command that prints a requirement and its commit history.
Agent:  [drafts requirements/REQ-NNN-show.md] Approve, edit, or push back?
You:    Approved, with one tweak: include git commits in the output.
Agent:  [writes failing tests, runs pytest, commits with Phase: tests]
        [implements, all tests pass, commits with Phase: implementation]
```

The init command also writes an `AGENTS.md` file describing the same workflow in plain markdown, for clients that don't speak Skills and for human contributors. Re-running `reqtool init` is a safe no-op; existing files are never overwritten.

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

## Workflow details

[AGENTS.md](AGENTS.md) is the canonical reference for the three-phase workflow. The bundled skill (installed by `reqtool init`) instructs AI agents to follow it.
