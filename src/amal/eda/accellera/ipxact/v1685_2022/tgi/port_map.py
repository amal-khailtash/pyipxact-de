"""Port map operations from IEEE 1685-2022 F.7.69 and F.7.70.

Logical and physical getters receive their own child handles. Source expressions
remain unchanged; numeric getters evaluate self-contained SystemVerilog constants.
Configured expression environments remain separate work. Edits use generated
choice fields, preserve wrapper metadata and invalidate removed descendants.
"""

import re
from collections.abc import Sequence
from typing import Any, Protocol

from org.accellera.ipxact.v1685_2022.abstraction_types import AbstractionTypes
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.index import Index
from org.accellera.ipxact.v1685_2022.indices import Indices
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.part_select import PartSelect
from org.accellera.ipxact.v1685_2022.range import Range
from org.accellera.ipxact.v1685_2022.right import Right
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression

from ._expressions import _integer, _source, _xml_text
from ._ranges import _apply_range, _array, _parts, _range_plan
from .address_space import _register_owned_child
from .component import _list_attr, _register_graph
from .core import TgiError, TgiFaultCode, detach_child_by_handle, get_handle, register_parent, resolve_handle

__all__: list[str] = [
    # BASE (F.7.69)
    "getLogicalPortRange",
    "getLogicalPortRangeExpression",
    "getLogicalPortRangeLeftID",
    "getLogicalPortRangeRightID",
    "getPhysicalPortPartSelectID",
    "getPhysicalPortSubPortIDs",
    "getPortMapIsInformative",
    "getPortMapLogicalPortID",
    "getPortMapLogicalTieOff",
    "getPortMapLogicalTieOffExpression",
    "getPortMapLogicalTieOffID",
    "getPortMapPhysicalPortID",
    # EXTENDED (F.7.70)
    "addPhysicalPortSubPort",
    "addPortMapPhysicalPortSubPort",
    "removePhysicalPortPartSelect",
    "removePhysicalPortSubPort",
    "removePortMapIsInformative",
    "setAbstractionTypeAbstractionRef",
    "setLogicalPortRange",
    "setPhysicalPortPartSelect",
    "setPortMapIsInformative",
    "setPortMapLogicalPort",
    "setPortMapLogicalTieOff",
    "setPortMapPhysicalPort",
    "setSubPortMapPartSelect",
]

_PortMap = AbstractionTypes.AbstractionType.PortMaps.PortMap
_LogicalPort = _PortMap.LogicalPort
_PhysicalPort = _PortMap.PhysicalPort
_SubPort = _PhysicalPort.SubPort
_CHOICE = "physical_port_or_logical_tie_off"
_UINT_MAX = (1 << 32) - 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require(handle: str, cls: type) -> Any:
    obj = resolve_handle(handle) if isinstance(handle, str) else None
    if not isinstance(obj, cls):
        raise TgiError(f"Invalid {cls.__name__} handle", TgiFaultCode.INVALID_ID)
    return obj


def _child[T](parent: object, attr: str, cls: type[T]) -> T | None:
    child = getattr(parent, attr)
    if child is None:
        return None
    if not isinstance(child, cls):
        if attr == _CHOICE and isinstance(child, (_PhysicalPort, UnsignedBitVectorExpression)):
            return None
        raise TgiError(f"Invalid {attr} child", TgiFaultCode.INVALID_ID)
    register_parent(child, parent, (attr,), "single")
    _register_graph(child)
    return child


def _child_id[T](parent: object, attr: str, cls: type[T]) -> str | None:
    child = _child(parent, attr, cls)
    return get_handle(child) if child is not None else None


