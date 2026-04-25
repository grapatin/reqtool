"""Entry point for the reqtool CLI.

Implements: REQ-001
Implements: REQ-002
Implements: REQ-003
Implements: REQ-004
"""
from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

import click
import yaml

from .registry import iter_req_files, requirements_dir


_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_MIN_SLUG_LEN = 3
_MAX_SLUG_LEN = 50
_REQUIRED_FIELDS = ("id", "title", "status")
_REQ_ID_RE = re.compile(r"^REQ-\d{3}$")


_AGENTS_TEMPLATE = """\
# AGENTS.md

This project uses requirement-driven development with [reqtool](https://github.com/grapatin/reqtool).

## Workflow

Follow the three-phase workflow for every change.

### Phase 1: Requirement
Run `reqtool list` to see existing requirements. Use `reqtool new <slug>` to draft a new one in `requirements/`. Fill in `## Intent`, `## Acceptance criteria`, and `## Out of scope`. Stop and ask the user to approve before proceeding.

### Phase 2: Tests
Create `tests/test_req_NNN_<slug>.py` with one test per acceptance criterion. Confirm all tests fail (no implementation yet). Update the requirement file: set `test_file` and `status: tests-written`. Commit both with the trailers `Requirement: REQ-NNN` and `Phase: tests`.

### Phase 3: Implementation
Write minimal code to make the tests pass. Every function or class implementing the requirement must include `Implements: REQ-NNN` in its docstring. Update the requirement file: `status: implemented`. Commit both with the trailers `Requirement: REQ-NNN` and `Phase: implementation`.

## Skill for AI agents

The skill at `.claude/skills/reqtool-workflow/SKILL.md` instructs AI agents (e.g. Claude Code) to follow the three-phase workflow described above. Activate `reqtool-workflow` whenever you are asked to add a feature, fix a bug, or change behaviour in this project.

## Useful commands

- `reqtool new <slug>` — create a new requirement file with the next available REQ number.
- `reqtool list` — list all requirements as tab-separated id, status, title.
- `git log --grep="Requirement: REQ-NNN"` — find all commits related to a requirement.
"""


_SKILL_TEMPLATE = """\
---
name: reqtool-workflow
description: "Use this skill when working in a project that follows requirement-driven development with reqtool. The skill instructs the agent to follow a three-phase workflow (requirement, tests, implementation) and to use reqtool commands for managing requirement files. Apply whenever the user asks to add a feature, fix a bug, or change behaviour in such a project."
---

# Reqtool workflow skill

This project uses requirement-driven development. Requirements and their tests are the primary asset. Code is generated to satisfy them.

## When to use this skill

Activate this skill whenever you are asked to add a feature, fix a bug, or otherwise change the behaviour of this project. Do not write implementation code without first agreeing on a requirement and committing tests.

## Three-phase workflow

For every change, work through the three phases in order. Do not skip phases.

### Phase 1: Requirement
1. Run `reqtool list` to see existing requirements and their statuses.
2. Run `reqtool new <slug>` to create a new requirement file. The slug must be lowercase, 3-50 characters, using only letters, digits, and hyphens.
3. Fill in `## Intent`, `## Acceptance criteria`, and `## Out of scope`.
4. Stop and ask the user to review the requirement. Do not proceed until they approve.

### Phase 2: Tests
1. Create `tests/test_req_NNN_<slug>.py` with one test per acceptance criterion. Test function names start with `test_req_NNN_`.
2. Run the tests and confirm they all fail.
3. Update the requirement file: set `test_file` and `status: tests-written`.
4. Commit both the tests and the updated requirement file with the trailers `Requirement: REQ-NNN` and `Phase: tests`.

### Phase 3: Implementation
1. Write minimal code to make the tests pass.
2. Every function or class implementing the requirement must include `Implements: REQ-NNN` in its docstring.
3. Update the requirement file: `status: implemented`.
4. Commit both the implementation and the updated requirement file with the trailers `Requirement: REQ-NNN` and `Phase: implementation`.

## Useful commands

- `reqtool new <slug>` — create a new requirement file with the next available REQ number.
- `reqtool list` — list all requirements as tab-separated id, status, title.
- `git log --grep="Requirement: REQ-NNN"` — find all commits related to a requirement.

## Hard rules

- Never modify implementation without a corresponding requirement and test.
- Never write tests without an approved requirement.
- Never invent a REQ number; let `reqtool new` assign it.

## When a bug is found in production

1. Do not fix the code first.
2. Write a new requirement describing the correct behaviour, or amend the existing requirement if the original was wrong.
3. Add a failing test for the bug. Commit with `Phase: tests`.
4. Fix the implementation by making sure all tests pass.
5. Commit with `Phase: fix` and reference the requirement.

## Lookups

- From code to requirement: grep for `REQ-` in the file, or `git blame` the line and read the commit trailer.
- From requirement to tests: open the requirement file, read `test_file` in frontmatter.
- From requirement to commits: `git log --grep="Requirement: REQ-NNN"`
- Find all code implementing a requirement: `grep -rn "Implements: REQ-NNN" src/`
"""


