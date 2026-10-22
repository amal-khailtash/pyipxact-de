"""IEEE 1685-2022 Bus Interface TGI operations.

This category implements the 53 BASE getters in Annex F.7.19 and the 55
EXTENDED edits in F.7.20 over the generated 2022 schema bindings. A bus
interface has one required interface-mode choice; its target, abstraction,
address-space, channel, remap, and file-set subtrees are represented by typed
xsdata objects. Numeric getters evaluate self-contained SystemVerilog
expressions while paired Expression and ID operations expose raw source and
child handles. Setters preserve expression wrappers and their bounds, and
removals invalidate the removed element and owned descendants.

Nested handles use the TGI handle manager and owner paths. The VLNV registry
contains only top-level IP-XACT documents; references resolve to registered
BusDefinition or AbstractionDefinition roots or to name-matched children in
the owning Component. Legacy convenience operations from the earlier partial
module remain exported after the numbered standard functions.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from org.accellera.ipxact.v1685_2022 import (
    AbstractionDefinition,
    BusDefinition,
    ComponentType,
)

from ._attribute_references import _root_for
from .bus_definition import removeBusDefinitionSystemGroupName
from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
    vlnv_to_tuple,
)

# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _fail(message: str, fault: str = TgiFaultCode.INVALID_ID) -> None:
    raise TgiError(message, fault)


def _resolve(handle: str, expected: str | tuple[str, ...] | None = None) -> Any:
    obj = resolve_handle(handle) if isinstance(handle, str) else None
    if obj is None:
        _fail("Invalid TGI handle")
    if expected is not None:
        expected_names = (expected,) if isinstance(expected, str) else expected
        expected_classes = tuple(
            cls for expected_name in expected_names for cls in _generated_type_map().get(expected_name, ())
        )
        if not expected_classes or not isinstance(obj, expected_classes):
            _fail("Invalid TGI handle")
    root = _root_for(obj)
    if root is not None:
        _register_graph(root)
    else:
        _register_graph(obj)
    return obj


def _register_graph(root: Any) -> None:
    """Register ownership paths for generated children without registry entries."""
    pending = [(root, None, None, "single")]
    seen: set[int] = set()
    while pending:
        obj, parent, attr, container = pending.pop()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        if parent is not None and attr is not None:
            register_parent(obj, parent, (attr,), container)
        if not is_dataclass(obj) or isinstance(obj, type):
            continue
        for item in fields(obj):
            value = getattr(obj, item.name)
            if is_dataclass(value) and not isinstance(value, type):
                pending.append((value, obj, item.name, "single"))
            elif isinstance(value, (list, tuple)):
                for child in value:
                    if is_dataclass(child) and not isinstance(child, type):
                        pending.append((child, obj, item.name, "list"))


def _path(obj: Any, path: str) -> Any:
    current = obj
    if path:
        for name in path.split("."):
            current = getattr(current, name, None)
            if current is None:
                break
    return current


def _list(obj: Any, path: str) -> list[Any]:
    value = _path(obj, path)
    return list(value) if isinstance(value, (list, tuple)) else []


def _child_handle(obj: Any, path: str) -> str | None:
    child = _path(obj, path)
    return get_handle(child) if child is not None else None


def _reference_tuple(ref: Any) -> tuple[str | None, str | None, str | None, str | None]:
    if ref is None:
        return (None, None, None, None)
    return tuple(getattr(ref, part, None) for part in ("vendor", "library", "name", "version"))  # type: ignore[return-value]


def _resolve_vlnv(ref: Any, target_type: type, label: str) -> str | None:
    if ref is None:
        return None
    vlnv = _reference_tuple(ref)
    target_id = registry.get_id(vlnv) if all(isinstance(part, str) and part for part in vlnv) else None
    target = resolve_handle(target_id) if target_id else None
    if target is None or not isinstance(target, target_type):
        _fail(f"Referenced {label} {vlnv!r} is unavailable", TgiFaultCode.NOT_FOUND)
    return get_handle(target)


def _mode_name(mode: Any) -> str | None:
    value = getattr(mode, "value", mode)
    return value if isinstance(value, str) else None


def _component_for(obj: Any) -> ComponentType:
    root = _root_for(obj)
    if not isinstance(root, ComponentType):
        _fail("Owning component is unavailable", TgiFaultCode.NOT_FOUND)
    _register_graph(root)
    return root


def _named_target(source: Any, collection: str, child_name: str, sought: str) -> Any | None:
    component = _component_for(source)
    matches = [item for item in _list(component, collection) if getattr(item, child_name, None) == sought]
    if len(matches) > 1:
        _fail(f"Ambiguous {collection} reference {sought!r}", TgiFaultCode.INVALID_ARGUMENT)
    if not matches:
        _fail(f"No {collection} target named {sought!r}", TgiFaultCode.NOT_FOUND)
    return matches[0]


def _eval_int(source: Any) -> int | None:
    if not isinstance(source, str) or not source.strip():
        return None
    try:
        try:
            return int(source, 10) if source.strip().lstrip("+-").isdigit() else int(source, 0)
        except ValueError:
            pass
        from amal.eda.systemverilog.expression_parser import SvExpressionParser

        value = SvExpressionParser().evaluate(source)
        return value if type(value) is int else None
    except ImportError, ValueError, TypeError, AttributeError:
        return None


def _checked_expression(value: str, argument: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{argument} must be a non-empty expression", TgiFaultCode.INVALID_ARGUMENT)
    evaluated = _eval_int(value)
    if evaluated is not None and not minimum <= evaluated <= maximum:
        _fail(f"{argument} is outside its IEEE 1685-2022 range", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _replace_child(parent: Any, attr: str, value: Any) -> None:
    old = getattr(parent, attr, None)
    if old is not None:
        _register_graph(parent)
        register_parent(old, parent, (attr,), "single")
        old_id = get_handle(old)
        if not detach_child_by_handle(old_id):
            setattr(parent, attr, None)
    setattr(parent, attr, value)
    if value is not None:
        register_parent(value, parent, (attr,), "single")
        _register_graph(value)


def _set_expression(parent: Any, attr: str, cls: type, text: str, argument: str, minimum: int, maximum: int) -> None:
    text = _checked_expression(text, argument, minimum, maximum)
    current = getattr(parent, attr, None)
    if current is not None and not isinstance(current, cls):
        _fail(f"Invalid {attr} model on parent")
    if current is not None:
        if getattr(current, "minimum", None) is not None:
            minimum = max(minimum, current.minimum)
        if getattr(current, "maximum", None) is not None:
            maximum = min(maximum, current.maximum)
        text = _checked_expression(text, argument, minimum, maximum)
    if current is None:
        current = cls(value=text)
        setattr(parent, attr, current)
        register_parent(current, parent, (attr,), "single")
    else:
        current.value = text
    _register_graph(current)


def _remove_attr(parent: Any, attr: str) -> bool:
    current = getattr(parent, attr, None)
    if current is None:
        return False
    _replace_child(parent, attr, None)
    return True


def _get_value(handle: str, expected: str, path: str, mode: str, default: Any = None) -> Any:
    obj = _resolve(handle, expected)
    value = _path(obj, path)
    if mode == "handle":
        return get_handle(value) if value is not None else None
    if mode == "expression":
        return getattr(value, "value", None) if value is not None else None
    if mode == "numeric":
        if value is None:
            return default
        result = _eval_int(getattr(value, "value", None))
        if result is None:
            return None
        return result
    if mode == "boolean":
        if value is None:
            return bool(default)
        result = _eval_int(getattr(value, "value", None))
        return bool(result) if result in (0, 1) else None
    if mode == "text":
        if value is None:
            return default
        if isinstance(value, Enum):
            return value.value
        return getattr(value, "value", value)
    if mode == "ids":
        items = _list(obj, path)
        return [get_handle(item) for item in items]
    if mode == "names":
        return [name for item in _list(obj, path) if (name := _mode_name(item)) is not None]
    _fail(f"Unsupported getter mode {mode}", TgiFaultCode.INTERNAL_ERROR)


def _get_mode_id(source_handle: str, expected: str, path: str, mode_ref: str) -> str | None:
    source = _resolve(source_handle, expected)
    items = _list(source, path)
    matches = [item for item in items if _mode_name(item) == mode_ref]
    if not matches:
        _fail(f"No mode reference named {mode_ref!r}", TgiFaultCode.NOT_FOUND)
    if len(matches) > 1:
        _fail(f"Ambiguous mode reference {mode_ref!r}", TgiFaultCode.INVALID_ARGUMENT)
    return get_handle(_named_target(source, "modes.mode", "name", mode_ref))


def _base(name: str, args: dict[str, Any]) -> Any:
    if name == "getAbstractionTypeAbstractionRefByVLNV":
        obj = _resolve(args["abstractionTypeID"], "AbstractionType")
        return _reference_tuple(obj.abstraction_ref)
    if name == "getAbstractionTypeAbstractionRefByID":
        obj = _resolve(args["abstractionTypeID"], "AbstractionType")
        return _resolve_vlnv(obj.abstraction_ref, AbstractionDefinition, "abstraction definition")
    if name == "getAbstractionTypeViewRefByNames":
        obj = _resolve(args["abstractionTypeID"], "AbstractionType")
        return [ref.value for ref in obj.view_ref]
    if name == "getAbstractionTypeViewRefByID":
        obj = _resolve(args["abstractionTypeID"], "AbstractionType")
        view_ref = _resolve(args["viewRef"], "ViewRef")
        if not any(candidate is view_ref for candidate in obj.view_ref):
            _fail("viewRef handle is not owned by this abstractionType", TgiFaultCode.INVALID_ARGUMENT)
        return get_handle(_named_target(obj, "model.views.view", "name", view_ref.value))
    if name == "getRemapAddressModeRefByID":
        remap = _resolve(args["remapAddressID"], ("UnsignedLongintExpression",))
        info = get_parent_info(get_handle(remap))
        record = resolve_handle(info.parent_handle) if info is not None else None
        if record is None or type(record).__name__ != "RemapAddresses":
            _fail("remapAddress is not attached to a remapAddresses record")
        modes = list(getattr(record, "mode_ref", []))
        if not modes:
            return None
        if len(modes) > 1:
            _fail("remapAddress record has multiple modeRefs", TgiFaultCode.INVALID_ARGUMENT)
        return get_handle(_named_target(record, "modes.mode", "name", modes[0].value))
    if name == "getChannelBusInterfaceRefByID":
        ref = _resolve(args["busInterfaceRefID"], "BusInterfaceRef")
        return get_handle(_named_target(ref, "bus_interfaces.bus_interface", "name", ref.local_name))
    if name == "getBusInterfaceBusTypeRefByVLNV":
        bi = _resolve(args["busInterfaceID"], "BusInterface")
        return _reference_tuple(bi.bus_type)
    if name == "getBusInterfaceBusTypeRefByID":
        bi = _resolve(args["busInterfaceID"], "BusInterface")
        return _resolve_vlnv(bi.bus_type, BusDefinition, "bus definition")
    if name == "getBusInterfaceInterfaceMode":
        bi = _resolve(args["busInterfaceID"], "BusInterface")
        if bi.choice is None:
            return None
        if (
            getattr(bi.choice, "qname", None)
            == "{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}mirroredInitiator"
        ):
            return "mirroredInitiator"
        return type(bi.choice).__name__[0].lower() + type(bi.choice).__name__[1:]
    if name == "getInitiatorAddressSpaceRefByName":
        initiator = _resolve(args["initiatorID"], "Initiator")
        ref = initiator.address_space_ref
        return ref.address_space_ref if ref is not None else None
    if name == "getAddressSpaceRefModeRefByID":
        return _get_mode_id(args["addressSpaceRefID"], "AddressSpaceRef", "mode_ref", args["modeRef"])
    if name == "getMemoryMapRefModeRefByID":
        return _get_mode_id(args["memoryMapRefID"], "MemoryMapRef", "mode_ref", args["modeRef"])
    if name == "getTargetMemoryMapRefByName":
        target = _resolve(args["targetID"], "Target")
        for value in target.memory_map_ref_or_transparent_bridge:
            if type(value).__name__ == "MemoryMapRef":
                return value.memory_map_ref
        return None
    if name == "getBusInterfaceConnectionRequired":
        bi = _resolve(args["busInterfaceID"], "BusInterface")
        return False if bi.connection_required is None else bi.connection_required
    if name == "getBusInterfaceEndianness":
        bi = _resolve(args["busInterfaceID"], "BusInterface")
        return bi.endianness.value if bi.endianness is not None else "little"

    desc = _BASE_GETTERS.get(name)
    if desc is None:
        _fail(f"Unimplemented BASE function {name}", TgiFaultCode.INTERNAL_ERROR)
    expected, path, mode, default = desc
    value = _get_value(args[next(iter(args))], expected, path, mode, default)
    if mode == "numeric" and value is not None:
        minimum, maximum = _NUMERIC_BOUNDS[name]
        if not minimum <= value <= maximum:
            return None
    if mode == "boolean" and value is not None and type(value) is not bool:
        return None
    return value


_BASE_GETTERS: dict[str, tuple[str, str, str, Any]] = {
    "getAbstractionTypePortMapIDs": ("AbstractionType", "port_maps.port_map", "ids", None),
    "getAbstractionTypeViewRefIDs": ("AbstractionType", "view_ref", "ids", None),
    "getAddressSpaceRefBaseAddress": ("AddressSpaceRef", "base_address", "numeric", 0),
    "getAddressSpaceRefBaseAddressExpression": ("AddressSpaceRef", "base_address", "expression", None),
    "getAddressSpaceRefBaseAddressID": ("AddressSpaceRef", "base_address", "handle", None),
    "getAddressSpaceRefModeRefByNames": ("AddressSpaceRef", "mode_ref", "names", None),
    "getBaseAddressesRange": ("BaseAddresses", "range", "numeric", None),
    "getBaseAddressesRangeExpression": ("BaseAddresses", "range", "expression", None),
    "getBaseAddressesRangeID": ("BaseAddresses", "range", "handle", None),
    "getBaseAddressesRemapAddressIDs": ("BaseAddresses", "remap_addresses", "ids", None),
    "getBusInterfaceAbstractionTypeIDs": ("BusInterface", "abstraction_types.abstraction_type", "ids", None),
    "getBusInterfaceBitSteering": ("BusInterface", "bit_steering", "boolean", 0),
    "getBusInterfaceBitSteeringExpression": ("BusInterface", "bit_steering", "expression", None),
    "getBusInterfaceBitSteeringID": ("BusInterface", "bit_steering", "handle", None),
    "getBusInterfaceBitsInLau": ("BusInterface", "bits_in_lau", "numeric", 8),
    "getBusInterfaceBitsInLauExpression": ("BusInterface", "bits_in_lau", "expression", None),
    "getBusInterfaceBitsInLauID": ("BusInterface", "bits_in_lau", "handle", None),
    "getBusInterfaceBusTypeID": ("BusInterface", "bus_type", "handle", None),
    "getBusInterfaceInitiatorID": ("BusInterface", "choice", "choice_id:Initiator", None),
    "getBusInterfaceMirroredSystemID": ("BusInterface", "choice", "choice_id:MirroredSystem", None),
    "getBusInterfaceMirroredTargetID": ("BusInterface", "choice", "choice_id:MirroredTarget", None),
    "getBusInterfaceMonitorID": ("BusInterface", "choice", "choice_id:Monitor", None),
    "getBusInterfaceSystemID": ("BusInterface", "choice", "choice_id:System", None),
    "getBusInterfaceTargetID": ("BusInterface", "choice", "choice_id:Target", None),
    "getBusInterfaceRefLocalName": ("BusInterfaceRef", "local_name", "text", None),
    "getChannelBusInterfaceRefIDs": ("Channel", "bus_interface_ref", "ids", None),
    "getFileSetRefGroupGroup": ("FileSetRefGroup", "group", "text", None),
    "getIndirectInterfaceBitsInLauID": ("IndirectInterfaceType", "bits_in_lau", "handle", None),
    "getInitiatorAddressSpaceRefID": ("Initiator", "address_space_ref", "handle", None),
    "getMemoryMapRefModeRefByNames": ("MemoryMapRef", "mode_ref", "names", None),
    "getMirroredSystemGroup": ("MirroredSystem", "group", "text", None),
    "getMirroredTargetBaseAddressesID": ("MirroredTarget", "base_addresses", "handle", None),
    "getMonitorGroup": ("Monitor", "group", "text", None),
    "getRemapAddressesRemapAddressID": ("RemapAddresses", "remap_address", "handle", None),
    "getSystemGroup": ("System", "group", "text", None),
    "getTargetFileSetRefGroupIDs": ("Target", "file_set_ref_group", "ids", None),
    "getTargetMemoryMapRefID": ("Target", "memory_map_ref_or_transparent_bridge", "choice_list_id:MemoryMapRef", None),
    "getTargetTransparentBridgeIDs": (
        "Target",
        "memory_map_ref_or_transparent_bridge",
        "choice_ids:TransparentBridge",
        None,
    ),
}

_NUMERIC_BOUNDS: dict[str, tuple[int, int]] = {
    "getAddressSpaceRefBaseAddress": (-(1 << 63), (1 << 63) - 1),
    "getBaseAddressesRange": (1, (1 << 64) - 1),
    "getBusInterfaceBitsInLau": (1, (1 << 64) - 1),
}


def _base_apply(name: str, args: dict[str, Any]) -> Any:
    if name in _BASE_GETTERS:
        expected, path, mode, default = _BASE_GETTERS[name]
        source = _resolve(args[next(iter(args))], expected)
        if mode.startswith("choice_list_id:"):
            wanted = mode.split(":", 1)[1]
            matches = [item for item in _list(source, path) if _is_expected(item, wanted)]
            if len(matches) > 1:
                _fail("Multiple memory-map references on one target", TgiFaultCode.INVALID_ARGUMENT)
            return get_handle(matches[0]) if matches else None
        if mode.startswith("choice_id:"):
            wanted = mode.split(":", 1)[1]
            choice = getattr(source, "choice", None)
            return get_handle(choice) if choice is not None and type(choice).__name__ == wanted else None
        if mode.startswith("choice_ids:"):
            wanted = mode.split(":", 1)[1]
            return [get_handle(item) for item in _list(source, path) if type(item).__name__ == wanted]
        value = _get_value(args[next(iter(args))], expected, path, mode, default)
        if mode == "numeric" and value is not None:
            minimum, maximum = _NUMERIC_BOUNDS[name]
            return value if minimum <= value <= maximum else None
        return value
    return _base(name, args)


def _mode_ref_value(value: Any) -> str | None:
    return getattr(value, "value", None) if value is not None else None


def _spec_call(name: str, args: dict[str, Any]) -> Any:
    if name.startswith("get"):
        return _base_apply(name, args)
    return _extended(name, args)


# ---------------------------------------------------------------------------


# Compatibility functions from the original partial category module.


# The standard setter keeps its original public spelling and exact signature.


# ---------------------------------------------------------------------------
# EXTENDED (F.7.20)
# ---------------------------------------------------------------------------


def _validated_name(value: Any, argument: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{argument} must be a non-empty xs:Name", TgiFaultCode.INVALID_ARGUMENT)
    from unicodedata import category

    def start(ch: str) -> bool:
        return ch in ":_" or category(ch) in {"Lu", "Ll", "Lt", "Lm", "Lo", "Nl"}

    def part(ch: str) -> bool:
        return start(ch) or ch in "-." or category(ch) in {"Mn", "Mc", "Nd", "Pc"}

    if not start(value[0]) or any(not part(ch) for ch in value[1:]):
        _fail(f"{argument} must be a valid xs:Name", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _validated_vlnv(value: Sequence[str] | str, argument: str) -> tuple[str, str, str, str]:
    try:
        parts = vlnv_to_tuple(value)
    except TypeError, ValueError:
        _fail(f"{argument} must be a four-part VLNV", TgiFaultCode.INVALID_ARGUMENT)
    if any(not isinstance(part, str) or not part.strip() for part in parts):
        _fail(f"{argument} requires four non-empty VLNV strings", TgiFaultCode.INVALID_ARGUMENT)
    return parts


def _expect_object(handle: str, name: str) -> Any:
    return _resolve(handle, name)


def _add_list(parent: Any, attr: str, item: Any) -> str:
    values = getattr(parent, attr, None)
    if values is None:
        values = []
        setattr(parent, attr, values)
    if not isinstance(values, list):
        _fail(f"Invalid {attr} list on model", TgiFaultCode.INVALID_ID)
    values.append(item)
    register_parent(item, parent, (attr,), "list")
    _register_graph(item)
    return get_handle(item)


def _remove_item(
    handle: str,
    expected: str,
    minimum: int = 0,
    parent_expected: str | None = None,
    parent_attr: str | None = None,
    container: str | None = None,
) -> bool:
    _resolve(handle, expected)
    info = get_parent_info(handle)
    if info is None:
        return False
    if parent_attr is not None and (info.path != (parent_attr,)):
        _fail("Object handle is not owned through the expected schema field", TgiFaultCode.INVALID_ID)
    if container is not None and info.container != container:
        _fail("Object handle is not in the expected schema container", TgiFaultCode.INVALID_ID)
    parent = resolve_handle(info.parent_handle)
    if parent is None:
        return False
    if parent_expected is not None and not _is_expected(parent, parent_expected):
        _fail("Object handle has an unexpected schema parent", TgiFaultCode.INVALID_ID)
    if info.container == "list" and len(getattr(parent, info.path[-1], [])) <= minimum:
        return False
    return detach_child_by_handle(handle)


def _is_expected(obj: Any, expected: str) -> bool:
    """Check generated model class identity for a schema-local type name."""
    types = _generated_type_map().get(expected, ())
    return bool(types) and isinstance(obj, types)


def _generated_type_map() -> dict[str, tuple[type, ...]]:
    from org.accellera.ipxact.v1685_2022.abstraction_types import AbstractionTypes
    from org.accellera.ipxact.v1685_2022.bits_in_lau import BitsInLau
    from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType
    from org.accellera.ipxact.v1685_2022.channels import Channels
    from org.accellera.ipxact.v1685_2022.file_set_ref import FileSetRef
    from org.accellera.ipxact.v1685_2022.indirect_interface import IndirectInterface
    from org.accellera.ipxact.v1685_2022.indirect_interface_type import IndirectInterfaceType
    from org.accellera.ipxact.v1685_2022.memory_map_ref import MemoryMapRef
    from org.accellera.ipxact.v1685_2022.memory_map_ref_type import MemoryMapRefType
    from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
    from org.accellera.ipxact.v1685_2022.signed_longint_expression import SignedLongintExpression
    from org.accellera.ipxact.v1685_2022.transparent_bridge import TransparentBridge
    from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression
    from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
    from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import (
        UnsignedPositiveLongintExpression,
    )
    from org.accellera.ipxact.v1685_2022.view_ref import ViewRef

    return {
        "AbstractionType": (AbstractionTypes.AbstractionType,),
        "AddressSpaceRef": (BusInterfaceType.Initiator.AddressSpaceRef,),
        "BaseAddresses": (BusInterfaceType.MirroredTarget.BaseAddresses,),
        "BusInterface": (BusInterfaceType,),
        "BusInterfaceRef": (Channels.Channel.BusInterfaceRef,),
        "Channel": (Channels.Channel,),
        "FileSetRef": (FileSetRef,),
        "FileSetRefGroup": (BusInterfaceType.Target.FileSetRefGroup,),
        "IndirectInterface": (IndirectInterface,),
        "IndirectInterfaceType": (IndirectInterfaceType, IndirectInterface),
        "Initiator": (BusInterfaceType.Initiator,),
        "MemoryMapRef": (MemoryMapRef,),
        "ModeRef": (
            BusInterfaceType.Initiator.AddressSpaceRef.ModeRef,
            MemoryMapRefType.ModeRef,
            ModeRef,
        ),
        "MirroredSystem": (BusInterfaceType.MirroredSystem,),
        "MirroredTarget": (BusInterfaceType.MirroredTarget,),
        "Monitor": (BusInterfaceType.Monitor,),
        "RemapAddresses": (BusInterfaceType.MirroredTarget.BaseAddresses.RemapAddresses,),
        "PortMap": (AbstractionTypes.AbstractionType.PortMaps.PortMap,),
        "BitsInLau": (BitsInLau,),
        "System": (BusInterfaceType.System,),
        "Target": (BusInterfaceType.Target,),
        "TransparentBridge": (TransparentBridge,),
        "UnsignedBitExpression": (UnsignedBitExpression,),
        "UnsignedLongintExpression": (UnsignedLongintExpression,),
        "UnsignedPositiveLongintExpression": (UnsignedPositiveLongintExpression,),
        "SignedLongintExpression": (SignedLongintExpression,),
        "ViewRef": (ViewRef,),
    }


def _set_group(parent: Any, attr: str, value: str) -> None:
    from org.accellera.ipxact.v1685_2022.group import Group

    current = getattr(parent, attr, None)
    if current is not None and not isinstance(current, Group):
        _fail(f"Invalid {attr} group model")
    if current is None:
        current = Group(value=value)
        setattr(parent, attr, current)
        register_parent(current, parent, (attr,), "single")
    else:
        current.value = value
    _register_graph(current)


def _set_choice(bi: Any, name: str, value: Any) -> Any:
    current = bi.choice
    if current is not None and type(current).__name__ == name:
        return current
    _replace_child(bi, "choice", value)
    return value


def _expression_plan(
    parent: Any, attr: str, cls: type, text: str, argument: str, minimum: int, maximum: int
) -> tuple[Any, str]:
    current = getattr(parent, attr, None)
    if current is not None and not isinstance(current, cls):
        _fail(f"Invalid {attr} model on parent")
    if current is not None:
        if current.minimum is not None:
            minimum = max(minimum, current.minimum)
        if current.maximum is not None:
            maximum = min(maximum, current.maximum)
    return current, _checked_expression(text, argument, minimum, maximum)


def _apply_expression(parent: Any, attr: str, cls: type, current: Any, text: str) -> None:
    if current is None:
        current = cls(value=text)
        setattr(parent, attr, current)
        register_parent(current, parent, (attr,), "single")
    else:
        current.value = text
    _register_graph(current)


def _mode_values(name: str) -> set[str]:
    return {"initiator", "target", "system", "mirroredInitiator", "mirroredTarget", "mirroredSystem"}


def _extended(name: str, args: dict[str, Any]) -> Any:
    from org.accellera.ipxact.v1685_2022.abstraction_types import AbstractionTypes
    from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType
    from org.accellera.ipxact.v1685_2022.channels import Channels
    from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
    from org.accellera.ipxact.v1685_2022.endianess_type import EndianessType
    from org.accellera.ipxact.v1685_2022.memory_map_ref import MemoryMapRef
    from org.accellera.ipxact.v1685_2022.memory_map_ref_type import MemoryMapRefType
    from org.accellera.ipxact.v1685_2022.signed_longint_expression import SignedLongintExpression
    from org.accellera.ipxact.v1685_2022.transparent_bridge import TransparentBridge
    from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression
    from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
    from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression

    if name == "addAbstractionTypePortMap":
        at = _expect_object(args["abstractionTypeID"], "AbstractionType")
        logical = _validated_name(args["logicalPortName"], "logicalPortName")
        physical = _validated_name(args["physicalPortName"], "physicalPortName")
        cls = AbstractionTypes.AbstractionType.PortMaps.PortMap
        port = cls(
            logical_port=cls.LogicalPort(name=logical),
            physical_port_or_logical_tie_off=cls.PhysicalPort(name=physical),
        )
        if at.port_maps is None:
            at.port_maps = AbstractionTypes.AbstractionType.PortMaps(port_map=[])
            register_parent(at.port_maps, at, ("port_maps",), "single")
        return _add_list(at.port_maps, "port_map", port)
    if name == "addAbstractionTypeViewRef":
        at = _expect_object(args["abstractionTypeID"], "AbstractionType")
        ref_name = _validated_name(args["viewRef"], "viewRef")
        if any(ref.value == ref_name for ref in at.view_ref):
            _fail("Duplicate viewRef in abstractionType", TgiFaultCode.ALREADY_EXISTS)
        from org.accellera.ipxact.v1685_2022.view_ref import ViewRef

        return _add_list(at, "view_ref", ViewRef(value=ref_name))
    if name == "addAddressSpaceRefModeRef":
        addr = _expect_object(args["addressSpaceRefID"], "AddressSpaceRef")
        value = _validated_name(args["modeRef"], "modeRef")
        if any(ref.value == value for ref in addr.mode_ref):
            _fail("Duplicate modeRef", TgiFaultCode.ALREADY_EXISTS)
        mode_cls = BusInterfaceType.Initiator.AddressSpaceRef.ModeRef
        return bool(_add_list(addr, "mode_ref", mode_cls(value=value)))
    if name == "addBaseAddressesRemapAddresses":
        base = _expect_object(args["baseAddressesID"], "BaseAddresses")
        source = _checked_expression(args["remapAddress"], "remapAddress", 0, (1 << 64) - 1)
        cls = BusInterfaceType.MirroredTarget.BaseAddresses.RemapAddresses
        item = cls(remap_address=UnsignedLongintExpression(value=source), mode_ref=[])
        result = _add_list(base, "remap_addresses", item)
        _register_graph(item.remap_address)
        register_parent(item.remap_address, item, ("remap_address",), "single")
        return result
    if name == "addBusInterfaceAbstractionType":
        bi = _expect_object(args["busInterfaceID"], "BusInterface")
        vlnv = _validated_vlnv(args["abstractionRef"], "abstractionRef")
        ref = ConfigurableLibraryRefType(vendor=vlnv[0], library=vlnv[1], name=vlnv[2], version=vlnv[3])
        at = AbstractionTypes.AbstractionType(abstraction_ref=ref, view_ref=[])
        if bi.abstraction_types is None:
            bi.abstraction_types = AbstractionTypes(abstraction_type=[])
            register_parent(bi.abstraction_types, bi, ("abstraction_types",), "single")
        return _add_list(bi.abstraction_types, "abstraction_type", at)
    if name == "addChannelBusInterfaceRef":
        channel = _expect_object(args["channelID"], "Channel")
        local_name = _validated_name(args["name"], "name")
        if any(ref.local_name == local_name for ref in channel.bus_interface_ref):
            _fail("Duplicate channel busInterfaceRef localName", TgiFaultCode.ALREADY_EXISTS)
        return _add_list(channel, "bus_interface_ref", Channels.Channel.BusInterfaceRef(local_name=local_name))
    if name == "addMemoryMapRefModeRef":
        ref = _expect_object(args["memoryMapRefID"], "MemoryMapRef")
        value = _validated_name(args["modeRef"], "modeRef")
        if any(item.value == value for item in ref.mode_ref):
            _fail("Duplicate modeRef", TgiFaultCode.ALREADY_EXISTS)
        cls = MemoryMapRefType.ModeRef
        return bool(_add_list(ref, "mode_ref", cls(value=value)))
    if name == "addTargetFileSetRefGroup":
        target = _expect_object(args["targetID"], "Target")
        return _add_list(target, "file_set_ref_group", BusInterfaceType.Target.FileSetRefGroup(file_set_ref=[]))
    if name == "addTargetTransparentBridge":
        target = _expect_object(args["targetID"], "Target")
        initiator = _validated_name(args["initiatorRef"], "initiatorRef")
        values = target.memory_map_ref_or_transparent_bridge
        for item in list(values):
            if isinstance(item, MemoryMapRef):
                register_parent(item, target, ("memory_map_ref_or_transparent_bridge",), "list")
                detach_child_by_handle(get_handle(item))
        bridge = TransparentBridge(initiator_ref=initiator)
        return _add_list(target, "memory_map_ref_or_transparent_bridge", bridge)

    if name == "removeAbstractionTypePortMap":
        port = _expect_object(args["portMapID"], "PortMap")
        info = get_parent_info(args["portMapID"])
        container = resolve_handle(info.parent_handle) if info else None
        if (
            info is None
            or info.path != ("port_map",)
            or info.container != "list"
            or not isinstance(container, AbstractionTypes.AbstractionType.PortMaps)
        ):
            _fail("portMap handle is not owned by an abstractionType portMaps list", TgiFaultCode.INVALID_ID)
        owner_info = get_parent_info(get_handle(container))
        owner = resolve_handle(owner_info.parent_handle) if owner_info is not None else None
        if (
            owner_info is None
            or owner_info.path != ("port_maps",)
            or owner_info.container != "single"
            or not isinstance(owner, AbstractionTypes.AbstractionType)
        ):
            _fail("portMap handle is not owned by an abstractionType", TgiFaultCode.INVALID_ID)
        removed = detach_child_by_handle(args["portMapID"])
        if (
            removed
            and container is not None
            and not container.port_map
            and (owner_info.path == ("port_maps",) and owner_info.container == "single")
        ):  # the validated owner is guaranteed by the preflight above
            detach_child_by_handle(get_handle(container))
        return removed
    if name == "removeAbstractionTypeViewRef":
        return _remove_item(
            args["viewRefID"], "ViewRef", parent_expected="AbstractionType", parent_attr="view_ref", container="list"
        )
    if name == "removeAddressSpaceRefBaseAddress":
        addr = _expect_object(args["addressSpaceRefID"], "AddressSpaceRef")
        return _remove_attr(addr, "base_address")
    if name == "removeAddressSpaceRefModeRef":
        addr = _expect_object(args["addressSpaceRefID"], "AddressSpaceRef")
        matches = [ref for ref in addr.mode_ref if ref.value == args["modeRef"]]
        if len(matches) > 1:
            _fail("Ambiguous modeRef", TgiFaultCode.INVALID_ARGUMENT)
        return (
            _remove_item(
                get_handle(matches[0]),
                "ModeRef",
                parent_expected="AddressSpaceRef",
                parent_attr="mode_ref",
                container="list",
            )
            if matches
            else False
        )
    if name == "removeBaseAddressesRemapAddresses":
        return _remove_item(
            args["remapAddressesID"],
            "RemapAddresses",
            minimum=1,
            parent_expected="BaseAddresses",
            parent_attr="remap_addresses",
            container="list",
        )
    if name == "removeBusInterfaceAbstractionType":
        at = _expect_object(args["abstractionTypeID"], "AbstractionType")
        info = get_parent_info(args["abstractionTypeID"])
        owner = resolve_handle(info.parent_handle) if info else None
        if (
            info is None
            or info.path != ("abstraction_type",)
            or info.container != "list"
            or not isinstance(owner, AbstractionTypes)
        ):
            _fail(
                "abstractionType handle is not owned by a busInterface abstractionTypes list", TgiFaultCode.INVALID_ID
            )
        owner_info = get_parent_info(get_handle(owner))
        bus_interface = resolve_handle(owner_info.parent_handle) if owner_info is not None else None
        if (
            owner_info is None
            or owner_info.path != ("abstraction_types",)
            or owner_info.container != "single"
            or not isinstance(bus_interface, BusInterfaceType)
        ):
            _fail("abstractionType handle is not owned by a busInterface", TgiFaultCode.INVALID_ID)
        removed = detach_child_by_handle(args["abstractionTypeID"])
        if (
            removed
            and owner is not None
            and not owner.abstraction_type
            and owner_info.path == ("abstraction_types",)
            and owner_info.container == "single"
        ):
            detach_child_by_handle(get_handle(owner))
        return removed
    if name == "removeBusInterfaceBitSteering":
        return _remove_attr(_expect_object(args["busInterfaceID"], "BusInterface"), "bit_steering")
    if name == "removeBusInterfaceBitsInLau":
        return _remove_attr(_expect_object(args["busInterfaceID"], "BusInterface"), "bits_in_lau")
    if name == "removeBusInterfaceConnectionRequired":
        return _remove_attr(_expect_object(args["busInterfaceID"], "BusInterface"), "connection_required")
    if name == "removeBusInterfaceEndianness":
        return _remove_attr(_expect_object(args["busInterfaceID"], "BusInterface"), "endianness")
    if name == "removeChannelBusInterfaceRef":
        _expect_object(args["busInterfaceRefID"], "BusInterfaceRef")
        info = get_parent_info(args["busInterfaceRefID"])
        channel = resolve_handle(info.parent_handle) if info else None
        if (
            info is None
            or info.path != ("bus_interface_ref",)
            or info.container != "list"
            or not isinstance(channel, Channels.Channel)
        ):
            _fail("busInterfaceRef handle is not owned by a channel", TgiFaultCode.INVALID_ID)
        if len(channel.bus_interface_ref) <= 2:
            return False
        return detach_child_by_handle(args["busInterfaceRefID"])
    if name == "removeFileSetRefGroupGroup":
        group = _expect_object(args["fileSetRefGroupID"], "FileSetRefGroup")
        existed = group.group is not None
        group.group = None
        return existed
    if name == "removeIndirectInterfaceBitsInLau":
        return _remove_attr(
            _expect_object(args["indirectInterfaceID"], ("IndirectInterface", "IndirectInterfaceType")), "bits_in_lau"
        )
    if name == "removeInitiatorAddressSpaceRef":
        return _remove_attr(_expect_object(args["initiatorID"], "Initiator"), "address_space_ref")
    if name == "removeMemoryMapRefModeRef":
        ref = _expect_object(args["memoryMapRefID"], "MemoryMapRef")
        matches = [item for item in ref.mode_ref if item.value == args["modeRef"]]
        if len(matches) > 1:
            _fail("Ambiguous modeRef", TgiFaultCode.INVALID_ARGUMENT)
        return (
            _remove_item(
                get_handle(matches[0]),
                "ModeRef",
                parent_expected="MemoryMapRef",
                parent_attr="mode_ref",
                container="list",
            )
            if matches
            else False
        )
    if name == "removeMirroredTargetBaseAddresses":
        return _remove_attr(_expect_object(args["mirroredTargetID"], "MirroredTarget"), "base_addresses")
    if name == "removeMonitorGroup":
        return _remove_attr(_expect_object(args["monitorID"], "Monitor"), "group")
    if name == "removeTargetFileSetRefGroup":
        return _remove_item(
            args["fileSetRefGroupID"],
            "FileSetRefGroup",
            parent_expected="Target",
            parent_attr="file_set_ref_group",
            container="list",
        )
    if name == "removeTargetMemoryMapRef":
        target = _expect_object(args["targetID"], "Target")
        for child in target.memory_map_ref_or_transparent_bridge:
            if isinstance(child, MemoryMapRef):
                child_handle = get_handle(child)
                register_parent(child, target, ("memory_map_ref_or_transparent_bridge",), "list")
                return detach_child_by_handle(child_handle)
        return False
    if name == "removeTargetTransparentBridge":
        return _remove_item(
            args["transparentBrigeID"],
            "TransparentBridge",
            parent_expected="Target",
            parent_attr="memory_map_ref_or_transparent_bridge",
            container="list",
        )

    if name == "setAddressSpaceRefBaseAddress":
        addr = _expect_object(args["addressSpaceRefID"], "AddressSpaceRef")
        _set_expression(
            addr, "base_address", SignedLongintExpression, args["baseAddress"], "baseAddress", -(1 << 63), (1 << 63) - 1
        )
        return True
    if name == "setBaseAddressesRange":
        base = _expect_object(args["baseAddressesID"], "BaseAddresses")
        _set_expression(base, "range", UnsignedPositiveLongintExpression, args["range"], "range", 1, (1 << 64) - 1)
        return True
    if name == "setBusInterfaceBitSteering":
        bi = _expect_object(args["busInterfaceID"], "BusInterface")
        _set_expression(bi, "bit_steering", UnsignedBitExpression, args["value"], "value", 0, 1)
        return True
    if name == "setBusInterfaceBitsInLau":
        bi = _expect_object(args["busInterfaceID"], "BusInterface")
        from org.accellera.ipxact.v1685_2022.bits_in_lau import BitsInLau

        _set_expression(bi, "bits_in_lau", BitsInLau, args["bitsInLau"], "bitsInLau", 1, (1 << 64) - 1)
        return True
    if name == "setBusInterfaceBusType":
        bi = _expect_object(args["busInterfaceID"], "BusInterface")
        parts = _validated_vlnv(args["vlnv"], "vlnv")
        current = bi.bus_type
        if current is None:
            current = ConfigurableLibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])
            bi.bus_type = current
            register_parent(current, bi, ("bus_type",), "single")
        elif isinstance(current, ConfigurableLibraryRefType):
            current.vendor, current.library, current.name, current.version = parts
        else:
            _fail("Invalid busType model")
        _register_graph(current)
        return True
    if name == "setBusInterfaceConnectionRequired":
        bi = _expect_object(args["busInterfaceID"], "BusInterface")
        if type(args["value"]) is not bool:
            _fail("value must be Boolean", TgiFaultCode.INVALID_ARGUMENT)
        bi.connection_required = args["value"]
        return True
    if name == "setBusInterfaceEndianness":
        bi = _expect_object(args["busInterfaceID"], "BusInterface")
        value = args["endianness"]
        if not isinstance(value, str) or value not in {"little", "big"}:
            _fail("endianness must be little or big", TgiFaultCode.INVALID_ARGUMENT)
        bi.endianness = EndianessType(value)
        return True
    if name.startswith("setBusInterface") and name in {
        "setBusInterfaceInitiator",
        "setBusInterfaceTarget",
        "setBusInterfaceSystem",
        "setBusInterfaceMirroredInitiator",
        "setBusInterfaceMirroredSystem",
        "setBusInterfaceMirroredTarget",
        "setBusInterfaceMonitor",
    }:
        bi = _expect_object(args["busInterfaceID"], "BusInterface")
        mode = name.removeprefix("setBusInterface")
        current = bi.choice
        if mode == "Initiator":
            value = BusInterfaceType.Initiator()
            same = isinstance(current, BusInterfaceType.Initiator)
        elif mode == "Target":
            ref = _validated_name(args["memoryMapRef"], "memoryMapRef")
            value = BusInterfaceType.Target(memory_map_ref_or_transparent_bridge=[MemoryMapRef(memory_map_ref=ref)])
            same = isinstance(current, BusInterfaceType.Target)
        elif mode == "System":
            from org.accellera.ipxact.v1685_2022.group import Group

            group = _validated_name(args["group"], "group")
            value = BusInterfaceType.System(group=Group(value=group))
            same = isinstance(current, BusInterfaceType.System)
        elif mode == "MirroredSystem":
            from org.accellera.ipxact.v1685_2022.group import Group

            group = _validated_name(args["group"], "group")
            value = BusInterfaceType.MirroredSystem(group=Group(value=group))
            same = isinstance(current, BusInterfaceType.MirroredSystem)
        elif mode == "MirroredTarget":
            value = BusInterfaceType.MirroredTarget()
            same = isinstance(current, BusInterfaceType.MirroredTarget)
        elif mode == "MirroredInitiator":
            from xsdata.formats.dataclass.models.generics import AnyElement

            qname = "{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}mirroredInitiator"
            value = AnyElement(qname=qname)
            same = isinstance(current, AnyElement) and current.qname == qname
        else:
            from org.accellera.ipxact.v1685_2022.monitor_interface_mode import MonitorInterfaceMode

            monitor_mode = args["interfaceMode"]
            if not isinstance(monitor_mode, str) or monitor_mode not in _mode_values(mode):
                _fail("Invalid monitor interfaceMode", TgiFaultCode.INVALID_ARGUMENT)
            value = BusInterfaceType.Monitor(interface_mode=MonitorInterfaceMode(monitor_mode))
            same = isinstance(current, BusInterfaceType.Monitor)
        if same:
            if mode == "Target":
                existing = next(
                    (item for item in current.memory_map_ref_or_transparent_bridge if isinstance(item, MemoryMapRef)),
                    None,
                )
                if existing is None:
                    for child in list(current.memory_map_ref_or_transparent_bridge):
                        if isinstance(child, TransparentBridge):
                            register_parent(child, current, ("memory_map_ref_or_transparent_bridge",), "list")
                            detach_child_by_handle(get_handle(child))
                    _add_list(
                        current, "memory_map_ref_or_transparent_bridge", value.memory_map_ref_or_transparent_bridge[0]
                    )
                else:
                    existing.memory_map_ref = ref
                    for child in list(current.memory_map_ref_or_transparent_bridge):
                        if isinstance(child, TransparentBridge):
                            register_parent(child, current, ("memory_map_ref_or_transparent_bridge",), "list")
                            detach_child_by_handle(get_handle(child))
            elif mode in {"System", "MirroredSystem"}:
                _set_group(current, "group", group)
            elif mode == "Monitor":
                current.interface_mode = value.interface_mode
            return True
        _set_choice(bi, mode, value)
        return True
    if name == "setBusInterfaceRefLocalName":
        ref = _expect_object(args["busInterfaceRefID"], "BusInterfaceRef")
        ref.local_name = _validated_name(args["name"], "name")
        return True
    if name == "setFileSetRefGroupGroup":
        group = _expect_object(args["fileSetRefGroupID"], "FileSetRefGroup")
        group.group = _validated_name(args["group"], "group")
        return True
    if name == "setFileSetRefLocalName":
        ref = _expect_object(args["fileSetRefID"], "FileSetRef")
        ref.local_name = _validated_name(args["localName"], "localName")
        return True
    if name == "setIndirectInterfaceBitsInLau":
        item = _expect_object(args["indirectInterfaceID"], ("IndirectInterface", "IndirectInterfaceType"))
        from org.accellera.ipxact.v1685_2022.bits_in_lau import BitsInLau

        _set_expression(item, "bits_in_lau", BitsInLau, args["bitsInLau"], "bitsInLau", 1, (1 << 64) - 1)
        return True
    if name == "setInitiatorAddressSpaceRef":
        initiator = _expect_object(args["initiatorID"], "Initiator")
        value = _validated_name(args["addressSpaceRef"], "addressSpaceRef")
        current = initiator.address_space_ref
        if current is None:
            current = BusInterfaceType.Initiator.AddressSpaceRef(address_space_ref=value)
            initiator.address_space_ref = current
            register_parent(current, initiator, ("address_space_ref",), "single")
        else:
            current.address_space_ref = value
        _register_graph(current)
        return True
    if name == "setMirroredSystemGroup":
        _set_group(
            _expect_object(args["mirroredSystemID"], "MirroredSystem"), "group", _validated_name(args["group"], "group")
        )
        return True
    if name == "setMirroredTargetBaseAddresses":
        mirrored = _expect_object(args["mirroredTargetID"], "MirroredTarget")
        remap_text = _checked_expression(args["remapAddress"], "remapAddress", 0, (1 << 64) - 1)
        range_text = _checked_expression(args["range"], "range", 1, (1 << 64) - 1)
        current = mirrored.base_addresses
        if current is not None and not isinstance(current, BusInterfaceType.MirroredTarget.BaseAddresses):
            _fail("Invalid baseAddresses model")
        record = current.remap_addresses[0] if current is not None and current.remap_addresses else None
        if record is not None and not isinstance(record.remap_address, UnsignedLongintExpression):
            _fail("Invalid remapAddress model")
        range_obj = current.range if current is not None else None
        if range_obj is not None and not isinstance(range_obj, UnsignedPositiveLongintExpression):
            _fail("Invalid range model")
        if current is None:
            record_cls = BusInterfaceType.MirroredTarget.BaseAddresses.RemapAddresses
            record = record_cls(remap_address=UnsignedLongintExpression(value=remap_text), mode_ref=[])
            current = BusInterfaceType.MirroredTarget.BaseAddresses(
                remap_addresses=[record], range=UnsignedPositiveLongintExpression(value=range_text)
            )
            mirrored.base_addresses = current
            register_parent(current, mirrored, ("base_addresses",), "single")
            register_parent(record, current, ("remap_addresses",), "list")
            register_parent(record.remap_address, record, ("remap_address",), "single")
            register_parent(current.range, current, ("range",), "single")
            _register_graph(current)
        else:
            _expression_plan(current, "range", UnsignedPositiveLongintExpression, range_text, "range", 1, (1 << 64) - 1)
            if record is None:
                record_cls = BusInterfaceType.MirroredTarget.BaseAddresses.RemapAddresses
                record = record_cls(remap_address=UnsignedLongintExpression(value=remap_text), mode_ref=[])
                _add_list(current, "remap_addresses", record)
                register_parent(record.remap_address, record, ("remap_address",), "single")
            else:
                _expression_plan(
                    record, "remap_address", UnsignedLongintExpression, remap_text, "remapAddress", 0, (1 << 64) - 1
                )
            _set_expression(current, "range", UnsignedPositiveLongintExpression, range_text, "range", 1, (1 << 64) - 1)
            _set_expression(
                record, "remap_address", UnsignedLongintExpression, remap_text, "remapAddress", 0, (1 << 64) - 1
            )
            for extra in list(current.remap_addresses[1:]):
                _register_graph(current)
                register_parent(extra, current, ("remap_addresses",), "list")
                detach_child_by_handle(get_handle(extra))
        return True
    if name == "setMonitorGroup":
        _set_group(_expect_object(args["monitorID"], "Monitor"), "group", _validated_name(args["group"], "group"))
        return True
    if name == "setRemapAddressesRemapAddress":
        record = _expect_object(args["remapAddressesID"], "RemapAddresses")
        _set_expression(
            record, "remap_address", UnsignedLongintExpression, args["remapAddress"], "remapAddress", 0, (1 << 64) - 1
        )
        return True
    if name == "setSystemGroup":
        _set_group(_expect_object(args["systemID"], "System"), "group", _validated_name(args["group"], "group"))
        return True
    if name == "setTargetMemoryMapRef":
        target = _expect_object(args["targetID"], "Target")
        value = _validated_name(args["memoryMapRef"], "memoryMapRef")
        values = target.memory_map_ref_or_transparent_bridge
        existing = next((item for item in values if isinstance(item, MemoryMapRef)), None)
        if existing is not None:
            existing.memory_map_ref = value
            for item in list(target.memory_map_ref_or_transparent_bridge):
                if isinstance(item, TransparentBridge):
                    register_parent(item, target, ("memory_map_ref_or_transparent_bridge",), "list")
                    detach_child_by_handle(get_handle(item))
            return True
        for item in list(values):
            register_parent(item, target, ("memory_map_ref_or_transparent_bridge",), "list")
            detach_child_by_handle(get_handle(item))
        target.memory_map_ref_or_transparent_bridge = []
        ref = MemoryMapRef(memory_map_ref=value)
        _add_list(target, "memory_map_ref_or_transparent_bridge", ref)
        return True
    _fail(f"Unimplemented EXTENDED function {name}", TgiFaultCode.INTERNAL_ERROR)


# ---------------------------------------------------------------------------
# BASE (F.7.19)
# ---------------------------------------------------------------------------


def getComponentBusInterfaceIDs(componentID: str) -> list[str]:
    """Return bus-interface handles; standard ownership is F.7.29.2 in component.py.

    Args:
        componentID: Component handle (legacy callers may pass a BusInterfaces handle).
    Returns:
        Handles for the component's busInterface elements.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    obj = _resolve(componentID)
    if type(obj).__name__ == "BusInterfaces":
        return [get_handle(item) for item in getattr(obj, "bus_interface", [])]
    if not isinstance(obj, ComponentType):
        _fail("Invalid component handle")
    from .component import getComponentBusInterfaceIDs as _component_bus_interfaces

    return _component_bus_interfaces(componentID)


