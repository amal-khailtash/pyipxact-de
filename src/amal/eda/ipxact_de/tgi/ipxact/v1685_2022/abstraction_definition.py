# ruff: noqa: I001
"""Abstraction definition category TGI functions.

Provides traversal of ports, parameters, choices and basic metadata getters
for :class:`AbstractionDefinition` objects.
"""
from collections.abc import Sequence

from .core import TgiError, TgiFaultCode, get_handle, resolve_handle, register_parent, detach_child_by_handle
from org.accellera.ipxact.v1685_2022.wire import Wire
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition, Choices

__all__ = [
    # BASE (F.7.2)
    "getAbstractionDefBusTypeRefByVLNV",
    "getAbstractionDefChoiceIDs",
    "getAbstractionDefExtendsRefByVLNV",
    "getAbstractionDefPortIDs",
    "getAbstractionDefPortLogicalName",
    "getAbstractionDefPortMatch",
    "getAbstractionDefPortOnSystemIDs",
    "getAbstractionDefPortPacketIDs",
    "getAbstractionDefPortStyle",
    "getAbstractionDefPortTransactionalModeBusWidth",
    "getAbstractionDefPortTransactionalModeBusWidthExpression",
    "getAbstractionDefPortTransactionalModeBusWidthID",
    "getAbstractionDefPortTransactionalModeInitiative",
    "getAbstractionDefPortTransactionalModeKindID",
    "getAbstractionDefPortTransactionalModePresence",
    "getAbstractionDefPortTransactionalModeProtocolID",
    "getAbstractionDefPortTransactionalOnInitiatorID",
    "getAbstractionDefPortTransactionalOnSystemIDs",
    "getAbstractionDefPortTransactionalOnTargetID",
    "getAbstractionDefPortTransactionalQualifierID",
    "getAbstractionDefPortWireDefaultValue",
    "getAbstractionDefPortWireDefaultValueExpression",
    "getAbstractionDefPortWireDefaultValueID",
    "getAbstractionDefPortWireModeDirection",
    "getAbstractionDefPortWireModeMirroredModeConstraintsID",
    "getAbstractionDefPortWireModeModeConstraintsID",
    "getAbstractionDefPortWireModePresence",
    "getAbstractionDefPortWireModeWidth",
    "getAbstractionDefPortWireModeWidthExpression",
    "getAbstractionDefPortWireModeWidthID",
    "getAbstractionDefPortWireOnInitiatorID",
    "getAbstractionDefPortWireOnSystemIDs",
    "getAbstractionDefPortWireOnTargetID",
    "getAbstractionDefPortWireQualifierID",
    "getAbstractionDefPortWireRequiresDriver",
    "getAbstractionDefPortWireRequiresDriverID",
    "getModeConstraintsDriveConstraintCellSpecificationID",
    "getModeConstraintsLoadConstraintID",
    "getModeConstraintsTimingConstraintIDs",
    "getOnSystemGroup",
    "getPacketEndianness",
    "getPacketFieldEndianness",
    "getPacketFieldQualifierID",
    "getPacketFieldValue",
    "getPacketFieldValueExpression",
    "getPacketFieldValueID",
    "getPacketFieldWidth",
    "getPacketFieldWidthExpression",
    "getPacketFieldWidthID",
    "getPacketPacketFieldIDs",
    # EXTENDED (F.7.3)
    "addAbstractionDefChoice",
    "addAbstractionDefPort",
    "addAbstractionDefPortMode",
    "addAbstractionDefPortPacket",
    "addAbstractionDefPortTransactionalOnSystem",
    "addAbstractionDefPortWireOnSystem",
    "removeAbstractionDefChoice",
    "removeAbstractionDefPort",
    "removeAbstractionDefPortMode",
    "removeAbstractionDefPortTransactionalOnSystem",
    "removeAbstractionDefPortWireOnSystem",
    "setAbstractionDefExtends",
    "removeAbstractionDefPortTransactionalModeBusWidth",
    "removeAbstractionDefPortTransactionalModeInitiative",
    "removeAbstractionDefPortTransactionalModeKind",
    "removeAbstractionDefPortTransactionalModePresence",
    "removeAbstractionDefPortTransactionalModeProtocol",
    "removeAbstractionDefPortTransactionalOnInitiator",
    "removeAbstractionDefPortTransactionalOnTarget",
    "removeAbstractionDefPortTransactionalQualifier",
    "removeAbstractionDefPortWireModeDirection",
    "removeAbstractionDefPortWireModeMirroredModeConstraints",
    "removeAbstractionDefPortWireModeModeConstraints",
    "removeAbstractionDefPortWireModePresence",
    "removeAbstractionDefPortWireModeWidth",
    "removeAbstractionDefPortWireOnInitiator",
    "removeAbstractionDefPortWireOnTarget",
    "removeAbstractionDefPortWireQualifier",
    "removeAbstractionDefPortWireRequiresDriver",
    "setAbstractionDefPortTransactionalModeBusWidth",
    "setAbstractionDefPortTransactionalModeInitiative",
    "setAbstractionDefPortTransactionalModeKind",
    "setAbstractionDefPortTransactionalModePresence",
    "setAbstractionDefPortTransactionalModeProtocol",
    "setAbstractionDefPortTransactionalOnInitiator",
    "setAbstractionDefPortTransactionalOnTarget",
    "setAbstractionDefPortTransactionalQualifier",
    "setAbstractionDefPortTransactional",
    "setAbstractionDefPortWire",
    "setAbstractionDefPortWireDefaultValue",
    "setAbstractionDefPortWireModeDirection",
    "setAbstractionDefPortWireModeMirroredModeConstraints",
    "setAbstractionDefPortWireModeModeConstraints",
    "setAbstractionDefPortWireModePresence",
    "setAbstractionDefPortWireModeWidth",
    "setAbstractionDefPortWireOnInitiator",
    "setAbstractionDefPortWireOnTarget",
    "setAbstractionDefPortWireQualifier",
    "setAbstractionDefPortWireRequiresDriver",
]


def _resolve(abstractionDefinitionID: str) -> AbstractionDefinition | None:
    """Resolve a handle to an :class:`AbstractionDefinition` object.

    Helper (non-spec) used internally by TGI functions.

    Args:
        abstractionDefinitionID: Handle that should reference an abstractionDefinition.

    Returns:
        The resolved :class:`AbstractionDefinition` instance or ``None`` if the
        handle does not reference the expected type.
    """
    obj = resolve_handle(abstractionDefinitionID)
    return obj if isinstance(obj, AbstractionDefinition) else None


def _resolve_port(portID: str) -> AbstractionDefinition.Ports.Port | None:
    """Resolve a handle to an abstraction definition port element.

    Helper (non-spec) used internally.

    Args:
        portID: Handle referencing a logical port inside an abstractionDefinition.

    Returns:
        Port object or ``None`` if the handle is invalid or another type.
    """
    obj = resolve_handle(portID)
    if isinstance(obj, AbstractionDefinition.Ports.Port):  # type: ignore[attr-defined]
        return obj
    return None


