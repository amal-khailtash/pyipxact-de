"""Parameter category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.65) and EXTENDED (F.7.66) functions for the ``parameter``
elements used widely across IP-XACT. Provides enumeration, choice & reference
helpers, value/expression accessors, and creation/removal/set operations.

Parameters retain generated Value wrappers and source expression text. Numeric
getters evaluate self-contained SystemVerilog constants using the declared type,
width, sign and bounds; configured environments remain a separate concern.
Invalid handles fault, absent optional references return None, and mutations
validate arguments before editing. Only top-level documents use the VLNV registry.
"""

from dataclasses import is_dataclass
from typing import Any, get_args, get_type_hints

from org.accellera.ipxact.v1685_2022 import (
    ComponentInstantiationType,
    ConfigurableElementValue,
    FileSetType,
    FormatType,
    ModuleParameterType,
    Parameter,
    Parameters,
    ParameterType,
    Value,
)

from ._attribute_references import _register_target_owner, _root_for, _walk
from ._parameter_values import _evaluate_numeric, _validate_numeric_update
from .core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    resolve_handle,
)

__all__ = [
    # BASE (F.7.65)
    "getModuleParameterDataTypeDefinitionRefByID",
    "getParameterChoiceRefByName",
    "getParameterIDFromReferenceID",
    "getParameterIDs",
    "getParameterNameFromReferenceID",
    "getParameterValue",
    "getParameterValueExpression",
    "getParameterValueID",
    # EXTENDED (F.7.66)
    "addParameter",
    "removeConfigGroupsAttribute",
    "removeParameter",
    "setParameterValue",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _require(handle: str, expected: type | tuple[type, ...] | None = None) -> Any:
    obj = resolve_handle(handle) if isinstance(handle, str) else None
    if obj is None or (expected is not None and not isinstance(obj, expected)):
        raise TgiError("Invalid parameter handle", TgiFaultCode.INVALID_ID)
    return obj


def _context(handle: str) -> tuple[Any | None, Parameters | None]:
    obj = _require(handle)
    if isinstance(obj, Parameters):
        return None, obj
    if is_dataclass(obj) and not isinstance(obj, type):
        annotation = get_type_hints(type(obj)).get("parameters")
        if annotation is Parameters or Parameters in get_args(annotation):
            holder = obj.parameters
            if holder is not None and not isinstance(holder, Parameters):
                raise TgiError("Invalid parameters holder", TgiFaultCode.INVALID_ARGUMENT)
            return obj, holder
    raise TgiError("ID does not identify a parameter container", TgiFaultCode.INVALID_ID)


def _items(holder: Parameters | None) -> list[ParameterType]:
    if holder is None:
        return []
    items = holder.parameter
    if not isinstance(items, (list, tuple)) or any(not isinstance(item, ParameterType) for item in items):
        raise TgiError("Invalid parameter collection", TgiFaultCode.INVALID_ARGUMENT)
    return list(items)


def _register(owner: Any | None, holder: Parameters | None) -> None:
    if holder is None:
        return
    if owner is not None:
        register_parent(holder, owner, ("parameters",), "single")
    for parameter in _items(holder):
        register_parent(parameter, holder, ("parameter",), "list")
        if isinstance(parameter.value, Value):
            register_parent(parameter.value, parameter, ("value",), "single")


def _text(text: str, name: str, *, nonempty: bool = False) -> str:
    if (
        not isinstance(text, str)
        or (nonempty and not text.strip())
        or any(
            not (
                ch in "\t\n\r"
                or " " <= ch <= "\ud7ff"
                or "\ue000" <= ch <= "\ufffd"
                or "\U00010000" <= ch <= "\U0010ffff"
            )
            for ch in text
        )
    ):
        raise TgiError(f"Invalid {name} string", TgiFaultCode.INVALID_ARGUMENT)
    return text


def _source(parameter: ParameterType) -> str | None:
    if parameter.value is None:
        return None
    if not isinstance(parameter.value, Value):
        raise TgiError("Invalid parameter Value wrapper", TgiFaultCode.INVALID_ARGUMENT)
    return _text(parameter.value.value, "expression")


def _reference_parameter(parametizedID: str, referenceID: str) -> ParameterType | ModuleParameterType | None:
    scope = _require(parametizedID)
    from .module_parameter import _get_context, _register_model

    module_context = _get_context(scope)
    ordinary_context = None
    if module_context is None or hasattr(scope, "parameters"):
        ordinary_context = _context(parametizedID)
    reference = _require(referenceID, (ConfigurableElementValue, str))
    text = reference.reference_id if isinstance(reference, ConfigurableElementValue) else reference
    _text(text, "referenceID", nonempty=True)
    parameters: list[ParameterType | ModuleParameterType] = []
    if ordinary_context is not None:
        parameters.extend(_items(ordinary_context[1]))
    if module_context is not None:
        owner, holder, list_field, parameter_type = module_context
        items = getattr(holder, list_field) if holder is not None else []
        if not isinstance(items, (list, tuple)) or any(not isinstance(item, parameter_type) for item in items):
            raise TgiError("Invalid module/type parameter collection", TgiFaultCode.INVALID_ARGUMENT)
        parameters.extend(items)
    candidates = [parameter for parameter in parameters if parameter.parameter_id == text]
    if len(candidates) > 1:
        raise TgiError("Ambiguous parameterId reference", TgiFaultCode.INVALID_ARGUMENT)
    if not candidates:
        return None
    parameter = candidates[0]
    if ordinary_context is not None:
        _register(*ordinary_context)
    if module_context is not None:
        _register_model(*module_context[:3])
    return parameter


# ---------------------------------------------------------------------------
# BASE (F.7.65)
# ---------------------------------------------------------------------------


def getModuleParameterDataTypeDefinitionRefByID(moduleParameterTypeID: str) -> str | None:
    """Return the referenced file from the owning instantiation's file sets.

    Section: F.7.65.1.

    Args:
        moduleParameterTypeID: Handle to a moduleParameterType element.

    Returns:
        str | None: File handle, or None for an absent/unresolved reference.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _require(moduleParameterTypeID, ModuleParameterType)
    reference = parameter.data_type_definition
    if reference is None:
        return None
    _text(reference, "dataTypeDefinition", nonempty=True)
    root = _root_for(parameter)
    locations = [(item, path) for item, path in _walk(root) if item is parameter]
    if not locations:
        return None
    instantiation = next(
        (item for item in reversed(locations[0][1]) if isinstance(item, ComponentInstantiationType)), None
    )
    if instantiation is None:
        return None
    names = {ref.local_name for ref in instantiation.file_set_ref}
    matches = []
    for holder, _ in _walk(root):
        if not isinstance(holder, FileSetType) or holder.name not in names:
            continue
        for file in holder.file:
            name = getattr(file.name, "value", file.name)
            if name == reference:
                matches.append(file)
    matches = list({id(file): file for file in matches}.values())
    if len(matches) > 1:
        raise TgiError("Ambiguous dataTypeDefinition file", TgiFaultCode.INVALID_ARGUMENT)
    if not matches:
        return None
    file = matches[0]
    _register_target_owner(root, file)
    return get_handle(file)


def getParameterChoiceRefByName(parameterBaseTypeID: str) -> str | None:
    """Return the declared choice reference name.

    Section: F.7.65.2.

    Args:
        parameterBaseTypeID: Handle to a parameter or module/type parameter.

    Returns:
        str | None: Choice name text, or None when no choiceRef is declared.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _require(parameterBaseTypeID, (ParameterType, ModuleParameterType))
    choice = parameter.choice_ref
    return None if choice is None else _text(choice, "choiceRef")


def getParameterIDFromReferenceID(parametizedID: str, referenceID: str) -> str | None:
    """Resolve a referenceId within the given element's own parameter collections.

    Section: F.7.65.3.

    Args:
        parametizedID: Handle to the element containing parameters (standard spelling).
        referenceID: Handle to a configurableElementValue or referenceId string.

    Returns:
        str | None: Referenced parameter handle, or None if unresolved.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _reference_parameter(parametizedID, referenceID)
    return get_handle(parameter) if parameter is not None else None


def getParameterIDs(parameterContainerElementID: str) -> list[str]:
    """Return the direct parameters in source order.

    Section: F.7.65.4.

    Args:
        parameterContainerElementID: Handle to an element supporting parameters, or its Parameters holder.

    Returns:
        list[str]: Parameter handles; an empty list if the optional holder is absent.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    owner, holder = _context(parameterContainerElementID)
    _register(owner, holder)
    return [get_handle(parameter) for parameter in _items(holder)]


def getParameterNameFromReferenceID(parametizedID: str, referenceID: str) -> str | None:
    """Return the referenced name from the given element's own parameter collections.

    Section: F.7.65.5.

    Args:
        parametizedID: Handle to the element containing parameters (standard spelling).
        referenceID: Handle to a configurableElementValue or referenceId string.

    Returns:
        str | None: Referenced parameter name, or None if unresolved.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _reference_parameter(parametizedID, referenceID)
    return parameter.name if parameter is not None else None


def getParameterValue(parameterID: str) -> str | None:
    """Return source text for strings or the evaluated numeric value as text.

    Section: F.7.65.6.

    Args:
        parameterID: Handle to a parameter element.

    Returns:
        str | None: Interpreted self-contained constant value; None if absent.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _require(parameterID, ParameterType)
    source = _source(parameter)
    if source is None or parameter.type_value is FormatType.STRING:
        return source
    return str(_evaluate_numeric(parameter, source))


def getParameterValueExpression(parameterID: str) -> str | None:
    """Return the unchanged parameter value source expression.

    Section: F.7.65.7.

    Args:
        parameterID: Handle to a parameter element.

    Returns:
        str | None: Source expression, including empty strings; None if absent.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    return _source(_require(parameterID, ParameterType))


def getParameterValueID(parameterID: str) -> str | None:
    """Return the owned Value wrapper handle.

    Section: F.7.65.8.

    Args:
        parameterID: Handle to a parameter element.

    Returns:
        str | None: Value handle, or None if the required value is temporarily absent.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _require(parameterID, ParameterType)
    if parameter.value is None:
        return None
    _source(parameter)
    register_parent(parameter.value, parameter, ("value",), "single")
    return get_handle(parameter.value)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.66)
