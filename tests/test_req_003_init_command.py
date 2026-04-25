"""Tests for REQ-003: Initialize a project for requirement-driven development."""
from __future__ import annotations

import re
import subprocess

import yaml


SKILL_PATH_PARTS = (".claude", "skills", "reqtool-workflow", "SKILL.md")


def run_init(cwd):
    return subprocess.run(
        ["reqtool", "init"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def skill_path(root):
    return root.joinpath(*SKILL_PATH_PARTS)


def parse_frontmatter_file(path):
    content = path.read_text()
    parts = content.split("---", 2)
    assert len(parts) == 3, (
        f"expected two '---' delimiters in {path}, got {len(parts) - 1}"
    )
    fm = yaml.safe_load(parts[1])
    body = parts[2]
    return fm, body


def test_req_003_creates_all_four_artifacts_in_empty_dir(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert (tmp_path / "requirements").is_dir()
    assert (tmp_path / "tests").is_dir()
    assert (tmp_path / "AGENTS.md").is_file()
    assert skill_path(tmp_path).is_file()


def test_req_003_creates_skill_parent_directories(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert (tmp_path / ".claude").is_dir()
    assert (tmp_path / ".claude" / "skills").is_dir()
    assert (tmp_path / ".claude" / "skills" / "reqtool-workflow").is_dir()


def test_req_003_does_not_modify_existing_files(tmp_path):
    sentinel_agents = "DO NOT MODIFY THIS AGENTS.md\n"
    sentinel_skill = "DO NOT MODIFY THIS SKILL.md\n"
    (tmp_path / "AGENTS.md").write_text(sentinel_agents)
    skill_p = skill_path(tmp_path)
    skill_p.parent.mkdir(parents=True)
    skill_p.write_text(sentinel_skill)
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert (tmp_path / "AGENTS.md").read_text() == sentinel_agents
    assert skill_p.read_text() == sentinel_skill


def test_req_003_skill_frontmatter_has_name_and_description(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    fm, _ = parse_frontmatter_file(skill_path(tmp_path))
    assert fm.get("name") == "reqtool-workflow", (
        f"expected name='reqtool-workflow', got {fm.get('name')!r}"
    )
    desc = fm.get("description")
    assert isinstance(desc, str) and desc.strip() != "", (
        f"description must be a non-empty string, got {desc!r}"
    )


def test_req_003_skill_frontmatter_parses_as_yaml(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    content = skill_path(tmp_path).read_text()
    parts = content.split("---", 2)
    assert len(parts) == 3, (
        f"missing YAML frontmatter delimiters; got {len(parts) - 1}"
    )
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), f"frontmatter is not a mapping: {fm!r}"


def test_req_003_skill_name_matches_parent_directory(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    skill_p = skill_path(tmp_path)
    fm, _ = parse_frontmatter_file(skill_p)
    assert fm["name"] == skill_p.parent.name, (
        f"name {fm['name']!r} must match parent dir {skill_p.parent.name!r}"
    )


def test_req_003_skill_name_format_valid(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    fm, _ = parse_frontmatter_file(skill_path(tmp_path))
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm["name"]), (
        f"name {fm['name']!r} must be lowercase alphanumeric with hyphens"
    )


def test_req_003_skill_description_within_bounds(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    fm, _ = parse_frontmatter_file(skill_path(tmp_path))
    desc_len = len(fm["description"])
    assert 1 <= desc_len <= 1024, (
        f"description length {desc_len} must be in [1, 1024]"
    )


def test_req_003_skill_body_mentions_workflow_and_commands(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    _, body = parse_frontmatter_file(skill_path(tmp_path))
    body_lower = body.lower()
    for keyword in ("requirement", "test", "implementation"):
        assert keyword in body_lower, (
            f"skill body should mention {keyword!r}; body was:\n{body}"
        )
    for command in ("reqtool new", "reqtool list"):
        assert command in body, (
            f"skill body should mention {command!r}; body was:\n{body}"
        )


def test_req_003_agents_md_references_skill_and_workflow(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    content = (tmp_path / "AGENTS.md").read_text()
    assert "reqtool-workflow" in content, (
        f"AGENTS.md should reference the skill 'reqtool-workflow'; content was:\n{content}"
    )
    content_lower = content.lower()
    for keyword in ("requirement", "test", "implementation"):
        assert keyword in content_lower, (
            f"AGENTS.md should mention {keyword!r}; content was:\n{content}"
        )


def test_req_003_stdout_uses_created_format_when_creating(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    created_lines = [ln for ln in lines if ln.startswith("Created ")]
    skipped_lines = [ln for ln in lines if ln.startswith("Skipped ")]
    assert len(created_lines) == 4, (
        f"expected 4 'Created ...' lines for empty target, got {len(created_lines)}; "
        f"stdout was:\n{result.stdout}"
    )
    assert skipped_lines == [], (
        f"expected no 'Skipped' lines on first run, got {skipped_lines!r}"
    )


def test_req_003_stdout_uses_skipped_format_when_existing(tmp_path):
    (tmp_path / "requirements").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "AGENTS.md").write_text("existing\n")
    skill_p = skill_path(tmp_path)
    skill_p.parent.mkdir(parents=True)
    skill_p.write_text("existing\n")
    result = run_init(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    skipped_lines = [ln for ln in lines if ln.startswith("Skipped ")]
    created_lines = [ln for ln in lines if ln.startswith("Created ")]
    assert len(skipped_lines) == 4, (
        f"expected 4 'Skipped ...' lines for fully-initialized target, got {len(skipped_lines)}; "
        f"stdout was:\n{result.stdout}"
    )
    assert created_lines == [], (
        f"expected no 'Created' lines, got {created_lines!r}"
    )
    for line in skipped_lines:
        assert line.endswith(" (already exists)"), (
            f"skipped line should end with ' (already exists)': {line!r}"
        )


def test_req_003_rerun_is_idempotent_noop(tmp_path):
    first = run_init(tmp_path)
    assert first.returncode == 0, f"first run stderr: {first.stderr!r}"
    second = run_init(tmp_path)
    assert second.returncode == 0, f"second run stderr: {second.stderr!r}"
    skipped = sum(
        1 for ln in second.stdout.splitlines() if ln.startswith("Skipped ")
    )
    assert skipped == 4, (
        f"expected all 4 artifacts to be Skipped on rerun, got {skipped}; "
        f"stdout was:\n{second.stdout}"
    )


def test_req_003_unexpected_error_exits_nonzero_with_stderr(tmp_path):
    skills = tmp_path / ".claude" / "skills"
    skills.mkdir(parents=True)
    skills.chmod(0o555)
    try:
        result = run_init(tmp_path)
        assert result.returncode != 0, (
            f"expected non-zero exit when SKILL.md cannot be created; "
            f"stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
        assert result.stderr.strip() != "", "expected error message on stderr"
        assert "No such command" not in result.stderr, (
            "init must be a registered subcommand, not surface 'No such command'"
        )
    finally:
        skills.chmod(0o755)
