"""Design configuration category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.39) and EXTENDED (F.7.40) functions for
``designConfiguration``. Only the public TGI API ("no more, no less") is
exported. Mutators return ``True`` on success and raise :class:`TgiError` with
``TgiFaultCode.INVALID_ID`` for invalid handles. If an element to remove is not
found the function returns ``False`` without raising.

Helper functions are prefixed with ``_`` and intentionally excluded from the
public API surface.
"""
# ruff: noqa: I001

import re

from org.accellera.ipxact.v1685_2022 import (
    Abstractor,
    Choices,
    ConfigurableElementValue,
    ConfigurableLibraryRefType,
    Design,
    DesignConfiguration,
    DesignConfigurationInstantiationType,
    GeneratorChain,
    InstanceName,
    LibraryRefType,
)

from ._expressions import _xml_text
from ._model import _owned_list_ids, _walk_model
from .address_space import _register_owned_child
from .instantiation import (
    _registered_reference_target, _validated_vlnv, getAbstractorInstanceAbstractorRefID,
    _validate_local_reference_name,
    getDesignConfigurationInstantiationDesignConfigurationRefByID,
)
from .name_group import _name_text, getName
from .design import getDesignInterconnectionIDs, getDesignMonitorInterconnectionIDs
from .configurable_element import getConfigurableElementValueIDs

from .core import (
    _HANDLE_MANAGER,
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.39)
    "getAbstractorInstanceAbstractorRefByID",
    "getAbstractorInstanceAbstractorRefByVLNV",
    "getAbstractorInstanceInstanceName",
    "getAbstractorInstanceViewName",
    "getAbstractorInstancesAbstractorInstanceIDs",
    "getAbstractorInstancesInterfaceRefIDs",
    "getDesignConfigurationChoiceIDs",
    "getDesignConfigurationDesignRefByID",
    "getDesignConfigurationDesignRefByVLNV",
    "getDesignConfigurationGeneratorChainConfigurationIDs",
    "getDesignConfigurationInterconnectionConfigurationIDs",
    "getDesignConfigurationViewConfigurationIDs",
    "getGeneratorChainConfigurationRefByID",
    "getGeneratorChainConfigurationRefByVLNV",
    "getInterconnectionConfigurationAbstractorsInstancesIDs",
    "getInterconnectionConfigurationInterconnectionRefByID",
    "getInterconnectionConfigurationInterconnectionRefByName",
    "getViewConfigurationConfigurableElementValueIDs",
    "getViewConfigurationInstanceName",
    "getViewConfigurationViewID",
    "getViewConfigurationViewRefByName",
    # EXTENDED (F.7.40)
    "addAbstractorInstancesAbstractorInstance",
    "addAbstractorInstancesInterfaceRef",
    "addDesignConfChoice",  # spec naming retained
    "addDesignConfigurationGeneratorChainConfiguration",
    "addDesignConfigurationInterconnectionConfiguration",
    "addDesignConfigurationViewConfiguration",
    "addInterconnectionConfigurationAbstractorInstances",
    "removeAbstractorInstancesAbstractorInstance",
    "removeAbstractorInstancesInterfaceRef",
    "removeDesignConfChoice",
    "removeDesignConfigurationDesignRef",
    "removeDesignConfigurationGeneratorChainConfiguration",
    "removeDesignConfigurationInterconnectionConfiguration",
    "removeDesignConfigurationViewConfiguration",
    "removeInterconnectionConfigurationAbstractorInstances",
    "removeViewConfigurationConfigurableElementValue",
    "setAbstractorInstanceAbstractorRef",
    "setAbstractorInstanceInstanceName",
    "setAbstractorInstanceViewName",
    "setDesignConfigurationDesignRef",
    "setInterconnectionConfigurationInterconnectionRef",
    "setViewConfigurationInstanceName",
    "setViewConfigurationView",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------

def _resolve(dcID: str) -> DesignConfiguration | None:
    obj = resolve_handle(dcID)
    return obj if isinstance(obj, DesignConfiguration) else None


def _resolve_interconnection_configuration(icID: str) -> DesignConfiguration.InterconnectionConfiguration | None:
    obj = resolve_handle(icID)
    return obj if isinstance(obj, DesignConfiguration.InterconnectionConfiguration) else None


