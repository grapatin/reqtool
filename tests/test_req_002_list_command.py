"""Tests for REQ-002: List requirements."""
from __future__ import annotations

import subprocess


def run_list(cwd):
    return subprocess.run(
        ["reqtool", "list"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def write_req(root, number, slug, title, status="draft"):
    reqs = root / "requirements"
    reqs.mkdir(exist_ok=True)
    path = reqs / f"REQ-{number:03d}-{slug}.md"
    path.write_text(
        "---\n"
        f"id: REQ-{number:03d}\n"
        f"title: {title}\n"
        f"status: {status}\n"
        'created: "2026-04-23"\n'
        "test_file: null\n"
        "depends_on: []\n"
        "---\n"
        f"# REQ-{number:03d}: {title}\n"
    )
    return path


def write_req_missing_field(root, number, missing_field):
    reqs = root / "requirements"
    reqs.mkdir(exist_ok=True)
    path = reqs / f"REQ-{number:03d}-missing-{missing_field}.md"
    lines = ["---"]
    if missing_field != "id":
        lines.append(f"id: REQ-{number:03d}")
    if missing_field != "title":
        lines.append("title: Something")
    if missing_field != "status":
        lines.append("status: draft")
    lines.append("---")
    path.write_text("\n".join(lines) + "\n")
    return path


def test_req_002_no_requirements_dir_prints_nothing(tmp_path):
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert result.stdout == "", f"stdout should be empty, got {result.stdout!r}"


def test_req_002_empty_requirements_dir_prints_nothing(tmp_path):
    (tmp_path / "requirements").mkdir()
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    assert result.stdout == "", f"stdout should be empty, got {result.stdout!r}"


def test_req_002_single_req_prints_one_line(tmp_path):
    write_req(tmp_path, 1, "foo", "Foo title")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = result.stdout.splitlines()
    assert len(lines) == 1, f"expected 1 line, got {len(lines)}: {lines!r}"


def test_req_002_multiple_reqs_one_line_each_sorted(tmp_path):
    write_req(tmp_path, 3, "third", "Third")
    write_req(tmp_path, 1, "first", "First")
    write_req(tmp_path, 2, "second", "Second")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = result.stdout.splitlines()
    assert len(lines) == 3, f"expected 3 lines, got {len(lines)}: {lines!r}"
    ids = [line.split("\t")[0] for line in lines]
    assert ids == ["REQ-001", "REQ-002", "REQ-003"], f"wrong order: {ids!r}"


def test_req_002_sorts_numerically_across_widths(tmp_path):
    write_req(tmp_path, 100, "hundred", "One hundred")
    write_req(tmp_path, 2, "two", "Two")
    write_req(tmp_path, 10, "ten", "Ten")
    write_req(tmp_path, 1, "one", "One")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    ids = [line.split("\t")[0] for line in result.stdout.splitlines()]
    assert ids == ["REQ-001", "REQ-002", "REQ-010", "REQ-100"], (
        f"expected numeric sort, got {ids!r}"
    )


def test_req_002_line_has_three_tab_separated_fields(tmp_path):
    write_req(tmp_path, 1, "foo", "Foo title")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        assert len(fields) == 3, (
            f"expected 3 tab-separated fields, got {len(fields)}: {line!r}"
        )


def test_req_002_line_contains_id_status_title_in_order(tmp_path):
    write_req(tmp_path, 7, "demo", "Demo title", status="tests-written")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    lines = result.stdout.splitlines()
    assert len(lines) == 1, f"expected 1 line, got {lines!r}"
    fields = lines[0].split("\t")
    assert fields == ["REQ-007", "tests-written", "Demo title"], (
        f"expected [id, status, title], got {fields!r}"
    )


def test_req_002_malformed_yaml_warns_and_continues(tmp_path):
    write_req(tmp_path, 1, "good", "Good one")
    bad = tmp_path / "requirements" / "REQ-002-bad.md"
    bad.write_text("---\nid: [unclosed\n---\n")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    ids = [line.split("\t")[0] for line in result.stdout.splitlines()]
    assert ids == ["REQ-001"], f"expected only REQ-001 on stdout, got {ids!r}"
    assert "REQ-002-bad.md" in result.stderr, (
        f"expected malformed filename in stderr, got {result.stderr!r}"
    )


def test_req_002_missing_id_warns_and_skips(tmp_path):
    write_req(tmp_path, 1, "good", "Good one")
    bad = write_req_missing_field(tmp_path, 2, "id")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    ids = [line.split("\t")[0] for line in result.stdout.splitlines()]
    assert ids == ["REQ-001"], f"expected only REQ-001 on stdout, got {ids!r}"
    assert bad.name in result.stderr, (
        f"expected {bad.name!r} in stderr, got {result.stderr!r}"
    )


def test_req_002_missing_title_warns_and_skips(tmp_path):
    write_req(tmp_path, 1, "good", "Good one")
    bad = write_req_missing_field(tmp_path, 2, "title")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    ids = [line.split("\t")[0] for line in result.stdout.splitlines()]
    assert ids == ["REQ-001"], f"expected only REQ-001 on stdout, got {ids!r}"
    assert bad.name in result.stderr, (
        f"expected {bad.name!r} in stderr, got {result.stderr!r}"
    )


def test_req_002_missing_status_warns_and_skips(tmp_path):
    write_req(tmp_path, 1, "good", "Good one")
    bad = write_req_missing_field(tmp_path, 2, "status")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    ids = [line.split("\t")[0] for line in result.stdout.splitlines()]
    assert ids == ["REQ-001"], f"expected only REQ-001 on stdout, got {ids!r}"
    assert bad.name in result.stderr, (
        f"expected {bad.name!r} in stderr, got {result.stderr!r}"
    )


def test_req_002_ignores_non_matching_filenames(tmp_path):
    reqs = tmp_path / "requirements"
    reqs.mkdir()
    (reqs / "notes.md").write_text("just some notes\n")
    (reqs / "readme.txt").write_text("readme\n")
    (reqs / "REQ-foo.md").write_text("---\nid: fake\n---\n")
    write_req(tmp_path, 1, "real", "Real one")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    ids = [line.split("\t")[0] for line in result.stdout.splitlines()]
    assert ids == ["REQ-001"], f"only REQ-001 should be listed, got {ids!r}"
    for bad_name in ("notes.md", "readme.txt", "REQ-foo.md"):
        assert bad_name not in result.stderr, (
            f"{bad_name!r} should be ignored silently; stderr: {result.stderr!r}"
        )


def test_req_002_mix_valid_and_malformed(tmp_path):
    write_req(tmp_path, 1, "good-one", "Good one")
    write_req(tmp_path, 3, "good-three", "Good three")
    bad = tmp_path / "requirements" / "REQ-002-bad.md"
    bad.write_text("---\nid: [unclosed\n---\n")
    result = run_list(tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr!r}"
    ids = [line.split("\t")[0] for line in result.stdout.splitlines()]
    assert ids == ["REQ-001", "REQ-003"], (
        f"expected valid files in sorted order, got {ids!r}"
    )
    assert "REQ-002-bad.md" in result.stderr, (
        f"malformed file should be named in stderr, got {result.stderr!r}"
    )
