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

from org.accellera.ipxact.v1685_2022.access_policies import AccessPolicies
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.banked_block_type import BankedBlockType
from org.accellera.ipxact.v1685_2022.enumerated_values import EnumeratedValues
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.register_file_definitions import RegisterFileDefinitions
from org.accellera.ipxact.v1685_2022.reset import Reset
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.volatile import Volatile

from .component import _list_attr, _register_graph, _register_owner_for
from .address_space import _register_owned_child
from ._expressions import SvExpressionError, _undeclared, _xml_text
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
from .register_file import _child_ids as _register_file_child_ids
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
    "removeRegisterAlternateRegister",
    "removeRegisterField",
    "removeRegisterFieldReset",
    "removeRegisterFieldTypeIdentifier",
    "removeRegisterFieldVolatility",
    "removeRegisterTypeIdentifier",
    "removeRegisterVolatility",
    "removeResetMask",
    "setAlternateRegisterTypeIdentifier",
    "setAlternateRegisterVolatility",
    "setFieldDefinitionBitWidth",
    "setFieldDefinitionTypeIdentifier",
    "setFieldDefinitionVolatile",
    "setModeRefPriority",
    "setRegisterAddressOffset",
    "setRegisterFieldBitWidth",
    "setRegisterFieldTypeIdentifier",
    "setRegisterFieldVolatility",
    "setRegisterSize",
    "setRegisterTypeIdentifier",
    "setRegisterVolatility",
    "setResetMask",
    "setResetValue",
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

type _AlternateRegister = AlternateRegisters.AlternateRegister

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


def _resolve_alternate_register(alternateRegisterID: str) -> _AlternateRegister:
    alternate_register = resolve_handle(alternateRegisterID)
    if not isinstance(alternate_register, AlternateRegisters.AlternateRegister):
        raise TgiError("Invalid alternateRegister handle", TgiFaultCode.INVALID_ID)
    _register_graph(alternate_register)
    return alternate_register


def _resolve_reset(resetID: str) -> Reset:
    reset = resolve_handle(resetID) if isinstance(resetID, str) else None
    if not isinstance(reset, Reset):
        raise TgiError("Invalid reset handle", TgiFaultCode.INVALID_ID)
    return reset


def _reset_field(reset: Reset) -> FieldType | FieldDefinitions.FieldDefinition | None:
    """Return the containing field when reset ownership is known to the handle manager."""
    current: Any = reset
    seen: set[int] = set()
    while id(current) not in seen:
        seen.add(id(current))
        info = get_parent_info(get_handle(current))
        if info is None:
            return None
        parent = resolve_handle(info.parent_handle)
        if isinstance(parent, (FieldType, FieldDefinitions.FieldDefinition)):
            _register_graph(parent)
            return parent
        if parent is None:
            return None
        current = parent
    return None


def _reset_field_width(reset: Reset, *, deferred: bool) -> int | None:
    """Resolve the inline field width used as the reset bit-vector context."""
    field = _reset_field(reset)
    if field is None:
        return None
    width = _register_field_bit_width(field) if isinstance(field, FieldType) else field.bit_width
    if width is None:
        return None
    source = _register_file_expression(width.value, "bitWidth", 1, _UINT32_MAX, width)
    return _integer_expression(source, _UINT32_MAX, deferred, minimum=1)


def _reset_expression(reset: Reset, name: str, *, required: bool) -> UnsignedBitVectorExpression | None:
    expression = getattr(reset, name, None)
    if expression is None and not required:
        return None
    if not isinstance(expression, UnsignedBitVectorExpression):
        raise TgiError(f"Invalid reset {name} model", TgiFaultCode.INVALID_ID)
    register_parent(expression, reset, (name,), "single")
    _register_graph(expression)
    if not isinstance(expression.value, str):
        raise TgiError(f"Invalid reset {name} source", TgiFaultCode.INVALID_ID)
    return expression


def _reset_expression_source(source: str, width: int | None) -> str:
    """Validate a bit-vector expression, deferring only undeclared identifiers."""
    _xml_text(source)
    if not source.strip():
        raise TgiError("Reset bit-vector expression must be nonempty", TgiFaultCode.INVALID_ARGUMENT)
    try:
        from amal.eda.systemverilog.expression_parser import SvExpressionParser

        SvExpressionParser().parse_bit_vector(source, width)
    except SvExpressionError as error:
        if _undeclared(error):
            return source
        raise TgiError("Invalid reset bit-vector expression", TgiFaultCode.INVALID_ARGUMENT) from error
    return source


def _register_field_resets(field: FieldType) -> tuple[FieldType.Resets | None, set[str]]:
    """Validate and register the optional resets group on an inline register field."""
    choice = getattr(field, "choice", None)
    if not isinstance(choice, (list, tuple)):
        raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
    holders = [child for child in choice if isinstance(child, FieldType.Resets)]
    if len(holders) > 1:
        raise TgiError("Multiple register field resets groups", TgiFaultCode.INVALID_ID)
    holder = holders[0] if holders else None
    width, reference, alias = _register_field_width_state(field)
    if holder is not None and width is None:
        raise TgiError("Register field resets require an inline bitWidth", TgiFaultCode.INVALID_ID)
    if holder is None:
        if width is None and reference is None and alias is None:
            raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
        return None, set()

    resets = getattr(holder, "reset", None)
    if not isinstance(resets, (list, tuple)) or not resets or any(not isinstance(reset, Reset) for reset in resets):
        raise TgiError("Invalid register field reset collection", TgiFaultCode.INVALID_ID)
    register_parent(holder, field, ("choice",), "list")
    _register_graph(holder)
    identities: set[str] = set()
    for reset in resets:
        reset_type_ref = getattr(reset, "reset_type_ref", None)
        identity = "HARD" if reset_type_ref is None else _schema_name(reset_type_ref, "Name")
        if identity in identities:
            raise TgiError("Duplicate resetTypeRef in register field", TgiFaultCode.INVALID_ID)
        identities.add(identity)
    return holder, identities


