"""Register category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.73) and EXTENDED (F.7.74) Register functions. Only the
functions defined in Annex F are exported. Most legacy BASE getters retain
their neutral invalid-handle behavior; register address and size operations
validate typed 2022 register handles. EXTENDED mutators raise :class:`TgiError`
with appropriate :class:`TgiFaultCode` values. Schema coverage remains partial.
"""

# ruff: noqa: I001
from types import SimpleNamespace
from typing import Any

from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.banked_block_type import BankedBlockType
from org.accellera.ipxact.v1685_2022.enumerated_values import EnumeratedValues
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.register_file_definitions import RegisterFileDefinitions
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.volatile import Volatile

from .component import _list_attr, _register_graph, _register_owner_for
from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)
from .register_file import _expression as _register_file_expression
from .register_file import _integer as _integer_expression
from .register_file import _numeric as _register_file_numeric
from .port_map import _name as _schema_name

__all__ = [
    # BASE (F.7.73)
    "getAliasOfAlternateRegisterRefByName",
    "getAliasOfAlternateRegisterRefID",
    "getAliasOfFieldRefByName",
    "getAliasOfFieldRefID",
    "getAliasOfRegisterRefByName",
    "getAliasOfRegisterRefID",
    "getAlternateRegisterFieldIDs",
    "getAlternateRegisterModeRefIDs",
    "getAlternateRegisterRefAlternateRegisterRefByName",
    "getAlternateRegisterTypeIdentifier",
    "getAlternateRegisterVolatility",
    "getBroadcastToAddressBlockRefByName",
    "getBroadcastToAddressBlockRefID",
    "getBroadcastToAddressSpaceRefByName",
    "getBroadcastToAddressSpaceRefID",
    "getBroadcastToAlternateRegisterRefByName",
    "getBroadcastToAlternateRegisterRefID",
    "getBroadcastToBankRefByNames",
    "getBroadcastToBankRefIDs",
    "getBroadcastToFieldRefByName",
    "getBroadcastToFieldRefID",
    "getBroadcastToMemoryMapRefByName",
    "getBroadcastToMemoryMapRefID",
    "getBroadcastToRegisterFileRefByNames",
    "getBroadcastToRegisterFileRefIDs",
    "getBroadcastToRegisterRefByName",
    "getBroadcastToRegisterRefID",
    "getEnumeratedValueExpression",
    "getEnumeratedValueUsage",
    "getEnumeratedValueValue",
    "getEnumeratedValueValueExpression",
    "getEnumeratedValueValueID",
    "getEnumeratedValuesEnumeratedValueIDs",
    "getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID",
    "getEnumeratedValuesEnumerationDefinitionRefByID",
    "getEnumeratedValuesEnumerationDefinitionRefByName",
    "getEnumeratedValuesEnumerationDefinitionRefID",
    "getFieldBitOffsetID",
    "getFieldDefinitionBitWidthID",
    "getFieldDefinitionEnumeratedValueIDs",
    "getFieldDefinitionTypeIdentifier",
    "getFieldDefinitionVolatile",
    "getFieldRefFieldRefByName",
    "getFieldRefIndexIDs",
    "getRegisterAddressOffset",
    "getRegisterAddressOffsetExpression",
    "getRegisterAddressOffsetID",
    "getRegisterAlternateRegisterIDs",
    "getRegisterFieldAliasOfID",
    "getRegisterFieldBitOffset",
    "getRegisterFieldBitOffsetExpression",
    "getRegisterFieldBitOffsetID",
    "getRegisterFieldBitWidth",
    "getRegisterFieldBitWidthExpression",
    "getRegisterFieldBitWidthID",
    "getRegisterFieldEnumeratedValuesID",
    "getRegisterFieldFieldDefinitionRefByExternalTypeDefID",
    "getRegisterFieldFieldDefinitionRefByID",
    "getRegisterFieldFieldDefinitionRefByName",
    "getRegisterFieldFieldDefinitionRefID",
    "getRegisterFieldIDs",
    "getRegisterFieldResetIDs",
    "getRegisterFieldTypeIdentifier",
    "getRegisterFieldVolatility",
    "getRegisterFileAddressOffsetID",
    "getRegisterRefAttributeByID",
    "getRegisterRefIndexIDs",
    "getRegisterRefRegisterRefByName",
    "getRegisterRegisterDefinitionRefByExternalTypeDefID",
    "getRegisterRegisterDefinitionRefByID",
    "getRegisterRegisterDefinitionRefByName",
    "getRegisterRegisterDefinitionRefID",
    "getRegisterSize",
    "getRegisterSizeExpression",
    "getRegisterSizeID",
    "getRegisterTypeIdentifier",
    "getRegisterVolatility",
    "getResetMask",
    "getResetMaskExpression",
    "getResetMaskID",
    "getResetValue",
    "getResetValueExpression",
    "getResetValueID",
    # EXTENDED (F.7.74)
    "addAlternateRegisterField",
    "addAlternaterRegisterModeRef",
    "addBroadcastToBankRef",
    "addBroadcastToRegisterFileRef",
    "addEnumeratedValuesFieldEnumeratedValue",
    "addFieldRefIndex",
    "addRegisterAlternateRegister",
    "addRegisterField",
    "addRegisterFieldReset",
    "addRegisterRefIndex",
    "removeAliasOfAlternateRegisterRef",
    "removeAliasOfRegisterRef",
    "removeAlternateRegisterField",
    "removeAlternateRegisterTypeIdentifier",
    "removeAlternateRegisterVolatility",
    "removeAlternaterRegisterModeRef",
    "removeBroadcastToAddressBlockRef",
    "removeBroadcastToAlternateRegisterRef",
    "removeBroadcastToBankRef",
    "removeBroadcastToMemoryMapRef",
    "removeBroadcastToRegisterFileRef",
    "removeBroadcastToRegisterRef",
    "removeRegisterFieldTypeIdentifier",
    "removeRegisterFieldVolatility",
    "removeRegisterTypeIdentifier",
    "removeRegisterVolatility",
    "setRegisterAddressOffset",
    "setRegisterFieldBitWidth",
    "setRegisterFieldTypeIdentifier",
    "setRegisterFieldVolatility",
    "setRegisterSize",
    "setRegisterTypeIdentifier",
    "setRegisterVolatility",
]

type _Register = (
    AddressBlockType.Register
    | BankedBlockType.Register
    | RegisterFile.Register
    | RegisterFileDefinitions.RegisterFileDefinition.Register
)
type _RegisterDefinitionRef = (
    AddressBlockType.Register.RegisterDefinitionRef
    | BankedBlockType.Register.RegisterDefinitionRef
    | RegisterFile.Register.RegisterDefinitionRef
    | RegisterFileDefinitions.RegisterFileDefinition.Register.RegisterDefinitionRef
)
_REGISTER_DEFINITION_REF_TYPES = (
    AddressBlockType.Register.RegisterDefinitionRef,
    BankedBlockType.Register.RegisterDefinitionRef,
    RegisterFile.Register.RegisterDefinitionRef,
    RegisterFileDefinitions.RegisterFileDefinition.Register.RegisterDefinitionRef,
)

_UINT32_MAX = (1 << 32) - 1
_UINT64_MAX = (1 << 64) - 1


def _resolve_register(registerID: str) -> _Register:
    register = resolve_handle(registerID)
    if not isinstance(
        register,
        (
            AddressBlockType.Register,
            BankedBlockType.Register,
            RegisterFile.Register,
            RegisterFileDefinitions.RegisterFileDefinition.Register,
        ),
    ):
        raise TgiError("Invalid register handle", TgiFaultCode.INVALID_ID)
    _register_graph(register)
    return register


def _resolve_field(fieldID: str) -> FieldType:
    field = resolve_handle(fieldID)
    if not isinstance(field, FieldType):
        raise TgiError("Invalid field handle", TgiFaultCode.INVALID_ID)
    _register_graph(field)
    return field


def _resolve_register_field(registerFieldID: str) -> tuple[FieldType, _Register | None]:
    field = resolve_handle(registerFieldID)
    if not isinstance(field, FieldType):
        raise TgiError("Invalid register field handle", TgiFaultCode.INVALID_ID)
    _register_owner_for(field)
    parent = resolve_handle(registerFieldID)
    seen: set[int] = set()
    while parent is not None and id(parent) not in seen:
        if isinstance(parent, _REGISTER_TYPES):
            _register_graph(parent)
            return field, parent
        seen.add(id(parent))
        info = get_parent_info(get_handle(parent))
        parent = resolve_handle(info.parent_handle) if info is not None else None
    return field, None