def _validate_slug(slug):
    """Raise click.UsageError if the slug violates a rule.

    Implements: REQ-001
    """
    if slug == "":
        raise click.UsageError("slug must not be empty")
    if len(slug) < _MIN_SLUG_LEN:
        raise click.UsageError(
            f"slug must be at least {_MIN_SLUG_LEN} characters (got {len(slug)})"
        )
    if len(slug) > _MAX_SLUG_LEN:
        raise click.UsageError(
            f"slug must be at most {_MAX_SLUG_LEN} characters (got {len(slug)})"
        )
    if not (slug[0].isascii() and slug[0].isalpha() and slug[0].islower()):
        raise click.UsageError("slug must start with a lowercase letter")
    if _SLUG_RE.match(slug):
        return
    if any(c.isupper() for c in slug):
        raise click.UsageError("slug must not contain uppercase letters")
    if " " in slug:
        raise click.UsageError("slug must not contain spaces")
    if "_" in slug:
        raise click.UsageError("slug must not contain underscores")
    raise click.UsageError(
        "slug may only contain lowercase letters, digits, and hyphens"
    )


def _next_req_number(directory):
    """Return max(existing REQ-NNN) + 1, or 1 if the directory has no matches.

    Implements: REQ-001
    """
    numbers = [n for n, _ in iter_req_files(directory)]
    return max(numbers) + 1 if numbers else 1


def _humanize_slug(slug):
    """Turn 'parse-gpx-header' into 'Parse gpx header'.

    Implements: REQ-001
    """
    return slug.replace("-", " ").capitalize()


def _render_file(req_id, title, today_iso):
    """Return the full markdown content for a fresh requirement file.

    Implements: REQ-001
    """
    return (
        "---\n"
        f"id: {req_id}\n"
        f"title: {title}\n"
        "status: draft\n"
        f'created: "{today_iso}"\n'
        "test_file: null\n"
        "depends_on: []\n"
        "---\n"
        "\n"
        f"# {req_id}: {title}\n"
        "\n"
        "## Intent\n"
        "TODO: describe the intent.\n"
        "\n"
        "## Acceptance criteria\n"
        "TODO: list acceptance criteria.\n"
        "\n"
        "## Out of scope\n"
        "TODO: list out-of-scope items.\n"
    )


def _parse_frontmatter(path):
    """Parse YAML frontmatter from a requirement file.

    Returns (frontmatter_dict, None) on success, (None, error_message) on failure.

    Implements: REQ-002
    """
    content = path.read_text()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, "missing YAML frontmatter"
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return None, f"malformed YAML: {e}"
    if not isinstance(fm, dict):
        return None, "frontmatter is not a mapping"
    return fm, None


@click.group()
def main():
    """Requirement-driven development CLI.

    Implements: REQ-001
    """


@main.command("new")
@click.argument("slug")
def new(slug):
    """Create a new requirement file in ./requirements/.

    Implements: REQ-001
    """
    _validate_slug(slug)
    directory = requirements_dir()
    directory.mkdir(exist_ok=True)
    req_id = f"REQ-{_next_req_number(directory):03d}"
    title = _humanize_slug(slug)
    target = directory / f"{req_id}-{slug}.md"
    target.write_text(_render_file(req_id, title, date.today().isoformat()))
    click.echo(str(target.resolve()))


