"""Catalog category TGI functions (IEEE 1685-2022).

Implements the Catalog BASE functions in F.7.23 and EXTENDED functions in
F.7.24. Catalogs contain ordered ``ipxactFile`` entries grouped under nine
IP-XACT document categories. Entry handles retain their Catalog and category
ownership so the extended operations can validate, update, and remove records.
"""

from collections.abc import Sequence

from org.accellera.ipxact.v1685_2022 import (
    Catalog,
    IpxactFilesType,
    IpxactFileType,
    IpxactUri,
    LibraryRefType,
)

from ._attribute_references import _root_for
from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    resolve_handle,
)

__all__ = [
    # BASE (F.7.23)
    "getCatalogAbstractionDefIpxactFileIDs",
    "getCatalogAbstractorsIpxactFileIDs",
    "getCatalogBusDefinitionsIpxactFileIDs",
    "getCatalogCatalogsIpxactFileIDs",
    "getCatalogComponentsIpxactFileIDs",
    "getCatalogDesignConfigurationsIpxactFileIDs",
    "getCatalogDesignsIpxactFileIDs",
    "getCatalogGeneratorChainsIpxactFileIDs",
    "getCatalogTypeDefinitionsIpxactFileIDs",
    "getIpxactFileName",
    "getIpxactFileVlnvRefByVLNV",
    # EXTENDED (F.7.24)
    "addCatalogAbstractionDefIpxactFile",
    "addCatalogAbstractorsIpxactFile",
    "addCatalogBusDefinitionsIpxactFile",
    "addCatalogCatalogsIpxactFile",
    "addCatalogComponentsIpxactFile",
    "addCatalogDesignConfigurationsIpxactFile",
    "addCatalogDesignsIpxactFile",
    "addCatalogGeneratorChainsIpxactFile",
    "addCatalogTypeDefinitionsIpxactFile",
    "removeCatalogAbstractionDefIpxactFile",
    "removeCatalogAbstractorsIpxactFile",
    "removeCatalogBusDefinitionsIpxactFile",
    "removeCatalogCatalogsIpxactFile",
    "removeCatalogComponentsIpxactFile",
    "removeCatalogDesignConfigurationsIpxactFile",
    "removeCatalogDesignsIpxactFile",
    "removeCatalogGeneratorChainsIpxactFile",
    "removeCatalogTypeDefinitionsIpxactFile",
    "setIpxactFileName",
    "setIpxactFileVlnv",
]

