"""Configurable element category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.31) and EXTENDED (F.7.32) configurable element
functions. Configurable definitions are parameters with resolve=user/generated,
identified by parameterId. Their defaults are distinct from instance override
entries stored in configurableElementValues. Reference IDs are XML Name strings,
not opaque TGI handles. Numeric defaults follow the Parameter category's constant
value policy; source expressions and generated wrappers are preserved.

Concrete XML document references and component instances resolve to their
registered source documents. View configurations resolve through their design,
component instance and selected view. No configured copies are registered as VLNV
roots. General configured descendant views and parameter environments remain a
separate configuration-service concern.
"""

import re
from collections.abc import Iterator
from dataclasses import fields, is_dataclass
from typing import Any

from lxml import etree

from amal.eda.systemverilog.expression_parser import SvExpressionError, SvExpressionParser
from org.accellera.ipxact.v1685_2022 import (
    AbstractionDefinition,
    Abstractor,
    BusDefinition,
    Component,
    ComponentInstance,
    ComponentInstantiationType,
    ConfigurableElementValue,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    Design,
    DesignConfiguration,
    DesignConfigurationInstantiationType,
    GeneratorChain,
    ModuleParameterType,
    ParameterType,
    TypeDefinitions,
    Value,
)

from ._attribute_references import _register_target_owner, _root_for
from ._parameter_values import _evaluate_numeric, _validate_numeric_update
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
from .name_group import _name_schema
from .parameter import _text

__all__ = [
    # BASE (F.7.31)
    "getConfigurableElementIDs",
    "getConfigurableElementValue",
    "getConfigurableElementValueExpression",
    "getConfigurableElementValueIDs",
    "getConfigurableElementValueReferenceID",
    "getConfigurableElementValueValueExpression",
    "getUnconfiguredID",
    # EXTENDED (F.7.32)
    "addConfigurableElementValue",
    "addViewConfigurationConfigurableElementValue",
    "removeConfigurableElementValue",
    "setConfigurableElementValue",
    "setConfigurableElementValueReferenceID",
    "setConfigurableElementValueValue",
]

# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------

_PARAMETER_TYPES = (ParameterType, ModuleParameterType)
_VIEW_CONFIGURATION = DesignConfiguration.ViewConfiguration
_CONFIGURED_VIEW = _VIEW_CONFIGURATION.View
_REFERENCE_FIELDS = (
    "component_ref",
    "abstractor_ref",
    "design_ref",
    "design_configuration_ref",
    "bus_type",
    "abstraction_ref",
    "type_definitions_ref",
    "group_selector_or_generator_chain_ref",
)
_EXPECTED_ROOTS = {
    "component_ref": "Component",
    "abstractor_ref": "Abstractor",
    "design_ref": "Design",
    "design_configuration_ref": "DesignConfiguration",
    "bus_type": "BusDefinition",
    "abstraction_ref": "AbstractionDefinition",
    "type_definitions_ref": "TypeDefinitions",
    "group_selector_or_generator_chain_ref": "GeneratorChain",
    "generator_chain_configuration": "GeneratorChain",
}


_ROOT_TYPES = {
    "AbstractionDefinition": AbstractionDefinition,
    "Abstractor": Abstractor,
    "BusDefinition": BusDefinition,
    "Component": Component,
    "Design": Design,
    "DesignConfiguration": DesignConfiguration,
    "TypeDefinitions": TypeDefinitions,
    "GeneratorChain": GeneratorChain,
}


def _require(handle: str, expected: type | tuple[type, ...] | None = None) -> Any:
    obj = resolve_handle(handle) if isinstance(handle, str) else None
    if obj is None or (expected is not None and not isinstance(obj, expected)):
        raise TgiError("Invalid configurable element handle", TgiFaultCode.INVALID_ID)
    return obj


def _reference_name(value: str) -> str:
    _text(value, "referenceID", nonempty=True)
    normalized = re.sub(r"[\t\n\r ]+", " ", value).strip(" ")
    element = etree.Element("name")
    element.text = normalized
    if not _name_schema("Name").validate(element):
        raise TgiError("referenceID must be an XML Name", TgiFaultCode.INVALID_ARGUMENT)
    return normalized