_REGISTER_TYPES = (
    AddressBlockType.Register,
    BankedBlockType.Register,
    RegisterFile.Register,
    RegisterFileDefinitions.RegisterFileDefinition.Register,
)


def _register_field_bit_offset(field: FieldType) -> UnsignedIntExpression:
    offset = getattr(field, "bit_offset", None)
    if not isinstance(offset, UnsignedIntExpression):
        raise TgiError("Invalid register field bitOffset model", TgiFaultCode.INVALID_ID)
    register_parent(offset, field, ("bit_offset",), "single")
    return offset


def _register_field_width_state(
    field: FieldType,
) -> tuple[UnsignedPositiveIntExpression | None, FieldType.FieldDefinitionRef | None, FieldType.AliasOf | None]:
    choice = getattr(field, "choice", ())
    if not isinstance(choice, (list, tuple)):
        raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
    widths = [child for child in choice if isinstance(child, UnsignedPositiveIntExpression)]
    references = [child for child in choice if isinstance(child, FieldType.FieldDefinitionRef)]
    aliases = [child for child in choice if isinstance(child, FieldType.AliasOf)]
    multiple_branches = sum(bool(group) for group in (widths, references, aliases)) > 1
    if len(widths) > 1 or len(references) > 1 or len(aliases) > 1 or multiple_branches:
        raise TgiError("Invalid register field bitWidth choice", TgiFaultCode.INVALID_ID)
    return (widths[0] if widths else None, references[0] if references else None, aliases[0] if aliases else None)


def _register_field_type_identifier(field: FieldType) -> str | None:
    identifiers = [child for child in getattr(field, "choice", ()) if isinstance(child, str)]
    if len(identifiers) > 1:
        raise TgiError("Multiple register field typeIdentifiers", TgiFaultCode.INVALID_ID)
    return identifiers[0] if identifiers else None


def _register_field_volatile(field: FieldType) -> bool | None:
    values = [child for child in getattr(field, "choice", ()) if type(child) is bool]
    if len(values) > 1:
        raise TgiError("Multiple register field volatile values", TgiFaultCode.INVALID_ID)
    return values[0] if values else None


def _register_field_bit_width(field: FieldType) -> UnsignedPositiveIntExpression | None:
    width, _, _ = _register_field_width_state(field)
    if width is not None:
        register_parent(width, field, ("choice",), "list")
    return width


