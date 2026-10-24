"""Module and type parameter operations from IEEE 1685-2022 Annex F.7.61-F.7.62.

The BASE functions enumerate module parameters and expose their value source
and evaluated value. The EXTENDED functions add, remove, and update parameters
using the generated IP-XACT 2022 model classes. Numeric values are evaluated
as self-contained SystemVerilog constant expressions; source expressions stay
in the XML model unchanged.
"""

# ruff: noqa: I001
from collections.abc import Iterable
from dataclasses import fields
from typing import Any

from org.accellera.ipxact.v1685_2022 import (
    ComponentInstantiationType,
    FormatType,
    ModuleParameterType,
    TypeParameter,
    Value,
)
from org.accellera.ipxact.v1685_2022.struct_port_type_defs import StructPortTypeDefs
from org.accellera.ipxact.v1685_2022.trans_type_def import TransTypeDef
from org.accellera.ipxact.v1685_2022.type_parameters import ServiceTypeDef, TypeParameters

from ._model import _walk_model

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
from ._parameter_values import _evaluate_numeric, _validate_numeric_update

__all__ = [
    # BASE (F.7.61)
    "getModuleParameterIDs",
    "getModuleParameterValue",
    "getModuleParameterValueExpression",
    # EXTENDED (F.7.62)
    "addModuleParameter",
    "removeModuleParameter",
    "setModuleParameterValue",
]


_STRUCT_PORT_TYPE_DEF = StructPortTypeDefs.StructPortTypeDef
_STRUCT_PORT_TYPE_PARAMETERS = _STRUCT_PORT_TYPE_DEF.TypeParameters
_CONTAINER_TYPES = (
    ComponentInstantiationType.ModuleParameters,
    TypeParameters,
    _STRUCT_PORT_TYPE_PARAMETERS,
)
# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _invalid_id(message: str = "Invalid module or type parameter ID") -> TgiError:
    return TgiError(message, TgiFaultCode.INVALID_ID)


def _require_handle(handle: str, expected: type | tuple[type, ...] | None = None) -> Any:
    obj = resolve_handle(handle) if isinstance(handle, str) else None
    if obj is None or (expected is not None and not isinstance(obj, expected)):
        raise _invalid_id()
    return obj


def _parent_container(owner: Any) -> tuple[Any | None, str, type[ModuleParameterType]] | None:
    """Return a supported owner's holder, list field and parameter class."""
    if isinstance(owner, ComponentInstantiationType):
        return owner.module_parameters, "module_parameter", ModuleParameterType
    if isinstance(owner, (TransTypeDef, ServiceTypeDef, _STRUCT_PORT_TYPE_DEF)):
        return owner.type_parameters, "type_parameter", TypeParameter
    return None


def _container_spec(container: Any) -> tuple[str, type[ModuleParameterType]] | None:
    if isinstance(container, ComponentInstantiationType.ModuleParameters):
        return "module_parameter", ModuleParameterType
    if isinstance(container, (TypeParameters, _STRUCT_PORT_TYPE_PARAMETERS)):
        return "type_parameter", TypeParameter
    return None


def _get_context(obj: Any) -> tuple[Any | None, Any | None, str, type[ModuleParameterType]] | None:
    """Return (owner, holder, list field, parameter type) for a real model ID."""
    spec = _container_spec(obj)
    if spec is not None:
        return None, obj, *spec
    parent_spec = _parent_container(obj)
    if parent_spec is not None:
        holder, list_field, parameter_type = parent_spec
        if holder is not None and not isinstance(holder, _CONTAINER_TYPES):
            return None
        return obj, holder, list_field, parameter_type
    return None


def _parameters(holder: Any, list_field: str, parameter_type: type[ModuleParameterType]) -> list[ModuleParameterType]:
    if holder is None:
        return []
    items = getattr(holder, list_field, None)
    if not isinstance(items, (list, tuple)):
        return []
    return [item for item in items if isinstance(item, parameter_type)]


def _holder_empty(holder: Any) -> bool:
    """Whether a schema holder has no remaining generated-model children."""
    return all(
        value is None or value == [] or value == ()
        for value in (getattr(holder, model_field.name) for model_field in fields(holder))
    )


def _register_model(owner: Any | None, holder: Any | None, list_field: str) -> None:
    if holder is None:
        return
    get_handle(holder)
    if owner is not None:
        parent_field = "module_parameters" if isinstance(owner, ComponentInstantiationType) else "type_parameters"
        register_parent(holder, owner, (parent_field,), "single")
    for parameter in _parameters(holder, list_field, ModuleParameterType):
        register_parent(parameter, holder, (list_field,), "list")
        if isinstance(parameter.value, Value):
            get_handle(parameter.value)
            register_parent(parameter.value, parameter, ("value",), "single")