def _walk_models(root: object) -> Iterator[object]:
    """Walk generated definitions in source order, registering parsed ownership."""
    pending = [(root, None, None, None)]
    seen: set[int] = set()
    while pending:
        obj, parent, field_name, container = pending.pop()
        if not is_dataclass(obj) or isinstance(obj, type) or id(obj) in seen:
            continue
        seen.add(id(obj))
        if parent is not None:
            register_parent(obj, parent, (field_name,), container)
        yield obj
        children = []
        for field in fields(obj):
            value = getattr(obj, field.name)
            if is_dataclass(value) and not isinstance(value, type):
                children.append((value, obj, field.name, "single"))
            elif isinstance(value, (list, tuple)):
                children.extend((child, obj, field.name, "list") for child in value if is_dataclass(child))
        pending.extend(reversed(children))


def _configurable(parameter: Any) -> bool:
    return isinstance(parameter, _PARAMETER_TYPES) and getattr(parameter.resolve, "value", None) in (
        "user",
        "generated",
    )


def _default(handle: str) -> ParameterType | ModuleParameterType:
    parameter = _require(handle, _PARAMETER_TYPES)
    if not _configurable(parameter):
        raise TgiError("ID is not a configurable definition", TgiFaultCode.INVALID_ID)
    _reference_name(parameter.parameter_id)
    if parameter.value is not None:
        if not isinstance(parameter.value, Value):
            raise TgiError("Invalid default Value wrapper", TgiFaultCode.INVALID_ARGUMENT)
        _text(parameter.value.value, "expression")
    return parameter


def _definitions(scope: Any, *, exclude_instantiations: bool = False) -> list[ParameterType | ModuleParameterType]:
    result = []
    excluded: set[int] = set()
    for obj in _walk_models(scope):
        info = get_parent_info(get_handle(obj))
        parent = resolve_handle(info.parent_handle) if info is not None else None
        if id(parent) in excluded or (
            exclude_instantiations
            and isinstance(obj, (ComponentInstantiationType, DesignConfigurationInstantiationType))
        ):
            excluded.add(id(obj))
            continue
        if _configurable(obj):
            _reference_name(obj.parameter_id)
            result.append(obj)
    references = [parameter.parameter_id for parameter in result]
    if len(set(references)) != len(references):
        raise TgiError("Duplicate configurable parameterId", TgiFaultCode.INVALID_ARGUMENT)
    return result


def _route(owner: Any) -> Any:
    if isinstance(owner, (_VIEW_CONFIGURATION,)):
        if not isinstance(owner.view, _CONFIGURED_VIEW):
            raise TgiError("viewConfiguration requires a generated view", TgiFaultCode.INVALID_ARGUMENT)
        register_parent(owner.view, owner, ("view",), "single")
        return owner.view
    if isinstance(owner, (ConfigurableElementValues, ConfigurableLibraryRefType, _CONFIGURED_VIEW)):
        return owner
    if is_dataclass(owner) and type(owner).__module__.startswith("org.accellera.ipxact.v1685_2022"):
        candidates = [
            (field, getattr(owner, field))
            for field in _REFERENCE_FIELDS
            if isinstance(getattr(owner, field, None), ConfigurableLibraryRefType)
        ]
        if len(candidates) == 1:
            field, reference = candidates[0]
            register_parent(reference, owner, (field,), "single")
            return reference
    raise TgiError("ID is not a configured reference or override holder", TgiFaultCode.INVALID_ID)


def _context(owner: Any) -> tuple[Any | None, ConfigurableElementValues | None]:
    owner = _route(owner)
    if isinstance(owner, ConfigurableElementValues):
        return None, owner
    holder = owner.configurable_element_values
    if holder is not None and not isinstance(holder, ConfigurableElementValues):
        raise TgiError("Invalid configurableElementValues holder", TgiFaultCode.INVALID_ARGUMENT)
    return owner, holder


