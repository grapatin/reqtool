# AGENTS.md

## Working philosophy

This project uses requirement-driven development. Requirements and their tests are the primary asset. Code is generated to satisfy them and is treated as replaceable.

Do not write implementation code until a requirement exists, has been agreed with the user, and has committed tests.

## Single source of truth

The requirement file is the source of truth for the requirement's description, acceptance criteria, current status, and associated test file. The git history is the source of truth for commit-level details (who changed what, when, and which phase). Do not duplicate git-tracked information into the requirement file.

## Requirement file format

Requirements live in `requirements/REQ-NNN-slug.md` where NNN is a zero-padded three-digit number. Each file has YAML frontmatter followed by markdown sections.

Required frontmatter fields:
- `id`: e.g. `REQ-001`
- `title`: short human-readable title
- `status`: one of `draft`, `tests-written`, `implemented`, `deprecated`
- `created`: ISO date
- `test_file`: path to the test file, or null if not yet written
- `depends_on`: list of requirement IDs this depends on

Commit history is tracked via git, not in the requirement file. Use the `Requirement:` and `Phase:` trailers in commit messages (see workflow below) and query with `git log --grep="Requirement: REQ-NNN"` to find all commits related to a requirement.

Required sections: `## Intent`, `## Acceptance criteria`, `## Out of scope`.

## Workflow for any new feature or change

### Phase 1: Requirement
1. Draft a requirement file at `requirements/REQ-NNN-short-slug.md`.
2. Use the next available REQ number. Check existing files to find it; do not guess.
3. Stop and ask the user to review. Do not proceed until the user explicitly approves the requirement.

### Phase 2: Tests
1. Create `tests/test_req_NNN_<slug>.py` with one test per acceptance criterion. Test function names start with `test_req_NNN_`.
2. Run the tests and confirm they fail (no implementation yet).
3. Update the requirement file: set `test_file` to the test file path and `status` to `tests-written`.
4. Commit both the tests and the updated requirement file together with this message:
   ```
   Add tests for REQ-NNN: <title>

   Requirement: REQ-NNN
   Phase: tests
   ```

#### Testing conventions
Tests for commands that read or write files, run git operations, or otherwise touch the filesystem must use pytest's tmp_path fixture for isolation. The subprocess invocation must pass cwd=tmp_path (or equivalent) so the command under test operates inside the temp directory, not the project root.
Never write tests that operate on the real requirements/ directory or the real git history.

### Phase 3: Implementation
1. Write minimal code to make the tests pass.
2. Every function or class implementing a requirement must have `Implements: REQ-NNN` in its docstring.
3. Update the requirement file: set `status` to `implemented`.
4. Commit both the implementation and the updated requirement file together with this message:
   ```
   Implement REQ-NNN: <title>

   Requirement: REQ-NNN
   Phase: implementation
   ```

## Lookups

- From code to requirement: grep for `REQ-` in the file, or `git blame` the line and read the commit trailer.
- From requirement to tests: open the requirement file, read `test_file` in frontmatter.
- From requirement to commits: `git log --grep="Requirement: REQ-NNN"`
- Find all code implementing a requirement: `grep -rn "Implements: REQ-NNN" src/`

## When a bug is found

1. Do not fix the code first.
2. Write a new requirement describing the correct behaviour, or amend the existing requirement if the original was wrong.
3. Add a failing test for the bug. Commit with `Phase: tests`.
4. Fix the implementation. Commit with `Phase: fix` and reference the requirement.

## Hard rules

- Never modify an implementation without a corresponding requirement and test.
- Never write tests without an agreed requirement.
- Never invent a REQ number; check the filesystem.
- If a change affects multiple requirements, make one commit per requirement where possible.
- The bootstrap commit (REQ-000) is the only commit allowed without the full workflow.
