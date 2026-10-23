"""Register file category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.75) and EXTENDED (F.7.76) Register file functions. Only
2022 standard APIs defined by Annex F are exported; no vendor extensions or
legacy names are exposed. BASE getters raise :class:`TgiError` with
:class:`TgiFaultCode.INVALID_ID` for invalid handles. EXTENDED mutators
raise :class:`TgiError` with :class:`TgiFaultCode.INVALID_ID` for invalid
handles and :class:`TgiFaultCode.INVALID_ARGUMENT` for semantic violations.

Edits preserve typed XML choices, expression sources and wrapper metadata.
Numeric getters evaluate self-contained unsigned constants with SvExpressionParser.
Definition targets resolve through the owning document's external declarations.
Replaced or removed children invalidate descendant handles.
"""

from collections.abc import Iterable
from typing import NoReturn

from org.accellera.ipxact.v1685_2022 import (
    AccessPolicies,
    AddressBlockRef,
    Component,
    ComponentType,
    ExternalTypeDefinitions,
    FieldType,
    Index,
    Indices,
    RegisterFile,
    RegisterFileDefinitions,
    RegisterFileRef,
    SimpleAccessHandle,
    TypeDefinitions,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

from ._attribute_references import _root_for
from ._expressions import _integer, _source
from .address_space import _register_owned_child
from .component import _list_attr, _register_graph
from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    register_parent,
    registry,
    resolve_handle,
)
from .port_map import _name as _schema_name

__all__ = [
    # BASE (F.7.75)
    "getAliasOfRegisterFileRefByNames",
    "getAliasOfRegisterFileRefIDs",
    "getRegisterFileAccessHandleIDs",
    "getRegisterFileAccessPolicyIDs",
    "getRegisterFileAddressOffset",
    "getRegisterFileAddressOffsetExpression",
    "getRegisterFileArrayID",
    "getRegisterFileRange",
    "getRegisterFileRangeExpression",
    "getRegisterFileRangeID",
    "getRegisterFileRefIndexIDs",
    "getRegisterFileRegisterFileDefinitionRefByExternalTypeDefID",
    "getRegisterFileRegisterFileDefinitionRefByID",
    "getRegisterFileRegisterFileDefinitionRefByName",
    "getRegisterFileRegisterFileDefinitionRefID",
    "getRegisterFileRegisterFileIDs",
    "getRegisterFileRegisterIDs",
    "getRegisterFileTypeIdentifier",
    # EXTENDED (F.7.76)
    "addAliasOfRegisterFileRef",
    "addRegisterFileDefinitionRegisterFile",
    "addRegisterFileRefIndex",
    "addRegisterFileRegister",
    "removeAliasOfRegisterFileRef",
    "removeRegisterFileAccessHandle",
    "removeRegisterFileRefIndex",
    "removeRegisterFileRegister",
    "removeRegisterFileRegisterFile",
    "removeRegisterFileTypeIdentifier",
    "setRegisterFileAddressOffset",
    "setRegisterFileRange",
    "setRegisterFileRegisterFileDefinitionRef",
    "setRegisterFileTypeIdentifier",
]

# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------

type _Expression = (
    UnsignedIntExpression
    | UnsignedLongintExpression
    | UnsignedPositiveIntExpression
    | UnsignedPositiveLongintExpression
    | Index
)
type _Definition = RegisterFileDefinitions.RegisterFileDefinition
type _Document = Component | TypeDefinitions

_UINT64_MAX = (1 << 64) - 1
_UINT32_MAX = (1 << 32) - 1


def _error(message: str, fault: str = TgiFaultCode.INVALID_ARGUMENT) -> NoReturn:
    raise TgiError(message, fault)


def _owning_root(obj: RegisterFile) -> _Document | None:
    root = _root_for(obj)
    if not isinstance(root, (Component, TypeDefinitions)):
        return None
    _register_graph(root)
    return root


