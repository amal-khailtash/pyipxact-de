"""Top element category TGI functions (IEEE 1685-2022).

BASE operations enumerate registered roots and access their VLNV and XML file
metadata. EXTENDED operations create roots, signal editing and update file
locations. Optional container arguments preserve historical scoped traversal.
"""
from collections.abc import Iterable, Sequence
from types import SimpleNamespace
from typing import Any

from org.accellera.ipxact.v1685_2022 import (
    AbstractionDefinition,
    Abstractor,
    AbstractorBusInterfaceType,
    AbstractorModeType,
    BusDefinition,
    Catalog,
    Component,
    Design,
    DesignConfiguration,
    Generator,
    GeneratorChain,
    IpxactUri,
    LibraryRefType,
    TypeDefinitions,
    Wire,
)

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    register_parent,
    registry,
    resolve_handle,
    vlnv_to_tuple,
)

__all__ = [
    # BASE (F.7.79)
    "getAbstractionDefIDs",
    "getAbstractorIDs",
    "getBusDefIDs",
    "getCatalogIDs",
    "getComponentIDs",
    "getDesignConfigurationIDs",
    "getDesignIDs",
    "getGeneratorChainIDs",
    "getID",
    "getTypeDefinitionsIDs",
    "getVLNV",
    "getXMLPath",
    # EXTENDED (F.7.80)
    "createAbstractionDef",
    "createAbstractor",
    "createBusDefinition",
    "createCatalog",
    "createComponent",
    "createDesign",
    "createDesignConfiguration",
    "createGeneratorChain",
    "createTypeDefinitions",
    "edit",
    "setXMLPath",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------

def _resolve_top(topID: str) -> Any | None:
    """Resolve a top element handle.

    Args:
        topID: Handle of the presumed top element.

    Returns:
        The underlying object or ``None`` if not found.
    """
    obj = resolve_handle(topID)
    return obj


def _collect_ids(container: Any | None, attr: str) -> list[str]:
    """Collect handles for elements of a named list attribute.

    Args:
        container: Parent object (may be ``None``).
        attr: Name of attribute expected to be a list (e.g. ``components``).

    Returns:
        List of child handles (empty if container/attribute absent).
    """
    if container is None or container is False:
        return []
    coll = getattr(container, attr, None)
    if coll is None:
        return []
    if isinstance(coll, list):
        return [get_handle(e) for e in coll]
    # Some generated group classes may wrap list under attribute
    if hasattr(coll, attr[:-1]):  # crude heuristic
        inner = getattr(coll, attr[:-1])
        if isinstance(inner, list):
            return [get_handle(e) for e in inner]
    # Fallback: treat as iterable
    if isinstance(coll, Iterable):
        return [get_handle(e) for e in coll]  # type: ignore[arg-type]
    return []


def _ensure_collection(top: Any, attr: str) -> list[Any]:
    """Return an existing list attribute or create an empty one.

    Args:
        top: Top element object.
        attr: Attribute name for the collection.

    Returns:
        The list instance stored on the object (created if missing).
    """
    existing = getattr(top, attr, None)
    if existing is None:
        new_list: list[Any] = []
        setattr(top, attr, new_list)
        return new_list
    return existing  # type: ignore[return-value]


def _new_or_ns(cls, **kwargs: Any) -> Any:
    """Instantiate *cls* with kwargs or fall back to ``SimpleNamespace``.

    Args:
        cls: Target class (schema generated when available).
        **kwargs: Initialization keyword arguments.

    Returns:
        Instance of ``cls`` or a ``SimpleNamespace`` with the same attributes.
    """
    try:  # pragma: no cover - happy path
        return cls(**kwargs)  # type: ignore[call-arg]
    except Exception:  # pragma: no cover - fallback
        return SimpleNamespace(**kwargs)


def _create_registered_root(cls, vlnv: Sequence[str], **kwargs: Any) -> str | None:
    """Create a generated root and register it; duplicate VLNVs return null."""
    parts = vlnv_to_tuple(vlnv)
    if not all(isinstance(part, str) and part.strip() for part in parts):
        raise TgiError("VLNV requires four nonempty strings", TgiFaultCode.INVALID_ARGUMENT)
    if registry.get_id(parts) is not None:
        return None
    obj = cls(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3], **kwargs)
    try:
        registry.register(obj, parts)
    except TgiError as exc:
        if exc.fault_code == TgiFaultCode.ALREADY_EXISTS:
            return None
        raise
    return get_handle(obj)


