"""Abstractor category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.4) and EXTENDED (F.7.5) Abstractor functions. Only 2022
standard APIs are exposed here. Functions raise :class:`TgiError` with
``TgiFaultCode.INVALID_ID`` for invalid handles and ``TgiFaultCode.INVALID_ARGUMENT``
for semantic violations as per the general TGI error model.
"""
# ruff: noqa: I001
from __future__ import annotations

from collections.abc import Sequence

from org.accellera.ipxact.v1685_2022 import (
    Abstractor,
    AbstractorBusInterfaceType,
    AbstractorGenerator,
    AbstractorGenerators,
    AbstractorPortType,
    Choices,
    FileSet,
    FileSets,
    IpxactUri,
)
from org.accellera.ipxact.v1685_2022.abstractor_type import AbstractorType
from org.accellera.ipxact.v1685_2022.abstraction_types import AbstractionTypes
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.4)
    "getAbstractorAbstractorGeneratorIDs",
    "getAbstractorAbstractorInterfaceIDs",
    "getAbstractorAbstractorMode",
    "getAbstractorAbstractorModeID",
    "getAbstractorBusTypeRefByVLNV",
    "getAbstractorChoiceIDs",
    "getAbstractorComponentInstantiationIDs",
    "getAbstractorFileSetIDs",
    "getAbstractorInterfaceAbstractionTypeIDs",
    "getAbstractorPortIDs",
    "getAbstractorViewIDs",
    # EXTENDED (F.7.5)
    "addAbstractorAbstractorGenerator",
    "addAbstractorChoice",
    "addAbstractorComponentInstantiation",
    "addAbstractorFileSet",
    "addAbstractorInterfaceAbstractionType",
    "addAbstractorTransactionalPort",
    "addAbstractorWirePort",
    "addAbstractorStructuredInterfacePort",
    "addAbstractorStructuredStructPort",
    "addAbstractorStructuredUnionPort",
    "addAbstractorView",
    "removeAbstractorAbstractorGenerator",
    "removeAbstractorChoice",
    "removeAbstractorComponentInstantiation",
    "removeAbstractorFileSet",
    "removeAbstractorInterfaceAbstractionType",
    "removeAbstractorPort",
    "removeAbstractorView",
    "setAbstractorAbstractorMode",
    "setAbstractorBusType",
]


def _resolve(abstractorID: str) -> Abstractor | None:  # helper (non-spec)
    obj = resolve_handle(abstractorID)
    return obj if isinstance(obj, Abstractor) else None


def _resolve_port(portID: str) -> AbstractorPortType | None:  # helper
    obj = resolve_handle(portID)
    return obj if isinstance(obj, AbstractorPortType) else None


# ---------------------------------------------------------------------------
# BASE (F.7.4)
# ---------------------------------------------------------------------------

def getAbstractorAbstractorGeneratorIDs(abstractorID: str) -> list[str]:
    """Return handles of all ``abstractorGenerator`` children.

    Section: F.7.4.1.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if a.abstractor_generators is None:
        return []
    return [get_handle(g) for g in getattr(a.abstractor_generators, "abstractor_generator", [])]


def getAbstractorAbstractorInterfaceIDs(abstractorID: str) -> list[str]:
    """Return handles of the exactly two abstractorInterface elements.

    Section: F.7.4.2.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if a.abstractor_interfaces is None:
        return []
    return [get_handle(i) for i in getattr(a.abstractor_interfaces, "abstractor_interface", [])]


def getAbstractorAbstractorMode(abstractorID: str) -> tuple[str | None, str | None]:
    """Return (modeValue, group) for the abstractorMode element.

    Section: F.7.4.3. Returns (None, None) if not present.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    am = a.abstractor_mode
    if am is None:
        return (None, None)
    val = getattr(am, "value", None)
    mode_val = getattr(val, "value", None) if val is not None else None
    return (mode_val, getattr(am, "group", None))


def getAbstractorAbstractorModeID(abstractorID: str) -> str | None:
    """Return handle of the ``abstractorMode`` element.

    Section: F.7.4.4. Returns None if absent.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    am = a.abstractor_mode
    return None if am is None else get_handle(am)