def _resolve_rf(registerFileID: str) -> RegisterFile:
    obj = resolve_handle(registerFileID)
    if not isinstance(obj, RegisterFile):
        _error("Invalid registerFile handle", TgiFaultCode.INVALID_ID)
    _register_graph(obj)
    return obj


def _resolve_alias(aliasOfID: str) -> FieldType.AliasOf:
    obj = resolve_handle(aliasOfID)
    if not isinstance(obj, FieldType.AliasOf):
        _error("Invalid aliasOf handle", TgiFaultCode.INVALID_ID)
    _register_graph(obj)
    return obj


def _resolve_register_file_ref(registerFileRefID: str) -> RegisterFileRef:
    obj = resolve_handle(registerFileRefID)
    if not isinstance(obj, RegisterFileRef):
        _error("Invalid registerFileRef handle", TgiFaultCode.INVALID_ID)
    _register_graph(obj)
    return obj


def _choice[T](parent: RegisterFile, model_type: type[T]) -> T | None:
    return next((child for child in getattr(parent, "choice", ()) if isinstance(child, model_type)), None)


def _choice_children[T](parent: RegisterFile, model_type: type[T]) -> list[T]:
    return [child for child in getattr(parent, "choice", ()) if isinstance(child, model_type)]


def _child_ids(parent: object, children: Iterable[object], path: tuple[str, ...]) -> list[str]:
    result = []
    for child in children:
        register_parent(child, parent, path, "list")
        _register_graph(child)
        result.append(get_handle(child))
    return result


def _expression(source: str, argument: str, minimum: int, maximum: int, wrapper: _Expression | None = None) -> str:
    if not isinstance(source, str):
        _error(f"{argument} must be a non-empty expression string")
    value = _source(source, wrapper, maximum)
    number = _integer(value, maximum, True)
    lower = minimum
    upper = maximum
    if wrapper is not None:
        current_minimum = getattr(wrapper, "minimum", None)
        current_maximum = getattr(wrapper, "maximum", None)
        if current_minimum is not None:
            lower = max(lower, current_minimum)
        if current_maximum is not None:
            upper = min(upper, current_maximum)
    if lower > upper or (number is not None and not lower <= number <= upper):
        _error(f"{argument} is outside the supported integer range")
    return value


def _name(source: str, argument: str) -> str:
    del argument
    return _schema_name(source, "Name")


def _numeric(node: _Expression | None, label: str, minimum: int = 0, maximum: int = _UINT64_MAX) -> int | None:
    if node is None:
        return None
    value = _integer(node.value, maximum)
    if value is None:
        _error(f"{label} expression cannot be evaluated")
    declared_minimum = getattr(node, "minimum", None)
    declared_maximum = getattr(node, "maximum", None)
    if (declared_minimum is not None and value < declared_minimum) or (
        declared_maximum is not None and value > declared_maximum
    ):
        _error(f"{label} is outside its declared bounds")
    if value < minimum:
        _error(f"{label} is outside the supported integer range")
    return value


def _offset(rf: RegisterFile) -> UnsignedLongintExpression:
    node = getattr(rf, "address_offset", None)
    if not isinstance(node, UnsignedLongintExpression):
        _error("Invalid registerFile addressOffset model", TgiFaultCode.INVALID_ID)
    return node


def _range(rf: RegisterFile) -> UnsignedPositiveLongintExpression | None:
    nodes = _choice_children(rf, UnsignedPositiveLongintExpression)
    if len(nodes) > 1:
        _error("Multiple registerFile ranges", TgiFaultCode.INVALID_ID)
    return nodes[0] if nodes else None


def _definition_ref(rf: RegisterFile) -> RegisterFile.RegisterFileDefinitionRef | None:
    refs = _choice_children(rf, RegisterFile.RegisterFileDefinitionRef)
    if len(refs) > 1:
        _error("Multiple registerFileDefinitionRefs", TgiFaultCode.INVALID_ID)
    return refs[0] if refs else None


def _alias_refs(alias: FieldType.AliasOf) -> list[RegisterFileRef]:
    return list(alias.register_file_ref)


