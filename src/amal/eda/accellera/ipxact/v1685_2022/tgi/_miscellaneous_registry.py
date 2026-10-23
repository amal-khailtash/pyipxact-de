"""VLNV registration and document persistence for Miscellaneous TGI."""

import os
import stat
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import etree
from xsdata.exceptions import ParserError, SerializerError

from amal.eda.ipxact_de.xml_document import XmlDocument
from amal.eda.ipxact_de.xml_validation import validate_ipxact_xml
from org.accellera.ipxact.v1685_2022 import (
    AbstractionDefinition,
    Abstractor,
    BusDefinition,
    Catalog,
    Component,
    Design,
    DesignConfiguration,
    GeneratorChain,
    IpxactFileType,
    TypeDefinitions,
)

from .core import VLNV, TgiError, TgiFaultCode, registry, resolve_handle

__all__: list[str] = [
    "registerCatalogVLNVs",
    "registerVLNV",
    "save",
    "unregisterCatalogVLNVs",
    "unregisterVLNV",
]

type _Root = (
    AbstractionDefinition
    | Abstractor
    | BusDefinition
    | Catalog
    | Component
    | Design
    | DesignConfiguration
    | GeneratorChain
    | TypeDefinitions
)

_ROOT_TYPES: dict[str, type[_Root]] = {
    "abstractor": Abstractor,
    "abstractionDefinition": AbstractionDefinition,
    "busDefinition": BusDefinition,
    "catalog": Catalog,
    "component": Component,
    "design": Design,
    "designConfiguration": DesignConfiguration,
    "generatorChain": GeneratorChain,
    "typeDefinitions": TypeDefinitions,
}
_ROOT_CLASS_NAMES = tuple(_ROOT_TYPES.values())
_CATALOG_FIELDS = (
    "catalogs",
    "bus_definitions",
    "abstraction_definitions",
    "components",
    "abstractors",
    "designs",
    "design_configurations",
    "generator_chains",
    "type_definitions",
)


def _load_root(file_name: str | Path, expected_type: type[_Root] | None = None) -> tuple[_Root, VLNV, Path]:
    """Parse a supported 1685-2022 top-level IP-XACT document."""
    path = Path(file_name).expanduser().resolve(strict=True)
    document = XmlDocument(path)
    if document.standard != "IPXACT" or document.version != "1685-2022":
        raise ValueError("Only IEEE 1685-2022 IP-XACT files can be registered")
    root_type = _ROOT_TYPES.get(document.root_name)
    if root_type is None or (expected_type is not None and root_type is not expected_type):
        raise ValueError("File root is not the expected top-level IP-XACT document")
    root = XmlDocument.parser().from_string(path.read_text(encoding="utf-8"), root_type)
    vlnv = _root_vlnv(root)
    return root, vlnv, path


def _root_vlnv(root: object) -> VLNV:
    """Read and validate the four VLNV fields on a top-level model."""
    values = tuple(getattr(root, field, None) for field in ("vendor", "library", "name", "version"))
    return _validated_vlnv(values, "Top-level document has no complete VLNV")


def _validated_vlnv(values: tuple[object, ...], message: str) -> VLNV:
    """Validate four VLNV fields and return a statically typed tuple."""
    if len(values) != 4:
        raise ValueError(message)
    vendor, library, name, version = values
    if (
        not isinstance(vendor, str)
        or not vendor.strip()
        or not isinstance(library, str)
        or not library.strip()
        or not isinstance(name, str)
        or not name.strip()
        or not isinstance(version, str)
        or not version.strip()
    ):
        raise ValueError(message)
    return vendor, library, name, version


def _catalog(catalog_id: str) -> tuple[Catalog, Path]:
    """Resolve a catalog handle and its source directory."""
    catalog = resolve_handle(catalog_id) if isinstance(catalog_id, str) else None
    file_name = registry.get_file_name(catalog_id) if isinstance(catalog_id, str) else None
    if not isinstance(catalog, Catalog) or not file_name:
        raise TgiError("Catalog handle is not a registered document", TgiFaultCode.INVALID_ID)
    return catalog, Path(file_name).expanduser().resolve().parent


def _catalog_entries(catalog: Catalog) -> list[tuple[IpxactFileType, VLNV, type[_Root]]]:
    """Return each declared VLNV with its catalog entry and expected root type."""
    entries: list[tuple[IpxactFileType, VLNV, type[_Root]]] = []
    for field in _CATALOG_FIELDS:
        files = getattr(catalog, field)
        if files is None:
            continue
        expected_root_name = {
            "catalogs": "catalog",
            "bus_definitions": "busDefinition",
            "abstraction_definitions": "abstractionDefinition",
            "components": "component",
            "abstractors": "abstractor",
            "designs": "design",
            "design_configurations": "designConfiguration",
            "generator_chains": "generatorChain",
            "type_definitions": "typeDefinitions",
        }[field]
        expected_type = _ROOT_TYPES[expected_root_name]
        for entry in files.ipxact_file:
            if entry.vlnv is None:
                raise ValueError("Catalog entry has no VLNV")
            values = tuple(getattr(entry.vlnv, attr, None) for attr in ("vendor", "library", "name", "version"))
            vlnv = _validated_vlnv(values, "Catalog entry has an incomplete VLNV")
            entries.append((entry, vlnv, expected_type))
    return entries