def _items(holder: ConfigurableElementValues | None) -> list[ConfigurableElementValue]:
    if holder is None:
        return []
    items = holder.configurable_element_value
    if not isinstance(items, (list, tuple)) or any(not isinstance(item, ConfigurableElementValue) for item in items):
        raise TgiError("Invalid configurableElementValue collection", TgiFaultCode.INVALID_ARGUMENT)
    return list(items)


def _register(owner: Any | None, holder: ConfigurableElementValues | None) -> None:
    if holder is None:
        return
    if owner is not None:
        register_parent(holder, owner, ("configurable_element_values",), "single")
    for value in _items(holder):
        register_parent(value, holder, ("configurable_element_value",), "list")


def _lookup(reference: Any, expected: str | None = None) -> Any | None:
    parts = tuple(getattr(reference, part, None) for part in ("vendor", "library", "name", "version"))
    if any(not isinstance(part, str) or not part for part in parts):
        raise TgiError("Incomplete configured document reference", TgiFaultCode.INVALID_ARGUMENT)
    handle = registry.get_id(parts)
    target = resolve_handle(handle) if handle is not None else None
    if target is not None:
        expected_types = (_ROOT_TYPES[expected],) if expected is not None else tuple(_ROOT_TYPES.values())
        if not isinstance(target, expected_types):
            raise TgiError(
                "Configured reference resolves to the wrong document type or schema version",
                TgiFaultCode.INVALID_ARGUMENT,
            )
    return target


def _view_source(view: Any) -> Any | None:
    root = _root_for(view)
    if not isinstance(root, DesignConfiguration):
        return None
    configurations = [
        item for item in _walk_models(root) if isinstance(item, _VIEW_CONFIGURATION) and item.view is view
    ]
    if len(configurations) != 1 or root.design_ref is None:
        return None
    design = _lookup(root.design_ref, "Design")
    if design is None:
        return None
    name = configurations[0].instance_name.value
    instances = (
        []
        if design.component_instances is None
        else [item for item in design.component_instances.component_instance if item.instance_name.value == name]
    )
    if len(instances) > 1:
        raise TgiError("Ambiguous viewConfiguration component instance", TgiFaultCode.INVALID_ARGUMENT)
    if not instances:
        raise TgiError(
            "Selected component instance is absent from the registered design", TgiFaultCode.INVALID_ARGUMENT
        )
    component = _lookup(instances[0].component_ref, "Component")
    if component is None:
        return None
    if component.model is None or component.model.views is None:
        raise TgiError("Registered component has no selected view definitions", TgiFaultCode.INVALID_ARGUMENT)
    views = [item for item in component.model.views.view if item.name == view.view_ref]
    if len(views) > 1:
        raise TgiError("Ambiguous selected view", TgiFaultCode.INVALID_ARGUMENT)
    if not views:
        raise TgiError("Selected view is absent from the registered component", TgiFaultCode.INVALID_ARGUMENT)
    return views[0]


def _source(owner: Any) -> Any | None:
    routed = _route(owner)
    if isinstance(routed, _CONFIGURED_VIEW):
        return _view_source(routed)
    if not isinstance(routed, ConfigurableLibraryRefType):
        raise TgiError("Override holder has no configured source relationship", TgiFaultCode.INVALID_ID)
    _register_target_owner(_root_for(routed), routed)
    info = get_parent_info(get_handle(routed))
    expected = _EXPECTED_ROOTS.get(info.path[-1]) if info is not None and info.path else None
    return _lookup(routed, expected)


def _override_scope(owner: Any) -> tuple[Any | None, bool]:
    routed = _route(owner)
    if isinstance(routed, ConfigurableElementValues):
        return None, False
    source = _source(owner)
    if source is None:
        return None, False
    if isinstance(routed, _CONFIGURED_VIEW):
        component = _root_for(source)
        if getattr(component, "model", None) is None or component.model.instantiations is None:
            raise TgiError("Selected view has no available instantiation scope", TgiFaultCode.INVALID_ARGUMENT)
        references = [
            ref
            for ref in (source.component_instantiation_ref, source.design_configuration_instantiation_ref)
            if ref is not None
        ]
        if len(references) != 1 or source.design_instantiation_ref is not None:
            raise TgiError(
                "Selected view does not reference a supported configurable instantiation", TgiFaultCode.INVALID_ARGUMENT
            )
        instantiations = component.model.instantiations
        entries = instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation
        matches = [
            item
            for item in entries
            if item.name == references[0]
            and isinstance(item, (ComponentInstantiationType, DesignConfigurationInstantiationType))
        ]
        if len(matches) > 1:
            raise TgiError("Ambiguous selected view instantiation", TgiFaultCode.INVALID_ARGUMENT)
        if not matches:
            raise TgiError(
                "Selected configurable instantiation is absent from the component", TgiFaultCode.INVALID_ARGUMENT
            )
        return matches[0], False
    info = get_parent_info(get_handle(routed))
    return source, info is not None and info.path == ("component_ref",)


