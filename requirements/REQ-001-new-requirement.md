---
id: REQ-001
title: Create a new requirement file from the command line
status: tests-written
created: 2026-04-23
test_file: tests/test_req_001_new_command.py
depends_on: []
---

# REQ-001: Create a new requirement file from the command line

## Intent
Provide a `reqtool new <slug>` command that creates a new requirement file with correctly populated frontmatter and the standard section headings, auto-incrementing the requirement number based on existing files. This removes the manual work of copying templates and picking numbers, which is the main friction in Phase 1 of the workflow.

## Acceptance criteria

- Given an empty `requirements/` directory, running `reqtool new parse-gpx-header` creates a file at `requirements/REQ-001-parse-gpx-header.md`.
- Given an existing `requirements/REQ-001-foo.md`, running `reqtool new bar` creates `requirements/REQ-002-bar.md`.
- Given existing `REQ-001-foo.md` and `REQ-003-baz.md` (with a gap), the next number assigned is `REQ-004`, not `REQ-002`. The tool always picks max(existing) + 1.
- The created file contains valid YAML frontmatter with all required fields: `id`, `title`, `status`, `created`, `test_file`, `depends_on`.
- The `id` field matches the filename's REQ number.
- The `title` field is a human-readable version of the slug (e.g. `parse-gpx-header` becomes `Parse gpx header`).
- The `status` field is set to `draft`.
- The `created` field is today's date in ISO format (YYYY-MM-DD).
- The `test_file` field is `null`; `depends_on` is an empty list.
- The file body contains the three required section headings: `## Intent`, `## Acceptance criteria`, `## Out of scope`, each followed by a placeholder line.
- The tool prints the absolute path of the created file to stdout on success.
- Given a `requirements/` directory that does not exist, the tool creates it before writing the file.
- Given an invalid slug (empty, contains uppercase, contains spaces, contains underscores, starts with a digit, shorter than 3 chars, longer than 50 chars), the tool exits with a non-zero status and prints an error message to stderr explaining the rule that was violated. No file is created.
- Given no slug argument, the tool exits with a non-zero status and prints usage information.

## Out of scope
- Opening the file in `$EDITOR` after creation (future requirement).
- Interactive prompting for title or other fields (future requirement).
- Detecting or refusing duplicate slugs across different REQ numbers.
- Running any git operations.
- Populating `depends_on` automatically.