def _indices(ref: RegisterFileRef | AddressBlockRef) -> list[Index]:
    if isinstance(ref, RegisterFileRef):
        return list(ref.indices.index) if ref.indices is not None else []
    if isinstance(ref, AddressBlockRef):
        return list(ref.indices.index) if ref.indices is not None else []
    _error("Invalid registerFileRef handle", TgiFaultCode.INVALID_ID)


def _append(parent: object, attr: str, child: object) -> None:
    items = _list_attr(parent, attr)
    items.append(child)


def _register_parent_graph(child: object, parent: object, attr: str, container: str) -> None:
    register_parent(child, parent, (attr,), container)
    _register_graph(child)


def _prune_empty_indices(ref: RegisterFileRef) -> None:
    holder = ref.indices
    if holder is not None and not holder.index:
        owner = _register_owned_child(holder, RegisterFileRef)
        if owner is ref:
            detach_child_by_handle(get_handle(holder))


def _detach_choice_child(rf: RegisterFile, child: object) -> None:
    handle = get_handle(child)
    _list_attr(rf, "choice")
    register_parent(child, rf, ("choice",), "list")
    _register_graph(child)
    if not detach_child_by_handle(handle):
        _error("Could not replace registerFile definition choice", TgiFaultCode.INVALID_ID)


def _replace_definition_ref(rf: RegisterFile, ref: RegisterFile.RegisterFileDefinitionRef) -> None:
    refs = _choice_children(rf, RegisterFile.RegisterFileDefinitionRef)
    if len(refs) > 1:
        _error("Multiple registerFileDefinitionRefs", TgiFaultCode.INVALID_ID)
    if refs:
        refs[0].value = ref.value
        refs[0].type_definitions = ref.type_definitions
        return
    for child in list(_list_attr(rf, "choice")):
        if not isinstance(child, str):
            _detach_choice_child(rf, child)
        else:
            rf.choice.remove(child)
    rf.choice.append(ref)
    _register_parent_graph(ref, rf, "choice", "list")


def _inline_choice(rf: RegisterFile, requirement: str) -> UnsignedPositiveLongintExpression:
    if _definition_ref(rf) is not None:
        _error(f"{requirement} requires an inline registerFile definition")
    range_node = _range(rf)
    if range_node is None:
        _error(f"{requirement} requires a registerFile range")
    return range_node


def _owner_type_definitions(root: _Document) -> ComponentType.TypeDefinitions | TypeDefinitions | None:
    return root if isinstance(root, TypeDefinitions) else getattr(root, "type_definitions", None)


def _external_type_definition(owner: _Document, name: str) -> ExternalTypeDefinitions | None:
    definitions = _owner_type_definitions(owner) if owner is not None else None
    if definitions is None:
        return None
    matches = [
        external
        for external in getattr(definitions, "external_type_definitions", ())
        if _name(external.name, "name") == _name(name, "typeDefinitions")
    ]
    if len(matches) > 1:
        _error(f"Ambiguous externalTypeDefinitions name {name!r}")
    return matches[0] if matches else None


def _scoped_external(rf: RegisterFile, type_definitions: str) -> ExternalTypeDefinitions | None:
    root = _owning_root(rf)
    if root is None:
        return None
    return _external_type_definition(root, type_definitions)


def _referenced_type_definitions(external: ExternalTypeDefinitions) -> TypeDefinitions | None:
    reference = getattr(external, "type_definitions_ref", None)
    if reference is None:
        return None
    vlnv = tuple(getattr(reference, part, None) for part in ("vendor", "library", "name", "version"))
    if any(not isinstance(value, str) or not value for value in vlnv):
        return None
    root_id = registry.get_id(vlnv)
    root = resolve_handle(root_id) if root_id is not None else None
    if root is None:
        return None
    if not isinstance(root, TypeDefinitions):
        _error("external typeDefinitions target is not a TypeDefinitions document", TgiFaultCode.INVALID_ID)
    _register_graph(root)
    return root