def getBusInterfaceName(busInterfaceID: str) -> str | None:
    """Return the bus-interface name.

    Args:
        busInterfaceID: Bus-interface handle.
    Returns:
        Name, if present.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    return getattr(_resolve(busInterfaceID, "BusInterface"), "name", None)


def getBusInterfaceDisplayName(busInterfaceID: str) -> str | None:
    """Return the displayName value.

    Args:
        busInterfaceID: Bus-interface handle.
    Returns:
        Display name, if present.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    value = getattr(_resolve(busInterfaceID, "BusInterface"), "display_name", None)
    return getattr(value, "value", None) if value is not None else None


def getBusInterfaceDescription(busInterfaceID: str) -> str | None:
    """Return the description value.

    Args:
        busInterfaceID: Bus-interface handle.
    Returns:
        Description, if present.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    value = getattr(_resolve(busInterfaceID, "BusInterface"), "description", None)
    return getattr(value, "value", None) if value is not None else None


# F.7.19.25.
def getBusInterfaceBusTypeRefByVLNV(busInterfaceID: str) -> tuple[str | None, str | None, str | None, str | None]:
    """Returns the VLNV of the busType defined on the given busInterface element.

    The Python result preserves the established (vendor, library, name, version) tuple. Annex prose describes
    String; the WSDL uses a four-part string array.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        busTypeVLNV: The VLNV of the bus

    Section: F.7.19.25.
    """
    return _spec_call("getBusInterfaceBusTypeRefByVLNV", locals())


def getBusInterfaceAbstractionTypeBusTypeViewRefsByVLNV(
    busInterfaceID: str,
) -> list[tuple[str | None, str | None, str | None, str | None]]:
    """Return legacy per-abstraction view-name tuples.

    Args:
        busInterfaceID: Bus-interface handle.
    Returns:
        One tuple per abstractionType, populated from its first viewRef.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    bi = _resolve(busInterfaceID, "BusInterface")
    values = []
    abstractions = getattr(getattr(bi, "abstraction_types", None), "abstraction_type", [])
    for abstraction in abstractions:
        view = abstraction.view_ref[0] if abstraction.view_ref else None
        values.append((None, None, getattr(view, "value", None), None))
    return values