def _reset_resolved_value(reset: Reset, expression: UnsignedBitVectorExpression) -> int:
    """Resolve the reset source in field-width bit context or its inferred width."""
    from amal.eda.systemverilog.expression_parser import SvExpressionParser

    try:
        result = SvExpressionParser().parse_bit_vector(expression.value, _reset_field_width(reset, deferred=False))
        return result.as_python()
    except SvExpressionError as error:
        raise TgiError("Cannot resolve reset bit-vector expression", TgiFaultCode.INVALID_ARGUMENT) from error


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
    offset_node = field.bit_offset
    if not isinstance(offset_node, UnsignedIntExpression):
        raise TgiError("Invalid register field bitOffset model", TgiFaultCode.INVALID_ID)
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


def _register_fields(register: _Register) -> list[FieldType]:
    choice = getattr(register, "choice", ())
    if not isinstance(choice, (list, tuple)):
        raise TgiError("Invalid register choice model", TgiFaultCode.INVALID_ID)
    fields = [child for child in choice if isinstance(child, FieldType)]
    allowed = (*_REGISTER_DEFINITION_REF_TYPES, str, UnsignedPositiveIntExpression, Volatile, AccessPolicies, FieldType)
    if any(not isinstance(child, allowed) for child in choice):
        raise TgiError("Invalid register choice child", TgiFaultCode.INVALID_ID)
    return fields


def _new_register_field(name: str, offset: str, width: str) -> FieldType:
    """Validate and construct the common inline-width field used by these builders."""
    field_name = _schema_name(name, "Name")
    offset_source = _register_file_expression(offset, "offset", 0, _UINT32_MAX)
    width_source = _register_file_expression(width, "width", 1, _UINT32_MAX)
    return FieldType(
        name=field_name,
        bit_offset=UnsignedIntExpression(value=offset_source),
        choice=[UnsignedPositiveIntExpression(value=width_source)],
    )


def _register_data_names(register: _Register) -> set[str]:
    """Return names that share a registerData key scope with ``register``."""
    own_name = getattr(register, "name", None)
    if not isinstance(own_name, str):
        raise TgiError("Invalid register name", TgiFaultCode.INVALID_ID)
    names = {_schema_name(own_name, "Name")}
    owner = _register_owned_child(register)
    info = get_parent_info(get_handle(register))
    if owner is None or info is None:
        return names
    if info.container != "list" or not info.path:
        raise TgiError("Register has no supported registerData owner", TgiFaultCode.INVALID_ID)
    siblings = getattr(owner, info.path[-1], None)
    if not isinstance(siblings, (list, tuple)) or not any(item is register for item in siblings):
        raise TgiError("Register has no supported registerData collection", TgiFaultCode.INVALID_ID)
    for sibling in siblings:
        if isinstance(sibling, _REGISTER_TYPES):
            sibling_name = getattr(sibling, "name", None)
            if isinstance(sibling_name, str):
                names.add(_schema_name(sibling_name, "Name"))
            holder = getattr(sibling, "alternate_registers", None)
            if holder is not None:
                if not isinstance(holder, AlternateRegisters):
                    raise TgiError("Invalid alternateRegisters model", TgiFaultCode.INVALID_ID)
                names.update(
                    _schema_name(item.name, "Name")
                    for item in holder.alternate_register
                    if isinstance(item, AlternateRegisters.AlternateRegister) and isinstance(item.name, str)
                )
        elif isinstance(sibling, RegisterFile):
            sibling_name = getattr(sibling, "name", None)
            if isinstance(sibling_name, str):
                names.add(_schema_name(sibling_name, "Name"))
    return names


def _check_new_field_containment(register: _Register, field: FieldType) -> None:
    size_node = _inline_register_choice(register, "addRegisterField")
    width_nodes = [child for child in field.choice if isinstance(child, UnsignedPositiveIntExpression)]
    if len(width_nodes) != 1:
        raise TgiError("Invalid register field model", TgiFaultCode.INVALID_ID)
    width_node = width_nodes[0]
    size_source = _register_file_expression(size_node.value, "size", 1, _UINT32_MAX, size_node)
    _integer_expression(size_source, _UINT32_MAX, True)
    width = _integer_expression(width_node.value, _UINT32_MAX, True)
    _check_register_field_containment(register, field, width)


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
    """Return field handles defined on an alternate register.

    Section: F.7.73.7.

    Args:
        alternateRegisterID: Handle to an alternateRegister element.

    Returns:
        Handles to the alternate register's fields, in document order.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    fields = alternate_register.field_value
    if any(not isinstance(field, FieldType) for field in fields):
        raise TgiError("Invalid alternate register field model", TgiFaultCode.INVALID_ID)
    return _register_file_child_ids(alternate_register, fields, ("field_value",))


def getAlternateRegisterModeRefIDs(alternateRegisterID: str) -> list[str]:
    """Return modeRef handles defined on an alternate register.

    Section: F.7.73.8.

    Args:
        alternateRegisterID: Handle to an alternateRegister element.

    Returns:
        Handles to the alternate register's modeRef elements, in document order.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    mode_refs = alternate_register.mode_ref
    if any(not isinstance(mode_ref, ModeRef) for mode_ref in mode_refs):
        raise TgiError("Invalid alternate register modeRef model", TgiFaultCode.INVALID_ID)
    return _register_file_child_ids(alternate_register, mode_refs, ("mode_ref",))


