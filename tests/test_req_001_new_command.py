"""Tests for REQ-001: Create a new requirement file from the command line."""
from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import pytest
import yaml


def run_new(slug, cwd):
    args = ["reqtool", "new"]
    if slug is not None:
        args.append(slug)
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def parse_requirement_file(path):
    content = path.read_text()
    parts = content.split("---", 2)
    assert len(parts) == 3, f"expected two '---' delimiters, got {len(parts) - 1}"
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2]
    return frontmatter, body


def test_req_001_creates_first_file_in_empty_dir(tmp_path):
    result = run_new("parse-gpx-header", tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert (tmp_path / "requirements" / "REQ-001-parse-gpx-header.md").exists()


def test_req_001_increments_after_existing(tmp_path):
    (tmp_path / "requirements").mkdir()
    (tmp_path / "requirements" / "REQ-001-foo.md").write_text("---\nid: REQ-001\n---\n")
    result = run_new("bar", tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert (tmp_path / "requirements" / "REQ-002-bar.md").exists()


def test_req_001_uses_max_plus_one_with_gaps(tmp_path):
    (tmp_path / "requirements").mkdir()
    (tmp_path / "requirements" / "REQ-001-foo.md").write_text("---\nid: REQ-001\n---\n")
    (tmp_path / "requirements" / "REQ-003-baz.md").write_text("---\nid: REQ-003\n---\n")
    result = run_new("qux", tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert (tmp_path / "requirements" / "REQ-004-qux.md").exists()
    assert not (tmp_path / "requirements" / "REQ-002-qux.md").exists()


def test_req_001_frontmatter_has_all_required_fields(tmp_path):
    run_new("parse-gpx-header", tmp_path)
    fm, _ = parse_requirement_file(
        tmp_path / "requirements" / "REQ-001-parse-gpx-header.md"
    )
    required = [
        "id",
        "title",
        "status",
        "created",
        "test_file",
        "depends_on",
    ]
    missing = [f for f in required if f not in fm]
    assert missing == [], f"missing frontmatter fields: {missing}"
    for forbidden in ("test_commit", "impl_commits"):
        assert forbidden not in fm, (
            f"generated file should not contain legacy field {forbidden!r}"
        )


def test_req_001_id_matches_filename_number(tmp_path):
    run_new("parse-gpx-header", tmp_path)
    fm, _ = parse_requirement_file(
        tmp_path / "requirements" / "REQ-001-parse-gpx-header.md"
    )
    assert fm["id"] == "REQ-001"


def test_req_001_title_is_humanized_slug(tmp_path):
    run_new("parse-gpx-header", tmp_path)
    fm, _ = parse_requirement_file(
        tmp_path / "requirements" / "REQ-001-parse-gpx-header.md"
    )
    assert fm["title"] == "Parse gpx header"


def test_req_001_status_is_draft(tmp_path):
    run_new("parse-gpx-header", tmp_path)
    fm, _ = parse_requirement_file(
        tmp_path / "requirements" / "REQ-001-parse-gpx-header.md"
    )
    assert fm["status"] == "draft"


def test_req_001_created_is_today_iso(tmp_path):
    run_new("parse-gpx-header", tmp_path)
    fm, _ = parse_requirement_file(
        tmp_path / "requirements" / "REQ-001-parse-gpx-header.md"
    )
    assert fm["created"] == date.today().isoformat()


def test_req_001_nullable_and_list_defaults(tmp_path):
    run_new("parse-gpx-header", tmp_path)
    fm, _ = parse_requirement_file(
        tmp_path / "requirements" / "REQ-001-parse-gpx-header.md"
    )
    assert fm["test_file"] is None
    assert fm["depends_on"] == []


def test_req_001_body_has_required_sections(tmp_path):
    run_new("parse-gpx-header", tmp_path)
    _, body = parse_requirement_file(
        tmp_path / "requirements" / "REQ-001-parse-gpx-header.md"
    )
    for heading in ("## Intent", "## Acceptance criteria", "## Out of scope"):
        assert heading in body, f"missing section: {heading}"
        idx = body.index(heading)
        after_lines = body[idx + len(heading):].splitlines()
        non_blank = [ln for ln in after_lines if ln.strip()]
        assert non_blank, f"no content after {heading}"
        assert not non_blank[0].startswith("## "), (
            f"expected a placeholder line after {heading}, got another heading: {non_blank[0]!r}"
        )


def test_req_001_prints_absolute_path_to_stdout(tmp_path):
    result = run_new("parse-gpx-header", tmp_path)
    expected = (tmp_path / "requirements" / "REQ-001-parse-gpx-header.md").resolve()
    assert result.stdout.strip() == str(expected), (
        f"stdout was {result.stdout!r}, expected {str(expected)!r}"
    )


def test_req_001_creates_requirements_dir_if_missing(tmp_path):
    assert not (tmp_path / "requirements").exists()
    result = run_new("parse-gpx-header", tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert (tmp_path / "requirements").is_dir()
    assert (tmp_path / "requirements" / "REQ-001-parse-gpx-header.md").exists()


@pytest.mark.parametrize(
    "bad_slug,category",
    [
        ("", "empty"),
        ("Foo", "contains uppercase"),
        ("foo bar", "contains space"),
        ("foo_bar", "contains underscore"),
        ("1foo", "starts with digit"),
        ("ab", "too short (2 chars)"),
        ("a" * 51, "too long (51 chars)"),
    ],
)
def test_req_001_rejects_invalid_slug(tmp_path, bad_slug, category):
    result = run_new(bad_slug, tmp_path)
    assert result.returncode != 0, (
        f"expected non-zero exit for {category} slug {bad_slug!r}"
    )
    assert result.stderr.strip() != "", (
        f"expected error message on stderr for {category} slug {bad_slug!r}"
    )
    assert "Traceback" not in result.stderr, (
        f"expected a rule-violation message, not a Python traceback, "
        f"for {category} slug {bad_slug!r}; stderr was:\n{result.stderr}"
    )
    req_dir = tmp_path / "requirements"
    if req_dir.exists():
        created = list(req_dir.glob("REQ-*.md"))
        assert created == [], (
            f"expected no files to be created for {category} slug, got {created}"
        )


def test_req_001_exits_with_usage_when_no_slug(tmp_path):
    result = run_new(None, tmp_path)
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "usage" in combined or "missing" in combined, (
        f"expected usage info in output, got stdout={result.stdout!r} stderr={result.stderr!r}"
    )