# F.7.19.26.
def getBusInterfaceConnectionRequired(busInterfaceID: str) -> bool:
    """Returns the connectionRequired defined on the given busInterface element.

    An omitted connectionRequired has the effective value False.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        value: The connectionRequired value

    Section: F.7.19.26.
    """
    return _spec_call("getBusInterfaceConnectionRequired", locals())


# F.7.19.1.
def getAbstractionTypeAbstractionRefByID(abstractionTypeID: str) -> str:
    """Returns the handle to the abstractionDefinition instance referenced from the given abtractionType element

    Args:
        abstractionTypeID: Handle to an abstractionType element

    Returns:
        abstractionDefinitionID: Handle to the referenced abstraction- Definition object

    Section: F.7.19.1.
    """
    return _spec_call("getAbstractionTypeAbstractionRefByID", locals())


# F.7.19.2.
def getAbstractionTypeAbstractionRefByVLNV(
    abstractionTypeID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Returns the VLNV of the abstractionDefinition referenced from the given abtractionType element.

    The Python result is a (vendor, library, name, version) tuple. Annex prose describes String; the WSDL uses a
    four-part string array.

    Args:
        abstractionTypeID: Handle to an abstractionType element

    Returns:
        VLNV: The VLNV of the referenced abstractionDefinition object

    Section: F.7.19.2.
    """
    return _spec_call("getAbstractionTypeAbstractionRefByVLNV", locals())


# F.7.19.3.
def getAbstractionTypePortMapIDs(abstractionTypeID: str) -> list[str]:
    """Returns the handles to all the portMaps defined on the given abstractionType element.

    Args:
        abstractionTypeID: Handle to an abstractionType element

    Returns:
        portMapIDs: List of handles to the portMap elements

    Section: F.7.19.3.
    """
    return _spec_call("getAbstractionTypePortMapIDs", locals())


# F.7.19.4.
def getAbstractionTypeViewRefByID(abstractionTypeID: str, viewRef: str) -> str:
    """Returns all the viewRefs defined on the given abstractionType element.

    Args:
        abstractionTypeID: Handle to an abstractionType element
        viewRef: Handle to the viewRef element

    Returns:
        viewID: Handle to the referenced view

    Section: F.7.19.4.
    """
    return _spec_call("getAbstractionTypeViewRefByID", locals())


# F.7.19.5.
def getAbstractionTypeViewRefByNames(abstractionTypeID: str) -> list[str]:
    """Returns all the viewRefs defined on the given abstractionType element.

    Args:
        abstractionTypeID: Handle to an abstractionType element

    Returns:
        viewRefs: List of the referenced views

    Section: F.7.19.5.
    """
    return _spec_call("getAbstractionTypeViewRefByNames", locals())


# F.7.19.6.
def getAbstractionTypeViewRefIDs(abstractionTypeID: str) -> list[str]:
    """Returns the handles to all the viewRefs defined on the given abstractionType element.

    Args:
        abstractionTypeID: Handle to an abstractionType element

    Returns:
        viewRefsIDs: List of handles to the viewRef elements

    Section: F.7.19.6.
    """
    return _spec_call("getAbstractionTypeViewRefIDs", locals())


# F.7.19.7.
def getAddressSpaceRefBaseAddress(addressSpaceRefID: str) -> int | None:
    """Returns the baseAddress resolved value on an addressSpaceRef element

    An omitted baseAddress has the effective offset 0. The Expression and ID getters preserve source absence.

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element

    Returns:
        baseAddressValue: The resolved baseAddress value

    Section: F.7.19.7.
    """
    return _spec_call("getAddressSpaceRefBaseAddress", locals())


# F.7.19.8.
def getAddressSpaceRefBaseAddressExpression(addressSpaceRefID: str) -> str | None:
    """Returns the baseAddress expression on an addressSpaceRef element

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element

    Returns:
        baseAddressExpression: The baseAddress expression

    Section: F.7.19.8.
    """
    return _spec_call("getAddressSpaceRefBaseAddressExpression", locals())


# F.7.19.9.
def getAddressSpaceRefBaseAddressID(addressSpaceRefID: str) -> str | None:
    """Returns the handle to the baseAddress defined on the given addressSpaceRef element.

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element

    Returns:
        baseAddressID: Handle to the baseAddress element

    Section: F.7.19.9.
    """
    return _spec_call("getAddressSpaceRefBaseAddressID", locals())


# F.7.19.10.
def getAddressSpaceRefModeRefByID(addressSpaceRefID: str, modeRef: str) -> str | None:
    """Returns the handle to the mode referenced from the given addressSpaceRef element.

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element
        modeRef: The referenced mode

    Returns:
        modeID: Handle to the referenced mode element

    Section: F.7.19.10.
    """
    return _spec_call("getAddressSpaceRefModeRefByID", locals())


# F.7.19.11.
def getAddressSpaceRefModeRefByNames(addressSpaceRefID: str) -> list[str]:
    """Returns all the modeRefs defined on the given addressSpaceRef element

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element

    Returns:
        modeRefs: List of the referenced modes

    Section: F.7.19.11.
    """
    return _spec_call("getAddressSpaceRefModeRefByNames", locals())


# F.7.19.12.
def getBaseAddressesRange(baseAddressesID: str) -> int | None:
    """Returns the range value defined on the given baseAddresses element.

    Args:
        baseAddressesID: Handle to a baseAddressses element

    Returns:
        rangeValue: The range value

    Section: F.7.19.12.
    """
    return _spec_call("getBaseAddressesRange", locals())


# F.7.19.13.
def getBaseAddressesRangeExpression(baseAddressesID: str) -> str | None:
    """Returns the range expression defined on the given baseAddresses element

    Args:
        baseAddressesID: Handle to a baseAddressses element

    Returns:
        rangeExpression: The range expression

    Section: F.7.19.13.
    """
    return _spec_call("getBaseAddressesRangeExpression", locals())


# F.7.19.14.
def getBaseAddressesRangeID(baseAddressesID: str) -> str | None:
    """Returns the handle to the range defined on the given baseAddresses element

    Args:
        baseAddressesID: Handle to a baseAddressses element

    Returns:
        rangeID: Handle to the range element

    Section: F.7.19.14.
    """
    return _spec_call("getBaseAddressesRangeID", locals())


# F.7.19.15.
def getBaseAddressesRemapAddressIDs(baseAddressesID: str) -> list[str]:
    """Returns the handles to all the remapAddress defined on the given baseAddresses element

    The returned handles identify remapAddresses records. Use getRemapAddressesRemapAddressID to retrieve each
    record's remapAddress expression handle.

    Args:
        baseAddressesID: Handle to a baseAddressses element

    Returns:
        remapAddressesIDs: List of handles to the baseAddress elements

    Section: F.7.19.15.
    """
    return _spec_call("getBaseAddressesRemapAddressIDs", locals())


# F.7.19.16.
def getBusInterfaceAbstractionTypeIDs(busInterfaceID: str) -> list[str]:
    """Returns the handles to all the abstractionTypes defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        abstractionTypeIDs: List of handles to the abstractionType elements

    Section: F.7.19.16.
    """
    return _spec_call("getBusInterfaceAbstractionTypeIDs", locals())


# F.7.19.17.
def getBusInterfaceBitSteering(busInterfaceID: str) -> bool:
    """Returns the bitSteering defined on the given busInterface element.

    An omitted bitSteering has the effective value False; an unresolved or non-bit expression returns None.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        value: The bitSteering value

    Section: F.7.19.17.
    """
    return _spec_call("getBusInterfaceBitSteering", locals())


# F.7.19.18.
def getBusInterfaceBitSteeringExpression(busInterfaceID: str) -> str | None:
    """Returns the bitSteering expression defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        valueExpression: The bitSteering expression

    Section: F.7.19.18.
    """
    return _spec_call("getBusInterfaceBitSteeringExpression", locals())


# F.7.19.19.
def getBusInterfaceBitSteeringID(busInterfaceID: str) -> str | None:
    """Returns the handle to the bitSteering defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        bitSteeringID: Handle to the bitSteering element

    Section: F.7.19.19.
    """
    return _spec_call("getBusInterfaceBitSteeringID", locals())


# F.7.19.20.
def getBusInterfaceBitsInLau(busInterfaceID: str) -> int | None:
    """Returns the bitsInLau resolved value on a busInterface element.

    An omitted bitsInLau has the effective value 8. Its Expression and ID getters return None when the source
    element is absent.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        value: The bitsInLau resolved value

    Section: F.7.19.20.
    """
    return _spec_call("getBusInterfaceBitsInLau", locals())


# F.7.19.21.
def getBusInterfaceBitsInLauExpression(busInterfaceID: str) -> str | None:
    """Returns the bitsInLau expression defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        bitsInLauExpression: The bitsInLau expression

    Section: F.7.19.21.
    """
    return _spec_call("getBusInterfaceBitsInLauExpression", locals())


# F.7.19.22.
def getBusInterfaceBitsInLauID(busInterfaceID: str) -> str | None:
    """Returns the handle to the bitsInLau defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        bitsInLauID: Handle to the bitsInLau element

    Section: F.7.19.22.
    """
    return _spec_call("getBusInterfaceBitsInLauID", locals())


# F.7.19.23.
def getBusInterfaceBusTypeID(busInterfaceID: str) -> str | None:
    """Returns the handle to the busType defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        busTypeID: Handle to the busType element

    Section: F.7.19.23.
    """
    return _spec_call("getBusInterfaceBusTypeID", locals())


# F.7.19.24.
def getBusInterfaceBusTypeRefByID(busInterfaceID: str) -> str | None:
    """Returns the handle to the busDefinition referenced from the busType defined on the given busInterface
    element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        busDefinitionID: Handle to the referenced busDefinition object

    Section: F.7.19.24.
    """
    return _spec_call("getBusInterfaceBusTypeRefByID", locals())


# F.7.19.27.
def getBusInterfaceEndianness(busInterfaceID: str) -> str:
    """Returns the endianness defined on the given busInterface element.

    An omitted endianness has the effective value "little".

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        value: The endianness value

    Section: F.7.19.27.
    """
    return _spec_call("getBusInterfaceEndianness", locals())


# F.7.19.28.
def getBusInterfaceInitiatorID(busInterfaceID: str) -> str | None:
    """Returns the handle to the initiator defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        initiatorID: Handle to an initiator element

    Section: F.7.19.28.
    """
    return _spec_call("getBusInterfaceInitiatorID", locals())


# F.7.19.29.
def getBusInterfaceInterfaceMode(busInterfaceID: str) -> str:
    """Returns the interfaceMode defined on the given busInterface element.

    Returns all seven schema modes: initiator, target, system, mirroredInitiator, mirroredTarget, mirroredSystem, or
    monitor. An absent choice returns None.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        interfaceMode: The interface mode (initiator, target, system)

    Section: F.7.19.29.
    """
    return _spec_call("getBusInterfaceInterfaceMode", locals())


# F.7.19.30.
def getBusInterfaceMirroredSystemID(busInterfaceID: str) -> str | None:
    """Returns the handle to the mirroredSystem element defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        mirroredSystemID: Handle to the mirroredSystem element

    Section: F.7.19.30.
    """
    return _spec_call("getBusInterfaceMirroredSystemID", locals())


# F.7.19.31.
def getBusInterfaceMirroredTargetID(busInterfaceID: str) -> str | None:
    """Returns the handle to the mirroredTarget element defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        mirroredTargetID: Handle to the mirroredTarget element

    Section: F.7.19.31.
    """
    return _spec_call("getBusInterfaceMirroredTargetID", locals())


# F.7.19.32.
def getBusInterfaceMonitorID(busInterfaceID: str) -> str | None:
    """Returns the handle to the monitor element defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        monitorID: Handle to the monitor element

    Section: F.7.19.32.
    """
    return _spec_call("getBusInterfaceMonitorID", locals())


# F.7.19.33.
def getBusInterfaceRefLocalName(busInterfaceRefID: str) -> str:
    """Returns the localName defined on the given busInterfaceRef element.

    Args:
        busInterfaceRefID: Handle to a busInterfaceRef element

    Returns:
        localName: The local name

    Section: F.7.19.33.
    """
    return _spec_call("getBusInterfaceRefLocalName", locals())


# F.7.19.34.
def getBusInterfaceSystemID(busInterfaceID: str) -> str | None:
    """Returns the handle to the system element defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        systemID: Handle to the system element

    Section: F.7.19.34.
    """
    return _spec_call("getBusInterfaceSystemID", locals())


# F.7.19.35.
def getBusInterfaceTargetID(busInterfaceID: str) -> str | None:
    """Returns the handle to the target defined on the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        targetID: Handle to the target element

    Section: F.7.19.35.
    """
    return _spec_call("getBusInterfaceTargetID", locals())


# F.7.19.36.
def getChannelBusInterfaceRefByID(busInterfaceRefID: str) -> str | None:
    """Returns the busInterface referenced from the given busInterfaceRef element.

    Args:
        busInterfaceRefID: Handle to an busInterfaceRef element

    Returns:
        busInterfaceID: Handle to the referenced busInterface element

    Section: F.7.19.36.
    """
    return _spec_call("getChannelBusInterfaceRefByID", locals())


# F.7.19.37.
def getChannelBusInterfaceRefIDs(channelID: str) -> list[str]:
    """Returns the handles to all the busInterfaceRefs defined on the given channel element.

    Args:
        channelID: Handle to a channel element

    Returns:
        busInterfaceRefIDs: List of handles to the busInterfaceRef elements

    Section: F.7.19.37.
    """
    return _spec_call("getChannelBusInterfaceRefIDs", locals())


# F.7.19.38.
def getFileSetRefGroupGroup(fileSetRefGroupID: str) -> str:
    """Returns the group defined on the given fileSetRefGroup element.

    Args:
        fileSetRefGroupID: Handle to a fileSetRefGroup element

    Returns:
        group: The group name

    Section: F.7.19.38.
    """
    return _spec_call("getFileSetRefGroupGroup", locals())


# F.7.19.39.
def getIndirectInterfaceBitsInLauID(indirectInterfaceID: str) -> str | None:
    """Returns the handle to the bitsInLau defined on the given indirectInterface element.

    Args:
        indirectInterfaceID: Handle to an indirectInterface element

    Returns:
        bitsInLauID: Handle to the bitsInLau element

    Section: F.7.19.39.
    """
    return _spec_call("getIndirectInterfaceBitsInLauID", locals())


# F.7.19.40.
def getInitiatorAddressSpaceRefByName(initiatorID: str) -> str | None:
    """Returns the addressSpace referenced from the given initiator element.

    Args:
        initiatorID: Handle to a busInterface initiator element

    Returns:
        addressSpace: The referenced addressSpace name

    Section: F.7.19.40.
    """
    return _spec_call("getInitiatorAddressSpaceRefByName", locals())


# F.7.19.41.
def getInitiatorAddressSpaceRefID(initiatorID: str) -> str | None:
    """Returns the addressSpaceRef defined on the given busInterface initiator element.

    Args:
        initiatorID: Handle to an initiator element

    Returns:
        addressSPaceRefID: Handle to the addressSpaceRef element

    Section: F.7.19.41.
    """
    return _spec_call("getInitiatorAddressSpaceRefID", locals())


# F.7.19.42.
def getMemoryMapRefModeRefByID(memoryMapRefID: str, modeRef: str) -> str | None:
    """Returns the handle to the mode referenced from the given memoryMapRef element.

    Args:
        memoryMapRefID: Handle to a memoryMapRef element
        modeRef: The referenced mode

    Returns:
        modeID: Handle to the referenced mode element

    Section: F.7.19.42.
    """
    return _spec_call("getMemoryMapRefModeRefByID", locals())


# F.7.19.43.
def getMemoryMapRefModeRefByNames(memoryMapRefID: str) -> list[str]:
    """Returns all the modeRefs defined on the given memoryMapRef element.

    Args:
        memoryMapRefID: Handle to a memoryMapRef element

    Returns:
        modeRefs: List of the referenced modes

    Section: F.7.19.43.
    """
    return _spec_call("getMemoryMapRefModeRefByNames", locals())


# F.7.19.44.
def getMirroredSystemGroup(mirroredSystemID: str) -> str:
    """Returns the group defined on the given mmirroredSystem element

    Args:
        mirroredSystemID: Handle to a mirroredSystem element

    Returns:
        group: The group value on the mirroredSystem element

    Section: F.7.19.44.
    """
    return _spec_call("getMirroredSystemGroup", locals())


# F.7.19.45.
def getMirroredTargetBaseAddressesID(mirroredTargetID: str) -> str | None:
    """Returns the handle to baseAddresses defined on the given mirroredTarget element.

    Args:
        mirroredTargetID: Handle to a mirroredTarget element

    Returns:
        baseAddressesID: Handle to a baseAddresses element

    Section: F.7.19.45.
    """
    return _spec_call("getMirroredTargetBaseAddressesID", locals())


# F.7.19.46.
def getMonitorGroup(monitorID: str) -> str:
    """Returns the group defined on the given busInterface monitor element.

    Args:
        monitorID: Handle to a monitor element

    Returns:
        group: The group name

    Section: F.7.19.46.
    """
    return _spec_call("getMonitorGroup", locals())


# F.7.19.47.
def getRemapAddressModeRefByID(remapAddressID: str) -> str | None:
    """Returns the handle to the mode referenced from the given remapAddress element.

    The input is a remapAddress expression handle. The owning record must have at most one modeRef; multiple
    references raise INVALID_ARGUMENT rather than select an arbitrary mode.

    Args:
        remapAddressID: Handle to a remapAddress element

    Returns:
        modeID: Handle to the referenced mode element

    Section: F.7.19.47.
    """
    return _spec_call("getRemapAddressModeRefByID", locals())


# F.7.19.48.
def getRemapAddressesRemapAddressID(remapAddressesID: str) -> str | None:
    """Returns the handle to remapAddress from the given remapAddresses element.

    Args:
        remapAddressesID: Handle to a remapAddresses element

    Returns:
        remapAddressID: Handle to a remapAddress element

    Section: F.7.19.48.
    """
    return _spec_call("getRemapAddressesRemapAddressID", locals())


# F.7.19.49.
def getSystemGroup(systemID: str) -> str:
    """Returns the group defined on the given busInterface system element.

    Args:
        systemID: Handle to a system element

    Returns:
        group: The group name

    Section: F.7.19.49.
    """
    return _spec_call("getSystemGroup", locals())


# F.7.19.50.
def getTargetFileSetRefGroupIDs(targetID: str) -> list[str]:
    """Returns the handles to all the fileSetRefgroups defined on the given target element.

    Args:
        targetID: Handle to a busInterface target element

    Returns:
        fileSetRefgroupIDs: List of handles to the fileSetRefGroup elements

    Section: F.7.19.50.
    """
    return _spec_call("getTargetFileSetRefGroupIDs", locals())


# F.7.19.51.
def getTargetMemoryMapRefByName(targetID: str) -> str | None:
    """Returns the memoryMapRef defined on the given target element.

    Args:
        targetID: Handle to a target element of a busInterface

    Returns:
        memoryMapRef: The memoryMap reference

    Section: F.7.19.51.
    """
    return _spec_call("getTargetMemoryMapRefByName", locals())


# F.7.19.52.
def getTargetMemoryMapRefID(targetID: str) -> str | None:
    """Returns the handle to the memoryMapRef defined on the given target element.

    Args:
        targetID: Handle to a busInterface target element

    Returns:
        memoryMapRefID: Handle to the memoryMapRef element

    Section: F.7.19.52.
    """
    return _spec_call("getTargetMemoryMapRefID", locals())


# F.7.19.53.
def getTargetTransparentBridgeIDs(targetID: str) -> list[str]:
    """Returns the handles to all the transparentBridges defined on the given target element.

    Args:
        targetID: Handle to a busInterface target element

    Returns:
        transparentBrigesIDs: List of handles to the transparentBridge ele- ments

    Section: F.7.19.53.
    """
    return _spec_call("getTargetTransparentBridgeIDs", locals())


# ---------------------------------------------------------------------------
# EXTENDED (F.7.20)
# ---------------------------------------------------------------------------


def addBusInterface(componentID: str, name: str, busTypeVLNV: tuple[str, str, str, str]) -> str:
    """Create a bus interface using the original convenience signature.

    This project convenience creates an initiator interface initially. Set its desired mode using the standard mode
    setters.

    Args:
        componentID: Component handle.
        name: Bus-interface name.
        busTypeVLNV: Four-part bus definition VLNV.
    Returns:
        New busInterface handle.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    comp = _resolve(componentID)
    if not isinstance(comp, ComponentType):
        _fail("Invalid component handle")
    parts = _validated_vlnv(busTypeVLNV, "busTypeVLNV")
    name = _validated_name(name, "name")
    if any(item.name == name for item in getattr(comp.bus_interfaces, "bus_interface", [])):
        _fail("Bus interface name already exists", TgiFaultCode.ALREADY_EXISTS)
    from org.accellera.ipxact.v1685_2022.bus_interface import BusInterface
    from org.accellera.ipxact.v1685_2022.bus_interfaces import BusInterfaces
    from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType

    if comp.bus_interfaces is None:
        comp.bus_interfaces = BusInterfaces(bus_interface=[])
    from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType

    register_parent(comp.bus_interfaces, comp, ("bus_interfaces",), "single")
    item = BusInterface(
        name=name,
        bus_type=ConfigurableLibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3]),
        choice=BusInterfaceType.Initiator(),
    )
    comp.bus_interfaces.bus_interface.append(item)
    register_parent(item, comp.bus_interfaces, ("bus_interface",), "list")
    _register_graph(item)
    return get_handle(item)


