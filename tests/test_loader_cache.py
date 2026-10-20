"""Repository cache integrity and stale registration recovery."""

import json
import os
from unittest.mock import patch

import pytest

from amal.eda.ipxact_de import loader
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import registry

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


def write_component(path, name="one"):
    path.write_text(
        f'<component xmlns="{NS}"><vendor>v</vendor><library>l</library>'
        f'<name>{name}</name><version>1</version></component>'
    )


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.delenv("IPXACT_XML_PATHS", raising=False)
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("bad", [None, {}, {"path": "relative", "mtime": 1}, {"path": "/bad", "mtime": "x"}])
def test_bad_records_do_not_discard_valid_neighbors(tmp_path, bad):
    path = tmp_path / "cache.json"
    good = {"path": str(tmp_path / "valid.xml"), "mtime": 1, "vlnv": ["v", "l", "n", "1"]}
    path.write_text(json.dumps([bad, good]))
    assert list(loader._load_cache(path)) == [good["path"]]


@pytest.mark.parametrize("field,value", [("vlnv", ["v"]), ("fingerprint", [1, "bad", 3]), ("mtime", True)])
def test_reject_invalid_metadata(tmp_path, field, value):
    path = tmp_path / "cache.json"
    record = {"path": str(tmp_path / "valid.xml"), "mtime": 1, "vlnv": ["v", "l", "n", "1"]}
    record[field] = value
    path.write_text(json.dumps([record]))
    assert loader._load_cache(path) == {}


def test_changed_file_with_preserved_mtime_reparsed(tmp_path):
    source = tmp_path / "component.xml"
    write_component(source)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    stat = source.stat()
    write_component(source, "different")
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(("v", "l", "one", "1")) is None
    assert registry.get_id(("v", "l", "different", "1")) is not None


@pytest.mark.parametrize("change", ["delete", "modify"])
def test_cache_only_load_discards_stale_files(tmp_path, change):
    source = tmp_path / "component.xml"
    write_component(source)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert loader.load_registry_from_cache(cache_dir=tmp_path)
    if change == "delete":
        source.unlink()
    else:
        write_component(source, "changed")
    assert not loader.load_registry_from_cache(cache_dir=tmp_path)
    assert registry.get_id(("v", "l", "one", "1")) is None


def test_empty_cache_clears_previous_registrations(tmp_path):
    source = tmp_path / "component.xml"
    write_component(source)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    (tmp_path / loader.CACHE_BASENAME).write_text("[]")
    assert not loader.load_registry_from_cache(cache_dir=tmp_path)
    assert registry.get_id(("v", "l", "one", "1")) is None


def test_cache_directory_created(tmp_path):
    source = tmp_path / "component.xml"
    write_component(source)
    cache_dir = tmp_path / "nested" / "cache"
    loader.load_registry_from_paths([str(source)], cache_dir=cache_dir)
    assert loader.load_registry_from_cache(cache_dir=cache_dir)


def test_failed_atomic_replace_preserves_cache_and_cleans_temporary(tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text("old cache")
    with patch.object(loader.os, "replace", side_effect=OSError("write failed")), pytest.raises(OSError):
        loader._save_cache(cache, {})
    assert cache.read_text() == "old cache"
    assert list(tmp_path.iterdir()) == [cache]


@pytest.mark.parametrize("content", ["{", "{}", "null"])
def test_malformed_cache_recovers_on_scan(tmp_path, content):
    source = tmp_path / "component.xml"
    write_component(source)
    (tmp_path / loader.CACHE_BASENAME).write_text(content)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(("v", "l", "one", "1")) is not None
    assert loader.load_registry_from_cache(cache_dir=tmp_path)


def test_legacy_cache_refreshes_before_registration(tmp_path):
    source = tmp_path / "component.xml"
    write_component(source, "current")
    record = {
        "path": str(source), "mtime": source.stat().st_mtime, "element": "component",
        "standard": "ipxact", "version": "1685-2022", "vlnv": ["v", "l", "stale", "1"],
    }
    (tmp_path / loader.CACHE_BASENAME).write_text(json.dumps([record]))
    assert not loader.load_registry_from_cache(cache_dir=tmp_path)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert registry.get_id(("v", "l", "current", "1")) is not None
    assert registry.get_id(("v", "l", "stale", "1")) is None


def test_default_cache_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "component.xml"
    write_component(source)
    loader.load_registry_from_paths([str(source)])
    assert loader.load_registry_from_cache()


def test_cached_registration_failure_falls_back_to_parsed_document(tmp_path):
    source = tmp_path / "component.xml"
    write_component(source)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    original = registry.register
    attempts = 0

    def fail_once(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ValueError("cached registration failed")
        return original(*args, **kwargs)

    with patch.object(registry, "register", side_effect=fail_once):
        loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    assert attempts == 2
    assert registry.get_id(("v", "l", "one", "1")) is not None


def test_cache_only_duplicate_keeps_first(tmp_path):
    first = tmp_path / "first.xml"
    second = tmp_path / "second.xml"
    write_component(first)
    write_component(second)
    records = {}
    for source in (first, second):
        records[str(source)] = loader.CacheEntry(
            str(source), source.stat().st_mtime, "component", "ipxact", "1685-2022",
            ("v", "l", "one", "1"), loader._fingerprint(source),
        )
    loader._save_cache(tmp_path / loader.CACHE_BASENAME, records)
    with patch.object(loader.logger, "warning") as warning:
        assert loader.load_registry_from_cache(cache_dir=tmp_path)
    from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import resolve_handle
    assert resolve_handle(registry.get_id(("v", "l", "one", "1"))).xml_path == str(first)
    assert any("Duplicate cached VLNV" in str(call) for call in warning.call_args_list)