def getAlternateRegisterRefAlternateRegisterRefByName(alternateRegisterRefID: str) -> str | None:
    """Return alternateRegisterRef value (F.7.73.9)."""
    r = _resolve(alternateRegisterRefID)
    return _maybe_value(getattr(r, "alternate_register_ref", None))


def getAlternateRegisterTypeIdentifier(alternateRegisterID: str) -> str | None:
    """Return alternate register typeIdentifier.

    Section: F.7.73.10.

    Args:
        alternateRegisterID: Handle to an alternate register element.

    Returns:
        The alternate register typeIdentifier, or None when it is absent.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    identifier = alternate_register.type_identifier
    if identifier is not None and not isinstance(identifier, str):
        raise TgiError("Invalid alternate register typeIdentifier", TgiFaultCode.INVALID_ID)
    return identifier


def getAlternateRegisterVolatility(alternateRegisterID: str) -> bool | None:
    """Return explicit alternate register volatility.

    Section: F.7.73.11.

    Args:
        alternateRegisterID: Handle to an alternate register element.

    Returns:
        The explicit volatility value, or None when it is absent.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    volatile = alternate_register.volatile
    if volatile is None:
        return None
    if not isinstance(volatile, Volatile) or type(volatile.value) is not bool:
        raise TgiError("Invalid alternate register volatile value", TgiFaultCode.INVALID_ID)
    return volatile.value


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


def _resolve_field_definition(fieldDefinitionID: str) -> FieldDefinitions.FieldDefinition:
    field = resolve_handle(fieldDefinitionID) if isinstance(fieldDefinitionID, str) else None
    if not isinstance(field, FieldDefinitions.FieldDefinition):
        raise TgiError("Invalid field definition handle", TgiFaultCode.INVALID_ID)
    return field


def _field_definition_width(field: FieldDefinitions.FieldDefinition) -> UnsignedPositiveIntExpression:
    width = field.bit_width
    if not isinstance(width, UnsignedPositiveIntExpression):
        raise TgiError("Invalid field definition bitWidth model", TgiFaultCode.INVALID_ID)
    register_parent(width, field, ("bit_width",), "single")
    _register_graph(width)
    return width


def getFieldDefinitionBitWidthID(fieldDefinitionID: str) -> str:
    """Return the field definition's required bitWidth handle.

    Section: F.7.73.39.

    Args:
        fieldDefinitionID: Handle to a fieldDefinition element.

    Returns:
        Handle to the owned bitWidth expression.
    """
    return get_handle(_field_definition_width(_resolve_field_definition(fieldDefinitionID)))


def getFieldDefinitionEnumeratedValueIDs(fieldDefinitionID: str) -> list[str]:
    """Return enumeratedValue handles (F.7.73.40)."""
    fd = _resolve(fieldDefinitionID)
    return _list_handles(fd, "enumerated_value")


def getFieldDefinitionTypeIdentifier(fieldDefinitionID: str) -> str | None:
    """Return the stored field definition typeIdentifier.

    Section: F.7.73.41.

    Args:
        fieldDefinitionID: Handle to a fieldDefinition element.

    Returns:
        The typeIdentifier string, or None when absent.
    """
    value = _resolve_field_definition(fieldDefinitionID).type_identifier
    if value is not None and not isinstance(value, str):
        raise TgiError("Invalid field definition typeIdentifier model", TgiFaultCode.INVALID_ID)
    return value


def getFieldDefinitionVolatile(fieldDefinitionID: str) -> bool:
    """Return field definition volatility, defaulting to false when absent.

    Section: F.7.73.42.

    Args:
        fieldDefinitionID: Handle to a fieldDefinition element.

    Returns:
        The stored Boolean, or False when the optional element is absent.
    """
    value = _resolve_field_definition(fieldDefinitionID).volatile
    if value is not None and not isinstance(value, bool):
        raise TgiError("Invalid field definition volatile model", TgiFaultCode.INVALID_ID)
    return False if value is None else value


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
    """Return the alternateRegister handles defined on a register.

    Section: F.7.73.48.

    Args:
        registerID: Handle to a register element.

    Returns:
        Handles to alternateRegister elements in schema order, or an empty list when none are defined.
    """
    register = _resolve_register(registerID)
    holder = getattr(register, "alternate_registers", None)
    if holder is None:
        return []
    if not isinstance(holder, AlternateRegisters):
        raise TgiError("Invalid register alternateRegisters model", TgiFaultCode.INVALID_ID)
    alternates = getattr(holder, "alternate_register", None)
    if not isinstance(alternates, (list, tuple)) or any(
        not isinstance(item, AlternateRegisters.AlternateRegister) for item in alternates
    ):
        raise TgiError("Invalid alternateRegister collection", TgiFaultCode.INVALID_ID)
    return _register_file_child_ids(holder, alternates, ("alternate_register",))


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
    """Return inline field handles defined on a register.

    Section: F.7.73.61.

    Args:
        registerID: Handle to a register element.

    Returns:
        Handles to inline fields in schema order, or an empty list on a register-definition reference.
    """
    register = _resolve_register(registerID)
    fields = _register_fields(register)
    return _register_file_child_ids(register, fields, ("choice",))