def removeBusInterface(busInterfaceID: str) -> bool:
    """Remove a bus interface through its registered owner.

    Args:
        busInterfaceID: Bus-interface handle.
    Returns:
        True when removed.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    obj = _resolve(busInterfaceID, "BusInterface")
    _register_graph(obj)
    info = get_parent_info(busInterfaceID)
    parent = resolve_handle(info.parent_handle) if info is not None else None
    removed = detach_child_by_handle(get_handle(obj))
    if removed and parent is not None and not parent.bus_interface:
        detach_child_by_handle(get_handle(parent))
    return removed


def setBusInterfaceBusTypeRefByVLNV(busInterfaceID: str, busTypeVLNV: Sequence[str] | str | None) -> bool:
    """Compatibility alias for setBusInterfaceBusType.

    The required busType cannot be cleared. A None input raises INVALID_ARGUMENT without changing the interface.

    Args:
        busInterfaceID: Bus-interface handle.
        busTypeVLNV: Four-part VLNV or legacy None to clear.
    Returns:
        True when set.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    if busTypeVLNV is None:
        _resolve(busInterfaceID, "BusInterface")
        _fail("busType is required and cannot be removed", TgiFaultCode.INVALID_ARGUMENT)
    return setBusInterfaceBusType(busInterfaceID, busTypeVLNV)


