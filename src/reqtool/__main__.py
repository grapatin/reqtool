"""Entry point for the reqtool CLI.

Implements: REQ-001
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import click


_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_MIN_SLUG_LEN = 3
_MAX_SLUG_LEN = 50
_REQ_FILENAME_RE = re.compile(r"^REQ-(\d{3})-.*\.md$")


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


def _next_req_number(requirements_dir):
    """Return max(existing REQ-NNN) + 1, or 1 if the directory has no matches.

    Implements: REQ-001
    """
    if not requirements_dir.exists():
        return 1
    numbers = [
        int(m.group(1))
        for entry in requirements_dir.iterdir()
        if (m := _REQ_FILENAME_RE.match(entry.name))
    ]
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
    requirements_dir = Path.cwd() / "requirements"
    requirements_dir.mkdir(exist_ok=True)
    req_id = f"REQ-{_next_req_number(requirements_dir):03d}"
    title = _humanize_slug(slug)
    target = requirements_dir / f"{req_id}-{slug}.md"
    target.write_text(_render_file(req_id, title, date.today().isoformat()))
    click.echo(str(target.resolve()))


if __name__ == "__main__":
    main()