def getRegisterFieldResetIDs(registerFieldID: str) -> list[str]:
    """Return reset handles for an inline register field (F.7.73.62).

    Section: F.7.73.62.

    Args:
        registerFieldID: Handle to a register field element.

    Returns:
        Handles to the field's reset elements in schema order, or an empty list when absent.
    """
    field, _ = _resolve_register_field(registerFieldID)
    holder, _ = _register_field_resets(field)
    if holder is None:
        return []
    return _register_file_child_ids(holder, holder.reset, ("reset",))


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
    """Return the resolved reset mask value.

    Section: F.7.73.78.

    Args:
        resetID: Handle to a reset element.

    Returns:
        Resolved mask integer, or None when no explicit mask element is stored.
    """
    reset = _resolve_reset(resetID)
    mask = _reset_expression(reset, "mask", required=False)
    return _reset_resolved_value(reset, mask) if mask is not None else None


def getResetMaskExpression(resetID: str) -> str | None:
    """Return the stored reset mask expression source.

    Section: F.7.73.79.

    Args:
        resetID: Handle to a reset element.

    Returns:
        Exact mask source text, or None when the optional mask is absent.
    """
    expression = _reset_expression(_resolve_reset(resetID), "mask", required=False)
    return expression.value if expression is not None else None


def getResetMaskID(resetID: str) -> str | None:
    """Return the owned reset mask expression handle.

    Section: F.7.73.80.

    Args:
        resetID: Handle to a reset element.

    Returns:
        Handle to the mask expression, or None when the optional mask is absent.
    """
    reset = _resolve_reset(resetID)
    expression = _reset_expression(reset, "mask", required=False)
    return get_handle(expression) if expression is not None else None


def getResetValue(resetID: str) -> int:
    """Return the resolved reset value.

    Section: F.7.73.81.

    Args:
        resetID: Handle to a reset element.

    Returns:
        Resolved reset value as an arbitrary-precision integer.
    """
    reset = _resolve_reset(resetID)
    expression = _reset_expression(reset, "value", required=True)
    assert expression is not None
    return _reset_resolved_value(reset, expression)


def getResetValueExpression(resetID: str) -> str:
    """Return the stored reset value expression source.

    Section: F.7.73.82.

    Args:
        resetID: Handle to a reset element.

    Returns:
        Exact reset value source text.
    """
    expression = _reset_expression(_resolve_reset(resetID), "value", required=True)
    assert expression is not None
    return expression.value


def getResetValueID(resetID: str) -> str:
    """Return the owned reset value expression handle.

    Section: F.7.73.83.

    Args:
        resetID: Handle to a reset element.

    Returns:
        Handle to the mandatory value expression.
    """
    reset = _resolve_reset(resetID)
    expression = _reset_expression(reset, "value", required=True)
    assert expression is not None
    return get_handle(expression)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.74)
# Mutators below create/remove child elements or attributes. Where schema
# objects are unavailable they raise INVALID_ID to signal unsupported handle.
# Implementations are skeletal pending full schema integration.
# ---------------------------------------------------------------------------


