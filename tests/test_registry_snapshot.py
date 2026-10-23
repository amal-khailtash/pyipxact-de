"""Snapshot restoration and cache refresh behavior for the registry."""

from collections.abc import Iterator
from os import stat_result
from pathlib import Path

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi.core import registry
from amal.eda.ipxact_de import loader

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


def write_component(path: Path, name: str = "one") -> None:
    path.write_text(
        f'<component xmlns="{NS}"><vendor>v</vendor><library>l</library>'
        f"<name>{name}</name><version>1</version></component>"
    )


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("IPXACT_XML_PATHS", raising=False)
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("change", ["modify", "delete"])
def test_snapshot_restores_stale_or_missing_source_without_stats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    source = tmp_path / "component.xml"
    write_component(source)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    if change == "delete":
        source.unlink()
    else:
        write_component(source, "changed")

    original_stat = Path.stat
    source_stats = 0

    def count_source_stat(path: Path, *args: object, **kwargs: object) -> stat_result:
        nonlocal source_stats
        if path == source:
            source_stats += 1
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", count_source_stat)
    assert loader.load_registry_from_cache(cache_dir=tmp_path, validate_files=False)
    assert source_stats == 0
    assert registry.get_id(("v", "l", "one", "1")) is not None

    assert not loader.load_registry_from_cache(cache_dir=tmp_path)
    assert source_stats == 1
    assert registry.get_id(("v", "l", "one", "1")) is None


def test_validating_cache_load_stats_each_cached_source_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sources = [tmp_path / "first.xml", tmp_path / "second.xml"]
    write_component(sources[0], "first")
    write_component(sources[1], "second")
    loader.load_registry_from_paths([str(path) for path in sources], cache_dir=tmp_path)

    original_stat = Path.stat
    source_stats = {path: 0 for path in sources}

    def count_source_stat(path: Path, *args: object, **kwargs: object) -> stat_result:
        if path in source_stats:
            source_stats[path] += 1
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", count_source_stat)
    assert loader.load_registry_from_cache(cache_dir=tmp_path)
    assert source_stats == {path: 1 for path in sources}


def test_scan_reparses_changed_sources_and_prunes_deleted_sources(tmp_path: Path) -> None:
    changed = tmp_path / "changed.xml"
    removed = tmp_path / "removed.xml"
    write_component(changed, "old")
    write_component(removed, "removed")
    loader.load_registry_from_paths([str(changed), str(removed)], cache_dir=tmp_path)

    write_component(changed, "updated")
    removed.unlink()
    loader.load_registry_from_paths([str(tmp_path)], cache_dir=tmp_path)

    assert registry.get_id(("v", "l", "old", "1")) is None
    assert registry.get_id(("v", "l", "updated", "1")) is not None
    assert registry.get_id(("v", "l", "removed", "1")) is None
    assert list(loader._load_cache(tmp_path / loader.CACHE_BASENAME)) == [str(changed)]


def test_snapshot_keeps_recognition_and_duplicate_policies(tmp_path: Path) -> None:
    first = tmp_path / "first.xml"
    duplicate = tmp_path / "duplicate.xml"
    unknown_edition = tmp_path / "unknown-edition.xml"
    nested_root = tmp_path / "nested-root.xml"
    common = ("v", "l", "duplicate", "1")
    cache = {
        str(first): loader.CacheEntry(str(first), 1.0, "component", "ipxact", "1685-2022", common),
        str(duplicate): loader.CacheEntry(str(duplicate), 1.0, "component", "ipxact", "1685-2022", common),
        str(unknown_edition): loader.CacheEntry(
            str(unknown_edition), 1.0, "component", "ipxact", "9999-9999", ("v", "l", "unknown", "1")
        ),
        str(nested_root): loader.CacheEntry(
            str(nested_root), 1.0, "wire", "ipxact", "1685-2022", ("v", "l", "nested", "1")
        ),
    }
    loader._save_cache(tmp_path / loader.CACHE_BASENAME, cache)

    assert loader.load_registry_from_cache(cache_dir=tmp_path, validate_files=False)
    handle = registry.get_id(common)
    assert handle is not None
    assert registry.get_file_name(handle) == str(first)
    assert registry.get_id(("v", "l", "unknown", "1")) is None
    assert registry.get_id(("v", "l", "nested", "1")) is None