# ---------------------------------------------------------------------------
# BASE (F.7.79) traversal & meta
# ---------------------------------------------------------------------------

def getAbstractionDefIDs(topElementID: str | None = None) -> list[str]:  # F.7.79.1
    """Return handles of Abstraction Definitions under a top element.

    Without arguments, enumerate registered roots (F.7.79.1).
    The optional top handle preserves historical scoped traversal.
    """
    if topElementID is None:
        return list(registry.iter_by_predicate(lambda root: isinstance(root, AbstractionDefinition)))
    top = _resolve_top(topElementID)
    return _collect_ids(top, "abstraction_definitions")


def getAbstractorIDs(topElementID: str | None = None) -> list[str]:  # F.7.79.2
    """Return handles of Abstractors under a top element registered in the environment."""
    if topElementID is None:
        return list(registry.iter_by_predicate(lambda root: isinstance(root, Abstractor)))
    top = _resolve_top(topElementID)
    return _collect_ids(top, "abstractors")


def getBusDefIDs(topElementID: str | None = None) -> list[str]:  # F.7.79.3
    """Return handles of Bus Definitions registered in the environment."""
    if topElementID is None:
        return list(registry.iter_by_predicate(lambda root: isinstance(root, BusDefinition)))
    top = _resolve_top(topElementID)
    return _collect_ids(top, "bus_definitions")


def _getCatalogIDs_spec(topElementID: str) -> list[str]:  # F.7.79.4
    """Return handles of Catalogs (BASE)."""
    top = _resolve_top(topElementID)
    return _collect_ids(top, "catalogs")


# Non-spec convenience alias required by existing tests exercising
# traversal over globally registered catalogs. Without argument it
# enumerates registered catalog roots (Administrative/Creation layer).
def _getCatalogIDs_noarg() -> list[str]:  # pragma: no cover - thin wrapper
    # Enumerate registered roots that are Catalog instances (or duck-type)
    def _is_catalog(obj: Any) -> bool:
        return obj.__class__.__name__ == "Catalog"

    return list(registry.iter_by_predicate(_is_catalog))


# Preserve backwards compatibility: if called without argument fall back
# to registry enumeration. This maintains spec signature while honoring
# test expectations during development phase.
def getCatalogIDs(*args, **kwargs):  # type: ignore[override]
    """Hybrid traversal.

    Dev-phase convenience: with no arguments enumerate globally
    registered root Catalog handles. With an argument delegate to the
    spec-conformant top-element scoped enumeration.
    """
    if not args and not kwargs:
        return _getCatalogIDs_noarg()
    return _getCatalogIDs_spec(*args, **kwargs)


def getComponentIDs(topElementID: str | None = None) -> list[str]:  # F.7.79.5
    """Return handles of Components registered in the environment."""
    if topElementID is None:
        return list(registry.iter_by_predicate(lambda root: isinstance(root, Component)))
    top = _resolve_top(topElementID)
    return _collect_ids(top, "components")


def getDesignConfigurationIDs(topElementID: str | None = None) -> list[str]:  # F.7.79.6
    """Return handles of Design Configurations registered in the environment."""
    if topElementID is None:
        return list(registry.iter_by_predicate(lambda root: isinstance(root, DesignConfiguration)))
    top = _resolve_top(topElementID)
    return _collect_ids(top, "design_configurations")