def addAlternateRegisterField(alternateRegisterID: str, name: str, offset: str, width: str) -> str:
    """Add a field to an alternate register.

    Section: F.7.74.1.

    Args:
        alternateRegisterID: Handle to an alternateRegister element.
        name: XML Name for the new field.
        offset: Unsigned 32-bit bitOffset expression.
        width: Positive unsigned 32-bit bitWidth expression.

    Returns:
        Handle to the new regField element.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    field = _new_register_field(name, offset, width)
    fields = getattr(alternate_register, "field_value", None)
    if not isinstance(fields, (list, tuple)) or any(not isinstance(existing, FieldType) for existing in fields):
        raise TgiError("Invalid alternate register field model", TgiFaultCode.INVALID_ID)
    if any(existing.name == field.name for existing in fields):
        raise TgiError(f"Alternate register field name {field.name!r} already exists", TgiFaultCode.INVALID_ARGUMENT)
    width_number = _integer_expression(field.choice[0].value, _UINT32_MAX, True)
    holder = _register_owned_child(alternate_register, AlternateRegisters)
    register = _register_owned_child(holder, _REGISTER_TYPES) if holder is not None else None
    if register is not None:
        _check_register_field_containment(register, field, width_number)
    _list_attr(alternate_register, "field_value").append(field)
    register_parent(field, alternate_register, ("field_value",), "list")
    _register_graph(field)
    return get_handle(field)


def addAlternaterRegisterModeRef(alternateRegisterID: str, modeRef: str, priority: int) -> str:
    """Add a modeRef to an alternate register.

    Section: F.7.74.2.

    Args:
        alternateRegisterID: Handle to an alternateRegister element.
        modeRef: XML Name of the referenced mode.
        priority: Unique non-negative integer priority for this alternate register.

    Returns:
        Handle to the new modeRef element.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    mode_name = _schema_name(modeRef, "Name")
    holder = _register_owned_child(alternate_register, AlternateRegisters)
    if holder is not None:
        for sibling in holder.alternate_register:
            if sibling is alternate_register:
                continue
            if any(getattr(existing, "value", None) == mode_name for existing in sibling.mode_ref):
                raise TgiError(
                    f"modeRef {mode_name!r} already exists in alternateRegisters", TgiFaultCode.INVALID_ARGUMENT
                )
    from .access_policy import _mode_ref_priority

    priority_value = _mode_ref_priority(alternate_register.mode_ref, mode_name, priority)
    mode_ref_node = ModeRef(value=mode_name, priority=priority_value)
    _list_attr(alternate_register, "mode_ref").append(mode_ref_node)
    register_parent(mode_ref_node, alternate_register, ("mode_ref",), "list")
    _register_graph(mode_ref_node)
    return get_handle(mode_ref_node)


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
    """Add an alternate register with its required mode and field.

    Section: F.7.74.7.

    Args:
        registerID: Handle to a register element.
        name: XML Name for the alternate register.
        modeRef: XML Name of the referenced mode.
        priority: Non-negative priority for the new modeRef.
        fieldName: XML Name for the required field.
        fieldOffset: Unsigned 32-bit field bitOffset expression.
        fieldWidth: Positive unsigned 32-bit field bitWidth expression.

    Returns:
        Handle to the new alternateRegister element.
    """
    register = _resolve_register(registerID)
    alternate_name = _schema_name(name, "Name")
    mode_name = _schema_name(modeRef, "Name")
    field = _new_register_field(fieldName, fieldOffset, fieldWidth)
    holder = getattr(register, "alternate_registers", None)
    if holder is not None and not isinstance(holder, AlternateRegisters):
        raise TgiError("Invalid register alternateRegisters model", TgiFaultCode.INVALID_ID)
    if holder is not None:
        alternates = getattr(holder, "alternate_register", None)
        if not isinstance(alternates, (list, tuple)) or any(
            not isinstance(item, AlternateRegisters.AlternateRegister) for item in alternates
        ):
            raise TgiError("Invalid alternateRegister collection", TgiFaultCode.INVALID_ID)
        if any(item.name == alternate_name for item in alternates):
            raise TgiError(f"Alternate register name {alternate_name!r} already exists", TgiFaultCode.INVALID_ARGUMENT)
        for sibling in alternates:
            if any(getattr(item, "value", None) == mode_name for item in sibling.mode_ref):
                raise TgiError(
                    f"modeRef {mode_name!r} already exists in alternateRegisters", TgiFaultCode.INVALID_ARGUMENT
                )
    if alternate_name in _register_data_names(register):
        raise TgiError(f"Register data name {alternate_name!r} already exists", TgiFaultCode.INVALID_ARGUMENT)
    from .access_policy import _mode_ref_priority

    priority_value = _mode_ref_priority((), mode_name, priority)
    width_number = _integer_expression(field.choice[0].value, _UINT32_MAX, True)
    _check_register_field_containment(register, field, width_number)
    mode_ref_node = ModeRef(value=mode_name, priority=priority_value)
    alternate = AlternateRegisters.AlternateRegister(
        name=alternate_name,
        mode_ref=[mode_ref_node],
        field_value=[field],
    )
    if holder is None:
        holder = AlternateRegisters(alternate_register=[])
        register.alternate_registers = holder
        register_parent(holder, register, ("alternate_registers",), "single")
    _list_attr(holder, "alternate_register").append(alternate)
    register_parent(alternate, holder, ("alternate_register",), "list")
    _register_graph(alternate)
    return get_handle(alternate)


def addRegisterField(registerID: str, name: str, offset: str, width: str) -> str:
    """Add an inline field to a register with an existing inline size.

    Section: F.7.74.8.

    Args:
        registerID: Handle to a register element.
        name: XML Name for the new field.
        offset: Unsigned 32-bit bitOffset expression.
        width: Positive unsigned 32-bit bitWidth expression.

    Returns:
        Handle to the new regField element.
    """
    register = _resolve_register(registerID)
    field = _new_register_field(name, offset, width)
    fields = _register_fields(register)
    if any(existing.name == field.name for existing in fields):
        raise TgiError(f"Register field name {field.name!r} already exists", TgiFaultCode.INVALID_ARGUMENT)
    _check_new_field_containment(register, field)
    _list_attr(register, "choice").append(field)
    register_parent(field, register, ("choice",), "list")
    _register_graph(field)
    return get_handle(field)


