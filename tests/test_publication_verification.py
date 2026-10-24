"""Check release artifact verification against package index records."""

import hashlib
import runpy
from pathlib import Path

import pytest

_VERIFY_FILES = runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools" / "verify_publication.py"))[
    "verify_files"
]


def _published_record(path: Path, *, yanked: bool = False) -> dict[str, object]:
    """Build package index metadata matching a local artifact."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"filename": path.name, "digests": {"sha256": digest}, "yanked": yanked}


def test_verify_files_accepts_matching_wheel_and_source_archive(tmp_path: Path) -> None:
    """Accept a release when each wheel and source archive matches its index hash."""
    wheel = tmp_path / "pyipxact_de-0.7.1-py3-none-any.whl"
    source = tmp_path / "pyipxact_de-0.7.1.tar.gz"
    wheel.write_bytes(b"wheel artifact bytes")
    source.write_bytes(b"source artifact bytes")

    _VERIFY_FILES([wheel, source], [_published_record(wheel), _published_record(source)])


def test_verify_files_rejects_missing_artifact(tmp_path: Path) -> None:
    """Reject a local distribution absent from package index metadata."""
    artifact = tmp_path / "pyipxact_de-0.7.1-py3-none-any.whl"
    artifact.write_bytes(b"wheel artifact bytes")

    with pytest.raises(ValueError, match="does not expose"):
        _VERIFY_FILES([artifact], [])


def test_verify_files_rejects_wrong_hash(tmp_path: Path) -> None:
    """Reject an index digest that differs from the local artifact bytes."""
    artifact = tmp_path / "pyipxact_de-0.7.1-py3-none-any.whl"
    artifact.write_bytes(b"wheel artifact bytes")
    record = _published_record(artifact)
    record["digests"] = {"sha256": "0" * 64}

    with pytest.raises(ValueError, match="differs or is yanked"):
        _VERIFY_FILES([artifact], [record])


def test_verify_files_rejects_yanked_artifact(tmp_path: Path) -> None:
    """Reject a matching artifact marked yanked on the package index."""
    artifact = tmp_path / "pyipxact_de-0.7.1-py3-none-any.whl"
    artifact.write_bytes(b"wheel artifact bytes")

    with pytest.raises(ValueError, match="differs or is yanked"):
        _VERIFY_FILES([artifact], [_published_record(artifact, yanked=True)])


def test_verify_files_rejects_empty_release() -> None:
    """Reject publication verification when the local release has no artifacts."""
    with pytest.raises(ValueError, match="No release distributions found"):
        _VERIFY_FILES([], [])
