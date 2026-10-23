"""Access policy operations for the IEEE 1685-2022 TGI.

This module implements Annex F sections F.7.6.1, F.7.9.1-F.7.9.49, and F.7.10.1-F.7.10.49. Field policy values and
write constraints use the generated schema choice models; setters keep the selected branches in schema order. A
fieldAccessPolicyDefinitionRef resolves its externalTypeDefinitions name in the owning document, then follows that
entry's VLNV to a registered typeDefinitions document. Mode references resolve against the owning document.

Numeric getters evaluate self-contained SystemVerilog integer expressions, while paired expression getters preserve
source text. Parsed traversal registers ownership so removal invalidates the removed subtree. Invalid handles raise
TgiError with INVALID_ID; invalid values raise INVALID_ARGUMENT. Direct fieldAccessPolicyDefinition inspection is a
project extension outside Annex F.
"""

from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Literal

from org.accellera.ipxact.v1685_2022.access_policies import AccessPolicies

from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)

__all__: list[str] = [
    # F.7.6
    "getFieldAccessPolicyModeRefByID",
    # F.7.9 (BASE)
    "getAccessPolicyAccess",
    "getAccessPolicyModeRefByID",
    "getAccessPolicyModeRefByNames",
    "getAccessPolicyModeRefIDs",
    "getAccessRestrictionModeRefIDs",
    "getAccessRestrictionModeRefbyID",
    "getAccessRestrictionModeRefbyNames",
    "getAccessRestrictionReadAccessMask",
    "getAccessRestrictionReadAccessMaskExpression",
    "getAccessRestrictionReadAccessMaskID",
    "getAccessRestrictionWriteAccessMask",
    "getAccessRestrictionWriteAccessMaskExpression",
    "getAccessRestrictionWriteAccessMaskID",
    "getAlternateRegisterAccessPolicyIDs",
    "getBankAccessPoliciesIDs",
    "getFieldAccessPoliciesFieldAccessPolicyIDs",
    "getFieldAccessPolicyAccess",
    "getFieldAccessPolicyAccessRestrictionIDs",
    "getFieldAccessPolicyFieldAccessPolicyDefinitionRefByExternalTypeDefID",
    "getFieldAccessPolicyFieldAccessPolicyDefinitionRefByID",
    "getFieldAccessPolicyFieldAccessPolicyDefinitionRefByName",
    "getFieldAccessPolicyFieldAccessPolicyDefinitionRefID",
    "getFieldAccessPolicyModeRefByName",
    "getFieldAccessPolicyModeRefIDs",
    "getFieldAccessPolicyModifiedWriteValue",
    "getFieldAccessPolicyModifiedWriteValueID",
    "getFieldAccessPolicyReadAction",
    "getFieldAccessPolicyReadActionID",
    "getFieldAccessPolicyReadResponse",
    "getFieldAccessPolicyReadResponseExpression",
    "getFieldAccessPolicyReadResponseID",
    "getFieldAccessPolicyReserved",
    "getFieldAccessPolicyReservedExpression",
    "getFieldAccessPolicyReservedID",
    "getFieldAccessPolicyTestable",
    "getFieldAccessPolicyTestableID",
    "getFieldAccessPolicyWriteValueConstraintID",
    "getFieldAccesspolicyBroadcastToIDs",
    "getRegisterAccessPolicyIDs",
    "getRegisterFieldFieldAccessPoliciesID",
    "getTypeDefinitionsFieldAccessPolicyDefinitionIDs",
    "getWriteValueConstraintMaximum",
    "getWriteValueConstraintMaximumExpression",
    "getWriteValueConstraintMaximumID",
    "getWriteValueConstraintMinimum",
    "getWriteValueConstraintMinimumExpression",
    "getWriteValueConstraintMinimumID",
    "getWriteValueConstraintUseEnumeratedValues",
    "getWriteValueConstraintWriteAsRead",
    # FieldAccessPolicyDefinition subset (spec grouped under F.7.9)
    "getFieldAccessPolicyDefinitionIDs",
    "getFieldAccessPolicyDefinitionName",
    "getFieldAccessPolicyDefinitionDisplayName",
    "getFieldAccessPolicyDefinitionShortDescription",
    "getFieldAccessPolicyDefinitionDescription",
    "getFieldAccessPolicyDefinitionAccess",
    "getFieldAccessPolicyDefinitionModifiedWriteValue",
    "getFieldAccessPolicyDefinitionWriteValueConstraint",
    "getFieldAccessPolicyDefinitionReadAction",
    "getFieldAccessPolicyDefinitionReadResponse",
    # F.7.10 (EXTENDED)
    "addAccessRestrictionModeRef",
    "addAddressBlockAccessPolicy",
    "addAlternateRegisterAccessPolicy",
    "addExternalTypeDefinitionsResetTypeLink",
    "addFieldAccessPoliciesFieldAccessPolicy",
    "addFieldAccessPolicyAccessRestriction",
    "addFieldAccessPolicyBroadcastTo",
    "addFieldAccessPolicyModeRef",
    "addFieldDefinitionFieldAccessPolicy",
    "addRegisterAccessPolicy",
    "addRegisterFileAccessPolicy",
    "removeAccessPolicyAccess",
    "removeAccessRestrictionModeRef",
    "removeAccessRestrictionReadAccessMask",
    "removeAccessRestrictionWriteAccessMask",
    "removeAddressBlockAccessPolicyID",
    "removeAlternateRegisterAccessPolicy",
    "removeFieldAccessPoliciesFieldAccessPolicy",
    "removeFieldAccessPolicyAccess",
    "removeFieldAccessPolicyAccessRestriction",
    "removeFieldAccessPolicyBroadcastTo",
    "removeFieldAccessPolicyFieldAccessPolicyDefinitionRef",
    "removeFieldAccessPolicyModeRef",
    "removeFieldAccessPolicyModifiedWriteValue",
    "removeFieldAccessPolicyReadAction",
    "removeFieldAccessPolicyReadResponse",
    "removeFieldAccessPolicyReserved",
    "removeFieldAccessPolicyTestable",
    "removeFieldAccessPolicyWriteValueConstraint",
    "removeFieldDefinitionFieldAccessPolicy",
    "removeRegisterAccessPolicy",
    "removeRegisterFileAccessPolicy",
    "setAccessPolicyAccess",
    "setAccessRestrictionReadAccessMask",
    "setAccessRestrictionWriteAccessMask",
    "setFieldAccessPolicyAccess",
    "setFieldAccessPolicyFieldAccessPolicyDefinitionRef",
    "setFieldAccessPolicyModifiedWriteValue",
    "setFieldAccessPolicyReadAction",
    "setFieldAccessPolicyReadResponse",
    "setFieldAccessPolicyReserved",
    "setFieldAccessPolicyTestable",
    "setFieldAccessPolicyWriteValueConstraintMinMax",
    "setFieldAccessPolicyWriteValueConstraintUseEnumeratedValue",
    "setFieldAccessPolicyWriteValueConstraintWriteAsRead",
    "setWriteValueConstraintMaximum",
    "setWriteValueConstraintMinimum",
    "setWriteValueConstraintUseEnumeratedValues",
    "setWriteValueConstraintWriteAsRead",
]

Numeric = int


# ---------------------------------------------------------------------------
# Internal helpers (non-spec)
# ---------------------------------------------------------------------------


def _is_definition(obj: Any) -> bool:
    return (
        obj is not None
        and hasattr(obj, "modified_write_value")
        and hasattr(obj, "write_value_constraint")
        and not hasattr(obj, "mode_ref")  # inline policies have mode_ref
    )


def _is_inline_field_policy(obj: Any) -> bool:
    return (
        obj is not None
        and type(obj).__name__ == "FieldAccessPolicy"
        and type(obj).__module__.rsplit(".", 1)[-1] in {"field_type", "field_definitions"}
    )


def _definition_container_to_defs(containerID: str) -> list[Any]:
    container = resolve_handle(containerID)
    if (
        container is None
        or type(container).__name__ != "FieldAccessPolicyDefinitions"
        or type(container).__module__.rsplit(".", 1)[-1] != "field_access_policy_definitions"
    ):
        raise TgiError("Invalid fieldAccessPolicyDefinitions handle", TgiFaultCode.INVALID_ID)
    return list(getattr(container, "field_access_policy_definition", []))


def _ids(
    iterable: Iterable[Any],
    parent: Any | None = None,
    path: tuple[str, ...] | None = None,
) -> list[str]:
    return [_child_handle(obj, parent, path, "list") for obj in iterable]


def _model_children(obj: object) -> Iterator[tuple[object, tuple[str, ...], Literal["single", "list"]]]:
    """Yield generated model children and their ownership paths."""
    if not is_dataclass(obj) or isinstance(obj, type):
        return
    for model_field in fields(obj):
        value = getattr(obj, model_field.name)
        if is_dataclass(value) and not isinstance(value, type):
            yield value, (model_field.name,), "single"
        elif isinstance(value, (list, tuple)):
            for child in value:
                if is_dataclass(child) and not isinstance(child, type):
                    yield child, (model_field.name,), "list"


def _register_model_graph(root: Any) -> None:
    """Register ownership for parsed generated-model edges under ``root``."""
    pending = [root]
    seen: set[int] = set()
    while pending:
        parent = pending.pop()
        if id(parent) in seen:
            continue
        seen.add(id(parent))
        for child, path, container in _model_children(parent):
            register_parent(child, parent, path, container)
            pending.append(child)


def _root_contains(root: Any, element: Any) -> bool:
    pending = [root]
    seen: set[int] = set()
    while pending:
        obj = pending.pop()
        if obj is element:
            return True
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        pending.extend(child for child, _path, _container in _model_children(obj))
    return False


def _owning_root(element: Any) -> Any:
    """Find the smallest registered XML document containing ``element``."""
    roots = [resolve_handle(root_handle) for root_handle in registry.iter_by_predicate(lambda _root: True)]
    containing = [root for root in roots if root is not None and _root_contains(root, element)]
    if containing:
        root = min(containing, key=lambda candidate: sum(1 for _ in _walk_model(candidate)))
        _register_model_graph(root)
        return root
    current = element
    seen: set[int] = set()
    while id(current) not in seen:
        seen.add(id(current))
        parent_info = get_parent_info(get_handle(current))
        parent = resolve_handle(parent_info.parent_handle) if parent_info is not None else None
        if parent is None:
            break
        current = parent
    _register_model_graph(current)
    return current


def _walk_model(root: object) -> Iterator[object]:
    pending = [root]
    seen: set[int] = set()
    while pending:
        obj = pending.pop()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        yield obj
        pending.extend(child for child, _path, _container in _model_children(obj))


def _child_handle(
    child: Any,
    parent: Any | None = None,
    path: tuple[str, ...] | None = None,
    container: str = "single",
) -> str:
    if parent is not None and path is not None:
        register_parent(child, parent, path, container)
    return get_handle(child)


def _scalar(obj: Any, attr: str) -> str | None:
    v = getattr(obj, attr, None)
    if v is None:
        return None
    value = getattr(v, "value", v)
    return value.value if isinstance(value, Enum) else value


def _scalar_bool(obj: Any, attr: str) -> bool | None:
    v = getattr(obj, attr, None)
    if v is None:
        return None
    value = getattr(v, "value", v)
    return value.value if isinstance(value, Enum) else value