def _definition_by_name(rf: RegisterFile, ref: RegisterFile.RegisterFileDefinitionRef) -> _Definition | None:
    external = _scoped_external(rf, ref.type_definitions)
    if external is None:
        return None
    definitions = _referenced_type_definitions(external)
    if definitions is None:
        return None
    group = getattr(definitions, "register_file_definitions", None)
    if group is None:
        return None
    matches = [item for item in group.register_file_definition if _name(item.name, "name") == _name(ref.value, "value")]
    if len(matches) > 1:
        _error(f"Ambiguous registerFileDefinition name {ref.value!r}")
    if matches:
        register_parent(group, definitions, ("register_file_definitions",), "single")
        register_parent(matches[0], group, ("register_file_definition",), "list")
        _register_graph(matches[0])
        return matches[0]
    return None


# ---------------------------------------------------------------------------
# BASE (F.7.75)
# ---------------------------------------------------------------------------


def getAliasOfRegisterFileRefByNames(aliasOfID: str) -> list[str]:
    """Section: F.7.75.1.

    Args:
        aliasOfID: Handle to an aliasOf element.

    Returns:
        List of registerFileRef names.
    """
    alias = _resolve_alias(aliasOfID)
    return [ref.register_file_ref for ref in _alias_refs(alias)]


def getAliasOfRegisterFileRefIDs(aliasOfID: str) -> list[str]:
    """Section: F.7.75.2.

    Args:
        aliasOfID: Handle to an aliasOf element.

    Returns:
        Owned registerFileRef node handles in hierarchical path order.
    """
    alias = _resolve_alias(aliasOfID)
    return _child_ids(alias, _alias_refs(alias), ("register_file_ref",))


def getRegisterFileAccessHandleIDs(registerFileID: str) -> list[str]:
    """Section: F.7.75.3.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        List of accessHandle handles.
    """
    rf = _resolve_rf(registerFileID)
    container = rf.access_handles
    if container is None:
        return []
    return _child_ids(container, container.access_handle, ("access_handle",))


def getRegisterFileAccessPolicyIDs(registerFileID: str) -> list[str]:
    """Section: F.7.75.4.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        List of accessPolicy handles.
    """
    rf = _resolve_rf(registerFileID)
    policies = _choice(rf, AccessPolicies)
    if policies is None:
        return []
    return _child_ids(policies, policies.access_policy, ("access_policy",))


def getRegisterFileAddressOffset(registerFileID: str) -> int | None:
    """Section: F.7.75.5.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Evaluated unsigned 64-bit addressOffset; unresolved expressions fault.
    """
    return _numeric(_offset(_resolve_rf(registerFileID)), "addressOffset")


def getRegisterFileAddressOffsetExpression(registerFileID: str) -> str | None:
    """Section: F.7.75.6.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        addressOffset source expression.
    """
    return _offset(_resolve_rf(registerFileID)).value


def getRegisterFileArrayID(registerFileID: str) -> str | None:
    """Section: F.7.75.7.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Handle to the array, or None when absent.
    """
    rf = _resolve_rf(registerFileID)
    if rf.array is None:
        return None
    register_parent(rf.array, rf, ("array",), "single")
    _register_graph(rf.array)
    return get_handle(rf.array)


def getRegisterFileRange(registerFileID: str) -> int | None:
    """Section: F.7.75.8.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Numeric range value, or None when the file uses a definition reference.
    """
    return _numeric(_range(_resolve_rf(registerFileID)), "range", 1)


def getRegisterFileRangeExpression(registerFileID: str) -> str | None:
    """Section: F.7.75.9.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Range source expression, or None when range is absent.
    """
    node = _range(_resolve_rf(registerFileID))
    return node.value if node is not None else None


def getRegisterFileRangeID(registerFileID: str) -> str | None:
    """Section: F.7.75.10.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Handle to the range, or None when range is absent.
    """
    node = _range(_resolve_rf(registerFileID))
    if node is None:
        return None
    register_parent(node, _resolve_rf(registerFileID), ("choice",), "list")
    return get_handle(node)