def _resolve_abstractor_instances(
    aiID: str,
) -> DesignConfiguration.InterconnectionConfiguration.AbstractorInstances | None:
    obj = resolve_handle(aiID)
    return (
        obj
        if isinstance(
            obj,
            DesignConfiguration.InterconnectionConfiguration.AbstractorInstances,
        )
        else None
    )


def _resolve_abstractor_instance(
    instID: str,
) -> (
    DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance
    | None
):
    obj = resolve_handle(instID)
    return (
        obj
        if isinstance(
            obj,
            DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance,
        )
        else None
    )


def _resolve_interface_ref(
    irID: str,
) -> DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.InterfaceRef | None:
    obj = resolve_handle(irID)
    return (
        obj
        if isinstance(
            obj,
            DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.InterfaceRef,
        )
        else None
    )


def _resolve_view_configuration(vcID: str) -> DesignConfiguration.ViewConfiguration | None:
    obj = resolve_handle(vcID)
    return obj if isinstance(obj, DesignConfiguration.ViewConfiguration) else None


def _resolve_configurable_element_value(cevID: str) -> ConfigurableElementValue | None:
    obj = resolve_handle(cevID)
    return obj if isinstance(obj, ConfigurableElementValue) else None


def _abstractor_name(owner: object, value: str) -> str:
    return _name_text(owner, _xml_text(value))


def _abstractor_scope(owner: object) -> object:
    scope = owner
    seen: set[int] = set()
    while not isinstance(scope, DesignConfiguration):
        if id(scope) in seen:
            raise TgiError("Cyclic abstractor ownership", TgiFaultCode.INVALID_ID)
        seen.add(id(scope))
        parent = _register_owned_child(scope)
        if parent is None:
            break
        scope = parent
    return scope


def _unique_abstractor_name(owner: object, name: str, current: object | None = None) -> None:
    for child, _, _, _ in _walk_model(_abstractor_scope(owner)):
        if (
            isinstance(child, DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance)
            and child is not current
            and _abstractor_name(child, child.instance_name) == name
        ):
            raise TgiError("Abstractor instance name already exists", TgiFaultCode.ALREADY_EXISTS)


def _xml_vlnv(value: tuple[str, str, str, str]) -> tuple[str, str, str, str]:
    parts = _validated_vlnv(value)
    for part in parts:
        _xml_text(part)
    return parts


def _set_reference[T: (LibraryRefType, ConfigurableLibraryRefType)](
    owner: object, attribute: str, model_type: type[T], value: tuple[str, str, str, str]
) -> T:
    parts = _xml_vlnv(value)
    ref = getattr(owner, attribute)
    if ref is not None and not isinstance(ref, model_type):
        raise TgiError(f"Invalid {attribute} model", TgiFaultCode.INVALID_ID)
    if ref is None:
        ref = model_type(vendor=parts[0], library=parts[1], name=parts[2], version=parts[3])
        setattr(owner, attribute, ref)
    else:
        ref.vendor, ref.library, ref.name, ref.version = parts
    register_parent(ref, owner, (attribute,), "single")
    return ref


def _generator_reference(handle: str) -> ConfigurableLibraryRefType | None:
    ref = resolve_handle(handle)
    if not isinstance(ref, ConfigurableLibraryRefType):
        return None
    owner = _register_owned_child(ref, DesignConfiguration)
    if not isinstance(owner, DesignConfiguration) or not any(
        child is ref for child in owner.generator_chain_configuration
    ):
        return None
    register_parent(ref, owner, ("generator_chain_configuration",), "list")
    return ref


def _configuration_document(handle: str) -> DesignConfiguration:
    obj = resolve_handle(handle)
    if isinstance(obj, DesignConfigurationInstantiationType):
        obj = resolve_handle(getDesignConfigurationInstantiationDesignConfigurationRefByID(handle))
    if not isinstance(obj, DesignConfiguration):
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    return obj


def _unique_interconnection_ref(
    owner: DesignConfiguration | DesignConfiguration.InterconnectionConfiguration,
    reference: str,
    current: DesignConfiguration.InterconnectionConfiguration | None = None,
) -> None:
    scope = owner if isinstance(owner, DesignConfiguration) else _register_owned_child(owner, DesignConfiguration)
    if isinstance(scope, DesignConfiguration) and any(
        child is not current and _abstractor_name(child, child.interconnection_ref) == reference
        for child in scope.interconnection_configuration
    ):
        raise TgiError("Interconnection reference already configured", TgiFaultCode.ALREADY_EXISTS)


