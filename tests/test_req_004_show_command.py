"""Tests for REQ-004: Show a requirement and its commit history."""
from __future__ import annotations

import subprocess

import pytest


def run_show(cwd, *args):
    return subprocess.run(
        ["reqtool", "show", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def init_git(cwd):
    subprocess.run(["git", "init", "-q"], cwd=cwd, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=cwd, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=cwd, check=True
    )


def stage_and_commit(cwd, message):
    subprocess.run(["git", "add", "-A"], cwd=cwd, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=cwd, check=True)


def write_req(root, number, slug, title="Title", status="draft"):
    reqs = root / "requirements"
    reqs.mkdir(exist_ok=True)
    path = reqs / f"REQ-{number:03d}-{slug}.md"
    path.write_text(
        "---\n"
        f"id: REQ-{number:03d}\n"
        f"title: {title}\n"
        f"status: {status}\n"
        'created: "2026-04-25"\n'
        "test_file: null\n"
        "depends_on: []\n"
        "---\n"
        "\n"
        f"# REQ-{number:03d}: {title}\n"
        "\n"
        "## Intent\n"
        "TODO\n"
    )
    return path


def commits_section_lines(stdout):
    """Return the non-blank lines of the '## Commits' section, in order."""
    lines = stdout.splitlines()
    idx = lines.index("## Commits")
    return [ln for ln in lines[idx + 1:] if ln.strip()]


@pytest.mark.parametrize(
    "bad_arg",
    [
        "1",
        "001",
        "REQ-1",
        "REQ-01",
        "REQ-0001",
        "REQ-abc",
        "show-requirement",
        "REQ_001",
        "req-001",
    ],
)
def test_req_004_canonical_argument_form_required(tmp_path, bad_arg):
    result = run_show(tmp_path, bad_arg)
    assert result.returncode != 0, (
        f"bad_arg={bad_arg!r} should be rejected; "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert result.stderr.strip() != "", (
        f"expected error on stderr for bad_arg={bad_arg!r}"
    )
    assert result.stdout == "", (
        f"expected empty stdout for bad_arg={bad_arg!r}, got {result.stdout!r}"
    )
    assert "No such command" not in result.stderr, (
        "show subcommand must be registered"
    )


def test_req_004_no_argument_exits_with_usage(tmp_path):
    result = run_show(tmp_path)
    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "usage" in combined or "missing" in combined, (
        f"expected usage info; stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "No such command" not in result.stderr


def test_req_004_resolves_to_unique_file(tmp_path):
    write_req(tmp_path, 1, "first", "First")
    write_req(tmp_path, 2, "second", "Second")
    result = run_show(tmp_path, "REQ-002")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert "REQ-002: Second" in result.stdout
    assert "REQ-001: First" not in result.stdout


def test_req_004_stdout_contains_file_contents_unmodified(tmp_path):
    path = write_req(tmp_path, 1, "foo", "Foo Title")
    raw = path.read_text()
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert result.stdout.startswith(raw), (
        f"stdout must start with the file content byte-for-byte. "
        f"raw={raw!r}, stdout={result.stdout!r}"
    )


def test_req_004_commits_section_appended(tmp_path):
    write_req(tmp_path, 1, "foo", "Foo")
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert "## Commits" in result.stdout, (
        f"expected '## Commits' section in stdout; got:\n{result.stdout}"
    )


def test_req_004_commits_listed_in_chronological_order(tmp_path):
    write_req(tmp_path, 1, "foo", "Foo")
    init_git(tmp_path)
    stage_and_commit(
        tmp_path,
        "Add tests for REQ-001\n\nRequirement: REQ-001\nPhase: tests\n",
    )
    (tmp_path / "src.py").write_text("# impl\n")
    stage_and_commit(
        tmp_path,
        "Implement REQ-001\n\nRequirement: REQ-001\nPhase: implementation\n",
    )
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = commits_section_lines(result.stdout)
    # Filter to lines that look like commit lines (3 tab-separated fields)
    commit_lines = [ln for ln in lines if len(ln.split("\t")) == 3]
    assert len(commit_lines) == 2, f"expected 2 commit lines, got {commit_lines!r}"
    phases = [ln.split("\t")[1] for ln in commit_lines]
    assert phases == ["tests", "implementation"], (
        f"expected chronological order [tests, implementation], got {phases!r}"
    )


def test_req_004_missing_phase_trailer_renders_dash(tmp_path):
    write_req(tmp_path, 1, "foo", "Foo")
    init_git(tmp_path)
    stage_and_commit(
        tmp_path,
        "Some change touching REQ-001\n\nRequirement: REQ-001\n",
    )
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = commits_section_lines(result.stdout)
    commit_lines = [ln for ln in lines if len(ln.split("\t")) == 3]
    assert len(commit_lines) == 1, (
        f"expected 1 commit line (line still included even without Phase trailer); "
        f"got {commit_lines!r}"
    )
    fields = commit_lines[0].split("\t")
    assert fields[1] == "-", (
        f"Phase column for trailer-less commit must be the literal '-', "
        f"got {fields[1]!r}"
    )


def test_req_004_zero_commits_section_says_none(tmp_path):
    write_req(tmp_path, 1, "foo", "Foo")
    init_git(tmp_path)
    stage_and_commit(tmp_path, "initial commit (no requirement trailer)")
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = commits_section_lines(result.stdout)
    assert lines and lines[0] == "(none)", (
        f"expected '(none)' as first line of Commits section; got {lines!r}"
    )


def test_req_004_not_a_git_repo_section_says_not_a_git_repository(tmp_path):
    write_req(tmp_path, 1, "foo", "Foo")
    # Deliberately do not init_git
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = commits_section_lines(result.stdout)
    assert lines and lines[0] == "(not a git repository)", (
        f"expected '(not a git repository)' notice; got {lines!r}"
    )


def test_req_004_malformed_file_shown_verbatim(tmp_path):
    reqs = tmp_path / "requirements"
    reqs.mkdir()
    path = reqs / "REQ-001-bad.md"
    raw = "---\nid: [unclosed\nbroken: yaml\n---\n# malformed body\n"
    path.write_text(raw)
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert result.stdout.startswith(raw), (
        f"malformed file should still be shown verbatim. "
        f"raw={raw!r}, stdout={result.stdout!r}"
    )
    assert result.stderr == "", (
        f"display is not validation; expected empty stderr, got {result.stderr!r}"
    )


def test_req_004_file_not_found_exits_nonzero_with_id_in_stderr(tmp_path):
    result = run_show(tmp_path, "REQ-999")
    assert result.returncode != 0, (
        f"expected non-zero exit; stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "REQ-999" in result.stderr, (
        f"stderr should name the requested ID; got {result.stderr!r}"
    )
    assert result.stdout == "", f"expected empty stdout, got {result.stdout!r}"
    assert "No such command" not in result.stderr


def test_req_004_ambiguous_match_exits_nonzero_with_filenames_in_stderr(tmp_path):
    write_req(tmp_path, 1, "first", "First")
    (tmp_path / "requirements" / "REQ-001-second.md").write_text(
        "---\nid: REQ-001\ntitle: Second\n---\n"
    )
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode != 0, (
        f"expected non-zero exit; stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    assert "REQ-001-first.md" in result.stderr, (
        f"stderr should name the colliding files; got {result.stderr!r}"
    )
    assert "REQ-001-second.md" in result.stderr, (
        f"stderr should name the colliding files; got {result.stderr!r}"
    )
    assert result.stdout == "", f"expected empty stdout, got {result.stdout!r}"
    assert "No such command" not in result.stderr


def test_req_004_exits_zero_on_found_and_shown(tmp_path):
    write_req(tmp_path, 1, "foo", "Foo")
    result = run_show(tmp_path, "REQ-001")
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