_CATEGORY_FIELDS = (
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


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _catalog(catalog_id: str | Catalog) -> Catalog:
    """Resolve a Catalog TGI handle, retaining support for direct model calls."""
    if not isinstance(catalog_id, (str, Catalog)):
        raise TgiError("Invalid catalog handle", TgiFaultCode.INVALID_ID)
    catalog = catalog_id if isinstance(catalog_id, Catalog) else resolve_handle(catalog_id)
    if not isinstance(catalog, Catalog):
        raise TgiError("Invalid catalog handle", TgiFaultCode.INVALID_ID)
    return catalog


def _catalog_entry(ipxact_file_id: str | IpxactFileType) -> IpxactFileType:
    """Resolve an ipxactFile handle, retaining support for direct model calls."""
    if not isinstance(ipxact_file_id, (str, IpxactFileType)):
        raise TgiError("Invalid ipxactFile handle", TgiFaultCode.INVALID_ID)
    entry = ipxact_file_id if isinstance(ipxact_file_id, IpxactFileType) else resolve_handle(ipxact_file_id)
    if not isinstance(entry, IpxactFileType):
        raise TgiError("Invalid ipxactFile handle", TgiFaultCode.INVALID_ID)
    return entry


def _register_category(catalog: Catalog, field: str) -> list[str]:
    """Return ordered entry IDs and record typed nested ownership."""
    files = getattr(catalog, field)
    if files is None:
        return []

    register_parent(files, catalog, (field,), "single")
    handles: list[str] = []
    for entry in files.ipxact_file:
        handle = get_handle(entry)
        register_parent(entry, catalog, (field, "ipxact_file"), "list")
        _register_entry_references(entry)
        handles.append(handle)
    return handles


def _register_entry_references(entry: IpxactFileType) -> None:
    """Register the required typed reference wrappers under their entry."""
    for field in ("name", "vlnv"):
        reference = getattr(entry, field)
        if reference is not None:
            register_parent(reference, entry, (field,), "single")


def _catalog_entries(catalog_id: str | Catalog, field: str) -> list[str]:
    """Return category entry handles from a Catalog handle or legacy object."""
    return _register_category(_catalog(catalog_id), field)


def _resolve_vlnv(vlnv: Sequence[str]) -> tuple[str, str, str, str]:
    """Validate a four-string VLNV before any Catalog mutation."""
    if isinstance(vlnv, str):
        raise TgiError("VLNV must be a four-string sequence", TgiFaultCode.INVALID_ARGUMENT)
    try:
        values = tuple(vlnv)
    except TypeError as exc:
        raise TgiError("VLNV must be a four-string sequence", TgiFaultCode.INVALID_ARGUMENT) from exc
    if len(values) != 4 or not all(isinstance(value, str) and value for value in values):
        raise TgiError("VLNV must contain four non-empty strings", TgiFaultCode.INVALID_ARGUMENT)
    return values  # type: ignore[return-value]


def _check_unique(
    catalog: Catalog,
    *,
    entry: IpxactFileType | None = None,
    name: str | None = None,
    vlnv: tuple[str, str, str, str] | None = None,
) -> None:
    """Enforce catalog.xsd name and VLNV uniqueness across all categories."""
    for field in _CATEGORY_FIELDS:
        files = getattr(catalog, field)
        if files is None:
            continue
        for candidate in files.ipxact_file:
            if candidate is entry:
                continue
            if name is not None and candidate.name is not None and candidate.name.value == name:
                raise TgiError("Catalog ipxactFile name already exists", TgiFaultCode.ALREADY_EXISTS)
            if candidate.vlnv is not None and vlnv is not None:
                current_vlnv = (
                    candidate.vlnv.vendor,
                    candidate.vlnv.library,
                    candidate.vlnv.name,
                    candidate.vlnv.version,
                )
                if current_vlnv == vlnv:
                    raise TgiError("Catalog ipxactFile VLNV already exists", TgiFaultCode.ALREADY_EXISTS)


def _entry_catalog_and_field(entry: IpxactFileType) -> tuple[Catalog, str] | None:
    """Return parsed owning Catalog/category when this entry has typed ownership."""
    info = get_parent_info(get_handle(entry))
    if info is not None and info.container == "list" and len(info.path) == 2 and info.path[1] == "ipxact_file":
        catalog = resolve_handle(info.parent_handle)
        field = info.path[0]
        if isinstance(catalog, Catalog) and field in _CATEGORY_FIELDS:
            files = getattr(catalog, field)
            if files is not None and any(candidate is entry for candidate in files.ipxact_file):
                _register_entry_references(entry)
                return catalog, field

    # A handle can be obtained directly from a nested model before any Catalog
    # getter has traversed it. Discover its registered top-level owner and
    # establish the same typed category path used by BASE enumeration.
    catalog = _root_for(entry)
    if not isinstance(catalog, Catalog):
        return None
    for field in _CATEGORY_FIELDS:
        files = getattr(catalog, field)
        if files is not None and any(candidate is entry for candidate in files.ipxact_file):
            register_parent(files, catalog, (field,), "single")
            register_parent(entry, catalog, (field, "ipxact_file"), "list")
            _register_entry_references(entry)
            return catalog, field
    return None


def _mutate_catalog_entry(
    ipxact_file_id: str | IpxactFileType,
    *,
    field: str | None = None,
    name: str | None = None,
    vlnv: Sequence[str] | None = None,
) -> bool:
    """Add or update an entry after validating schema-wide uniqueness."""
    entry = _catalog_entry(ipxact_file_id)
    owner = _entry_catalog_and_field(entry)
    if field is not None and (owner is None or owner[1] != field):
        raise TgiError("ipxactFile handle does not belong to the requested category", TgiFaultCode.INVALID_ID)

    vlnv_tuple = _resolve_vlnv(vlnv) if vlnv is not None else None
    if name is not None and not isinstance(name, str):
        raise TgiError("ipxactFile name must be a string", TgiFaultCode.INVALID_ARGUMENT)
    if owner is not None and (name is not None or vlnv_tuple is not None):
        _check_unique(owner[0], entry=entry, name=name, vlnv=vlnv_tuple)

    if name is not None:
        if entry.name is None:
            entry.name = IpxactUri(value=name)
        else:
            entry.name.value = name
        register_parent(entry.name, entry, ("name",), "single")
    if vlnv_tuple is not None:
        if entry.vlnv is None:
            entry.vlnv = LibraryRefType(
                vendor=vlnv_tuple[0], library=vlnv_tuple[1], name=vlnv_tuple[2], version=vlnv_tuple[3]
            )
        else:
            entry.vlnv.vendor, entry.vlnv.library, entry.vlnv.name, entry.vlnv.version = vlnv_tuple
        register_parent(entry.vlnv, entry, ("vlnv",), "single")
    return True


def _add_ipxact_file(
    catalog_id: str | Catalog,
    field: str,
    vlnv: Sequence[str],
    file_name: str,
) -> str:
    """Validate and append one typed entry, then register its owner metadata."""
    catalog = _catalog(catalog_id)
    values = _resolve_vlnv(vlnv)
    if not isinstance(file_name, str):
        raise TgiError("ipxactFile name must be a string", TgiFaultCode.INVALID_ARGUMENT)
    _check_unique(catalog, name=file_name, vlnv=values)

    files = getattr(catalog, field)
    if files is None:
        files = IpxactFilesType()
    entry = IpxactFileType(
        vlnv=LibraryRefType(vendor=values[0], library=values[1], name=values[2], version=values[3]),
        name=IpxactUri(value=file_name),
    )
    current = list(files.ipxact_file)
    current.append(entry)
    files.ipxact_file = current
    setattr(catalog, field, files)
    register_parent(files, catalog, (field,), "single")
    register_parent(entry, catalog, (field, "ipxact_file"), "list")
    _register_entry_references(entry)
    return get_handle(entry)


def _remove_ipxact_file(ipxact_file_id: str, field: str) -> bool:
    """Remove the addressed entry only when it belongs to this category."""
    if not isinstance(ipxact_file_id, str):
        return False
    entry = resolve_handle(ipxact_file_id)
    if not isinstance(entry, IpxactFileType):
        return False
    owner = _entry_catalog_and_field(entry)
    if owner is None or owner[1] != field:
        return False
    catalog, _ = owner
    files = getattr(catalog, field)
    if not detach_child_by_handle(ipxact_file_id):
        return False
    if files is not None and not files.ipxact_file:
        container_id = get_handle(files)
        register_parent(files, catalog, (field,), "single")
        if not detach_child_by_handle(container_id):
            setattr(catalog, field, None)
    return True


# ---------------------------------------------------------------------------
# BASE (F.7.23)
# ---------------------------------------------------------------------------


def getCatalogAbstractionDefIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog abstractionDefinitions ipxactFile elements (F.7.23.1).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to abstractionDefinitions ipxactFile elements (empty if absent).

    Section: F.7.23.1.
    """
    return _catalog_entries(catalogID, "abstraction_definitions")


def getCatalogAbstractorsIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog abstractors ipxactFile elements (F.7.23.2).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to abstractors ipxactFile elements (empty if absent).

    Section: F.7.23.2.
    """
    return _catalog_entries(catalogID, "abstractors")


def getCatalogBusDefinitionsIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog busDefinitions ipxactFile elements (F.7.23.3).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to busDefinitions ipxactFile elements (empty if absent).

    Section: F.7.23.3.
    """
    return _catalog_entries(catalogID, "bus_definitions")


def getCatalogCatalogsIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog catalogs ipxactFile elements (F.7.23.4).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to catalogs ipxactFile elements (empty if absent).

    Section: F.7.23.4.
    """
    return _catalog_entries(catalogID, "catalogs")


def getCatalogComponentsIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog components ipxactFile elements (F.7.23.5).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to components ipxactFile elements (empty if absent).

    Section: F.7.23.5.
    """
    return _catalog_entries(catalogID, "components")


def getCatalogDesignConfigurationsIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog designConfigurations ipxactFile elements (F.7.23.6).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to designConfigurations ipxactFile elements (empty if absent).

    Section: F.7.23.6.
    """
    return _catalog_entries(catalogID, "design_configurations")


def getCatalogDesignsIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog designs ipxactFile elements (F.7.23.7).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to designs ipxactFile elements (empty if absent).

    Section: F.7.23.7.
    """
    return _catalog_entries(catalogID, "designs")


def getCatalogGeneratorChainsIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog generatorChains ipxactFile elements (F.7.23.8).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to generatorChains ipxactFile elements (empty if absent).

    Section: F.7.23.8.
    """
    return _catalog_entries(catalogID, "generator_chains")


def getCatalogTypeDefinitionsIpxactFileIDs(catalogID: str | Catalog) -> list[str]:
    """Return handles to the Catalog typeDefinitions ipxactFile elements (F.7.23.9).

    Args:
        catalogID: Handle to a catalog element; a Catalog object is accepted for compatibility.

    Returns:
        Ordered handles to typeDefinitions ipxactFile elements (empty if absent).

    Section: F.7.23.9.
    """
    return _catalog_entries(catalogID, "type_definitions")


def getIpxactFileName(ipxactFileID: str | IpxactFileType) -> str | None:
    """Return the stored file name for an ipxactFile element (F.7.23.10).

    Args:
        ipxactFileID: Handle to an ipxactFile element; a model object is accepted for compatibility.

    Returns:
        The lexical URI stored in the name element, or None for malformed model data.

    Section: F.7.23.10.
    """
    entry = _catalog_entry(ipxactFileID)
    return None if entry.name is None else entry.name.value


def getIpxactFileVlnvRefByVLNV(
    ipxactFileID: str | IpxactFileType,
) -> tuple[str, str, str, str] | None:
    """Return the four stored VLNV parts for an ipxactFile element (F.7.23.11).

    Args:
        ipxactFileID: Handle to an ipxactFile element; a model object is accepted for compatibility.

    Returns:
        The vendor, library, name, and version tuple, or None for malformed model data.

    Section: F.7.23.11.
    """
    entry = _catalog_entry(ipxactFileID)
    if entry.vlnv is None:
        return None
    return entry.vlnv.vendor, entry.vlnv.library, entry.vlnv.name, entry.vlnv.version


# ---------------------------------------------------------------------------
# EXTENDED (F.7.24)
# ---------------------------------------------------------------------------


def addCatalogAbstractionDefIpxactFile(
    catalogID: str | Catalog,
    abstractionDefVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add an abstractionDefinition ipxactFile to a catalog (F.7.24.1).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        abstractionDefVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.1.
    """
    return _add_ipxact_file(catalogID, "abstraction_definitions", abstractionDefVLNV, fileName)


def addCatalogAbstractorsIpxactFile(
    catalogID: str | Catalog,
    abstractorVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add an abstractor ipxactFile to a catalog (F.7.24.2).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        abstractorVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.2.
    """
    return _add_ipxact_file(catalogID, "abstractors", abstractorVLNV, fileName)


def addCatalogBusDefinitionsIpxactFile(
    catalogID: str | Catalog,
    busDefVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add a busDefinition ipxactFile to a catalog (F.7.24.3).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        busDefVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.3.
    """
    return _add_ipxact_file(catalogID, "bus_definitions", busDefVLNV, fileName)


def addCatalogCatalogsIpxactFile(
    catalogID: str | Catalog,
    catalogVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add a catalog ipxactFile to a catalog (F.7.24.4).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        catalogVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.4.
    """
    return _add_ipxact_file(catalogID, "catalogs", catalogVLNV, fileName)


def addCatalogComponentsIpxactFile(
    catalogID: str | Catalog,
    componentVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add a component ipxactFile to a catalog (F.7.24.5).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        componentVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.5.
    """
    return _add_ipxact_file(catalogID, "components", componentVLNV, fileName)


def addCatalogDesignConfigurationsIpxactFile(
    catalogID: str | Catalog,
    designConfigurationVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add a designConfiguration ipxactFile to a catalog (F.7.24.6).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        designConfigurationVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.6.
    """
    return _add_ipxact_file(catalogID, "design_configurations", designConfigurationVLNV, fileName)


def addCatalogDesignsIpxactFile(
    catalogID: str | Catalog,
    designVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add a design ipxactFile to a catalog (F.7.24.7).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        designVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.7.
    """
    return _add_ipxact_file(catalogID, "designs", designVLNV, fileName)


def addCatalogGeneratorChainsIpxactFile(
    catalogID: str | Catalog,
    generatorChainVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add a generatorChain ipxactFile to a catalog (F.7.24.8).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        generatorChainVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.8.
    """
    return _add_ipxact_file(catalogID, "generator_chains", generatorChainVLNV, fileName)


def addCatalogTypeDefinitionsIpxactFile(
    catalogID: str | Catalog,
    typeDefinitionVLNV: Sequence[str],
    fileName: str,
) -> str:
    """Add a typeDefinition ipxactFile to a catalog (F.7.24.9).

    Args:
        catalogID: Handle to the catalog element; a Catalog object is accepted for compatibility.
        typeDefinitionVLNV: Four strings (vendor, library, name, version).
        fileName: File name URI stored in the ipxactFile name element.

    Returns:
        Handle to the new ipxactFile element.

    Section: F.7.24.9.
    """
    return _add_ipxact_file(catalogID, "type_definitions", typeDefinitionVLNV, fileName)


def removeCatalogAbstractionDefIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed abstractionDefinitions ipxactFile element (F.7.24.10).

    Args:
        ipxactFileID: Handle to an abstractionDefinitions ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.10.
    """
    return _remove_ipxact_file(ipxactFileID, "abstraction_definitions")


def removeCatalogAbstractorsIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed abstractors ipxactFile element (F.7.24.11).

    Args:
        ipxactFileID: Handle to an abstractors ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.11.
    """
    return _remove_ipxact_file(ipxactFileID, "abstractors")


def removeCatalogBusDefinitionsIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed busDefinitions ipxactFile element (F.7.24.12).

    Args:
        ipxactFileID: Handle to a busDefinitions ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.12.
    """
    return _remove_ipxact_file(ipxactFileID, "bus_definitions")


def removeCatalogCatalogsIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed catalogs ipxactFile element (F.7.24.13).

    Args:
        ipxactFileID: Handle to a catalogs ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.13.
    """
    return _remove_ipxact_file(ipxactFileID, "catalogs")


def removeCatalogComponentsIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed components ipxactFile element (F.7.24.14).

    Args:
        ipxactFileID: Handle to a components ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.14.
    """
    return _remove_ipxact_file(ipxactFileID, "components")


def removeCatalogDesignConfigurationsIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed designConfigurations ipxactFile element (F.7.24.15).

    Args:
        ipxactFileID: Handle to a designConfigurations ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.15.
    """
    return _remove_ipxact_file(ipxactFileID, "design_configurations")


def removeCatalogDesignsIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed designs ipxactFile element (F.7.24.16).

    Args:
        ipxactFileID: Handle to a designs ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.16.
    """
    return _remove_ipxact_file(ipxactFileID, "designs")


def removeCatalogGeneratorChainsIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed generatorChains ipxactFile element (F.7.24.17).

    Args:
        ipxactFileID: Handle to a generatorChains ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.17.
    """
    return _remove_ipxact_file(ipxactFileID, "generator_chains")


def removeCatalogTypeDefinitionsIpxactFile(ipxactFileID: str) -> bool:
    """Remove the addressed typeDefinitions ipxactFile element (F.7.24.18).

    Args:
        ipxactFileID: Handle to a typeDefinitions ipxactFile element.

    Returns:
        True when that entry is removed; false if it is absent or owned by another category.

    Section: F.7.24.18.
    """
    return _remove_ipxact_file(ipxactFileID, "type_definitions")


def setIpxactFileName(ipxactFileID: str | IpxactFileType, name: str) -> bool:
    """Set the name of an ipxactFile element (F.7.24.19).

    Args:
        ipxactFileID: Handle to an ipxactFile element; a model object is accepted for compatibility.
        name: Name URI to store in the ipxactFile element.

    Returns:
        True when the name is set.

    Section: F.7.24.19.
    """
    if not isinstance(name, str):
        raise TgiError("ipxactFile name must be a string", TgiFaultCode.INVALID_ARGUMENT)
    return _mutate_catalog_entry(ipxactFileID, name=name)


def setIpxactFileVlnv(ipxactFileID: str | IpxactFileType, vlnv: Sequence[str]) -> bool:
    """Set the four-part VLNV of an ipxactFile element (F.7.24.20).

    Args:
        ipxactFileID: Handle to an ipxactFile element; a model object is accepted for compatibility.
        vlnv: Four strings (vendor, library, name, version).

    Returns:
        True when the VLNV is set.

    Section: F.7.24.20.
    """
    _resolve_vlnv(vlnv)
    return _mutate_catalog_entry(ipxactFileID, vlnv=vlnv)