def addBusInterfaceAbstractionTypeBusTypeViewRef(busInterfaceID: str, viewVLNV: tuple[str, str, str, str]) -> bool:
    """Add a legacy name-only viewRef to the first abstractionType.

    Args:
        busInterfaceID: Bus-interface handle.
        viewVLNV: Legacy four-part tuple; the third item supplies the local view name.
    Returns:
        True when added.

    Section: Project extension outside IEEE 1685-2022 Annex F.
    """
    bi = _resolve(busInterfaceID, "BusInterface")
    abstractions = getattr(bi.abstraction_types, "abstraction_type", []) if bi.abstraction_types else []
    if not abstractions:
        _fail("A valid abstractionType with abstractionRef is required", TgiFaultCode.INVALID_ARGUMENT)
    ref = _validated_name(_validated_vlnv(viewVLNV, "viewVLNV")[2], "viewVLNV")
    return bool(addAbstractionTypeViewRef(get_handle(abstractions[0]), ref))


# F.7.20.36.
def setBusInterfaceConnectionRequired(busInterfaceID: str, value: bool) -> bool:
    """Sets connectionRequired with the given value for the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element
        value: ConnectionRequired value

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.36.
    """
    return _spec_call("setBusInterfaceConnectionRequired", locals())


# F.7.20.1.
def addAbstractionTypePortMap(abstractionTypeID: str, logicalPortName: str, physicalPortName: str) -> str:
    """Adds a portMap with the given name, logicalPortName, and physicalPortName to the given abstractionType

    Args:
        abstractionTypeID: Handle to an abstractionType element
        logicalPortName: Logical port name
        physicalPortName: Physical port name

    Returns:
        portMapID: Handle to a new portMap element

    Section: F.7.20.1.
    """
    return _spec_call("addAbstractionTypePortMap", locals())