def getAbstractorBusTypeRefByVLNV(abstractorID: str) -> tuple[str | None, str | None, str | None, str | None]:
    """Return busType VLNV reference.

    Section: F.7.4.5.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    bt = a.bus_type
    if bt is None:
        return (None, None, None, None)
    return (bt.vendor, bt.library, bt.name, bt.version)


def getAbstractorChoiceIDs(abstractorID: str) -> list[str]:
    """Return handles of ``choice`` children.

    Section: F.7.4.6.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if a.choices is None:
        return []
    return [get_handle(c) for c in getattr(a.choices, "choice", [])]


def getAbstractorComponentInstantiationIDs(abstractorID: str) -> list[str]:
    """Return handles of componentInstantiation elements in model.instantiations.

    Section: F.7.4.7.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    model = a.model
    if model is None or model.instantiations is None:
        return []
    return [get_handle(ci) for ci in getattr(model.instantiations, "component_instantiation", [])]


def getAbstractorFileSetIDs(abstractorID: str) -> list[str]:
    """Return handles of fileSet children.

    Section: F.7.4.8.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if a.file_sets is None:
        return []
    return [get_handle(fs) for fs in getattr(a.file_sets, "file_set", [])]


def getAbstractorInterfaceAbstractionTypeIDs(abstractorInterfaceID: str) -> list[str]:
    """List abstraction types on the supplied interface (F.7.4.9)."""
    interface = resolve_handle(abstractorInterfaceID)
    if not isinstance(interface, AbstractorBusInterfaceType):
        raise TgiError("Invalid abstractor interface handle", TgiFaultCode.INVALID_ID)
    if interface.abstraction_types is None:
        return []
    return [get_handle(item) for item in interface.abstraction_types.abstraction_type]


def getAbstractorPortIDs(abstractorID: str) -> list[str]:
    """Return handles of all abstractor model ports.

    Section: F.7.4.10.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    model = a.model
    if model is None or model.ports is None:
        return []
    return [get_handle(p) for p in getattr(model.ports, "port", [])]


def getAbstractorViewIDs(abstractorID: str) -> list[str]:
    """Return handles of view elements in model.views.

    Section: F.7.4.11.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    model = a.model
    if model is None or model.views is None:
        return []
    return [get_handle(v) for v in getattr(model.views, "view", [])]


# ---------------------------------------------------------------------------
# EXTENDED (F.7.5) – creation, removal, set operations
# ---------------------------------------------------------------------------

