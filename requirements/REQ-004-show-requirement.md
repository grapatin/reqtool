---
id: REQ-004
title: Show a requirement and its commit history
status: tests-written
created: "2026-04-25"
test_file: tests/test_req_004_show_command.py
depends_on: []
---

# REQ-004: Show a requirement and its commit history

## Intent

Provide a `reqtool show REQ-NNN` command that prints the unmodified contents of a single requirement file followed by a summary of the git commits associated with that requirement via the `Requirement: REQ-NNN` trailer convention. The command makes a requirement and the work done against it visible in one place without manually running `git log --grep`.

## Acceptance criteria

- The command takes exactly one positional argument in the canonical form `REQ-NNN`: the literal prefix `REQ-` followed by exactly three digits. Numeric shorthand (`1`, `001`) and slug forms are not accepted.
- An argument that does not match `^REQ-\d{3}$` causes the command to exit with a non-zero status and print a clear error to stderr explaining the expected form. No stdout output. No file is read.
- Invoked with no argument, the command exits non-zero with a usage message on stderr (standard click missing-argument behaviour).
- A well-formed `REQ-NNN` argument resolves to the unique file matching `requirements/REQ-NNN-*.md` in the current working directory.
- On success, stdout contains the unmodified contents of the resolved requirement file (frontmatter and body, byte-for-byte), followed by a `## Commits` section. The file content is not parsed, normalised, or rendered.
- The `## Commits` section lists, in chronological order (oldest first), one tab-separated line per commit whose message contains the trailer `Requirement: REQ-NNN`. Each line contains: the 7-character short SHA, the value of the commit's `Phase:` trailer, and the commit subject, in that order.
- If a matching commit's message does not contain a `Phase:` trailer, the Phase column contains the literal string `-` (single hyphen). The line is still included.
- If zero commits match, the `## Commits` section contains a single line `(none)`.
- If the current working directory is not inside a git repository (or `git` is unavailable on `PATH`), the `## Commits` section contains a single line `(not a git repository)` instead of commit data — an explicit notice, not silent omission.
- Display is not validation: a malformed requirement file (unparseable YAML, missing required fields, extra fields, etc.) is still shown verbatim. No warnings, no stderr output. The only failure modes are file-not-found and ambiguous match.
- File-not-found: when no file matches `requirements/REQ-NNN-*.md`, the command exits non-zero with an error on stderr that names the requested REQ ID. No stdout output.
- Ambiguous match: when more than one file matches `requirements/REQ-NNN-*.md`, the command exits non-zero with an error on stderr that lists each colliding filename. No stdout output.
- The command exits with code 0 whenever the requested requirement was found and shown, regardless of whether any commits matched or whether the directory is a git repository.

## Out of scope

- Resolving a requirement by slug or by bare numeric ID (e.g. `1`, `001`). Only the canonical `REQ-NNN` form is accepted.
- A `--json` flag or any structured/machine output format (future requirement when a concrete need appears).
- Editing the requirement in `$EDITOR` (future requirement, likely `reqtool edit`).
- Showing commit diffs, patch contents, or per-file changes — only short SHA, phase, and subject for each commit.
- Showing the body of the test file referenced by the `test_file` frontmatter field.
- Validating frontmatter, body structure, or content. This command displays; validation belongs to a future `reqtool check` or similar.
- Pagination, colour, or terminal-width-aware formatting.
- Looking up requirements outside the current working directory's `requirements/` (e.g. across multiple projects, parent directories, or absolute paths).
- Behaviour when the git repository is corrupt or `git` returns errors other than "not a repo". Error handling beyond the basic "not a git repository" notice is a future requirement if the need arises.
- A `--no-commits` flag to omit the Commits section. The section is always present.