# F.7.20.2.
def addAbstractionTypeViewRef(abstractionTypeID: str, viewRef: str) -> str:
    """Adds a viewRef with the given name to the given abstractionType element.

    Args:
        abstractionTypeID: Handle to an abstractionType element
        viewRef: View name

    Returns:
        viewRefID: the viewRef identifier

    Section: F.7.20.2.
    """
    return _spec_call("addAbstractionTypeViewRef", locals())


# F.7.20.3.
def addAddressSpaceRefModeRef(addressSpaceRefID: str, modeRef: str) -> bool:
    """Adds an mode reference on an addressSpaceRef element

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element
        modeRef: The modeRef expression to be added on an addressSpaceRef element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.3.
    """
    return _spec_call("addAddressSpaceRefModeRef", locals())


# F.7.20.4.
def addBaseAddressesRemapAddresses(baseAddressesID: str, remapAddress: str) -> str:
    """Adds a remapAddress on a baseAddresses element

    Args:
        baseAddressesID: Handle to a baseAddresses element
        remapAddress: The remapAddress value to be set on the remapAddresses element

    Returns:
        remapAddressesID: Handle to a remapAddresses element

    Section: F.7.20.4.
    """
    return _spec_call("addBaseAddressesRemapAddresses", locals())


# F.7.20.5.
def addBusInterfaceAbstractionType(busInterfaceID: str, abstractionRef: Sequence[str]) -> str:
    """Adds an abstractionType with the given abstractionRef to the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element
        abstractionRef: AbstractionDef VLNV

    Returns:
        abstractionTypeID: Handle to a new abstractionType element

    Section: F.7.20.5.
    """
    return _spec_call("addBusInterfaceAbstractionType", locals())