def addRegisterFieldReset(registerFieldID: str, value: str) -> str:
    """Add a HARD reset to an inline register field (F.7.74.9).

    Section: F.7.74.9.

    Args:
        registerFieldID: Handle to a register field element.
        value: Unsigned bit-vector expression for the reset value.

    Returns:
        Handle to the added reset element.
    """
    field, _ = _resolve_register_field(registerFieldID)
    width, reference, alias = _register_field_width_state(field)
    if width is None:
        if reference is not None or alias is not None:
            raise TgiError("Reset requires an inline register field", TgiFaultCode.INVALID_ARGUMENT)
        raise TgiError("Invalid register field choice model", TgiFaultCode.INVALID_ID)
    holder, identities = _register_field_resets(field)
    if "HARD" in identities:
        raise TgiError("A HARD reset already exists on this register field", TgiFaultCode.INVALID_ARGUMENT)

    width_source = _register_file_expression(width.value, "bitWidth", 1, _UINT32_MAX, width)
    resolved_width = _integer_expression(width_source, _UINT32_MAX, True, minimum=1)
    source = _reset_expression_source(value, resolved_width)
    reset = Reset(value=UnsignedBitVectorExpression(value=source))

    if holder is None:
        holder = FieldType.Resets(reset=[reset])
        items = _list_attr(field, "choice")
        field_data_index = next(
            (
                index
                for index, child in enumerate(items)
                if isinstance(child, (FieldType.FieldAccessPolicies, EnumeratedValues))
            ),
            len(items),
        )
        items.insert(field_data_index, holder)
        register_parent(holder, field, ("choice",), "list")
        _register_graph(holder)
    else:
        resets = _list_attr(holder, "reset")
        resets.append(reset)
        register_parent(reset, holder, ("reset",), "list")
        _register_graph(reset)
    return get_handle(reset)


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
    """Remove a field from its alternate register.

    Section: F.7.74.13.

    Args:
        regFieldID: Handle to a regField element.

    Returns:
        True when the field was removed.
    """
    field = resolve_handle(regFieldID)
    if not isinstance(field, FieldType):
        raise TgiError("Invalid alternate register field handle", TgiFaultCode.INVALID_ID)
    alternate_register = _register_owned_child(field, AlternateRegisters.AlternateRegister)
    if alternate_register is None or not any(item is field for item in alternate_register.field_value):
        raise TgiError("Field is not owned by an alternate register", TgiFaultCode.INVALID_ID)
    _register_graph(alternate_register)
    _list_attr(alternate_register, "field_value")
    if not detach_child_by_handle(regFieldID):
        raise TgiError("Could not remove alternate register field", TgiFaultCode.INVALID_ID)
    return True


def removeRegisterAlternateRegister(alternateRegisterID: str) -> bool:
    """Remove an alternateRegister and prune its empty optional holder.

    Section: F.7.74.25.

    Args:
        alternateRegisterID: Handle to an alternateRegister element.

    Returns:
        True when the alternateRegister was removed.
    """
    alternate = resolve_handle(alternateRegisterID)
    if not isinstance(alternate, AlternateRegisters.AlternateRegister):
        raise TgiError("Invalid alternateRegister handle", TgiFaultCode.INVALID_ID)
    holder = _register_owned_child(alternate, AlternateRegisters)
    info = get_parent_info(alternateRegisterID)
    if (
        holder is None
        or info is None
        or info.path != ("alternate_register",)
        or info.container != "list"
        or not any(item is alternate for item in getattr(holder, "alternate_register", ()))
    ):
        raise TgiError("alternateRegister is not owned by a register", TgiFaultCode.INVALID_ID)
    register = _register_owned_child(holder, _REGISTER_TYPES)
    holder_info = get_parent_info(get_handle(holder))
    if (
        register is None
        or holder_info is None
        or holder_info.path != ("alternate_registers",)
        or holder_info.container != "single"
        or getattr(register, "alternate_registers", None) is not holder
    ):
        raise TgiError("alternateRegisters has no supported register owner", TgiFaultCode.INVALID_ID)
    _register_graph(register)
    _list_attr(holder, "alternate_register")
    if not detach_child_by_handle(alternateRegisterID):
        raise TgiError("Could not remove alternateRegister", TgiFaultCode.INVALID_ID)
    if not holder.alternate_register and not detach_child_by_handle(get_handle(holder)):
        raise TgiError("Could not remove empty alternateRegisters holder", TgiFaultCode.INVALID_ID)
    return True


def removeRegisterField(registerFieldID: str) -> bool:
    """Remove an inline field from a register choice.

    Section: F.7.74.26.

    Args:
        registerFieldID: Handle to a field owned directly by a register.

    Returns:
        True when the field was removed.

    Removing the final field follows the TGI editing policy and can leave a model that
    requires a subsequent edit before schema validation succeeds.
    """
    field = resolve_handle(registerFieldID)
    if not isinstance(field, FieldType):
        raise TgiError("Invalid register field handle", TgiFaultCode.INVALID_ID)
    register = _register_owned_child(field, _REGISTER_TYPES)
    info = get_parent_info(registerFieldID)
    if (
        register is None
        or info is None
        or info.path != ("choice",)
        or info.container != "list"
        or not any(item is field for item in getattr(register, "choice", ()))
    ):
        raise TgiError("Field is not owned directly by a register", TgiFaultCode.INVALID_ID)
    _register_graph(register)
    _list_attr(register, "choice")
    if not detach_child_by_handle(registerFieldID):
        raise TgiError("Could not remove register field", TgiFaultCode.INVALID_ID)
    return True