def _choice_value(parameter: ParameterType | ModuleParameterType, expression: str) -> Any:
    """Compare known choice values under the category's source/numeric policy."""
    if getattr(parameter.type_value, "value", None) != "string":
        return _evaluate_numeric(parameter, expression)
    try:
        return SvExpressionParser().evaluate(expression)
    except SvExpressionError:
        return expression


def _validate_choice(parameter: ParameterType | ModuleParameterType, expression: str) -> None:
    if parameter.choice_ref is None:
        return
    root = _root_for(parameter)
    holder = getattr(root, "choices", None)
    choices = [] if holder is None else [choice for choice in holder.choice if choice.name == parameter.choice_ref]
    if len(choices) != 1:
        raise TgiError("Configurable choiceRef is missing or ambiguous", TgiFaultCode.INVALID_ARGUMENT)
    try:
        value = _choice_value(parameter, expression)
    except TgiError:
        # Numeric setters already reject malformed/known-invalid constants;
        # unresolved symbolic values await their configured environment.
        return
    permitted = [_choice_value(parameter, _text(item.value, "enumeration")) for item in choices[0].enumeration]
    if value not in permitted:
        raise TgiError("Override value is not permitted by choiceRef", TgiFaultCode.INVALID_ARGUMENT)


def _validate_override(owner: Any | None, reference: str, expression: str) -> None:
    if owner is None:
        return
    scope, exclude = _override_scope(owner)
    if scope is None:
        return  # Offline documents retain reference/source text for later validation.
    matches = [
        parameter
        for parameter in _definitions(scope, exclude_instantiations=exclude)
        if parameter.parameter_id == reference
    ]
    if not matches:
        raise TgiError(
            "referenceID does not identify a configurable definition in this context", TgiFaultCode.INVALID_ARGUMENT
        )
    _validate_numeric_update(matches[0], expression)
    _validate_choice(matches[0], expression)


def _holder_for(value: ConfigurableElementValue) -> tuple[Any | None, ConfigurableElementValues | None]:
    root = _root_for(value)
    _register_target_owner(root, value)
    info = get_parent_info(get_handle(value))
    holder = resolve_handle(info.parent_handle) if info is not None else None
    if not isinstance(holder, ConfigurableElementValues) or info.path != ("configurable_element_value",):
        return None, None
    _register_target_owner(root, holder)
    info = get_parent_info(get_handle(holder))
    owner = resolve_handle(info.parent_handle) if info is not None else None
    return owner, holder


def _add(owner: Any, referenceID: str, expression: str) -> str:
    owner, holder = _context(owner)
    reference = _reference_name(referenceID)
    _text(expression, "expression")
    items = _items(holder)
    if any(_reference_name(item.reference_id) == reference for item in items):
        raise TgiError("referenceID already configured", TgiFaultCode.ALREADY_EXISTS)
    _validate_override(owner, reference, expression)
    value = ConfigurableElementValue(reference_id=reference, value=expression)
    if holder is None:
        holder = ConfigurableElementValues(configurable_element_value=[value])
        owner.configurable_element_values = holder
    else:
        holder.configurable_element_value = [*items, value]
    _register(owner, holder)
    return get_handle(value)


# ---------------------------------------------------------------------------
# BASE (F.7.31)
# ---------------------------------------------------------------------------