# ---------------------------------------------------------------------------


def addParameter(parameterContainerElementID: str, name: str, expression: str) -> str:
    """Add a typed parameter with a required Value expression atomically.

    Section: F.7.66.1.

    Args:
        parameterContainerElementID: Handle to a supported parameter container or holder.
        name: Unique nonempty parameter name; whitespace is preserved.
        expression: Initial source expression text.

    Returns:
        str: New parameter handle.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
            ALREADY_EXISTS for duplicate names.
    """
    owner, holder = _context(parameterContainerElementID)
    _text(name, "name", nonempty=True)
    _text(expression, "expression")
    items = _items(holder)
    if any(parameter.name == name for parameter in items):
        raise TgiError("Parameter name already exists", TgiFaultCode.ALREADY_EXISTS)
    parameter = Parameter(name=name, value=Value(value=expression))
    if holder is None:
        holder = Parameters(parameter=[parameter])
        owner.parameters = holder
    else:
        holder.parameter = [*items, parameter]
    _register(owner, holder)
    return get_handle(parameter)


def removeConfigGroupsAttribute(parameterID: str) -> bool:
    """Remove the token-list configGroups attribute.

    Section: F.7.66.2.

    Args:
        parameterID: Handle to a parameter or module/type parameter.

    Returns:
        bool: True if removed; False when no tokens are present.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _require(parameterID, (ParameterType, ModuleParameterType))
    if not parameter.config_groups:
        return False
    parameter.config_groups = []
    return True


def removeParameter(parameterID: str) -> bool:
    """Remove an owned parameter and invalidate its descendant handles.

    Section: F.7.66.3.

    Args:
        parameterID: Handle to the parameter to remove.

    Returns:
        bool: True if removed; False if no owning collection can be found.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _require(parameterID, ParameterType)
    root = _root_for(parameter)
    _register_target_owner(root, parameter)
    info = get_parent_info(parameterID)
    if info is None:
        return False
    holder = resolve_handle(info.parent_handle)
    if not isinstance(holder, Parameters) or info.path != ("parameter",) or info.container != "list":
        return False
    items = _items(holder)
    if not any(item is parameter for item in items):
        return False
    _register_target_owner(root, holder)
    holder.parameter = items
    holder_info = get_parent_info(get_handle(holder))
    if not detach_child_by_handle(parameterID):
        return False
    if not holder.parameter and holder_info is not None and holder_info.container == "single":
        detach_child_by_handle(get_handle(holder))
    return True


def setParameterValue(parameterID: str, expression: str) -> bool:
    """Set the parameter source expression after numeric validation.

    Section: F.7.66.4.

    Args:
        parameterID: Handle to a parameter element.
        expression: New expression text; unresolved names are retained for later evaluation.

    Returns:
        bool: True if the value was updated.

    Raises:
        TgiError: INVALID_ID for invalid handles; INVALID_ARGUMENT for malformed
            models or expressions, ambiguity, and numeric range violations.
    """
    parameter = _require(parameterID, ParameterType)
    _text(expression, "expression")
    if parameter.value is not None:
        _source(parameter)
    _validate_numeric_update(parameter, expression)
    if parameter.value is None:
        parameter.value = Value(value=expression)
    else:
        parameter.value.value = expression
    register_parent(parameter.value, parameter, ("value",), "single")
    return True