def removeAlternateRegisterTypeIdentifier(alternateRegisterID: str) -> bool:
    """Remove the alternate register typeIdentifier.

    Section: F.7.74.14.

    Args:
        alternateRegisterID: Handle to an alternate register element.

    Returns:
        True if a typeIdentifier was removed, otherwise False.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    identifier = alternate_register.type_identifier
    if identifier is None:
        return False
    if not isinstance(identifier, str):
        raise TgiError("Invalid alternate register typeIdentifier", TgiFaultCode.INVALID_ID)
    alternate_register.type_identifier = None
    return True


def removeAlternateRegisterVolatility(alternateRegisterID: str) -> bool:
    """Remove explicit alternate register volatility.

    Section: F.7.74.15.

    Args:
        alternateRegisterID: Handle to an alternate register element.

    Returns:
        True if explicit volatility was removed, otherwise False.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    volatile = alternate_register.volatile
    if volatile is None:
        return False
    if not isinstance(volatile, Volatile) or type(volatile.value) is not bool:
        raise TgiError("Invalid alternate register volatile value", TgiFaultCode.INVALID_ID)
    volatile_id = get_handle(volatile)
    _register_graph(volatile)
    if not detach_child_by_handle(volatile_id):
        raise TgiError("Could not remove alternate register volatility", TgiFaultCode.INVALID_ID)
    return True


def removeAlternaterRegisterModeRef(modeRefID: str) -> bool:
    """Remove a modeRef from its containing element.

    Section: F.7.74.16.

    Args:
        modeRefID: Handle to a modeRef element.

    Returns:
        True when the modeRef was removed.
    """
    mode_ref_node = resolve_handle(modeRefID)
    if not isinstance(mode_ref_node, ModeRef):
        raise TgiError("Invalid modeRef handle", TgiFaultCode.INVALID_ID)
    parent = _register_owned_child(mode_ref_node)
    info = get_parent_info(modeRefID)
    if (
        parent is None
        or info is None
        or info.path != ("mode_ref",)
        or info.container != "list"
        or not any(item is mode_ref_node for item in getattr(parent, "mode_ref", ()))
    ):
        raise TgiError("modeRef has no supported owning element", TgiFaultCode.INVALID_ID)
    _register_graph(parent)
    _list_attr(parent, "mode_ref")
    if not detach_child_by_handle(modeRefID):
        raise TgiError("Could not remove modeRef", TgiFaultCode.INVALID_ID)
    return True


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


def removeRegisterFieldReset(resetID: str) -> bool:
    """Remove a reset from its owning inline register field (F.7.74.31).

    Section: F.7.74.31.

    Args:
        resetID: Handle to a reset element.

    Returns:
        True when the reset was removed.
    """
    reset = _resolve_reset(resetID)
    _register_owner_for(reset)
    holder = _register_owned_child(reset, FieldType.Resets)
    if holder is None:
        raise TgiError("Reset has no register field resets owner", TgiFaultCode.INVALID_ID)
    reset_info = get_parent_info(resetID)
    if (
        reset_info is None
        or reset_info.path != ("reset",)
        or reset_info.container != "list"
        or not any(item is reset for item in getattr(holder, "reset", ()))
    ):
        raise TgiError("Reset is not contained by its register field resets owner", TgiFaultCode.INVALID_ID)

    field = _register_owned_child(holder, FieldType)
    holder_info = get_parent_info(get_handle(holder))
    if (
        field is None
        or holder_info is None
        or holder_info.path != ("choice",)
        or holder_info.container != "list"
        or not any(item is holder for item in getattr(field, "choice", ()))
    ):
        raise TgiError("Reset has no register field owner", TgiFaultCode.INVALID_ID)
    field, _ = _resolve_register_field(get_handle(field))
    _register_graph(field)
    current_holder, _ = _register_field_resets(field)
    if current_holder is not holder:
        raise TgiError("Reset owner choice changed during removal", TgiFaultCode.INVALID_ID)
    resets = _list_attr(holder, "reset")
    if not any(item is reset for item in resets):
        raise TgiError("Reset is not in its register field resets group", TgiFaultCode.INVALID_ID)

    if not detach_child_by_handle(resetID):
        raise TgiError("Could not remove register field reset", TgiFaultCode.INVALID_ID)
    if not holder.reset and not detach_child_by_handle(get_handle(holder)):
        raise TgiError("Could not remove empty register field resets holder", TgiFaultCode.INVALID_ID)
    return True


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


def removeResetMask(resetID: str) -> bool:
    """Remove the optional mask from a reset.

    Section: F.7.74.37.

    Args:
        resetID: Handle to a reset element.

    Returns:
        True when an explicit mask was removed, otherwise False.
    """
    reset = _resolve_reset(resetID)
    mask = _reset_expression(reset, "mask", required=False)
    if mask is None:
        return False
    mask_id = get_handle(mask)
    if not detach_child_by_handle(mask_id):
        raise TgiError("Could not remove reset mask", TgiFaultCode.INVALID_ID)
    return True