def getDesignIDs(topElementID: str | None = None) -> list[str]:  # F.7.79.7
    """Return handles of Designs registered in the environment."""
    if topElementID is None:
        return list(registry.iter_by_predicate(lambda root: isinstance(root, Design)))
    top = _resolve_top(topElementID)
    return _collect_ids(top, "designs")


def getGeneratorChainIDs(topElementID: str | None = None) -> list[str]:  # F.7.79.8
    """Return handles of Generator Chains registered in the environment."""
    if topElementID is None:
        return list(registry.iter_by_predicate(lambda root: isinstance(root, GeneratorChain)))
    top = _resolve_top(topElementID)
    return _collect_ids(top, "generator_chains")


def getID(elementID):  # F.7.79.9
    """Resolve a registered root by four-part VLNV (F.7.79.9).

    A handle argument is retained as a historical identity convenience.
    Unknown VLNVs and invalid handles return None.
    """
    # VLNV pattern
    if isinstance(elementID, list | tuple) and len(elementID) == 4 and all(
        isinstance(p, str) for p in elementID
    ):
        return registry.get_id(elementID)  # administrative semantics
    if not isinstance(elementID, str):  # not a handle
        return None
    obj = resolve_handle(elementID)
    return None if obj is None else get_handle(obj)


def getTypeDefinitionsIDs(topElementID: str | None = None) -> list[str]:  # F.7.79.10
    """Return handles of Type Definitions registered in the environment."""
    if topElementID is None:
        return list(registry.iter_by_predicate(lambda root: isinstance(root, TypeDefinitions)))
    top = _resolve_top(topElementID)
    return _collect_ids(top, "type_definitions")


def getVLNV(elementID: str):  # F.7.79.11
    """Return the registered root VLNV, or None if no association exists (F.7.79.11)."""
    return registry.get_vlnv(elementID) if isinstance(elementID, str) else None


def getXMLPath(elementID: str, dereference: bool = False) -> str | None:  # F.7.79.12
    """Return the registered XML file location, optionally resolving filesystem links.

    An unregistered root or a root without a file location returns None.
    """
    from pathlib import Path

    if not isinstance(dereference, bool):
        raise TgiError("dereference requires a Boolean", TgiFaultCode.INVALID_ARGUMENT)
    path = registry.get_file_name(elementID)
    return str(Path(path).resolve()) if path is not None and dereference else path


# ---------------------------------------------------------------------------
# EXTENDED (F.7.80) creation & edit
# ---------------------------------------------------------------------------

def _required_text(value: str, label: str) -> None:
    """Reject missing or non-string names before registering a root."""
    if not isinstance(value, str) or not value.strip():
        raise TgiError(f"{label} requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)


def _bus_reference(vlnv: Sequence[str]) -> LibraryRefType:
    """Validate a referenced bus VLNV without requiring repository resolution."""
    parts = vlnv_to_tuple(vlnv)
    if not all(isinstance(part, str) and part.strip() for part in parts):
        raise TgiError("Bus VLNV requires four nonempty strings", TgiFaultCode.INVALID_ARGUMENT)
    return LibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])


def createAbstractionDef(
    abstractionDefVLNV: Sequence[str], busDefVLNV: Sequence[str], logicalName: str, type: str
) -> str | None:
    """Create an abstraction with its initial wire or transactional port (F.7.80.1).

    Invalid inputs raise INVALID_ARGUMENT; duplicate root VLNVs return None.
    The bus reference need not already exist in the registry.
    """
    _required_text(logicalName, "Logical port name")
    if type not in ("wire", "transactional"):
        raise TgiError("Port style must be wire or transactional", TgiFaultCode.INVALID_ARGUMENT)
    bus = _bus_reference(busDefVLNV)
    port = AbstractionDefinition.Ports.Port(
        logical_name=logicalName,
        wire_or_transactional=Wire() if type == "wire" else AbstractionDefinition.Ports.Port.Transactional(),
    )
    handle = _create_registered_root(
        AbstractionDefinition, abstractionDefVLNV, bus_type=bus, ports=AbstractionDefinition.Ports(port=[port])
    )
    if handle is not None:
        register_parent(port, resolve_handle(handle), ("ports", "port"), "list")
    return handle


