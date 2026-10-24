import email.utils
import os
import urllib.request
import zipfile
from pathlib import Path
from types import ModuleType

import pytest
from filelock import FileLock, Timeout


@pytest.fixture
def cache_module(request: pytest.FixtureRequest) -> ModuleType:
    expected_path = Path(__file__).with_name("conftest.py").resolve()
    for plugin in request.config.pluginmanager.get_plugins():
        plugin_path = getattr(plugin, "__file__", None)
        if plugin_path is not None and Path(plugin_path).resolve() == expected_path:
            return plugin
    raise AssertionError(f"pytest did not load the expected root conftest: {expected_path}")


def _write_zip(path: Path, members: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, contents in members.items():
            archive.writestr(name, contents)


def test_cached_archives_prepare_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache_module: ModuleType
) -> None:
    cache_dir = tmp_path / "cache"
    zip_path = cache_dir / "examples.zip"
    _write_zip(zip_path, {"z.xml": "z", "a.xml": "a"})

    def fail_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("cached archives should not make network requests")

    monkeypatch.setattr(cache_module, "_remote_last_modified", fail_network)
    monkeypatch.setattr(urllib.request, "urlretrieve", fail_network)

    found = cache_module._prepare_leon2_examples(
        cache_dir,
        [("https://example.invalid/examples.zip", "v1685_2022", "examples")],
        refresh=False,
    )

    assert found == [
        (cache_dir / "examples" / "a.xml", "v1685_2022"),
        (cache_dir / "examples" / "z.xml", "v1685_2022"),
    ]


def test_refresh_checks_head_and_downloads_newer_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache_module: ModuleType
) -> None:
    archive_path = tmp_path / "examples.zip"
    archive_path.write_bytes(b"old")
    newer_timestamp = archive_path.stat().st_mtime + 100
    head_timeouts: list[float | None] = []

    class Response:
        headers = {"Last-Modified": email.utils.formatdate(newer_timestamp, usegmt=True)}

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_urlopen(request: urllib.request.Request, *, timeout: float | None = None) -> Response:
        assert request.get_method() == "HEAD"
        head_timeouts.append(timeout)
        return Response()

    def fake_urlretrieve(url: str, destination: Path) -> tuple[str, None]:
        Path(destination).write_bytes(b"new")
        return str(destination), None

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(urllib.request, "urlretrieve", fake_urlretrieve)

    downloaded = cache_module._download_if_newer(
        "https://example.invalid/examples.zip", archive_path, refresh=True, head_timeout=0.25
    )

    assert downloaded is True
    assert archive_path.read_bytes() == b"new"
    assert head_timeouts == [0.25]


def test_refresh_skips_download_when_remote_timestamp_is_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache_module: ModuleType
) -> None:
    archive_path = tmp_path / "examples.zip"
    archive_path.write_bytes(b"cached")
    timestamp = 1_700_000_000
    os.utime(archive_path, (timestamp, timestamp))

    class Response:
        headers = {"Last-Modified": email.utils.formatdate(timestamp, usegmt=True)}

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: Response())

    def fail_download(url: str, destination: Path) -> None:
        raise AssertionError("a current archive should not be downloaded")

    monkeypatch.setattr(urllib.request, "urlretrieve", fail_download)

    downloaded = cache_module._download_if_newer("https://example.invalid/examples.zip", archive_path, refresh=True)

    assert downloaded is False
    assert archive_path.read_bytes() == b"cached"


def test_missing_archive_download_failure_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache_module: ModuleType
) -> None:
    def fail_download(url: str, destination: Path) -> None:
        raise OSError("offline")

    monkeypatch.setattr(urllib.request, "urlretrieve", fail_download)

    with pytest.raises(RuntimeError, match="Failed to download ZIP file 'examples.zip': offline"):
        cache_module._prepare_leon2_examples(
            tmp_path,
            [("https://example.invalid/examples.zip", "v1685_2022", "examples")],
            refresh=False,
        )


def test_unchanged_cached_archive_reuses_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache_module: ModuleType
) -> None:
    cache_dir = tmp_path / "cache"
    _write_zip(cache_dir / "examples.zip", {"example.xml": "<root/>"})
    leon2_zips = [("https://example.invalid/examples.zip", "v1685_2022", "examples")]

    cache_module._prepare_leon2_examples(cache_dir, leon2_zips, refresh=False)

    def fail_extract(zip_path: Path, extract_dir: Path) -> None:
        raise AssertionError("unchanged archives should reuse their extraction")

    monkeypatch.setattr(cache_module, "_extract_zip", fail_extract)
    found = cache_module._prepare_leon2_examples(cache_dir, leon2_zips, refresh=False)

    assert found == [(cache_dir / "examples" / "example.xml", "v1685_2022")]


def test_preparation_holds_file_lock_through_download_and_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache_module: ModuleType
) -> None:
    cache_dir = tmp_path / "cache"
    checked_lock = cache_dir / ".prepare.lock"
    lock_checks: list[bool] = []

    def fake_download(url: str, destination: Path, *, refresh: bool = False) -> bool:
        with pytest.raises(Timeout):
            FileLock(checked_lock).acquire(timeout=0)
        lock_checks.append(True)
        _write_zip(destination, {"nested/example.xml": "<root/>"})
        return True

    monkeypatch.setattr(cache_module, "_download_if_newer", fake_download)

    found = cache_module._prepare_leon2_examples(
        cache_dir,
        [("https://example.invalid/examples.zip", "v1685_2014", "examples")],
        refresh=False,
    )

    assert lock_checks == [True]
    assert found == [(cache_dir / "examples" / "nested" / "example.xml", "v1685_2014")]


def test_callable_parametrize_ids_are_stable(cache_module: ModuleType) -> None:
    def parser(value: str) -> str:
        return value

    first = cache_module.pytest_make_parametrize_id(None, parser, "converter")
    second = cache_module.pytest_make_parametrize_id(None, parser, "converter")

    assert first == second == f"converter={parser.__module__}.{parser.__qualname__}"
    assert cache_module.pytest_make_parametrize_id(None, None, "optional") is None