def getRegisterFileRefIndexIDs(addressBlockRefID: str) -> list[str]:
    """Section: F.7.75.11.

    Args:
        addressBlockRefID: Handle to a registerFileRef or addressBlockRef element.

    Returns:
        List of handles to the reference indices.
    """
    ref = resolve_handle(addressBlockRefID)
    if not isinstance(ref, (RegisterFileRef, AddressBlockRef)):
        _error("Invalid reference handle", TgiFaultCode.INVALID_ID)
    _register_graph(ref)
    return _child_ids(ref.indices, _indices(ref), ("index",)) if ref.indices is not None else []


def getRegisterFileRegisterFileDefinitionRefByExternalTypeDefID(registerFileID: str) -> str | None:
    """Section: F.7.75.12.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Handle to its externalTypeDefinitions declaration, if resolved.
    """
    rf = _resolve_rf(registerFileID)
    ref = _definition_ref(rf)
    if ref is None:
        return None
    external = _scoped_external(rf, ref.type_definitions)
    if external is None:
        return None
    root = _owning_root(rf)
    definitions = _owner_type_definitions(root) if root is not None else None
    if definitions is not None:
        register_parent(external, definitions, ("external_type_definitions",), "list")
    return get_handle(external)


def getRegisterFileRegisterFileDefinitionRefByID(registerFileID: str) -> str | None:
    """Section: F.7.75.13.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Handle to the referenced registerFileDefinition, if loaded.
    """
    rf = _resolve_rf(registerFileID)
    ref = _definition_ref(rf)
    target = _definition_by_name(rf, ref) if ref is not None else None
    return get_handle(target) if target is not None else None


def getRegisterFileRegisterFileDefinitionRefByName(registerFileID: str) -> str | None:
    """Section: F.7.75.14.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Referenced registerFileDefinition name, if present.
    """
    ref = _definition_ref(_resolve_rf(registerFileID))
    return ref.value if ref is not None else None


def getRegisterFileRegisterFileDefinitionRefID(registerFileID: str) -> str | None:
    """Section: F.7.75.15.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        Handle to the registerFileDefinitionRef element.
    """
    ref = _definition_ref(_resolve_rf(registerFileID))
    if ref is None:
        return None
    register_parent(ref, _resolve_rf(registerFileID), ("choice",), "list")
    return get_handle(ref)


def getRegisterFileRegisterFileIDs(registerFileID: str) -> list[str]:
    """Section: F.7.75.16.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        List of nested registerFile handles.
    """
    rf = _resolve_rf(registerFileID)
    if _definition_ref(rf) is not None:
        return []
    return _child_ids(rf, _choice_children(rf, RegisterFile), ("choice",))


def getRegisterFileRegisterIDs(registerFileID: str) -> list[str]:
    """Section: F.7.75.17.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        List of register handles.
    """
    rf = _resolve_rf(registerFileID)
    if _definition_ref(rf) is not None:
        return []
    return _child_ids(rf, _choice_children(rf, RegisterFile.Register), ("choice",))


def getRegisterFileTypeIdentifier(registerFileID: str) -> str | None:
    """Section: F.7.75.18.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        typeIdentifier value, or None when absent.
    """
    rf = _resolve_rf(registerFileID)
    if _definition_ref(rf) is not None:
        return None
    return next((value for value in rf.choice if isinstance(value, str)), None)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.76)
# ---------------------------------------------------------------------------


def addAliasOfRegisterFileRef(aliasOfID: str, registerFileRef: str) -> str:
    """Section: F.7.76.1.

    Args:
        aliasOfID: Handle to an aliasOf element.
        registerFileRef: Name of the referenced registerFile.

    Returns:
        Handle to the new registerFileRef.
    """
    alias = _resolve_alias(aliasOfID)
    name = _name(registerFileRef, "registerFileRef")
    ref = RegisterFileRef(register_file_ref=name)
    _append(alias, "register_file_ref", ref)
    _register_parent_graph(ref, alias, "register_file_ref", "list")
    return get_handle(ref)