def _choice(policy: Any, model_type: type) -> Any | None:
    return next((item for item in getattr(policy, "choice", ()) if isinstance(item, model_type)), None)


def _choice_handle(policy: Any, model_type: type) -> str | None:
    child = _choice(policy, model_type)
    return _child_handle(child, policy, ("choice",), "list") if child is not None else None


def _evaluated_numeric(obj: Any) -> Numeric | None:
    if obj is None:
        return None
    source = getattr(obj, "value", None)
    if type(source) is int:
        return source
    if not isinstance(source, str) or not source.strip():
        return None
    try:
        try:
            return int(source, 0)
        except ValueError:
            from amal.eda.systemverilog.expression_parser import SvExpressionParser

            value = SvExpressionParser().evaluate(source)
            return value if type(value) is int else None
    except ImportError, ValueError, TypeError:
        return None
    except Exception as error:
        try:
            from amal.eda.systemverilog.expression_parser import SvExpressionError
        except ImportError:
            raise error from None
        if isinstance(error, SvExpressionError):
            return None
        raise


def _expression(obj: Any) -> str | None:
    if obj is None:
        return None
    value = getattr(obj, "value", None)
    return str(value) if value is not None else None


def _get_access_restrictions(policy: Any) -> list[Any]:
    cont = getattr(policy, "access_restrictions", None)
    if cont is None:
        return []
    return list(getattr(cont, "access_restriction", []))


def _get_write_value_constraint(policy: Any) -> Any | None:
    return getattr(policy, "write_value_constraint", None)


def _get_inline_field_policy(policyID: str) -> Any:
    obj = resolve_handle(policyID)
    if not _is_inline_field_policy(obj):
        raise TgiError("Invalid fieldAccessPolicy handle", TgiFaultCode.INVALID_ID)
    _owning_root(obj)
    return obj


def _get_access_policy(accessPolicyID: str) -> Any:
    obj = resolve_handle(accessPolicyID)
    if obj is None or not hasattr(obj, "mode_ref") or _is_inline_field_policy(obj):
        raise TgiError("Invalid accessPolicy handle", TgiFaultCode.INVALID_ID)
    if type(obj).__name__ != "AccessPolicy" or type(obj).__module__.rsplit(".", 1)[-1] != "access_policies":
        raise TgiError("Invalid accessPolicy handle", TgiFaultCode.INVALID_ID)
    _owning_root(obj)
    return obj


def _get_access_restriction_handle(restrictionID: str) -> Any:
    obj = resolve_handle(restrictionID)
    if obj is None or not hasattr(obj, "read_access_mask") or not hasattr(obj, "mode_ref"):
        raise TgiError("Invalid accessRestriction handle", TgiFaultCode.INVALID_ID)
    if type(obj).__name__ != "AccessRestrictionType":
        raise TgiError("Invalid accessRestriction handle", TgiFaultCode.INVALID_ID)
    _owning_root(obj)
    return obj


def _get_write_value_constraint_handle(wvcID: str) -> Any:
    obj = resolve_handle(wvcID)
    if obj is None or type(obj).__name__ != "WriteValueConstraint":
        raise TgiError("Invalid writeValueConstraint handle", TgiFaultCode.INVALID_ID)
    _owning_root(obj)
    return obj


def _field_policy_choice_types() -> tuple[type, type, type, type, type, type]:
    from org.accellera.ipxact.v1685_2022.access import Access
    from org.accellera.ipxact.v1685_2022.field_access_policy_definition_ref import FieldAccessPolicyDefinitionRef
    from org.accellera.ipxact.v1685_2022.modified_write_value import ModifiedWriteValue
    from org.accellera.ipxact.v1685_2022.read_action import ReadAction
    from org.accellera.ipxact.v1685_2022.read_response import ReadResponse
    from org.accellera.ipxact.v1685_2022.write_value_constraint import WriteValueConstraint

    return Access, FieldAccessPolicyDefinitionRef, ModifiedWriteValue, ReadAction, ReadResponse, WriteValueConstraint


def _owner_type_definitions(root: Any) -> Any | None:
    return root if type(root).__name__ == "TypeDefinitions" else getattr(root, "type_definitions", None)


def _external_type_definition(owner: Any, name: str) -> Any | None:
    type_definitions = _owner_type_definitions(owner)
    if type_definitions is None:
        return None
    matches = [
        external
        for external in getattr(type_definitions, "external_type_definitions", ())
        if getattr(external, "name", None) == name
    ]
    if len(matches) > 1:
        raise TgiError(
            f"Ambiguous externalTypeDefinitions name {name!r} in owning document",
            TgiFaultCode.INVALID_ARGUMENT,
        )
    return matches[0] if matches else None


def _referenced_type_definitions(external: Any) -> Any | None:
    reference = getattr(external, "type_definitions_ref", None)
    if reference is None:
        return None
    vlnv = tuple(getattr(reference, part, None) for part in ("vendor", "library", "name", "version"))
    if any(not isinstance(value, str) or not value for value in vlnv):
        return None
    root_handle = registry.get_id(vlnv)
    root = resolve_handle(root_handle) if root_handle is not None else None
    if root is None:
        return None
    return root if type(root).__name__ == "TypeDefinitions" else getattr(root, "type_definitions", None)


def _referenced_mode(source: Any, name: str) -> Any | None:
    root = _owning_root(source)
    type_definitions = _owner_type_definitions(root)
    modes = getattr(type_definitions, "modes", None)
    if modes is None:
        return None
    matches = [mode for mode in getattr(modes, "mode", ()) if getattr(mode, "name", None) == name]
    if len(matches) > 1:
        raise TgiError(f"Ambiguous mode name {name!r} in owning document", TgiFaultCode.INVALID_ARGUMENT)
    return matches[0] if matches else None


def _replace_choice(policy: Any, model_type: type, replacement: Any | None) -> None:
    """Update a typed choice in place or remove it while invalidating old handles."""
    choice = policy.choice
    old_indices = [index for index, item in enumerate(choice) if isinstance(item, model_type)]
    insert_at = old_indices[0] if old_indices else len(choice)
    if replacement is not None:
        if old_indices:
            existing = choice[insert_at]
            for model_field in fields(existing):
                if model_field.name not in {"id", "other_attributes", "vendor_extensions"}:
                    setattr(existing, model_field.name, getattr(replacement, model_field.name))
            register_parent(existing, policy, ("choice",), "list")
            for index in reversed(old_indices[1:]):
                old_handle = get_handle(choice[index])
                if get_parent_info(old_handle) is None:
                    register_parent(choice[index], policy, ("choice",), "list")
                detach_child_by_handle(old_handle)
            return
        choice.insert(_choice_insert_index(policy, replacement), replacement)
        register_parent(replacement, policy, ("choice",), "list")
        return
    for index in reversed(old_indices):
        old = choice[index]
        old_handle = get_handle(old)
        if get_parent_info(old_handle) is None:
            register_parent(old, policy, ("choice",), "list")
        detach_child_by_handle(old_handle)


def _replace_constraint_element(constraint: Any, model_type: type, replacement: Any | None) -> None:
    _replace_choice(constraint, model_type, replacement)


def _resolve_parent(handle: str, required: tuple[str, ...], label: str) -> Any:
    obj = resolve_handle(handle)
    allowed = {
        "addressBlock": {("address_block", "AddressBlock")},
        "alternateRegister": {("alternate_registers", "AlternateRegister")},
        "register": {
            ("address_block_type", "Register"),
            ("register_file", "Register"),
            ("register_file_definitions", "Register"),
            ("address_block_definitions", "Register"),
        },
        "registerFile": {("register_file", "RegisterFile"), ("register_file_definitions", "RegisterFile")},
        "fieldDefinition": {("field_definitions", "FieldDefinition")},
        "externalTypeDefinitions": {("external_type_definitions", "ExternalTypeDefinitions")},
    }.get(label)
    model_type = (type(obj).__module__.rsplit(".", 1)[-1], type(obj).__name__) if obj is not None else None
    if (
        obj is None
        or any(
            not hasattr(obj, name) and not (name == "access_policies" and hasattr(obj, "choice")) for name in required
        )
        or (allowed is not None and model_type not in allowed)
    ):
        raise TgiError(f"Invalid {label} handle", TgiFaultCode.INVALID_ID)
    _owning_root(obj)
    return obj


def _field_policy_module(policy: object) -> type:
    module_name = type(policy).__module__.rsplit(".", 1)[-1]
    if module_name == "field_type":
        from org.accellera.ipxact.v1685_2022.field_type import FieldType

        return FieldType.FieldAccessPolicies.FieldAccessPolicy
    from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions

    return FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy


def _field_policy_model_for_container(container: object) -> type:
    if type(container).__module__.rsplit(".", 1)[-1] == "field_type":
        from org.accellera.ipxact.v1685_2022.field_type import FieldType

        return FieldType.FieldAccessPolicies.FieldAccessPolicy
    from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions

    return FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy


def _require_text(value: str, argument: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TgiError(f"{argument} must be a non-empty string", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _require_bool(value: bool, argument: str) -> bool:
    if type(value) is not bool:
        raise TgiError(f"{argument} must be a boolean", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _enum_value(enum_type: type[Enum], value: Any, argument: str) -> Enum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as error:
        allowed = ", ".join(member.value for member in enum_type)
        raise TgiError(f"{argument} must be one of: {allowed}", TgiFaultCode.INVALID_ARGUMENT) from error


def _set_optional(parent: Any, attr: str, replacement: Any, preserve: tuple[str, ...] = ()) -> None:
    """Update an existing optional wrapper in place or attach a new wrapper."""
    old = getattr(parent, attr, None)
    if old is not None and type(old) is type(replacement):
        if is_dataclass(old):
            for model_field in fields(old):
                if model_field.name not in preserve and model_field.name not in {
                    "id",
                    "other_attributes",
                    "vendor_extensions",
                }:
                    setattr(old, model_field.name, getattr(replacement, model_field.name))
        else:
            raise TgiError(f"Cannot update generated wrapper for {attr}", TgiFaultCode.INVALID_ARGUMENT)
        register_parent(old, parent, (attr,), "single")
        return
    if old is not None:
        old_handle = get_handle(old)
        if get_parent_info(old_handle) is None:
            register_parent(old, parent, (attr,), "single")
        detach_child_by_handle(old_handle)
    setattr(parent, attr, replacement)
    register_parent(replacement, parent, (attr,), "single")


def _new_constraint(policy: Any, choice: Any) -> Any:
    from org.accellera.ipxact.v1685_2022.write_value_constraint import WriteValueConstraint

    constraint_type = _field_policy_choice_types()[5]
    constraint = _choice(policy, constraint_type)
    if constraint is None:
        constraint = WriteValueConstraint()
        _replace_choice(policy, constraint_type, constraint)
    _clear_constraint_choices(constraint, (type(choice),))
    _update_choice(constraint, type(choice), choice)
    return constraint


def _clear_constraint_choices(constraint: Any, keep_types: tuple[type, ...]) -> None:
    for child in list(getattr(constraint, "choice", ())):
        if isinstance(child, keep_types):
            continue
        handle = get_handle(child)
        if get_parent_info(handle) is None:
            register_parent(child, constraint, ("choice",), "list")
        if not detach_child_by_handle(handle):
            raise TgiError("Could not replace writeValueConstraint branch", TgiFaultCode.INVALID_ID)


def _set_constraint_min_max(constraint: Any, minimum: Any, maximum: Any) -> None:
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    _clear_constraint_choices(constraint, (WriteValueConstraintType.Minimum, WriteValueConstraintType.Maximum))
    minimum_model = _update_choice(constraint, WriteValueConstraintType.Minimum, minimum)
    maximum_model = _update_choice(constraint, WriteValueConstraintType.Maximum, maximum)
    for child in list(constraint.choice):
        if child is not minimum_model and child is not maximum_model:
            handle = get_handle(child)
            if get_parent_info(handle) is None:
                register_parent(child, constraint, ("choice",), "list")
            detach_child_by_handle(handle)
    constraint.choice[:] = [minimum_model, maximum_model]


def _set_inline_policy_choice(policy: Any, model_type: type, replacement: Any) -> None:
    """Set an inline field policy value, removing an incompatible definitionRef."""
    ref_type = _field_policy_choice_types()[1]
    _replace_choice(policy, ref_type, None)
    _replace_choice(policy, model_type, replacement)


def _update_choice(parent: Any, model_type: type, replacement: Any) -> Any:
    """Update an existing choice wrapper in place, preserving its handle and metadata."""
    old = _choice(parent, model_type)
    if old is None:
        parent.choice.insert(_choice_insert_index(parent, replacement), replacement)
        register_parent(replacement, parent, ("choice",), "list")
        return replacement
    for model_field in fields(old):
        if model_field.name not in {"id", "other_attributes", "vendor_extensions"}:
            setattr(old, model_field.name, getattr(replacement, model_field.name))
    register_parent(old, parent, ("choice",), "list")
    return old


def _choice_insert_index(parent: Any, replacement: Any) -> int:
    if _is_inline_field_policy(parent):
        ordered_types = _field_policy_choice_types()
        ordered = (ordered_types[0], ordered_types[2], ordered_types[5], ordered_types[3], ordered_types[4])
    elif type(parent).__name__ == "WriteValueConstraint":
        from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

        ordered = (
            WriteValueConstraintType.WriteAsRead,
            WriteValueConstraintType.UseEnumeratedValues,
            WriteValueConstraintType.Minimum,
            WriteValueConstraintType.Maximum,
        )
    else:
        return len(parent.choice)
    rank = {model_type: index for index, model_type in enumerate(ordered)}
    replacement_rank = rank.get(type(replacement))
    if replacement_rank is None:
        return len(parent.choice)
    return next(
        (index for index, child in enumerate(parent.choice) if rank.get(type(child), len(rank)) > replacement_rank),
        len(parent.choice),
    )


def _remove_child(handle: str, expected: type, label: str) -> bool:
    child = resolve_handle(handle)
    if child is None or not isinstance(child, expected):
        raise TgiError(f"Invalid {label} handle", TgiFaultCode.INVALID_ID)
    _owning_root(child)
    if not detach_child_by_handle(handle):
        raise TgiError(f"{label} handle has no registered parent", TgiFaultCode.INVALID_ID)
    return True


def _clear_optional(parent: Any, attr: str) -> bool:
    old = getattr(parent, attr, None)
    if old is None:
        return False
    old_handle = get_handle(old)
    if get_parent_info(old_handle) is None:
        register_parent(old, parent, (attr,), "single")
    if not detach_child_by_handle(old_handle):
        raise TgiError(f"Could not remove {attr}", TgiFaultCode.INVALID_ID)
    return True


def _first[T](it: Sequence[T], pred: Callable[[T], bool]) -> T | None:
    for x in it:
        if pred(x):
            return x
    return None


# ---------------------------------------------------------------------------
# FieldAccessPolicyDefinition getters (subset of F.7.9 grouping)
# ---------------------------------------------------------------------------
def getFieldAccessPolicyDefinitionIDs(fieldAccessPolicyDefinitionsID: str) -> list[str]:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        fieldAccessPolicyDefinitionsID (str): Handle to fieldAccessPolicyDefinitions.

    Returns:
        IDs (list[Any]): Handles of locally declared fieldAccessPolicyDefinition elements.
    """
    return _ids(_definition_container_to_defs(fieldAccessPolicyDefinitionsID))


def _get_definition(definitionID: str) -> Any:
    obj = resolve_handle(definitionID)
    if not _is_definition(obj):
        raise TgiError("Invalid FieldAccessPolicyDefinition handle", TgiFaultCode.INVALID_ID)
    return obj


def getFieldAccessPolicyDefinitionName(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        Name (str | None): Definition name, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "name")


def getFieldAccessPolicyDefinitionDisplayName(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        DisplayName (str | None): Display name text, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "display_name")


def getFieldAccessPolicyDefinitionShortDescription(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        ShortDescription (str | None): Short description text, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "short_description")


def getFieldAccessPolicyDefinitionDescription(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        Description (str | None): Description text, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "description")


def getFieldAccessPolicyDefinitionAccess(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        Access (str | None): Access enum text, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "access")


def getFieldAccessPolicyDefinitionModifiedWriteValue(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        ModifiedWriteValue (str | None): Modified write value enum text, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "modified_write_value")


def getFieldAccessPolicyDefinitionWriteValueConstraint(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        WriteValueConstraint (str | None): WriteValueConstraint handle, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "write_value_constraint")


def getFieldAccessPolicyDefinitionReadAction(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        ReadAction (str | None): Read action enum text, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "read_action")


def getFieldAccessPolicyDefinitionReadResponse(definitionID: str) -> str | None:
    """Project extension: inspect a local fieldAccessPolicyDefinition; this operation is outside Annex F.

    Section: Project extension outside IEEE 1685-2022 Annex F.

    Args:
        definitionID (str): Handle to fieldAccessPolicyDefinition.

    Returns:
        ReadResponse (str | None): Raw readResponse expression text, or None if absent.
    """
    return _scalar(_get_definition(definitionID), "read_response")


# ---------------------------------------------------------------------------
# F.7.6 legacy compatibility
# ---------------------------------------------------------------------------
def getFieldAccessPolicyModeRefByID(fieldAccessPolicyID: str, modeRef: str) -> str | None:  # F.7.6.1
    """Section: F.7.6.1

    Description:
        Returns the modeID defined on the given field access policy element.

    Args:
        fieldAccessPolicyID (str): Handle to an field access policy element
        modeRef (str): Handle to the referenced modeRef element

    Returns:
        modeID (str | None): Handle to the referenced mode element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    ref = resolve_handle(modeRef)
    if ref is None or not any(ref is item for item in getattr(pol, "mode_ref", ())):
        raise TgiError("Invalid modeRef handle for fieldAccessPolicy", TgiFaultCode.INVALID_ID)
    _child_handle(ref, pol, ("mode_ref",), "list")
    mode = _referenced_mode(pol, getattr(ref, "value", None))
    return get_handle(mode) if mode is not None else None


# ---------------------------------------------------------------------------
# F.7.9 BASE AccessPolicy and related getters (full coverage)
# ---------------------------------------------------------------------------
def getAccessPolicyAccess(accessPolicyID: str) -> str | None:  # F.7.9.1
    """Section: F.7.9.1

    Description:
        Returns the access defined on the given accessPolicy element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element

    Returns:
        access (str | None): The access value
    """
    return _scalar(_get_access_policy(accessPolicyID), "access")


def getAccessPolicyModeRefByID(accessPolicyID: str, modeRef: str) -> str | None:  # F.7.9.2
    """Section: F.7.9.2

    Description:
        Returns the handle to the referenced mode defined on the given accessPolicy element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element
        modeRef (str): The referenced mode

    Returns:
        modeID (str | None): Handle to the referenced mode element
    """
    ap = _get_access_policy(accessPolicyID)
    m = _first(getattr(ap, "mode_ref", []), lambda r: getattr(r, "value", None) == modeRef)
    if m is None:
        return None
    _child_handle(m, ap, ("mode_ref",), "list")
    target = _referenced_mode(ap, modeRef)
    return get_handle(target) if target is not None else None


def getAccessPolicyModeRefByNames(accessPolicyID: str) -> list[str]:  # F.7.9.3
    """Section: F.7.9.3

    Description:
        Returns all the modeRef names defined on the accessPolicy element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element

    Returns:
        modeRef (list[Any]): List of the modeRef names
    """
    ap = _get_access_policy(accessPolicyID)
    return [getattr(r, "value", "") for r in getattr(ap, "mode_ref", [])]


def getAccessPolicyModeRefIDs(accessPolicyID: str) -> list[str]:  # F.7.9.4
    """Section: F.7.9.4

    Description:
        Returns the handles to all the modeRef idefined on the given accessPolicy element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element

    Returns:
        modeRefIDs (list[Any]): List of handles to the modeRef elements
    """
    ap = _get_access_policy(accessPolicyID)
    return _ids(getattr(ap, "mode_ref", []), ap, ("mode_ref",))


def getAccessRestrictionModeRefIDs(accessRestrictionID: str) -> list[str]:  # F.7.9.5
    """Section: F.7.9.5

    Description:
        Returns the handles to all the modeRefs defined on the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        modeRefIDs (list[Any]): List of handles to the modeRef elements
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    return _ids(getattr(ar, "mode_ref", []), ar, ("mode_ref",))


def getAccessRestrictionModeRefbyID(accessRestrictionID: str, modeRef: str) -> str | None:  # F.7.9.6
    """Section: F.7.9.6

    Description:
        Returns the modeID defined on the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element
        modeRef (str): Handle to the referenced modeRef element

    Returns:
        modeID (str | None): Handle to the referenced mode element
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    m = resolve_handle(modeRef)
    if m is None or not any(m is item for item in getattr(ar, "mode_ref", ())):
        raise TgiError("Invalid modeRef handle for accessRestriction", TgiFaultCode.INVALID_ID)
    _child_handle(m, ar, ("mode_ref",), "list")
    target = _referenced_mode(ar, getattr(m, "value", None))
    return get_handle(target) if target is not None else None


def getAccessRestrictionModeRefbyNames(accessRestrictionID: str) -> list[str]:  # F.7.9.7
    """Section: F.7.9.7

    Description:
        Returns all the modeRef defined on the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        modeRef (list[Any]): The list of all the modeRef values
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    return [getattr(r, "value", "") for r in getattr(ar, "mode_ref", [])]


def getAccessRestrictionReadAccessMask(accessRestrictionID: str) -> Numeric | None:  # F.7.9.8
    """Section: F.7.9.8

    Description:
        Returns the readAccessMask value defined on the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        readAccessMask (Numeric | None): The readAccessMask value. Returns None if absent or not evaluable as a
            self-contained integer.
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    m = getattr(ar, "read_access_mask", None)
    return _evaluated_numeric(m)


def getAccessRestrictionReadAccessMaskExpression(accessRestrictionID: str) -> str | None:  # F.7.9.9
    """Section: F.7.9.9

    Description:
        Returns the readAccessMask expression defined on the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        readAccessMask (str | None): The readAccessMask expression Preserves the raw expression text.
    """
    return _expression(_get_access_restriction_handle(accessRestrictionID).read_access_mask)


def getAccessRestrictionReadAccessMaskID(accessRestrictionID: str) -> str | None:  # F.7.9.10
    """Section: F.7.9.10

    Description:
        Returns the handle to the readAccessMask defined on the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        readAccessMaskID (str | None): Handle to the readAccessMask element
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    m = getattr(ar, "read_access_mask", None)
    return _child_handle(m, ar, ("read_access_mask",)) if m is not None else None


def getAccessRestrictionWriteAccessMask(accessRestrictionID: str) -> Numeric | None:  # F.7.9.11
    """Section: F.7.9.11

    Description:
        Returns the writeAccessMask value defined on the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        writeAccessMask (Numeric | None): The writeAccessMask value. Returns None if absent or not evaluable as a
            self-contained integer.
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    m = getattr(ar, "write_access_mask", None)
    return _evaluated_numeric(m)


def getAccessRestrictionWriteAccessMaskExpression(accessRestrictionID: str) -> str | None:  # F.7.9.12
    """Section: F.7.9.12

    Description:
        Returns the writeAccessMask expression on an accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        writeAccessMask (str | None): The writeAccessMask expression Preserves the raw expression text.
    """
    return _expression(_get_access_restriction_handle(accessRestrictionID).write_access_mask)


def getAccessRestrictionWriteAccessMaskID(accessRestrictionID: str) -> str | None:  # F.7.9.13
    """Section: F.7.9.13

    Description:
        Returns the handle to the readAccessMask element defined on the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        writeAccessMaskID (str | None): Handle to the writeAccessMask element
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    m = getattr(ar, "write_access_mask", None)
    return _child_handle(m, ar, ("write_access_mask",)) if m is not None else None


def _collect_access_policies(parentID: str, attr_name: str) -> list[Any]:
    parent = resolve_handle(parentID)
    if parent is None:
        raise TgiError("Invalid parent handle", TgiFaultCode.INVALID_ID)
    if hasattr(parent, attr_name):
        cont = getattr(parent, attr_name, None)
        path, container_kind = (attr_name,), "single"
    else:
        from org.accellera.ipxact.v1685_2022.access_policies import AccessPolicies

        cont = _first(getattr(parent, "choice", ()), lambda child: isinstance(child, AccessPolicies))
        path, container_kind = ("choice",), "list"
    if cont is None:
        return []
    register_parent(cont, parent, path, container_kind)
    policies = list(getattr(cont, "access_policy", []))
    for policy in policies:
        register_parent(policy, cont, ("access_policy",), "list")
    return policies


def getAlternateRegisterAccessPolicyIDs(alternateRegisterID: str) -> list[str]:  # F.7.9.14
    """Section: F.7.9.14

    Description:
        Returns the handles to all the accessPolicies defined on the given alternateRegister element.

    Args:
        alternateRegisterID (str): Handle to an alternateRegister element

    Returns:
        accessPolicyID (list[Any]): List of handles to the accessPolicy elements
    """
    return _ids(_collect_access_policies(alternateRegisterID, "access_policies"))


def getBankAccessPoliciesIDs(bankID: str) -> list[str]:  # F.7.9.15
    """Section: F.7.9.15

    Description:
        Returns the handles to all the accessPolicies defined on the given bank element.

    Args:
        bankID (str): Handle to a bank element

    Returns:
        accessPoliciesIDs (list[Any]): List of handles to the accessPolicies elements
    """
    return _ids(_collect_access_policies(bankID, "access_policies"))


def getFieldAccessPoliciesFieldAccessPolicyIDs(fieldAccessPoliciesID: str) -> list[str]:  # F.7.9.16
    """Section: F.7.9.16

    Description:
        Returns the handles to all the fieldAccessPolicies defined on the given fieldAccessPolicies element

    Args:
        fieldAccessPoliciesID (str): Handle to a fieldAccessPolicies element

    Returns:
        fieldAccessPolicyIDs (list[Any]): List of handes to the fieldAccessPolicy elements
    """
    cont = resolve_handle(fieldAccessPoliciesID)
    if cont is None or not hasattr(cont, "field_access_policy"):
        raise TgiError("Invalid fieldAccessPolicies handle", TgiFaultCode.INVALID_ID)
    return _ids(getattr(cont, "field_access_policy", []))


def getFieldAccessPolicyAccess(fieldAccessPolicyID: str) -> str | None:  # F.7.9.17
    """Section: F.7.9.17

    Description:
        Returns the access defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        access (str | None): The access value
    """
    from org.accellera.ipxact.v1685_2022.access import Access

    return _scalar(_choice(_get_inline_field_policy(fieldAccessPolicyID), Access), "value")


def getFieldAccessPolicyAccessRestrictionIDs(fieldAccessPolicyID: str) -> list[str]:  # F.7.9.18
    """Section: F.7.9.18

    Description:
        Returns the handles to all the accessRestrictions defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        accessRestrictionIDs (list[Any]): List of handles to the accessRestriction elements
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    container = getattr(pol, "access_restrictions", None)
    if container is None:
        return []
    register_parent(container, pol, ("access_restrictions",), "single")
    return _ids(_get_access_restrictions(pol), container, ("access_restriction",))


def getFieldAccessPolicyFieldAccessPolicyDefinitionRefByExternalTypeDefID(
    fieldAccessPolicyID: str,
) -> str | None:  # F.7.9.19
    """Section: F.7.9.19

    Description:
        Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute of the
        fieldAccessPolicyDefinitionRef defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        fieldAccesspolicyDefinitionRefID (str | None): Handle to the externalTypeDefinitions element referenced by the
            typeDefinitions attribute.
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    ref = _choice(pol, _field_policy_choice_types()[1])
    if ref is None:
        return None
    owner = _owning_root(pol)
    external = _external_type_definition(owner, getattr(ref, "type_definitions", ""))
    if external is None:
        return None
    definitions = _owner_type_definitions(owner)
    register_parent(external, definitions, ("external_type_definitions",), "list")
    return get_handle(external)


def getFieldAccessPolicyFieldAccessPolicyDefinitionRefByID(fieldAccessPolicyID: str) -> str | None:  # F.7.9.20
    """Section: F.7.9.20

    Description:
        Returns the handle to the fieldAccesspolicyDefinition referenced from the given

    Args:
        fieldAccessPolicyID (str): Handle a fieldAccessPolicy element

    Returns:
        fieldAccesspolicyDefinitionRefID (str | None): Handle to the referenced fieldAccesspolicyDefinition element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    ref = _choice(pol, _field_policy_choice_types()[1])
    if ref is None:
        return None
    owner = _owning_root(pol)
    external = _external_type_definition(owner, getattr(ref, "type_definitions", ""))
    target_definitions = _referenced_type_definitions(external) if external is not None else None
    definitions = getattr(target_definitions, "field_access_policy_definitions", None)
    if definitions is None:
        return None
    matches = [item for item in definitions.field_access_policy_definition if item.name == ref.value]
    if len(matches) > 1:
        raise TgiError("Ambiguous fieldAccessPolicyDefinition reference", TgiFaultCode.INVALID_ARGUMENT)
    if not matches:
        return None
    register_parent(definitions, target_definitions, ("field_access_policy_definitions",), "single")
    register_parent(matches[0], definitions, ("field_access_policy_definition",), "list")
    return get_handle(matches[0])


def getFieldAccessPolicyFieldAccessPolicyDefinitionRefByName(fieldAccessPolicyID: str) -> str | None:  # F.7.9.21
    """Section: F.7.9.21

    Description:
        Returns the fieldAccessPolicyDefinition defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        fieldAccesspolicyDefinition (str | None): The fieldAccesspolicyDefinition name
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    ref = _choice(pol, _field_policy_choice_types()[1])
    return getattr(ref, "value", None) if ref is not None else None


def getFieldAccessPolicyFieldAccessPolicyDefinitionRefID(fieldAccessPolicyID: str) -> str | None:  # F.7.9.22
    """Section: F.7.9.22

    Description:
        Returns the handle to the fieldAccesspolicyDefinitionRef defined on the given fieldAccessPolicy
        element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        fieldAccesspolicyDefinitionRefID (str | None): Handle to the fieldAccesspolicyDefinitionRef element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return _choice_handle(pol, _field_policy_choice_types()[1])


def getFieldAccessPolicyModeRefByName(fieldAccessPolicyID: str) -> list[str]:  # F.7.9.23
    """Section: F.7.9.23

    Description:
        Returns all the modeRefs defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        modeRefs (list[Any]): List of the referenced modes
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return [getattr(r, "value", "") for r in getattr(pol, "mode_ref", [])]


def getFieldAccessPolicyModeRefIDs(fieldAccessPolicyID: str) -> list[str]:  # F.7.9.24
    """Section: F.7.9.24

    Description:
        Returns the handles to all the modeRefs defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy

    Returns:
        modeRefIDs (list[Any]): List of handles to the modeRef elements
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return _ids(getattr(pol, "mode_ref", []), pol, ("mode_ref",))


def getFieldAccessPolicyModifiedWriteValue(fieldAccessPolicyID: str) -> str | None:  # F.7.9.25
    """Section: F.7.9.25

    Description:
        Returns the modifiedWriteValue defined on the given accessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element.

    Returns:
        modifiedWriteValue (str | None): The value of the modifiedWriteValue element
    """
    return _scalar(_choice(_get_inline_field_policy(fieldAccessPolicyID), _field_policy_choice_types()[2]), "value")


def getFieldAccessPolicyModifiedWriteValueID(fieldAccessPolicyID: str) -> str | None:  # F.7.9.26
    """Section: F.7.9.26

    Description:
        Returns the handle to the modifiedWriteValue defined on the given fieldAccesspolicy.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        modifiedWriteValueID (str | None): Handle to the modifiedWriteValue element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return _choice_handle(pol, _field_policy_choice_types()[2])


def getFieldAccessPolicyReadAction(fieldAccessPolicyID: str) -> str | None:  # F.7.9.27
    """Section: F.7.9.27

    Description:
        Returns the readAction on a fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        readAction (str | None): The readAction value
    """
    return _scalar(_choice(_get_inline_field_policy(fieldAccessPolicyID), _field_policy_choice_types()[3]), "value")


def getFieldAccessPolicyReadActionID(fieldAccessPolicyID: str) -> str | None:  # F.7.9.28
    """Section: F.7.9.28

    Description:
        Returns the handle to the readAction defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        readActionID (str | None): Handle to the readAction element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return _choice_handle(pol, _field_policy_choice_types()[3])


def getFieldAccessPolicyReadResponse(fieldAccessPolicyID: str) -> Numeric | None:  # F.7.9.29
    """Section: F.7.9.29

    Description:
        Returns the readResponse value defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        readResponse (Numeric | None): The readResponse value. Returns None if absent or not evaluable as a
            self-contained integer.
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    rr = _choice(pol, _field_policy_choice_types()[4])
    return _evaluated_numeric(rr)


def getFieldAccessPolicyReadResponseExpression(fieldAccessPolicyID: str) -> str | None:  # F.7.9.30
    """Section: F.7.9.30

    Description:
        Returns the readResponse expression defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        readResponse (str | None): The readResponse expression value Preserves the raw expression text.
    """
    return _expression(_choice(_get_inline_field_policy(fieldAccessPolicyID), _field_policy_choice_types()[4]))


def getFieldAccessPolicyReadResponseID(fieldAccessPolicyID: str) -> str | None:  # F.7.9.31
    """Section: F.7.9.31

    Description:
        Returns the handle to the readResponse element defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        readResponseID (str | None): Handle to the readResponse element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return _choice_handle(pol, _field_policy_choice_types()[4])


def getFieldAccessPolicyReserved(fieldAccessPolicyID: str) -> bool | None:  # F.7.9.32
    """Section: F.7.9.32

    Description:
        Returns the reserved value on the fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        value (bool | None): The reserved value on the fieldAccessPolicy element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    r = getattr(pol, "reserved", None)
    value = _evaluated_numeric(r)
    return None if value is None else bool(value)


def getFieldAccessPolicyReservedExpression(fieldAccessPolicyID: str) -> str | None:  # F.7.9.33
    """Section: F.7.9.33

    Description:
        Returns the reserved expression on the fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        reserved (str | None): The reserved expression on the fieldAccessPolicy element. Preserves the raw expression
            text.
    """
    return _expression(getattr(_get_inline_field_policy(fieldAccessPolicyID), "reserved", None))


def getFieldAccessPolicyReservedID(fieldAccessPolicyID: str) -> str | None:  # F.7.9.34
    """Section: F.7.9.34

    Description:
        Returns the handle to the reserved element defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        reservedID (str | None): Handle to the reserved element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    r = getattr(pol, "reserved", None)
    return _child_handle(r, pol, ("reserved",)) if r is not None else None


def getFieldAccessPolicyTestable(fieldAccessPolicyID: str) -> bool | None:  # F.7.9.35
    """Section: F.7.9.35

    Description:
        Returns the testable value on the fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        value (bool | None): The testable value
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    t = getattr(pol, "testable", None)
    return getattr(t, "value", None) if t is not None else None


def getFieldAccessPolicyTestableID(fieldAccessPolicyID: str) -> str | None:  # F.7.9.36
    """Section: F.7.9.36

    Description:
        Returns the handle to the testable element defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        testableID (str | None): Handle to the testable element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    t = getattr(pol, "testable", None)
    return get_handle(t) if t is not None else None


def getFieldAccessPolicyWriteValueConstraintID(fieldAccessPolicyID: str) -> str | None:  # F.7.9.37
    """Section: F.7.9.37

    Description:
        Returns the handle to the writeValueConstraint defined on the given fieldAccesspolicy.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        writeValueConstraintID (str | None): Handle to the writeValueConstraint element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return _choice_handle(pol, _field_policy_choice_types()[5])


def getFieldAccesspolicyBroadcastToIDs(fieldAccessPolicyID: str) -> list[str]:  # F.7.9.38
    """Section: F.7.9.38

    Description:
        Returns the handles to all the broadcastTo elements defined on the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        broadcastToIDs (list[Any]): Handles to the list of broadcastTo elements
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    b = getattr(pol, "broadcasts", None)
    if b is None:
        return []
    register_parent(b, pol, ("broadcasts",), "single")
    return _ids(getattr(b, "broadcast_to", []), b, ("broadcast_to",))


def getRegisterAccessPolicyIDs(registerID: str) -> list[str]:  # F.7.9.39
    """Section: F.7.9.39

    Description:
        Returns the handles to all the accessPolicies defined on the given register element.

    Args:
        registerID (str): Handle to a register element

    Returns:
        accessPoliciesIDs (list[Any]): List of handles to the accessPolicies elements
    """
    return _ids(_collect_access_policies(registerID, "access_policies"))


def getRegisterFieldFieldAccessPoliciesID(registerFieldID: str) -> str | None:  # F.7.9.40
    """Section: F.7.9.40

    Description:
        Returns the handle to the fieldAccessPolicies defined on the given registerField element.

    Args:
        registerFieldID (str): Handle to a register field element

    Returns:
        fieldAccessPoliciesID (str | None): Handle to the fieldAccessPolicies element
    """
    f = resolve_handle(registerFieldID)
    if f is None:
        raise TgiError("Invalid registerField handle", TgiFaultCode.INVALID_ID)
    cont = getattr(f, "field_access_policies", None)
    return _child_handle(cont, f, ("field_access_policies",)) if cont is not None else None


def getTypeDefinitionsFieldAccessPolicyDefinitionIDs(typeDefinitionsID: str) -> list[str]:  # F.7.9.41
    """Section: F.7.9.41

    Description:
        Returns the handles to all the fieldAccessPolicyDefinitions defined on the given typeDefinitions
        element.

    Args:
        typeDefinitionsID (str): Handle to a typeDefinitions element

    Returns:
        fieldAccessPolicyDefinitionIDs (list[Any]): List of handles to the fieldAccessPolicyDefinitionID elements
    """
    td = resolve_handle(typeDefinitionsID)
    if td is None or not hasattr(td, "field_access_policy_definitions"):
        raise TgiError("Invalid typeDefinitions handle", TgiFaultCode.INVALID_ID)
    defs = getattr(td, "field_access_policy_definitions", None)
    if defs is None:
        return []
    register_parent(defs, td, ("field_access_policy_definitions",), "single")
    return _ids(getattr(defs, "field_access_policy_definition", []), defs, ("field_access_policy_definition",))


def getWriteValueConstraintMaximum(writeValueConstraintID: str) -> Numeric | None:  # F.7.9.42
    """Section: F.7.9.42

    Description:
        Returns the maximum value defined on the given writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element

    Returns:
        maximum (Numeric | None): The maximum value Returns None if absent or not evaluable as a self-contained integer.
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    m = _first(w.choice, lambda item: isinstance(item, WriteValueConstraintType.Maximum))
    return _evaluated_numeric(m)


def getWriteValueConstraintMaximumExpression(writeValueConstraintID: str) -> str | None:  # F.7.9.43
    """Section: F.7.9.43

    Description:
        Returns the maximum expression defined on the given writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element

    Returns:
        maximum (str | None): The maximum expression value Preserves the raw expression text.
    """
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    w = _get_write_value_constraint_handle(writeValueConstraintID)
    m = _first(w.choice, lambda item: isinstance(item, WriteValueConstraintType.Maximum))
    return _expression(m)


def getWriteValueConstraintMaximumID(writeValueConstraintID: str) -> str | None:  # F.7.9.44
    """Section: F.7.9.44

    Description:
        Returns the handle to the maximum element defined on the given writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element

    Returns:
        maximumID (str | None): Handle to the maximum element
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    m = _first(w.choice, lambda item: isinstance(item, WriteValueConstraintType.Maximum))
    return _child_handle(m, w, ("choice",), "list") if m is not None else None


def getWriteValueConstraintMinimum(writeValueConstraintID: str) -> Numeric | None:  # F.7.9.45
    """Section: F.7.9.45

    Description:
        Returns the minimum value defined on the given writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element

    Returns:
        minimum (Numeric | None): The minimum value Returns None if absent or not evaluable as a self-contained integer.
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    m = _first(w.choice, lambda item: isinstance(item, WriteValueConstraintType.Minimum))
    return _evaluated_numeric(m)


def getWriteValueConstraintMinimumExpression(writeValueConstraintID: str) -> str | None:  # F.7.9.46
    """Section: F.7.9.46

    Description:
        Returns the minimum expression defined on the given writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element

    Returns:
        minimum (str | None): The minimum expression value Preserves the raw expression text.
    """
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    w = _get_write_value_constraint_handle(writeValueConstraintID)
    m = _first(w.choice, lambda item: isinstance(item, WriteValueConstraintType.Minimum))
    return _expression(m)


def getWriteValueConstraintMinimumID(writeValueConstraintID: str) -> str | None:  # F.7.9.47
    """Section: F.7.9.47

    Description:
        Returns the handle to the minimum element defined on the given writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element

    Returns:
        minimumID (str | None): Handle to the minimum element
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    m = _first(w.choice, lambda item: isinstance(item, WriteValueConstraintType.Minimum))
    return _child_handle(m, w, ("choice",), "list") if m is not None else None


def getWriteValueConstraintUseEnumeratedValues(writeValueConstraintID: str) -> bool | None:  # F.7.9.48
    """Section: F.7.9.48

    Description:
        Returns the UseEnumeratedValues field on a writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element

    Returns:
        value (bool | None): The UseEnumeratedValues value
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    item = _first(w.choice, lambda item: isinstance(item, WriteValueConstraintType.UseEnumeratedValues))
    return getattr(item, "value", None) if item is not None else None


def getWriteValueConstraintWriteAsRead(writeValueConstraintID: str) -> bool | None:  # F.7.9.49
    """Section: F.7.9.49

    Description:
        Returns the writeAsRead value defined on the given writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element

    Returns:
        value (bool | None): The writeAsRead value
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    item = _first(w.choice, lambda item: isinstance(item, WriteValueConstraintType.WriteAsRead))
    return getattr(item, "value", None) if item is not None else None


# ---------------------------------------------------------------------------
# F.7.10 EXTENDED – add/remove/set operations
# ---------------------------------------------------------------------------
def _append_and_register(parent: object, list_attr: str, child: object, path: tuple[str, ...]) -> str:
    lst = getattr(parent, list_attr)
    lst.append(child)
    register_parent(child, parent, path, "list")
    return get_handle(child)


def _mode_ref_priority(mode_refs: Sequence[Any], mode_ref: str, priority: int | None) -> int:
    _require_text(mode_ref, "modeRef")
    if any(getattr(item, "value", None) == mode_ref for item in mode_refs):
        raise TgiError(f"modeRef {mode_ref!r} already exists in this element", TgiFaultCode.INVALID_ARGUMENT)
    used = {getattr(item, "priority", None) for item in mode_refs}
    if priority is None:
        priority = 0
        while priority in used:
            priority += 1
    elif type(priority) is not int or priority < 0:
        raise TgiError("priority must be a non-negative integer or None", TgiFaultCode.INVALID_ARGUMENT)
    if priority in used:
        raise TgiError(f"modeRef priority {priority} already exists in this element", TgiFaultCode.INVALID_ARGUMENT)
    return priority


def addAccessRestrictionModeRef(accessRestrictionID: str, modeRef: str, priority: int | None = None) -> str:  # F.7.10.1
    """Section: F.7.10.1

    Description:
        Adds a modeRef to the given accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element
        modeRef (str): Name of the referenced mode
        priority (int | None): Optional non-negative priority; omitted values use the next available priority.

    Returns:
        modeRefID (str): the modeRef identifier
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef

    priority = _mode_ref_priority(ar.mode_ref, modeRef, priority)
    mr = ModeRef(value=modeRef, priority=priority)
    ar.mode_ref.append(mr)  # type: ignore[attr-defined]
    register_parent(mr, ar, ("mode_ref",), "list")
    return get_handle(mr)


def _ensure_access_policies(parent: Any) -> AccessPolicies:
    if hasattr(parent, "access_policies"):
        if parent.access_policies is None:
            parent.access_policies = AccessPolicies()  # type: ignore[attr-defined]
        container = parent.access_policies
        register_parent(container, parent, ("access_policies",), "single")
        return container
    container = _first(getattr(parent, "choice", ()), lambda item: isinstance(item, AccessPolicies))
    if container is None:
        container = AccessPolicies()
        choice = parent.choice
        module_name = type(parent).__module__.rsplit(".", 1)[-1]
        class_name = type(parent).__name__
        boundaries = set()
        if module_name == "address_block":
            boundaries = {"Register", "RegisterFile", "Bank", "Parameters"}
        elif module_name == "address_block_type" and class_name == "Register":
            boundaries = {"FieldType"}
        elif module_name == "register_file":
            boundaries = {"Register", "RegisterFile"}
        insert_at = next(
            (
                index
                for index, item in enumerate(choice)
                if type(item).__name__ in boundaries
                or (type(item).__module__.rsplit(".", 1)[-1] == "address_block_type" and "Register" in boundaries)
                or (type(item).__module__.rsplit(".", 1)[-1] == "register_file" and "RegisterFile" in boundaries)
            ),
            len(choice),
        )
        choice.insert(insert_at, container)
    register_parent(container, parent, ("choice",), "list")
    return container


def _new_access_policy() -> Any:
    from org.accellera.ipxact.v1685_2022.access_policies import AccessPolicies

    return AccessPolicies.AccessPolicy()


def addAddressBlockAccessPolicy(addressBlockID: str) -> str:  # F.7.10.2
    """Section: F.7.10.2

    Description:
        Adds an accessPolicy element on the addressBlock.

    Args:
        addressBlockID (str): Handle to an addressblock

    Returns:
        accessPolicyID (str): Handle to the added accessPolicy
    """
    blk = _resolve_parent(addressBlockID, ("access_policies",), "addressBlock")
    container = _ensure_access_policies(blk)
    ap = _new_access_policy()
    return _append_and_register(container, "access_policy", ap, ("access_policy",))


def addAlternateRegisterAccessPolicy(registerID: str) -> str:  # F.7.10.3
    """Section: F.7.10.3

    Description:
        Adds accessPolicy for the given alternateRegister.

    Args:
        registerID (str): Handle to an alternate register

    Returns:
        accessPolicyID (str): Handle to the added accessPolicy
    """
    reg = _resolve_parent(registerID, ("access_policies",), "alternateRegister")
    container = _ensure_access_policies(reg)
    ap = _new_access_policy()
    return _append_and_register(container, "access_policy", ap, ("access_policy",))


def addExternalTypeDefinitionsResetTypeLink(
    externalTypeDefinitionsID: str,
    externalResetTypeReference: str,
    resetTypeReference: str,
) -> str:  # F.7.10.4
    """Section: F.7.10.4

    Description:
        Adds a resetTypeLink to an externalTypeDefinitions.

    Args:
        externalTypeDefinitionsID (str): Handle to an externalTypeDefinitions
        externalResetTypeReference (str): Handle to the externalResetTypeReference to set on the resetTypeLink
        resetTypeReference (str): Handle to the resetTypeReference to set on the resetTypeLink

    Returns:
        resetTypeLinkID (str): The identifier of the added resetTypeLink
    """
    external = _resolve_parent(externalTypeDefinitionsID, ("reset_type_links",), "externalTypeDefinitions")
    external_ref = resolve_handle(externalResetTypeReference)
    reset_ref = resolve_handle(resetTypeReference)
    if (
        external_ref is None
        or reset_ref is None
        or type(external_ref).__module__.rsplit(".", 1)[-1] != "reset_type_links"
        or type(external_ref).__name__ != "ExternalResetTypeReference"
        or type(reset_ref).__module__.rsplit(".", 1)[-1] != "reset_type_links"
        or type(reset_ref).__name__ != "ResetTypeReference"
    ):
        raise TgiError("Invalid reset type reference handle", TgiFaultCode.INVALID_ID)
    external_name = getattr(external_ref, "reset_type_ref", None)
    reset_name = getattr(reset_ref, "reset_type_ref", None)
    _require_text(external_name, "externalResetTypeReference")
    _require_text(reset_name, "resetTypeReference")
    from org.accellera.ipxact.v1685_2022.reset_type_links import ResetTypeLinks

    if external.reset_type_links is None:
        external.reset_type_links = ResetTypeLinks()  # type: ignore[attr-defined]
        register_parent(external.reset_type_links, external, ("reset_type_links",), "single")
    model = ResetTypeLinks.ResetTypeLink(
        external_reset_type_reference=ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference(
            reset_type_ref=external_name
        ),
        reset_type_reference=ResetTypeLinks.ResetTypeLink.ResetTypeReference(reset_type_ref=reset_name),
    )
    return _append_and_register(external.reset_type_links, "reset_type_link", model, ("reset_type_link",))


def addFieldAccessPoliciesFieldAccessPolicy(fieldAccessPoliciesID: str) -> str:  # F.7.10.5
    """Section: F.7.10.5

    Description:
        Adds an fieldAccessPolicy on the given fieldAccessPolicies element

    Args:
        fieldAccessPoliciesID (str): Handle to a fieldAccessPolicies element

    Returns:
        fieldAccessPolicyID (str): the fieldAccessPolicy identifier
    """
    cont = resolve_handle(fieldAccessPoliciesID)
    if cont is None or not hasattr(cont, "field_access_policy"):
        raise TgiError("Invalid fieldAccessPolicies handle", TgiFaultCode.INVALID_ID)
    from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions

    pol = FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy()
    cont.field_access_policy.append(pol)  # type: ignore[attr-defined]
    register_parent(pol, cont, ("field_access_policy",), "list")
    return get_handle(pol)


def addFieldAccessPolicyAccessRestriction(fieldAccessPolicyID: str) -> str:  # F.7.10.6
    """Section: F.7.10.6

    Description:
        Adds an accessRestriction to a fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        accessRestrictionID (str): the accessRestriction identifier
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.access_restriction_type import AccessRestrictionType
    from org.accellera.ipxact.v1685_2022.access_restrictions import AccessRestrictions

    if pol.access_restrictions is None:  # type: ignore[attr-defined]
        pol.access_restrictions = AccessRestrictions()  # type: ignore[attr-defined]
    ar = AccessRestrictionType()
    pol.access_restrictions.access_restriction.append(ar)  # type: ignore[attr-defined]
    register_parent(ar, pol.access_restrictions, ("access_restrictions", "access_restriction"), "list")
    return get_handle(ar)


def addFieldAccessPolicyBroadcastTo(
    fieldAccessPolicyID: str,
    memoryMapRef: str | None = None,
    addressBlockRef: str | None = None,
    registerRef: str | None = None,
    fieldRef: str | None = None,
) -> str:  # F.7.10.7
    """Section: F.7.10.7

    Description:
        Adds a broadcast to the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        memoryMapRef (str | None): Name of the broadcasted memoryMap
        addressBlockRef (str | None): Name of the broadcasted addressBlock
        registerRef (str | None): Name of the broadcasted register
        fieldRef (str | None): Name of the broadcasted field

    Returns:
        broadcastToID (str): Handle of the broadcastTo element
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    _require_text(fieldRef, "fieldRef")
    from org.accellera.ipxact.v1685_2022.address_block_ref import AddressBlockRef
    from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
    from org.accellera.ipxact.v1685_2022.register_ref import RegisterRef

    policy_model = _field_policy_module(pol)
    if pol.broadcasts is None:  # type: ignore[attr-defined]
        pol.broadcasts = policy_model.Broadcasts()  # type: ignore[attr-defined]
    broadcast_to_type = policy_model.Broadcasts.BroadcastTo
    bt = broadcast_to_type(field_ref=FieldRef(field_ref=fieldRef))
    if memoryMapRef is not None:
        bt.address_space_ref_or_memory_map_ref_or_memory_remap_ref.append(
            broadcast_to_type.MemoryMapRef(memory_map_ref=memoryMapRef)
        )
    if addressBlockRef is not None:
        bt.address_block_ref = AddressBlockRef(address_block_ref=addressBlockRef)  # type: ignore[attr-defined]
    if registerRef is not None:
        bt.register_ref = RegisterRef(register_ref=registerRef)  # type: ignore[attr-defined]
    pol.broadcasts.broadcast_to.append(bt)  # type: ignore[attr-defined]
    register_parent(bt, pol.broadcasts, ("broadcasts", "broadcast_to"), "list")
    return get_handle(bt)


def addFieldAccessPolicyModeRef(fieldAccessPolicyID: str, modeRef: str, priority: int | None = None) -> str:  # F.7.10.8
    """Section: F.7.10.8

    Description:
        Adds a modeRef on the given fieldAccessPolicy.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        modeRef (str): Name of the referenced mode
        priority (int | None): Optional non-negative priority; omitted values use the next available priority.

    Returns:
        modeRefID (str): Handle to the added modeRef
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef

    priority = _mode_ref_priority(pol.mode_ref, modeRef, priority)
    mr = ModeRef(value=modeRef, priority=priority)
    pol.mode_ref.append(mr)  # type: ignore[attr-defined]
    register_parent(mr, pol, ("mode_ref",), "list")
    return get_handle(mr)


def addFieldDefinitionFieldAccessPolicy(fieldDefinitionID: str) -> str:  # F.7.10.9
    """Section: F.7.10.9

    Description:
        Adds an accessPolicy to the given fieldDefinition.

    Args:
        fieldDefinitionID (str): Handle to a fieldDefinition element

    Returns:
        fieldAccessPolicyID (str): Handle to the added AccessEntry
    """
    fd = resolve_handle(fieldDefinitionID)
    if fd is None:
        raise TgiError("Invalid fieldDefinition handle", TgiFaultCode.INVALID_ID)
    if getattr(fd, "field_access_policies", None) is None:
        from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions

        fd.field_access_policies = FieldDefinitions.FieldDefinition.FieldAccessPolicies()  # type: ignore[attr-defined]
    from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions

    pol = FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy()
    fd.field_access_policies.field_access_policy.append(pol)  # type: ignore[attr-defined]
    register_parent(pol, fd.field_access_policies, ("field_access_policies", "field_access_policy"), "list")
    return get_handle(pol)


def addRegisterAccessPolicy(registerID: str) -> str:  # F.7.10.10
    """Section: F.7.10.10

    Description:
        Adds accessPolicy on the given register element.

    Args:
        registerID (str): Handle to a register element

    Returns:
        accessPolicyID (str): Handle to the added accessPolicy
    """
    reg = resolve_handle(registerID)
    if reg is None:
        raise TgiError("Invalid register handle", TgiFaultCode.INVALID_ID)
    container = _ensure_access_policies(reg)
    ap = _new_access_policy()
    return _append_and_register(container, "access_policy", ap, ("access_policy",))


def addRegisterFileAccessPolicy(registerFileID: str) -> str:  # F.7.10.11
    """Section: F.7.10.11

    Description:
        Adds an accessPolicy on a registerFile element.

    Args:
        registerFileID (str): Handle to a registerFile element

    Returns:
        accessPolicyID (str): The accessPolicy identifier
    """
    rf = resolve_handle(registerFileID)
    if rf is None:
        raise TgiError("Invalid registerFile handle", TgiFaultCode.INVALID_ID)
    container = _ensure_access_policies(rf)
    ap = _new_access_policy()
    return _append_and_register(container, "access_policy", ap, ("access_policy",))


# Removals
def removeAccessPolicyAccess(accessPolicyID: str) -> bool:  # F.7.10.12
    """Section: F.7.10.12

    Description:
        Removes the access field on the given accessPolicy.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    ap = _get_access_policy(accessPolicyID)
    if getattr(ap, "access", None) is None:
        return False
    ap.access = None  # type: ignore[attr-defined]
    return True


def removeAccessRestrictionModeRef(modeRefID: str) -> bool:  # F.7.10.13
    """Section: F.7.10.13

    Description:
        Removes a modeRef from its containing accessRestriction element.

    Args:
        modeRefID (str): Name of the referenced mode

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef

    child = resolve_handle(modeRefID)
    info = get_parent_info(modeRefID)
    parent = resolve_handle(info.parent_handle) if info is not None else None
    if (
        child is None
        or not isinstance(child, ModeRef)
        or parent is None
        or type(parent).__name__ != "AccessRestrictionType"
    ):
        raise TgiError("Invalid accessRestriction modeRef handle", TgiFaultCode.INVALID_ID)
    _get_access_restriction_handle(get_handle(parent))
    return _remove_child(modeRefID, ModeRef, "modeRef")


def removeAccessRestrictionReadAccessMask(accessRestrictionID: str) -> bool:  # F.7.10.14
    """Section: F.7.10.14

    Description:
        Removes a readAccessMask on an accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    return _clear_optional(ar, "read_access_mask")


def removeAccessRestrictionWriteAccessMask(accessRestrictionID: str) -> bool:  # F.7.10.15
    """Section: F.7.10.15

    Description:
        Removes a writeAccessMask on an accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    return _clear_optional(ar, "write_access_mask")


def removeAddressBlockAccessPolicyID(accessPolicyID: str) -> bool:  # F.7.10.16
    """Section: F.7.10.16

    Description:
        Removes the given accessPolicy from its containing addressBlock element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    return _remove_child(accessPolicyID, type(_new_access_policy()), "accessPolicy")


def removeAlternateRegisterAccessPolicy(accessPolicyID: str) -> bool:  # F.7.10.17
    """Section: F.7.10.17

    Description:
        Removes the given accessPolicy from its containing alternateRegister element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    return _remove_child(accessPolicyID, type(_new_access_policy()), "accessPolicy")


def removeFieldAccessPoliciesFieldAccessPolicy(
    fieldAccessPoliciesID: str,
    fieldAccessPolicyID: str | None = None,
) -> bool:  # F.7.10.18
    """Section: F.7.10.18

    Description:
        Removes the given fieldAccessPolicy from its containing fieldAccessPolicies element.

    Args:
        fieldAccessPoliciesID (str): Handle to an fieldAccessPolicies element
        fieldAccessPolicyID (str | None): Optional child handle to select one policy when the container has multiple
            children.

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    container = resolve_handle(fieldAccessPoliciesID)
    if container is None or not hasattr(container, "field_access_policy"):
        raise TgiError("Invalid fieldAccessPolicies handle", TgiFaultCode.INVALID_ID)
    _owning_root(container)
    if fieldAccessPolicyID is None:
        children = list(container.field_access_policy)
        if not children:
            return False
        if len(children) > 1:
            raise TgiError(
                "fieldAccessPolicyID is required when multiple policies exist",
                TgiFaultCode.INVALID_ARGUMENT,
            )
        fieldAccessPolicyID = get_handle(children[0])
    child = resolve_handle(fieldAccessPolicyID)
    if not _is_inline_field_policy(child):
        raise TgiError("Invalid fieldAccessPolicy handle", TgiFaultCode.INVALID_ID)
    if not any(child is item for item in container.field_access_policy):
        return False
    register_parent(child, container, ("field_access_policy",), "list")
    return detach_child_by_handle(fieldAccessPolicyID)


def removeFieldAccessPolicyAccess(fieldAccessPolicyID: str) -> bool:  # F.7.10.19
    """Section: F.7.10.19

    Description:
        Removes the access Attribute on the given fieldAccessPolicy.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.access import Access

    if _choice(pol, Access) is None:
        return False
    _replace_choice(pol, Access, None)
    return True


def removeFieldAccessPolicyAccessRestriction(accessRestrictionID: str) -> bool:  # F.7.10.20
    """Section: F.7.10.20

    Description:
        Removes the given accessRestriction from its containing element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    from org.accellera.ipxact.v1685_2022.access_restriction_type import AccessRestrictionType

    return _remove_child(accessRestrictionID, AccessRestrictionType, "accessRestriction")


def removeFieldAccessPolicyBroadcastTo(broadcastToID: str) -> bool:  # F.7.10.21
    """Section: F.7.10.21

    Description:
        Removes the given broadcastTo from its containing fieldAccessPolicy element.

    Args:
        broadcastToID (str): Handle to a broadcastTo element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    child = resolve_handle(broadcastToID)
    if child is None or type(child).__name__ != "BroadcastTo":
        raise TgiError("Invalid broadcastTo handle", TgiFaultCode.INVALID_ID)
    _owning_root(child)
    if not detach_child_by_handle(broadcastToID):
        raise TgiError("broadcastTo handle has no registered parent", TgiFaultCode.INVALID_ID)
    return True


def removeFieldAccessPolicyFieldAccessPolicyDefinitionRef(fieldAccessPolicyID: str) -> bool:  # F.7.10.22
    """Section: F.7.10.22

    Description:
        Removes the given fieldAccessPolicyDefinitionRef from its containing fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.field_access_policy_definition_ref import FieldAccessPolicyDefinitionRef

    if _choice(pol, FieldAccessPolicyDefinitionRef) is None:
        return False
    _replace_choice(pol, FieldAccessPolicyDefinitionRef, None)
    return True


def removeFieldAccessPolicyModeRef(modeRefID: str) -> bool:  # F.7.10.23
    """Section: F.7.10.23

    Description:
        Removes the given modeRef from its containing fieldAccessPolicy element.

    Args:
        modeRefID (str): Handle to a modeRef element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef

    child = resolve_handle(modeRefID)
    info = get_parent_info(modeRefID)
    parent = resolve_handle(info.parent_handle) if info is not None else None
    if child is None or not isinstance(child, ModeRef) or parent is None or not _is_inline_field_policy(parent):
        raise TgiError("Invalid fieldAccessPolicy modeRef handle", TgiFaultCode.INVALID_ID)
    _get_inline_field_policy(get_handle(parent))
    return _remove_child(modeRefID, ModeRef, "modeRef")


def removeFieldAccessPolicyModifiedWriteValue(fieldAccessPolicyID: str) -> bool:  # F.7.10.24
    """Section: F.7.10.24

    Description:
        Removes the value of the modifiedWriteValue of the given fieldAccessPolicy.

    Args:
        fieldAccessPolicyID (str): Handle to the fieldAccessPolicy

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    choice_type = _field_policy_choice_types()[2]
    if _choice(pol, choice_type) is None:
        return False
    _replace_choice(pol, choice_type, None)
    return True


def removeFieldAccessPolicyReadAction(fieldAccessPolicyID: str) -> bool:  # F.7.10.25
    """Section: F.7.10.25

    Description:
        Removes the value of the readAction of the given fieldAccessPolicy.

    Args:
        fieldAccessPolicyID (str): Handle to the fieldAccessPolicy

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    choice_type = _field_policy_choice_types()[3]
    if _choice(pol, choice_type) is None:
        return False
    _replace_choice(pol, choice_type, None)
    return True


def removeFieldAccessPolicyReadResponse(fieldAccessPolicyID: str) -> bool:  # F.7.10.26
    """Section: F.7.10.26

    Description:
        Removes the readResponse field on a fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to an fieldAccessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    choice_type = _field_policy_choice_types()[4]
    if _choice(pol, choice_type) is None:
        return False
    _replace_choice(pol, choice_type, None)
    return True


def removeFieldAccessPolicyReserved(fieldAccessPolicyID: str) -> bool:  # F.7.10.27
    """Section: F.7.10.27

    Description:
        Removes the Reserved value for fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return _clear_optional(pol, "reserved")


def removeFieldAccessPolicyTestable(fieldAccessPolicyID: str) -> bool:  # F.7.10.28
    """Section: F.7.10.28

    Description:
        Removes a testable element on the given fieldAccessPolicy.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    return _clear_optional(pol, "testable")


def removeFieldAccessPolicyWriteValueConstraint(fieldAccessPolicyID: str) -> bool:  # F.7.10.29
    """Section: F.7.10.29

    Description:
        Removes the writeValueConstraint elements from the given fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    constraint_type = _field_policy_choice_types()[5]
    if _choice(pol, constraint_type) is None:
        return False
    _replace_choice(pol, constraint_type, None)
    return True


def removeFieldDefinitionFieldAccessPolicy(accessPolicyID: str) -> bool:  # F.7.10.30
    """Section: F.7.10.30

    Description:
        Removes the given field accessPolicy from its containing FileDefinition element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    child = resolve_handle(accessPolicyID)
    if not _is_inline_field_policy(child):
        raise TgiError("Invalid fieldAccessPolicy handle", TgiFaultCode.INVALID_ID)
    _owning_root(child)
    if not detach_child_by_handle(accessPolicyID):
        raise TgiError("fieldAccessPolicy has no registered parent", TgiFaultCode.INVALID_ID)
    return True


def removeRegisterAccessPolicy(accessPolicyID: str) -> bool:  # F.7.10.31
    """Section: F.7.10.31

    Description:
        Removes the given accessPolicy from its containing register element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    return _remove_child(accessPolicyID, type(_new_access_policy()), "accessPolicy")


def removeRegisterFileAccessPolicy(accessPolicyID: str) -> bool:  # F.7.10.32
    """Section: F.7.10.32

    Description:
        Removes the given accessPolicy from its containing registerFile element.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    return _remove_child(accessPolicyID, type(_new_access_policy()), "accessPolicy")


# Setters
def setAccessPolicyAccess(accessPolicyID: str, access: str) -> bool:  # F.7.10.33
    """Section: F.7.10.33

    Description:
        Sets the access field on the given accessPolicy.

    Args:
        accessPolicyID (str): Handle to an accessPolicy element
        access (str): Access enumerated value. Can be one of: read-only, write-only,

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    ap = _get_access_policy(accessPolicyID)
    ap.access = access  # type: ignore[attr-defined]
    return True


def setAccessRestrictionReadAccessMask(accessRestrictionID: str, readAccessMask: str) -> bool:  # F.7.10.34
    """Section: F.7.10.34

    Description:
        Sets a readAccessMask on an accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element
        readAccessMask (str): Value of the readAccessMask

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression

    _require_text(readAccessMask, "readAccessMask")
    _set_optional(ar, "read_access_mask", UnsignedBitVectorExpression(value=readAccessMask))
    return True


def setAccessRestrictionWriteAccessMask(accessRestrictionID: str, writeAccessMask: str) -> bool:  # F.7.10.35
    """Section: F.7.10.35

    Description:
        Sets a writeAccessMask on an accessRestriction element.

    Args:
        accessRestrictionID (str): Handle to an accessRestriction element
        writeAccessMask (str): Value of the writeAccessMask

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    ar = _get_access_restriction_handle(accessRestrictionID)
    from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression

    _require_text(writeAccessMask, "writeAccessMask")
    _set_optional(ar, "write_access_mask", UnsignedBitVectorExpression(value=writeAccessMask))
    return True


def setFieldAccessPolicyAccess(fieldAccessPolicyID: str, access: str) -> bool:  # F.7.10.36
    """Section: F.7.10.36

    Description:
        Sets the access Attribute on the given fieldAccessPolicy.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        access (str): Access enumerated value. Can be one of: read-only, write-only, read-write, writeOnce,
            read-writeOnce or
            no-access

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.access import Access
    from org.accellera.ipxact.v1685_2022.access_type import AccessType

    _set_inline_policy_choice(pol, Access, Access(value=_enum_value(AccessType, access, "access")))
    return True


def setFieldAccessPolicyFieldAccessPolicyDefinitionRef(
    fieldAccessPolicyID: str,
    value: str,
    typeDefinitions: str,
) -> bool:  # F.7.10.37
    """Section: F.7.10.37

    Description:
        Sets the FieldAccessPolicyDefinitionRef on the given fieldAccesspolicy.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        value (str): Name of the referenced fieldAccessPolicyDefinition in an external typeDefinitions
        typeDefinitions (str): Name of the component externalTypeDefinitions

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    _require_text(value, "value")
    _require_text(typeDefinitions, "typeDefinitions")
    owner = _owning_root(pol)
    if _external_type_definition(owner, typeDefinitions) is None:
        raise TgiError(
            "typeDefinitions must name an externalTypeDefinitions in the owning document",
            TgiFaultCode.INVALID_ARGUMENT,
        )
    from org.accellera.ipxact.v1685_2022.field_access_policy_definition_ref import FieldAccessPolicyDefinitionRef

    ref_type = _field_policy_choice_types()[1]
    for model_type in (_field_policy_choice_types()[0], *_field_policy_choice_types()[2:]):
        _replace_choice(pol, model_type, None)
    _replace_choice(pol, ref_type, FieldAccessPolicyDefinitionRef(value=value, type_definitions=typeDefinitions))
    return True


def setFieldAccessPolicyModifiedWriteValue(
    fieldAccessPolicyID: str,
    value: str,
    modify: str | None = None,
) -> bool:  # F.7.10.38
    """Section: F.7.10.38

    Description:
        Sets the value of the modifiedWriteValue of the given fieldAccessPolicy.

    Args:
        fieldAccessPolicyID (str): Handle to the fieldAccessPolicy
        value (str): Value of the modifiedWriteValue. Can be one of: oneToClear, one-
        modify (str | None): Optional project extension argument.

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.modified_write_value import ModifiedWriteValue
    from org.accellera.ipxact.v1685_2022.modified_write_value_type import ModifiedWriteValueType

    if modify is not None:
        _require_text(modify, "modify")
    _set_inline_policy_choice(
        pol,
        ModifiedWriteValue,
        ModifiedWriteValue(value=_enum_value(ModifiedWriteValueType, value, "value"), modify=modify),
    )
    return True


def setFieldAccessPolicyReadAction(fieldAccessPolicyID: str, readAction: str) -> bool:  # F.7.10.39
    """Section: F.7.10.39

    Description:
        Sets the read action field on a fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to an fieldAccessPolicy element
        readAction (str): the readAction value to set

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.read_action import ReadAction
    from org.accellera.ipxact.v1685_2022.read_action_type import ReadActionType

    _set_inline_policy_choice(
        pol,
        ReadAction,
        ReadAction(value=_enum_value(ReadActionType, readAction, "readAction")),
    )
    return True


def setFieldAccessPolicyReadResponse(fieldAccessPolicyID: str, readResponse: str) -> bool:  # F.7.10.40
    """Section: F.7.10.40

    Description:
        Sets the readResponse field on a fieldAccessPolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to an fieldAccessPolicy element
        readResponse (str): The readResponse value to set

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.read_response import ReadResponse

    _require_text(readResponse, "readResponse")
    _set_inline_policy_choice(pol, ReadResponse, ReadResponse(value=readResponse))
    return True


def setFieldAccessPolicyReserved(fieldAccessPolicyID: str, reserved: str) -> bool:  # F.7.10.41
    """Section: F.7.10.41

    Description:
        Sets the Reserved value for fieldAccesspolicy element.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        reserved (str): Reserved value

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression

    _require_text(reserved, "reserved")
    _set_optional(pol, "reserved", UnsignedBitExpression(value=reserved))
    return True


def setFieldAccessPolicyTestable(
    fieldAccessPolicyID: str,
    testable: bool,
    testConstraint: str | None = None,
) -> bool:  # F.7.10.42
    """Section: F.7.10.42

    Description:
        Sets a testable element on the given fieldAccesspolicy.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        testable (bool): Handle to value of the added testable
        testConstraint (str | None): Optional project extension argument.

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    _require_bool(testable, "testable")
    if testConstraint is not None:
        _require_text(testConstraint, "testConstraint")
    policy_model = _field_policy_module(pol)
    default_constraint = policy_model.Testable.__dataclass_fields__["test_constraint"].default
    constraint = default_constraint
    if testConstraint is not None:
        constraint = _enum_value(type(default_constraint), testConstraint, "testConstraint")
    _set_optional(
        pol,
        "testable",
        policy_model.Testable(value=testable, test_constraint=constraint),
        preserve=("test_constraint",) if testConstraint is None else (),
    )
    return True


def setFieldAccessPolicyWriteValueConstraintMinMax(
    fieldAccessPolicyID: str,
    minimum: str,
    maximum: str,
) -> bool:  # F.7.10.43
    """Section: F.7.10.43

    Description:
        Sets a writeValueConstraint with a minimum and maximum on fieldAccessPolicy with all his mandatory
        attribute.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        minimum (str): The minimum value
        maximum (str): The maximum value

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    _require_text(minimum, "minimum")
    _require_text(maximum, "maximum")
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    _replace_choice(pol, _field_policy_choice_types()[1], None)
    _new_constraint(
        pol,
        WriteValueConstraintType.Minimum(value=minimum),
    )
    constraint = _choice(pol, _field_policy_choice_types()[5])
    _set_constraint_min_max(
        constraint,
        WriteValueConstraintType.Minimum(value=minimum),
        WriteValueConstraintType.Maximum(value=maximum),
    )
    return True


def setFieldAccessPolicyWriteValueConstraintUseEnumeratedValue(
    fieldAccessPolicyID: str,
    useEnumeratedValue: bool,
) -> bool:  # F.7.10.44
    """Section: F.7.10.44

    Description:
        Sets a writeValueConstraint with a useEnumeratedValue on fieldAccessPolicy with all his mandatory
        attribute.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        useEnumeratedValue (bool): The useEnumeratedValue value

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    _require_bool(useEnumeratedValue, "useEnumeratedValue")
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    _replace_choice(pol, _field_policy_choice_types()[1], None)
    _new_constraint(pol, WriteValueConstraintType.UseEnumeratedValues(value=useEnumeratedValue))
    return True


def setFieldAccessPolicyWriteValueConstraintWriteAsRead(
    fieldAccessPolicyID: str,
    writeAsRead: bool,
) -> bool:  # F.7.10.45
    """Section: F.7.10.45

    Description:
        Sets a writeValueConstraint with a writeAsRead on fieldAccessPolicy with all his mandatory attribute.

    Args:
        fieldAccessPolicyID (str): Handle to a fieldAccessPolicy element
        writeAsRead (bool): The writeAsRead value

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    pol = _get_inline_field_policy(fieldAccessPolicyID)
    _require_bool(writeAsRead, "writeAsRead")
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    _replace_choice(pol, _field_policy_choice_types()[1], None)
    _new_constraint(pol, WriteValueConstraintType.WriteAsRead(value=writeAsRead))
    return True


def setWriteValueConstraintMaximum(writeValueConstraintID: str, maximum: str | None) -> bool:  # F.7.10.46
    """Section: F.7.10.46

    Description:
        Sets the maximum field on a writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element
        maximum (str | None): Maximum value. None removes both range bounds atomically.

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    if maximum is None:
        _replace_choice(w, WriteValueConstraintType.Minimum, None)
        _replace_choice(w, WriteValueConstraintType.Maximum, None)
    else:
        _require_text(maximum, "maximum")
        if _choice(w, WriteValueConstraintType.Minimum) is None:
            raise TgiError("minimum and maximum must be set together", TgiFaultCode.INVALID_ARGUMENT)
        for other_type in (WriteValueConstraintType.WriteAsRead, WriteValueConstraintType.UseEnumeratedValues):
            _replace_choice(w, other_type, None)
        _replace_choice(w, WriteValueConstraintType.Maximum, WriteValueConstraintType.Maximum(value=maximum))
    return True


def setWriteValueConstraintMinimum(writeValueConstraintID: str, minimum: str | None) -> bool:  # F.7.10.47
    """Section: F.7.10.47

    Description:
        Sets the minimum on a writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element
        minimum (str | None): Minimum value. None removes both range bounds atomically.

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    if minimum is None:
        _replace_choice(w, WriteValueConstraintType.Maximum, None)
        _replace_choice(w, WriteValueConstraintType.Minimum, None)
    else:
        _require_text(minimum, "minimum")
        if _choice(w, WriteValueConstraintType.Maximum) is None:
            raise TgiError("minimum and maximum must be set together", TgiFaultCode.INVALID_ARGUMENT)
        for other_type in (WriteValueConstraintType.WriteAsRead, WriteValueConstraintType.UseEnumeratedValues):
            _replace_choice(w, other_type, None)
        _replace_choice(w, WriteValueConstraintType.Minimum, WriteValueConstraintType.Minimum(value=minimum))
    return True


def setWriteValueConstraintUseEnumeratedValues(
    writeValueConstraintID: str,
    useEnumeratedValues: bool,
) -> bool:  # F.7.10.48
    """Section: F.7.10.48

    Description:
        Sets the UseEnumeratedValues on a writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element
        useEnumeratedValues (bool): True to only allow write enumeration values to be written

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    _require_bool(useEnumeratedValues, "useEnumeratedValues")
    for other_type in (
        WriteValueConstraintType.WriteAsRead,
        WriteValueConstraintType.Minimum,
        WriteValueConstraintType.Maximum,
    ):
        _replace_choice(w, other_type, None)
    _replace_choice(
        w,
        WriteValueConstraintType.UseEnumeratedValues,
        WriteValueConstraintType.UseEnumeratedValues(value=useEnumeratedValues),
    )
    return True


def setWriteValueConstraintWriteAsRead(
    writeValueConstraintID: str,
    writeAsRead: bool,
) -> bool:  # F.7.10.49
    """Section: F.7.10.49

    Description:
        Sets the writeAsRead element of the given writeValueConstraint element.

    Args:
        writeValueConstraintID (str): Handle to a writeValueConstraint element
        writeAsRead (bool): True if the access is writeAsRead

    Returns:
        status (bool): Indicates call is successful (true) or not (false)
    """
    w = _get_write_value_constraint_handle(writeValueConstraintID)
    from org.accellera.ipxact.v1685_2022.write_value_constraint_type import WriteValueConstraintType

    _require_bool(writeAsRead, "writeAsRead")
    for other_type in (
        WriteValueConstraintType.UseEnumeratedValues,
        WriteValueConstraintType.Minimum,
        WriteValueConstraintType.Maximum,
    ):
        _replace_choice(w, other_type, None)
    _replace_choice(
        w,
        WriteValueConstraintType.WriteAsRead,
        WriteValueConstraintType.WriteAsRead(value=writeAsRead),
    )
    return True
