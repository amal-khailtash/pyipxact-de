"""Tests for release metadata validation against temporary Git histories."""

import json
import runpy
import subprocess
from pathlib import Path

import pytest

_CHECKER = Path(__file__).resolve().parents[1] / "tools" / "check_release_metadata.py"
_VALIDATE_RELEASE = runpy.run_path(str(_CHECKER))["validate_release"]


def _git(repo: Path, *args: str) -> str:
    """Run a Git command in a test repository and return its output."""
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _release_repo(repo: Path, head_changes: dict[str, str]) -> tuple[str, str]:
    """Create base and proposed release commits with optional head file edits."""
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Release test")
    _git(repo, "config", "user.email", "release-test@example.invalid")

    files = {
        "pyproject.toml": ('[project]\nname = "pyipxact-de"\nversion = "0.7.0"\ndependencies = ["xsdata>=24"]\n'),
        "uv.lock": (
            'version = 1\nrevision = 3\nrequires-python = ">=3.14"\n\n'
            '[[package]]\nname = "xsdata"\nversion = "24.12"\n'
            'source = { registry = "https://pypi.org/simple" }\n\n'
            '[[package]]\nname = "pyipxact-de"\nversion = "0.7.0"\n'
            'source = { editable = "." }\n'
        ),
        ".release-please-manifest.json": json.dumps({".": "0.7.0"}) + "\n",
        "CHANGELOG.md": "## [0.7.0]\n\nInitial release.\n",
        "src/amal/eda/ipxact_de/__init__.py": '"""Minimal source fixture."""\n',
    }
    for name, contents in files.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base release")
    base = _git(repo, "rev-parse", "HEAD")

    for name, contents in head_changes.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "proposed release")
    head = _git(repo, "rev-parse", "HEAD")
    return base, head


def _valid_changes() -> dict[str, str]:
    """Return the expected metadata-only version bump to 0.7.1."""
    return {
        "pyproject.toml": ('[project]\nname = "pyipxact-de"\nversion = "0.7.1"\ndependencies = ["xsdata>=24"]\n'),
        "uv.lock": (
            'version = 1\nrevision = 3\nrequires-python = ">=3.14"\n\n'
            '[[package]]\nname = "xsdata"\nversion = "24.12"\n'
            'source = { registry = "https://pypi.org/simple" }\n\n'
            '[[package]]\nname = "pyipxact-de"\nversion = "0.7.1"\n'
            'source = { editable = "." }\n'
        ),
        ".release-please-manifest.json": json.dumps({".": "0.7.1"}) + "\n",
        "CHANGELOG.md": "## [0.7.1]\n\nRelease notes.\n",
    }


def test_valid_metadata_only_version_bump_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Accept a bump when project, lock, manifest and changelog agree."""
    base, head = _release_repo(tmp_path / "repo", _valid_changes())
    monkeypatch.chdir(tmp_path / "repo")

    assert _VALIDATE_RELEASE(base, head) == "0.7.1"


def test_stale_local_project_lock_version_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a bump whose editable project version was not updated in uv.lock."""
    changes = _valid_changes()
    changes["uv.lock"] = changes["uv.lock"].replace(
        'name = "pyipxact-de"\nversion = "0.7.1"',
        'name = "pyipxact-de"\nversion = "0.7.0"',
    )
    base, head = _release_repo(tmp_path / "repo", changes)
    monkeypatch.chdir(tmp_path / "repo")

    with pytest.raises(ValueError, match="lockfile"):
        _VALIDATE_RELEASE(base, head)


@pytest.mark.parametrize("changed_file", ["pyproject.toml", "uv.lock"])
def test_dependency_changes_fail(changed_file: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject dependency changes in project metadata and the resolved lock."""
    changes = _valid_changes()
    if changed_file == "pyproject.toml":
        changes[changed_file] = changes[changed_file].replace("xsdata>=24", "xsdata>=25")
    else:
        changes[changed_file] = changes[changed_file].replace(
            'name = "xsdata"\nversion = "24.12"',
            'name = "xsdata"\nversion = "25.1"',
        )
    base, head = _release_repo(tmp_path / "repo", changes)
    monkeypatch.chdir(tmp_path / "repo")

    with pytest.raises(ValueError, match="changes project settings|lockfile"):
        _VALIDATE_RELEASE(base, head)


def test_source_file_changes_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a release commit that includes source changes."""
    changes = _valid_changes()
    changes["src/amal/eda/ipxact_de/__init__.py"] = '"""Changed source fixture."""\n'
    base, head = _release_repo(tmp_path / "repo", changes)
    monkeypatch.chdir(tmp_path / "repo")

    with pytest.raises(ValueError, match="unexpected changes"):
        _VALIDATE_RELEASE(base, head)


@pytest.mark.parametrize("inconsistency", ["manifest", "changelog"])
def test_manifest_or_changelog_inconsistency_fails(
    inconsistency: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject release metadata when the manifest or changelog misses the new version."""
    changes = _valid_changes()
    if inconsistency == "manifest":
        changes[".release-please-manifest.json"] = json.dumps({".": "0.7.0"}) + "\n"
    else:
        changes["CHANGELOG.md"] = "## [0.7.0]\n\nNo release entry.\n"
    base, head = _release_repo(tmp_path / "repo", changes)
    monkeypatch.chdir(tmp_path / "repo")

    with pytest.raises(ValueError, match="manifest|Changelog"):
        _VALIDATE_RELEASE(base, head)
