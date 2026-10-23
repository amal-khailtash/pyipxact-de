"""IEEE 1685-2022 Component TGI operations (F.7.29 and F.7.30).

The BASE functions traverse component definitions and configured component
instances. EXTENDED functions add or remove schema-owned children and update
the specified mode, memory-map, power-domain, and indirect-interface values.
Top-level IP-XACT documents alone are stored in the VLNV registry; nested
objects receive opaque handles from the TGI handle manager.

Invalid or mismatched handles raise TgiError with INVALID_ID. Invalid input
values raise TgiError with INVALID_ARGUMENT. Removal returns False for stale
handles or absent optional values, and successful edits preserve generated
xsdata wrapper and choice objects whenever the schema node already exists.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import fields, is_dataclass
from typing import Any

from org.accellera.ipxact.v1685_2022 import ComponentType

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

__all__ = [
    # BASE (F.7.29)
    "getComponentAddressSpaceIDs",
    "getComponentBusInterfaceIDs",
    "getComponentChannelIDs",
    "getComponentChoiceIDs",
    "getComponentClearboxElementIDs",
    "getComponentComponentGeneratorIDs",
    "getComponentComponentInstantiationIDs",
    "getComponentCpuIDs",
    "getComponentDesignConfigurationInstantiationIDs",
    "getComponentDesignInstantiationIDs",
    "getComponentExternalTypeDefinitionsIDs",
    "getComponentFileSetIDs",
    "getComponentIndirectInterfaceIDs",
    "getComponentMemoryMapIDs",
    "getComponentModeIDs",
    "getComponentOtherClockDriverIDs",
    "getComponentPortIDs",
    "getComponentPowerDomainIDs",
    "getComponentResetTypeIDs",
    "getComponentSelectedViewIDs",
    "getComponentViewIDs",
    "getModeCondition",
    "getModeConditionExpression",
    "getModeName",
    # EXTENDED (F.7.30)
    "addComponentAddressSpace",
    "addComponentChannel",
    "addComponentChoice",
    "addComponentClearboxElement",
    "addComponentComponentGenerator",
    "addComponentComponentInstantiation",
    "addComponentCpu",
    "addComponentDesignConfigurationInstantiation",
    "addComponentDesignInstantiation",
    "addComponentFileSet",
    "addComponentIndirectInterface",
    "addComponentInitiatorBusInterface",
    "addComponentMemoryMap",
    "addComponentMirroredInitiatorBusInterface",
    "addComponentMirroredSystemBusInterface",
    "addComponentMirroredTargetBusInterface",
    "addComponentMode",
    "addComponentMonitorBusInterface",
    "addComponentOtherClockDriver",
    "addComponentResetType",
    "addComponentStructuredInterfacePort",
    "addComponentStructuredStructPort",
    "addComponentStructuredUnionPort",
    "addComponentSystemBusInterface",
    "addComponentTargetBusInterface",
    "addComponentTransactionalPort",
    "addComponentView",
    "addComponentWirePort",
    "removeComponentAddressSpace",
    "removeComponentBusInterface",
    "removeComponentChannel",
    "removeComponentChoice",
    "removeComponentClearboxElement",
    "removeComponentComponentGenerator",
    "removeComponentComponentInstantiation",
    "removeComponentCpu",
    "removeComponentDesignConfigurationInstantiation",
    "removeComponentDesignInstantiation",
    "removeComponentFileSet",
    "removeComponentIndirectInterface",
    "removeComponentMemoryMap",
    "removeComponentMode",
    "removeComponentOtherClockDriver",
    "removeComponentPort",
    "removeComponentResetType",
    "removeComponentView",
    "removeMemoryMapAddressUnitBits",
    "removeModeCondition",
    "removePowerDomainAlwaysOn",
    "setIndirectInterfaceIndirectAddressRef",
    "setIndirectInterfaceIndirectDataRef",
    "setMemoryMapAddressUnitBits",
    "setModeCondition",
    "setModeName",
]


# Helpers (non-spec)


def _fail(message: str, fault: str = TgiFaultCode.INVALID_ID) -> None:
    raise TgiError(message, fault)


_COMPONENT_LIST_PATHS = (
    ("address_spaces", "address_space"),
    ("bus_interfaces", "bus_interface"),
    ("channels", "channel"),
    ("choices", "choice"),
    ("clearbox_elements", "clearbox_element"),
    ("component_generators", "component_generator"),
    ("cpus", "cpu"),
    ("file_sets", "file_set"),
    ("indirect_interfaces", "indirect_interface"),
    ("memory_maps", "memory_map"),
    ("modes", "mode"),
    ("other_clock_drivers", "other_clock_driver"),
    ("power_domains", "power_domain"),
    ("reset_types", "reset_type"),
    ("type_definitions", "external_type_definitions"),
    ("model", "views", "view"),
    ("model", "ports", "port"),
    (
        "model",
        "instantiations",
        "component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
    ),
)


def _follow(root: Any, path: Sequence[str]) -> Any | None:
    current = root
    for segment in path:
        current = getattr(current, segment, None)
        if current is None:
            return None
    return current


def _register_graph(root: Any) -> None:
    """Register immediate generated-object ownership paths below a document."""
    pending: list[Any] = [root]
    seen: set[int] = set()
    while pending:
        parent = pending.pop()
        if id(parent) in seen:
            continue
        seen.add(id(parent))
        if not is_dataclass(parent) or isinstance(parent, type):
            continue
        for item in fields(parent):
            value = getattr(parent, item.name)
            if is_dataclass(value) and not isinstance(value, type):
                register_parent(value, parent, (item.name,), "single")
                pending.append(value)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    if is_dataclass(child) and not isinstance(child, type):
                        register_parent(child, parent, (item.name,), "list")
                        pending.append(child)
    if isinstance(root, ComponentType):
        for path in _COMPONENT_LIST_PATHS:
            container = _follow(root, path[:-1])
            if container is None:
                continue
            if is_dataclass(container) and not isinstance(container, type):
                register_parent(container, root, path[:-1], "single")
            for child in _value_list(root, ".".join(path)):
                register_parent(child, root, path, "list")
        from org.accellera.ipxact.v1685_2022.sub_port_type import PortStructuredType

        for port in _value_list(root, "model.ports.port"):
            structured = getattr(port, "wire_or_transactional_or_structured", None)
            if not isinstance(structured, PortStructuredType):
                continue
            register_parent(structured, port, ("wire_or_transactional_or_structured",), "single")
            definitions = structured.struct_port_type_defs
            if definitions is not None:
                register_parent(definitions, structured, ("struct_port_type_defs",), "single")
                for definition in definitions.struct_port_type_def:
                    register_parent(definition, structured, ("struct_port_type_defs", "struct_port_type_def"), "list")
            sub_ports = structured.sub_ports
            if sub_ports is not None:
                register_parent(sub_ports, structured, ("sub_ports",), "single")
                for sub_port in sub_ports.sub_port:
                    register_parent(sub_port, structured, ("sub_ports", "sub_port"), "list")


def _registered_component_roots() -> Iterable[ComponentType]:
    for handle in registry.iter_by_predicate(lambda obj: isinstance(obj, ComponentType)):
        root = resolve_handle(handle)
        if isinstance(root, ComponentType):
            yield root


def _contains_identity(root: Any, target: Any) -> bool:
    pending = [root]
    seen: set[int] = set()
    while pending:
        obj = pending.pop()
        if obj is target:
            return True
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        if not is_dataclass(obj) or isinstance(obj, type):
            continue
        for item in fields(obj):
            value = getattr(obj, item.name)
            if is_dataclass(value) and not isinstance(value, type):
                pending.append(value)
            elif isinstance(value, (list, tuple)):
                pending.extend(value)
    return False


def _component_for_instance(instance: Any) -> ComponentType:
    reference = getattr(instance, "component_ref", None)
    parts = tuple(getattr(reference, key, None) for key in ("vendor", "library", "name", "version"))
    if not all(isinstance(part, str) and part for part in parts):
        _fail("Component instance has no complete componentRef", TgiFaultCode.NOT_FOUND)
    component_id = registry.get_id(parts)
    component = resolve_handle(component_id) if component_id is not None else None
    if not isinstance(component, ComponentType):
        _fail(f"Referenced component {parts!r} is not registered", TgiFaultCode.NOT_FOUND)
    _register_graph(component)
    return component


def _resolve_component(handle: str, *, allow_instance: bool = True) -> ComponentType:
    obj = resolve_handle(handle) if isinstance(handle, str) else None
    if isinstance(obj, ComponentType):
        _register_graph(obj)
        return obj
    if allow_instance:
        from org.accellera.ipxact.v1685_2022.component_instance import ComponentInstance

        if isinstance(obj, ComponentInstance):
            return _component_for_instance(obj)
    _fail("Invalid component handle")
    raise AssertionError("unreachable")


def _resolve_typed(handle: str, expected: type | tuple[type, ...], label: str) -> Any:
    obj = resolve_handle(handle) if isinstance(handle, str) else None
    if obj is None or not isinstance(obj, expected):
        _fail(f"Invalid {label} handle")
    _register_owner_for(obj)
    return obj


def _register_owner_for(child: Any) -> ComponentType | None:
    """Recover and register a parsed child's graph through a registered root."""
    info = get_parent_info(get_handle(child))
    if info is not None:
        parent = resolve_handle(info.parent_handle)
        seen: set[int] = set()
        while parent is not None and id(parent) not in seen:
            if isinstance(parent, ComponentType):
                _register_graph(parent)
                return parent
            seen.add(id(parent))
            parent_info = get_parent_info(get_handle(parent))
            parent = resolve_handle(parent_info.parent_handle) if parent_info is not None else None
    for root in _registered_component_roots():
        if _contains_identity(root, child):
            _register_graph(root)
            return root
    return None


