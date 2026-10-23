"""Cross-edition XML inventory and TGI handle behavior."""

import subprocess
import sys
from collections.abc import Iterator
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from rich.console import Console

from amal.eda.accellera.ipxact.v1685_2022.tgi import name_group
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    VLNV,
    RegisteredElement,
    TgiError,
    get_handle,
    register_parent,
    registry,
)
from amal.eda.ipxact_de import cli, loader
from org.accellera.ipxact.v1685_2014 import Port as Ipxact2014Port
from org.accellera.ipxact.v1685_2022 import Port as CurrentPort
from org.accellera.spirit.v1_5 import Port as Spirit15Port
from org.accellera.standard import STANDARDS, Standard

EDITIONS = [(standard, version) for standard, meta in STANDARDS.items() for version in meta.versions]


def _vlnv(standard: str, version: str) -> VLNV:
    edition_name = f"{standard}_{version.replace('.', '_').replace('-', '_')}"
    return "example.org", "library", edition_name, "1.0"


def _write_component(path: Path, standard: str, version: str, vlnv: VLNV) -> Path:
    namespace = Standard.ns_url_for(standard, version)
    fields = "".join(
        f"<{field}>{value}</{field}>"
        for field, value in zip(("vendor", "library", "name", "version"), vlnv, strict=True)
    )
    path.write_text(f'<component xmlns="{namespace}">{fields}</component>')
    return path


def _assert_inventory(expected: dict[VLNV, tuple[str, str]]) -> None:
    found: dict[VLNV, RegisteredElement] = {}
    for handle in registry.iter_documents():
        metadata = registry.get_document_info(handle)
        assert metadata is not None
        found[metadata.vlnv] = metadata

    assert set(found) == set(expected)
    for vlnv, (standard, version) in expected.items():
        metadata = found[vlnv]
        assert metadata.standard == standard
        assert metadata.schema_version == version
        assert metadata.tgi_supported == ((standard, version) == ("ipxact", "1685-2022"))