def _check_register_field_containment(register: _Register | None, field: FieldType, width: int | None) -> None:
    if register is None or width is None or field.array is not None:
        return
    size_node = _register_size(register)
    if size_node is None:
        return
    size = _integer_expression(size_node.value, _UINT32_MAX, True)
    if size is None:
        return
    if (size_node.minimum is not None and size < size_node.minimum) or (
        size_node.maximum is not None and size > size_node.maximum
    ):
        raise TgiError("Register size is outside its declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    offset_node = _register_field_bit_offset(field)
    offset = _integer_expression(offset_node.value, _UINT32_MAX, True)
    if offset is None:
        return
    if (offset_node.minimum is not None and offset < offset_node.minimum) or (
        offset_node.maximum is not None and offset > offset_node.maximum
    ):
        raise TgiError("Register field bitOffset is outside its declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    if offset + width > size:
        raise TgiError("Register field bitWidth would extend beyond the register size", TgiFaultCode.INVALID_ARGUMENT)


def _register_address_offset(register: _Register) -> UnsignedLongintExpression:
    offset = getattr(register, "address_offset", None)
    if not isinstance(offset, UnsignedLongintExpression):
        raise TgiError("Invalid register addressOffset model", TgiFaultCode.INVALID_ID)
    register_parent(offset, register, ("address_offset",), "single")
    return offset


def _register_size(register: _Register) -> UnsignedPositiveIntExpression | None:
    sizes = [child for child in getattr(register, "choice", ()) if isinstance(child, UnsignedPositiveIntExpression)]
    if len(sizes) > 1:
        raise TgiError("Multiple register sizes", TgiFaultCode.INVALID_ID)
    references = [
        child for child in getattr(register, "choice", ()) if isinstance(child, _REGISTER_DEFINITION_REF_TYPES)
    ]
    if len(references) > 1 or (references and sizes):
        raise TgiError("Invalid register definition choice", TgiFaultCode.INVALID_ID)
    if sizes:
        register_parent(sizes[0], register, ("choice",), "list")
        return sizes[0]
    return None


def _register_definition_reference(register: _Register) -> _RegisterDefinitionRef | None:
    references = [
        child for child in getattr(register, "choice", ()) if isinstance(child, _REGISTER_DEFINITION_REF_TYPES)
    ]
    if len(references) > 1:
        raise TgiError("Multiple register definition references", TgiFaultCode.INVALID_ID)
    return references[0] if references else None


def _register_type_identifier(register: _Register) -> str | None:
    identifiers = [child for child in getattr(register, "choice", ()) if isinstance(child, str)]
    if len(identifiers) > 1:
        raise TgiError("Multiple register typeIdentifiers", TgiFaultCode.INVALID_ID)
    return identifiers[0] if identifiers else None


def _register_volatile(register: _Register) -> Volatile | None:
    volatiles = [child for child in getattr(register, "choice", ()) if isinstance(child, Volatile)]
    if len(volatiles) > 1:
        raise TgiError("Multiple register volatile values", TgiFaultCode.INVALID_ID)
    if volatiles:
        register_parent(volatiles[0], register, ("choice",), "list")
        return volatiles[0]
    return None


def _inline_register_choice(register: _Register, requirement: str) -> UnsignedPositiveIntExpression:
    size = _register_size(register)
    if _register_definition_reference(register) is not None:
        raise TgiError(f"{requirement} requires an inline register definition", TgiFaultCode.INVALID_ARGUMENT)
    if size is None:
        raise TgiError(f"{requirement} requires an inline register size", TgiFaultCode.INVALID_ARGUMENT)
    return size


def _check_field_containment(register: _Register, size: int | None) -> None:
    """Reject known inline scalar fields extending past a known replacement size.

    Array replication and referenced field-definition widths need additional
    effective-width resolution and remain outside this setter's containment check.
    """
    if size is None:
        return
    for field in getattr(register, "choice", ()):
        if not isinstance(field, FieldType) or field.array is not None:
            continue
        widths = [child for child in field.choice if isinstance(child, UnsignedPositiveIntExpression)]
        if len(widths) > 1:
            raise TgiError("Multiple register field bitWidths", TgiFaultCode.INVALID_ID)
        if not widths:
            continue
        if not isinstance(field.bit_offset, UnsignedIntExpression):
            raise TgiError("Invalid register field bitOffset model", TgiFaultCode.INVALID_ID)
        offset = _integer_expression(field.bit_offset.value, _UINT32_MAX, True)
        width = _integer_expression(widths[0].value, _UINT32_MAX, True)
        if offset is not None and offset < 0:
            raise TgiError("Register field bitOffset is negative", TgiFaultCode.INVALID_ARGUMENT)
        if width is not None and width < 1:
            raise TgiError("Register field bitWidth is not positive", TgiFaultCode.INVALID_ARGUMENT)
        for node, number, label in (
            (field.bit_offset, offset, "bitOffset"),
            (widths[0], width, "bitWidth"),
        ):
            if number is not None and (
                (node.minimum is not None and number < node.minimum)
                or (node.maximum is not None and number > node.maximum)
            ):
                raise TgiError(f"Register field {label} is outside its declared bounds", TgiFaultCode.INVALID_ARGUMENT)
        if offset is not None and width is not None and offset + width > size:
            raise TgiError("Register size would exclude an existing field", TgiFaultCode.INVALID_ARGUMENT)


def _replace_register_choice(register: _Register, choice: UnsignedPositiveIntExpression) -> None:
    items = _list_attr(register, "choice")
    for child in list(items):
        if isinstance(child, str):
            items.remove(child)
            continue
        child_handle = get_handle(child)
        register_parent(child, register, ("choice",), "list")
        _register_graph(child)
        if not detach_child_by_handle(child_handle):
            raise TgiError("Could not replace register definition choice", TgiFaultCode.INVALID_ID)
    items.append(choice)
    register_parent(choice, register, ("choice",), "list")
    _register_graph(choice)


# ---------------------------------------------------------------------------
# Internal helper utilities (non-spec)
# ---------------------------------------------------------------------------


def _resolve(handle: str) -> Any | None:
    return resolve_handle(handle)


def _maybe_value(node: Any | None) -> Any | None:
    if node is None:
        return None
    return getattr(node, "value", node)


def _list_handles(container: Any | None, attr: str) -> list[str]:
    if container is None:
        return []
    lst = getattr(container, attr, [])
    return [get_handle(e) for e in lst]


def _coerce_int(value: str) -> int | str:
    """Best-effort convert to int (supports bases)."""
    try:
        return int(value, 0)
    except Exception:  # noqa: BLE001
        return value


def _ns(**kwargs: Any) -> SimpleNamespace:
    return SimpleNamespace(**kwargs)


# ---------------------------------------------------------------------------
# BASE (F.7.73) – many getters are thin wrappers over attribute presence
# NOTE: Many legacy getters retain graceful defaults where the model linkage is
# incomplete. Register address and size operations use typed 1685-2022 models.
# ---------------------------------------------------------------------------
# The following block uses repetitive patterns; each function retains a short
# docstring referencing its Section number for traceability.


def getAliasOfAlternateRegisterRefByName(aliasOfID: str) -> str | None:
    """Return alternateRegisterRef value (F.7.73.1)."""
    a = _resolve(aliasOfID)
    ref = getattr(a, "alternate_register_ref", None)
    return _maybe_value(ref)


def getAliasOfAlternateRegisterRefID(aliasOfID: str) -> str | None:
    """Return handle of alternateRegisterRef (F.7.73.2)."""
    a = _resolve(aliasOfID)
    ref = getattr(a, "alternate_register_ref", None)
    return get_handle(ref) if ref is not None else None


def getAliasOfFieldRefByName(aliasOfID: str) -> str | None:
    """Return fieldRef value (F.7.73.3)."""
    a = _resolve(aliasOfID)
    ref = getattr(a, "field_ref", None)
    return _maybe_value(ref)


def getAliasOfFieldRefID(aliasOfID: str) -> str | None:
    """Return handle of fieldRef (F.7.73.4)."""
    a = _resolve(aliasOfID)
    ref = getattr(a, "field_ref", None)
    return get_handle(ref) if ref is not None else None


def getAliasOfRegisterRefByName(aliasOfID: str) -> str | None:
    """Return registerRef value (F.7.73.5)."""
    a = _resolve(aliasOfID)
    ref = getattr(a, "register_ref", None)
    return _maybe_value(ref)


def getAliasOfRegisterRefID(aliasOfID: str) -> str | None:
    """Return handle of registerRef (F.7.73.6)."""
    a = _resolve(aliasOfID)
    ref = getattr(a, "register_ref", None)
    return get_handle(ref) if ref is not None else None


def getAlternateRegisterFieldIDs(alternateRegisterID: str) -> list[str]:
    """Return field handles of alternateRegister (F.7.73.7)."""
    ar = _resolve(alternateRegisterID)
    return _list_handles(ar, "field")


def getAlternateRegisterModeRefIDs(alternateRegisterID: str) -> list[str]:
    """Return modeRef handles (F.7.73.8)."""
    ar = _resolve(alternateRegisterID)
    return _list_handles(ar, "mode_ref")


def getAlternateRegisterRefAlternateRegisterRefByName(alternateRegisterRefID: str) -> str | None:
    """Return alternateRegisterRef value (F.7.73.9)."""
    r = _resolve(alternateRegisterRefID)
    return _maybe_value(getattr(r, "alternate_register_ref", None))


def getAlternateRegisterTypeIdentifier(alternateRegisterID: str) -> str | None:
    """Return typeIdentifier value (F.7.73.10)."""
    ar = _resolve(alternateRegisterID)
    return _maybe_value(getattr(ar, "type_identifier", None))


def getAlternateRegisterVolatility(alternateRegisterID: str) -> bool | None:
    """Return volatility boolean (F.7.73.11)."""
    ar = _resolve(alternateRegisterID)
    val = getattr(getattr(ar, "volatile", None), "value", None)
    return val if isinstance(val, bool) else None


# BroadcastTo getters (grouped)


def getBroadcastToAddressBlockRefByName(broadcastToID: str) -> str | None:
    """Return addressBlockRef value (F.7.73.12)."""
    b = _resolve(broadcastToID)
    return _maybe_value(getattr(b, "address_block_ref", None))


def getBroadcastToAddressBlockRefID(broadcastToID: str) -> str | None:
    """Return handle of addressBlockRef (F.7.73.13)."""
    b = _resolve(broadcastToID)
    ref = getattr(b, "address_block_ref", None)
    return get_handle(ref) if ref is not None else None


def getBroadcastToAddressSpaceRefByName(broadcastToID: str) -> str | None:
    """Return addressSpaceRef value (F.7.73.14)."""
    b = _resolve(broadcastToID)
    return _maybe_value(getattr(b, "address_space_ref", None))


def getBroadcastToAddressSpaceRefID(broadcastToID: str) -> str | None:
    """Return handle of addressSpaceRef (F.7.73.15)."""
    b = _resolve(broadcastToID)
    ref = getattr(b, "address_space_ref", None)
    return get_handle(ref) if ref is not None else None


def getBroadcastToAlternateRegisterRefByName(broadcastToID: str) -> str | None:
    """Return alternateRegisterRef value (F.7.73.16)."""
    b = _resolve(broadcastToID)
    return _maybe_value(getattr(b, "alternate_register_ref", None))


def getBroadcastToAlternateRegisterRefID(broadcastToID: str) -> str | None:
    """Return handle of alternateRegisterRef (F.7.73.17)."""
    b = _resolve(broadcastToID)
    ref = getattr(b, "alternate_register_ref", None)
    return get_handle(ref) if ref is not None else None


def getBroadcastToBankRefByNames(broadcastToID: str) -> list[str]:
    """Return list of bankRef values (F.7.73.18)."""
    b = _resolve(broadcastToID)
    vals = getattr(b, "bank_ref", []) if b else []
    result: list[str] = []
    for v in vals:
        val = getattr(v, "value", v)
        if val is not None:
            result.append(str(val))
    return result


def getBroadcastToBankRefIDs(broadcastToID: str) -> list[str]:
    """Return handles of bankRef elements (F.7.73.19)."""
    b = _resolve(broadcastToID)
    return _list_handles(b, "bank_ref")


def getBroadcastToFieldRefByName(broadcastToID: str) -> str | None:
    """Return fieldRef value (F.7.73.20)."""
    b = _resolve(broadcastToID)
    return _maybe_value(getattr(b, "field_ref", None))


def getBroadcastToFieldRefID(broadcastToID: str) -> str | None:
    """Return handle of fieldRef (F.7.73.21)."""
    b = _resolve(broadcastToID)
    ref = getattr(b, "field_ref", None)
    return get_handle(ref) if ref is not None else None


def getBroadcastToMemoryMapRefByName(broadcastToID: str) -> str | None:
    """Return memoryMapRef value (F.7.73.22)."""
    b = _resolve(broadcastToID)
    return _maybe_value(getattr(b, "memory_map_ref", None))


def getBroadcastToMemoryMapRefID(broadcastToID: str) -> str | None:
    """Return handle of memoryMapRef (F.7.73.23)."""
    b = _resolve(broadcastToID)
    ref = getattr(b, "memory_map_ref", None)
    return get_handle(ref) if ref is not None else None


def getBroadcastToRegisterFileRefByNames(broadcastToID: str) -> list[str]:
    """Return registerFileRef names (F.7.73.24)."""
    b = _resolve(broadcastToID)
    refs = getattr(b, "register_file_ref", []) if b else []
    out: list[str] = []
    for r in refs:
        val = getattr(r, "value", r)
        if val is not None:
            out.append(str(val))
    return out


def getBroadcastToRegisterFileRefIDs(broadcastToID: str) -> list[str]:
    """Return handles of registerFileRef elements (F.7.73.25)."""
    b = _resolve(broadcastToID)
    return _list_handles(b, "register_file_ref")


def getBroadcastToRegisterRefByName(broadcastToID: str) -> str | None:
    """Return registerRef value (F.7.73.26)."""
    b = _resolve(broadcastToID)
    return _maybe_value(getattr(b, "register_ref", None))


def getBroadcastToRegisterRefID(broadcastToID: str) -> str | None:
    """Return handle of registerRef (F.7.73.27)."""
    b = _resolve(broadcastToID)
    ref = getattr(b, "register_ref", None)
    return get_handle(ref) if ref is not None else None


# EnumeratedValue(s)


def getEnumeratedValueExpression(enumeratedValueID: str) -> str | None:
    """Return expression (F.7.73.28)."""
    ev = _resolve(enumeratedValueID)
    return _maybe_value(getattr(ev, "expression", None))


def getEnumeratedValueUsage(enumeratedValueID: str) -> str | None:
    """Return usage (F.7.73.29)."""
    ev = _resolve(enumeratedValueID)
    return _maybe_value(getattr(ev, "usage", None))


def getEnumeratedValueValue(enumeratedValueID: str) -> int | None:
    """Return numeric value (F.7.73.30)."""
    ev = _resolve(enumeratedValueID)
    val = getattr(getattr(ev, "value", None), "value", None)
    return int(val) if isinstance(val, int | bool) else None


def getEnumeratedValueValueExpression(enumeratedValueID: str) -> str | None:
    """Return value expression (F.7.73.31)."""
    ev = _resolve(enumeratedValueID)
    value = getattr(ev, "value", None)
    return getattr(value, "value_expression", None)


def getEnumeratedValueValueID(enumeratedValueID: str) -> str | None:
    """Return handle of value element (F.7.73.32)."""
    ev = _resolve(enumeratedValueID)
    value = getattr(ev, "value", None)
    return get_handle(value) if value is not None else None


def getEnumeratedValuesEnumeratedValueIDs(enumeratedValuesID: str) -> list[str]:
    """Return enumeratedValue handles (F.7.73.33)."""
    evs = _resolve(enumeratedValuesID)
    return _list_handles(evs, "enumerated_value")


def getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(enumeratedValuesID: str) -> str | None:
    """Return externalTypeDefinitions handle (F.7.73.34)."""
    evs = _resolve(enumeratedValuesID)
    ref = getattr(getattr(evs, "enumeration_definition_ref", None), "external_type_definitions", None)
    return get_handle(ref) if ref is not None else None


def getEnumeratedValuesEnumerationDefinitionRefByID(enumeratedValuesID: str) -> str | None:
    """Return enumerationDefinition handle (F.7.73.35)."""
    evs = _resolve(enumeratedValuesID)
    ref = getattr(getattr(evs, "enumeration_definition_ref", None), "enumeration_definition", None)
    return get_handle(ref) if ref is not None else None


def getEnumeratedValuesEnumerationDefinitionRefByName(enumeratedValuesID: str) -> str | None:
    """Return enumerationDefinitionRef value (F.7.73.36)."""
    evs = _resolve(enumeratedValuesID)
    ref = getattr(evs, "enumeration_definition_ref", None)
    return _maybe_value(ref)


def getEnumeratedValuesEnumerationDefinitionRefID(enumeratedValuesID: str) -> str | None:
    """Return handle of enumerationDefinitionRef (F.7.73.37)."""
    evs = _resolve(enumeratedValuesID)
    ref = getattr(evs, "enumeration_definition_ref", None)
    return get_handle(ref) if ref is not None else None


# Field / FieldDefinition / FieldRef


def getFieldBitOffsetID(fieldID: str) -> str | None:
    """Return the owned bitOffset handle (F.7.73.38).

    Section: F.7.73.38.

    Args:
        fieldID: Handle to a field element.

    Returns:
        Handle to the field's unsigned bitOffset expression.
    """
    field = _resolve_field(fieldID)
    return get_handle(_register_field_bit_offset(field))


def getFieldDefinitionBitWidthID(fieldDefinitionID: str) -> str | None:
    """Return bitWidth handle (F.7.73.39)."""
    fd = _resolve(fieldDefinitionID)
    bw = getattr(fd, "bit_width", None)
    return get_handle(bw) if bw is not None else None


def getFieldDefinitionEnumeratedValueIDs(fieldDefinitionID: str) -> list[str]:
    """Return enumeratedValue handles (F.7.73.40)."""
    fd = _resolve(fieldDefinitionID)
    return _list_handles(fd, "enumerated_value")


def getFieldDefinitionTypeIdentifier(fieldDefinitionID: str) -> str | None:
    """Return typeIdentifier (F.7.73.41)."""
    fd = _resolve(fieldDefinitionID)
    return _maybe_value(getattr(fd, "type_identifier", None))


def getFieldDefinitionVolatile(fieldDefinitionID: str) -> bool | None:
    """Return volatile flag (F.7.73.42)."""
    fd = _resolve(fieldDefinitionID)
    val = getattr(getattr(fd, "volatile", None), "value", None)
    return val if isinstance(val, bool) else None


def getFieldRefFieldRefByName(fieldRefID: str) -> str | None:
    """Return fieldRef value (F.7.73.43)."""
    fr = _resolve(fieldRefID)
    return _maybe_value(getattr(fr, "field_ref", None))


def getFieldRefIndexIDs(fieldRefID: str) -> list[str]:
    """Return index handles (F.7.73.44)."""
    fr = _resolve(fieldRefID)
    return _list_handles(fr, "index")


# Register (address / size / type)


def getRegisterAddressOffset(registerID: str) -> int | None:
    """Return evaluated unsigned 64-bit addressOffset (F.7.73.45).

    Section: F.7.73.45.

    Args:
        registerID: Handle to a register element.

    Returns:
        Evaluated addressOffset; unresolved expressions fault.
    """
    offset = _register_address_offset(_resolve_register(registerID))
    return _register_file_numeric(offset, "addressOffset", 0, _UINT64_MAX)


def getRegisterAddressOffsetExpression(registerID: str) -> str | None:
    """Return addressOffset source text (F.7.73.46).

    Section: F.7.73.46.

    Args:
        registerID: Handle to a register element.

    Returns:
        The stored addressOffset expression.
    """
    return _register_address_offset(_resolve_register(registerID)).value


def getRegisterAddressOffsetID(registerID: str) -> str | None:
    """Return addressOffset handle (F.7.73.47).

    Section: F.7.73.47.

    Args:
        registerID: Handle to a register element.

    Returns:
        Handle to the owned addressOffset expression.
    """
    return get_handle(_register_address_offset(_resolve_register(registerID)))


def getRegisterAlternateRegisterIDs(registerID: str) -> list[str]:
    """Return alternateRegister handles (F.7.73.48)."""
    r = _resolve(registerID)
    return _list_handles(r, "alternate_register")


# Register Field getters (aliases, offsets, widths, enumeratedValues, resets)


def getRegisterFieldAliasOfID(registerFieldID: str) -> str | None:
    """Return aliasOf handle (F.7.73.49)."""
    f = _resolve(registerFieldID)
    ao = getattr(f, "alias_of", None)
    return get_handle(ao) if ao is not None else None


def getRegisterFieldBitOffset(registerFieldID: str) -> int | None:
    """Return the evaluated unsigned 32-bit bitOffset (F.7.73.50).

    Section: F.7.73.50.

    Args:
        registerFieldID: Handle to a field owned by a register.

    Returns:
        Evaluated bitOffset; an unresolved expression faults.
    """
    field, _ = _resolve_register_field(registerFieldID)
    return _register_file_numeric(_register_field_bit_offset(field), "bitOffset", 0, _UINT32_MAX)


def getRegisterFieldBitOffsetExpression(registerFieldID: str) -> str | None:
    """Return the stored bitOffset source expression (F.7.73.51).

    Section: F.7.73.51.

    Args:
        registerFieldID: Handle to a field owned by a register.

    Returns:
        The bitOffset expression text.
    """
    field, _ = _resolve_register_field(registerFieldID)
    return _register_field_bit_offset(field).value


def getRegisterFieldBitOffsetID(registerFieldID: str) -> str | None:
    """Return the owned bitOffset handle (F.7.73.52).

    Section: F.7.73.52.

    Args:
        registerFieldID: Handle to a field owned by a register.

    Returns:
        Handle to the field's unsigned bitOffset expression.
    """
    field, _ = _resolve_register_field(registerFieldID)
    return get_handle(_register_field_bit_offset(field))


def getRegisterFieldBitWidth(registerFieldID: str) -> int | None:
    """Return the evaluated positive unsigned 32-bit bitWidth (F.7.73.53).

    Section: F.7.73.53.

    Args:
        registerFieldID: Handle to a field owned by a register.

    Returns:
        Evaluated inline bitWidth, or None for a field definition reference.
    """
    field, _ = _resolve_register_field(registerFieldID)
    width = _register_field_bit_width(field)
    return _register_file_numeric(width, "bitWidth", 1, _UINT32_MAX)


def getRegisterFieldBitWidthExpression(registerFieldID: str) -> str | None:
    """Return the stored bitWidth source expression (F.7.73.54).

    Section: F.7.73.54.

    Args:
        registerFieldID: Handle to a field owned by a register.

    Returns:
        The inline bitWidth expression text, or None for a reference choice.
    """
    field, _ = _resolve_register_field(registerFieldID)
    width = _register_field_bit_width(field)
    return width.value if width is not None else None


def getRegisterFieldBitWidthID(registerFieldID: str) -> str | None:
    """Return the owned bitWidth handle (F.7.73.55).

    Section: F.7.73.55.

    Args:
        registerFieldID: Handle to a field owned by a register.

    Returns:
        Handle to the inline bitWidth expression, or None for a reference choice.
    """
    field, _ = _resolve_register_field(registerFieldID)
    width = _register_field_bit_width(field)
    return get_handle(width) if width is not None else None


def getRegisterFieldEnumeratedValuesID(registerFieldID: str) -> str | None:
    """Return enumeratedValues handle (F.7.73.56)."""
    f = _resolve(registerFieldID)
    evs = getattr(f, "enumerated_values", None)
    return get_handle(evs) if evs is not None else None


def getRegisterFieldFieldDefinitionRefByExternalTypeDefID(registerFieldID: str) -> str | None:
    """Return externalTypeDefinitions handle (F.7.73.57)."""
    f = _resolve(registerFieldID)
    ref = getattr(getattr(f, "field_definition_ref", None), "external_type_definitions", None)
    return get_handle(ref) if ref is not None else None


def getRegisterFieldFieldDefinitionRefByID(registerFieldID: str) -> str | None:
    """Return fieldDefinition handle (F.7.73.58)."""
    f = _resolve(registerFieldID)
    ref = getattr(getattr(f, "field_definition_ref", None), "field_definition", None)
    return get_handle(ref) if ref is not None else None


def getRegisterFieldFieldDefinitionRefByName(registerFieldID: str) -> str | None:
    """Return fieldDefinitionRef value (F.7.73.59)."""
    f = _resolve(registerFieldID)
    ref = getattr(f, "field_definition_ref", None)
    return _maybe_value(ref)


def getRegisterFieldFieldDefinitionRefID(registerFieldID: str) -> str | None:
    """Return fieldDefinitionRef handle (F.7.73.60)."""
    f = _resolve(registerFieldID)
    ref = getattr(f, "field_definition_ref", None)
    return get_handle(ref) if ref is not None else None


def getRegisterFieldIDs(registerID: str) -> list[str]:
    """Return register field handles (F.7.73.61)."""
    r = _resolve(registerID)
    return _list_handles(r, "field")


def getRegisterFieldResetIDs(registerFieldID: str) -> list[str]:
    """Return reset handles (F.7.73.62)."""
    f = _resolve(registerFieldID)
    return _list_handles(f, "reset")


def getRegisterFieldTypeIdentifier(registerFieldID: str) -> str | None:
    """Return an inline register field typeIdentifier (F.7.73.63).

    Section: F.7.73.63.

    Args:
        registerFieldID: Handle to a register field element.

    Returns:
        The typeIdentifier for an inline-width or alias field, or None for a field-definition reference.
    """
    field, _ = _resolve_register_field(registerFieldID)
    width, reference, alias = _register_field_width_state(field)
    if reference is not None:
        return None
    if width is None and alias is None:
        raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
    return _register_field_type_identifier(field)


def getRegisterFieldVolatility(registerFieldID: str) -> bool | None:
    """Return register field volatility (F.7.73.64).

    Section: F.7.73.64.

    Args:
        registerFieldID: Handle to a register field element.

    Returns:
        The explicit volatility, False by default for inline-width fields, or None for alias and reference fields.
    """
    field, _ = _resolve_register_field(registerFieldID)
    width, reference, alias = _register_field_width_state(field)
    if width is None:
        if reference is not None or alias is not None:
            return None
        raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
    volatile = _register_field_volatile(field)
    return False if volatile is None else volatile


def getRegisterFileAddressOffsetID(registerFileID: str) -> str | None:
    """Return addressOffset handle (F.7.73.65)."""
    rf = _resolve(registerFileID)
    off = getattr(rf, "address_offset", None)
    return get_handle(off) if off is not None else None


# RegisterRef


def getRegisterRefAttributeByID(registerRefID: str) -> str | None:
    """Return referenced register handle (F.7.73.66)."""
    rr = _resolve(registerRefID)
    reg = getattr(rr, "register", None)
    return get_handle(reg) if reg is not None else None


def getRegisterRefIndexIDs(registerRefID: str) -> list[str]:
    """Return index handles (F.7.73.67)."""
    rr = _resolve(registerRefID)
    return _list_handles(rr, "index")


def getRegisterRefRegisterRefByName(registerRefID: str) -> str | None:
    """Return registerRef value (F.7.73.68)."""
    rr = _resolve(registerRefID)
    return _maybe_value(getattr(rr, "register_ref", None))


# Register definition references


def getRegisterRegisterDefinitionRefByExternalTypeDefID(registerID: str) -> str | None:
    """Return externalTypeDefinitions handle (F.7.73.69)."""
    r = _resolve(registerID)
    ref = getattr(getattr(r, "register_definition_ref", None), "external_type_definitions", None)
    return get_handle(ref) if ref is not None else None


def getRegisterRegisterDefinitionRefByID(registerID: str) -> str | None:
    """Return registerDefinition handle (F.7.73.70)."""
    r = _resolve(registerID)
    ref = getattr(getattr(r, "register_definition_ref", None), "register_definition", None)
    return get_handle(ref) if ref is not None else None


def getRegisterRegisterDefinitionRefByName(registerID: str) -> str | None:
    """Return registerDefinitionRef value (F.7.73.71)."""
    r = _resolve(registerID)
    ref = getattr(r, "register_definition_ref", None)
    return _maybe_value(ref)


def getRegisterRegisterDefinitionRefID(registerID: str) -> str | None:
    """Return registerDefinitionRef handle (F.7.73.72)."""
    r = _resolve(registerID)
    ref = getattr(r, "register_definition_ref", None)
    return get_handle(ref) if ref is not None else None


# Size / type / volatility


def getRegisterSize(registerID: str) -> int | None:
    """Return evaluated inline unsigned positive 32-bit size (F.7.73.73).

    Section: F.7.73.73.

    Args:
        registerID: Handle to a register element.

    Returns:
        Evaluated inline size, or None when the register uses a definition reference.
    """
    size = _register_size(_resolve_register(registerID))
    return _register_file_numeric(size, "size", 1, _UINT32_MAX)


def getRegisterSizeExpression(registerID: str) -> str | None:
    """Return stored inline size expression text (F.7.73.74).

    Section: F.7.73.74.

    Args:
        registerID: Handle to a register element.

    Returns:
        Inline size source text, or None when the register uses a definition reference.
    """
    size = _register_size(_resolve_register(registerID))
    return size.value if size is not None else None


def getRegisterSizeID(registerID: str) -> str | None:
    """Return inline size handle (F.7.73.75).

    Section: F.7.73.75.

    Args:
        registerID: Handle to a register element.

    Returns:
        Handle to the owned size expression, or None for a definition reference.
    """
    size = _register_size(_resolve_register(registerID))
    return get_handle(size) if size is not None else None


def getRegisterTypeIdentifier(registerID: str) -> str | None:
    """Return inline typeIdentifier (F.7.73.76).

    Section: F.7.73.76.

    Args:
        registerID: Handle to a register element.

    Returns:
        Inline typeIdentifier, or None when absent or a definition reference is used.
    """
    register = _resolve_register(registerID)
    _register_size(register)
    if _register_definition_reference(register) is not None:
        return None
    return _register_type_identifier(register)


def getRegisterVolatility(registerID: str) -> bool | None:
    """Return volatility boolean (F.7.73.77).

    Section: F.7.73.77.

    Args:
        registerID: Handle to a register element.

    Returns:
        Explicit volatility value, or None when it is absent or a definition reference is used.
    """
    register = _resolve_register(registerID)
    _register_size(register)
    if _register_definition_reference(register) is not None:
        return None
    volatile = _register_volatile(register)
    if volatile is None:
        return None
    if type(volatile.value) is not bool:
        raise TgiError("Invalid register volatile value", TgiFaultCode.INVALID_ID)
    return volatile.value


# Reset values


def getResetMask(resetID: str) -> int | None:
    """Return reset mask resolved value (F.7.73.78)."""
    rst = _resolve(resetID)
    m = getattr(rst, "mask", None)
    val = getattr(m, "value", None)
    return int(val) if isinstance(val, int) else None


def getResetMaskExpression(resetID: str) -> str | None:
    """Return reset mask expression (F.7.73.79)."""
    rst = _resolve(resetID)
    m = getattr(rst, "mask", None)
    return getattr(m, "value_expression", None)


def getResetMaskID(resetID: str) -> str | None:
    """Return mask handle (F.7.73.80)."""
    rst = _resolve(resetID)
    m = getattr(rst, "mask", None)
    return get_handle(m) if m is not None else None


def getResetValue(resetID: str) -> int | None:
    """Return reset value (F.7.73.81)."""
    rst = _resolve(resetID)
    v = getattr(rst, "value", None)
    val = getattr(v, "value", None)
    return int(val) if isinstance(val, int) else None


def getResetValueExpression(resetID: str) -> str | None:
    """Return reset value expression (F.7.73.82)."""
    rst = _resolve(resetID)
    v = getattr(rst, "value", None)
    return getattr(v, "value_expression", None)


def getResetValueID(resetID: str) -> str | None:
    """Return reset value handle (F.7.73.83)."""
    rst = _resolve(resetID)
    v = getattr(rst, "value", None)
    return get_handle(v) if v is not None else None


# ---------------------------------------------------------------------------
# EXTENDED (F.7.74)
# Mutators below create/remove child elements or attributes. Where schema
# objects are unavailable they raise INVALID_ID to signal unsupported handle.
# Implementations are skeletal pending full schema integration.
# ---------------------------------------------------------------------------


def addAlternateRegisterField(alternateRegisterID: str, name: str, offset: str, width: str) -> str:
    """Add field to alternateRegister (F.7.74.1)."""
    ar = _resolve(alternateRegisterID)
    if ar is None:
        raise TgiError("Invalid alternateRegister handle", TgiFaultCode.INVALID_ID)
    field = _ns(
        name=name,
        bit_offset=_ns(value=_coerce_int(offset)),
        bit_width=_ns(value=_coerce_int(width)),
    )
    if not hasattr(ar, "field"):
        ar.field = []  # type: ignore[attr-defined]
    ar.field.append(field)  # type: ignore[attr-defined]
    register_parent(field, ar, ("field",), "list")
    return get_handle(field)


def addAlternaterRegisterModeRef(alternateRegisterID: str, modeRef: str, priority: int) -> str:
    """Add modeRef to alternateRegister (F.7.74.2)."""
    ar = _resolve(alternateRegisterID)
    if ar is None:
        raise TgiError("Invalid alternateRegister handle", TgiFaultCode.INVALID_ID)
    mr = _ns(value=modeRef, priority=priority)
    if not hasattr(ar, "mode_ref"):
        ar.mode_ref = []  # type: ignore[attr-defined]
    ar.mode_ref.append(mr)  # type: ignore[attr-defined]
    register_parent(mr, ar, ("mode_ref",), "list")
    return get_handle(mr)


def addBroadcastToBankRef(broadcastToID: str, bankRef: str) -> str:
    """Add bankRef to broadcastTo (F.7.74.3)."""
    b = _resolve(broadcastToID)
    if b is None:
        raise TgiError("Invalid broadcastTo handle", TgiFaultCode.INVALID_ID)
    br = _ns(value=bankRef)
    if not hasattr(b, "bank_ref"):
        b.bank_ref = []  # type: ignore[attr-defined]
    b.bank_ref.append(br)  # type: ignore[attr-defined]
    register_parent(br, b, ("bank_ref",), "list")
    return get_handle(br)


def addBroadcastToRegisterFileRef(broadcastToID: str, registerFileRef: str) -> str:
    """Add registerFileRef (F.7.74.4)."""
    b = _resolve(broadcastToID)
    if b is None:
        raise TgiError("Invalid broadcastTo handle", TgiFaultCode.INVALID_ID)
    rf = _ns(value=registerFileRef)
    if not hasattr(b, "register_file_ref"):
        b.register_file_ref = []  # type: ignore[attr-defined]
    b.register_file_ref.append(rf)  # type: ignore[attr-defined]
    register_parent(rf, b, ("register_file_ref",), "list")
    return get_handle(rf)


def addEnumeratedValuesFieldEnumeratedValue(enumeratedValuesID: str, name: str, value: str) -> str:
    """Add enumeratedValue (F.7.74.5)."""
    evs = _resolve(enumeratedValuesID)
    if evs is None:
        raise TgiError("Invalid enumeratedValues handle", TgiFaultCode.INVALID_ID)
    ev = _ns(name=name, value=_ns(value=_coerce_int(value)))
    if not hasattr(evs, "enumerated_value"):
        evs.enumerated_value = []  # type: ignore[attr-defined]
    evs.enumerated_value.append(ev)  # type: ignore[attr-defined]
    register_parent(ev, evs, ("enumerated_value",), "list")
    return get_handle(ev)


def addFieldRefIndex(fieldRefID: str, value: str) -> str:
    """Add index to fieldRef (F.7.74.6)."""
    fr = _resolve(fieldRefID)
    if fr is None:
        raise TgiError("Invalid fieldRef handle", TgiFaultCode.INVALID_ID)
    idx = _ns(value=_coerce_int(value))
    if not hasattr(fr, "index"):
        fr.index = []  # type: ignore[attr-defined]
    fr.index.append(idx)  # type: ignore[attr-defined]
    register_parent(idx, fr, ("index",), "list")
    return get_handle(idx)


def addRegisterAlternateRegister(
    registerID: str,
    name: str,
    modeRef: str,
    priority: int,
    fieldName: str,
    fieldOffset: str,
    fieldWidth: str,
) -> str:
    """Add alternateRegister (F.7.74.7)."""
    r = _resolve(registerID)
    if r is None:
        raise TgiError("Invalid register handle", TgiFaultCode.INVALID_ID)
    mr = _ns(value=modeRef, priority=priority)
    fld = _ns(
        name=fieldName,
        bit_offset=_ns(value=_coerce_int(fieldOffset)),
        bit_width=_ns(value=_coerce_int(fieldWidth)),
    )
    ar = _ns(name=name, mode_ref=[mr], field=[fld])
    if not hasattr(r, "alternate_register"):
        r.alternate_register = []  # type: ignore[attr-defined]
    r.alternate_register.append(ar)  # type: ignore[attr-defined]
    register_parent(ar, r, ("alternate_register",), "list")
    register_parent(mr, ar, ("mode_ref",), "list")
    register_parent(fld, ar, ("field",), "list")
    return get_handle(ar)


def addRegisterField(registerID: str, name: str, offset: str, width: str) -> str:
    """Add field to register (F.7.74.8)."""
    r = _resolve(registerID)
    if r is None:
        raise TgiError("Invalid register handle", TgiFaultCode.INVALID_ID)
    f = _ns(
        name=name,
        bit_offset=_ns(value=_coerce_int(offset)),
        bit_width=_ns(value=_coerce_int(width)),
    )
    if not hasattr(r, "field"):
        r.field = []  # type: ignore[attr-defined]
    r.field.append(f)  # type: ignore[attr-defined]
    register_parent(f, r, ("field",), "list")
    return get_handle(f)


def addRegisterFieldReset(registerFieldID: str, value: str) -> str:
    """Add reset to register field (F.7.74.9)."""
    f = _resolve(registerFieldID)
    if f is None:
        raise TgiError("Invalid register field handle", TgiFaultCode.INVALID_ID)
    rst = _ns(value=_ns(value=_coerce_int(value)))
    if not hasattr(f, "reset"):
        f.reset = []  # type: ignore[attr-defined]
    f.reset.append(rst)  # type: ignore[attr-defined]
    register_parent(rst, f, ("reset",), "list")
    return get_handle(rst)


def addRegisterRefIndex(registerRefID: str, value: str) -> str:
    """Add index to registerRef (F.7.74.10)."""
    rr = _resolve(registerRefID)
    if rr is None:
        raise TgiError("Invalid registerRef handle", TgiFaultCode.INVALID_ID)
    idx = _ns(value=_coerce_int(value))
    if not hasattr(rr, "index"):
        rr.index = []  # type: ignore[attr-defined]
    rr.index.append(idx)  # type: ignore[attr-defined]
    register_parent(idx, rr, ("index",), "list")
    return get_handle(idx)


# Removes


def removeAliasOfAlternateRegisterRef(aliasOfID: str) -> bool:
    """Remove alternateRegisterRef (F.7.74.11)."""
    a = _resolve(aliasOfID)
    if a is None:
        raise TgiError("Invalid aliasOf handle", TgiFaultCode.INVALID_ID)
    if getattr(a, "alternate_register_ref", None) is None:
        return False
    a.alternate_register_ref = None  # type: ignore[attr-defined]
    return True


def removeAliasOfRegisterRef(aliasOfID: str) -> bool:
    """Remove registerRef (F.7.74.12)."""
    a = _resolve(aliasOfID)
    if a is None:
        raise TgiError("Invalid aliasOf handle", TgiFaultCode.INVALID_ID)
    if getattr(a, "register_ref", None) is None:
        return False
    a.register_ref = None  # type: ignore[attr-defined]
    return True


def removeAlternateRegisterField(regFieldID: str) -> bool:
    """Remove alternate register field (F.7.74.13)."""
    return detach_child_by_handle(regFieldID)


def removeAlternateRegisterTypeIdentifier(alternateRegisterID: str) -> bool:
    """Remove typeIdentifier (F.7.74.14)."""
    ar = _resolve(alternateRegisterID)
    if ar is None:
        raise TgiError("Invalid alternateRegister handle", TgiFaultCode.INVALID_ID)
    if getattr(ar, "type_identifier", None) is None:
        return False
    ar.type_identifier = None  # type: ignore[attr-defined]
    return True


def removeAlternateRegisterVolatility(alternateRegisterID: str) -> bool:
    """Remove volatility (F.7.74.15)."""
    ar = _resolve(alternateRegisterID)
    if ar is None:
        raise TgiError("Invalid alternateRegister handle", TgiFaultCode.INVALID_ID)
    if getattr(ar, "volatile", None) is None:
        return False
    ar.volatile = None  # type: ignore[attr-defined]
    return True


def removeAlternaterRegisterModeRef(modeRefID: str) -> bool:
    """Remove modeRef element (F.7.74.16)."""
    return detach_child_by_handle(modeRefID)


def removeBroadcastToAddressBlockRef(broadcastToID: str) -> bool:
    """Remove addressBlockRef (F.7.74.17)."""
    b = _resolve(broadcastToID)
    if b is None:
        raise TgiError("Invalid broadcastTo handle", TgiFaultCode.INVALID_ID)
    if getattr(b, "address_block_ref", None) is None:
        return False
    b.address_block_ref = None  # type: ignore[attr-defined]
    return True


def removeBroadcastToAlternateRegisterRef(broadcastToID: str) -> bool:
    """Remove alternateRegisterRef (F.7.74.18)."""
    b = _resolve(broadcastToID)
    if b is None:
        raise TgiError("Invalid broadcastTo handle", TgiFaultCode.INVALID_ID)
    if getattr(b, "alternate_register_ref", None) is None:
        return False
    b.alternate_register_ref = None  # type: ignore[attr-defined]
    return True


def removeBroadcastToBankRef(bankRefID: str) -> bool:
    """Remove bankRef by element handle (F.7.74.19)."""
    return detach_child_by_handle(bankRefID)


def removeBroadcastToMemoryMapRef(broadcastToID: str) -> bool:
    """Remove memoryMapRef (F.7.74.20)."""
    b = _resolve(broadcastToID)
    if b is None:
        raise TgiError("Invalid broadcastTo handle", TgiFaultCode.INVALID_ID)
    if getattr(b, "memory_map_ref", None) is None:
        return False
    b.memory_map_ref = None  # type: ignore[attr-defined]
    return True


def removeBroadcastToRegisterFileRef(registerRefID: str) -> bool:
    """Remove registerFileRef (F.7.74.21)."""
    return detach_child_by_handle(registerRefID)


def removeBroadcastToRegisterRef(registerRefID: str) -> bool:
    """Remove registerRef (F.7.74.22)."""
    return detach_child_by_handle(registerRefID)


def removeRegisterFieldTypeIdentifier(registerFieldID: str) -> bool:
    """Remove a register field typeIdentifier (F.7.74.32).

    Section: F.7.74.32.

    Args:
        registerFieldID: Handle to a register field element.

    Returns:
        True if a typeIdentifier was removed, otherwise False.
    """
    field, _ = _resolve_register_field(registerFieldID)
    width, reference, alias = _register_field_width_state(field)
    if reference is not None or (width is None and alias is None):
        return False
    identifier = _register_field_type_identifier(field)
    if identifier is None:
        return False
    items = _list_attr(field, "choice")
    index = next((index for index, child in enumerate(items) if isinstance(child, str)), None)
    if index is None:
        raise TgiError("Register field typeIdentifier choice changed during removal", TgiFaultCode.INVALID_ID)
    del items[index]
    return True


def removeRegisterFieldVolatility(registerFieldID: str) -> bool:
    """Remove register field volatility (F.7.74.33).

    Section: F.7.74.33.

    Args:
        registerFieldID: Handle to a register field element.

    Returns:
        True if an explicit volatility value was removed, otherwise False.
    """
    field, _ = _resolve_register_field(registerFieldID)
    width, reference, alias = _register_field_width_state(field)
    if width is None:
        if reference is not None or alias is not None:
            return False
        raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
    volatile = _register_field_volatile(field)
    if volatile is None:
        return False
    items = _list_attr(field, "choice")
    index = next((index for index, child in enumerate(items) if type(child) is bool), None)
    if index is None:
        raise TgiError("Register field volatility choice changed during removal", TgiFaultCode.INVALID_ID)
    del items[index]
    return True


def removeRegisterTypeIdentifier(registerID: str) -> bool:
    """Remove inline typeIdentifier (F.7.74.35).

    Section: F.7.74.35.

    Args:
        registerID: Handle to a register element.

    Returns:
        True if an inline typeIdentifier was removed, otherwise False.
    """
    register = _resolve_register(registerID)
    _register_size(register)
    if _register_definition_reference(register) is not None:
        return False
    identifier = _register_type_identifier(register)
    if identifier is None:
        return False
    items = _list_attr(register, "choice")
    index = next((index for index, child in enumerate(items) if isinstance(child, str)), None)
    if index is None:
        raise TgiError("Register typeIdentifier choice changed during removal", TgiFaultCode.INVALID_ID)
    del items[index]
    return True


def removeRegisterVolatility(registerID: str) -> bool:
    """Remove explicit volatility (F.7.74.36).

    Section: F.7.74.36.

    Args:
        registerID: Handle to a register element.

    Returns:
        True if explicit volatility was removed, otherwise False.
    """
    register = _resolve_register(registerID)
    _register_size(register)
    if _register_definition_reference(register) is not None:
        return False
    volatile = _register_volatile(register)
    if volatile is None:
        return False
    volatile_id = get_handle(volatile)
    _register_graph(volatile)
    if not detach_child_by_handle(volatile_id):
        raise TgiError("Could not remove register volatility", TgiFaultCode.INVALID_ID)
    return True


def setRegisterAddressOffset(registerID: str, value: str) -> bool:
    """Set addressOffset.

    Section: F.7.74.56.

    Args:
        registerID: Handle to a register element.
        value: New unsigned 64-bit addressOffset expression.

    Returns:
        True after the existing expression node is updated.
    """
    register = _resolve_register(registerID)
    offset = _register_address_offset(register)
    source = _register_file_expression(value, "addressOffset", 0, _UINT64_MAX, offset)
    offset.value = source
    register_parent(offset, register, ("address_offset",), "single")
    return True


def setRegisterFieldBitWidth(registerFieldID: str, value: str) -> bool:
    """Set inline bitWidth from an unsigned positive 32-bit expression.

    Section: F.7.74.58.

    Args:
        registerFieldID: Handle to a field owned by a register.
        value: New bitWidth expression source.

    Returns:
        True after updating the inline bitWidth choice.
    """
    field, register = _resolve_register_field(registerFieldID)
    current, reference, alias = _register_field_width_state(field)
    source = _register_file_expression(value, "bitWidth", 1, _UINT32_MAX, current)
    number = _integer_expression(source, _UINT32_MAX, True)
    _check_register_field_containment(register, field, number)
    items = _list_attr(field, "choice")

    if current is not None:
        current.value = source
        register_parent(current, field, ("choice",), "list")
        _register_graph(current)
        return True

    branch = reference if reference is not None else alias
    if branch is not None:
        position = next((index for index, child in enumerate(items) if child is branch), None)
        if position is None:
            raise TgiError("Register field choice changed during update", TgiFaultCode.INVALID_ID)
        branch_id = get_handle(branch)
        register_parent(branch, field, ("choice",), "list")
        _register_graph(branch)
        if not detach_child_by_handle(branch_id):
            raise TgiError("Could not replace register field definition choice", TgiFaultCode.INVALID_ID)
    else:
        position = next(
            (
                index
                for index, child in enumerate(items)
                if isinstance(
                    child,
                    (bool, FieldType.Resets, FieldType.FieldAccessPolicies, EnumeratedValues),
                )
            ),
            len(items),
        )

    width = UnsignedPositiveIntExpression(value=source)
    items.insert(position, width)
    register_parent(width, field, ("choice",), "list")
    _register_graph(width)
    return True


def setRegisterFieldTypeIdentifier(regFieldID: str, typeIdentifier: str) -> bool:
    """Set a register field typeIdentifier (F.7.74.62).

    Section: F.7.74.62.

    Args:
        regFieldID: Handle to a register field element.
        typeIdentifier: New register field typeIdentifier name.

    Returns:
        True after setting the typeIdentifier.
    """
    field, _ = _resolve_register_field(regFieldID)
    width, reference, alias = _register_field_width_state(field)
    if reference is not None:
        raise TgiError(
            "setRegisterFieldTypeIdentifier requires an inline or alias field",
            TgiFaultCode.INVALID_ARGUMENT,
        )
    if width is None and alias is None:
        raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
    value = _schema_name(typeIdentifier, "Name")
    identifier = _register_field_type_identifier(field)
    items = _list_attr(field, "choice")
    if identifier is not None:
        index = next((index for index, child in enumerate(items) if isinstance(child, str)), None)
        if index is None:
            raise TgiError("Register field typeIdentifier choice changed during update", TgiFaultCode.INVALID_ID)
        items[index] = value
        return True
    position = next(
        (
            index
            for index, child in enumerate(items)
            if isinstance(child, (UnsignedPositiveIntExpression, FieldType.AliasOf))
        ),
        None,
    )
    if position is None:
        raise TgiError("Register field choice changed during update", TgiFaultCode.INVALID_ID)
    items.insert(position, value)
    return True


def setRegisterFieldVolatility(regFieldID: str, volatile: bool) -> bool:
    """Set register field volatility (F.7.74.63).

    Section: F.7.74.63.

    Args:
        regFieldID: Handle to a register field element.
        volatile: Whether the register field is volatile.

    Returns:
        True after setting explicit volatility.
    """
    field, _ = _resolve_register_field(regFieldID)
    width, reference, alias = _register_field_width_state(field)
    if width is None:
        if reference is not None or alias is not None:
            raise TgiError("setRegisterFieldVolatility requires an inline field width", TgiFaultCode.INVALID_ARGUMENT)
        raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
    if type(volatile) is not bool:
        raise TgiError("volatile must be a boolean", TgiFaultCode.INVALID_ARGUMENT)
    current = _register_field_volatile(field)
    items = _list_attr(field, "choice")
    if current is not None:
        index = next((index for index, child in enumerate(items) if type(child) is bool), None)
        if index is None:
            raise TgiError("Register field volatility choice changed during update", TgiFaultCode.INVALID_ID)
        items[index] = volatile
        return True
    position = next((index for index, child in enumerate(items) if child is width), None)
    if position is None:
        raise TgiError("Register field bitWidth choice changed during update", TgiFaultCode.INVALID_ID)
    items.insert(position + 1, volatile)
    return True


def setRegisterSize(registerID: str, value: str) -> bool:
    """Set inline size, replacing a register-definition choice when present.

    Section: F.7.74.65.

    Args:
        registerID: Handle to a register element.
        value: New unsigned positive 32-bit size expression.

    Returns:
        True after updating the inline size or replacing a definition choice.
    """
    register = _resolve_register(registerID)
    current = _register_size(register)
    definition_ref = _register_definition_reference(register)
    source = _register_file_expression(value, "size", 1, _UINT32_MAX, current)
    number = _integer_expression(source, _UINT32_MAX, True)
    if definition_ref is None:
        _check_field_containment(register, number)
    if definition_ref is not None:
        _replace_register_choice(register, UnsignedPositiveIntExpression(value=source))
    elif current is not None:
        current.value = source
        register_parent(current, register, ("choice",), "list")
    else:
        items = _list_attr(register, "choice")
        position = next((index for index, child in enumerate(items) if not isinstance(child, str)), len(items))
        size = UnsignedPositiveIntExpression(value=source)
        items.insert(position, size)
        register_parent(size, register, ("choice",), "list")
        _register_graph(size)
    return True


def setRegisterTypeIdentifier(registerID: str, typeIdentifier: str) -> bool:
    """Set an inline typeIdentifier on a register.

    Section: F.7.74.66.

    Args:
        registerID: Handle to a register element.
        typeIdentifier: New register typeIdentifier name.

    Returns:
        True after setting the inline typeIdentifier.
    """
    register = _resolve_register(registerID)
    size = _inline_register_choice(register, "setRegisterTypeIdentifier")
    value = _schema_name(typeIdentifier, "Name")
    identifier = _register_type_identifier(register)
    items = _list_attr(register, "choice")
    if identifier is not None:
        index = next((index for index, child in enumerate(items) if isinstance(child, str)), None)
        if index is None:
            raise TgiError("Register typeIdentifier choice changed during update", TgiFaultCode.INVALID_ID)
        items[index] = value
        return True
    position = next((index for index, child in enumerate(items) if child is size), None)
    if position is None:
        raise TgiError("Register size choice changed during update", TgiFaultCode.INVALID_ID)
    items.insert(position, value)
    return True


def setRegisterVolatility(registerID: str, volatile: bool) -> bool:
    """Set explicit register volatility.

    Section: F.7.74.67.

    Args:
        registerID: Handle to a register element.
        volatile: Whether the register value is volatile.

    Returns:
        True after setting the explicit volatility value.
    """
    register = _resolve_register(registerID)
    size = _inline_register_choice(register, "setRegisterVolatility")
    if type(volatile) is not bool:
        raise TgiError("volatile must be a boolean", TgiFaultCode.INVALID_ARGUMENT)
    current = _register_volatile(register)
    items = _list_attr(register, "choice")
    if current is None:
        current = Volatile(value=volatile)
        position = next((index for index, child in enumerate(items) if child is size), None)
        if position is None:
            raise TgiError("Register size choice changed during update", TgiFaultCode.INVALID_ID)
        items.insert(position + 1, current)
    else:
        current.value = volatile
    register_parent(current, register, ("choice",), "list")
    _register_graph(current)
    return True