def getConfigurableElementIDs(unconfiguredElementID: str) -> list[str]:
    """Return configurable definition handles in source order.

    Section: F.7.31.1.

    Args:
        unconfiguredElementID: Handle to an unconfigured document or definition subtree.

    Returns:
        list[str]: Handles to user/generated parameters with parameterId.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    owner = _require(unconfiguredElementID)
    if not is_dataclass(owner) or isinstance(
        owner,
        (
            ConfigurableLibraryRefType,
            ConfigurableElementValues,
            ConfigurableElementValue,
            ComponentInstance,
            _VIEW_CONFIGURATION,
            _CONFIGURED_VIEW,
        ),
    ):
        raise TgiError("ID is not an unconfigured definition", TgiFaultCode.INVALID_ID)
    return [get_handle(parameter) for parameter in _definitions(owner)]


def getConfigurableElementValue(configurableElementID: str) -> str | None:
    """Return the configurable definition's default value.

    Section: F.7.31.2.

    Args:
        configurableElementID: Handle to a user/generated parameter definition.

    Returns:
        str | None: STRING source or self-contained numeric default as text; None if absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    parameter = _default(configurableElementID)
    from .module_parameter import getModuleParameterValue
    from .parameter import getParameterValue

    getter = getModuleParameterValue if isinstance(parameter, ModuleParameterType) else getParameterValue
    return getter(configurableElementID)


def getConfigurableElementValueExpression(configurableElementID: str) -> str | None:
    """Return the unchanged default source expression.

    Section: F.7.31.3.

    Args:
        configurableElementID: Handle to a user/generated parameter definition.

    Returns:
        str | None: Source text, including empty strings; None if absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    parameter = _default(configurableElementID)
    if parameter.value is None:
        return None
    if not isinstance(parameter.value, Value):
        raise TgiError("Invalid default Value wrapper", TgiFaultCode.INVALID_ARGUMENT)
    register_parent(parameter.value, parameter, ("value",), "single")
    return _text(parameter.value.value, "expression")


def getConfigurableElementValueIDs(configuredElementID: str) -> list[str]:
    """Return direct instance override handles in source order.

    Section: F.7.31.4.

    Args:
        configuredElementID: Handle to a configured document reference, instance, view configuration or holder.

    Returns:
        list[str]: Override handles; empty if the optional holder is absent.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    owner, holder = _context(_require(configuredElementID))
    _register(owner, holder)
    return [get_handle(value) for value in _items(holder)]


def getConfigurableElementValueReferenceID(configurableElementValueID: str) -> str | None:
    """Return the override's lexical parameterId reference.

    Section: F.7.31.5.

    Args:
        configurableElementValueID: Handle to a configurableElementValue override.

    Returns:
        str | None: XML Name reference text.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    value = _require(configurableElementValueID, ConfigurableElementValue)
    return _reference_name(value.reference_id)


def getConfigurableElementValueValueExpression(configurableElementValueID: str) -> str | None:
    """Return the unchanged instance override expression.

    Section: F.7.31.6.

    Args:
        configurableElementValueID: Handle to a configurableElementValue override.

    Returns:
        str | None: Override source text.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    value = _require(configurableElementValueID, ConfigurableElementValue)
    return _text(value.value, "expression")