@main.command("list")
def list_cmd():
    """List all requirements: one tab-separated line of id, status, title.

    Implements: REQ-002
    """
    directory = requirements_dir()
    entries = []
    for number, path in iter_req_files(directory):
        fm, error = _parse_frontmatter(path)
        if error is not None:
            click.echo(f"{path.name}: {error}", err=True)
            continue
        missing = [f for f in _REQUIRED_FIELDS if f not in fm]
        if missing:
            click.echo(
                f"{path.name}: missing required field(s): {', '.join(missing)}",
                err=True,
            )
            continue
        entries.append((number, fm["id"], fm["status"], fm["title"]))
    entries.sort(key=lambda e: e[0])
    for _, id_, status, title in entries:
        click.echo(f"{id_}\t{status}\t{title}")


@main.command("init")
def init_cmd():
    """Initialize the current directory for requirement-driven development.

    Creates `requirements/`, `tests/`, `AGENTS.md`, and a Claude Code skill
    at `.claude/skills/reqtool-workflow/SKILL.md`. Each artifact is created
    only if missing; existing files and directories are left untouched.

    Implements: REQ-003
    """
    cwd = Path.cwd()
    artifacts = (
        ("dir", cwd / "requirements", None),
        ("dir", cwd / "tests", None),
        ("file", cwd / "AGENTS.md", _AGENTS_TEMPLATE),
        (
            "file",
            cwd / ".claude" / "skills" / "reqtool-workflow" / "SKILL.md",
            _SKILL_TEMPLATE,
        ),
    )
    for kind, path, content in artifacts:
        if path.exists():
            click.echo(f"Skipped {path} (already exists)")
            continue
        try:
            if kind == "dir":
                path.mkdir(parents=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
        except OSError as e:
            raise click.ClickException(f"failed to create {path}: {e}")
        click.echo(f"Created {path}")


def _commits_section_lines(req_id):
    """Return the lines of the `## Commits` section for the given REQ ID.

    Implements: REQ-004
    """
    try:
        rp = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ["(not a git repository)"]
    if rp.returncode != 0:
        return ["(not a git repository)"]

    log = subprocess.run(
        [
            "git", "log",
            "--reverse",
            "--abbrev=7",
            "--format=%h%x09%s%x09%(trailers:key=Phase,valueonly)",
            f"--grep=Requirement: {req_id}",
        ],
        capture_output=True,
        text=True,
    )
    if log.returncode != 0:
        return ["(none)"]

    lines = []
    for raw in log.stdout.splitlines():
        parts = raw.split("\t")
        if len(parts) < 3:
            continue
        sha, subject, phase = parts[0], parts[1], parts[2]
        phase_value = phase.strip() or "-"
        lines.append(f"{sha}\t{phase_value}\t{subject}")

    return lines if lines else ["(none)"]


@main.command("show")
@click.argument("req_id")
def show_cmd(req_id):
    """Print a requirement file followed by its commit history.

    Implements: REQ-004
    """
    if not _REQ_ID_RE.match(req_id):
        raise click.UsageError(
            f"argument must be in the form 'REQ-NNN' (literal 'REQ-' "
            f"followed by exactly three digits); got {req_id!r}"
        )

    directory = requirements_dir()
    matches = (
        sorted(directory.glob(f"{req_id}-*.md")) if directory.exists() else []
    )

    if len(matches) == 0:
        raise click.ClickException(f"no requirement file found for {req_id}")
    if len(matches) > 1:
        names = "\n".join(f"  {p.name}" for p in matches)
        raise click.ClickException(
            f"ambiguous match for {req_id}; multiple files found:\n{names}"
        )

    path = matches[0]
    click.echo(path.read_text(), nl=False)
    click.echo()
    click.echo("## Commits")
    for line in _commits_section_lines(req_id):
        click.echo(line)


if __name__ == "__main__":
    main()