def _value_list(obj: Any, path: str) -> list[Any]:
    current = obj
    for segment in path.split("."):
        current = getattr(current, segment, None)
        if current is None:
            return []
    return list(current) if isinstance(current, (list, tuple)) else []


def _ids(items: Iterable[Any]) -> list[str]:
    return [get_handle(item) for item in items]


def _component_ids(component: ComponentType, path: str) -> list[str]:
    return _ids(_value_list(component, path))


def _component_only(handle: str) -> ComponentType:
    return _resolve_component(handle, allow_instance=False)


def _require_text(value: str, argument: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TgiError(f"{argument} must be a nonempty string", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _vlnv(value: Sequence[str] | str, argument: str) -> tuple[str, str, str, str]:
    from .core import vlnv_to_tuple

    try:
        parts = vlnv_to_tuple(value)
    except (TypeError, TgiError) as error:
        raise TgiError(f"{argument} must contain four VLNV strings", TgiFaultCode.INVALID_ARGUMENT) from error
    if any(not isinstance(part, str) or not part.strip() for part in parts):
        raise TgiError(f"{argument} must contain four nonempty VLNV strings", TgiFaultCode.INVALID_ARGUMENT)
    return parts


def _list_attr(parent: Any, attr: str) -> list[Any]:
    value = getattr(parent, attr)
    if not isinstance(value, list):
        value = list(value)
        setattr(parent, attr, value)
    return value


def _ensure_container(parent: Any, attr: str, cls: type) -> Any:
    value = getattr(parent, attr)
    if value is None:
        value = cls()
        setattr(parent, attr, value)
        register_parent(value, parent, (attr,), "single")
    return value


def _ensure_model(component: ComponentType) -> Any:
    from org.accellera.ipxact.v1685_2022.model import Model

    if component.model is None:
        component.model = Model()
        register_parent(component.model, component, ("model",), "single")
    return component.model


def _ensure_model_container(component: ComponentType, attr: str, cls: type) -> tuple[Any, Any]:
    model = _ensure_model(component)
    container = _ensure_container(model, attr, cls)
    return model, container


def _append_child(parent: Any, attr: str, child: Any) -> str:
    _list_attr(parent, attr).append(child)
    register_parent(child, parent, (attr,), "list")
    handle = get_handle(child)
    component = _register_owner_for(parent)
    if component is not None:
        _register_graph(component)
    return handle


def _assert_unique(component: ComponentType, path: str, name: str, argument: str = "name") -> None:
    _require_text(name, argument)
    for child in _value_list(component, path):
        if getattr(child, "name", getattr(child, "clock_name", None)) == name:
            raise TgiError(f"Duplicate {argument} {name!r}", TgiFaultCode.ALREADY_EXISTS)


def _owned_child(handle: str, expected: type | tuple[type, ...], label: str) -> Any | None:
    child = resolve_handle(handle) if isinstance(handle, str) else None
    if child is None:
        return None
    if not isinstance(child, expected):
        _fail(f"Handle is not a {label}")
    if _register_owner_for(child) is None:
        _fail(f"{label} has no component owner")
    return child


def _remove_child(handle: str, expected: type | tuple[type, ...], label: str) -> bool:
    child = _owned_child(handle, expected, label)
    if child is None:
        return False
    info = get_parent_info(get_handle(child))
    parent = resolve_handle(info.parent_handle) if info is not None else None
    removed = detach_child_by_handle(get_handle(child))
    if removed and parent is not None:
        if isinstance(parent, ComponentType) and info is not None:
            _prune_component_path(parent, info.path)
        else:
            _prune_empty_container(parent)
    return removed


def _prune_component_path(component: ComponentType, path: Sequence[str]) -> None:
    for length in range(len(path) - 1, 0, -1):
        container = _follow(component, path[:length])
        if container is not None and _is_empty_owned_container(container):
            detach_child_by_handle(get_handle(container))


def _is_empty_owned_container(obj: Any) -> bool:
    from org.accellera.ipxact.v1685_2022.model import Model

    if isinstance(obj, Model):
        return obj.views is None and obj.instantiations is None and obj.ports is None
    if not is_dataclass(obj) or isinstance(obj, type):
        return False
    values = [getattr(obj, item.name) for item in fields(obj)]
    return bool(values) and all(value is None or (isinstance(value, (list, tuple)) and not value) for value in values)


def _prune_empty_container(obj: Any) -> None:
    current = obj
    seen: set[int] = set()
    while id(current) not in seen and _is_empty_owned_container(current):
        seen.add(id(current))
        parent_info = get_parent_info(get_handle(current))
        if parent_info is None:
            break
        parent = resolve_handle(parent_info.parent_handle)
        if parent is None or isinstance(parent, ComponentType):
            if parent is not None:
                detach_child_by_handle(get_handle(current))
            break
        if not detach_child_by_handle(get_handle(current)):
            break
        current = parent


# ---------------------------------------------------------------------------
# BASE (F.7.29)
# ---------------------------------------------------------------------------


def getComponentAddressSpaceIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component address spaces.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of addressSpace handles.

    Section: F.7.29.1.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "address_spaces.address_space")


def getComponentBusInterfaceIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component bus interfaces.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of busInterface handles.

    Section: F.7.29.2.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "bus_interfaces.bus_interface")


def getComponentChannelIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component channels.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of channel handles.

    Section: F.7.29.3.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "channels.channel")


def getComponentChoiceIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component choices.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of choice handles.

    Section: F.7.29.4.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "choices.choice")


def getComponentClearboxElementIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component clearbox elements.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of clearboxElement handles.

    Section: F.7.29.5.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "clearbox_elements.clearbox_element")


def getComponentComponentGeneratorIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component generators.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of componentGenerator handles.

    Section: F.7.29.6.
    """
    return _component_ids(
        _resolve_component(componentOrComponentInstanceID), "component_generators.component_generator"
    )


def getComponentComponentInstantiationIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component instantiations in the component model.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of ComponentInstantiationType handles.

    Section: F.7.29.7.
    """
    from org.accellera.ipxact.v1685_2022.component_instantiation_type import ComponentInstantiationType

    return [
        handle
        for handle in _component_ids(
            _resolve_component(componentOrComponentInstanceID),
            "model.instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
        )
        if isinstance(resolve_handle(handle), ComponentInstantiationType)
    ]


def getComponentCpuIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component CPUs.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of cpu handles.

    Section: F.7.29.8.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "cpus.cpu")


def getComponentDesignConfigurationInstantiationIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of designConfigurationInstantiation elements in the component model.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of DesignConfigurationInstantiationType handles.

    Section: F.7.29.9.
    """
    from org.accellera.ipxact.v1685_2022.design_configuration_instantiation_type import (
        DesignConfigurationInstantiationType,
    )

    return [
        handle
        for handle in _component_ids(
            _resolve_component(componentOrComponentInstanceID),
            "model.instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
        )
        if isinstance(resolve_handle(handle), DesignConfigurationInstantiationType)
    ]


def getComponentDesignInstantiationIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of designInstantiation elements in the component model.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of DesignInstantiationType handles.

    Section: F.7.29.10.
    """
    from org.accellera.ipxact.v1685_2022.design_instantiation_type import DesignInstantiationType

    return [
        handle
        for handle in _component_ids(
            _resolve_component(componentOrComponentInstanceID),
            "model.instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
        )
        if isinstance(resolve_handle(handle), DesignInstantiationType)
    ]


def getComponentExternalTypeDefinitionsIDs(componentID: str) -> list[str]:
    """Return handles of external type definitions.

    Args:
        componentID: Handle to a component element.

    Returns:
        List of externalTypeDefinitions handles.

    Section: F.7.29.11.
    """
    return _component_ids(_component_only(componentID), "type_definitions.external_type_definitions")


def getComponentFileSetIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component file sets.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of fileSet handles.

    Section: F.7.29.12.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "file_sets.file_set")


def getComponentIndirectInterfaceIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component indirect interfaces.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of indirectInterface handles.

    Section: F.7.29.13.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "indirect_interfaces.indirect_interface")


def getComponentMemoryMapIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component memory maps.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of memoryMap handles.

    Section: F.7.29.14.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "memory_maps.memory_map")


def getComponentModeIDs(componentID: str) -> list[str]:
    """Return handles of component modes.

    Args:
        componentID: Handle to a component element.

    Returns:
        List of mode handles.

    Section: F.7.29.15.
    """
    return _component_ids(_component_only(componentID), "modes.mode")


def getComponentOtherClockDriverIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component clock drivers.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of otherClockDriver handles.

    Section: F.7.29.16.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "other_clock_drivers.other_clock_driver")


def getComponentPortIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component model ports of every style.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of port handles.

    Section: F.7.29.17.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "model.ports.port")


def getComponentPowerDomainIDs(componentID: str) -> list[str]:
    """Return handles of component power domains.

    Args:
        componentID: Handle to a component element.

    Returns:
        List of powerDomain handles.

    Section: F.7.29.18.
    """
    return _component_ids(_component_only(componentID), "power_domains.power_domain")


def getComponentResetTypeIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of component reset types.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of resetType handles.

    Section: F.7.29.19.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "reset_types.reset_type")


def getComponentSelectedViewIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of selected views for the given component instance.

    An unconfigured component has no selected views.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of selected View handles.

    Section: F.7.29.20.
    """
    from org.accellera.ipxact.v1685_2022.component_instance import ComponentInstance

    obj = resolve_handle(componentOrComponentInstanceID) if isinstance(componentOrComponentInstanceID, str) else None
    if not isinstance(obj, ComponentInstance):
        _component_only(componentOrComponentInstanceID)
        return []
    component = _component_for_instance(obj)
    owner_design = _design_for_instance(obj)
    if owner_design is None:
        return []
    design_vlnv = tuple(getattr(owner_design, key, None) for key in ("vendor", "library", "name", "version"))
    from org.accellera.ipxact.v1685_2022.design_configuration import DesignConfiguration

    configurations = []
    for handle in registry.iter_by_predicate(lambda root: isinstance(root, DesignConfiguration)):
        configuration = resolve_handle(handle)
        ref = getattr(configuration, "design_ref", None)
        ref_vlnv = tuple(getattr(ref, key, None) for key in ("vendor", "library", "name", "version"))
        if ref_vlnv == design_vlnv:
            configurations.append(configuration)
    if len(configurations) > 1:
        _fail("More than one registered designConfiguration matches the owning design", TgiFaultCode.INVALID_ARGUMENT)
    if not configurations:
        return []
    instance_name = getattr(getattr(obj, "instance_name", None), "value", None)
    selections = [
        item
        for item in configurations[0].view_configuration
        if getattr(getattr(item, "instance_name", None), "value", None) == instance_name
    ]
    if len(selections) > 1:
        _fail(f"More than one view is selected for component instance {instance_name!r}", TgiFaultCode.INVALID_ARGUMENT)
    if not selections:
        return []
    view_name = selections[0].view.view_ref
    matches = [view for view in _value_list(component, "model.views.view") if view.name == view_name]
    if not matches:
        _fail(f"Selected view {view_name!r} does not exist on the referenced component", TgiFaultCode.NOT_FOUND)
    return _ids(matches)


def getComponentViewIDs(componentOrComponentInstanceID: str) -> list[str]:
    """Return handles of all component model views.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.

    Returns:
        List of view handles.

    Section: F.7.29.21.
    """
    return _component_ids(_resolve_component(componentOrComponentInstanceID), "model.views.view")


def _resolve_mode(modeID: str) -> Any:
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT

    return _resolve_typed(modeID, CT.Modes.Mode, "mode")


def _mode_expression(mode: Any) -> str | None:
    condition = getattr(mode, "condition", None)
    value = getattr(condition, "value", None)
    return value if isinstance(value, str) else None


def _try_evaluate_expression(expression: str) -> int | None:
    try:
        from amal.eda.systemverilog.expression_parser import SvExpressionParser

        value = SvExpressionParser().evaluate(expression)
    except ImportError, ValueError, TypeError, AttributeError:
        return None
    if type(value) is not int:
        raise TgiError("Expression must evaluate to an integer", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _resolved_bit_expression(expression: str | None) -> str | None:
    if expression is None:
        return None
    value = _try_evaluate_expression(expression)
    if value not in (0, 1):
        raise TgiError("Mode condition must resolve to unsigned bit 0 or 1", TgiFaultCode.INVALID_ARGUMENT)
    return str(value)


def _validated_expression(expression: str, argument: str, minimum: int, maximum: int) -> str:
    expression = _require_text(expression, argument)
    value = _try_evaluate_expression(expression)
    if value is not None and not minimum <= value <= maximum:
        raise TgiError(f"{argument} is outside its allowed numeric range", TgiFaultCode.INVALID_ARGUMENT)
    return expression


def getModeCondition(modeID: str) -> str | None:
    """Return the resolved condition value for a component mode.

    Args:
        modeID: Handle to a mode element.

    Returns:
        Resolved condition as a string, or None when absent. Unresolved expressions raise INVALID_ARGUMENT.

    Section: F.7.29.22.
    """
    return _resolved_bit_expression(_mode_expression(_resolve_mode(modeID)))


def getModeConditionExpression(modeID: str) -> str | None:
    """Return the source condition expression for a component mode.

    Args:
        modeID: Handle to a mode element.

    Returns:
        Condition expression as a string, or None when absent.

    Section: F.7.29.23.
    """
    return _mode_expression(_resolve_mode(modeID))


def getModeName(modeID: str) -> str:
    """Return the name of a component mode.

    Args:
        modeID: Handle to a mode element.

    Returns:
        Mode name as a string.

    Section: F.7.29.24.
    """
    return _resolve_mode(modeID).name


# ---------------------------------------------------------------------------
# EXTENDED (F.7.30) – creation
# ---------------------------------------------------------------------------


def addComponentAddressSpace(componentID: str, name: str, range: str, width: str) -> str:
    """Add an addressSpace with its name, range expression, and width expression.

    Args:
        componentID: Handle to a component element.
        name: Address-space name.
        range: Address-space range expression.
        width: Address-space width expression.

    Returns:
        Handle to the new addressSpace.

    Section: F.7.30.1.
    """
    from org.accellera.ipxact.v1685_2022.address_spaces import AddressSpaces
    from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
    from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression

    component = _component_only(componentID)
    _assert_unique(component, "address_spaces.address_space", name)
    range = _validated_expression(range, "range", 1, (1 << 63) - 1)
    width = _validated_expression(width, "width", 1, (1 << 32) - 1)
    child = AddressSpaces.AddressSpace(
        name=name,
        range=UnsignedPositiveLongintExpression(value=range),
        width=UnsignedPositiveIntExpression(value=width),
    )
    container = _ensure_container(component, "address_spaces", AddressSpaces)
    return _append_child(container, "address_space", child)


def addComponentChannel(componentID: str, name: str, busInterfaceRefs: Sequence[str]) -> str:
    """Add a channel with the given name and referenced bus interfaces.

    Args:
        componentID: Handle to a component element.
        name: Channel name.
        busInterfaceRefs: Names of at least two bus interfaces in this component.

    Returns:
        Handle to the new channel.

    Section: F.7.30.2.
    """
    from org.accellera.ipxact.v1685_2022.channels import Channels

    component = _component_only(componentID)
    _assert_unique(component, "channels.channel", name)
    if (
        not isinstance(busInterfaceRefs, Sequence)
        or isinstance(busInterfaceRefs, (str, bytes))
        or len(busInterfaceRefs) < 2
    ):
        raise TgiError("busInterfaceRefs must contain at least two names", TgiFaultCode.INVALID_ARGUMENT)
    refs = [_require_text(ref, "busInterfaceRefs item") for ref in busInterfaceRefs]
    child = Channels.Channel(
        name=name,
        bus_interface_ref=[Channels.Channel.BusInterfaceRef(local_name=ref) for ref in refs],
    )
    return _append_child(_ensure_container(component, "channels", Channels), "channel", child)


def addComponentChoice(componentID: str, name: str, enumerations: Sequence[str]) -> str:
    """Add a choice and its enumeration values.

    Args:
        componentID: Handle to a component element.
        name: Choice name.
        enumerations: One or more legal enumeration expressions.

    Returns:
        Handle to the new choice.

    Section: F.7.30.3.
    """
    from org.accellera.ipxact.v1685_2022.choices import Choices

    component = _component_only(componentID)
    _assert_unique(component, "choices.choice", name)
    if not isinstance(enumerations, Sequence) or isinstance(enumerations, (str, bytes)) or not enumerations:
        raise TgiError("enumerations must contain at least one value", TgiFaultCode.INVALID_ARGUMENT)
    values = [_require_text(value, "enumerations item") for value in enumerations]
    child = Choices.Choice(name=name, enumeration=[Choices.Choice.Enumeration(value=value) for value in values])
    return _append_child(_ensure_container(component, "choices", Choices), "choice", child)


def addComponentClearboxElement(componentID: str, name: str, type: str) -> str:
    """Add a clearboxElement with its name and clearbox type.

    Args:
        componentID: Handle to a component element.
        name: Clearbox-element name.
        type: One of signal, pin, or interface.

    Returns:
        Handle to the new clearboxElement.

    Section: F.7.30.4.
    """
    from org.accellera.ipxact.v1685_2022.clearbox_element_type import ClearboxElementType
    from org.accellera.ipxact.v1685_2022.simple_clearbox_type import SimpleClearboxType

    component = _component_only(componentID)
    _assert_unique(component, "clearbox_elements.clearbox_element", name)
    try:
        kind = SimpleClearboxType(type)
    except (TypeError, ValueError) as error:
        raise TgiError("Invalid clearbox type", TgiFaultCode.INVALID_ARGUMENT) from error
    child = ClearboxElementType(name=name, clearbox_type=kind)
    return _append_child(
        _ensure_container(component, "clearbox_elements", ComponentType.ClearboxElements), "clearbox_element", child
    )


def addComponentComponentGenerator(componentID: str, name: str, generatorExecutable: str) -> str:
    """Add a componentGenerator with its executable path.

    Args:
        componentID: Handle to a component element.
        name: Generator name.
        generatorExecutable: Path or URI for the generator executable.

    Returns:
        Handle to the new componentGenerator.

    Section: F.7.30.5.
    """
    from org.accellera.ipxact.v1685_2022.component_generator import ComponentGenerator
    from org.accellera.ipxact.v1685_2022.component_generators import ComponentGenerators
    from org.accellera.ipxact.v1685_2022.ipxact_uri import IpxactUri

    component = _component_only(componentID)
    _assert_unique(component, "component_generators.component_generator", name)
    _require_text(generatorExecutable, "generatorExecutable")
    child = ComponentGenerator(name=name, generator_exe=IpxactUri(value=generatorExecutable))
    return _append_child(
        _ensure_container(component, "component_generators", ComponentGenerators), "component_generator", child
    )


def addComponentComponentInstantiation(componentID: str, name: str) -> str:
    """Add a componentInstantiation with the given name.

    Args:
        componentID: Handle to a component element.
        name: Component-instantiation name.

    Returns:
        Handle to the new componentInstantiation.

    Section: F.7.30.6.
    """
    from org.accellera.ipxact.v1685_2022.component_instantiation_type import ComponentInstantiationType

    component = _component_only(componentID)
    _assert_unique(
        component,
        "model.instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
        name,
    )
    return _append_instantiation(component, ComponentInstantiationType(name=name))


def addComponentCpu(componentID: str, name: str, memoryMapRef: str, range: str, width: str) -> str:
    """Add a CPU with its memory-map reference, range, and width.

    Args:
        componentID: Handle to a component element.
        name: CPU name.
        memoryMapRef: Name of the referenced memory map.
        range: CPU range expression.
        width: CPU width expression.

    Returns:
        Handle to the new cpu.

    Section: F.7.30.7.
    """
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT
    from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
    from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression

    from .cpu import _name, _source

    component = _component_only(componentID)
    name = _name(name)
    memoryMapRef = _name(memoryMapRef)
    range = _source(range, 1, (1 << 64) - 1)
    width = _source(width, 1, (1 << 32) - 1)
    _assert_unique(component, "cpus.cpu", name)
    child = CT.Cpus.Cpu(
        name=name,
        memory_map_ref=memoryMapRef,
        range=UnsignedPositiveLongintExpression(value=range),
        width=UnsignedPositiveIntExpression(value=width),
    )
    return _append_child(_ensure_container(component, "cpus", CT.Cpus), "cpu", child)


def addComponentDesignConfigurationInstantiation(
    componentOrComponentInstanceID: str, name: str, designConfigurationVLNV: Sequence[str] | str
) -> str:
    """Add a designConfigurationInstantiation referencing a design configuration VLNV.

    Args:
        componentOrComponentInstanceID: Handle to a component or componentInstance element.
        name: Instantiation name.
        designConfigurationVLNV: Four-part design-configuration VLNV.

    Returns:
        Handle to the new designConfigurationInstantiation.

    Section: F.7.30.8.
    """
    from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
    from org.accellera.ipxact.v1685_2022.design_configuration_instantiation_type import (
        DesignConfigurationInstantiationType,
    )

    component = _resolve_component(componentOrComponentInstanceID)
    _assert_unique(
        component,
        "model.instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
        name,
    )
    parts = _vlnv(designConfigurationVLNV, "designConfigurationVLNV")
    reference = ConfigurableLibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])
    return _append_instantiation(
        component, DesignConfigurationInstantiationType(name=name, design_configuration_ref=reference)
    )


def addComponentDesignInstantiation(componentID: str, name: str, designVLNV: Sequence[str] | str) -> str:
    """Add a designInstantiation referencing a design VLNV.

    Args:
        componentID: Handle to a component element.
        name: Instantiation name.
        designVLNV: Four-part design VLNV.

    Returns:
        Handle to the new designInstantiation.

    Section: F.7.30.9.
    """
    from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
    from org.accellera.ipxact.v1685_2022.design_instantiation_type import DesignInstantiationType

    component = _component_only(componentID)
    _assert_unique(
        component,
        "model.instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation",
        name,
    )
    parts = _vlnv(designVLNV, "designVLNV")
    reference = ConfigurableLibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])
    return _append_instantiation(component, DesignInstantiationType(name=name, design_ref=reference))


def addComponentFileSet(componentID: str, name: str) -> str:
    """Add a fileSet with the given name.

    Args:
        componentID: Handle to a component element.
        name: File-set name.

    Returns:
        Handle to the new fileSet.

    Section: F.7.30.10.
    """
    from org.accellera.ipxact.v1685_2022.file_set import FileSet
    from org.accellera.ipxact.v1685_2022.file_sets import FileSets

    component = _component_only(componentID)
    _assert_unique(component, "file_sets.file_set", name)
    return _append_child(_ensure_container(component, "file_sets", FileSets), "file_set", FileSet(name=name))


def addComponentIndirectInterface(
    componentID: str, name: str, indirectAddressRef: str, indirectData: str, memoryMapRef: str | None
) -> str:
    """Add an indirectInterface with field references and an optional memory-map reference.

    Args:
        componentID: Handle to a component element.
        name: Indirect-interface name.
        indirectAddressRef: Field name for the indirect address reference.
        indirectData: Field name for the indirect data reference.
        memoryMapRef: Optional referenced memory-map name.

    Returns:
        Handle to the new indirectInterface.

    Section: F.7.30.11.
    """
    from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
    from org.accellera.ipxact.v1685_2022.indirect_address_ref import IndirectAddressRef
    from org.accellera.ipxact.v1685_2022.indirect_data_ref import IndirectDataRef
    from org.accellera.ipxact.v1685_2022.indirect_interface import IndirectInterface
    from org.accellera.ipxact.v1685_2022.indirect_interfaces import IndirectInterfaces

    component = _component_only(componentID)
    _assert_unique(component, "indirect_interfaces.indirect_interface", name)
    _require_text(indirectAddressRef, "indirectAddressRef")
    _require_text(indirectData, "indirectData")
    if memoryMapRef is not None:
        _require_text(memoryMapRef, "memoryMapRef")
    child = IndirectInterface(
        name=name,
        indirect_address_ref=IndirectAddressRef(field_ref=FieldRef(field_ref=indirectAddressRef)),
        indirect_data_ref=IndirectDataRef(field_ref=FieldRef(field_ref=indirectData)),
        memory_map_ref_or_transparent_bridge=[memoryMapRef] if memoryMapRef is not None else [],
    )
    return _append_child(
        _ensure_container(component, "indirect_interfaces", IndirectInterfaces), "indirect_interface", child
    )


def _add_bus_interface(
    component: ComponentType,
    name: str,
    busVLNV: Sequence[str] | str,
    role: str,
    group: str | None = None,
    interfaceMode: str | None = None,
) -> str:
    from xsdata.formats.dataclass.models.generics import AnyElement

    from org.accellera.ipxact.v1685_2022.bus_interface import BusInterface
    from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType
    from org.accellera.ipxact.v1685_2022.bus_interfaces import BusInterfaces
    from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
    from org.accellera.ipxact.v1685_2022.group import Group
    from org.accellera.ipxact.v1685_2022.monitor_interface_mode import MonitorInterfaceMode

    _assert_unique(component, "bus_interfaces.bus_interface", name)
    parts = _vlnv(busVLNV, "busVLNV")
    choice: Any
    if role == "initiator":
        choice = BusInterfaceType.Initiator()
    elif role == "target":
        choice = BusInterfaceType.Target()
    elif role == "system":
        choice = BusInterfaceType.System(group=Group(value=_require_text(group, "group")))
    elif role == "mirroredInitiator":
        choice = AnyElement(qname="{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}mirroredInitiator")
    elif role == "mirroredTarget":
        choice = BusInterfaceType.MirroredTarget()
    elif role == "mirroredSystem":
        choice = BusInterfaceType.MirroredSystem(group=Group(value=_require_text(group, "group")))
    elif role == "monitor":
        try:
            mode = MonitorInterfaceMode(interfaceMode)
        except (TypeError, ValueError) as error:
            raise TgiError("Invalid monitor interfaceMode", TgiFaultCode.INVALID_ARGUMENT) from error
        choice = BusInterfaceType.Monitor(interface_mode=mode)
    else:
        raise AssertionError(role)
    child = BusInterface(
        name=name,
        bus_type=ConfigurableLibraryRefType(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3]),
        choice=choice,
    )
    return _append_child(_ensure_container(component, "bus_interfaces", BusInterfaces), "bus_interface", child)


def addComponentInitiatorBusInterface(componentID: str, name: str, busVLNV: Sequence[str] | str) -> str:
    """Add an initiator busInterface with its bus-definition reference.

    Args:
        componentID: Handle to a component element.
        name: Bus-interface name.
        busVLNV: Four-part bus-definition VLNV.

    Returns:
        Handle to the new busInterface.

    Section: F.7.30.12.
    """
    return _add_bus_interface(_component_only(componentID), name, busVLNV, "initiator")


def addComponentMemoryMap(componentID: str, name: str) -> str:
    """Add a memoryMap with the given name.

    Args:
        componentID: Handle to a component element.
        name: Memory-map name.

    Returns:
        Handle to the new memoryMap.

    Section: F.7.30.13.
    """
    from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
    from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps

    component = _component_only(componentID)
    _assert_unique(component, "memory_maps.memory_map", name)
    child = MemoryMapType(name=name)
    handle = _append_child(_ensure_container(component, "memory_maps", MemoryMaps), "memory_map", child)
    return handle


def addComponentMirroredInitiatorBusInterface(componentID: str, name: str, busVLNV: Sequence[str] | str) -> str:
    """Add a mirrored-initiator busInterface with its bus-definition reference.

    Args:
        componentID: Handle to a component element.
        name: Bus-interface name.
        busVLNV: Four-part bus-definition VLNV.

    Returns:
        Handle to the new busInterface.

    Section: F.7.30.14.
    """
    return _add_bus_interface(_component_only(componentID), name, busVLNV, "mirroredInitiator")


def addComponentMirroredSystemBusInterface(
    componentID: str, name: str, busVLNV: Sequence[str] | str, group: str
) -> str:
    """Add a mirrored-system busInterface with its bus-definition reference and group.

    Args:
        componentID: Handle to a component element.
        name: Bus-interface name.
        busVLNV: Four-part bus-definition VLNV.
        group: Mirrored-system group name.

    Returns:
        Handle to the new busInterface.

    Section: F.7.30.15.
    """
    return _add_bus_interface(_component_only(componentID), name, busVLNV, "mirroredSystem", group)


def addComponentMirroredTargetBusInterface(componentID: str, name: str, busVLNV: Sequence[str] | str) -> str:
    """Add a mirrored-target busInterface with its bus-definition reference.

    Args:
        componentID: Handle to a component element.
        name: Bus-interface name.
        busVLNV: Four-part bus-definition VLNV.

    Returns:
        Handle to the new busInterface.

    Section: F.7.30.16.
    """
    return _add_bus_interface(_component_only(componentID), name, busVLNV, "mirroredTarget")


def addComponentMode(componentID: str, name: str) -> str:
    """Add a mode with the given name.

    Args:
        componentID: Handle to a component element.
        name: Mode name.

    Returns:
        Handle to the new mode.

    Section: F.7.30.17.
    """
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT

    component = _component_only(componentID)
    _assert_unique(component, "modes.mode", name)
    return _append_child(_ensure_container(component, "modes", CT.Modes), "mode", CT.Modes.Mode(name=name))


def addComponentMonitorBusInterface(
    componentID: str, name: str, busVLNV: Sequence[str] | str, interfaceMode: str
) -> str:
    """Add a monitor busInterface with its bus-definition reference and monitored interface mode.

    Args:
        componentID: Handle to a component element.
        name: Bus-interface name.
        busVLNV: Four-part bus-definition VLNV.
        interfaceMode: Interface mode being monitored.

    Returns:
        Handle to the new busInterface.

    Section: F.7.30.18.
    """
    return _add_bus_interface(_component_only(componentID), name, busVLNV, "monitor", interfaceMode=interfaceMode)


def addComponentOtherClockDriver(
    componentID: str,
    name: str,
    periodExpression: str,
    offsetExpression: str,
    valueExpression: str,
    durationExpression: str,
) -> str:
    """Add an otherClockDriver with its waveform expressions.

    Args:
        componentID: Handle to a component element.
        name: Clock name.
        periodExpression: Clock period expression.
        offsetExpression: Clock pulse-offset expression.
        valueExpression: Clock pulse-value expression.
        durationExpression: Clock pulse-duration expression.

    Returns:
        Handle to the new otherClockDriver.

    Section: F.7.30.19.
    """
    from org.accellera.ipxact.v1685_2022.clock_driver_type import ClockDriverType
    from org.accellera.ipxact.v1685_2022.other_clock_driver import OtherClockDriver
    from org.accellera.ipxact.v1685_2022.other_clocks import OtherClocks
    from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression

    component = _component_only(componentID)
    _assert_unique(component, "other_clock_drivers.other_clock_driver", name)
    for value, argument in (
        (periodExpression, "periodExpression"),
        (offsetExpression, "offsetExpression"),
        (valueExpression, "valueExpression"),
        (durationExpression, "durationExpression"),
    ):
        _require_text(value, argument)
    child = OtherClockDriver(
        clock_name=name,
        clock_period=ClockDriverType.ClockPeriod(value=periodExpression),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(value=offsetExpression),
        clock_pulse_value=UnsignedBitExpression(value=valueExpression),
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(value=durationExpression),
    )
    return _append_child(_ensure_container(component, "other_clock_drivers", OtherClocks), "other_clock_driver", child)


def addComponentResetType(componentID: str, name: str) -> str:
    """Add a resetType with the given name.

    Args:
        componentID: Handle to a component element.
        name: Reset-type name.

    Returns:
        Handle to the new resetType.

    Section: F.7.30.20.
    """
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT

    component = _component_only(componentID)
    _assert_unique(component, "reset_types.reset_type", name)
    return _append_child(
        _ensure_container(component, "reset_types", CT.ResetTypes), "reset_type", CT.ResetTypes.ResetType(name=name)
    )


def _add_structured_port(
    component: ComponentType,
    name: str,
    type_name: str,
    kind: str,
    direction: str | None = None,
    sub_port_name: str | None = None,
) -> str:
    from org.accellera.ipxact.v1685_2022 import ComponentPortDirectionType, StructPortTypeDefs
    from org.accellera.ipxact.v1685_2022.model_type import ModelType
    from org.accellera.ipxact.v1685_2022.port import Port
    from org.accellera.ipxact.v1685_2022.port_wire_type import PortWireType
    from org.accellera.ipxact.v1685_2022.sub_port_type import PortStructuredType, SubPortType

    _assert_unique(component, "model.ports.port", name)
    _require_text(type_name, "structPortTypeDefTypeName")
    if kind == "union":
        _require_text(sub_port_name, "subPortName")
    if kind == "interface":
        choice: Any = PortStructuredType.Interface()
        wire_direction = None
    else:
        try:
            wire_direction = ComponentPortDirectionType(direction)
        except (TypeError, ValueError) as error:
            raise TgiError("Invalid structured-port direction", TgiFaultCode.INVALID_ARGUMENT) from error
        choice = (
            PortStructuredType.Struct(direction=wire_direction)
            if kind == "struct"
            else PortStructuredType.UnionType(direction=wire_direction)
        )
    definition = StructPortTypeDefs.StructPortTypeDef(
        type_name=StructPortTypeDefs.StructPortTypeDef.TypeName(value=type_name)
    )
    structured = PortStructuredType(
        struct_or_union_or_interface=choice, struct_port_type_defs=StructPortTypeDefs(struct_port_type_def=[definition])
    )
    if sub_port_name is not None:
        sub = SubPortType(name=sub_port_name, wire_or_structured=PortWireType(direction=wire_direction))
        structured.sub_ports = PortStructuredType.SubPorts(sub_port=[sub])
    port = Port(name=name, wire_or_transactional_or_structured=structured)
    _, ports = _ensure_model_container(component, "ports", ModelType.Ports)
    handle = _append_child(ports, "port", port)
    register_parent(structured, port, ("wire_or_transactional_or_structured",), "single")
    register_parent(structured.struct_port_type_defs, structured, ("struct_port_type_defs",), "single")
    register_parent(definition, structured, ("struct_port_type_defs", "struct_port_type_def"), "list")
    if structured.sub_ports is not None:
        register_parent(structured.sub_ports, structured, ("sub_ports",), "single")
        register_parent(sub, structured, ("sub_ports", "sub_port"), "list")
    return handle


def addComponentStructuredInterfacePort(componentID: str, name: str, structPortTypeDefTypeName: str) -> str:
    """Add a structured interface port with the specified struct port type definition.

    Args:
        componentID: Handle to a component element.
        name: Port name.
        structPortTypeDefTypeName: Referenced structured type name.

    Returns:
        Handle to the new port.

    Section: F.7.30.21.
    """
    return _add_structured_port(_component_only(componentID), name, structPortTypeDefTypeName, "interface")


def addComponentStructuredStructPort(
    componentID: str, name: str, structPortTypeDefTypeName: str, direction: str
) -> str:
    """Add a structured struct port with the specified type and direction.

    Args:
        componentID: Handle to a component element.
        name: Port name.
        structPortTypeDefTypeName: Referenced structured type name.
        direction: Port direction.

    Returns:
        Handle to the new port.

    Section: F.7.30.22.
    """
    return _add_structured_port(_component_only(componentID), name, structPortTypeDefTypeName, "struct", direction)


def addComponentStructuredUnionPort(
    componentID: str, name: str, structPortTypeDefTypeName: str, subPortName: str, direction: str
) -> str:
    """Add a structured union port with its named sub-port and direction.

    Args:
        componentID: Handle to a component element.
        name: Port name.
        structPortTypeDefTypeName: Referenced structured type name.
        subPortName: Union member name.
        direction: Port direction.

    Returns:
        Handle to the new port.

    Section: F.7.30.23.
    """
    return _add_structured_port(
        _component_only(componentID), name, structPortTypeDefTypeName, "union", direction, subPortName
    )


def addComponentSystemBusInterface(componentID: str, name: str, busVLNV: Sequence[str] | str, group: str) -> str:
    """Add a system busInterface with its bus-definition reference and group.

    Args:
        componentID: Handle to a component element.
        name: Bus-interface name.
        busVLNV: Four-part bus-definition VLNV.
        group: System-interface group name.

    Returns:
        Handle to the new busInterface.

    Section: F.7.30.24.
    """
    return _add_bus_interface(_component_only(componentID), name, busVLNV, "system", group)


def addComponentTargetBusInterface(componentID: str, name: str, busVLNV: Sequence[str] | str) -> str:
    """Add a target busInterface with its bus-definition reference.

    Args:
        componentID: Handle to a component element.
        name: Bus-interface name.
        busVLNV: Four-part bus-definition VLNV.

    Returns:
        Handle to the new busInterface.

    Section: F.7.30.25.
    """
    return _add_bus_interface(_component_only(componentID), name, busVLNV, "target")


def addComponentTransactionalPort(componentID: str, name: str, initiative: str) -> str:
    """Add a transactional port with its initiative.

    Args:
        componentID: Handle to a component element.
        name: Port name.
        initiative: Port initiative value.

    Returns:
        Handle to the new port.

    Section: F.7.30.26.
    """
    from org.accellera.ipxact.v1685_2022.initiative import Initiative
    from org.accellera.ipxact.v1685_2022.initiative_type import InitiativeType
    from org.accellera.ipxact.v1685_2022.port_transactional_type import PortTransactionalType

    component = _component_only(componentID)
    _assert_unique(component, "model.ports.port", name)
    try:
        value = InitiativeType(initiative)
    except (TypeError, ValueError) as error:
        raise TgiError("Invalid port initiative", TgiFaultCode.INVALID_ARGUMENT) from error
    return _append_port(component, name, PortTransactionalType(initiative=Initiative(value=value)))


def addComponentView(componentID: str, name: str) -> str:
    """Add a view with the given name.

    Args:
        componentID: Handle to a component element.
        name: View name.

    Returns:
        Handle to the new view.

    Section: F.7.30.27.
    """
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    component = _component_only(componentID)
    _assert_unique(component, "model.views.view", name)
    model, views = _ensure_model_container(component, "views", ModelType.Views)
    return _append_child(views, "view", ModelType.Views.View(name=name))


def addComponentWirePort(componentID: str, name: str, direction: str) -> str:
    """Add a wire port with its direction.

    Args:
        componentID: Handle to a component element.
        name: Port name.
        direction: Port direction.

    Returns:
        Handle to the new port.

    Section: F.7.30.28.
    """
    from org.accellera.ipxact.v1685_2022.component_port_direction_type import ComponentPortDirectionType
    from org.accellera.ipxact.v1685_2022.port_wire_type import PortWireType

    component = _component_only(componentID)
    _assert_unique(component, "model.ports.port", name)
    try:
        value = ComponentPortDirectionType(direction)
    except (TypeError, ValueError) as error:
        raise TgiError("Invalid port direction", TgiFaultCode.INVALID_ARGUMENT) from error
    return _append_port(component, name, PortWireType(direction=value))


def _append_port(component: ComponentType, name: str, style: Any) -> str:
    from org.accellera.ipxact.v1685_2022.model_type import ModelType
    from org.accellera.ipxact.v1685_2022.port import Port

    _, ports = _ensure_model_container(component, "ports", ModelType.Ports)
    return _append_child(ports, "port", Port(name=name, wire_or_transactional_or_structured=style))


def _append_instantiation(component: ComponentType, instance: Any) -> str:
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    _, instances = _ensure_model_container(component, "instantiations", ModelType.Instantiations)
    return _append_child(
        instances, "component_instantiation_or_design_instantiation_or_design_configuration_instantiation", instance
    )


# ---------------------------------------------------------------------------
# EXTENDED (F.7.30) – removal
# ---------------------------------------------------------------------------


def removeComponentAddressSpace(addressSpaceID: str) -> bool:
    """Remove the given addressSpace element.

    Args:
        addressSpaceID: Handle to an addressSpace element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.29.
    """
    from org.accellera.ipxact.v1685_2022.address_spaces import AddressSpaces

    return _remove_child(addressSpaceID, AddressSpaces.AddressSpace, "addressSpace")


def removeComponentBusInterface(busInterfaceID: str) -> bool:
    """Remove the given busInterface element.

    Args:
        busInterfaceID: Handle to a busInterface element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.30.
    """
    from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType

    return _remove_child(busInterfaceID, BusInterfaceType, "busInterface")


def removeComponentChannel(channelID: str) -> bool:
    """Remove the given channel element.

    Args:
        channelID: Handle to a channel element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.31.
    """
    from org.accellera.ipxact.v1685_2022.channels import Channels

    return _remove_child(channelID, Channels.Channel, "channel")


def removeComponentChoice(choiceID: str) -> bool:
    """Remove the given choice element.

    Args:
        choiceID: Handle to a choice element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.32.
    """
    from org.accellera.ipxact.v1685_2022.choices import Choices

    return _remove_child(choiceID, Choices.Choice, "choice")


def removeComponentClearboxElement(clearboxElementID: str) -> bool:
    """Remove the given clearboxElement.

    Args:
        clearboxElementID: Handle to a clearboxElement element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.33.
    """
    from org.accellera.ipxact.v1685_2022.clearbox_element_type import ClearboxElementType

    return _remove_child(clearboxElementID, ClearboxElementType, "clearboxElement")


def removeComponentComponentGenerator(generatorID: str) -> bool:
    """Remove the given componentGenerator.

    Args:
        generatorID: Handle to a componentGenerator element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.34.
    """
    from org.accellera.ipxact.v1685_2022.component_generator import ComponentGenerator

    return _remove_child(generatorID, ComponentGenerator, "componentGenerator")


def removeComponentComponentInstantiation(componentInstantiationID: str) -> bool:
    """Remove the given componentInstantiation.

    Args:
        componentInstantiationID: Handle to a componentInstantiation element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.35.
    """
    from org.accellera.ipxact.v1685_2022.component_instantiation_type import ComponentInstantiationType

    return _remove_child(componentInstantiationID, ComponentInstantiationType, "componentInstantiation")


def removeComponentCpu(cpuID: str) -> bool:
    """Remove the given cpu.

    Args:
        cpuID: Handle to a cpu element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.36.
    """
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT

    return _remove_child(cpuID, CT.Cpus.Cpu, "cpu")


def removeComponentDesignConfigurationInstantiation(designConfigurationInstantiationID: str) -> bool:
    """Remove the given designConfigurationInstantiation.

    Args:
        designConfigurationInstantiationID: Handle to a designConfigurationInstantiation element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.37.
    """
    from org.accellera.ipxact.v1685_2022.design_configuration_instantiation_type import (
        DesignConfigurationInstantiationType,
    )

    return _remove_child(
        designConfigurationInstantiationID, DesignConfigurationInstantiationType, "designConfigurationInstantiation"
    )


def removeComponentDesignInstantiation(designInstantiationID: str) -> bool:
    """Remove the given designInstantiation.

    Args:
        designInstantiationID: Handle to a designInstantiation element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.38.
    """
    from org.accellera.ipxact.v1685_2022.design_instantiation_type import DesignInstantiationType

    return _remove_child(designInstantiationID, DesignInstantiationType, "designInstantiation")


def removeComponentFileSet(fileSetID: str) -> bool:
    """Remove the given fileSet.

    Args:
        fileSetID: Handle to a fileSet element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.39.
    """
    from org.accellera.ipxact.v1685_2022.file_set import FileSet

    return _remove_child(fileSetID, FileSet, "fileSet")


def removeComponentIndirectInterface(indirectInterfaceID: str) -> bool:
    """Remove the given indirectInterface.

    Args:
        indirectInterfaceID: Handle to an indirectInterface element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.40.
    """
    from org.accellera.ipxact.v1685_2022.indirect_interface import IndirectInterface

    return _remove_child(indirectInterfaceID, IndirectInterface, "indirectInterface")


def removeComponentMemoryMap(memoryMapID: str) -> bool:
    """Remove the given memoryMap.

    Args:
        memoryMapID: Handle to a memoryMap element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.41.
    """
    from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType

    return _remove_child(memoryMapID, MemoryMapType, "memoryMap")


def removeComponentMode(modeID: str) -> bool:
    """Remove the given mode from its containing component.

    Args:
        modeID: Handle to a mode element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.42.
    """
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT

    return _remove_child(modeID, CT.Modes.Mode, "mode")


def removeComponentOtherClockDriver(clockDriverID: str) -> bool:
    """Remove the given otherClockDriver.

    Args:
        clockDriverID: Handle to an otherClockDriver element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.43.
    """
    from org.accellera.ipxact.v1685_2022.other_clock_driver import OtherClockDriver

    return _remove_child(clockDriverID, OtherClockDriver, "otherClockDriver")


def removeComponentPort(portID: str) -> bool:
    """Remove the given port.

    Args:
        portID: Handle to a port element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.44.
    """
    from org.accellera.ipxact.v1685_2022.port import Port

    return _remove_child(portID, Port, "port")


def removeComponentResetType(resetTypeID: str) -> bool:
    """Remove the given resetType.

    Args:
        resetTypeID: Handle to a resetType element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.45.
    """
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT

    return _remove_child(resetTypeID, CT.ResetTypes.ResetType, "resetType")


def removeComponentView(viewID: str) -> bool:
    """Remove the given view.

    Args:
        viewID: Handle to a view element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.46.
    """
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    return _remove_child(viewID, ModelType.Views.View, "view")


def _design_for_instance(instance: Any) -> Any | None:
    from org.accellera.ipxact.v1685_2022.design import Design

    info = get_parent_info(get_handle(instance))
    parent = resolve_handle(info.parent_handle) if info is not None else None
    seen: set[int] = set()
    while parent is not None and id(parent) not in seen:
        if isinstance(parent, Design):
            _register_graph(parent)
            return parent
        seen.add(id(parent))
        parent_info = get_parent_info(get_handle(parent))
        parent = resolve_handle(parent_info.parent_handle) if parent_info is not None else None
    for handle in registry.iter_by_predicate(lambda root: isinstance(root, Design)):
        design = resolve_handle(handle)
        if design is not None and _contains_identity(design, instance):
            _register_graph(design)
            return design
    return None


def removeMemoryMapAddressUnitBits(memoryMapID: str) -> bool:
    """Remove addressUnitBits from a memoryMap or memoryMapDefinition.

    Args:
        memoryMapID: Handle to a memoryMap or memoryMapDefinition element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.47.
    """
    from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
    from org.accellera.ipxact.v1685_2022.memory_map_definitions import MemoryMapDefinitions
    from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType

    obj = resolve_handle(memoryMapID) if isinstance(memoryMapID, str) else None
    if obj is None or not isinstance(obj, (MemoryMapType, MemoryMapDefinitions.MemoryMapDefinition)):
        _fail("Invalid memoryMap handle")
    _register_owner_for(obj)
    if isinstance(obj, MemoryMapType):
        bits = next((value for value in obj.choice if isinstance(value, AddressUnitBits)), None)
        if bits is None:
            return False
        register_parent(bits, obj, ("choice",), "list")
        return detach_child_by_handle(get_handle(bits))
    bits = obj.address_unit_bits
    if bits is None:
        return False
    return detach_child_by_handle(get_handle(bits))


def _forget(obj: Any) -> bool:
    handle = get_handle(obj)
    return detach_child_by_handle(handle)


def removeModeCondition(modeID: str) -> bool:
    """Remove the condition associated with a component mode.

    Args:
        modeID: Handle to a mode element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.48.
    """
    mode = _resolve_mode(modeID)
    condition = mode.condition
    if condition is None:
        return False
    register_parent(condition, mode, ("condition",), "single")
    return detach_child_by_handle(get_handle(condition))


def removePowerDomainAlwaysOn(powerDomainID: str) -> bool:
    """Remove alwaysOn from a powerDomain element.

    Args:
        powerDomainID: Handle to a powerDomain element.

    Returns:
        True if removed; otherwise False.

    Section: F.7.30.49.
    """
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT

    domain = _resolve_typed(powerDomainID, CT.PowerDomains.PowerDomain, "powerDomain")
    value = domain.always_on
    if value is None:
        return False
    register_parent(value, domain, ("always_on",), "single")
    return detach_child_by_handle(get_handle(value))


def _set_indirect_field(handle: str, attr: str, value: str) -> bool:
    from org.accellera.ipxact.v1685_2022.indirect_interface import IndirectInterface

    interface = _resolve_typed(handle, IndirectInterface, "indirectInterface")
    value = _require_text(value, "fieldRef")
    reference = getattr(interface, attr)
    if reference.field_ref is None:
        from org.accellera.ipxact.v1685_2022.field_ref import FieldRef

        reference.field_ref = FieldRef(field_ref=value)
        register_parent(reference.field_ref, reference, ("field_ref",), "single")
    else:
        reference.field_ref.field_ref = value
    return True


def setIndirectInterfaceIndirectAddressRef(indirectInterfaceID: str, fieldRef: str) -> bool:
    """Set the fieldRef node on an indirectAddressRef.

    Args:
        indirectInterfaceID: Handle to an indirectInterface element.
        fieldRef: Field name for the indirect address reference.

    Returns:
        True when set.

    Section: F.7.30.50.
    """
    return _set_indirect_field(indirectInterfaceID, "indirect_address_ref", fieldRef)


def setIndirectInterfaceIndirectDataRef(indirectInterfaceID: str, fieldRef: str) -> bool:
    """Set the fieldRef node on an indirectDataRef.

    Args:
        indirectInterfaceID: Handle to an indirectInterface element.
        fieldRef: Field name for the indirect data reference.

    Returns:
        True when set.

    Section: F.7.30.51.
    """
    return _set_indirect_field(indirectInterfaceID, "indirect_data_ref", fieldRef)


def _memory_map(handle: str) -> Any:
    from org.accellera.ipxact.v1685_2022.memory_map_definitions import MemoryMapDefinitions
    from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType

    return _resolve_typed(handle, (MemoryMapType, MemoryMapDefinitions.MemoryMapDefinition), "memoryMap")


def setMemoryMapAddressUnitBits(memoryMapID: str, addressUnitBit: str) -> bool:
    """Set addressUnitBits on a memoryMap or memoryMapDefinition.

    Args:
        memoryMapID: Handle to a memoryMap or memoryMapDefinition element.
        addressUnitBit: Positive addressUnitBits expression.

    Returns:
        True when set.

    Section: F.7.30.52.
    """
    from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
    from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
    from org.accellera.ipxact.v1685_2022.shared_type import SharedType

    memory_map = _memory_map(memoryMapID)
    expression = _validated_expression(addressUnitBit, "addressUnitBit", 1, (1 << 63) - 1)
    if isinstance(memory_map, MemoryMapType):
        from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType

        if any(isinstance(item, MemoryMapType.MemoryMapDefinitionRef) for item in memory_map.choice):
            raise TgiError("addressUnitBits cannot be set on a memoryMapDefinitionRef", TgiFaultCode.INVALID_ARGUMENT)
        wrapper = next((item for item in memory_map.choice if isinstance(item, AddressUnitBits)), None)
        if wrapper is None:
            wrapper = AddressUnitBits(value=expression)
            choice = _list_attr(memory_map, "choice")
            index = next((i for i, item in enumerate(choice) if isinstance(item, SharedType)), len(choice))
            choice.insert(index, wrapper)
            register_parent(wrapper, memory_map, ("choice",), "list")
        else:
            wrapper.value = expression
    else:
        wrapper = memory_map.address_unit_bits
        if wrapper is None:
            memory_map.address_unit_bits = AddressUnitBits(value=expression)
            register_parent(memory_map.address_unit_bits, memory_map, ("address_unit_bits",), "single")
        else:
            wrapper.value = expression
    return True


def _set_mode_condition_value(value: str) -> str:
    value = _require_text(value, "condition")
    resolved = _try_evaluate_expression(value)
    if resolved is not None and resolved not in (0, 1):
        raise TgiError("Mode condition must resolve to unsigned bit 0 or 1", TgiFaultCode.INVALID_ARGUMENT)
    return value


def setModeCondition(modeID: str, condition: str) -> bool:
    """Set the condition expression on a component mode.

    Args:
        modeID: Handle to a mode element.
        condition: Unsigned-bit condition expression.

    Returns:
        True when set.

    Section: F.7.30.53.
    """
    from org.accellera.ipxact.v1685_2022.unresolved_unsigned_bit_expression import UnresolvedUnsignedBitExpression

    mode = _resolve_mode(modeID)
    expression = _set_mode_condition_value(condition)
    if mode.condition is None:
        mode.condition = UnresolvedUnsignedBitExpression(value=expression)
        register_parent(mode.condition, mode, ("condition",), "single")
    else:
        mode.condition.value = expression
    return True


def setModeName(modeID: str, name: str) -> bool:
    """Set the name of a component mode.

    Args:
        modeID: Handle to a mode element.
        name: Mode name.

    Returns:
        True when set.

    Section: F.7.30.54.
    """
    mode = _resolve_mode(modeID)
    name = _require_text(name, "name")
    owner = _register_owner_for(mode)
    if owner is not None:
        for sibling in _value_list(owner, "modes.mode"):
            if sibling is not mode and sibling.name == name:
                raise TgiError(f"Duplicate mode name {name!r}", TgiFaultCode.ALREADY_EXISTS)
    mode.name = name
    return True