def setAlternateRegisterTypeIdentifier(alternateRegisterID: str, typeIdentifier: str) -> bool:
    """Set alternate register typeIdentifier.

    Section: F.7.74.42.

    Args:
        alternateRegisterID: Handle to an alternate register element.
        typeIdentifier: New alternate register typeIdentifier name.

    Returns:
        True after setting the typeIdentifier.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    value = _schema_name(typeIdentifier, "Name")
    current = alternate_register.type_identifier
    if current is not None and not isinstance(current, str):
        raise TgiError("Invalid alternate register typeIdentifier", TgiFaultCode.INVALID_ID)
    alternate_register.type_identifier = value
    return True


def setAlternateRegisterVolatility(alternateRegisterID: str, _volatile: bool) -> bool:
    """Set explicit alternate register volatility.

    Section: F.7.74.43.

    Args:
        alternateRegisterID: Handle to an alternate register element.
        _volatile: Whether the alternate register value is volatile.

    Returns:
        True after setting explicit volatility.
    """
    alternate_register = _resolve_alternate_register(alternateRegisterID)
    if type(_volatile) is not bool:
        raise TgiError("_volatile must be a boolean", TgiFaultCode.INVALID_ARGUMENT)
    current = alternate_register.volatile
    if current is not None and (not isinstance(current, Volatile) or type(current.value) is not bool):
        raise TgiError("Invalid alternate register volatile value", TgiFaultCode.INVALID_ID)
    if current is None:
        current = Volatile(value=_volatile)
        alternate_register.volatile = current
    else:
        current.value = _volatile
    register_parent(current, alternate_register, ("volatile",), "single")
    _register_graph(current)
    return True


def setModeRefPriority(modeRefID: str, priority: int) -> bool:
    """Set the priority on a modeRef.

    Section: F.7.74.55.

    Args:
        modeRefID: Handle to a modeRef element.
        priority: Unique non-negative integer priority in the containing element.

    Returns:
        True after updating the priority.
    """
    mode_ref_node = resolve_handle(modeRefID)
    if not isinstance(mode_ref_node, ModeRef):
        raise TgiError("Invalid modeRef handle", TgiFaultCode.INVALID_ID)
    if type(priority) is not int or priority < 0:
        raise TgiError("priority must be a non-negative integer", TgiFaultCode.INVALID_ARGUMENT)
    parent = _register_owned_child(mode_ref_node)
    info = get_parent_info(modeRefID)
    if parent is None:
        if info is not None:
            raise TgiError("modeRef has no supported owning element", TgiFaultCode.INVALID_ID)
        mode_refs: list[ModeRef] | tuple[ModeRef, ...] = ()
    else:
        mode_refs = getattr(parent, "mode_ref", None)
        if (
            info is None
            or info.path != ("mode_ref",)
            or info.container != "list"
            or not isinstance(mode_refs, (list, tuple))
            or not any(item is mode_ref_node for item in mode_refs)
        ):
            raise TgiError("modeRef has no supported owning element", TgiFaultCode.INVALID_ID)
    if any(item is not mode_ref_node and getattr(item, "priority", None) == priority for item in mode_refs):
        raise TgiError(f"modeRef priority {priority} already exists in this element", TgiFaultCode.INVALID_ARGUMENT)
    if parent is not None:
        _register_graph(parent)
    mode_ref_node.priority = priority
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


def setFieldDefinitionBitWidth(fieldDefinitionID: str, value: str) -> bool:
    """Set a field definition's positive unsigned 32-bit bitWidth expression.

    Section: F.7.74.52.

    Args:
        fieldDefinitionID: Handle to a fieldDefinition element.
        value: New bitWidth expression source.

    Returns:
        True after updating the existing expression wrapper.
    """
    field = _resolve_field_definition(fieldDefinitionID)
    width = _field_definition_width(field)
    source = _register_file_expression(value, "bitWidth", 1, _UINT32_MAX, width)
    width.value = source
    return True


def setFieldDefinitionTypeIdentifier(fieldDefinitionID: str, value: str) -> bool:
    """Set a field definition's typeIdentifier name.

    Section: F.7.74.53.

    Args:
        fieldDefinitionID: Handle to a fieldDefinition element.
        value: XML Name for the typeIdentifier.

    Returns:
        True after setting the typeIdentifier string.
    """
    field = _resolve_field_definition(fieldDefinitionID)
    source = _schema_name(value, "Name")
    field.type_identifier = source
    return True


def setFieldDefinitionVolatile(fieldDefinitionID: str, value: bool) -> bool:
    """Set a field definition's volatile Boolean.

    Section: F.7.74.54.

    Args:
        fieldDefinitionID: Handle to a fieldDefinition element.
        value: New volatility Boolean.

    Returns:
        True after setting the volatile element.
    """
    field = _resolve_field_definition(fieldDefinitionID)
    if not isinstance(value, bool):
        raise TgiError("Field definition volatility must be a Boolean", TgiFaultCode.INVALID_ARGUMENT)
    field.volatile = value
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


def setResetMask(resetID: str, mask: str) -> bool:
    """Set the optional mask expression on a reset.

    Section: F.7.74.68.

    Args:
        resetID: Handle to a reset element.
        mask: SystemVerilog expression for the reset mask.

    Returns:
        True after setting the mask source.
    """
    reset = _resolve_reset(resetID)
    width = _reset_field_width(reset, deferred=True)
    source = _reset_expression_source(mask, width)
    current = _reset_expression(reset, "mask", required=False)
    if current is None:
        current = UnsignedBitVectorExpression(value=source)
        reset.mask = current
    else:
        current.value = source
    register_parent(current, reset, ("mask",), "single")
    _register_graph(current)
    return True


def setResetValue(resetID: str, value: str) -> bool:
    """Set the mandatory reset value expression.

    Section: F.7.74.69.

    Args:
        resetID: Handle to a reset element.
        value: SystemVerilog expression for the reset value.

    Returns:
        True after setting the value source.
    """
    reset = _resolve_reset(resetID)
    width = _reset_field_width(reset, deferred=True)
    source = _reset_expression_source(value, width)
    current = _reset_expression(reset, "value", required=True)
    assert current is not None
    current.value = source
    register_parent(current, reset, ("value",), "single")
    _register_graph(current)
    return True