def _walk(root: Any) -> Iterable[tuple[Any, Any | None, str | None]]:
    """Yield generated model objects with their immediate owning field."""
    for obj, parent, field_name, _container in _walk_model(root):
        yield obj, parent, field_name


def _registered_root_parent(target: Any) -> tuple[Any, Any, str] | None:
    """Find target's immediate owner inside a registered top-level model root."""
    for root_id in registry.iter_by_predicate(lambda _root: True):
        root = resolve_handle(root_id)
        if root is None:
            continue
        for obj, parent, field_name in _walk(root):
            if obj is target and parent is not None and field_name is not None:
                return root, parent, field_name
    return None


def _value_source(parameter: ModuleParameterType) -> str | None:
    value = parameter.value
    source = value.value if isinstance(value, Value) else None
    if source is None:
        return None
    if not isinstance(source, str):
        raise TgiError("Parameter value must be a string expression", TgiFaultCode.INVALID_ARGUMENT)
    return source


# ---------------------------------------------------------------------------
# BASE (F.7.61)
# ---------------------------------------------------------------------------


def getModuleParameterIDs(moduleOrTypeParameterContainerElementID: str) -> list[str]:  # F.7.61.1
    """STATIC
    Return IDs for the module or type parameters contained by an IP-XACT element.

    Args:
        moduleOrTypeParameterContainerElementID: ID of a module parameter holder,
            type parameter holder, component instantiation, or type definition.

    Returns:
        IDs for the contained parameters, in document order.

    Section: F.7.61.1.
    """
    obj = _require_handle(moduleOrTypeParameterContainerElementID)
    context = _get_context(obj)
    if context is None:
        raise _invalid_id("ID is not a module or type parameter container")
    owner, holder, list_field, parameter_type = context
    _register_model(owner, holder, list_field)
    return [get_handle(parameter) for parameter in _parameters(holder, list_field, parameter_type)]


def getModuleParameterValue(moduleParameterID: str) -> str | None:  # F.7.61.2
    """STATIC
    Return the interpreted value of a module or type parameter.

    Text parameters retain their source text. Numeric parameters are evaluated
    as self-contained SystemVerilog constant expressions using the declared
    IP-XACT type, vector width, sign and optional bounds.

    Args:
        moduleParameterID: ID of a module or type parameter.

    Returns:
        The parameter value as text, or None when no value is present.

    Section: F.7.61.2.
    """
    parameter = _require_handle(moduleParameterID, ModuleParameterType)
    source = _value_source(parameter)
    if source is None or parameter.type_value is FormatType.STRING:
        return source
    return str(_evaluate_numeric(parameter, source))


def getModuleParameterValueExpression(moduleParameterID: str) -> str | None:  # F.7.61.3
    """STATIC
    Return the source expression stored as a module or type parameter value.

    Args:
        moduleParameterID: ID of a module or type parameter.

    Returns:
        The source expression exactly as stored, or None when absent.

    Section: F.7.61.3.
    """
    parameter = _require_handle(moduleParameterID, ModuleParameterType)
    return _value_source(parameter)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.62)
# ---------------------------------------------------------------------------