@pytest.fixture(autouse=True)
def _isolated_registry(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("IPXACT_XML_PATHS", raising=False)
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("mode", ["fresh", "cached", "cache-only"])
def test_all_editions_are_inventoried_across_scan_modes(tmp_path: Path, mode: str) -> None:
    root = tmp_path / "documents"
    root.mkdir()
    expected = {}
    paths = []
    for index, (standard, version) in enumerate(EDITIONS):
        vlnv = _vlnv(standard, version)
        path = _write_component(root / f"component-{index}.xml", standard, version, vlnv)
        expected[vlnv] = (standard, version)
        paths.append(path)

    loader.load_registry_from_paths([str(root)], cache_dir=tmp_path)
    if mode == "cached":
        loader.load_registry_from_paths([str(root)], cache_dir=tmp_path)
    elif mode == "cache-only":
        registry.clear()
        assert loader.load_registry_from_cache(cache_dir=tmp_path)

    _assert_inventory(expected)


def test_non_top_level_document_root_is_excluded(tmp_path: Path) -> None:
    namespace = Standard.ns_url_for("ipxact", "1685-2022")
    vlnv = ("example.org", "library", "nested-element", "1.0")
    fields = "".join(
        f"<{field}>{value}</{field}>"
        for field, value in zip(("vendor", "library", "name", "version"), vlnv, strict=True)
    )
    path = tmp_path / "nested.xml"
    path.write_text(f'<wire xmlns="{namespace}">{fields}</wire>')

    loader.load_registry_from_paths([str(path)], cache_dir=tmp_path)

    assert registry.get_id(vlnv) is None
    assert list(registry.iter_documents()) == []


def test_first_duplicate_vlnv_wins_in_scan_and_cache(tmp_path: Path) -> None:
    vlnv = ("example.org", "library", "duplicate", "1.0")
    first = _write_component(tmp_path / "first.xml", "ipxact", "1685-2022", vlnv)
    second = _write_component(tmp_path / "second.xml", "spirit", "1.5", vlnv)

    loader.load_registry_from_paths([str(first), str(second)], cache_dir=tmp_path)
    handle = registry.get_id(vlnv)
    assert handle is not None
    assert registry.get_file_name(handle) == str(first)
    assert registry.get_document_info(handle).standard == "ipxact"

    loader.load_registry_from_paths([str(first), str(second)], cache_dir=tmp_path)
    handle = registry.get_id(vlnv)
    assert handle is not None
    assert registry.get_file_name(handle) == str(first)
    assert registry.get_document_info(handle).standard == "ipxact"


@pytest.mark.parametrize("removal", ["none", "unregister", "clear"])
def test_older_registered_document_handles_remain_invalid_for_tgi(tmp_path: Path, removal: str) -> None:
    vlnv = _vlnv("spirit", "1.5")
    source = _write_component(tmp_path / "old.xml", "spirit", "1.5", vlnv)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    handle = registry.get_id(vlnv)
    assert handle is not None

    if removal == "unregister":
        assert registry.unregister(vlnv)
    elif removal == "clear":
        registry.clear()

    for operation in (name_group.getName, lambda element_id: name_group.setName(element_id, "renamed")):
        with pytest.raises(TgiError) as error:
            operation(handle)
        assert error.value.fault_code == "INVALID_ID"


@pytest.mark.parametrize(
    "port_class",
    [Spirit15Port, Ipxact2014Port],
)
def test_generated_older_nested_models_are_rejected(port_class: type[Spirit15Port] | type[Ipxact2014Port]) -> None:
    handle = get_handle(port_class(name="data"))
    for operation in (name_group.getName, lambda element_id: name_group.setName(element_id, "renamed")):
        with pytest.raises(TgiError) as error:
            operation(handle)
        assert error.value.fault_code == "INVALID_ID"


def test_custom_child_handle_is_rejected_when_owned_by_older_document(tmp_path: Path) -> None:
    vlnv = _vlnv("spirit", "1.5")
    source = _write_component(tmp_path / "old.xml", "spirit", "1.5", vlnv)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    root_handle = registry.get_id(vlnv)
    assert root_handle is not None
    old_root = registry.get_document_info(root_handle).root
    child = SimpleNamespace(name="nested")
    child_handle = get_handle(child)
    register_parent(child, old_root, ("child",), "single")

    for operation in (name_group.getName, lambda element_id: name_group.setName(element_id, "renamed")):
        with pytest.raises(TgiError) as error:
            operation(child_handle)
        assert error.value.fault_code == "INVALID_ID"


def test_iter_by_predicate_excludes_older_inventory_entries(tmp_path: Path) -> None:
    old_vlnv = _vlnv("spirit", "1.5")
    current_vlnv = _vlnv("ipxact", "1685-2022")
    old = _write_component(tmp_path / "old.xml", "spirit", "1.5", old_vlnv)
    current = _write_component(tmp_path / "current.xml", "ipxact", "1685-2022", current_vlnv)
    loader.load_registry_from_paths([str(old), str(current)], cache_dir=tmp_path)

    old_handle = registry.get_id(old_vlnv)
    current_handle = registry.get_id(current_vlnv)
    assert old_handle is not None
    assert current_handle is not None
    assert set(registry.iter_by_predicate(lambda _root: True)) == {current_handle}
    assert set(registry.iter_documents()) == {old_handle, current_handle}


def test_current_generated_nested_model_is_accepted() -> None:
    port = CurrentPort(name="data")
    handle = get_handle(port)

    assert name_group.getName(handle) == "data"
    assert name_group.setName(handle, "renamed")
    assert name_group.getName(handle) == "renamed"


def test_cli_lists_older_edition_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vlnv = _vlnv("spirit", "1.5")
    source = _write_component(tmp_path / "old.xml", "spirit", "1.5", vlnv)
    loader.load_registry_from_paths([str(source)], cache_dir=tmp_path)
    output = StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, force_terminal=False, color_system=None))
    monkeypatch.setattr(sys, "argv", ["ipxact-de", "registry", "list", "--flat"])

    cli.main()

    assert ":".join(vlnv) in output.getvalue()


@pytest.mark.parametrize("flat", [False, True])
def test_cli_scan_then_list_preserves_cache_between_processes(tmp_path: Path, flat: bool) -> None:
    vlnv = _vlnv("spirit", "1.5")
    source = _write_component(tmp_path / "old.xml", "spirit", "1.5", vlnv)
    command = [sys.executable, "-m", "amal.eda.ipxact_de.cli"]
    scan = subprocess.run(
        command + ["registry", "scan", str(source)], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert scan.returncode == 0, scan.stderr
    cache = tmp_path / loader.CACHE_BASENAME
    saved_cache = cache.read_bytes()
    version = subprocess.run(command + ["version"], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert version.returncode == 0, version.stderr
    assert cache.read_bytes() == saved_cache
    arguments = ["registry", "list"] + (["--flat"] if flat else [])
    listing = subprocess.run(command + arguments, cwd=tmp_path, capture_output=True, text=True, check=False)
    assert listing.returncode == 0, listing.stderr
    assert vlnv[2] in listing.stdout
    if flat:
        assert ":".join(vlnv) in listing.stdout
    assert cache.read_bytes() == saved_cache