def _ensure_transactional(portID: str):
    """Resolve and return the transactional sub-element for a port.

    Section: Annex F helper (not a spec TGI function).

    Args:
        portID: Handle of a transactional abstractionDefPort.

    Returns:
        The transactional object referenced by the port.

    Raises:
        TgiError: If the handle is invalid or the port is not transactional.
    """
    p = _resolve_port(portID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    if p.transactional is None:
        raise TgiError("Port not transactional", TgiFaultCode.INVALID_ARGUMENT)
    return p.transactional


def _resolve_packet(packetID: str):  # type: ignore[return-type]
    """Resolve a handle to a packet element.

    Helper (non-spec) used internally by packet-related TGI functions.

    Args:
        packetID: Handle referencing a ``packet`` element of a packet style port.

    Returns:
        Resolved packet object or ``None`` if the handle does not reference a
        packet element.
    """
    obj = resolve_handle(packetID)
    from org.accellera.ipxact.v1685_2022.port_packet_type import PortPacketType
    return obj if isinstance(obj, PortPacketType) else None


def _resolve_packet_field(packetFieldID: str):  # type: ignore[return-type]
    """Resolve a handle to a packetField element.

    Helper (non-spec) used internally by packet-related TGI functions.

    Args:
        packetFieldID: Handle referencing a ``packetField`` element.

    Returns:
        Resolved packetField object or ``None`` if the handle is invalid or
        references another type.
    """
    obj = resolve_handle(packetFieldID)
    from org.accellera.ipxact.v1685_2022.port_packet_field_type import PortPacketFieldType
    return obj if isinstance(obj, PortPacketFieldType) else None

# ---------------------------------------------------------------------------
# BASE
# ---------------------------------------------------------------------------


def getAbstractionDefBusTypeRefByVLNV(
    abstractionDefinitionID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return busType VLNV tuple.

    Section: F.7.2.1.

    Args:
        abstractionDefinitionID: Handle to an abstractionDefinition (or instance) element.

    Returns:
        Tuple ``(vendor, library, name, version)`` with each item possibly ``None``
        if the busType reference is absent.
    """
    ad = _resolve(abstractionDefinitionID)
    if ad is None:
        raise TgiError("Invalid abstraction definition handle", TgiFaultCode.INVALID_ID)
    bt = ad.bus_type
    if bt is None:
        return (None, None, None, None)
    return (bt.vendor, bt.library, bt.name, bt.version)


def getAbstractionDefChoiceIDs(abstractionDefinitionID: str) -> list[str]:
    """Return handles of all ``choice`` children.

    Section: F.7.2.2.

    Args:
        abstractionDefinitionID: Handle to an abstractionDefinition element.

    Returns:
        List of choice element handles (empty if none defined).
    """
    ad = _resolve(abstractionDefinitionID)
    if ad is None:
        raise TgiError("Invalid abstraction definition handle", TgiFaultCode.INVALID_ID)
    if ad.choices is None:
        return []
    for choice in ad.choices.choice:
        register_parent(choice, ad, ("choices", "choice"), "list")
    return [get_handle(choice) for choice in ad.choices.choice]


def getAbstractionDefExtendsRefByVLNV(
    abstractionDefinitionID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return the extends VLNV tuple.

    Section: F.7.2.3.

    Args:
        abstractionDefinitionID: Handle to an abstractionDefinition element.

    Returns:
        Tuple ``(vendor, library, name, version)`` or all ``None`` if no extends present.
    """
    ad = _resolve(abstractionDefinitionID)
    if ad is None:
        raise TgiError("Invalid abstraction definition handle", TgiFaultCode.INVALID_ID)
    ext = ad.extends
    if ext is None:
        return (None, None, None, None)
    return (ext.vendor, ext.library, ext.name, ext.version)


def getAbstractionDefPortIDs(abstractionDefinitionID: str) -> list[str]:
    """Return handles of all logical ports.

    Section: F.7.2.4.

    Args:
        abstractionDefinitionID: Handle to an abstractionDefinition element.

    Returns:
        List of port handles (empty if no ports defined).
    """
    ad = _resolve(abstractionDefinitionID)
    if ad is None:
        raise TgiError("Invalid abstraction definition handle", TgiFaultCode.INVALID_ID)
    if ad.ports is None:
        return []
    for port in ad.ports.port:
        register_parent(port, ad, ("ports", "port"), "list")
    return [get_handle(port) for port in ad.ports.port]


def getAbstractionDefPortLogicalName(abstractionDefPortID: str) -> str | None:
    """Return the logicalName of a port.

    Section: F.7.2.5.

    Args:
        abstractionDefPortID: Handle to an abstractionDefPort element.

    Returns:
        Logical name string or ``None`` if not present.
    """
    p = _resolve_port(abstractionDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    return p.logical_name


def getAbstractionDefPortMatch(abstractionDefPortID: str) -> bool | None:
    """Return the match flag of a port.

    Section: F.7.2.6.

    Args:
        abstractionDefPortID: Handle to an abstractionDefPort element.

    Returns:
        Boolean value or ``None`` if the element is absent.
    """
    p = _resolve_port(abstractionDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    return p.match


def getAbstractionDefPortOnSystemIDs(abstractionDefPortID: str) -> list[str]:
    """Return all system modes in document order for either style (F.7.2.7)."""
    port = _resolve_port(abstractionDefPortID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    style = port.wire_or_transactional
    if not isinstance(style, (Wire, AbstractionDefinition.Ports.Port.Transactional)):
        return []
    for mode in style.on_system:
        register_parent(mode, style, ("on_system",), "list")
    return [get_handle(mode) for mode in style.on_system]


def getAbstractionDefPortPacketIDs(abstractionDefPortID: str) -> list[str]:
    """Return handles of packet elements under the port.

    Section: F.7.2.8.

    Args:
        abstractionDefPortID: Handle to an abstractionDefPort element.

    Returns:
        List of packet handles in document order (empty if none).
    """
    p = _resolve_port(abstractionDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    pkts = p.packets
    if pkts is None:
        return []
    for packet in pkts.packet:
        register_parent(packet, pkts, ("packet",), "list")
    return [get_handle(packet) for packet in pkts.packet]


def getAbstractionDefPortStyle(abstractionDefPortModeID: str) -> str | None:
    """Return the style of a port (wire, transactional, packet).

    Section: F.7.2.9.

    Args:
        abstractionDefPortModeID: Handle to an abstractionDefPort element.

    Returns:
        Style string or ``None`` if style cannot be determined.
    """
    p = _resolve_port(abstractionDefPortModeID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    if isinstance(p.wire_or_transactional, AbstractionDefinition.Ports.Port.Transactional):
        return "transactional"
    if isinstance(p.wire_or_transactional, Wire):
        return "wire"
    if p.packets is not None:
        return "packet"
    return None


def getAbstractionDefPortTransactionalModeBusWidth(abstractionDefPortModeID: str) -> int | None:
    """Return transactional busWidth resolved value.

    Section: F.7.2.10.

    Args:
        abstractionDefPortModeID: Handle to a transactional abstractionDefPort element.

    Returns:
        Integer width or ``None`` if not specified / not transactional.
    """
    p = _resolve_port(abstractionDefPortModeID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    tr = getattr(p, "transactional", None)
    if tr is None:
        return None
    # On initiator/on target do not carry busWidth; onSystem entries may.
    for os in getattr(tr, "on_system", []):
        bw = getattr(os, "bus_width", None)
        if bw is not None and getattr(bw, "value", None) is not None:
            try:
                return int(bw.value)  # type: ignore[arg-type]
            except Exception:  # pragma: no cover
                return None
    return None


def getAbstractionDefPortTransactionalModeBusWidthExpression(abstractionDefPortModeID: str) -> str | None:
    """Return the supplied transactional mode's bus width expression (F.7.2.11)."""
    tr = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (tr.OnInitiator, tr.OnTarget, tr.OnSystem)):
        raise TgiError("Invalid transactional logical port mode handle", TgiFaultCode.INVALID_ID)
    child = mode.bus_width
    if child is None:
        return None
    return child.value


def getAbstractionDefPortTransactionalModeBusWidthID(abstractionDefPortModeID: str) -> str | None:
    """Return the supplied transactional mode's bus width handle (F.7.2.12)."""
    tr = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (tr.OnInitiator, tr.OnTarget, tr.OnSystem)):
        raise TgiError("Invalid transactional logical port mode handle", TgiFaultCode.INVALID_ID)
    child = mode.bus_width
    if child is None:
        return None
    register_parent(child, mode, ("bus_width",), "single")
    return get_handle(child)


def getAbstractionDefPortTransactionalModeInitiative(abstractionDefPortModeID: str) -> str | None:
    """Return the supplied transactional mode's initiative value (F.7.2.13)."""
    tr = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (tr.OnInitiator, tr.OnTarget, tr.OnSystem)):
        raise TgiError("Invalid transactional logical port mode handle", TgiFaultCode.INVALID_ID)
    child = mode.initiative
    if child is None:
        return None
    return child.value


def getAbstractionDefPortTransactionalModeKindID(abstractionDefPortModeID: str) -> str | None:
    """Return the supplied transactional mode's kind handle (F.7.2.14)."""
    tr = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (tr.OnInitiator, tr.OnTarget, tr.OnSystem)):
        raise TgiError("Invalid transactional logical port mode handle", TgiFaultCode.INVALID_ID)
    child = mode.kind
    if child is None:
        return None
    register_parent(child, mode, ("kind",), "single")
    return get_handle(child)


def getAbstractionDefPortTransactionalModePresence(abstractionDefPortModeID: str) -> str | None:
    """Return the supplied transactional mode's presence value (F.7.2.15)."""
    tr = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (tr.OnInitiator, tr.OnTarget, tr.OnSystem)):
        raise TgiError("Invalid transactional logical port mode handle", TgiFaultCode.INVALID_ID)
    child = mode.presence
    if child is None:
        return None
    return child.value.value


def getAbstractionDefPortTransactionalModeProtocolID(abstractionDefPortModeID: str) -> str | None:
    """Return the supplied transactional mode's protocol handle (F.7.2.16)."""
    tr = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (tr.OnInitiator, tr.OnTarget, tr.OnSystem)):
        raise TgiError("Invalid transactional logical port mode handle", TgiFaultCode.INVALID_ID)
    child = mode.protocol
    if child is None:
        return None
    register_parent(child, mode, ("protocol",), "single")
    return get_handle(child)


def getAbstractionDefPortTransactionalOnInitiatorID(abstractionDefPortID: str) -> str | None:
    """Return transactional onInitiator handle.

    Section: F.7.2.17.

    Args:
        abstractionDefPortID: Handle to a transactional port element.

    Returns:
        Handle string or ``None`` if absent.
    """
    p = _resolve_port(abstractionDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    tr = p.wire_or_transactional
    if not isinstance(tr, AbstractionDefinition.Ports.Port.Transactional):
        return None
    if tr is None or tr.on_initiator is None:
        return None
    register_parent(tr.on_initiator, tr, ("on_initiator",), "single")
    return get_handle(tr.on_initiator)


def getAbstractionDefPortTransactionalOnSystemIDs(abstractionDefPortID: str) -> list[str]:
    """Return transactional onSystem handles.

    Section: F.7.2.18.

    Args:
        abstractionDefPortID: Handle to a transactional port element.

    Returns:
        List of handles (may be empty).
    """
    port = _resolve_port(abstractionDefPortID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    style = port.wire_or_transactional
    if not isinstance(style, AbstractionDefinition.Ports.Port.Transactional):
        return []
    for mode in style.on_system:
        register_parent(mode, style, ("on_system",), "list")
    return [get_handle(mode) for mode in style.on_system]


def getAbstractionDefPortTransactionalOnTargetID(abstractionDefPortID: str) -> str | None:
    """Return transactional onTarget handle.

    Section: F.7.2.19.

    Args:
        abstractionDefPortID: Handle to a transactional port element.

    Returns:
        Handle string or ``None``.
    """
    p = _resolve_port(abstractionDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    tr = p.wire_or_transactional
    if not isinstance(tr, AbstractionDefinition.Ports.Port.Transactional):
        return None
    if tr is None or tr.on_target is None:
        return None
    register_parent(tr.on_target, tr, ("on_target",), "single")
    return get_handle(tr.on_target)


def getAbstractionDefPortTransactionalQualifierID(portID: str) -> str | None:
    """Return the owned transactional qualifier handle (F.7.2.20)."""
    port = _resolve_port(portID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    style = port.wire_or_transactional
    if not isinstance(style, AbstractionDefinition.Ports.Port.Transactional) or style.qualifier is None:
        return None
    register_parent(style.qualifier, style, ("qualifier",), "single")
    return get_handle(style.qualifier)


def getAbstractionDefPortWireDefaultValue(abstractionDefPortID: str) -> int | None:
    """Return wire defaultValue numeric value.

    Section: F.7.2.21.

    Args:
        abstractionDefPortID: Handle to a wire port element.

    Returns:
        Integer value or ``None`` if not present / not wire.
    """
    p = _resolve_port(abstractionDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    w = getattr(p, "wire", None)
    dv = getattr(w, "default_value", None) if w is not None else None
    if dv is None:
        return None
    try:
        return int(getattr(dv, "value", None))  # type: ignore[arg-type]
    except Exception:  # pragma: no cover
        return None


def getAbstractionDefPortWireDefaultValueExpression(abstractionDefPortID: str) -> str | None:
    """Return a wire port's default-value expression text (F.7.2.22)."""
    port = _resolve_port(abstractionDefPortID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    wire = port.wire_or_transactional
    if not isinstance(wire, Wire):
        return None
    from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import (
        UnsignedBitVectorExpression,
    )

    default_value = wire.default_value_or_requires_driver
    return default_value.value if isinstance(default_value, UnsignedBitVectorExpression) else None


def getAbstractionDefPortWireDefaultValueID(abstractionDefPortModeID: str) -> str | None:
    """Return the owned wire default-value handle when that choice is present (F.7.2.23)."""
    port = _resolve_port(abstractionDefPortModeID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    wire = port.wire_or_transactional
    if not isinstance(wire, Wire):
        return None
    from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import (
        UnsignedBitVectorExpression,
    )

    default_value = wire.default_value_or_requires_driver
    if not isinstance(default_value, UnsignedBitVectorExpression):
        return None
    register_parent(default_value, wire, ("default_value_or_requires_driver",), "single")
    return get_handle(default_value)


def getAbstractionDefPortWireModeDirection(abstractionDefPortModeID: str) -> str | None:
    """Return the direction restriction on a wire mode element (F.7.2.24)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        raise TgiError("Invalid wire mode handle", TgiFaultCode.INVALID_ID)
    direction = mode.direction
    return direction.value if direction is not None else None


def getAbstractionDefPortWireModeMirroredModeConstraintsID(abstractionDefPortModeID: str) -> str | None:
    """Return the mirrored-mode constraints child handle, if defined (F.7.2.25)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        raise TgiError("Invalid wire mode handle", TgiFaultCode.INVALID_ID)
    constraints = mode.mirrored_mode_constraints
    if constraints is None:
        return None
    register_parent(constraints, mode, ("mirrored_mode_constraints",), "single")
    return get_handle(constraints)


def getAbstractionDefPortWireModeModeConstraintsID(abstractionDefPortModeID: str) -> str | None:
    """Return the mode constraints child handle, if defined (F.7.2.26)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        raise TgiError("Invalid wire mode handle", TgiFaultCode.INVALID_ID)
    constraints = mode.mode_constraints
    if constraints is None:
        return None
    register_parent(constraints, mode, ("mode_constraints",), "single")
    return get_handle(constraints)


def getAbstractionDefPortWireModePresence(abstractionDefPortModeID: str) -> str | None:
    """Return the presence value on a wire mode element (F.7.2.27)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        raise TgiError("Invalid wire mode handle", TgiFaultCode.INVALID_ID)
    presence = mode.presence
    return presence.value.value if presence is not None else None


def getAbstractionDefPortWireModeWidth(abstractionDefPortModeID: str) -> int | None:
    """Return wire width numeric value.

    Section: F.7.2.28.

    Args:
        abstractionDefPortModeID: Handle to a wire port element.

    Returns:
        Integer width or ``None``.
    """
    p = _resolve_port(abstractionDefPortModeID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    w = getattr(p, "wire", None)
    width = getattr(w, "width", None) if w is not None else None
    if width is None:
        return None
    try:
        return int(getattr(width, "value", None))  # type: ignore[arg-type]
    except Exception:  # pragma: no cover
        return None


def getAbstractionDefPortWireModeWidthExpression(abstractionDefPortModeID: str) -> str | None:
    """Return the width expression text on a wire mode element (F.7.2.29)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        raise TgiError("Invalid wire mode handle", TgiFaultCode.INVALID_ID)
    width = mode.width
    return width.value if width is not None else None


def getAbstractionDefPortWireModeWidthID(abstractionDefPortModeID: str) -> str | None:
    """Return the supplied wire mode's owned width handle (F.7.2.30)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        raise TgiError("Invalid wire logical port mode handle", TgiFaultCode.INVALID_ID)
    child = mode.width
    if child is None:
        return None
    register_parent(child, mode, ("width",), "single")
    return get_handle(child)


def getAbstractionDefPortWireOnInitiatorID(abstractionDefPortID: str) -> str | None:
    """F.7.2.31 Return handle to the wire onInitiator element.

    Args:
        abstractionDefPortID: Handle to a logical wire port element.

    Returns:
        Handle to the onInitiator element or None if absent / not wire style.
    """
    p = _resolve_port(abstractionDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    w = p.wire_or_transactional
    if not isinstance(w, Wire):
        return None
    if w is None or getattr(w, "on_initiator", None) is None:
        return None
    register_parent(w.on_initiator, w, ("on_initiator",), "single")
    return get_handle(w.on_initiator)


def getAbstractionDefPortWireOnSystemIDs(portID: str) -> list[str]:
    """F.7.2.32 Return handles to all wire onSystem elements.

    Args:
        portID: Handle to a logical wire port element.

    Returns:
        List of onSystem element handles (may be empty).
    """
    p = _resolve_port(portID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    w = p.wire_or_transactional
    if not isinstance(w, Wire):
        return []
    if w is None:
        return []
    for mode in w.on_system:
        register_parent(mode, w, ("on_system",), "list")
    return [get_handle(mode) for mode in w.on_system]


def getAbstractionDefPortWireOnTargetID(abstractionDefPortID: str) -> str | None:
    """F.7.2.33 Return handle to the wire onTarget element.

    Args:
        abstractionDefPortID: Handle to a logical wire port element.

    Returns:
        Handle to onTarget element or None if absent / not wire style.
    """
    p = _resolve_port(abstractionDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    w = p.wire_or_transactional
    if not isinstance(w, Wire):
        return None
    if w is None or getattr(w, "on_target", None) is None:
        return None
    register_parent(w.on_target, w, ("on_target",), "single")
    return get_handle(w.on_target)


def getAbstractionDefPortWireQualifierID(portID: str) -> str | None:
    """Return the owned wire qualifier handle (F.7.2.34)."""
    port = _resolve_port(portID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    style = port.wire_or_transactional
    if not isinstance(style, Wire) or style.qualifier is None:
        return None
    register_parent(style.qualifier, style, ("qualifier",), "single")
    return get_handle(style.qualifier)


def getAbstractionDefPortWireRequiresDriver(abstractionDefPortID: str) -> bool | None:
    """Return requiresDriver for a wire port, or None for another choice (F.7.2.35)."""
    port = _resolve_port(abstractionDefPortID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    wire = port.wire_or_transactional
    if not isinstance(wire, Wire):
        return None
    from org.accellera.ipxact.v1685_2022.requires_driver import RequiresDriver

    driver = wire.default_value_or_requires_driver
    return driver.value if isinstance(driver, RequiresDriver) else None


def getAbstractionDefPortWireRequiresDriverID(abstractionDefPortModeID: str) -> str | None:
    """Return the owned requiresDriver handle for a wire port (F.7.2.36)."""
    port = _resolve_port(abstractionDefPortModeID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    wire = port.wire_or_transactional
    if not isinstance(wire, Wire):
        return None
    from org.accellera.ipxact.v1685_2022.requires_driver import RequiresDriver

    driver = wire.default_value_or_requires_driver
    if not isinstance(driver, RequiresDriver):
        return None
    register_parent(driver, wire, ("default_value_or_requires_driver",), "single")
    return get_handle(driver)


def getModeConstraintsDriveConstraintCellSpecificationID(modeConstraintsID: str) -> str | None:
    """Return handle to driveConstraint/cellSpecification.

    Section: F.7.2.37.

    Args:
        modeConstraintsID: Handle to a modeConstraints element.

    Returns:
        Handle to first cellSpecification element or ``None``.
    """
    obj = resolve_handle(modeConstraintsID)
    from org.accellera.ipxact.v1685_2022.abstraction_def_port_constraints_type import (
        AbstractionDefPortConstraintsType,
    )
    if not isinstance(obj, AbstractionDefPortConstraintsType):  # type: ignore[arg-type]
        raise TgiError("Invalid modeConstraints handle", TgiFaultCode.INVALID_ID)
    for dc in getattr(obj, "drive_constraint", []):  # type: ignore[attr-defined]
        cs = getattr(dc, "cell_specification", None)
        if cs is not None:
            return get_handle(cs)
    return None


def getModeConstraintsLoadConstraintID(modeConstraintsID: str) -> str | None:
    """Return handle to loadConstraint.

    Section: F.7.2.38.

    Args:
        modeConstraintsID: Handle to a modeConstraints element.

    Returns:
        Handle string or ``None`` if absent.
    """
    obj = resolve_handle(modeConstraintsID)
    from org.accellera.ipxact.v1685_2022.abstraction_def_port_constraints_type import (
        AbstractionDefPortConstraintsType,
    )
    if not isinstance(obj, AbstractionDefPortConstraintsType):  # type: ignore[arg-type]
        raise TgiError("Invalid modeConstraints handle", TgiFaultCode.INVALID_ID)
    for lc in getattr(obj, "load_constraint", []):  # type: ignore[attr-defined]
        return get_handle(lc)
    return None


def getModeConstraintsTimingConstraintIDs(modeConstraintsID: str) -> list[str]:
    """Return timingConstraint handles.

    Section: F.7.2.39.

    Args:
        modeConstraintsID: Handle to a modeConstraints element.

    Returns:
        List of timingConstraint handles (possibly empty).
    """
    obj = resolve_handle(modeConstraintsID)
    from org.accellera.ipxact.v1685_2022.abstraction_def_port_constraints_type import (
        AbstractionDefPortConstraintsType,
    )
    if not isinstance(obj, AbstractionDefPortConstraintsType):  # type: ignore[arg-type]
        raise TgiError("Invalid modeConstraints handle", TgiFaultCode.INVALID_ID)
    return [get_handle(tc) for tc in getattr(obj, "timing_constraint", [])]  # type: ignore[attr-defined]


def getOnSystemGroup(onSystemID: str) -> str | None:
    """Return onSystem group attribute.

    Section: F.7.2.40.

    Args:
        onSystemID: Handle to an onSystem element (transactional or wire).

    Returns:
        Group name string or ``None``.
    """
    obj = _resolve_logical_system(onSystemID)
    if obj is None:
        raise TgiError("Invalid onSystem handle", TgiFaultCode.INVALID_ID)
    return obj.group


def getPacketEndianness(packetID: str) -> str | None:
    """Return explicitly defined packet endianness.

    Section: F.7.2.41.

    Args:
        packetID: Handle to a packet element.

    Returns:
        Endianness string (big/little) or ``None``.
    """
    pkt = _resolve_packet(packetID)
    if pkt is None:
        raise TgiError("Invalid packet handle", TgiFaultCode.INVALID_ID)
    end = getattr(pkt, "endianness", None)
    return getattr(end, "value", None) if end is not None else None


def getPacketFieldEndianness(packetFieldID: str) -> str | None:
    """Return explicitly defined packetField endianness.

    Section: F.7.2.42.

    Args:
        packetFieldID: Handle to a packetField element.

    Returns:
        Endianness string or ``None``.
    """
    pf = _resolve_packet_field(packetFieldID)
    if pf is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    end = getattr(pf, "endianness", None)
    return getattr(end, "value", None) if end is not None else None


def getPacketFieldQualifierID(packetFieldID: str) -> str | None:
    """Return handle of packetField qualifier.

    Section: F.7.2.43.

    Args:
        packetFieldID: Handle to a packetField element.

    Returns:
        Qualifier handle string or ``None``.
    """
    pf = _resolve_packet_field(packetFieldID)
    if pf is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    qual = getattr(pf, "qualifier", None)
    if qual is None:
        return None
    register_parent(qual, pf, ("qualifier",), "single")
    return get_handle(qual)


def getPacketFieldValue(packetFieldID: str) -> int | None:
    """Return numeric packetField value.

    Section: F.7.2.44.

    Args:
        packetFieldID: Handle to a packetField element.

    Returns:
        Integer value or ``None``.
    """
    pf = _resolve_packet_field(packetFieldID)
    if pf is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    val = getattr(pf, "value", None)
    if val is None:
        return None
    try:
        return int(getattr(val, "value", None))  # type: ignore[arg-type]
    except Exception:  # pragma: no cover
        return None


def getPacketFieldValueExpression(packetFieldID: str) -> str | None:
    """Return packetField value expression.

    Section: F.7.2.45.

    Args:
        packetFieldID: Handle to a packetField element.

    Returns:
        Expression string or ``None``.
    """
    pf = _resolve_packet_field(packetFieldID)
    if pf is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    val = getattr(pf, "value", None)
    return getattr(val, "value", None) if val is not None else None


def getPacketFieldValueID(packetFieldID: str) -> str | None:
    """Return the optional value element handle (F.7.2.46)."""
    field = _resolve_packet_field(packetFieldID)
    if field is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    if field.value is None:
        return None
    register_parent(field.value, field, ("value",), "single")
    return get_handle(field.value)


def getPacketFieldWidth(packetFieldID: str) -> int | None:
    """Return packetField width numeric value.

    Section: F.7.2.47.

    Args:
        packetFieldID: Handle to a packetField element.

    Returns:
        Integer width or ``None``.
    """
    pf = _resolve_packet_field(packetFieldID)
    if pf is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    width = getattr(pf, "width", None)
    if width is None:
        return None
    try:
        return int(getattr(width, "value", None))  # type: ignore[arg-type]
    except Exception:  # pragma: no cover
        return None


def getPacketFieldWidthExpression(packetFieldID: str) -> str | None:
    """Return packetField width expression.

    Section: F.7.2.48.

    Args:
        packetFieldID: Handle to a packetField element.

    Returns:
        Expression string or ``None``.
    """
    pf = _resolve_packet_field(packetFieldID)
    if pf is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    width = getattr(pf, "width", None)
    return getattr(width, "value", None) if width is not None else None


def getPacketFieldWidthID(packetFieldID: str) -> str | None:
    """Return handle of packetField width element.

    Section: F.7.2.49.

    Args:
        packetFieldID: Handle to a packetField element.

    Returns:
        Width handle string or ``None``.
    """
    pf = _resolve_packet_field(packetFieldID)
    if pf is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    width = getattr(pf, "width", None)
    if width is None:
        return None
    register_parent(width, pf, ("width",), "single")
    return get_handle(width)


def getPacketPacketFieldIDs(packetID: str) -> list[str]:
    """Return packetField child handles of a packet.

    Section: F.7.2.50.

    Args:
        packetID: Handle to a packet element.

    Returns:
        List of packetField handles (possibly empty).
    """
    pkt = _resolve_packet(packetID)
    if pkt is None:
        raise TgiError("Invalid packet handle", TgiFaultCode.INVALID_ID)
    pf_container = getattr(pkt, "packet_fields", None)
    if pf_container is None:
        return []
    for field in pf_container.packet_field:
        register_parent(field, pf_container, ("packet_field",), "list")
    return [get_handle(field) for field in pf_container.packet_field]


# ---------------------------------------------------------------------------
# EXTENDED
# ---------------------------------------------------------------------------


def addAbstractionDefChoice(abstractionDefinitionID: str, name: str, enumerations: Sequence[str]) -> str:
    """Add the named choice and its supplied enumeration expressions (F.7.3.1)."""
    from .choice import _validated_choice

    ad = _resolve(abstractionDefinitionID)
    if ad is None:
        raise TgiError("Invalid abstraction definition handle", TgiFaultCode.INVALID_ID)
    choice = _validated_choice(name, enumerations)
    if ad.choices is None:
        ad.choices = Choices()
    ad.choices.choice.append(choice)
    register_parent(choice, ad, ("choices", "choice"), "list")
    return get_handle(choice)


def addAbstractionDefPort(abstractionDefinitionID: str, logicalName: str, type: str) -> str:
    """Add a logical wire or transactional port (F.7.3.2).

    Validate inputs before modifying the root. Packet metadata is separate
    from the standard port-style choice.
    """
    ad = _resolve(abstractionDefinitionID)
    if ad is None:
        raise TgiError("Invalid abstraction definition handle", TgiFaultCode.INVALID_ID)
    if not isinstance(logicalName, str) or not logicalName.strip():
        raise TgiError("Logical name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if type not in ("wire", "transactional"):
        raise TgiError("Port type must be wire or transactional", TgiFaultCode.INVALID_ARGUMENT)
    style = Wire() if type == "wire" else AbstractionDefinition.Ports.Port.Transactional()
    port = AbstractionDefinition.Ports.Port(logical_name=logicalName, wire_or_transactional=style)
    if ad.ports is None:
        ad.ports = AbstractionDefinition.Ports()
    ad.ports.port.append(port)
    register_parent(port, ad, ("ports", "port"), "list")
    return get_handle(port)


def addAbstractionDefPortMode(abstractionDefPortID: str, mode: str) -> str:
    """Create a standard logical-port mode (F.7.3.3).

    System mode starts with an empty group because this operation has no group
    input; complete that group before semantic validation.
    """
    port = _resolve_port(abstractionDefPortID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    names = {"onInitiator": "on_initiator", "onTarget": "on_target", "onSystem": "on_system"}
    if not isinstance(mode, str) or mode not in names:
        raise TgiError("Invalid logical port mode", TgiFaultCode.INVALID_ARGUMENT)
    style = port.wire_or_transactional
    if not isinstance(style, (Wire, AbstractionDefinition.Ports.Port.Transactional)):
        raise TgiError("Port has no supported style", TgiFaultCode.INVALID_ARGUMENT)
    attr = names[mode]
    cls = getattr(type(style), mode[0].upper() + mode[1:])
    if mode == "onSystem":
        item = cls(group="")
        style.on_system.append(item)
        container = "list"
    else:
        item = getattr(style, attr)
        if item is None:
            item = cls()
            setattr(style, attr, item)
        container = "single"
    register_parent(item, style, (attr,), container)
    return get_handle(item)


def addAbstractionDefPortPacket(
    absDefPortID: str,
    packetName: str,
    packetFieldName: str,
    packetFieldWidth: str,
) -> str:  # pragma: no cover - scaffold
    """Add a port packet with one field.

    Section: F.7.3.4.

    Creates (if necessary) the packets container and adds a new packet with a
    single field.

    Args:
        absDefPortID: Port handle.
        packetName: Packet name.
        packetFieldName: Field name.
        packetFieldWidth: Width expression string.

    Returns:
        Handle of the created packet element.

    Raises:
        TgiError: If the port handle is invalid.
    """
    p = _resolve_port(absDefPortID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    from org.accellera.ipxact.v1685_2022.packets import Packets
    from org.accellera.ipxact.v1685_2022.port_packet_field_type import PortPacketFieldType
    from org.accellera.ipxact.v1685_2022.port_packet_fields_type import (
        PortPacketFieldsType,
    )
    from org.accellera.ipxact.v1685_2022.port_packet_type import PortPacketType
    from org.accellera.ipxact.v1685_2022.unresolved_unsigned_positive_int_expression import (
        UnresolvedUnsignedPositiveIntExpression,
    )

    for label, value in (("Packet name", packetName), ("Field name", packetFieldName),
                         ("Field width expression", packetFieldWidth)):
        if not isinstance(value, str) or not value.strip():
            raise TgiError(f"{label} requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    field = PortPacketFieldType(
        name=packetFieldName,
        width=UnresolvedUnsignedPositiveIntExpression(value=packetFieldWidth),  # type: ignore[arg-type]
    )
    packet = PortPacketType(
        name=packetName,
        packet_fields=PortPacketFieldsType(packet_field=[field]),  # type: ignore[arg-type]
    )
    if p.packets is None:
        p.packets = Packets()
    p.packets.packet.append(packet)  # type: ignore[attr-defined]
    register_parent(packet, p.packets, ("packet",), "list")
    # Register field relationship
    if packet.packet_fields is not None:  # type: ignore[truthy-bool]
        register_parent(field, packet.packet_fields, ("packet_field",), "list")
    return get_handle(packet)


def addAbstractionDefPortTransactionalOnSystem(portID: str, group: str) -> str:
    """Append a grouped transactional system mode with atomic input validation."""
    port = _resolve_port(portID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    style = port.wire_or_transactional
    if not isinstance(style, AbstractionDefinition.Ports.Port.Transactional):
        raise TgiError("Wrong logical port style", TgiFaultCode.INVALID_ARGUMENT)
    if not isinstance(group, str) or not group.strip():
        raise TgiError("Group requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    item = AbstractionDefinition.Ports.Port.Transactional.OnSystem(group=group)
    style.on_system.append(item)
    register_parent(item, style, ("on_system",), "list")
    return get_handle(item)


def addAbstractionDefPortWireOnSystem(portID: str, group: str) -> str:
    """Append a grouped wire system mode with atomic input validation."""
    port = _resolve_port(portID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    style = port.wire_or_transactional
    if not isinstance(style, Wire):
        raise TgiError("Wrong logical port style", TgiFaultCode.INVALID_ARGUMENT)
    if not isinstance(group, str) or not group.strip():
        raise TgiError("Group requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    item = Wire.OnSystem(group=group)
    style.on_system.append(item)
    register_parent(item, style, ("on_system",), "list")
    return get_handle(item)


def removeAbstractionDefChoice(choiceID: str) -> bool:  # pragma: no cover - scaffold
    """Remove a choice element.

    Section: F.7.3.9.

    Args:
        choiceID: Choice handle.

    Returns:
        True if removed, False otherwise.
    """
    target = resolve_handle(choiceID)
    if target is None:
        return False
    return detach_child_by_handle(choiceID)


def removeAbstractionDefPort(portID: str) -> bool:
    """Remove a port.

    Section: F.7.3.11.

    Args:
        portID: Port handle.

    Returns:
        True if removed, False otherwise.
    """
    target = _resolve_port(portID)
    if target is None:
        return False
    return detach_child_by_handle(portID)


def removeAbstractionDefPortMode(portModeID: str) -> bool:
    """Detach a wire or transactional mode by its handle (F.7.3.13)."""
    tr = AbstractionDefinition.Ports.Port.Transactional
    obj = resolve_handle(portModeID)
    if not isinstance(obj, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem,
                            tr.OnInitiator, tr.OnTarget, tr.OnSystem)):
        return False
    return detach_child_by_handle(portModeID)


def removeAbstractionDefPortTransactionalOnSystem(onSystemID: str) -> bool:
    """Detach only a transactional system mode (F.7.3.20)."""
    if not isinstance(resolve_handle(onSystemID), AbstractionDefinition.Ports.Port.Transactional.OnSystem):
        return False
    return detach_child_by_handle(onSystemID)


def removeAbstractionDefPortWireOnSystem(onSystemID: str) -> bool:
    """Detach only a wire system mode (F.7.3.30)."""
    return isinstance(resolve_handle(onSystemID), Wire.OnSystem) and detach_child_by_handle(onSystemID)


def setAbstractionDefExtends(
    abstractionDefinitionID: str, vendor: str, library: str, name: str, version: str
) -> bool:  # pragma: no cover - scaffold
    """Set the extends reference.

    Section: F.7.3.44.

    Args:
        abstractionDefinitionID: Abstraction definition handle.
        vendor: Vendor string.
        library: Library string.
        name: Name string.
        version: Version string.

    Returns:
        True on success.

    Raises:
        TgiError: If the handle is invalid.
    """
    ad = _resolve(abstractionDefinitionID)
    if ad is None:
        raise TgiError("Invalid abstraction definition handle", TgiFaultCode.INVALID_ID)
    from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType

    ad.extends = LibraryRefType(vendor=vendor, library=library, name=name, version=version)  # type: ignore[arg-type]
    return True


def removeAbstractionDefPortTransactionalModeBusWidth(abstractionDefPortModeID: str) -> bool:
    """Remove busWidth from one transactional mode locus (F.7.3.14)."""
    transactional = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (transactional.OnInitiator, transactional.OnTarget, transactional.OnSystem)):
        return False
    child = mode.bus_width
    if child is None:
        return False
    child_handle = get_handle(child)
    register_parent(child, mode, ("bus_width",), "single")
    return detach_child_by_handle(child_handle)


def removeAbstractionDefPortTransactionalModeInitiative(abstractionDefPortModeID: str) -> bool:
    """Remove initiative from one transactional mode locus (F.7.3.15)."""
    transactional = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (transactional.OnInitiator, transactional.OnTarget, transactional.OnSystem)):
        return False
    if mode.initiative is None:
        return False
    mode.initiative = None
    return True


def removeAbstractionDefPortTransactionalModeKind(abstractionDefPortModeID: str) -> bool:
    """Remove kind from one transactional mode locus (F.7.3.16)."""
    transactional = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (transactional.OnInitiator, transactional.OnTarget, transactional.OnSystem)):
        return False
    child = mode.kind
    if child is None:
        return False
    child_handle = get_handle(child)
    register_parent(child, mode, ("kind",), "single")
    return detach_child_by_handle(child_handle)


def removeAbstractionDefPortTransactionalModePresence(abstractionDefPortModeID: str) -> bool:
    """Remove presence from one transactional mode locus (F.7.3.17)."""
    transactional = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (transactional.OnInitiator, transactional.OnTarget, transactional.OnSystem)):
        return False
    child = mode.presence
    if child is None:
        return False
    child_handle = get_handle(child)
    register_parent(child, mode, ("presence",), "single")
    return detach_child_by_handle(child_handle)


def removeAbstractionDefPortTransactionalModeProtocol(abstractionDefPortModeID: str) -> bool:
    """Remove protocol from one transactional mode locus (F.7.3.18)."""
    transactional = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (transactional.OnInitiator, transactional.OnTarget, transactional.OnSystem)):
        return False
    child = mode.protocol
    if child is None:
        return False
    child_handle = get_handle(child)
    register_parent(child, mode, ("protocol",), "single")
    return detach_child_by_handle(child_handle)


def removeAbstractionDefPortTransactionalOnInitiator(portID: str) -> bool:
    """Remove the transactional on_initiator and invalidate its handle (F.7.3.19)."""
    return _remove_port_locus(portID, AbstractionDefinition.Ports.Port.Transactional, "on_initiator")


def removeAbstractionDefPortTransactionalOnTarget(portID: str) -> bool:
    """Remove the transactional on_target and invalidate its handle (F.7.3.21)."""
    return _remove_port_locus(portID, AbstractionDefinition.Ports.Port.Transactional, "on_target")


def removeAbstractionDefPortTransactionalQualifier(portID: str) -> bool:
    """Remove only the transactional qualifier and invalidate its handle (F.7.3.22)."""
    port = _resolve_port(portID)
    if port is None:
        return False
    style = port.wire_or_transactional
    if not isinstance(style, AbstractionDefinition.Ports.Port.Transactional) or style.qualifier is None:
        return False
    register_parent(style.qualifier, style, ("qualifier",), "single")
    return detach_child_by_handle(get_handle(style.qualifier))


def _ensure_wire(portID: str):
    """Resolve and return the wire sub-element for a port.

    Helper (non-spec) used by wire set/remove functions.

    Args:
        portID: Handle of a wire style port.

    Returns:
        Wire style object.

    Raises:
        TgiError: If handle invalid or port not wire style.
    """
    p = _resolve_port(portID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    if p.wire is None:
        raise TgiError("Port not wire", TgiFaultCode.INVALID_ARGUMENT)
    return p.wire


def removeAbstractionDefPortWireModeDirection(abstractionDefPortModeID: str) -> bool:
    """Remove direction from one wire mode locus (F.7.3.24)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        return False
    if mode.direction is None:
        return False
    mode.direction = None
    return True


def removeAbstractionDefPortWireModeMirroredModeConstraints(
    abstractionDefPortModeID: str,
) -> bool:
    """Remove mirroredModeConstraints from one wire mode locus (F.7.3.25)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        return False
    child = mode.mirrored_mode_constraints
    if child is None:
        return False
    register_parent(child, mode, ("mirrored_mode_constraints",), "single")
    return detach_child_by_handle(get_handle(child))


def removeAbstractionDefPortWireModeModeConstraints(abstractionDefPortModeID: str) -> bool:
    """Remove modeConstraints from one wire mode locus (F.7.3.26)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        return False
    child = mode.mode_constraints
    if child is None:
        return False
    register_parent(child, mode, ("mode_constraints",), "single")
    return detach_child_by_handle(get_handle(child))


def removeAbstractionDefPortWireModePresence(abstractionDefPortModeID: str) -> bool:
    """Remove presence from one wire mode locus (F.7.3.27)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        return False
    child = mode.presence
    if child is None:
        return False
    register_parent(child, mode, ("presence",), "single")
    return detach_child_by_handle(get_handle(child))


def removeAbstractionDefPortWireModeWidth(abstractionDefPortModeID: str) -> bool:
    """Remove width from one wire mode locus (F.7.3.28)."""
    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        return False
    child = mode.width
    if child is None:
        return False
    register_parent(child, mode, ("width",), "single")
    return detach_child_by_handle(get_handle(child))


def removeAbstractionDefPortWireOnInitiator(portID: str) -> bool:
    """Remove the wire on_initiator and invalidate its handle (F.7.3.29)."""
    return _remove_port_locus(portID, Wire, "on_initiator")


def removeAbstractionDefPortWireOnTarget(portID: str) -> bool:
    """Remove the wire on_target and invalidate its handle (F.7.3.31)."""
    return _remove_port_locus(portID, Wire, "on_target")


def removeAbstractionDefPortWireQualifier(portID: str) -> bool:
    """Remove only the wire qualifier and invalidate its handle (F.7.3.32)."""
    port = _resolve_port(portID)
    if port is None:
        return False
    style = port.wire_or_transactional
    if not isinstance(style, Wire) or style.qualifier is None:
        return False
    register_parent(style.qualifier, style, ("qualifier",), "single")
    return detach_child_by_handle(get_handle(style.qualifier))


def removeAbstractionDefPortWireRequiresDriver(portID: str) -> bool:
    """Remove only the requiresDriver alternative and invalidate its handle (F.7.3.33)."""
    port = _resolve_port(portID)
    if port is None:
        return False
    wire = port.wire_or_transactional
    if not isinstance(wire, Wire):
        return False
    from org.accellera.ipxact.v1685_2022.requires_driver import RequiresDriver

    driver = wire.default_value_or_requires_driver
    if not isinstance(driver, RequiresDriver):
        return False
    register_parent(driver, wire, ("default_value_or_requires_driver",), "single")
    return detach_child_by_handle(get_handle(driver))


def setAbstractionDefPortTransactionalModeBusWidth(abstractionDefPortModeID: str, width: str) -> bool:
    """Set bus_width on the supplied transactional mode (F.7.3.48)."""
    return _set_logical_mode_property(abstractionDefPortModeID, width, "transactional", "bus_width")


def setAbstractionDefPortTransactionalModeInitiative(abstractionDefPortModeID: str, initiative: str) -> bool:
    """Set the supplied transactional mode's initiative (F.7.3.49)."""
    from org.accellera.ipxact.v1685_2022 import (
        OnInitiatorInitiative, OnSystemInitiative, OnTargetInitiative,
    )

    tr = AbstractionDefinition.Ports.Port.Transactional
    mode = resolve_handle(abstractionDefPortModeID)
    enum_types = {
        tr.OnInitiator: OnInitiatorInitiative,
        tr.OnTarget: OnTargetInitiative,
        tr.OnSystem: OnSystemInitiative,
    }
    if not isinstance(mode, tuple(enum_types)):
        raise TgiError("Invalid transactional logical port mode handle", TgiFaultCode.INVALID_ID)
    if not isinstance(initiative, str):
        raise TgiError("Initiative requires a string", TgiFaultCode.INVALID_ARGUMENT)
    enum_type = next(enum for mode_type, enum in enum_types.items() if isinstance(mode, mode_type))
    try:
        converted = enum_type(initiative)
    except ValueError as error:
        raise TgiError("Invalid initiative value", TgiFaultCode.INVALID_ARGUMENT) from error
    mode.initiative = converted
    return True


def setAbstractionDefPortTransactionalModeKind(abstractionDefPortModeID: str, kind: str) -> bool:
    """Set kind on the supplied transactional mode (F.7.3.50)."""
    return _set_logical_mode_property(abstractionDefPortModeID, kind, "transactional", "kind")


def setAbstractionDefPortTransactionalModePresence(abstractionDefPortModeID: str, presence: str) -> bool:
    """Set presence on the supplied transactional mode (F.7.3.51)."""
    return _set_logical_mode_property(abstractionDefPortModeID, presence, "transactional", "presence")


def setAbstractionDefPortTransactionalModeProtocol(abstractionDefPortModeID: str, protocolType: str) -> bool:
    """Set protocol on the supplied transactional mode (F.7.3.52)."""
    return _set_logical_mode_property(abstractionDefPortModeID, protocolType, "transactional", "protocol")


def setAbstractionDefPortTransactionalOnInitiator(portID: str) -> bool:
    """Ensure the transactional onInitiator exists (F.7.3.53)."""
    _ensure_port_locus(portID, AbstractionDefinition.Ports.Port.Transactional, "onInitiator")
    return True


def setAbstractionDefPortTransactionalOnTarget(portID: str) -> bool:
    """Ensure the transactional onTarget exists (F.7.3.54)."""
    _ensure_port_locus(portID, AbstractionDefinition.Ports.Port.Transactional, "onTarget")
    return True


def setAbstractionDefPortTransactionalQualifier(portID: str) -> bool:
    """Ensure the transactional qualifier, preserving existing content (F.7.3.55)."""
    from org.accellera.ipxact.v1685_2022 import QualifierType

    port = _resolve_port(portID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    style = port.wire_or_transactional
    if not isinstance(style, AbstractionDefinition.Ports.Port.Transactional):
        raise TgiError("Port has the wrong style", TgiFaultCode.INVALID_ARGUMENT)
    if style.qualifier is None:
        style.qualifier = QualifierType()
    register_parent(style.qualifier, style, ("qualifier",), "single")
    return True


def setAbstractionDefPortTransactional(portID: str) -> bool:
    """Ensure port has transactional style container.

    Section: F.7.3.56.

    Args:
        portID: Port handle.

    Returns:
        True (idempotent create).
    """
    p = _resolve_port(portID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    if p.transactional is None:
        p.transactional = AbstractionDefinition.Ports.Port.Transactional()  # type: ignore[attr-defined]
    return True


def setAbstractionDefPortWire(portID: str) -> bool:
    """Ensure port has wire style container.

    Section: F.7.3.57.

    Args:
        portID: Port handle.

    Returns:
        True (idempotent create).
    """
    p = _resolve_port(portID)
    if p is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    if p.wire is None:
        from org.accellera.ipxact.v1685_2022.wire import Wire
        p.wire = Wire()  # type: ignore[arg-type]
    return True


def setAbstractionDefPortWireDefaultValue(abstractionDefPortID: str, valueExpression: str) -> bool:
    """Set a wire default-value expression while preserving choice-child identity (F.7.3.58)."""
    port = _resolve_port(abstractionDefPortID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    wire = port.wire_or_transactional
    if not isinstance(wire, Wire):
        raise TgiError("Port is not wire style", TgiFaultCode.INVALID_ARGUMENT)
    if not isinstance(valueExpression, str) or not valueExpression.strip():
        raise TgiError("Default value expression requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)

    from org.accellera.ipxact.v1685_2022.requires_driver import RequiresDriver
    from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import (
        UnsignedBitVectorExpression,
    )

    default_value = wire.default_value_or_requires_driver
    if isinstance(default_value, UnsignedBitVectorExpression):
        default_value.value = valueExpression
        register_parent(default_value, wire, ("default_value_or_requires_driver",), "single")
        return True
    if isinstance(default_value, RequiresDriver):
        old_handle = get_handle(default_value)
        register_parent(default_value, wire, ("default_value_or_requires_driver",), "single")
        detach_child_by_handle(old_handle)

    replacement = UnsignedBitVectorExpression(value=valueExpression)
    wire.default_value_or_requires_driver = replacement
    register_parent(replacement, wire, ("default_value_or_requires_driver",), "single")
    return True


def setAbstractionDefPortWireModeDirection(abstractionDefPortModeID: str, direction: str) -> bool:
    """Set direction on the supplied wire mode (F.7.3.59)."""
    return _set_logical_mode_property(abstractionDefPortModeID, direction, "wire", "direction")


def setAbstractionDefPortWireModeMirroredModeConstraints(
    abstractionDefPortModeID: str, timingConstraintClockName: str
) -> bool:
    """Ensure the supplied wire mode's mirrored_mode_constraints container (F.7.3.60)."""
    from org.accellera.ipxact.v1685_2022 import AbstractionDefPortConstraintsType, TimingConstraint

    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        raise TgiError("Invalid wire mode handle", TgiFaultCode.INVALID_ID)
    if not isinstance(timingConstraintClockName, str) or not timingConstraintClockName.strip():
        raise TgiError("Timing clock name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    constraints = mode.mirrored_mode_constraints
    if constraints is None:
        timing = TimingConstraint(value=0.0, clock_name=timingConstraintClockName)
        constraints = AbstractionDefPortConstraintsType(timing_constraint=[timing])
        mode.mirrored_mode_constraints = constraints
        register_parent(timing, constraints, ("timing_constraint",), "list")
    register_parent(constraints, mode, ("mirrored_mode_constraints",), "single")
    return True


def setAbstractionDefPortWireModeModeConstraints(
    abstractionDefPortModeID: str, timingConstraintClockName: str
) -> bool:
    """Ensure the supplied wire mode's mode_constraints container (F.7.3.61)."""
    from org.accellera.ipxact.v1685_2022 import AbstractionDefPortConstraintsType, TimingConstraint

    mode = resolve_handle(abstractionDefPortModeID)
    if not isinstance(mode, (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem)):
        raise TgiError("Invalid wire mode handle", TgiFaultCode.INVALID_ID)
    if not isinstance(timingConstraintClockName, str) or not timingConstraintClockName.strip():
        raise TgiError("Timing clock name requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    constraints = mode.mode_constraints
    if constraints is None:
        timing = TimingConstraint(value=0.0, clock_name=timingConstraintClockName)
        constraints = AbstractionDefPortConstraintsType(timing_constraint=[timing])
        mode.mode_constraints = constraints
        register_parent(timing, constraints, ("timing_constraint",), "list")
    register_parent(constraints, mode, ("mode_constraints",), "single")
    return True


def setAbstractionDefPortWireModePresence(abstractionDefPortModeID: str, presence: str) -> bool:
    """Set presence on the supplied wire mode (F.7.3.62)."""
    return _set_logical_mode_property(abstractionDefPortModeID, presence, "wire", "presence")


def setAbstractionDefPortWireModeWidth(abstractionDefPortModeID: str, width: str) -> bool:
    """Set width on the supplied wire mode (F.7.3.63)."""
    return _set_logical_mode_property(abstractionDefPortModeID, width, "wire", "width")


def setAbstractionDefPortWireOnInitiator(portID: str) -> bool:
    """Ensure the wire onInitiator exists (F.7.3.64)."""
    _ensure_port_locus(portID, Wire, "onInitiator")
    return True


def setAbstractionDefPortWireOnTarget(portID: str) -> bool:
    """Ensure the wire onTarget exists (F.7.3.65)."""
    _ensure_port_locus(portID, Wire, "onTarget")
    return True


def setAbstractionDefPortWireQualifier(abstractionDefPortID: str) -> bool:
    """Ensure the wire qualifier, preserving existing content (F.7.3.66)."""
    from org.accellera.ipxact.v1685_2022 import QualifierType

    port = _resolve_port(abstractionDefPortID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    style = port.wire_or_transactional
    if not isinstance(style, Wire):
        raise TgiError("Port has the wrong style", TgiFaultCode.INVALID_ARGUMENT)
    if style.qualifier is None:
        style.qualifier = QualifierType()
    register_parent(style.qualifier, style, ("qualifier",), "single")
    return True


def setAbstractionDefPortWireRequiresDriver(abstractionDefPortID: str, value: bool) -> bool:
    """Set the requiresDriver choice while preserving same-alternative identity (F.7.3.67)."""
    port = _resolve_port(abstractionDefPortID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    wire = port.wire_or_transactional
    if not isinstance(wire, Wire):
        raise TgiError("Port style does not match the setter", TgiFaultCode.INVALID_ARGUMENT)
    if type(value) is not bool:
        raise TgiError("requiresDriver value must be a bool", TgiFaultCode.INVALID_ARGUMENT)
    from org.accellera.ipxact.v1685_2022.requires_driver import RequiresDriver
    from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression

    current = wire.default_value_or_requires_driver
    if isinstance(current, RequiresDriver):
        current.value = value
        register_parent(current, wire, ("default_value_or_requires_driver",), "single")
        return True
    if isinstance(current, UnsignedBitVectorExpression):
        register_parent(current, wire, ("default_value_or_requires_driver",), "single")
        if not detach_child_by_handle(get_handle(current)):
            return False
    driver = RequiresDriver(value=value)
    wire.default_value_or_requires_driver = driver
    register_parent(driver, wire, ("default_value_or_requires_driver",), "single")
    return True


def addPacketPacketField(packetID: str, fieldName: str, width: int) -> str:
    """Append a named field with a positive integer width (F.7.3.8)."""
    from org.accellera.ipxact.v1685_2022.port_packet_field_type import PortPacketFieldType
    from org.accellera.ipxact.v1685_2022.port_packet_fields_type import PortPacketFieldsType
    from org.accellera.ipxact.v1685_2022.unresolved_unsigned_positive_int_expression import (
        UnresolvedUnsignedPositiveIntExpression,
    )

    packet = _resolve_packet(packetID)
    if packet is None:
        raise TgiError("Invalid packet handle", TgiFaultCode.INVALID_ID)
    if not isinstance(fieldName, str) or not fieldName.strip() or type(width) is not int or width <= 0:
        raise TgiError("Field requires a name and positive integer width", TgiFaultCode.INVALID_ARGUMENT)
    field = PortPacketFieldType(name=fieldName, width=UnresolvedUnsignedPositiveIntExpression(value=str(width)))
    if packet.packet_fields is None:
        packet.packet_fields = PortPacketFieldsType()
    packet.packet_fields.packet_field.append(field)
    register_parent(field, packet.packet_fields, ("packet_field",), "list")
    return get_handle(field)


def removePacketPacketField(packetFieldID: str) -> bool:
    """Detach the identified packet field (F.7.3.43)."""
    return _resolve_packet_field(packetFieldID) is not None and detach_child_by_handle(packetFieldID)


def removeAbstractionDefPortPacket(packetID: str) -> bool:
    """Detach the identified logical-port packet (F.7.68.38)."""
    return _resolve_packet(packetID) is not None and detach_child_by_handle(packetID)


def _set_packet_endianness(handle: str, endianness: str, *, field: bool) -> bool:
    from org.accellera.ipxact.v1685_2022.endianess_type import EndianessType

    target = _resolve_packet_field(handle) if field else _resolve_packet(handle)
    if target is None:
        raise TgiError("Invalid packet or field handle", TgiFaultCode.INVALID_ID)
    if not isinstance(endianness, str) or endianness not in ("big", "little"):
        raise TgiError("Endianness must be big or little", TgiFaultCode.INVALID_ARGUMENT)
    target.endianness = EndianessType(endianness)
    return True


def setPacketEndianness(packetID: str, endianness: str) -> bool:
    """Set explicit packet endianness (F.7.3.71)."""
    return _set_packet_endianness(packetID, endianness, field=False)


def setPacketFieldEndianness(packetFieldID: str, endianness: str) -> bool:
    """Set explicit field endianness (F.7.3.72)."""
    return _set_packet_endianness(packetFieldID, endianness, field=True)


def removePacketEndianness(packetID: str) -> bool:
    """Remove explicit packet endianness (F.7.3.39)."""
    packet = _resolve_packet(packetID)
    if packet is None or packet.endianness is None:
        return False
    packet.endianness = None
    return True


def removePacketFieldEndianness(packetFieldID: str) -> bool:
    """Remove explicit field endianness (F.7.3.40)."""
    field = _resolve_packet_field(packetFieldID)
    if field is None or field.endianness is None:
        return False
    field.endianness = None
    return True


def _set_packet_field_expression(packetFieldID: str, expression: str, *, width: bool) -> bool:
    from org.accellera.ipxact.v1685_2022.unresolved_unsigned_positive_int_expression import (
        UnresolvedUnsignedPositiveIntExpression,
    )
    from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression

    field = _resolve_packet_field(packetFieldID)
    if field is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    if not isinstance(expression, str) or not expression.strip():
        raise TgiError("Expression requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    attr = "width" if width else "value"
    element = getattr(field, attr)
    if element is None:
        element = (UnresolvedUnsignedPositiveIntExpression(value=expression) if width
                   else UnsignedBitVectorExpression(value=expression))
        setattr(field, attr, element)
    else:
        element.value = expression
    register_parent(element, field, (attr,), "single")
    return True


def setPacketFieldValue(packetFieldID: str, expression: str) -> bool:
    """Set the source value expression without resolving it (F.7.3.74)."""
    return _set_packet_field_expression(packetFieldID, expression, width=False)


def setPacketFieldWidth(packetFieldID: str, expression: str) -> bool:
    """Set the source width expression without resolving it (F.7.3.75)."""
    return _set_packet_field_expression(packetFieldID, expression, width=True)


__all__ += [
    "addPacketPacketField", "removePacketPacketField", "removeAbstractionDefPortPacket",
    "setPacketEndianness", "setPacketFieldEndianness", "removePacketEndianness",
    "removePacketFieldEndianness", "setPacketFieldValue", "setPacketFieldWidth",
]


def setPacketFieldQualifier(packetFieldID: str) -> bool:
    """Ensure a qualifier container exists (F.7.3.73; WSDL takes only the field ID).

    Existing qualifier content and handle identity are preserved. Qualifier
    flags are edited through the qualifier category operations.
    """
    from org.accellera.ipxact.v1685_2022.qualifier_type import QualifierType

    field = _resolve_packet_field(packetFieldID)
    if field is None:
        raise TgiError("Invalid packetField handle", TgiFaultCode.INVALID_ID)
    if field.qualifier is None:
        field.qualifier = QualifierType()
    register_parent(field.qualifier, field, ("qualifier",), "single")
    return True


def removePacketFieldQualifier(packetFieldID: str) -> bool:
    """Remove the field qualifier and invalidate its handle (F.7.3.41)."""
    field = _resolve_packet_field(packetFieldID)
    if field is None or field.qualifier is None:
        return False
    register_parent(field.qualifier, field, ("qualifier",), "single")
    return detach_child_by_handle(get_handle(field.qualifier))


def removePacketFieldValue(packetFieldID: str) -> bool:
    """Remove the optional field value and invalidate its handle (F.7.3.42)."""
    field = _resolve_packet_field(packetFieldID)
    if field is None or field.value is None:
        return False
    register_parent(field.value, field, ("value",), "single")
    return detach_child_by_handle(get_handle(field.value))


__all__ += ["setPacketFieldQualifier", "removePacketFieldQualifier", "removePacketFieldValue"]


def _remove_port_locus(portID: str, style_type: type, attr: str) -> bool:
    port = _resolve_port(portID)
    if port is None or not isinstance(port.wire_or_transactional, style_type):
        return False
    style = port.wire_or_transactional
    mode = getattr(style, attr)
    if mode is None:
        return False
    register_parent(mode, style, (attr,), "single")
    return detach_child_by_handle(get_handle(mode))


def _resolve_logical_system(handle: str):
    obj = resolve_handle(handle)
    return obj if isinstance(obj, (Wire.OnSystem, AbstractionDefinition.Ports.Port.Transactional.OnSystem)) else None


def setOnSystemGroup(onSystemID: str, group: str) -> bool:
    """Set a nonempty logical system group without replacing the mode (F.7.3.70)."""
    mode = _resolve_logical_system(onSystemID)
    if mode is None:
        raise TgiError("Invalid onSystem handle", TgiFaultCode.INVALID_ID)
    if not isinstance(group, str) or not group.strip():
        raise TgiError("Group requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    mode.group = group
    return True


def setAbstractionDefPortMode(abstractionDefPortID: str, mode: str) -> str:
    """Ensure a named mode, or append a system mode (F.7.3.47).

    As with addAbstractionDefPortMode, complete an onSystem group using
    setOnSystemGroup before semantic validation.
    """
    return addAbstractionDefPortMode(abstractionDefPortID, mode)


def _ensure_port_locus(portID: str, style_type: type, mode: str) -> str:
    port = _resolve_port(portID)
    if port is None:
        raise TgiError("Invalid abstractionDefPort handle", TgiFaultCode.INVALID_ID)
    if not isinstance(port.wire_or_transactional, style_type):
        raise TgiError("Port style does not match the setter", TgiFaultCode.INVALID_ARGUMENT)
    return addAbstractionDefPortMode(portID, mode)


__all__ += ["setOnSystemGroup", "setAbstractionDefPortMode"]


def _set_logical_mode_property(handle: str, value: str, style: str, attr: str) -> bool:
    from org.accellera.ipxact.v1685_2022 import (
        Direction, Kind, KindType, Presence, PresenceType, Protocol, ProtocolTypeType,
        UnsignedPositiveIntExpression,
    )

    tr = AbstractionDefinition.Ports.Port.Transactional
    types = (Wire.OnInitiator, Wire.OnTarget, Wire.OnSystem) if style == "wire" else (
        tr.OnInitiator, tr.OnTarget, tr.OnSystem)
    mode = resolve_handle(handle)
    if not isinstance(mode, types):
        raise TgiError("Invalid logical port mode handle", TgiFaultCode.INVALID_ID)
    if not isinstance(value, str) or not value.strip():
        raise TgiError("Property requires a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    try:
        if attr == "presence":
            converted = PresenceType(value)
            replacement = Presence(value=converted)
        elif attr == "kind":
            converted = KindType(value)
            replacement = Kind(value=converted)
        elif attr == "protocol":
            converted = ProtocolTypeType(value)
            replacement = Protocol(protocol_type=Protocol.ProtocolType(value=converted))
        elif attr == "direction":
            converted = Direction(value)
            mode.direction = converted
            return True
        else:
            converted = value
            model = type(mode).Width if attr == "width" else UnsignedPositiveIntExpression
            replacement = model(value=value)
    except ValueError as error:
        raise TgiError("Invalid mode property value", TgiFaultCode.INVALID_ARGUMENT) from error
    child = getattr(mode, attr)
    if child is None:
        child = replacement
        setattr(mode, attr, child)
    elif attr == "protocol":
        child.protocol_type.value = converted
    else:
        child.value = converted
    register_parent(child, mode, (attr,), "single")
    return True


def removeAbstractionDefPortWireDefaultValue(abstractionDefPortID: str) -> bool:
    """Remove and invalidate only the wire default-value expression (F.7.3.23)."""
    port = _resolve_port(abstractionDefPortID)
    if port is None:
        return False
    wire = port.wire_or_transactional
    if not isinstance(wire, Wire):
        return False
    from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import (
        UnsignedBitVectorExpression,
    )

    default_value = wire.default_value_or_requires_driver
    if not isinstance(default_value, UnsignedBitVectorExpression):
        return False
    child_handle = get_handle(default_value)
    register_parent(default_value, wire, ("default_value_or_requires_driver",), "single")
    return detach_child_by_handle(child_handle)

__all__ += ["removeAbstractionDefPortWireDefaultValue"]