def addRegisterFileDefinitionRegisterFile(
    registerFileDefinitionID: str,
    name: str,
    addressOffset: str,
    range: str,
) -> str:
    """Section: F.7.76.2.

    Args:
        registerFileDefinitionID: Handle to a registerFileDefinition.
        name: Name of the new registerFile.
        addressOffset: Register-file address offset expression.
        range: Positive register-file range expression.

    Returns:
        Handle to the added registerFile.
    """
    definition = resolve_handle(registerFileDefinitionID)
    expected = RegisterFileDefinitions.RegisterFileDefinition
    if not isinstance(definition, expected):
        _error("Invalid registerFileDefinition handle", TgiFaultCode.INVALID_ID)
    _register_graph(definition)
    file_name = _name(name, "name")
    offset_source = _expression(addressOffset, "addressOffset", 0, _UINT64_MAX)
    range_source = _expression(range, "range", 1, _UINT64_MAX)
    siblings = definition.register_or_register_file
    if any(_name(sibling.name, "name") == file_name for sibling in siblings):
        _error(f"registerFile name {file_name!r} already exists in this definition")
    child = RegisterFile(
        name=file_name,
        address_offset=UnsignedLongintExpression(value=offset_source),
        choice=[UnsignedPositiveLongintExpression(value=range_source)],
    )
    _append(definition, "register_or_register_file", child)
    _register_parent_graph(child, definition, "register_or_register_file", "list")
    return get_handle(child)


def addRegisterFileRefIndex(registerFileRefID: str, value: str) -> str:
    """Section: F.7.76.3.

    Args:
        registerFileRefID: Handle to a registerFileRef element.
        value: Index value.

    Returns:
        Handle to the added index.
    """
    ref = _resolve_register_file_ref(registerFileRefID)
    source = _expression(value, "value", 0, _UINT32_MAX)
    if ref.indices is None:
        ref.indices = Indices(index=[])
        register_parent(ref.indices, ref, ("indices",), "single")
    index = Index(value=source)
    _append(ref.indices, "index", index)
    _register_parent_graph(index, ref.indices, "index", "list")
    return get_handle(index)


def _register_names(rf: RegisterFile) -> set[str]:
    names: set[str] = set()
    for child in rf.choice:
        if isinstance(child, (RegisterFile, RegisterFile.Register)):
            child_name = getattr(child, "name", None)
            if isinstance(child_name, str):
                names.add(_name(child_name, "name"))
            if isinstance(child, RegisterFile.Register) and child.alternate_registers is not None:
                names.update(
                    _name(item.name, "name")
                    for item in child.alternate_registers.alternate_register
                    if isinstance(item.name, str)
                )
    return names


def addRegisterFileRegister(
    registerFileID: str,
    name: str,
    offset: str,
    size: str,
    fieldName: str,
    fieldOffset: str,
    fieldWidth: str,
) -> str:
    """Section: F.7.76.4.

    Args:
        registerFileID: Handle to a registerFile element.
        name: Register name.
        offset: Register offset expression.
        size: Register size expression.
        fieldName: Field name.
        fieldOffset: Field bit offset expression.
        fieldWidth: Field width expression.

    Returns:
        Handle to the new register element.
    """
    rf = _resolve_rf(registerFileID)
    _inline_choice(rf, "addRegisterFileRegister")
    reg_name = _name(name, "name")
    field_name = _name(fieldName, "fieldName")
    offset_source = _expression(offset, "offset", 0, _UINT64_MAX)
    size_source = _expression(size, "size", 1, _UINT32_MAX)
    field_offset_source = _expression(fieldOffset, "fieldOffset", 0, _UINT32_MAX)
    field_width_source = _expression(fieldWidth, "fieldWidth", 1, _UINT32_MAX)
    size_number = _integer(size_source, _UINT32_MAX, True)
    field_offset_number = _integer(field_offset_source, _UINT32_MAX, True)
    width_number = _integer(field_width_source, _UINT32_MAX, True)
    if (
        size_number is not None
        and field_offset_number is not None
        and width_number is not None
        and field_offset_number + width_number > size_number
    ):
        _error("field bit range exceeds register size")
    if reg_name in _register_names(rf):
        _error(f"register name {reg_name!r} already exists in this registerFile")
    field = FieldType(
        name=field_name,
        bit_offset=UnsignedIntExpression(value=field_offset_source),
        choice=[UnsignedPositiveIntExpression(value=field_width_source)],
    )
    register = RegisterFile.Register(
        name=reg_name,
        address_offset=UnsignedLongintExpression(value=offset_source),
        choice=[UnsignedPositiveIntExpression(value=size_source), field],
    )
    _append(rf, "choice", register)
    _register_parent_graph(register, rf, "choice", "list")
    return get_handle(register)