def createAbstractor(
    vlnv: Sequence[str], mode: str, busDefVLNV: Sequence[str],
    firstBusInterfaceName: str, secondBusInterfaceName: str,
) -> str | None:
    """Create an abstractor with its mode, bus reference, and two interfaces (F.7.80.2).

    Invalid inputs raise INVALID_ARGUMENT; duplicate root VLNVs return None.
    System mode is initialized without a group because this operation has no
    group input; callers must supply it before semantic validation.
    """
    try:
        mode_value = AbstractorModeType(mode)
    except (ValueError, TypeError):
        raise TgiError("Invalid abstractor mode", TgiFaultCode.INVALID_ARGUMENT) from None
    _required_text(firstBusInterfaceName, "First interface name")
    _required_text(secondBusInterfaceName, "Second interface name")
    if firstBusInterfaceName == secondBusInterfaceName:
        raise TgiError("Abstractor interface names must differ", TgiFaultCode.INVALID_ARGUMENT)
    bus = _bus_reference(busDefVLNV)
    interfaces = [AbstractorBusInterfaceType(name=firstBusInterfaceName),
                  AbstractorBusInterfaceType(name=secondBusInterfaceName)]
    mode_object = Abstractor.AbstractorMode(value=mode_value)
    handle = _create_registered_root(
        Abstractor, vlnv, abstractor_mode=mode_object, bus_type=bus,
        abstractor_interfaces=Abstractor.AbstractorInterfaces(abstractor_interface=interfaces),
    )
    if handle is not None:
        root = resolve_handle(handle)
        register_parent(mode_object, root, ("abstractor_mode",), "scalar")
        for interface in interfaces:
            register_parent(interface, root, ("abstractor_interfaces", "abstractor_interface"), "list")
    return handle


def createBusDefinition(vlnv: Sequence[str], directConnection: bool, isAddressable: bool) -> str | None:
    """Create a bus definition with Boolean capabilities (F.7.80.3)."""
    if not isinstance(directConnection, bool) or not isinstance(isAddressable, bool):
        raise TgiError("Bus capabilities require Boolean values", TgiFaultCode.INVALID_ARGUMENT)
    return _create_registered_root(
        BusDefinition, vlnv, direct_connection=directConnection, is_addressable=isAddressable
    )


def createCatalog(vlnv: Sequence[str] | str, name: str | None = None) -> str | None:  # F.7.80.4
    """Create and register a catalog from its VLNV (F.7.80.4).

    Duplicate VLNVs return None. The historical top-handle/name form remains
    available as a convenience overload, outside the standard contract.
    """
    if name is None:
        return _create_registered_root(Catalog, vlnv)
    # Preserve the historical top-handle/name convenience form.
    topElementID = vlnv
    top = _resolve_top(topElementID)
    if top is None:
        raise TgiError("Invalid top element handle", TgiFaultCode.INVALID_ID)
    coll = _ensure_collection(top, "catalogs")
    obj = _new_or_ns(Catalog, name=name)
    coll.append(obj)
    register_parent(obj, top, ("catalogs",), "list")
    return get_handle(obj)


def createComponent(vlnv: Sequence[str] | str, name: str | None = None) -> str | None:  # F.7.80.5
    """Create a Component (EXTENDED)."""
    if name is None:
        return _create_registered_root(Component, vlnv)
    # Preserve the historical top-handle/name convenience form.
    topElementID = vlnv
    top = _resolve_top(topElementID)
    if top is None:
        raise TgiError("Invalid top element handle", TgiFaultCode.INVALID_ID)
    coll = _ensure_collection(top, "components")
    obj = _new_or_ns(Component, name=name)
    coll.append(obj)
    register_parent(obj, top, ("components",), "list")
    return get_handle(obj)