def getUnconfiguredID(configuredElementID: str) -> str | None:
    """Resolve a concrete configured reference to its source definition.

    Section: F.7.31.7.

    Args:
        configuredElementID: Handle to a configured document reference, instance, selected view or override.

    Returns:
        str | None: Source document/view/parameter handle; None when unresolved.
            General configured copies require a configuration service.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    owner = _require(configuredElementID)
    if isinstance(owner, ConfigurableElementValue):
        parent, holder = _holder_for(owner)
        if parent is None:
            return None
        scope, exclude = _override_scope(parent)
        if scope is None:
            return None
        reference = _reference_name(owner.reference_id)
        matches = [
            parameter
            for parameter in _definitions(scope, exclude_instantiations=exclude)
            if parameter.parameter_id == reference
        ]
        return get_handle(matches[0]) if matches else None
    source = _source(owner)
    return get_handle(source) if source is not None else None


# ---------------------------------------------------------------------------
# EXTENDED (F.7.32)
# ---------------------------------------------------------------------------


def addConfigurableElementValue(configuredElementID: str, referenceID: str, expression: str) -> str:
    """Add a typed instance override atomically.

    Section: F.7.32.1.

    Args:
        configuredElementID: Handle to a supported reference, instance, view configuration or holder.
        referenceID: Literal parameterId as an XML Name (XML whitespace is collapsed).
        expression: Override source expression.

    Returns:
        str: New configurableElementValue handle.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
            ALREADY_EXISTS for duplicate reference IDs.
    """
    return _add(_require(configuredElementID), referenceID, expression)


def addViewConfigurationConfigurableElementValue(viewConfigurationID: str, referenceID: str, expression: str) -> str:
    """Add an override beneath the required configured view.

    Section: F.7.32.2.

    Args:
        viewConfigurationID: Handle to a generated viewConfiguration with an existing view.
        referenceID: Literal parameterId as an XML Name.
        expression: Override source expression.

    Returns:
        str: New configurableElementValue handle; viewRef is preserved.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
            ALREADY_EXISTS for duplicate reference IDs.
    """
    return _add(_require(viewConfigurationID, _VIEW_CONFIGURATION), referenceID, expression)


def removeConfigurableElementValue(configurableElementValueID: str) -> bool:
    """Remove an owned override and prune its empty optional holder.

    Section: F.7.32.3.

    Args:
        configurableElementValueID: Handle to the override to remove.

    Returns:
        bool: True if removed; False if no owning collection can be found.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    value = _require(configurableElementValueID, ConfigurableElementValue)
    owner, holder = _holder_for(value)
    if holder is None:
        return False
    items = _items(holder)
    if not any(item is value for item in items):
        return False
    holder.configurable_element_value = items
    _register(owner, holder)
    if not detach_child_by_handle(configurableElementValueID):
        return False
    if not holder.configurable_element_value and owner is not None:
        detach_child_by_handle(get_handle(holder))
    return True


def setConfigurableElementValue(configurableElementID: str, expression: str) -> bool:
    """Set a configurable definition's default expression.

    Section: F.7.32.4.

    Args:
        configurableElementID: Handle to a user/generated parameter definition.
        expression: New default source expression.

    Returns:
        bool: True if the default is updated; existing Value metadata is retained.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    parameter = _default(configurableElementID)
    _text(expression, "expression")
    from .module_parameter import setModuleParameterValue
    from .parameter import setParameterValue

    setter = setModuleParameterValue if isinstance(parameter, ModuleParameterType) else setParameterValue
    return setter(configurableElementID, expression)


def setConfigurableElementValueReferenceID(configurableElementValueID: str, referenceID: str) -> bool:
    """Change an override reference atomically.

    Section: F.7.32.5.

    Args:
        configurableElementValueID: Handle to the override.
        referenceID: New literal parameterId as an XML Name.

    Returns:
        bool: True when updated; duplicate references are rejected.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
            ALREADY_EXISTS for duplicate reference IDs.
    """
    value = _require(configurableElementValueID, ConfigurableElementValue)
    reference = _reference_name(referenceID)
    owner, holder = _holder_for(value)
    if any(item is not value and _reference_name(item.reference_id) == reference for item in _items(holder)):
        raise TgiError("referenceID already configured", TgiFaultCode.ALREADY_EXISTS)
    _validate_override(owner, reference, _text(value.value, "expression"))
    value.reference_id = reference
    return True


def setConfigurableElementValueValue(configurableElementValueID: str, expression: str) -> bool:
    """Set an instance override expression without changing its definition.

    Section: F.7.32.6.

    Args:
        configurableElementValueID: Handle to the override.
        expression: New override source expression.

    Returns:
        bool: True when updated; identity and wildcard metadata are retained.

    Raises:
        TgiError: INVALID_ID for invalid or unsupported handles; INVALID_ARGUMENT
            for malformed XML content, models, references or constant ranges.
    """
    value = _require(configurableElementValueID, ConfigurableElementValue)
    _text(expression, "expression")
    owner, holder = _holder_for(value)
    _validate_override(owner, _reference_name(value.reference_id), expression)
    value.value = expression
    return True