def _view_reference_text(value: str) -> str:
    value = re.sub(r"[\t\r\n ]+", " ", _xml_text(value)).strip(" ")
    _validate_local_reference_name(value, "NMTOKEN")
    return value


# ---------------------------------------------------------------------------
# BASE (F.7.39)
# ---------------------------------------------------------------------------

def getAbstractorInstanceAbstractorRefByID(abstractorInstanceID: str) -> str:
    """Return the handle of the abstractor referenced by an abstractorInstance.

    Section: F.7.39.1. A missing or wrong-kind target raises NOT_FOUND.
    """
    ref_id = getAbstractorInstanceAbstractorRefID(abstractorInstanceID)
    ref = resolve_handle(ref_id) if ref_id is not None else None
    if ref is not None and not isinstance(ref, ConfigurableLibraryRefType):
        raise TgiError("Invalid abstractorRef model", TgiFaultCode.INVALID_ID)
    return get_handle(_registered_reference_target(ref, Abstractor, "abstractorRef"))


def getAbstractorInstanceAbstractorRefByVLNV(
    abstractorInstanceID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return (vendor, library, name, version) of the abstractorRef.

    Section: F.7.39.2.
    """
    ref_id = getAbstractorInstanceAbstractorRefID(abstractorInstanceID)
    if ref_id is None:
        return (None, None, None, None)
    ref = resolve_handle(ref_id)
    if not isinstance(ref, ConfigurableLibraryRefType):
        raise TgiError("Invalid abstractorRef model", TgiFaultCode.INVALID_ID)
    return (ref.vendor, ref.library, ref.name, ref.version)


def getAbstractorInstanceInstanceName(abstractorInstanceID: str) -> str | None:
    """Return instanceName of an abstractorInstance.

    Section: F.7.39.3.
    """
    inst = _resolve_abstractor_instance(abstractorInstanceID)
    if inst is None:
        raise TgiError("Invalid abstractorInstance handle", TgiFaultCode.INVALID_ID)
    return inst.instance_name


def getAbstractorInstanceViewName(abstractorInstanceID: str) -> str | None:
    """Return viewName of an abstractorInstance.

    Section: F.7.39.4.
    """
    inst = _resolve_abstractor_instance(abstractorInstanceID)
    if inst is None:
        raise TgiError("Invalid abstractorInstance handle", TgiFaultCode.INVALID_ID)
    return inst.view_name


def getAbstractorInstancesAbstractorInstanceIDs(abstractorInstancesID: str) -> list[str]:
    """Return handles of ``abstractorInstance`` children within an abstractorInstances container.

    Section: F.7.39.5.
    """
    ai = _resolve_abstractor_instances(abstractorInstancesID)
    if ai is None:
        raise TgiError("Invalid abstractorInstances handle", TgiFaultCode.INVALID_ID)
    return _owned_list_ids(ai, ai.abstractor_instance, "abstractor_instance")


def getAbstractorInstancesInterfaceRefIDs(abstractorInstancesID: str) -> list[str]:
    """Return handles of ``interfaceRef`` elements under an abstractorInstances.

    Section: F.7.39.6.
    """
    ai = _resolve_abstractor_instances(abstractorInstancesID)
    if ai is None:
        raise TgiError("Invalid abstractorInstances handle", TgiFaultCode.INVALID_ID)
    return _owned_list_ids(ai, ai.interface_ref, "interface_ref")


def getDesignConfigurationChoiceIDs(designConfigurationID: str) -> list[str]:
    """Return handles of ``choice`` elements.

    Section: F.7.39.7.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    if dc.choices is None:
        return []
    return [get_handle(c) for c in getattr(dc.choices, "choice", [])]


def getDesignConfigurationDesignRefByID(designConfigurationID: str) -> str:
    """Return the handle of the design referenced by ``designRef``.

    Section: F.7.39.8. Missing or wrong-kind targets raise NOT_FOUND.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    dr = dc.design_ref
    if dr is not None:
        if not isinstance(dr, LibraryRefType):
            raise TgiError("Invalid designRef model", TgiFaultCode.INVALID_ID)
        register_parent(dr, dc, ("design_ref",), "single")
    return get_handle(_registered_reference_target(dr, Design, "designRef"))


def getDesignConfigurationDesignRefByVLNV(
    designConfigurationID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return designRef VLNV tuple.

    Section: F.7.39.9.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    dr = dc.design_ref
    if dr is None:
        return (None, None, None, None)
    if not isinstance(dr, LibraryRefType):
        raise TgiError("Invalid designRef model", TgiFaultCode.INVALID_ID)
    register_parent(dr, dc, ("design_ref",), "single")
    return (dr.vendor, dr.library, dr.name, dr.version)


def getDesignConfigurationGeneratorChainConfigurationIDs(designConfigurationID: str) -> list[str]:
    """Return handles of ``generatorChainConfiguration`` entries.

    Section: F.7.39.10.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    return _owned_list_ids(dc, dc.generator_chain_configuration, "generator_chain_configuration")


def getDesignConfigurationInterconnectionConfigurationIDs(designConfigurationID: str) -> list[str]:
    """Return handles of ``interconnectionConfiguration`` entries.

    Section: F.7.39.11.
    """
    dc = _configuration_document(designConfigurationID)
    return _owned_list_ids(dc, dc.interconnection_configuration, "interconnection_configuration")


def getDesignConfigurationViewConfigurationIDs(designConfigurationID: str) -> list[str]:
    """Return handles of ``viewConfiguration`` entries.

    Section: F.7.39.12.
    """
    dc = _configuration_document(designConfigurationID)
    return _owned_list_ids(dc, dc.view_configuration, "view_configuration")


def getGeneratorChainConfigurationRefByID(generatorChainConfigurationID: str) -> str:
    """Return the handle of the referenced generatorChain object.

    Section: F.7.39.13. Missing or wrong-kind targets raise NOT_FOUND.
    """
    obj = _generator_reference(generatorChainConfigurationID)
    if obj is None:
        raise TgiError("Invalid generatorChainConfiguration handle", TgiFaultCode.INVALID_ID)
    return get_handle(_registered_reference_target(obj, GeneratorChain, "generatorChainConfiguration"))


def getGeneratorChainConfigurationRefByVLNV(
    generatorChainConfigurationID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return VLNV of a generatorChainConfiguration reference.

    Section: F.7.39.14.
    """
    obj = _generator_reference(generatorChainConfigurationID)
    if obj is None:
        raise TgiError("Invalid generatorChainConfiguration handle", TgiFaultCode.INVALID_ID)
    return (obj.vendor, obj.library, obj.name, obj.version)


def getInterconnectionConfigurationAbstractorsInstancesIDs(interconnectionConfigurationID: str) -> list[str]:
    """Return handles of ``abstractorInstances`` groups under an interconnectionConfiguration.

    Section: F.7.39.15.
    """
    ic = _resolve_interconnection_configuration(interconnectionConfigurationID)
    if ic is None:
        raise TgiError("Invalid interconnectionConfiguration handle", TgiFaultCode.INVALID_ID)
    return _owned_list_ids(ic, ic.abstractor_instances, "abstractor_instances")


def getInterconnectionConfigurationInterconnectionRefByID(interconnectionConfigurationID: str) -> str:
    """Return the handle of the referenced design interconnection.

    Section: F.7.39.16. Missing or ambiguous names raise NOT_FOUND.
    """
    ic = _resolve_interconnection_configuration(interconnectionConfigurationID)
    if ic is None:
        raise TgiError("Invalid interconnectionConfiguration handle", TgiFaultCode.INVALID_ID)
    dc = _register_owned_child(ic, DesignConfiguration)
    if not isinstance(dc, DesignConfiguration):
        raise TgiError("Interconnection configuration has no owning designConfiguration", TgiFaultCode.NOT_FOUND)
    design_id = getDesignConfigurationDesignRefByID(get_handle(dc))
    name = _abstractor_name(ic, ic.interconnection_ref)
    candidates = [
        child_id
        for child_id in [*getDesignInterconnectionIDs(design_id), *getDesignMonitorInterconnectionIDs(design_id)]
        if (child_name := getName(child_id)) is not None
        and _abstractor_name(resolve_handle(child_id), child_name) == name
    ]
    if len(candidates) != 1:
        raise TgiError("Referenced interconnection is missing or ambiguous", TgiFaultCode.NOT_FOUND)
    return candidates[0]


def getInterconnectionConfigurationInterconnectionRefByName(interconnectionConfigurationID: str) -> str | None:
    """Return the stored interconnectionRef name.

    Section: F.7.39.17.
    """
    ic = _resolve_interconnection_configuration(interconnectionConfigurationID)
    if ic is None:
        raise TgiError("Invalid interconnectionConfiguration handle", TgiFaultCode.INVALID_ID)
    return ic.interconnection_ref


def getViewConfigurationConfigurableElementValueIDs(viewConfigurationID: str) -> list[str]:
    """Return handles of configurableElementValue children within a viewConfiguration's view.

    Section: F.7.39.18.
    """
    vc = _resolve_view_configuration(viewConfigurationID)
    if vc is None:
        raise TgiError("Invalid viewConfiguration handle", TgiFaultCode.INVALID_ID)
    if vc.view is None:
        return []
    return getConfigurableElementValueIDs(viewConfigurationID)


def getViewConfigurationInstanceName(viewConfigurationID: str) -> str | None:
    """Return instanceName for a viewConfiguration.

    Section: F.7.39.19.
    """
    vc = _resolve_view_configuration(viewConfigurationID)
    if vc is None:
        raise TgiError("Invalid viewConfiguration handle", TgiFaultCode.INVALID_ID)
    inst = vc.instance_name
    if inst is None:
        return None
    if not isinstance(inst, InstanceName):
        raise TgiError("Invalid instanceName model", TgiFaultCode.INVALID_ID)
    register_parent(inst, vc, ("instance_name",), "single")
    return inst.value


def getViewConfigurationViewID(viewConfigurationID: str) -> str | None:
    """Return handle of the ``view`` element of a viewConfiguration.

    Section: F.7.39.20.
    """
    vc = _resolve_view_configuration(viewConfigurationID)
    if vc is None:
        raise TgiError("Invalid viewConfiguration handle", TgiFaultCode.INVALID_ID)
    view = vc.view
    if view is not None:
        if not isinstance(view, DesignConfiguration.ViewConfiguration.View):
            raise TgiError("Invalid view model", TgiFaultCode.INVALID_ID)
        register_parent(view, vc, ("view",), "single")
    return None if view is None else get_handle(view)


def getViewConfigurationViewRefByName(viewConfigurationID: str) -> str | None:
    """Return the stored viewRef from a viewConfiguration or view element (F.7.39.21)."""
    obj = resolve_handle(viewConfigurationID)
    if isinstance(obj, DesignConfiguration.ViewConfiguration.View):
        return obj.view_ref
    view_id = getViewConfigurationViewID(viewConfigurationID)
    view = resolve_handle(view_id) if view_id is not None else None
    return view.view_ref if isinstance(view, DesignConfiguration.ViewConfiguration.View) else None


# ---------------------------------------------------------------------------
# EXTENDED (F.7.40)
# ---------------------------------------------------------------------------

def addAbstractorInstancesAbstractorInstance(
    abstractorInstancesID: str,
    abstractorVLNV: tuple[str, str, str, str],
    instanceName: str,
    viewName: str,
) -> str:
    """Create and append an ``abstractorInstance``.

    Section: F.7.40.1. Arguments follow the standard's VLNV, instanceName,
    viewName order after the containing abstractorInstances handle.
    """
    ai = _resolve_abstractor_instances(abstractorInstancesID)
    if ai is None:
        raise TgiError("Invalid abstractorInstances handle", TgiFaultCode.INVALID_ID)
    name = _abstractor_name(ai, instanceName)
    view = _abstractor_name(ai, viewName)
    parts = _xml_vlnv(abstractorVLNV)
    _unique_abstractor_name(ai, name)
    inst = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance(
        instance_name=name,
        view_name=view,
        abstractor_ref=ConfigurableLibraryRefType(
            vendor=parts[0],
            library=parts[1],
            name=parts[2],
            version=parts[3],
        ),
    )
    ai.abstractor_instance = [*ai.abstractor_instance, inst]
    register_parent(inst, ai, ("abstractor_instance",), "list")
    register_parent(inst.abstractor_ref, inst, ("abstractor_ref",), "single")
    return get_handle(inst)


def addAbstractorInstancesInterfaceRef(
    abstractorInstancesID: str, componentRef: str, busRef: str
) -> str:
    """Add an interfaceRef to an abstractorInstances container.

    Section: F.7.40.2.
    """
    ai = _resolve_abstractor_instances(abstractorInstancesID)
    if ai is None:
        raise TgiError("Invalid abstractorInstances handle", TgiFaultCode.INVALID_ID)
    component = _abstractor_name(ai, componentRef)
    bus = _abstractor_name(ai, busRef)
    scope = _register_owned_child(ai, DesignConfiguration.InterconnectionConfiguration) or ai
    for child, _, _, _ in _walk_model(scope):
        if (
            isinstance(child, DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.InterfaceRef)
            and (_abstractor_name(child, child.component_ref), _abstractor_name(child, child.bus_ref))
            == (component, bus)
        ):
            raise TgiError(
                "Interface endpoint already configured for this interconnection", TgiFaultCode.ALREADY_EXISTS
            )
    ir = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.InterfaceRef(
        component_ref=component, bus_ref=bus
    )
    ai.interface_ref = [*ai.interface_ref, ir]
    register_parent(ir, ai, ("interface_ref",), "list")
    return get_handle(ir)


def addDesignConfChoice(designConfigurationID: str, name: str) -> str:
    """Add a ``choice`` element to the designConfiguration.

    Section: F.7.40.3.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    if dc.choices is None:
        dc.choices = Choices(choice=[])
    ch = Choices.Choice(name=name)
    dc.choices.choice.append(ch)  # type: ignore[attr-defined]
    register_parent(ch, dc, ("choices",), "list")
    return get_handle(ch)


def addDesignConfigurationGeneratorChainConfiguration(
    designConfigurationID: str, vlnv: tuple[str, str, str, str]
) -> str:
    """Append a generatorChainConfiguration reference.

    Section: F.7.40.4.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    parts = _xml_vlnv(vlnv)
    if any((ref.vendor, ref.library, ref.name, ref.version) == parts for ref in dc.generator_chain_configuration):
        raise TgiError("Generator chain reference already configured", TgiFaultCode.ALREADY_EXISTS)
    ref = ConfigurableLibraryRefType(
        vendor=parts[0], library=parts[1], name=parts[2], version=parts[3]
    )
    dc.generator_chain_configuration = [*dc.generator_chain_configuration, ref]
    register_parent(ref, dc, ("generator_chain_configuration",), "list")
    return get_handle(ref)


def addDesignConfigurationInterconnectionConfiguration(
    designConfigurationID: str, interconnectionRef: str,
    abstractorVLNV: tuple[str, str, str, str], instanceName: str, viewName: str,
) -> str:
    """Create an interconnectionConfiguration with the given ref and abstractor.

    Section: F.7.40.5.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    reference = _abstractor_name(dc, interconnectionRef)
    _unique_interconnection_ref(dc, reference)
    ic = DesignConfiguration.InterconnectionConfiguration(
        interconnection_ref=reference
    )
    ic_id = get_handle(ic)
    register_parent(ic, dc, ("interconnection_configuration",), "list")
    try:
        addInterconnectionConfigurationAbstractorInstances(ic_id, abstractorVLNV, instanceName, viewName)
    except TgiError:
        _HANDLE_MANAGER.forget(ic_id)
        raise
    dc.interconnection_configuration = [*dc.interconnection_configuration, ic]
    return ic_id


def addDesignConfigurationViewConfiguration(
    designConfigurationID: str, instanceName: str, viewRef: str
) -> str:
    """Add a viewConfiguration selecting a viewRef for an instance.

    Section: F.7.40.6.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    vc = DesignConfiguration.ViewConfiguration(
        instance_name=InstanceName(value=instanceName),
        view=DesignConfiguration.ViewConfiguration.View(view_ref=viewRef),
    )
    dc.view_configuration.append(vc)  # type: ignore[attr-defined]
    register_parent(vc, dc, ("view_configuration",), "list")
    return get_handle(vc)


def addInterconnectionConfigurationAbstractorInstances(
    interconnectionConfigurationID: str,
    abstractorVLNV: tuple[str, str, str, str],
    instanceName: str,
    viewName: str,
) -> str:
    """Append an ``abstractorInstances`` grouping containing the given abstractor.

    Section: F.7.40.7.
    """
    ic = _resolve_interconnection_configuration(interconnectionConfigurationID)
    if ic is None:
        raise TgiError("Invalid interconnectionConfiguration handle", TgiFaultCode.INVALID_ID)
    name = _abstractor_name(ic, instanceName)
    _unique_abstractor_name(ic, name)
    grp = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances()
    group_id = get_handle(grp)
    try:
        addAbstractorInstancesAbstractorInstance(group_id, abstractorVLNV, name, viewName)
    except TgiError:
        _HANDLE_MANAGER.forget(group_id)
        raise
    ic.abstractor_instances = [*ic.abstractor_instances, grp]
    register_parent(grp, ic, ("abstractor_instances",), "list")
    return group_id


def removeAbstractorInstancesAbstractorInstance(abstractorInstanceID: str) -> bool:
    """Remove an abstractorInstance.

    Section: F.7.40.8. Returns False if handle invalid or not found under its parent.
    The section's input label says abstractorInstancesID; its description
    identifies the individual abstractorInstance to remove.
    """
    inst = _resolve_abstractor_instance(abstractorInstanceID)
    if inst is None:
        return False
    if _register_owned_child(inst, DesignConfiguration.InterconnectionConfiguration.AbstractorInstances) is None:
        return False
    return detach_child_by_handle(abstractorInstanceID)


def removeAbstractorInstancesInterfaceRef(interfaceRefID: str) -> bool:
    """Remove an interfaceRef.

    Section: F.7.40.9.
    """
    ir = _resolve_interface_ref(interfaceRefID)
    if ir is None:
        return False
    if _register_owned_child(ir, DesignConfiguration.InterconnectionConfiguration.AbstractorInstances) is None:
        return False
    return detach_child_by_handle(interfaceRefID)


def removeDesignConfChoice(choiceID: str) -> bool:
    """Remove a design configuration choice.

    Section: F.7.40.10.
    """
    obj = resolve_handle(choiceID)
    # Validate it is a Choices.Choice instance
    if not isinstance(obj, Choices.Choice):  # type: ignore[attr-defined]
        return False
    return detach_child_by_handle(choiceID)


def removeDesignConfigurationDesignRef(designConfigurationID: str) -> bool:
    """Remove the designRef element.

    Section: F.7.40.11.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    if dc.design_ref is None:
        return False
    if not isinstance(dc.design_ref, LibraryRefType):
        raise TgiError("Invalid designRef model", TgiFaultCode.INVALID_ID)
    register_parent(dc.design_ref, dc, ("design_ref",), "single")
    return detach_child_by_handle(get_handle(dc.design_ref))


def removeDesignConfigurationGeneratorChainConfiguration(generatorChainConfigurationID: str) -> bool:
    """Remove a generatorChainConfiguration reference.

    Section: F.7.40.12.
    """
    obj = _generator_reference(generatorChainConfigurationID)
    if obj is None:
        return False
    return detach_child_by_handle(generatorChainConfigurationID)


def removeDesignConfigurationInterconnectionConfiguration(interconnectionConfigurationID: str) -> bool:
    """Remove an interconnectionConfiguration element.

    Section: F.7.40.13.
    """
    ic = _resolve_interconnection_configuration(interconnectionConfigurationID)
    if ic is None:
        return False
    if _register_owned_child(ic, DesignConfiguration) is None:
        return False
    return detach_child_by_handle(interconnectionConfigurationID)


def removeDesignConfigurationViewConfiguration(viewConfigurationID: str) -> bool:
    """Remove a viewConfiguration element.

    Section: F.7.40.14.
    """
    vc = _resolve_view_configuration(viewConfigurationID)
    if vc is None:
        return False
    return detach_child_by_handle(viewConfigurationID)


def removeInterconnectionConfigurationAbstractorInstances(abstractorInstancesID: str) -> bool:
    """Remove an abstractorInstances grouping.

    Section: F.7.40.15.
    """
    ai = _resolve_abstractor_instances(abstractorInstancesID)
    if ai is None:
        return False
    if _register_owned_child(ai, DesignConfiguration.InterconnectionConfiguration) is None:
        return False
    return detach_child_by_handle(abstractorInstancesID)


def removeViewConfigurationConfigurableElementValue(configurableElementValueID: str) -> bool:
    """Remove a configurableElementValue.

    Section: F.7.40.16.
    """
    cev = _resolve_configurable_element_value(configurableElementValueID)
    if cev is None:
        return False
    return detach_child_by_handle(configurableElementValueID)


def setAbstractorInstanceAbstractorRef(
    abstractorInstanceID: str, vlnv: tuple[str, str, str, str]
) -> bool:
    """Set the abstractorRef VLNV, preserving its configurable values and handle.

    Section: F.7.40.17.
    """
    inst = _resolve_abstractor_instance(abstractorInstanceID)
    if inst is None:
        raise TgiError("Invalid abstractorInstance handle", TgiFaultCode.INVALID_ID)
    _set_reference(inst, "abstractor_ref", ConfigurableLibraryRefType, vlnv)
    return True


def setAbstractorInstanceInstanceName(abstractorInstanceID: str, instanceName: str) -> bool:
    """Set instanceName of an abstractorInstance.

    Section: F.7.40.18.
    """
    inst = _resolve_abstractor_instance(abstractorInstanceID)
    if inst is None:
        raise TgiError("Invalid abstractorInstance handle", TgiFaultCode.INVALID_ID)
    name = _abstractor_name(inst, instanceName)
    _unique_abstractor_name(inst, name, inst)
    inst.instance_name = name
    return True


def setAbstractorInstanceViewName(abstractorInstanceID: str, viewName: str) -> bool:
    """Set viewName of an abstractorInstance.

    Section: F.7.40.19.
    """
    inst = _resolve_abstractor_instance(abstractorInstanceID)
    if inst is None:
        raise TgiError("Invalid abstractorInstance handle", TgiFaultCode.INVALID_ID)
    inst.view_name = _abstractor_name(inst, viewName)
    return True


def setDesignConfigurationDesignRef(
    designConfigurationID: str, vlnv: tuple[str, str, str, str]
) -> bool:
    """Set (or create) the designRef reference.

    Section: F.7.40.20.
    """
    dc = _resolve(designConfigurationID)
    if dc is None:
        raise TgiError("Invalid designConfiguration handle", TgiFaultCode.INVALID_ID)
    _set_reference(dc, "design_ref", LibraryRefType, vlnv)
    return True


def setInterconnectionConfigurationInterconnectionRef(
    interconnectionConfigurationID: str, interconnectionRef: str,
) -> bool:
    """Set the interconnectionRef XML Name (F.7.40.21)."""
    ic = _resolve_interconnection_configuration(interconnectionConfigurationID)
    if ic is None:
        raise TgiError("Invalid interconnectionConfiguration handle", TgiFaultCode.INVALID_ID)
    reference = _abstractor_name(ic, interconnectionRef)
    _unique_interconnection_ref(ic, reference, ic)
    ic.interconnection_ref = reference
    return True


def setViewConfigurationInstanceName(viewConfigurationID: str, instanceName: str) -> bool:
    """Set the instanceName XML Name, preserving its wrapper (F.7.40.22)."""
    vc = _resolve_view_configuration(viewConfigurationID)
    if vc is None:
        raise TgiError("Invalid viewConfiguration handle", TgiFaultCode.INVALID_ID)
    name = _abstractor_name(vc, instanceName)
    scope = _register_owned_child(vc, DesignConfiguration)
    if isinstance(scope, DesignConfiguration) and any(
        child is not vc and child.instance_name is not None
        and _abstractor_name(child, child.instance_name.value) == name
        for child in scope.view_configuration
    ):
        raise TgiError("Component instance already has a view configuration", TgiFaultCode.ALREADY_EXISTS)
    inst = vc.instance_name
    if inst is not None and not isinstance(inst, InstanceName):
        raise TgiError("Invalid instanceName model", TgiFaultCode.INVALID_ID)
    if inst is None:
        inst = InstanceName(value=name)
        vc.instance_name = inst
    else:
        inst.value = name
    register_parent(inst, vc, ("instance_name",), "single")
    return True


def setViewConfigurationView(viewConfigurationID: str, viewRef: str) -> bool:
    """Set the viewRef NMTOKEN, preserving the view and overrides (F.7.40.23)."""
    vc = _resolve_view_configuration(viewConfigurationID)
    if vc is None:
        raise TgiError("Invalid viewConfiguration handle", TgiFaultCode.INVALID_ID)
    reference = _view_reference_text(viewRef)
    view = vc.view
    if view is not None and not isinstance(view, DesignConfiguration.ViewConfiguration.View):
        raise TgiError("Invalid view model", TgiFaultCode.INVALID_ID)
    if view is None:
        view = DesignConfiguration.ViewConfiguration.View(view_ref=reference)
        vc.view = view
    else:
        view.view_ref = reference
    register_parent(view, vc, ("view",), "single")
    return True