def createDesign(vlnv: Sequence[str] | str, name: str | None = None) -> str | None:  # F.7.80.6
    """Create a Design (EXTENDED)."""
    if name is None:
        return _create_registered_root(Design, vlnv)
    # Preserve the historical top-handle/name convenience form.
    topElementID = vlnv
    top = _resolve_top(topElementID)
    if top is None:
        raise TgiError("Invalid top element handle", TgiFaultCode.INVALID_ID)
    coll = _ensure_collection(top, "designs")
    obj = _new_or_ns(Design, name=name)
    coll.append(obj)
    register_parent(obj, top, ("designs",), "list")
    return get_handle(obj)


def createDesignConfiguration(vlnv: Sequence[str] | str, name: str | None = None) -> str | None:  # F.7.80.7
    """Create a Design Configuration (EXTENDED)."""
    if name is None:
        return _create_registered_root(DesignConfiguration, vlnv)
    # Preserve the historical top-handle/name convenience form.
    topElementID = vlnv
    top = _resolve_top(topElementID)
    if top is None:
        raise TgiError("Invalid top element handle", TgiFaultCode.INVALID_ID)
    coll = _ensure_collection(top, "design_configurations")
    obj = _new_or_ns(DesignConfiguration, name=name)
    coll.append(obj)
    register_parent(obj, top, ("design_configurations",), "list")
    return get_handle(obj)


def createGeneratorChain(generatorChainVLNV: Sequence[str], generatorName: str, generatorExe: str) -> str | None:
    """Create a chain containing its initial generator (F.7.80.8)."""
    if not isinstance(generatorName, str) or not generatorName.strip():
        raise TgiError("Generator name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if not isinstance(generatorExe, str) or not generatorExe.strip():
        raise TgiError("Generator executable requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    generator = Generator(name=generatorName, generator_exe=IpxactUri(value=generatorExe))
    handle = _create_registered_root(
        GeneratorChain, generatorChainVLNV,
        generator_chain_selector_or_component_generator_selector_or_generator=[generator],
    )
    if handle is not None:
        register_parent(
            generator, resolve_handle(handle),
            ("generator_chain_selector_or_component_generator_selector_or_generator",), "list",
        )
    return handle


def createTypeDefinitions(vlnv: Sequence[str] | str, name: str | None = None) -> str | None:  # F.7.80.9
    """Create a TypeDefinitions element (EXTENDED)."""
    if name is None:
        return _create_registered_root(TypeDefinitions, vlnv)
    # Preserve the historical top-handle/name convenience form.
    topElementID = vlnv
    top = _resolve_top(topElementID)
    if top is None:
        raise TgiError("Invalid top element handle", TgiFaultCode.INVALID_ID)
    coll = _ensure_collection(top, "type_definitions")
    obj = _new_or_ns(TypeDefinitions, name=name)
    coll.append(obj)
    register_parent(obj, top, ("type_definitions",), "list")
    return get_handle(obj)


def edit(elementID: str) -> bool:  # F.7.80.10
    """Signal the start of editing a registered root in this writable environment.

    No checkout is required by the in-memory backend; model content is preserved.
    Unknown, unregistered and child handles return False.
    """
    return registry.get_vlnv(elementID) is not None


def setXMLPath(elementID: str, path: str) -> bool:  # F.7.80.11
    """Set a registered root's XML location without modifying serialized content."""
    if registry.get_vlnv(elementID) is None:
        raise TgiError("Invalid registered root handle", TgiFaultCode.INVALID_ID)
    if not isinstance(path, str) or not path.strip():
        raise TgiError("XML path requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    return registry.set_file_name(elementID, path)
