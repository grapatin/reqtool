"""Entry point for the reqtool CLI.

Implements: REQ-001
Implements: REQ-002
"""
from __future__ import annotations

import re
from datetime import date

import click
import yaml

from .registry import iter_req_files, requirements_dir


_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_MIN_SLUG_LEN = 3
_MAX_SLUG_LEN = 50
_REQUIRED_FIELDS = ("id", "title", "status")


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


if __name__ == "__main__":
    main()