# F.7.20.6.
def addChannelBusInterfaceRef(channelID: str, name: str) -> str:
    """Adds a busInterfaceRef with the given name to the given channel element.

    Args:
        channelID: Handle to a channel element
        name: BusInterface name

    Returns:
        busInterfaceRefID: Handle to busInterfaceRef element

    Section: F.7.20.6.
    """
    return _spec_call("addChannelBusInterfaceRef", locals())


# F.7.20.7.
def addMemoryMapRefModeRef(memoryMapRefID: str, modeRef: str) -> bool:
    """Adds a modeRef on the given memoryMapRef element

    Args:
        memoryMapRefID: Handle to a memoryMapRef element
        modeRef: The mode reference to be add on the memoryMapRef element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.7.
    """
    return _spec_call("addMemoryMapRefModeRef", locals())


# F.7.20.8.
def addTargetFileSetRefGroup(targetID: str) -> str:
    """Adds a fileSetRefGroup on the given target element

    Args:
        targetID: Handle to a target element of a busInterface

    Returns:
        fileSetRefGroupID: Handle to a fileSetRefGroup element

    Section: F.7.20.8.
    """
    return _spec_call("addTargetFileSetRefGroup", locals())


# F.7.20.9.
def addTargetTransparentBridge(targetID: str, initiatorRef: str) -> str:
    """Adds a transparentBridge on the given target element

    Args:
        targetID: Handle to a target element of a busInterface
        initiatorRef: The initiator reference value to be added

    Returns:
        transparentBridgeID: Handle of a transparentBrige element

    Section: F.7.20.9.
    """
    return _spec_call("addTargetTransparentBridge", locals())


# F.7.20.10.
def removeAbstractionTypePortMap(portMapID: str) -> bool:
    """Removes the given portMap element.

    Args:
        portMapID: Handle to a portMap element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.10.
    """
    return _spec_call("removeAbstractionTypePortMap", locals())


# F.7.20.11.
def removeAbstractionTypeViewRef(viewRefID: str) -> bool:
    """Removes the viewRef element with the given viewRef ID.

    Args:
        viewRefID: Handle of the viewRef

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.11.
    """
    return _spec_call("removeAbstractionTypeViewRef", locals())


# F.7.20.12.
def removeAddressSpaceRefBaseAddress(addressSpaceRefID: str) -> bool:
    """Removes the baseAddress from the given addressSpaceRef element

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.12.
    """
    return _spec_call("removeAddressSpaceRefBaseAddress", locals())


# F.7.20.13.
def removeAddressSpaceRefModeRef(addressSpaceRefID: str, modeRef: str) -> bool:
    """Removes the designated modeRef from the given addressSpaceRef element.

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element
        modeRef: The mode reference to be removed

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.13.
    """
    return _spec_call("removeAddressSpaceRefModeRef", locals())


# F.7.20.14.
def removeBaseAddressesRemapAddresses(remapAddressesID: str) -> bool:
    """Removes a remapAddresses element from a baseAddresses element.

    Args:
        remapAddressesID: Handle to a remapAddresses element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.14.
    """
    return _spec_call("removeBaseAddressesRemapAddresses", locals())


# F.7.20.16.
def removeBusInterfaceAbstractionType(abstractionTypeID: str) -> bool:
    """Removes the given abstractionType element.

    Args:
        abstractionTypeID: Handle to an abstractionType element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.16.
    """
    return _spec_call("removeBusInterfaceAbstractionType", locals())


# F.7.20.17.
def removeBusInterfaceBitSteering(busInterfaceID: str) -> bool:
    """Removes bitSteering from the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.17.
    """
    return _spec_call("removeBusInterfaceBitSteering", locals())


# F.7.20.18.
def removeBusInterfaceBitsInLau(busInterfaceID: str) -> bool:
    """Removes the bitsInLau for the given busInterface element.

    Args:
        busInterfaceID: Handle to an busInterface element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.18.
    """
    return _spec_call("removeBusInterfaceBitsInLau", locals())


# F.7.20.19.
def removeBusInterfaceConnectionRequired(busInterfaceID: str) -> bool:
    """Removes connectionRequired from the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.19.
    """
    return _spec_call("removeBusInterfaceConnectionRequired", locals())


# F.7.20.20.
def removeBusInterfaceEndianness(busInterfaceID: str) -> bool:
    """Removes endianness from the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.20.
    """
    return _spec_call("removeBusInterfaceEndianness", locals())


# F.7.20.21.
def removeChannelBusInterfaceRef(busInterfaceRefID: str) -> bool:
    """remove the selected busInterfaceRef from the Channel element if busInterfaceRef list size is greater than 2.

    Args:
        busInterfaceRefID: Handle to a busInterfaceRef element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.21.
    """
    return _spec_call("removeChannelBusInterfaceRef", locals())


# F.7.20.22.
def removeFileSetRefGroupGroup(fileSetRefGroupID: str) -> bool:
    """Removes the group on the given fileSetRefGroup element.

    Args:
        fileSetRefGroupID: Handle to a fileSetRefGroup element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.22.
    """
    return _spec_call("removeFileSetRefGroupGroup", locals())


# F.7.20.23.
def removeIndirectInterfaceBitsInLau(indirectInterfaceID: str) -> bool:
    """Removes the bitsInLau for the given indirectInterface element.

    Args:
        indirectInterfaceID: Handle to an indirectInterface element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.23.
    """
    return _spec_call("removeIndirectInterfaceBitsInLau", locals())


# F.7.20.24.
def removeInitiatorAddressSpaceRef(initiatorID: str) -> bool:
    """Removes the addressSpaceRef from an initiator element.

    Args:
        initiatorID: Handle to an initiator element of a busInterface

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.24.
    """
    return _spec_call("removeInitiatorAddressSpaceRef", locals())


# F.7.20.25.
def removeMemoryMapRefModeRef(memoryMapRefID: str, modeRef: str) -> bool:
    """Removes a modeRef from the given memoryMapRef element.

    Args:
        memoryMapRefID: Handle to a memoryMapRef element
        modeRef: The mode reference to be remove on the memoryMapRef element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.25.
    """
    return _spec_call("removeMemoryMapRefModeRef", locals())


# F.7.20.26.
def removeMirroredTargetBaseAddresses(mirroredTargetID: str) -> bool:
    """Removes the baseAddresses from the given mirroredTarget element.

    Args:
        mirroredTargetID: Handle to a mirroredTarget element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.26.
    """
    return _spec_call("removeMirroredTargetBaseAddresses", locals())


# F.7.20.27.
def removeMonitorGroup(monitorID: str) -> bool:
    """Removes the group on the given monitor element of a busInterface.

    Args:
        monitorID: Handle to a monitor element of a busInterface

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.27.
    """
    return _spec_call("removeMonitorGroup", locals())


# F.7.20.28.
def removeTargetFileSetRefGroup(fileSetRefGroupID: str) -> bool:
    """Removes a fileSetRefGroup element from the given target element.

    Args:
        fileSetRefGroupID: Handle to a fileSetRefGroup

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.28.
    """
    return _spec_call("removeTargetFileSetRefGroup", locals())


# F.7.20.29.
def removeTargetMemoryMapRef(targetID: str) -> bool:
    """Removes the memoryMap reference on a target element of a bus interface.

    Args:
        targetID: Handle to a target element of a busInterface

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.29.
    """
    return _spec_call("removeTargetMemoryMapRef", locals())


# F.7.20.30.
def removeTargetTransparentBridge(transparentBrigeID: str) -> bool:
    """Removes a transparentBridge element from the given target element.

    Args:
        transparentBrigeID: Handle to a transparentBrige element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.30.
    """
    return _spec_call("removeTargetTransparentBridge", locals())


# F.7.20.31.
def setAddressSpaceRefBaseAddress(addressSpaceRefID: str, baseAddress: str) -> bool:
    """Sets the baseAddress on an addressSpaceRef element.

    Args:
        addressSpaceRefID: Handle to an addressSpaceRef element
        baseAddress: The baseAddress expression to be set

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.31.
    """
    return _spec_call("setAddressSpaceRefBaseAddress", locals())


# F.7.20.32.
def setBaseAddressesRange(baseAddressesID: str, range: str) -> bool:
    """Sets the range on a baseAddress element.

    Args:
        baseAddressesID: Handle to a baseAddresses element
        range: the new range to set

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.32.
    """
    return _spec_call("setBaseAddressesRange", locals())


# F.7.20.33.
def setBusInterfaceBitSteering(busInterfaceID: str, value: str) -> bool:
    """Sets bitSteering with the given value for the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element
        value: BitSteering value

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.33.
    """
    return _spec_call("setBusInterfaceBitSteering", locals())


