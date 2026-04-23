---
id: REQ-002
title: List requirements
status: draft
created: "2026-04-23"
test_file: null
depends_on: []
---

# REQ-002: List requirements

## Intent
Provide a `reqtool list` command that prints all requirements in the
project with their ID, status, and title. Users need a quick way to
see what requirements exist and where they are in the workflow without
manually scanning the `requirements/` directory.

## Acceptance criteria
- Given a project with no `requirements/` directory, `reqtool list` 
  prints nothing to stdout and exits with code 0.
- Given an empty `requirements/` directory, `reqtool list` prints 
  nothing to stdout and exits with code 0.
- Given a `requirements/` directory with valid REQ files, `reqtool list` 
  prints one line per requirement to stdout.
- Each line contains the requirement ID, status, and title, separated
  by single tab characters, in that order.
- Output is sorted by numeric ID ascending (REQ-001 before REQ-002 
  before REQ-010).
- Given malformed requirement files (unparseable YAML frontmatter, 
  or missing required fields `id`, `title`, or `status`), the tool 
  prints a warning to stderr naming each malformed file and the reason, 
  and continues processing the valid files. Exit code remains 0.
- Only files matching the pattern `REQ-NNN-*.md` are considered 
  requirement files. Other files in `requirements/` are ignored silently.

## Out of scope
- Filtering by status, ID range, or any other field (future requirement).
- Sorting by anything other than numeric ID (future requirement).
- Showing commit information (future requirement, likely part of 
  `reqtool show`).
- Output format options (JSON, CSV, table with headers) — future 
  requirement.
- Colored output or terminal formatting.
- Handling of requirements outside the `requirements/` directory.