def _catalog_targets(
    entries: list[tuple[IpxactFileType, VLNV, type[_Root]]], base_dir: Path
) -> list[tuple[Path, VLNV, type[_Root]]]:
    """Resolve catalog entry URIs to local document paths."""
    targets: list[tuple[Path, VLNV, type[_Root]]] = []
    for entry, vlnv, expected_type in entries:
        if entry.name is None:
            raise ValueError("Catalog entry has no file name")
        uri_text = getattr(entry.name, "value", None)
        if not isinstance(uri_text, str) or not uri_text.strip():
            raise ValueError("Catalog entry has no file name")
        uri = urlsplit(uri_text.strip())
        if (
            uri.scheme not in ("", "file")
            or uri.netloc not in ("", "localhost")
            or uri.query
            or uri.fragment
            or not uri.path
        ):
            raise ValueError(f"Catalog URI is not a local file: {uri_text}")
        if any(ord(char) < 32 for char in uri.path) or "%" in uri.path and "%00" in uri.path.lower():
            raise ValueError("Catalog URI contains invalid path data")
        target_path = (base_dir / unquote(uri.path, errors="strict")).resolve(strict=True)
        targets.append((target_path, vlnv, expected_type))
    return targets


def registerVLNV(fileName: str, replace: bool) -> bool:
    """Register a top-level IP-XACT document loaded from ``fileName``."""
    if not isinstance(fileName, str) or not isinstance(replace, bool):
        return False
    try:
        root, vlnv, path = _load_root(fileName)
        existing_id = registry.get_id(vlnv)
        if existing_id is not None and not replace:
            return False
        if existing_id is not None:
            registry.unregister(vlnv)
        registry.register(root, vlnv, file_name=str(path), replace=False, element_type=type(root).__name__)
        return True
    except OSError, UnicodeError, etree.XMLSyntaxError, ParserError, ValueError, TgiError:
        return False


def _catalog_registry_change(catalog_id: str, *, register: bool) -> bool:
    try:
        catalog, base_dir = _catalog(catalog_id)
        entries = _catalog_entries(catalog)
        targets = _catalog_targets(entries, base_dir) if register else []
        if not register:
            for _entry, vlnv, _expected_type in entries:
                registry.unregister(vlnv)
            return True
        loaded = [_load_root(path, expected_type) for path, _vlnv, expected_type in targets]
        for (_root, actual_vlnv, _path), (_target, expected_vlnv, _root_type) in zip(loaded, targets, strict=True):
            if actual_vlnv != expected_vlnv:
                raise ValueError("Catalog VLNV does not match the referenced document")
        pending: dict[VLNV, tuple[_Root, Path]] = {}
        for root, vlnv, path in loaded:
            if vlnv in pending and pending[vlnv][1] != path:
                return False
            pending[vlnv] = (root, path)
        if any(registry.get_id(vlnv) is not None for vlnv in pending):
            return False
        for vlnv, (root, path) in pending.items():
            registry.register(root, vlnv, file_name=str(path), element_type=type(root).__name__)
        return True
    except OSError, UnicodeError, etree.XMLSyntaxError, ParserError, ValueError, TgiError:
        return False


def registerCatalogVLNVs(catalogID: str) -> bool:
    """Register the actual top-level documents referenced by a catalog."""
    return _catalog_registry_change(catalogID, register=True)


def unregisterCatalogVLNVs(catalogID: str) -> bool:
    """Unregister the VLNVs referenced by a catalog."""
    return _catalog_registry_change(catalogID, register=False)


def unregisterVLNV(VLNV: tuple[str, str, str, str] | list[str]) -> bool:
    """Unregister the requested four-part VLNV."""
    try:
        if isinstance(VLNV, str) or len(VLNV) != 4 or not all(isinstance(part, str) for part in VLNV):
            return False
        return registry.unregister(VLNV)
    except TypeError, TgiError:
        return False


def _schema_root() -> Path | None:
    """Find the checked-out schema tree when running from a source checkout."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "submodules" / "accellera-schemas"
        if candidate.is_dir():
            return candidate
    candidate = Path.cwd() / "submodules" / "accellera-schemas"
    return candidate if candidate.is_dir() else None


def _staged_valid(path: Path, content: str) -> Path | None:
    """Write and validate a same-directory temporary document."""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".xml", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        result = validate_ipxact_xml(temporary, schema_root=_schema_root())
        if not result.ok:
            temporary.unlink(missing_ok=True)
            return None
        return temporary
    except OSError, UnicodeError, ValueError, etree.XMLSyntaxError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        return None


def save() -> bool:
    """Persist registered top-level models after schema validation."""
    staged: list[tuple[Path, Path]] = []
    try:
        handles = list(registry.iter_by_predicate(lambda root: isinstance(root, _ROOT_CLASS_NAMES)))
        for handle in handles:
            root = resolve_handle(handle)
            file_name = registry.get_file_name(handle)
            if root is None or file_name is None:
                return False
            path = Path(file_name).expanduser().resolve()
            if not path.is_file():
                return False
            staged_path = _staged_valid(path, XmlDocument.serializer().render(root))
            if staged_path is None:
                return False
            staged.append((staged_path, path))
        for temporary, path in staged:
            os.replace(temporary, path)
        return True
    except OSError, RuntimeError, ValueError, TypeError, SerializerError:
        return False
    finally:
        for temporary, _path in staged:
            temporary.unlink(missing_ok=True)