def _remove_owned(handle: str, expected_type: type, label: str) -> bool:
    obj = resolve_handle(handle)
    if not isinstance(obj, expected_type):
        _error(f"Invalid {label} handle", TgiFaultCode.INVALID_ID)
    parent_type = {
        "registerFileRef": FieldType.AliasOf,
        "accessHandle": RegisterFile.AccessHandles,
        "index": Indices,
        "register": RegisterFile,
        "registerFile": (RegisterFile, RegisterFileDefinitions.RegisterFileDefinition),
    }[label]
    parent = _register_owned_child(obj, parent_type)
    if parent is None:
        _error(f"Unowned {label} handle", TgiFaultCode.INVALID_ID)
    holder_owner = None
    if label in ("index", "accessHandle"):
        holder_owner = _register_owned_child(parent, RegisterFileRef if label == "index" else RegisterFile)
        if holder_owner is None:
            _error(f"Invalid {label} owner", TgiFaultCode.INVALID_ID)
    attr = {"registerFileRef": "register_file_ref", "accessHandle": "access_handle", "index": "index"}.get(label)
    if attr is None:
        attr = "choice" if isinstance(parent, RegisterFile) else "register_or_register_file"
    if not any(item is obj for item in getattr(parent, attr)):
        _error(f"Invalid {label} ownership", TgiFaultCode.INVALID_ID)
    _list_attr(parent, attr)
    _register_graph(parent)
    removed = detach_child_by_handle(handle)
    if removed and holder_owner is not None and not getattr(parent, attr):
        _register_graph(holder_owner)
        detach_child_by_handle(get_handle(parent))
    return removed


def removeAliasOfRegisterFileRef(registerFileRefID: str) -> bool:
    """Section: F.7.76.5.

    Args:
        registerFileRefID: Handle to a registerFileRef element.

    Returns:
        True when the reference was removed.
    """
    return _remove_owned(registerFileRefID, RegisterFileRef, "registerFileRef")


def removeRegisterFileAccessHandle(accessHandleID: str) -> bool:
    """Section: F.7.76.6.

    Args:
        accessHandleID: Handle to the accessHandle to remove.

    Returns:
        True when the accessHandle was removed.
    """
    return _remove_owned(accessHandleID, SimpleAccessHandle, "accessHandle")


def removeRegisterFileRefIndex(indexID: str) -> bool:
    """Section: F.7.76.7.

    Args:
        indexID: Handle to an index element.

    Returns:
        True when the index was removed.
    """
    return _remove_owned(indexID, Index, "index")


def removeRegisterFileRegister(registerID: str) -> bool:
    """Section: F.7.76.8.

    Args:
        registerID: Handle to a register element.

    Returns:
        True when the register was removed.
    """
    return _remove_owned(registerID, RegisterFile.Register, "register")


def removeRegisterFileRegisterFile(registerFileID: str) -> bool:
    """Section: F.7.76.9.

    Args:
        registerFileID: Handle to the nested registerFile element to remove.

    Returns:
        True when the nested registerFile was removed.
    """
    return _remove_owned(registerFileID, RegisterFile, "registerFile")