def addAbstractorAbstractorGenerator(abstractorID: str, name: str, generatorExecutable: str) -> str:
    """Create and append an ``abstractorGenerator``.

    Section: F.7.5.1.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if not isinstance(name, str) or not name.strip():
        raise TgiError("Generator name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if not isinstance(generatorExecutable, str) or not generatorExecutable.strip():
        raise TgiError("Generator executable requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    gen = AbstractorGenerator(name=name, generator_exe=IpxactUri(value=generatorExecutable))
    if a.abstractor_generators is None:
        a.abstractor_generators = AbstractorGenerators()
    a.abstractor_generators.abstractor_generator.append(gen)
    register_parent(gen, a, ("abstractor_generators", "abstractor_generator"), "list")
    return get_handle(gen)


def addAbstractorChoice(abstractorID: str, name: str, enumerations: Sequence[str]) -> str:
    """Add a named choice with its enumeration expressions (F.7.5.2).

    Invalid inputs leave the choices collection unchanged.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if not isinstance(name, str) or not name.strip():
        raise TgiError("Choice name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if isinstance(enumerations, (str, bytes)) or not isinstance(enumerations, Sequence):
        raise TgiError("Enumerations require a sequence of strings", TgiFaultCode.INVALID_ARGUMENT)
    values = list(enumerations)
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise TgiError("Enumerations require nonempty expressions", TgiFaultCode.INVALID_ARGUMENT)
    ch = Choices.Choice(name=name, enumeration=[Choices.Choice.Enumeration(value=value) for value in values])
    if a.choices is None:
        a.choices = Choices()
    a.choices.choice.append(ch)
    register_parent(ch, a, ("choices", "choice"), "list")
    for enumeration in ch.enumeration:
        register_parent(enumeration, ch, ("enumeration",), "list")
    return get_handle(ch)


def addAbstractorComponentInstantiation(abstractorID: str, name: str) -> str:
    """Add a ``componentInstantiation`` under model.instantiations.

    Section: F.7.5.3.
    """
    from org.accellera.ipxact.v1685_2022.component_instantiation_type import (
        ComponentInstantiationType,
    )
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if not isinstance(name, str) or not name.strip():
        raise TgiError("Instantiation name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if a.model is None:
        from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
        a.model = AbstractorModelType()
    if a.model.instantiations is None:
        from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
        a.model.instantiations = AbstractorModelType.Instantiations()
    ci = ComponentInstantiationType(name=name)
    a.model.instantiations.component_instantiation.append(ci)  # type: ignore[attr-defined]
    register_parent(ci, a, ("model", "instantiations", "component_instantiation"), "list")
    return get_handle(ci)


def addAbstractorFileSet(abstractorID: str, name: str) -> str:
    """Add a new ``fileSet`` under the abstractor.

    Section: F.7.5.4.
    """
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if not isinstance(name, str) or not name.strip():
        raise TgiError("File set name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if a.file_sets is None:
        a.file_sets = FileSets()
    fs = FileSet(name=name)
    a.file_sets.file_set.append(fs)  # type: ignore[attr-defined]
    register_parent(fs, a, ("file_sets", "file_set"), "list")
    return get_handle(fs)


def addAbstractorInterfaceAbstractionType(
    abstractorBusInterfaceID: str, abstractionRef: tuple[str, str, str, str],
) -> str:
    """Add a validated abstraction reference to an interface (F.7.5.5)."""
    from .core import vlnv_to_tuple

    interface = resolve_handle(abstractorBusInterfaceID)
    if not isinstance(interface, AbstractorBusInterfaceType):
        raise TgiError("Invalid abstractor interface handle", TgiFaultCode.INVALID_ID)
    parts = vlnv_to_tuple(abstractionRef)
    if not all(isinstance(part, str) and part.strip() for part in parts):
        raise TgiError("Abstraction VLNV requires four nonempty strings", TgiFaultCode.INVALID_ARGUMENT)
    item = AbstractionTypes.AbstractionType(abstraction_ref=ConfigurableLibraryRefType(
        vendor=parts[0], library=parts[1], name=parts[2], version=parts[3],
    ))
    if interface.abstraction_types is None:
        interface.abstraction_types = AbstractionTypes()
    interface.abstraction_types.abstraction_type.append(item)
    register_parent(item, interface, ("abstraction_types", "abstraction_type"), "list")
    return get_handle(item)


def _append_model_port(abstractorID: str, name: str, style) -> str:
    """Append a generated port after validating its name and owner."""
    from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType

    root = _resolve(abstractorID)
    if root is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if not isinstance(name, str) or not name.strip():
        raise TgiError("Port name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    port = AbstractorPortType(name=name, wire_or_transactional_or_structured=style)
    if root.model is None:
        root.model = AbstractorModelType()
    if root.model.ports is None:
        root.model.ports = AbstractorModelType.Ports()
    root.model.ports.port.append(port)
    register_parent(port, root, ("model", "ports", "port"), "list")
    return get_handle(port)


def addAbstractorTransactionalPort(abstractorID: str, name: str, initiative: str) -> str:
    """Add a transactional port with a standard initiative (F.7.5.9)."""
    from org.accellera.ipxact.v1685_2022 import AbstractorPortTransactionalType, Initiative, InitiativeType

    if _resolve(abstractorID) is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    try:
        value = InitiativeType(initiative)
    except (TypeError, ValueError):
        raise TgiError("Invalid port initiative", TgiFaultCode.INVALID_ARGUMENT) from None
    return _append_model_port(abstractorID, name, AbstractorPortTransactionalType(initiative=Initiative(value=value)))


def addAbstractorWirePort(abstractorID: str, name: str, direction: str) -> str:
    """Add a wire port with a standard direction (F.7.5.11)."""
    from org.accellera.ipxact.v1685_2022 import AbstractorPortWireType, ComponentPortDirectionType

    if _resolve(abstractorID) is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    try:
        value = ComponentPortDirectionType(direction)
    except (TypeError, ValueError):
        raise TgiError("Invalid port direction", TgiFaultCode.INVALID_ARGUMENT) from None
    return _append_model_port(abstractorID, name, AbstractorPortWireType(direction=value))


def addAbstractorStructuredInterfacePort(
    abstractorID: str,
    name: str,
    subPortName: str,
    structPortTypeDefTypeName: str,
) -> str:
    """Add a structured interface port (adds a subPort reference).

    Section: F.7.5.8.
    """
    from org.accellera.ipxact.v1685_2022.abstractor_sub_port_type import (
        AbstractorPortStructuredType,
        AbstractorSubPortType,
    )
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if a.model is None:
        from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
        a.model = AbstractorModelType()
    if a.model.ports is None:
        from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
        a.model.ports = AbstractorModelType.Ports()
    p = AbstractorPortType(name=name)
    p.structured = AbstractorPortStructuredType()
    sp = AbstractorSubPortType(name=subPortName)
    p.structured.interface_port.append(sp)  # type: ignore[attr-defined]
    a.model.ports.port.append(p)  # type: ignore[attr-defined]
    register_parent(p, a, ("model", "ports"), "list")
    return get_handle(p)


def addAbstractorStructuredStructPort(
    abstractorID: str,
    name: str,
    subPortName: str,
    structPortTypeDefTypeName: str,
    direction: str | None = None,
) -> str:
    """Add a structured structPort with direction.

    Section: F.7.5.9.
    """
    from org.accellera.ipxact.v1685_2022.abstractor_sub_port_type import (
        AbstractorPortStructuredType,
        AbstractorSubPortType,
    )
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if a.model is None:
        from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
        a.model = AbstractorModelType()
    if a.model.ports is None:
        from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
        a.model.ports = AbstractorModelType.Ports()
    p = AbstractorPortType(name=name)
    p.structured = AbstractorPortStructuredType()
    sp = AbstractorSubPortType(name=subPortName)
    if direction:
        sp.direction = direction  # type: ignore[attr-defined]
    p.structured.struct_port.append(sp)  # type: ignore[attr-defined]
    a.model.ports.port.append(p)  # type: ignore[attr-defined]
    register_parent(p, a, ("model", "ports"), "list")
    return get_handle(p)


def addAbstractorStructuredUnionPort(
    abstractorID: str,
    name: str,
    structPortTypeDefTypeName: str,
    subPortName: str,
    direction: str | None = None,
) -> str:
    """Add a structured unionPort with direction.

    Section: F.7.5.10.
    """
    from org.accellera.ipxact.v1685_2022.abstractor_sub_port_type import (
        AbstractorPortStructuredType,
        AbstractorSubPortType,
    )
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if a.model is None:
        from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
        a.model = AbstractorModelType()
    if a.model.ports is None:
        from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
        a.model.ports = AbstractorModelType.Ports()
    p = AbstractorPortType(name=name)
    p.structured = AbstractorPortStructuredType()
    sp = AbstractorSubPortType(name=subPortName)
    if direction:
        sp.direction = direction  # type: ignore[attr-defined]
    p.structured.union_port.append(sp)  # type: ignore[attr-defined]
    a.model.ports.port.append(p)  # type: ignore[attr-defined]
    register_parent(p, a, ("model", "ports"), "list")
    return get_handle(p)


def addAbstractorView(abstractorID: str, name: str) -> str:
    """Add a view element under model.views.

    Section: F.7.5.10.
    """
    from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    if not isinstance(name, str) or not name.strip():
        raise TgiError("View name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if a.model is None:
        a.model = AbstractorModelType()
    if a.model.views is None:
        a.model.views = AbstractorModelType.Views()
    v = AbstractorModelType.Views.View(name=name)
    a.model.views.view.append(v)  # type: ignore[attr-defined]
    register_parent(v, a, ("model", "views", "view"), "list")
    return get_handle(v)


def removeAbstractorAbstractorGenerator(abstractorGeneratorID: str) -> bool:
    """Remove an abstractorGenerator.

    Section: F.7.5.12.
    """
    return detach_child_by_handle(abstractorGeneratorID)


def removeAbstractorChoice(choiceID: str) -> bool:
    """Remove a choice element.

    Section: F.7.5.14.
    """
    return detach_child_by_handle(choiceID)


def removeAbstractorComponentInstantiation(componentInstantiationID: str) -> bool:
    """Remove a componentInstantiation.

    Section: F.7.5.15.
    """
    return detach_child_by_handle(componentInstantiationID)


def removeAbstractorFileSet(fileSetID: str) -> bool:
    """Remove a fileSet element.

    Section: F.7.5.16.
    """
    return detach_child_by_handle(fileSetID)


def removeAbstractorInterfaceAbstractionType(abstractionTypeID: str) -> bool:
    """Remove an abstractionType from an abstractorInterface.

    Section: F.7.5.17.
    """
    return detach_child_by_handle(abstractionTypeID)


def removeAbstractorPort(portID: str) -> bool:
    """Remove a model port (any style).

    Section: F.7.5.18.
    """
    return detach_child_by_handle(portID)


def removeAbstractorView(viewID: str) -> bool:
    """Remove a model view.

    Section: F.7.5.19.
    """
    return detach_child_by_handle(viewID)


def setAbstractorAbstractorMode(abstractorID: str, modeValue: str, group: str | None = None) -> bool:
    """Set the standard mode while preserving its handle (F.7.5.21).

    The optional group argument is a convenience for system-mode completion.
    Omitting it preserves any existing group. Invalid inputs do not mutate the model.
    """
    from org.accellera.ipxact.v1685_2022.abstractor_mode_type import AbstractorModeType

    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    try:
        mode = AbstractorModeType(modeValue)
    except (ValueError, TypeError):
        raise TgiError("Invalid abstractor mode", TgiFaultCode.INVALID_ARGUMENT) from None
    if group is not None and (not isinstance(group, str) or not group.strip()):
        raise TgiError("System group requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if a.abstractor_mode is None:
        a.abstractor_mode = AbstractorType.AbstractorMode(value=mode, group=group)
    else:
        a.abstractor_mode.value = mode
        if group is not None:
            a.abstractor_mode.group = group
    register_parent(a.abstractor_mode, a, ("abstractor_mode",), "scalar")
    return True


def setAbstractorBusType(abstractorID: str, vlnv: tuple[str, str, str, str]) -> bool:
    """Set a validated bus VLNV reference (F.7.5.22).

    Reference resolution is deferred; invalid VLNVs leave the existing reference intact.
    """
    from .core import vlnv_to_tuple

    a = _resolve(abstractorID)
    if a is None:
        raise TgiError("Invalid abstractor handle", TgiFaultCode.INVALID_ID)
    parts = vlnv_to_tuple(vlnv)
    if not all(isinstance(part, str) and part.strip() for part in parts):
        raise TgiError("Bus VLNV requires four nonempty strings", TgiFaultCode.INVALID_ARGUMENT)
    a.bus_type = LibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])
    register_parent(a.bus_type, a, ("bus_type",), "scalar")
    return True