# F.7.20.34.
def setBusInterfaceBitsInLau(busInterfaceID: str, bitsInLau: str) -> bool:
    """Sets the given bitsInLau expression for the busInterface element.

    Args:
        busInterfaceID: Handle to an busInterface element
        bitsInLau: The bitsInLau expression

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.34.
    """
    return _spec_call("setBusInterfaceBitsInLau", locals())


# F.7.20.35.
def setBusInterfaceBusType(busInterfaceID: str, vlnv: Sequence[str]) -> bool:
    """Sets the busType on a busInterface element.

    Args:
        busInterfaceID: Handle to an busInterface element
        vlnv: The vlnv expression to be set on the busType

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.35.
    """
    return _spec_call("setBusInterfaceBusType", locals())


# F.7.20.37.
def setBusInterfaceEndianness(busInterfaceID: str, endianness: str) -> bool:
    """Sets endianness with the given value for the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element
        endianness: Endianness value : little or big

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.37.
    """
    return _spec_call("setBusInterfaceEndianness", locals())


# F.7.20.38.
def setBusInterfaceInitiator(busInterfaceID: str) -> bool:
    """Sets the bus interface mode to initiator.

    Args:
        busInterfaceID: Handle to an busInterface element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.38.
    """
    return _spec_call("setBusInterfaceInitiator", locals())


# F.7.20.39.
def setBusInterfaceMirroredInitiator(busInterfaceID: str) -> bool:
    """Sets the bus interface mode to mirroredInitiator.

    Args:
        busInterfaceID: Handle to an busInterface element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.39.
    """
    return _spec_call("setBusInterfaceMirroredInitiator", locals())


# F.7.20.40.
def setBusInterfaceMirroredSystem(busInterfaceID: str, group: str) -> bool:
    """Sets the bus interface mode to mirroredSystem.

    Args:
        busInterfaceID: Handle to an busInterface element
        group: The group value to be set on the system element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.40.
    """
    return _spec_call("setBusInterfaceMirroredSystem", locals())


# F.7.20.41.
def setBusInterfaceMirroredTarget(busInterfaceID: str) -> bool:
    """Sets the bus interface mode to mirroredTarget.

    Args:
        busInterfaceID: Handle to an busInterface element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.41.
    """
    return _spec_call("setBusInterfaceMirroredTarget", locals())


# F.7.20.42.
def setBusInterfaceMonitor(busInterfaceID: str, interfaceMode: str) -> bool:
    """Sets the bus interface mode to monitor.

    Args:
        busInterfaceID: Handle to an busInterface element
        interfaceMode: The interfaceMode value to be set on the monitor element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.42.
    """
    return _spec_call("setBusInterfaceMonitor", locals())


# F.7.20.43.
def setBusInterfaceRefLocalName(busInterfaceRefID: str, name: str) -> bool:
    """Returns the element localName on a busInterfaceRef of a channel element.

    Args:
        busInterfaceRefID: Handle to the identifier to a busInterfaceRef element
        name: BusInterface name

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.43.
    """
    return _spec_call("setBusInterfaceRefLocalName", locals())


# F.7.20.44.
def setBusInterfaceSystem(busInterfaceID: str, group: str) -> bool:
    """Sets the bus interface mode to system.

    Args:
        busInterfaceID: Handle to an busInterface element
        group: The group value to be set on the system element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.44.
    """
    return _spec_call("setBusInterfaceSystem", locals())


# F.7.20.45.
def setBusInterfaceTarget(busInterfaceID: str, memoryMapRef: str) -> bool:
    """Sets the bus interface mode to target.

    Args:
        busInterfaceID: Handle to an busInterface element
        memoryMapRef: The memoryMap reference set on the target element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.45.
    """
    return _spec_call("setBusInterfaceTarget", locals())


# F.7.20.46.
def setFileSetRefGroupGroup(fileSetRefGroupID: str, group: str) -> bool:
    """Sets the group on the given fileSetRefGroup element.

    Args:
        fileSetRefGroupID: Handle to a fileSetRefGroup element
        group: The group value to be set on the fileSetRefGroup element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.46.
    """
    return _spec_call("setFileSetRefGroupGroup", locals())


# F.7.20.47.
def setFileSetRefLocalName(fileSetRefID: str, localName: str) -> bool:
    """Sets the localName on a fileSetRef element.

    Args:
        fileSetRefID: Handle to a fileSetRef element
        localName: The local Name value to be set

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.47.
    """
    return _spec_call("setFileSetRefLocalName", locals())


# F.7.20.48.
def setIndirectInterfaceBitsInLau(indirectInterfaceID: str, bitsInLau: str) -> bool:
    """Sets the given bitsInLau expression for the indirectInterface element.

    Args:
        indirectInterfaceID: Handle to an indirectInterface element
        bitsInLau: BitsInLau expression

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.48.
    """
    return _spec_call("setIndirectInterfaceBitsInLau", locals())


# F.7.20.49.
def setInitiatorAddressSpaceRef(initiatorID: str, addressSpaceRef: str) -> bool:
    """Sets the addressSpaceRef on an initiator element of a busInterface.

    Args:
        initiatorID: Handle to an initiator element of a busInterface
        addressSpaceRef: The addressSpace reference to be set on the initiator element

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.49.
    """
    return _spec_call("setInitiatorAddressSpaceRef", locals())


# F.7.20.50.
def setMirroredSystemGroup(mirroredSystemID: str, group: str) -> bool:
    """Sets the group on the given mmirroredSystem element.

    Args:
        mirroredSystemID: Handle to a mirroredSystem element
        group: The group value to be set

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.50.
    """
    return _spec_call("setMirroredSystemGroup", locals())


# F.7.20.51.
def setMirroredTargetBaseAddresses(mirroredTargetID: str, remapAddress: str, range: str) -> bool:
    """Sets the baseAddresses for the given mirroredTarget element.

    Args:
        mirroredTargetID: Handle to a mirroredTarget element
        remapAddress: The new remapAddress expression
        range: The new range expression

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.51.
    """
    return _spec_call("setMirroredTargetBaseAddresses", locals())


# F.7.20.52.
def setMonitorGroup(monitorID: str, group: str) -> bool:
    """Sets the group on the given monitor element of a busInterface.

    Args:
        monitorID: Handle to a monitor element of a busInterface
        group: The group value to be set

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.52.
    """
    return _spec_call("setMonitorGroup", locals())


# F.7.20.53.
def setRemapAddressesRemapAddress(remapAddressesID: str, remapAddress: str) -> bool:
    """Sets the remapAddress from the given remapAddresses element.

    Args:
        remapAddressesID: Handle to a remapAddresses element
        remapAddress: The remapAddress value to be set

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.53.
    """
    return _spec_call("setRemapAddressesRemapAddress", locals())


# F.7.20.54.
def setSystemGroup(systemID: str, group: str) -> bool:
    """Sets the group on a system element of a busInterface.

    Args:
        systemID: Handle to a system element of a busInterface
        group: The group value to be set

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.54.
    """
    return _spec_call("setSystemGroup", locals())


# F.7.20.55.
def setTargetMemoryMapRef(targetID: str, memoryMapRef: str) -> bool:
    """Sets the memoryMap reference on a target element of a bus interface.

    Args:
        targetID: Handle to a target element of a busInterface
        memoryMapRef: The memoryMap reference to be set

    Returns:
        status: Indicates call is successful (true) or not (false)

    Section: F.7.20.55.
    """
    return _spec_call("setTargetMemoryMapRef", locals())


__all__ = [
    # Original compatibility exports retained in their original relative order.
    "getComponentBusInterfaceIDs",
    "getBusInterfaceName",
    "getBusInterfaceDisplayName",
    "getBusInterfaceDescription",
    "getBusInterfaceBusTypeRefByVLNV",
    "getBusInterfaceAbstractionTypeBusTypeViewRefsByVLNV",
    "getBusInterfaceConnectionRequired",
    "addBusInterface",
    "removeBusInterface",
    "setBusInterfaceBusTypeRefByVLNV",
    "addBusInterfaceAbstractionTypeBusTypeViewRef",
    # BASE (F.7.19), followed in standard order.
    "getAbstractionTypeAbstractionRefByID",
    "getAbstractionTypeAbstractionRefByVLNV",
    "getAbstractionTypePortMapIDs",
    "getAbstractionTypeViewRefByID",
    "getAbstractionTypeViewRefByNames",
    "getAbstractionTypeViewRefIDs",
    "getAddressSpaceRefBaseAddress",
    "getAddressSpaceRefBaseAddressExpression",
    "getAddressSpaceRefBaseAddressID",
    "getAddressSpaceRefModeRefByID",
    "getAddressSpaceRefModeRefByNames",
    "getBaseAddressesRange",
    "getBaseAddressesRangeExpression",
    "getBaseAddressesRangeID",
    "getBaseAddressesRemapAddressIDs",
    "getBusInterfaceAbstractionTypeIDs",
    "getBusInterfaceBitSteering",
    "getBusInterfaceBitSteeringExpression",
    "getBusInterfaceBitSteeringID",
    "getBusInterfaceBitsInLau",
    "getBusInterfaceBitsInLauExpression",
    "getBusInterfaceBitsInLauID",
    "getBusInterfaceBusTypeID",
    "getBusInterfaceBusTypeRefByID",
    "getBusInterfaceEndianness",
    "getBusInterfaceInitiatorID",
    "getBusInterfaceInterfaceMode",
    "getBusInterfaceMirroredSystemID",
    "getBusInterfaceMirroredTargetID",
    "getBusInterfaceMonitorID",
    "getBusInterfaceRefLocalName",
    "getBusInterfaceSystemID",
    "getBusInterfaceTargetID",
    "getChannelBusInterfaceRefByID",
    "getChannelBusInterfaceRefIDs",
    "getFileSetRefGroupGroup",
    "getIndirectInterfaceBitsInLauID",
    "getInitiatorAddressSpaceRefByName",
    "getInitiatorAddressSpaceRefID",
    "getMemoryMapRefModeRefByID",
    "getMemoryMapRefModeRefByNames",
    "getMirroredSystemGroup",
    "getMirroredTargetBaseAddressesID",
    "getMonitorGroup",
    "getRemapAddressModeRefByID",
    "getRemapAddressesRemapAddressID",
    "getSystemGroup",
    "getTargetFileSetRefGroupIDs",
    "getTargetMemoryMapRefByName",
    "getTargetMemoryMapRefID",
    "getTargetTransparentBridgeIDs",
    # EXTENDED (F.7.20), followed in standard order.
    "addAbstractionTypePortMap",
    "addAbstractionTypeViewRef",
    "addAddressSpaceRefModeRef",
    "addBaseAddressesRemapAddresses",
    "addBusInterfaceAbstractionType",
    "addChannelBusInterfaceRef",
    "addMemoryMapRefModeRef",
    "addTargetFileSetRefGroup",
    "addTargetTransparentBridge",
    "removeAbstractionTypePortMap",
    "removeAbstractionTypeViewRef",
    "removeAddressSpaceRefBaseAddress",
    "removeAddressSpaceRefModeRef",
    "removeBaseAddressesRemapAddresses",
    "removeBusDefinitionSystemGroupName",
    "removeBusInterfaceAbstractionType",
    "removeBusInterfaceBitSteering",
    "removeBusInterfaceBitsInLau",
    "removeBusInterfaceConnectionRequired",
    "removeBusInterfaceEndianness",
    "removeChannelBusInterfaceRef",
    "removeFileSetRefGroupGroup",
    "removeIndirectInterfaceBitsInLau",
    "removeInitiatorAddressSpaceRef",
    "removeMemoryMapRefModeRef",
    "removeMirroredTargetBaseAddresses",
    "removeMonitorGroup",
    "removeTargetFileSetRefGroup",
    "removeTargetMemoryMapRef",
    "removeTargetTransparentBridge",
    "setAddressSpaceRefBaseAddress",
    "setBaseAddressesRange",
    "setBusInterfaceBitSteering",
    "setBusInterfaceBitsInLau",
    "setBusInterfaceBusType",
    "setBusInterfaceConnectionRequired",
    "setBusInterfaceEndianness",
    "setBusInterfaceInitiator",
    "setBusInterfaceMirroredInitiator",
    "setBusInterfaceMirroredSystem",
    "setBusInterfaceMirroredTarget",
    "setBusInterfaceMonitor",
    "setBusInterfaceRefLocalName",
    "setBusInterfaceSystem",
    "setBusInterfaceTarget",
    "setFileSetRefGroupGroup",
    "setFileSetRefLocalName",
    "setIndirectInterfaceBitsInLau",
    "setInitiatorAddressSpaceRef",
    "setMirroredSystemGroup",
    "setMirroredTargetBaseAddresses",
    "setMonitorGroup",
    "setRemapAddressesRemapAddress",
    "setSystemGroup",
    "setTargetMemoryMapRef",
]
