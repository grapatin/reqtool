---
id: REQ-003
title: Initialize a project for requirement-driven development
status: tests-written
created: "2026-04-24"
test_file: tests/test_req_003_init_command.py
depends_on: []
---

# REQ-003: Initialize a project for requirement-driven development

## Intent
Provide a `reqtool init` command that sets up a target project to use
the requirement-driven development workflow. Running it creates the
necessary directory structure, an AGENTS.md describing the workflow,
and an Agent Skills-compatible skill that instructs AI agents how to
follow the workflow using `reqtool`. This makes the methodology
portable: any project can adopt it with one command.

The command is safe to run on projects that already contain some of
the relevant artifacts. It creates only what is missing and never
modifies existing files or directories.

## Acceptance criteria

- For each of the four artifacts (`requirements/` directory, `tests/`
  directory, `AGENTS.md` file, and `.claude/skills/reqtool-workflow/SKILL.md`
  file), `reqtool init` checks whether it exists at the current working
  directory. If it does not exist, it is created, populated from a
  bundled template where applicable. If it exists, it is left untouched.
- When creating the skill's `SKILL.md`, any missing parent directories
  (`.claude/` and `.claude/skills/`) are created as needed. Existing
  parent directories are not modified.
- The tool never modifies, appends to, or overwrites an existing file
  or directory.
- The generated `SKILL.md` frontmatter contains at minimum a `name`
  field equal to `reqtool-workflow` and a non-empty `description` field
  describing what the skill does and when to use it.
- The generated `SKILL.md` is valid per the Agent Skills specification:
  frontmatter parses as YAML, the `name` matches the parent directory
  name, `name` is lowercase alphanumeric-with-hyphens, and `description`
  is 1-1024 characters.
- The generated `SKILL.md` body instructs an agent to follow the
  three-phase workflow (requirement, tests, implementation) and to use
  `reqtool new` and `reqtool list` where appropriate.
- The generated `AGENTS.md` references the installed skill and the
  three-phase workflow.
- On success, for each of the four artifacts, the tool prints to stdout
  a line indicating either `Created <path>` or `Skipped <path> (already
  exists)`.
- The tool exits with code 0 whenever it completes without error,
  regardless of whether artifacts were created or all were skipped.
  Re-running `reqtool init` on an already-initialized project is a
  successful no-op.
- If an unexpected error occurs during creation (permission denied,
  disk full, etc.), the tool exits with a non-zero code and prints the
  error to stderr. Artifacts already created in this run are left in
  place; the tool does not attempt rollback.

## Out of scope
- A `--force` flag to overwrite existing files (future requirement).
  The current behavior never overwrites; `--force` would change that.
- Merging template content into an existing `AGENTS.md` (future
  requirement).
- Detecting whether an existing `AGENTS.md` already describes the
  reqtool workflow. The tool checks only for file existence, not
  content.
- Creating an initial `REQ-000-bootstrap.md` in the target project
  (future requirement).
- Detecting the target project's language or adapting templates to it.
- Installing `reqtool` itself into the target project or its virtual
  environment. The skill assumes `reqtool` is available on PATH.
- Supporting skill locations other than `.claude/skills/`.
- Validating the generated skill using an external tool like
  `skills-ref`. The acceptance criteria above pin down enough structure
  that the project's own tests verify validity.
- Updating templates after initial install (future requirement; likely
  a separate `reqtool update` command).