def removeRegisterFileTypeIdentifier(registerFileID: str) -> bool:
    """Section: F.7.76.10.

    Args:
        registerFileID: Handle to a registerFile element.

    Returns:
        True if a typeIdentifier was removed, otherwise False.
    """
    rf = _resolve_rf(registerFileID)
    if _definition_ref(rf) is not None:
        return False
    indexes = [index for index, item in enumerate(rf.choice) if isinstance(item, str)]
    if not indexes:
        return False
    del _list_attr(rf, "choice")[indexes[0]]
    return True


def setRegisterFileAddressOffset(registerFileID: str, expression: str) -> bool:
    """Section: F.7.76.11.

    Args:
        registerFileID: Handle to a registerFile element.
        expression: New addressOffset expression.

    Returns:
        True when addressOffset was set.
    """
    rf = _resolve_rf(registerFileID)
    current = _offset(rf)
    source = _expression(expression, "addressOffset", 0, _UINT64_MAX, current)
    current.value = source
    register_parent(current, rf, ("address_offset",), "single")
    return True


def setRegisterFileRange(registerFileID: str, expression: str) -> bool:
    """Section: F.7.76.12.

    Args:
        registerFileID: Handle to a registerFile element.
        expression: New positive range expression.

    Returns:
        True when range was set.
    """
    rf = _resolve_rf(registerFileID)
    current = _range(rf)
    source = _expression(expression, "range", 1, _UINT64_MAX, current)
    _list_attr(rf, "choice")
    if _definition_ref(rf) is not None:
        for child in list(rf.choice):
            if not isinstance(child, str):
                _detach_choice_child(rf, child)
            else:
                rf.choice.remove(child)
        current = UnsignedPositiveLongintExpression(value=source)
        rf.choice.append(current)
        _register_parent_graph(current, rf, "choice", "list")
    elif current is None:
        current = UnsignedPositiveLongintExpression(value=source)
        type_identifier_position = next((index + 1 for index, item in enumerate(rf.choice) if isinstance(item, str)), 0)
        rf.choice.insert(type_identifier_position, current)
        _register_parent_graph(current, rf, "choice", "list")
    else:
        current.value = source
        register_parent(current, rf, ("choice",), "list")
    return True


def setRegisterFileRegisterFileDefinitionRef(registerFileID: str, value: str, typeDefinitions: str) -> bool:
    """Section: F.7.76.13.

    Args:
        registerFileID: Handle to a registerFile element.
        value: Referenced registerFileDefinition name.
        typeDefinitions: Name of the component externalTypeDefinitions.

    Returns:
        True when the definition reference was set.
    """
    rf = _resolve_rf(registerFileID)
    definition_name = _name(value, "value")
    type_name = _name(typeDefinitions, "typeDefinitions")
    ref = RegisterFile.RegisterFileDefinitionRef(value=definition_name, type_definitions=type_name)
    _replace_definition_ref(rf, ref)
    return True


def setRegisterFileTypeIdentifier(registerFileID: str, typeIdentifier: str) -> bool:
    """Section: F.7.76.14.

    Args:
        registerFileID: Handle to a registerFile element.
        typeIdentifier: Register-file typeIdentifier.

    Returns:
        True when typeIdentifier was set.
    """
    rf = _resolve_rf(registerFileID)
    _inline_choice(rf, "setRegisterFileTypeIdentifier")
    value = _name(typeIdentifier, "typeIdentifier")
    _list_attr(rf, "choice")
    indexes = [index for index, item in enumerate(rf.choice) if isinstance(item, str)]
    if len(indexes) > 1:
        _error("Multiple registerFile typeIdentifiers", TgiFaultCode.INVALID_ID)
    if indexes:
        rf.choice[indexes[0]] = value
    else:
        range_position = next(
            (index for index, item in enumerate(rf.choice) if isinstance(item, UnsignedPositiveLongintExpression)),
            len(rf.choice),
        )
        rf.choice.insert(range_position, value)
    return True