def addModuleParameter(
    moduleOrTypeParameterContainerElementID: str,
    name: str,
    expression: str,
) -> str:  # F.7.62.1
    """STATIC
    Add a module or type parameter to the selected IP-XACT parameter container.

    A component instantiation receives a ``moduleParameter``. A transactional,
    service, or structured-port type definition receives a ``typeParameter``.
    Duplicate names in one container are rejected without modifying the model.

    Args:
        moduleOrTypeParameterContainerElementID: ID of a supported container or
            its owning component instantiation or type definition.
        name: Unique parameter name within the selected container.
        expression: Initial source expression for the parameter value.

    Returns:
        ID of the new module or type parameter.

    Section: F.7.62.1.
    """
    obj = _require_handle(moduleOrTypeParameterContainerElementID)
    if not isinstance(name, str) or not name.strip():
        raise TgiError("Parameter name must be a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    if not isinstance(expression, str):
        raise TgiError("Parameter expression must be a string", TgiFaultCode.INVALID_ARGUMENT)
    context = _get_context(obj)
    if context is None:
        raise _invalid_id("ID is not a module or type parameter container")
    owner, holder, list_field, parameter_type = context

    if holder is None:
        if isinstance(obj, ComponentInstantiationType):
            holder = ComponentInstantiationType.ModuleParameters()
            obj.module_parameters = holder
            register_parent(holder, obj, ("module_parameters",), "single")
        elif isinstance(obj, (TransTypeDef, ServiceTypeDef)):
            holder = TypeParameters()
            obj.type_parameters = holder
            register_parent(holder, obj, ("type_parameters",), "single")
        elif isinstance(obj, _STRUCT_PORT_TYPE_DEF):
            holder = _STRUCT_PORT_TYPE_PARAMETERS()
            obj.type_parameters = holder
            register_parent(holder, obj, ("type_parameters",), "single")
        else:  # Defensive; _get_context admits only these parents.
            raise _invalid_id("ID is not a module or type parameter container")

    items = getattr(holder, list_field)
    if any(parameter.name == name for parameter in items):
        raise TgiError("A parameter with this name already exists", TgiFaultCode.INVALID_ARGUMENT)

    parameter = parameter_type(name=name, value=Value(value=expression))
    _validate_numeric_update(parameter, expression)
    if not isinstance(items, list):
        items = list(items)
        setattr(holder, list_field, items)
    items.append(parameter)
    _register_model(owner, holder, list_field)
    get_handle(parameter)
    return get_handle(parameter)


def removeModuleParameter(moduleParameterID: str) -> bool:  # F.7.62.2
    """STATIC
    Remove a module or type parameter and prune its holder when that holder is empty.

    The operation accepts only a module or type parameter ID. An ID that has
    already been removed returns False; registered model values and emptied
    schema holder objects are invalidated with the parameter.

    Args:
        moduleParameterID: ID of the module or type parameter to remove.

    Returns:
        True when the parameter was removed, otherwise False for a stale ID.

    Section: F.7.62.2.
    """
    parameter = resolve_handle(moduleParameterID) if isinstance(moduleParameterID, str) else None
    if parameter is None:
        return False
    if not isinstance(parameter, ModuleParameterType):
        raise _invalid_id("ID does not identify a module or type parameter")

    parent_info = get_parent_info(moduleParameterID)
    holder = resolve_handle(parent_info.parent_handle) if parent_info is not None else None
    if holder is None:
        discovered = _registered_root_parent(parameter)
        if discovered is None:
            return False
        _, holder, list_field = discovered
        register_parent(parameter, holder, (list_field,), "list")
        holder_location = _registered_root_parent(holder)
        if holder_location is not None:
            _, owner, owner_field = holder_location
            if owner_field in ("module_parameters", "type_parameters"):
                register_parent(holder, owner, (owner_field,), "single")
        get_handle(holder)
    else:
        list_field = parent_info.path[-1] if parent_info.path else ""

    items = getattr(holder, list_field, None) if list_field else None
    if isinstance(items, tuple):
        if not any(item is parameter for item in items):
            return False
        items = list(items)
        setattr(holder, list_field, items)
    if not list_field or not isinstance(items, list):
        return False

    holder_info = get_parent_info(get_handle(holder))
    removed = detach_child_by_handle(moduleParameterID)
    if not removed:
        return False

    if _holder_empty(holder):
        if holder_info is None:
            # A parsed parent holder may have been found just before removal.
            holder_location = _registered_root_parent(holder)
            if holder_location is not None:
                _, owner, owner_field = holder_location
                if owner_field in ("module_parameters", "type_parameters"):
                    register_parent(holder, owner, (owner_field,), "single")
                    holder_info = get_parent_info(get_handle(holder))
        if holder_info is not None and holder_info.container == "single":
            detach_child_by_handle(get_handle(holder))
    return True


def setModuleParameterValue(moduleOrTypeParameterID: str, expression: str) -> bool:  # F.7.62.3
    """STATIC
    Set a module or type parameter's value expression.

    Numeric constant expressions are checked against their declared type,
    vector width and configured bounds before the source text is changed.
    Unresolved symbolic expressions remain available for later resolution.

    Args:
        moduleOrTypeParameterID: ID of the module or type parameter to update.
        expression: New source expression for the parameter value.

    Returns:
        True when the value is updated.

    Section: F.7.62.3.
    """
    parameter = _require_handle(moduleOrTypeParameterID, ModuleParameterType)
    if not isinstance(expression, str):
        raise TgiError("Parameter expression must be a string", TgiFaultCode.INVALID_ARGUMENT)
    _validate_numeric_update(parameter, expression)
    if parameter.value is None:
        parameter.value = Value(value=expression)
    else:
        parameter.value.value = expression
    value = parameter.value
    get_handle(value)
    register_parent(value, parameter, ("value",), "single")
    return True