def _name(value: str, kind: str) -> str:
    from lxml import etree

    from .name_group import _name_schema

    _xml_text(value)
    value = re.sub(r"[\t\n\r ]+", " ", value).strip(" ")
    element = etree.Element("name")
    element.text = value
    if not _name_schema(kind).validate(element):
        raise TgiError(f"Invalid {kind}", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _remove_child(parent: Any, attr: str) -> bool:
    child = getattr(parent, attr)
    if child is None:
        return False
    register_parent(child, parent, (attr,), "single")
    _register_graph(child)
    return detach_child_by_handle(get_handle(child))


def _replace_choice(parent: Any, value: Any) -> None:
    _remove_child(parent, _CHOICE)
    setattr(parent, _CHOICE, value)
    register_parent(value, parent, (_CHOICE,), "single")
    _register_graph(value)


class _PartSelectOwner(Protocol):
    """Generated objects owning an optional partSelect."""

    part_select: PartSelect | None


def _set_part_select(parent: _PartSelectOwner, range: Sequence[str] | None, indices: Sequence[str] | None) -> str:
    current = parent.part_select
    old_range, old_indices = _parts(current)
    range_values = _range_plan(range, old_range) if range is not None else None
    index_values = _array(indices, "indices") if indices is not None else []
    if range_values is None and not index_values:
        raise TgiError("partSelect requires a range or indices", TgiFaultCode.INVALID_ARGUMENT)
    if old_indices is not None and not isinstance(old_indices.index, (list, tuple)):
        raise TgiError("Invalid indices model", TgiFaultCode.INVALID_ID)
    old_items = list(old_indices.index) if old_indices else []
    if any(not isinstance(item, Index) for item in old_items):
        raise TgiError("Invalid indices model", TgiFaultCode.INVALID_ID)
    index_values = [
        _source(value, old_items[i] if i < len(old_items) else None) for i, value in enumerate(index_values)
    ]
    if current is None:
        current = PartSelect()
        parent.part_select = current
    register_parent(current, parent, ("part_select",), "single")
    # Normalize compound storage before removing any obsolete owned child.
    value = current.range_or_indices
    if isinstance(value, tuple):
        current.range_or_indices = list(value)
    _register_graph(current)
    for child, keep in [(old_range, range_values is not None), (old_indices, bool(index_values))]:
        if child is not None and not keep:
            detach_child_by_handle(get_handle(child))
    children = []
    if index_values:
        holder = old_indices or Indices()
        holder.index = old_items
        _register_graph(holder)
        for item in old_items[len(index_values) :]:
            detach_child_by_handle(get_handle(item))
        items = []
        for i, value in enumerate(index_values):
            item = old_items[i] if i < len(old_items) else Index(value=value)
            item.value = value
            items.append(item)
        holder.index = items
        children.append(holder)
    if range_values is not None:
        children.append(_apply_range(old_range, range_values))
    current.range_or_indices = children[0] if len(children) == 1 else children
    _register_graph(current)
    return get_handle(current)


# ---------------------------------------------------------------------------
# BASE functions (F.7.69)
# ---------------------------------------------------------------------------


def getLogicalPortRange(logicalPortID: str) -> list[int] | None:
    """Return evaluated left and right bounds of a logical port.

    Args:
        logicalPortID: Handle to a logicalPort child.

    Returns:
        Two evaluated unsigned integers, or None when the range is absent. Unresolved expressions fault.

    Section: F.7.69.1.
    """
    logical = _require(logicalPortID, _LogicalPort)
    value = _child(logical, "range", Range)
    if value is None:
        return None
    return [_integer(value.left.value, _UINT_MAX), _integer(value.right.value, _UINT_MAX)]


def getLogicalPortRangeExpression(logicalPortID: str) -> list[str] | None:
    """Return the stored left and right expression sources of a logical port.

    Args:
        logicalPortID: Handle to a logicalPort child.

    Returns:
        Two source strings [left, right], or None when the range is absent.

    Section: F.7.69.2.
    """
    value = _child(_require(logicalPortID, _LogicalPort), "range", Range)
    return [value.left.value, value.right.value] if value is not None else None


def getLogicalPortRangeLeftID(logicalPortID: str) -> str | None:
    """Return the stable handle to the logical range left bound.

    Args:
        logicalPortID: Handle to a logicalPort child.

    Returns:
        Owned child handle, or None when optional content or the matching choice is absent.

    Section: F.7.69.3.
    """
    value = _child(_require(logicalPortID, _LogicalPort), "range", Range)
    return _child_id(value, "left", Left) if value is not None else None


def getLogicalPortRangeRightID(logicalPortID: str) -> str | None:
    """Return the stable handle to the logical range right bound.

    Args:
        logicalPortID: Handle to a logicalPort child.

    Returns:
        Owned child handle, or None when optional content or the matching choice is absent.

    Section: F.7.69.4.
    """
    value = _child(_require(logicalPortID, _LogicalPort), "range", Range)
    return _child_id(value, "right", Right) if value is not None else None


def getPhysicalPortPartSelectID(physicalPortID: str) -> str | None:
    """Return the owned partSelect handle of a physical port.

    Args:
        physicalPortID: Handle to a physicalPort child.

    Returns:
        Owned child handle, or None when optional content or the matching choice is absent.

    Section: F.7.69.5.
    """
    return _child_id(_require(physicalPortID, _PhysicalPort), "part_select", PartSelect)


def getPhysicalPortSubPortIDs(physicalPortID: str) -> list[str]:
    """Return physical subport handles in hierarchical path order.

    Args:
        physicalPortID: Handle to a physicalPort child.

    Returns:
        Handles in source order, including repeated path names; an empty list when absent.

    Section: F.7.69.6.
    """
    physical = _require(physicalPortID, _PhysicalPort)
    _register_graph(physical)
    return [get_handle(item) for item in physical.sub_port]


def getPortMapIsInformative(portMapID: str) -> bool:
    """Return the isInformative flag, defaulting to False when omitted.

    Args:
        portMapID: Handle to a portMap element.

    Returns:
        Stored Boolean, or False when the optional element is absent.

    Section: F.7.69.7.
    """
    value = _require(portMapID, _PortMap).is_informative
    return False if value is None else value


def getPortMapLogicalPortID(portMapID: str) -> str:
    """Return the owned logicalPort handle of a port map.

    Args:
        portMapID: Handle to a portMap element.

    Returns:
        Owned logicalPort handle. Missing required content faults INVALID_ID.

    Section: F.7.69.8.
    """
    handle = _child_id(_require(portMapID, _PortMap), "logical_port", _LogicalPort)
    if handle is None:
        raise TgiError("Port map lacks required logicalPort", TgiFaultCode.INVALID_ID)
    return handle


def getPortMapLogicalTieOff(portMapID: str) -> int | None:
    """Return the evaluated unsigned logical tie-off value.

    Args:
        portMapID: Handle to a portMap element.

    Returns:
        Unsigned integer within the TGI Long range, or None for a physical mapping.
        Unresolved expressions and values exceeding signed 64-bit bounds fault.

    Section: F.7.69.9.
    """
    value = _child(_require(portMapID, _PortMap), _CHOICE, UnsignedBitVectorExpression)
    return _integer(value.value, (1 << 63) - 1) if value is not None else None


def getPortMapLogicalTieOffExpression(portMapID: str) -> str | None:
    """Return the exact logical tie-off expression source.

    Args:
        portMapID: Handle to a portMap element.

    Returns:
        Exact stored source, or None for a physical mapping.

    Section: F.7.69.10.
    """
    value = _child(_require(portMapID, _PortMap), _CHOICE, UnsignedBitVectorExpression)
    return value.value if value is not None else None


def getPortMapLogicalTieOffID(portMapID: str) -> str | None:
    """Return the owned logical tie-off expression handle.

    Args:
        portMapID: Handle to a portMap element.

    Returns:
        Owned child handle, or None when optional content or the matching choice is absent.

    Section: F.7.69.11.
    """
    return _child_id(_require(portMapID, _PortMap), _CHOICE, UnsignedBitVectorExpression)


def getPortMapPhysicalPortID(portMapID: str) -> str | None:
    """Return the physicalPort handle when the physical mapping choice is selected.

    Args:
        portMapID: Handle to a portMap element.

    Returns:
        Owned child handle, or None when optional content or the matching choice is absent.

    Section: F.7.69.12.
    """
    return _child_id(_require(portMapID, _PortMap), _CHOICE, _PhysicalPort)


# ---------------------------------------------------------------------------
# EXTENDED functions (F.7.70)
# ---------------------------------------------------------------------------


def addPhysicalPortSubPort(physicalPortID: str, name: str) -> str:
    """Append a subport name to the physical port hierarchical path.

    Args:
        physicalPortID: Handle to a physicalPort child.
        name: Physical subport portName to append to the hierarchical path.

    Returns:
        Handle to the owned generated child.

    Section: F.7.70.1.
    """
    physical = _require(physicalPortID, _PhysicalPort)
    name = _name(name, "portName")
    child = _SubPort(name=name)
    _list_attr(physical, "sub_port").append(child)
    register_parent(child, physical, ("sub_port",), "list")
    return get_handle(child)


def addPortMapPhysicalPortSubPort(portMapID: str, name: str) -> str:
    """Append a subport through the existing physical mapping choice.

    Args:
        portMapID: Handle to a portMap element.
        name: Physical subport portName to append to the hierarchical path.

    Returns:
        Handle to the owned generated child.

    Section: F.7.70.2.
    """
    physical_id = getPortMapPhysicalPortID(portMapID)
    if physical_id is None:
        raise TgiError("Port map has no physicalPort", TgiFaultCode.INVALID_ARGUMENT)
    return addPhysicalPortSubPort(physical_id, name)


def removePhysicalPortPartSelect(physicalPortID: str) -> bool:
    """Remove a physical part select and invalidate its descendant handles.

    Args:
        physicalPortID: Handle to a physicalPort child.

    Returns:
        True if removed; False if optional content is absent. Invalid or unowned handles fault.

    Section: F.7.70.3.
    """
    return _remove_child(_require(physicalPortID, _PhysicalPort), "part_select")


def removePhysicalPortSubPort(subPortID: str) -> bool:
    """Remove an owned physical subport and invalidate its descendant handles.

    Args:
        subPortID: Handle to a subPort of a physicalPort.

    Returns:
        True if the owned child is removed; False for inconsistent ownership.
        Invalid or unowned handles fault.

    Section: F.7.70.4.
    """
    child = _require(subPortID, _SubPort)
    owner = _register_owned_child(child, _PhysicalPort)
    if owner is None:
        raise TgiError("Subport has no owning physicalPort", TgiFaultCode.INVALID_ID)
    _list_attr(owner, "sub_port")
    _register_graph(owner)
    return detach_child_by_handle(subPortID)


def removePortMapIsInformative(portMapID: str) -> bool:
    """Remove the explicit isInformative flag, restoring its default.

    Args:
        portMapID: Handle to a portMap element.

    Returns:
        True if removed; False if optional content is absent. Invalid or unowned handles fault.

    Section: F.7.70.5.
    """
    port_map = _require(portMapID, _PortMap)
    if port_map.is_informative is None:
        return False
    port_map.is_informative = None
    return True


def setAbstractionTypeAbstractionRef(abstractionTypeID: str, vlnv: Sequence[str]) -> bool:
    """Set the typed abstraction reference while preserving overrides and metadata.

    Args:
        abstractionTypeID: Handle to an abstractionType element.
        vlnv: Vendor/library XML Names followed by name/version NMTOKENs.

    Returns:
        True on success. Invalid arguments raise INVALID_ARGUMENT before mutation.

    Section: F.7.70.6.
    """
    abstraction = _require(abstractionTypeID, AbstractionTypes.AbstractionType)
    values = _array(vlnv, "vlnv")
    if len(values) != 4:
        raise TgiError("vlnv requires four attributes", TgiFaultCode.INVALID_ARGUMENT)
    values = [_name(value, "Name" if i < 2 else "NMTOKEN") for i, value in enumerate(values)]
    current = abstraction.abstraction_ref
    if current is not None and not isinstance(current, ConfigurableLibraryRefType):
        raise TgiError("Invalid abstractionRef model", TgiFaultCode.INVALID_ID)
    if current is None:
        current = ConfigurableLibraryRefType(vendor=values[0], library=values[1], name=values[2], version=values[3])
        abstraction.abstraction_ref = current
    else:
        current.vendor, current.library, current.name, current.version = values
    register_parent(current, abstraction, ("abstraction_ref",), "single")
    _register_graph(current)
    return True


def setLogicalPortRange(logicalPortID: str, range: Sequence[str]) -> bool:
    """Set logical range sources atomically while preserving expression wrappers.

    Args:
        logicalPortID: Handle to a logicalPort child.
        range: Exactly two unsigned 32-bit expression sources [left, right].

    Returns:
        True on success. Invalid arguments raise INVALID_ARGUMENT before mutation.

    Section: F.7.70.7.
    """
    logical = _require(logicalPortID, _LogicalPort)
    current = logical.range
    values = _range_plan(range, current)
    logical.range = _apply_range(current, values)
    register_parent(logical.range, logical, ("range",), "single")
    _register_graph(logical.range)
    return True


def setPhysicalPortPartSelect(physicalPortID: str, range: Sequence[str] | None, indices: Sequence[str] | None) -> bool:
    """Set a physical part select with a range, indices, or both in schema order.

    Args:
        physicalPortID: Handle to a physicalPort child.
        range: Two unsigned 32-bit expression sources [left, right]; None omits the range in a part select.
        indices: Unsigned 32-bit index expression sources in order; None or an empty sequence omits indices.

    Returns:
        True on success. Invalid arguments raise INVALID_ARGUMENT before mutation.

    Section: F.7.70.8.
    """
    _set_part_select(_require(physicalPortID, _PhysicalPort), range, indices)
    return True


def setPortMapIsInformative(portMapID: str, value: bool) -> bool:
    """Set the explicit Boolean isInformative flag.

    Args:
        portMapID: Handle to a portMap element.
        value: Boolean isInformative value.

    Returns:
        True on success. Invalid arguments raise INVALID_ARGUMENT before mutation.

    Section: F.7.70.9.
    """
    port_map = _require(portMapID, _PortMap)
    if type(value) is not bool:
        raise TgiError("value must be Boolean", TgiFaultCode.INVALID_ARGUMENT)
    port_map.is_informative = value
    return True


def setPortMapLogicalPort(portMapID: str, name: str) -> bool:
    """Set the logical port name while preserving its range and handle.

    Args:
        portMapID: Handle to a portMap element.
        name: XML Name of the logical port in the abstraction definition.

    Returns:
        True on success. Invalid arguments raise INVALID_ARGUMENT before mutation.

    Section: F.7.70.10.
    """
    port_map = _require(portMapID, _PortMap)
    name = _name(name, "Name")
    current = port_map.logical_port
    if current is None:
        port_map.logical_port = _LogicalPort(name=name)
    elif isinstance(current, _LogicalPort):
        current.name = name
    else:
        raise TgiError("Invalid logicalPort model", TgiFaultCode.INVALID_ID)
    register_parent(port_map.logical_port, port_map, ("logical_port",), "single")
    _register_graph(port_map.logical_port)
    return True


def setPortMapLogicalTieOff(portMapID: str, expression: str) -> bool:
    """Set the logical tie-off source, replacing any physical mapping choice.

    Args:
        portMapID: Handle to a portMap element.
        expression: Unsigned bit-vector expression source; symbolic names remain unresolved.

    Returns:
        True on success. Invalid arguments raise INVALID_ARGUMENT before mutation.

    Section: F.7.70.11.
    """
    port_map = _require(portMapID, _PortMap)
    current = _child(port_map, _CHOICE, UnsignedBitVectorExpression)
    expression = _source(expression, current, None)
    if current is None:
        _replace_choice(port_map, UnsignedBitVectorExpression(value=expression))
    else:
        current.value = expression
    return True


def setPortMapPhysicalPort(portMapID: str, name: str) -> bool:
    """Set the physical port name, replacing any logical tie-off choice.

    Args:
        portMapID: Handle to a portMap element.
        name: portName of the physical component port.

    Returns:
        True on success. Invalid arguments raise INVALID_ARGUMENT before mutation.

    Section: F.7.70.12.
    """
    port_map = _require(portMapID, _PortMap)
    name = _name(name, "portName")
    current = _child(port_map, _CHOICE, _PhysicalPort)
    if current is None:
        _replace_choice(port_map, _PhysicalPort(name=name))
    else:
        current.name = name
    return True


def setSubPortMapPartSelect(subPortID: str, range: Sequence[str] | None, indices: Sequence[str] | None) -> str:
    """Set an owned subport part select and return its stable handle.

    Args:
        subPortID: Handle to a subPort of a physicalPort.
        range: Two unsigned 32-bit expression sources [left, right]; None omits the range in a part select.
        indices: Unsigned 32-bit index expression sources in order; None or an empty sequence omits indices.

    Returns:
        Handle to the owned generated child.

    Section: F.7.70.13.
    """
    return _set_part_select(_require(subPortID, _SubPort), range, indices)
