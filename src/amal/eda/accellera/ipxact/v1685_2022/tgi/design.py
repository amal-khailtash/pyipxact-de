"""Design category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.37) and EXTENDED (F.7.38) Design functions. Only
standard public TGI APIs are exposed – no convenience helpers beyond the
spec list ("no more, no less").

Each getter follows the error model used across the TGI layer:
* Invalid handle -> ``TgiError`` with ``TgiFaultCode.INVALID_ID`` where the
  spec implies the input must be a valid handle. Where the spec permits an
  empty result, absent optional child collections yield empty lists / None instead.
* Mutators return ``True`` on success, ``False`` on semantic no-op (e.g. element
  absent for remove*) and raise ``INVALID_ID`` for bad handles.

Internal and external ad-hoc port part-select operations reuse generated models
and shared range/index expression validation, ownership and subtree removal.
Port-reference lists traverse generated mixed holders; stored names and sub-port
paths use shared reference mappings and ordered ownership helpers. Ad-hoc
connection builders reuse endpoint builders and preserve schema reference order.
Tied values reuse generic expression access and child removal; numeric constants
resolve through SvExpressionParser and open/default retain their standard meaning.

Created child elements are registered with parent relationships so that
handle lifecycle & reverse traversal remain coherent inside the DE.
"""
# ruff: noqa: I001

from collections.abc import Iterable, Sequence

from ._model import _owned_list_ids, _sub_port_references
from ._miscellaneous_part_select import _part_select
from .port_map import _child, _child_id, _name, _remove_child, _set_part_select
from ._attribute_references import _reference_value
from .address_space import _register_owned_child, _remove_owned
from .component import _list_attr
from .choice import _validated_choice
from ._generator_context import _design_context_id
from ._library_reference import _set_reference, _xml_vlnv
from .instantiation import _registered_reference_target, getComponentInstanceComponentRefID
from .power import _external_power_domain_target, _instance_power_domain_link_ids, _internal_names
from .miscellaneous import _expression_source, getExpression, getExpressionValue, setExpressionValue

from org.accellera.ipxact.v1685_2022 import (
    Design,
    Component,
    ComponentInstances,
    ConfigurableLibraryRefType,
    InstanceName,
    StringExpression,
    AdHocConnections,
    Interconnection,
    MonitorInterconnection,
    Interconnections,
    Parameters,
    ParameterType,
)
from org.accellera.ipxact.v1685_2022.active_interface import ActiveInterface
from org.accellera.ipxact.v1685_2022.hier_interface_type import HierInterfaceType
from org.accellera.ipxact.v1685_2022.monitor_interface_type import MonitorInterfaceType
from org.accellera.ipxact.v1685_2022.ad_hoc_connection import AdHocConnection
from org.accellera.ipxact.v1685_2022.external_port_reference import ExternalPortReference
from org.accellera.ipxact.v1685_2022.sub_port_reference import SubPortReference
from org.accellera.ipxact.v1685_2022.part_select import PartSelect
from org.accellera.ipxact.v1685_2022.component_instance import ComponentInstance
from org.accellera.ipxact.v1685_2022.choices import Choices
from org.accellera.ipxact.v1685_2022.complex_tied_value_expression import ComplexTiedValueExpression
from org.accellera.ipxact.v1685_2022.power_domain_links import PowerDomainLinks

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)
# Expression access uses shared Miscellaneous helpers and Power reference context.

__all__ = [
    # BASE (F.7.37)
    "getActiveinterfaceExcludePortIDs",
    "getAdHocConnectionExternalPortReferenceIDs",
    "getAdHocConnectionInternalPortReferenceIDs",
    "getAdHocConnectionTiedValue",
    "getAdHocConnectionTiedValueExpression",
    "getAdHocConnectionTiedValueID",
    "getInternalPortReferenceComponentInstanceRefByName",
    "getComponentInstanceComponentRefByID",
    "getComponentInstanceComponentRefByVLNV",
    "getComponentInstanceName",
    "getComponentInstancePowerDomainLinkIDs",
    "getDesignAdHocConnectionIDs",
    "getDesignChoiceIDs",
    "getDesignComponentInstanceIDs",
    "getDesignID",
    "getDesignInterconnectionIDs",
    "getDesignMonitorInterconnectionIDs",
    "getExternalPortReferencePartSelectID",
    "getExternalPortReferencePortRefByName",
    "getExternalPortReferenceSubPortReferenceIDs",
    "getInterconnectionActiveInterfaceIDs",
    "getInterconnectionHierInterfaceIDs",
    "getInternalPortReferencePartSelectID",
    "getInternalPortReferencePortRefByName",
    "getInternalPortReferenceSubPortReferenceIDs",
    "getMonitorInterconnectionMonitorInterfaceIDs",
    "getMonitorInterconnectionMonitoredActiveInterfaceID",
    "getPowerDomainLinkExternalPowerDomainRef",
    "getPowerDomainLinkExternalPowerDomainRefByID",
    "getPowerDomainLinkExternalPowerDomainRefByName",
    "getPowerDomainLinkExternalPowerDomainRefExpression",
    "getPowerDomainLinkExternalPowerDomainRefID",
    "getPowerDomainLinkInternalPowerDomainRefs",
    # EXTENDED (F.7.38)
    "addActiveInterfaceExcludePort",
    "addAdHocConnectionExternalPortReference",
    "addAdHocConnectionInternalPortReference",
    "addDesignAdHocConnection",
    "addDesignChoice",
    "addDesignComponentInstance",
    "addDesignExternalAdHocConnection",
    "addDesignInterconnection",
    "addDesignMonitorInterconnection",
    "addInterconnectionActiveInterface",
    "addInterconnectionHierInterface",
    "addMonitorInterconnectionMonitorInterface",
    "removeActiveInterfaceExcludePort",
    "removeAdHocConnectionExternalPortReference",
    "removeAdHocConnectionInternalPortReference",
    "removeAdHocConnectionTiedValue",
    "removeDesignAdHocConnection",
    "removeDesignChoice",
    "removeDesignComponentInstance",
    "removeDesignInterconnection",
    "removeDesignMonitorConnection",
    "removeExternalPortReferencePartSelect",
    "removeExternalPortReferenceSubPortReference",
    "removeInterconnectionActiveInterface",
    "removeInterconnectionHierInterface",
    "removeInternalPortReferencePartSelect",
    "removeInternalPortReferenceSubPortReference",
    "removeMonitorInterconnectionMonitorInterface",
    "setAdHocConnectionTiedValue",
    "setComponentInstanceComponentRef",
    "setExternalPortReferencePartSelect",
    "setInternalPortReferencePartSelect",
    "setInterconnectionActiveInterface",
    "setInterconnectionHierInterface",
    "setMonitorInterconnectionMonitoredActiveInterface",
    "setMonitoredActiveInterfacePath",
    "setPowerDomainLinkExternalPowerDomainRef",
]


# ---------------------------------------------------------------------------
# Helpers (internal – not exported)
# ---------------------------------------------------------------------------


def _resolve_design(designID: str) -> Design | None:
    obj = resolve_handle(designID)
    return obj if isinstance(obj, Design) else None


def _resolve_interconnection(interconnectionID: str) -> Interconnection | None:
    obj = resolve_handle(interconnectionID)
    return obj if isinstance(obj, Interconnection) else None


def _resolve_monitor_interconnection(monitorID: str) -> MonitorInterconnection | None:
    obj = resolve_handle(monitorID)
    return obj if isinstance(obj, MonitorInterconnection) else None


def _resolve_component_instance(instID: str) -> ComponentInstance | None:
    obj = resolve_handle(instID)
    return obj if isinstance(obj, ComponentInstance) else None


def _resolve_ad_hoc(adHocID: str) -> AdHocConnection | None:
    obj = resolve_handle(adHocID)
    return obj if isinstance(obj, AdHocConnection) else None


def _port_reference[T: ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference](
    handle: str, model_type: type[T]
) -> T:
    """Resolve the generated ad-hoc port-reference model required by the operation."""
    owner = resolve_handle(handle) if isinstance(handle, str) else None
    if not isinstance(owner, model_type):
        raise TgiError("Invalid portReference handle", TgiFaultCode.INVALID_ID)
    return owner


def _port_reference_part_select_id(
    owner: ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference,
) -> str | None:
    """Validate and register the owner's generated part-select graph."""
    handle = _child_id(owner, "part_select", PartSelect)
    if handle is not None:
        _part_select(handle)
    return handle


def _port_reference_name(
    owner: ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference, xml_name: str
) -> str:
    """Read a stored reference name through the shared XML attribute mapping."""
    value = _reference_value(owner, xml_name)
    if value is None:
        raise TgiError("Invalid port reference source", TgiFaultCode.INVALID_ID)
    return value


def _component_reference(instance_id: str) -> ConfigurableLibraryRefType | None:
    """Reuse the component-instance reference-node getter and its strict generated type."""
    ref_id = getComponentInstanceComponentRefID(instance_id)
    if ref_id is None:
        return None
    ref = resolve_handle(ref_id)
    if not isinstance(ref, ConfigurableLibraryRefType):
        raise TgiError("Invalid componentRef model", TgiFaultCode.INVALID_ID)
    return ref


def _design_component_instances(
    design_id: str,
) -> tuple[Design, ComponentInstances | None, Sequence[ComponentInstance]]:
    """Validate the Design's component-instance holder and ordered generated collection."""
    return _design_children(
        design_id, "component_instances", ComponentInstances, "component_instance", ComponentInstance
    )


def _design_children[H, T](
    design_id: str,
    attribute: str,
    holder_type: type[H],
    child_attribute: str,
    child_types: type[T] | tuple[type[T], ...],
) -> tuple[Design, H | None, Sequence[T]]:
    """Validate a Design collection and register the actual schema holder ownership."""
    owner = _resolve_design(design_id)
    if owner is None:
        raise TgiError("Invalid design handle", TgiFaultCode.INVALID_ID)
    holder = _child(owner, attribute, holder_type)
    if holder is None:
        return owner, None, ()
    children = getattr(holder, child_attribute)
    if not isinstance(children, (list, tuple)) or any(not isinstance(child, child_types) for child in children):
        raise TgiError(f"Invalid {child_attribute} collection", TgiFaultCode.INVALID_ID)
    return owner, holder, children


def _design_connections(
    design_id: str,
) -> tuple[Design, Interconnections | None, Sequence[Interconnection | MonitorInterconnection]]:
    """Traverse the ordered mixed interconnection collection."""
    return _design_children(
        design_id,
        "interconnections",
        Interconnections,
        "interconnection_or_monitor_interconnection",
        (Interconnection, MonitorInterconnection),
    )


def _insert_design_connection(design_id: str, child: Interconnection | MonitorInterconnection) -> str:
    """Attach a fully validated connection after checking the shared name namespace."""
    owner, holder, children = _design_connections(design_id)
    name = _name(child.name, "Name")
    for current in children:
        try:
            current_name = _name(current.name, "Name")
        except TgiError as error:
            raise TgiError("Invalid existing connection name", TgiFaultCode.INVALID_ID) from error
        if current_name == name:
            raise TgiError("Duplicate connection name", TgiFaultCode.ALREADY_EXISTS)
    if holder is None:
        holder = Interconnections()
        owner.interconnections = holder
        register_parent(holder, owner, ("interconnections",), "single")
    _list_attr(holder, "interconnection_or_monitor_interconnection").append(child)
    _owned_list_ids(
        holder, holder.interconnection_or_monitor_interconnection, "interconnection_or_monitor_interconnection"
    )
    return get_handle(child)


def _remove_design_connection[T: Interconnection | MonitorInterconnection](
    connection_id: str, model_type: type[T]
) -> bool:
    """Remove only a member of its owning Design's mixed connection collection."""
    child = resolve_handle(connection_id)
    if not isinstance(child, model_type):
        raise TgiError("Invalid connection handle", TgiFaultCode.INVALID_ID)
    holder = _register_owned_child(child, Interconnections)
    owner = _register_owned_child(holder, Design) if isinstance(holder, Interconnections) else None
    if not isinstance(owner, Design) or owner.interconnections is not holder:
        raise TgiError("Connection has no owning Design", TgiFaultCode.INVALID_ID)
    _, _, children = _design_connections(get_handle(owner))
    if not any(item is child for item in children):
        raise TgiError("Connection is not in the owning collection", TgiFaultCode.INVALID_ID)
    _owned_list_ids(holder, children, "interconnection_or_monitor_interconnection")
    _list_attr(holder, "interconnection_or_monitor_interconnection")
    result = _remove_owned(connection_id, model_type, Interconnections, "connection")
    if not holder.interconnection_or_monitor_interconnection:
        detach_child_by_handle(get_handle(holder))
    return result


def _active_interface(interface_id: str) -> ActiveInterface:
    """Resolve the active-interface type used by excluded-port operations."""
    owner = resolve_handle(interface_id)
    if not isinstance(owner, ActiveInterface):
        raise TgiError("Invalid activeInterface handle", TgiFaultCode.INVALID_ID)
    return owner


def _exclude_ports(
    interface_id: str,
) -> tuple[ActiveInterface, ActiveInterface.ExcludePorts | None, Sequence[ActiveInterface.ExcludePorts.ExcludePort]]:
    """Validate the excluded-port holder and its ordered generated children."""
    owner = _active_interface(interface_id)
    holder = _child(owner, "exclude_ports", ActiveInterface.ExcludePorts)
    if holder is None:
        return owner, None, ()
    children = holder.exclude_port
    if not isinstance(children, (list, tuple)) or any(
        not isinstance(child, ActiveInterface.ExcludePorts.ExcludePort) for child in children
    ):
        raise TgiError("Invalid excludePort collection", TgiFaultCode.INVALID_ID)
    return owner, holder, children


def _interconnection_interfaces[T: ActiveInterface | HierInterfaceType | MonitorInterfaceType](
    connection_id: str, model_type: type[T]
) -> tuple[Interconnection | MonitorInterconnection, str, Sequence[T]]:
    """Validate one ordered endpoint collection of an interconnection.

    Monitor connection endpoint lists use the same ownership and storage rules.
    """
    if model_type is MonitorInterfaceType:
        owner = _resolve_monitor_interconnection(connection_id)
        attribute = "monitor_interface"
    else:
        owner = _resolve_interconnection(connection_id)
        attribute = "active_interface" if model_type is ActiveInterface else "hier_interface"
    if owner is None:
        raise TgiError("Invalid interconnection handle", TgiFaultCode.INVALID_ID)
    children = getattr(owner, attribute)
    if not isinstance(children, (list, tuple)) or any(not isinstance(child, model_type) for child in children):
        raise TgiError("Invalid interconnection interface collection", TgiFaultCode.INVALID_ID)
    return owner, attribute, children


def _build_instance_interface[T: ActiveInterface | MonitorInterfaceType](
    model_type: type[T], component_instance_ref: str, bus_ref: str
) -> T:
    """Build a generated component-instance endpoint with shared schema name validation."""
    return model_type(component_instance_ref=_name(component_instance_ref, "Name"), bus_ref=_name(bus_ref, "Name"))


def _add_interconnection_interface(
    connection_id: str, child: ActiveInterface | HierInterfaceType | MonitorInterfaceType
) -> str:
    """Append a validated endpoint using its generated collection and immediate ownership."""
    model_type = (
        ActiveInterface
        if isinstance(child, ActiveInterface)
        else MonitorInterfaceType
        if isinstance(child, MonitorInterfaceType)
        else HierInterfaceType
    )
    owner, attribute, _ = _interconnection_interfaces(connection_id, model_type)
    # Ensure list
    items = _list_attr(owner, attribute)
    items.append(child)
    _owned_list_ids(owner, items, attribute)
    return get_handle(child)


def _remove_interconnection_interface[T: ActiveInterface | HierInterfaceType](
    interface_id: str, model_type: type[T]
) -> bool:
    """Remove an endpoint only from its actual interconnection collection."""
    child = resolve_handle(interface_id)
    if not isinstance(child, model_type):
        raise TgiError("Invalid interconnection interface handle", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(child, Interconnection)
    if not isinstance(owner, Interconnection):
        raise TgiError("Interface has no owning interconnection", TgiFaultCode.INVALID_ID)
    owner_id = get_handle(owner)
    children = (
        getInterconnectionActiveInterfaceIDs(owner_id)
        if model_type is ActiveInterface
        else getInterconnectionHierInterfaceIDs(owner_id)
    )
    if interface_id not in children:
        raise TgiError("Interface is not in the owning endpoint list", TgiFaultCode.INVALID_ID)
    attribute = "active_interface" if model_type is ActiveInterface else "hier_interface"
    _list_attr(owner, attribute)
    return _remove_owned(interface_id, model_type, Interconnection, "interconnection interface")


def _replace_first_interconnection_interface(
    connection_id: str,
    model_type: type[ActiveInterface] | type[HierInterfaceType],
    bus_ref: str,
    component_instance_ref: str | None = None,
) -> bool:
    """Replace the first endpoint through the public builders and owned removers."""
    owner, attribute, children = _interconnection_interfaces(connection_id, model_type)
    first = children[0] if children else None
    if model_type is ActiveInterface:
        if component_instance_ref is None:
            raise TgiError("Missing component instance reference", TgiFaultCode.INVALID_ARGUMENT)
        addInterconnectionActiveInterface(connection_id, component_instance_ref, bus_ref)
    else:
        addInterconnectionHierInterface(connection_id, bus_ref)
    if first is not None:
        # Replace first
        if model_type is ActiveInterface:
            removeInterconnectionActiveInterface(get_handle(first))
        else:
            removeInterconnectionHierInterface(get_handle(first))
        items = _list_attr(owner, attribute)
        items.insert(0, items.pop())
    return True


def _ad_hoc_port_references(
    connection_id: str,
) -> tuple[
    AdHocConnection,
    AdHocConnection.PortReferences | None,
    Sequence[ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference],
]:
    """Validate the generated mixed reference holder without normalizing its storage."""
    owner = _resolve_ad_hoc(connection_id)
    if owner is None:
        raise TgiError("Invalid adHocConnection handle", TgiFaultCode.INVALID_ID)
    holder = _child(owner, "port_references", AdHocConnection.PortReferences)
    if holder is None:
        return owner, None, ()
    children = holder.internal_port_reference_or_external_port_reference
    if not isinstance(children, (list, tuple)) or any(
        not isinstance(child, (ExternalPortReference, AdHocConnection.PortReferences.InternalPortReference))
        for child in children
    ):
        raise TgiError("Invalid ad-hoc port reference collection", TgiFaultCode.INVALID_ID)
    return owner, holder, children


def _ad_hoc_port_reference_ids[T: ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference](
    connection_id: str, model_type: type[T]
) -> list[str]:
    """Filter generated mixed references, retaining their immediate holder ownership."""
    _, holder, children = _ad_hoc_port_references(connection_id)
    return (
        []
        if holder is None
        else _owned_list_ids(
            holder,
            (child for child in children if isinstance(child, model_type)),
            "internal_port_reference_or_external_port_reference",
        )
    )


def _insert_ad_hoc_port_reference(
    connection_id: str, child: ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference
) -> str:
    """Insert a named endpoint while preserving the schema's internal-before-external order."""
    owner, holder, children = _ad_hoc_port_references(connection_id)
    external_seen = False
    for current in children:
        if isinstance(current, ExternalPortReference):
            external_seen = True
        elif external_seen:
            raise TgiError("Invalid ad-hoc port reference order", TgiFaultCode.INVALID_ID)
    if holder is None:
        holder = AdHocConnection.PortReferences()
        owner.port_references = holder
        register_parent(holder, owner, ("port_references",), "single")
    items = _list_attr(holder, "internal_port_reference_or_external_port_reference")
    index = len(items)
    if isinstance(child, AdHocConnection.PortReferences.InternalPortReference):
        index = next((i for i, current in enumerate(items) if isinstance(current, ExternalPortReference)), len(items))
    items.insert(index, child)
    _owned_list_ids(holder, items, "internal_port_reference_or_external_port_reference")
    return get_handle(child)


def _remove_ad_hoc_port_reference[T: ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference](
    reference_id: str, model_type: type[T]
) -> bool:
    """Remove an endpoint belonging to the actual mixed holder of an ad-hoc connection."""
    child = _port_reference(reference_id, model_type)
    holder = _register_owned_child(child, AdHocConnection.PortReferences)
    if not isinstance(holder, AdHocConnection.PortReferences):
        raise TgiError("Reference has no owning ad-hoc holder", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, AdHocConnection)
    if not isinstance(owner, AdHocConnection) or owner.port_references is not holder:
        raise TgiError("Holder has no owning ad-hoc connection", TgiFaultCode.INVALID_ID)
    _, _, children = _ad_hoc_port_references(get_handle(owner))
    if not any(current is child for current in children):
        raise TgiError("Reference is not in the owning endpoint list", TgiFaultCode.INVALID_ID)
    _list_attr(holder, "internal_port_reference_or_external_port_reference")
    return _remove_owned(reference_id, model_type, AdHocConnection.PortReferences, "ad-hoc port reference")


def _design_ad_hoc_connections(
    design_id: str,
) -> tuple[Design, AdHocConnections | None, Sequence[AdHocConnection]]:
    """Validate the Design's ad-hoc connection holder and ordered child collection."""
    return _design_children(design_id, "ad_hoc_connections", AdHocConnections, "ad_hoc_connection", AdHocConnection)


def _build_design_ad_hoc_connection(
    design_id: str, name: str, port_ref: str, component_instance_ref: str | None = None
) -> str:
    """Build a connection through the public endpoint builders, then attach it to the Design."""
    owner, holder, children = _design_ad_hoc_connections(design_id)
    source_name, source_port = _name(name, "portName"), _name(port_ref, "portName")
    source_instance = None if component_instance_ref is None else _name(component_instance_ref, "Name")
    for current in children:
        try:
            current_name = _name(current.name, "portName")
        except TgiError as error:
            raise TgiError("Invalid existing ad-hoc connection name", TgiFaultCode.INVALID_ID) from error
        if current_name == source_name:
            raise TgiError("Duplicate ad-hoc connection name", TgiFaultCode.INVALID_ARGUMENT)
    # init port_references
    child = AdHocConnection(name=source_name, port_references=AdHocConnection.PortReferences())
    handle = get_handle(child)
    if source_instance is None:
        addAdHocConnectionExternalPortReference(handle, source_port)
    else:
        addAdHocConnectionInternalPortReference(handle, source_instance, source_port)
    if holder is None:
        holder = AdHocConnections()
        owner.ad_hoc_connections = holder
        register_parent(holder, owner, ("ad_hoc_connections",), "single")
    _list_attr(holder, "ad_hoc_connection").append(child)
    getDesignAdHocConnectionIDs(design_id)
    return handle


def _port_sub_reference_ids(
    owner: ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference,
) -> list[str]:
    """Return ordered handles to validated sub-port references."""
    return _owned_list_ids(owner, _sub_port_references(owner), "sub_port_reference")


def _remove_port_sub_reference[T: ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference](
    reference_id: str, owner_type: type[T]
) -> bool:
    """Remove one sub-port path entry belonging to the required port-reference type."""
    child = resolve_handle(reference_id)
    if not isinstance(child, SubPortReference):
        raise TgiError("Invalid subPortReference handle", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(child, owner_type)
    if not isinstance(owner, owner_type):
        raise TgiError("Sub-port reference has no owning port reference", TgiFaultCode.INVALID_ID)
    if get_handle(child) not in _port_sub_reference_ids(owner):
        raise TgiError("Reference is not in the owning sub-port path", TgiFaultCode.INVALID_ID)
    _list_attr(owner, "sub_port_reference")
    return _remove_owned(reference_id, SubPortReference, owner_type, "port sub-reference")


def _iter[T](seq: Iterable[T] | None) -> list[T]:
    if seq is None:
        return []
    if isinstance(seq, list):
        return seq
    try:
        return list(seq)
    except Exception:  # pragma: no cover
        return []


# ---------------------------------------------------------------------------
# BASE (F.7.37)
# ---------------------------------------------------------------------------


def getActiveinterfaceExcludePortIDs(activeInterfaceID: str) -> list[str]:
    """Return handles of excludePort elements of an activeInterface.

    Section: F.7.37.1.
    """
    _, holder, children = _exclude_ports(activeInterfaceID)
    return [] if holder is None else _owned_list_ids(holder, children, "exclude_port")


def getAdHocConnectionExternalPortReferenceIDs(adHocConnectionID: str) -> list[str]:
    """Return handles of externalPortReference children.

    Section: F.7.37.2.
    """
    return _ad_hoc_port_reference_ids(adHocConnectionID, ExternalPortReference)


def getAdHocConnectionInternalPortReferenceIDs(adHocConnectionID: str) -> list[str]:
    """Return handles of internalPortReference children.

    Section: F.7.37.3.
    """
    return _ad_hoc_port_reference_ids(adHocConnectionID, AdHocConnection.PortReferences.InternalPortReference)


def getAdHocConnectionTiedValue(adHocConnectionID: str) -> str | None:
    """Return tiedValue value if present.

    Numeric constants evaluate to unsigned integer text; open/default retain
    their standard meaning. Unresolved expressions raise INVALID_ARGUMENT.

    Section: F.7.37.4.
    """
    value_id = getAdHocConnectionTiedValueID(adHocConnectionID)
    return None if value_id is None else getExpressionValue(value_id)


def getAdHocConnectionTiedValueExpression(adHocConnectionID: str) -> str | None:
    """Return tiedValue expression string.

    Section: F.7.37.5.
    """
    value_id = getAdHocConnectionTiedValueID(adHocConnectionID)
    return None if value_id is None else getExpression(value_id)


def getAdHocConnectionTiedValueID(adHocConnectionID: str) -> str | None:
    """Return handle of tiedValue element.

    Section: F.7.37.6.
    """
    ac = _resolve_ad_hoc(adHocConnectionID)
    if ac is None:
        raise TgiError("Invalid adHocConnection handle", TgiFaultCode.INVALID_ID)
    return _child_id(ac, "tied_value", ComplexTiedValueExpression)


def getInternalPortReferenceComponentInstanceRefByName(internalPortReferenceID: str) -> str:
    """Return componentInstanceRef attribute value.

    Section: F.7.37.7.
    """
    # internalPortReference is nested dataclass
    owner = _port_reference(internalPortReferenceID, AdHocConnection.PortReferences.InternalPortReference)
    return _port_reference_name(owner, "componentInstanceRef")


def getComponentInstanceComponentRefByID(componentInstanceID: str) -> str:
    """Return handle of referenced component (componentRef).

    Section: F.7.37.8. Missing or wrong-kind registered component targets raise NOT_FOUND.
    """
    # The XML schema holds only VLNV strings; resolution to component object would be DE responsibility.
    ref = _component_reference(componentInstanceID)
    return get_handle(_registered_reference_target(ref, Component, "componentRef"))


def getComponentInstanceComponentRefByVLNV(
    componentInstanceID: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Return (vendor, library, name, version) VLNV referenced.

    Section: F.7.37.9.
    """
    ref = _component_reference(componentInstanceID)
    if ref is None:
        return (None, None, None, None)
    parts = (ref.vendor, ref.library, ref.name, ref.version)
    if any(part is not None and not isinstance(part, str) for part in parts):
        raise TgiError("Invalid componentRef VLNV content", TgiFaultCode.INVALID_ID)
    return parts


def getComponentInstanceName(componentInstanceID: str) -> str | None:
    """Return componentInstance name.

    Section: F.7.37.10.
    """
    owner = _resolve_component_instance(componentInstanceID)
    if owner is None:
        raise TgiError("Invalid componentInstance handle", TgiFaultCode.INVALID_ID)
    name = _child(owner, "instance_name", InstanceName)
    if name is None:
        return None
    if not isinstance(name.value, str):
        raise TgiError("Invalid instanceName content", TgiFaultCode.INVALID_ID)
    return name.value


def getComponentInstancePowerDomainLinkIDs(componentInstanceID: str) -> list[str]:  # F.7.37.11
    """Return ordered instance power-domain link handles with immediate ownership.

    Section: F.7.37.11.
    """
    return _instance_power_domain_link_ids(componentInstanceID)


def getDesignAdHocConnectionIDs(designID: str) -> list[str]:
    """Return handles of adHocConnection children.

    Section: F.7.37.12.
    """
    _, holder, children = _design_ad_hoc_connections(designID)
    return [] if holder is None else _owned_list_ids(holder, children, "ad_hoc_connection")


def getDesignChoiceIDs(designID: str) -> list[str]:
    """Return handles of choice elements.

    Section: F.7.37.13.
    """
    _, holder, children = _design_children(designID, "choices", Choices, "choice", Choices.Choice)
    return [] if holder is None else _owned_list_ids(holder, children, "choice")


def getDesignComponentInstanceIDs(designID: str) -> list[str]:
    """Return handles of componentInstance elements.

    Section: F.7.37.14.
    """
    _, holder, children = _design_component_instances(designID)
    return [] if holder is None else _owned_list_ids(holder, children, "component_instance")


def getDesignID(top: bool) -> str | None:
    """Return handle to current or top design.

    Section: F.7.37.15. The host supplies scoped generator context; absent context returns None.
    """
    return _design_context_id(top)


def _connection_ids(design: Design, model_type: type[Interconnection | MonitorInterconnection]) -> list[str]:
    _, holder, children = _design_connections(get_handle(design))
    return (
        []
        if holder is None
        else _owned_list_ids(
            holder,
            (child for child in children if isinstance(child, model_type)),
            "interconnection_or_monitor_interconnection",
        )
    )


def getDesignInterconnectionIDs(designID: str) -> list[str]:
    """Return handles of interconnection elements.

    Section: F.7.37.16.
    """
    d = _resolve_design(designID)
    if d is None:
        raise TgiError("Invalid design handle", TgiFaultCode.INVALID_ID)
    return _connection_ids(d, Interconnection)


def getDesignMonitorInterconnectionIDs(designID: str) -> list[str]:
    """Return handles of monitorInterconnection elements.

    Section: F.7.37.17.
    """
    d = _resolve_design(designID)
    if d is None:
        raise TgiError("Invalid design handle", TgiFaultCode.INVALID_ID)
    return _connection_ids(d, MonitorInterconnection)


def getExternalPortReferencePartSelectID(externalPortReferenceID: str) -> str | None:
    """Return handle of partSelect element of externalPortReference.

    Section: F.7.37.18.
    """
    owner = _port_reference(externalPortReferenceID, ExternalPortReference)
    return _port_reference_part_select_id(owner)


def getExternalPortReferencePortRefByName(externalPortReferenceID: str) -> str:
    """Return portRef attribute of externalPortReference.

    Section: F.7.37.19.
    """
    owner = _port_reference(externalPortReferenceID, ExternalPortReference)
    return _port_reference_name(owner, "portRef")


def getExternalPortReferenceSubPortReferenceIDs(externalPortReferenceID: str) -> list[str]:
    """Return handles of subPortReference elements for externalPortReference.

    Section: F.7.37.20.
    """
    owner = _port_reference(externalPortReferenceID, ExternalPortReference)
    return _port_sub_reference_ids(owner)


def getInterconnectionActiveInterfaceIDs(interconnectionID: str) -> list[str]:
    """Return handles of activeInterface children.

    Section: F.7.37.21.
    """
    owner, attribute, children = _interconnection_interfaces(interconnectionID, ActiveInterface)
    return _owned_list_ids(owner, children, attribute)


def getInterconnectionHierInterfaceIDs(interconnectionID: str) -> list[str]:
    """Return handles of hierInterface children.

    Section: F.7.37.22.
    """
    owner, attribute, children = _interconnection_interfaces(interconnectionID, HierInterfaceType)
    return _owned_list_ids(owner, children, attribute)


def getInternalPortReferencePartSelectID(internalPortReferenceID: str) -> str | None:
    """Return handle of partSelect element for internalPortReference.

    Section: F.7.37.23.
    """
    owner = _port_reference(internalPortReferenceID, AdHocConnection.PortReferences.InternalPortReference)
    return _port_reference_part_select_id(owner)


def getInternalPortReferencePortRefByName(internalPortReferenceID: str) -> str:
    """Return portRef attribute from internalPortReference.

    Section: F.7.37.24.
    """
    owner = _port_reference(internalPortReferenceID, AdHocConnection.PortReferences.InternalPortReference)
    return _port_reference_name(owner, "portRef")


def getInternalPortReferenceSubPortReferenceIDs(internalPortReferenceID: str) -> list[str]:
    """Return handles of subPortReference elements of internalPortReference.

    Section: F.7.37.25.
    """
    owner = _port_reference(internalPortReferenceID, AdHocConnection.PortReferences.InternalPortReference)
    return _port_sub_reference_ids(owner)


def getMonitorInterconnectionMonitorInterfaceIDs(monitorInterconnectionID: str) -> list[str]:
    """Return handles of monitorInterface elements.

    Section: F.7.37.26.
    """
    owner, attribute, children = _interconnection_interfaces(monitorInterconnectionID, MonitorInterfaceType)
    return _owned_list_ids(owner, children, attribute)


def getMonitorInterconnectionMonitoredActiveInterfaceID(monitorInterconnectionID: str) -> str | None:
    """Return handle of monitoredActiveInterface element.

    Section: F.7.37.27.
    """
    owner = _resolve_monitor_interconnection(monitorInterconnectionID)
    if owner is None:
        raise TgiError("Invalid monitorInterconnection handle", TgiFaultCode.INVALID_ID)
    return _child_id(owner, "monitored_active_interface", MonitorInterfaceType)


def getPowerDomainLinkExternalPowerDomainRef(powerDomainLinkID: str) -> str | None:
    """Return external power domain value from powerDomainLink.

    Section: F.7.37.28.
    """
    expression_id = getPowerDomainLinkExternalPowerDomainRefID(powerDomainLinkID)
    return None if expression_id is None else getExpressionValue(expression_id)


def getPowerDomainLinkExternalPowerDomainRefByID(powerDomainLinkID: str) -> str | None:
    """Return handle to referenced external power domain.

    Section: F.7.37.29. Resolve in the registered component referencing this Design.
    """
    name = getPowerDomainLinkExternalPowerDomainRefByName(powerDomainLinkID)
    link = resolve_handle(powerDomainLinkID)
    if not isinstance(link, PowerDomainLinks.PowerDomainLink):
        raise TgiError("Invalid powerDomainLink handle", TgiFaultCode.INVALID_ID)
    return _external_power_domain_target(link, name)


def getPowerDomainLinkExternalPowerDomainRefByName(powerDomainLinkID: str) -> str | None:
    """Return external power domain referenced (string).

    Section: F.7.37.30.
    """
    return getPowerDomainLinkExternalPowerDomainRef(powerDomainLinkID)


def getPowerDomainLinkExternalPowerDomainRefExpression(powerDomainLinkID: str) -> str | None:
    """Return the raw external power-domain string expression.

    Section: F.7.37.31.
    """
    expression_id = getPowerDomainLinkExternalPowerDomainRefID(powerDomainLinkID)
    return None if expression_id is None else getExpression(expression_id)


def getPowerDomainLinkExternalPowerDomainRefID(powerDomainLinkID: str) -> str | None:
    """Return handle of external power domain expression element.

    Section: F.7.37.32.
    """
    link = resolve_handle(powerDomainLinkID)
    if not isinstance(link, PowerDomainLinks.PowerDomainLink):
        raise TgiError("Invalid powerDomainLink handle", TgiFaultCode.INVALID_ID)
    return _child_id(link, "external_power_domain_reference", StringExpression)


def getPowerDomainLinkInternalPowerDomainRefs(powerDomainLinkID: str) -> list[str]:
    """Return internal power domain reference names (strings).

    Section: F.7.37.33.
    """
    link = resolve_handle(powerDomainLinkID)
    if not isinstance(link, PowerDomainLinks.PowerDomainLink):
        raise TgiError("Invalid powerDomainLink handle", TgiFaultCode.INVALID_ID)
    return _internal_names([link])


# ---------------------------------------------------------------------------
# EXTENDED (F.7.38)
# ---------------------------------------------------------------------------


def addActiveInterfaceExcludePort(activeInterfaceID: str, excludePort: str) -> str:
    """Add an excludePort to an activeInterface.

    Section: F.7.38.1.
    """
    owner, holder, _ = _exclude_ports(activeInterfaceID)
    child = ActiveInterface.ExcludePorts.ExcludePort(value=_name(excludePort, "portName"))
    if holder is None:
        holder = ActiveInterface.ExcludePorts()
        owner.exclude_ports = holder
        register_parent(holder, owner, ("exclude_ports",), "single")
    _list_attr(holder, "exclude_port").append(child)
    getActiveinterfaceExcludePortIDs(activeInterfaceID)
    return get_handle(child)


def addAdHocConnectionExternalPortReference(adHocConnectionID: str, portRef: str) -> str:
    """Add externalPortReference with portRef to adHocConnection.

    Section: F.7.38.2.
    """
    child = ExternalPortReference(port_ref=_name(portRef, "portName"))
    return _insert_ad_hoc_port_reference(adHocConnectionID, child)


def addAdHocConnectionInternalPortReference(adHocConnectionID: str, componentInstanceRef: str, portRef: str) -> str:
    """Add internalPortReference.

    Section: F.7.38.3.
    """
    child = AdHocConnection.PortReferences.InternalPortReference(
        component_instance_ref=_name(componentInstanceRef, "Name"), port_ref=_name(portRef, "portName")
    )
    return _insert_ad_hoc_port_reference(adHocConnectionID, child)


def addDesignAdHocConnection(designID: str, name: str, componentInstanceRef: str, portRef: str) -> str:
    """Add adHocConnection with one internalPortReference.

    Section: F.7.38.4.
    """
    source_instance = _name(componentInstanceRef, "Name")
    return _build_design_ad_hoc_connection(designID, name, portRef, source_instance)


def addDesignChoice(designID: str, name: str, enumerations: Sequence[str]) -> str:
    """Add choice with name and enumerations.

    Section: F.7.38.5.
    """
    owner, holder, children = _design_children(designID, "choices", Choices, "choice", Choices.Choice)
    child = _validated_choice(name, enumerations)
    child.name = _name(child.name, "Name")
    for enumeration in child.enumeration:
        enumeration.value = _expression_source(enumeration.value, enumeration)
    for current in children:
        try:
            current_name = _name(current.name, "Name")
        except TgiError as error:
            raise TgiError("Invalid existing choice name", TgiFaultCode.INVALID_ID) from error
        if current_name == child.name:
            raise TgiError("Choice name already defined", TgiFaultCode.ALREADY_EXISTS)
    if holder is None:
        holder = Choices()
        owner.choices = holder
        register_parent(holder, owner, ("choices",), "single")
    _list_attr(holder, "choice").append(child)
    getDesignChoiceIDs(designID)
    _owned_list_ids(child, child.enumeration, "enumeration")
    return get_handle(child)


def addDesignComponentInstance(
    designID: str,
    componentVLNV: tuple[str, str, str, str],
    componentInstanceName: str,
) -> str:
    """Add componentInstance referencing component VLNV.

    Section: F.7.38.6.
    """
    owner, holder, children = _design_component_instances(designID)
    parts = _xml_vlnv(componentVLNV)
    source_name = _name(componentInstanceName, "Name")
    for current in children:
        try:
            current_name = getComponentInstanceName(get_handle(current))
            if current_name is None:
                raise TgiError("Missing existing instanceName", TgiFaultCode.INVALID_ID)
            normalized = _name(current_name, "Name")
        except TgiError as error:
            raise TgiError("Invalid existing instanceName", TgiFaultCode.INVALID_ID) from error
        if normalized == source_name:
            raise TgiError("Duplicate component instance name", TgiFaultCode.INVALID_ARGUMENT)
    # component_ref is ConfigurableLibraryRefType in the schema, preserving configurable values.
    child = ComponentInstance(
        instance_name=InstanceName(value=source_name),
        component_ref=ConfigurableLibraryRefType(vendor="", library="", name="", version=""),
    )
    handle = get_handle(child)
    setComponentInstanceComponentRef(handle, parts)
    if holder is None:
        holder = ComponentInstances()
        owner.component_instances = holder
        register_parent(holder, owner, ("component_instances",), "single")
    _list_attr(holder, "component_instance").append(child)
    getDesignComponentInstanceIDs(designID)
    return handle


def addDesignExternalAdHocConnection(designID: str, name: str, portRef: str) -> str:
    """Add adHocConnection with single externalPortReference.

    Section: F.7.38.7.
    """
    return _build_design_ad_hoc_connection(designID, name, portRef)


def addDesignInterconnection(
    designID: str,
    name: str,
    componentInstanceRef1: str,
    busInterfaceRef1: str,
    componentInstanceRef2: str,
    busInterfaceRef2: str,
) -> str:
    """Add interconnection with two activeInterface endpoints.

    Section: F.7.38.8.
    """
    _design_connections(designID)
    child = Interconnection(name=_name(name, "Name"))
    first_instance, first_bus = _name(componentInstanceRef1, "Name"), _name(busInterfaceRef1, "Name")
    second_instance, second_bus = _name(componentInstanceRef2, "Name"), _name(busInterfaceRef2, "Name")
    child_id = get_handle(child)
    addInterconnectionActiveInterface(child_id, first_instance, first_bus)
    addInterconnectionActiveInterface(child_id, second_instance, second_bus)
    return _insert_design_connection(designID, child)


def addDesignMonitorInterconnection(
    designID: str,
    name: str,
    componentInstanceRef1: str,
    activeInterfaceBusInterfaceRef: str,
    componentInstanceRef2: str,
    interfaceBusInterfaceRef: str,
) -> str:
    """Add monitorInterconnection with monitoredActiveInterface + monitorInterface.

    Section: F.7.38.9.
    """
    _design_connections(designID)
    source_name = _name(name, "Name")
    first_instance, first_bus = _name(componentInstanceRef1, "Name"), _name(activeInterfaceBusInterfaceRef, "Name")
    second_instance, second_bus = _name(componentInstanceRef2, "Name"), _name(interfaceBusInterfaceRef, "Name")
    first = _build_instance_interface(MonitorInterfaceType, first_instance, first_bus)
    child = MonitorInterconnection(name=source_name, monitored_active_interface=first)
    child_id = get_handle(child)
    register_parent(first, child, ("monitored_active_interface",), "single")
    addMonitorInterconnectionMonitorInterface(child_id, second_instance, second_bus)
    return _insert_design_connection(designID, child)


def addInterconnectionActiveInterface(interconnectionID: str, componentInstanceRef: str, busInterfaceRef: str) -> str:
    """Add an activeInterface to an interconnection.

    Section: F.7.38.10.
    """
    child = _build_instance_interface(ActiveInterface, componentInstanceRef, busInterfaceRef)
    return _add_interconnection_interface(interconnectionID, child)


def addInterconnectionHierInterface(interconnectionID: str, busInterfaceRef: str) -> str:
    """Add a hierInterface to an interconnection.

    Section: F.7.38.11.
    """
    child = HierInterfaceType(bus_ref=_name(busInterfaceRef, "Name"))
    return _add_interconnection_interface(interconnectionID, child)


def addMonitorInterconnectionMonitorInterface(
    monitorInterconnectionID: str,
    componentInstanceRef: str,
    busInterfaceRef: str,
) -> str:
    """Add monitorInterface to a monitorInterconnection.

    Section: F.7.38.12.
    """
    child = _build_instance_interface(MonitorInterfaceType, componentInstanceRef, busInterfaceRef)
    return _add_interconnection_interface(monitorInterconnectionID, child)


def removeActiveInterfaceExcludePort(excludePortID: str) -> bool:
    """Remove excludePort element.

    Section: F.7.38.13.
    """
    child = resolve_handle(excludePortID)
    if not isinstance(child, ActiveInterface.ExcludePorts.ExcludePort):
        raise TgiError("Invalid excludePort handle", TgiFaultCode.INVALID_ID)
    holder = _register_owned_child(child, ActiveInterface.ExcludePorts)
    if not isinstance(holder, ActiveInterface.ExcludePorts):
        raise TgiError("Port has no owning exclusion holder", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, ActiveInterface)
    if not isinstance(owner, ActiveInterface) or owner.exclude_ports is not holder:
        raise TgiError("Exclusion holder has no owning activeInterface", TgiFaultCode.INVALID_ID)
    if excludePortID not in getActiveinterfaceExcludePortIDs(get_handle(owner)):
        raise TgiError("Port is not in the owning exclusion list", TgiFaultCode.INVALID_ID)
    _list_attr(holder, "exclude_port")
    return _remove_owned(
        excludePortID, ActiveInterface.ExcludePorts.ExcludePort, ActiveInterface.ExcludePorts, "excludePort"
    )


def removeAdHocConnectionExternalPortReference(externalPortReferenceID: str) -> bool:
    """Remove externalPortReference element.

    Section: F.7.38.14.
    """
    return _remove_ad_hoc_port_reference(externalPortReferenceID, ExternalPortReference)


def removeAdHocConnectionInternalPortReference(internalPortReferenceID: str) -> bool:
    """Remove internalPortReference element.

    Section: F.7.38.15.
    """
    return _remove_ad_hoc_port_reference(internalPortReferenceID, AdHocConnection.PortReferences.InternalPortReference)


def removeAdHocConnectionTiedValue(adHocConnectionID: str) -> bool:
    """Remove tiedValue element from adHocConnection.

    Section: F.7.38.16.
    """
    if getAdHocConnectionTiedValueID(adHocConnectionID) is None:
        return False
    ac = _resolve_ad_hoc(adHocConnectionID)
    if ac is None:
        raise TgiError("Invalid adHocConnection handle", TgiFaultCode.INVALID_ID)
    return _remove_child(ac, "tied_value")


def removeDesignAdHocConnection(adHocConnectionID: str) -> bool:
    """Remove adHocConnection element.

    Section: F.7.38.17.
    """
    child = _resolve_ad_hoc(adHocConnectionID)
    if child is None:
        raise TgiError("Invalid adHocConnection handle", TgiFaultCode.INVALID_ID)
    holder = _register_owned_child(child, AdHocConnections)
    if not isinstance(holder, AdHocConnections):
        raise TgiError("Connection has no owning ad-hoc holder", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, Design)
    if not isinstance(owner, Design) or owner.ad_hoc_connections is not holder:
        raise TgiError("Holder has no owning Design", TgiFaultCode.INVALID_ID)
    if get_handle(child) not in getDesignAdHocConnectionIDs(get_handle(owner)):
        raise TgiError("Connection is not in the owning collection", TgiFaultCode.INVALID_ID)
    _list_attr(holder, "ad_hoc_connection")
    return _remove_owned(adHocConnectionID, AdHocConnection, AdHocConnections, "ad-hoc connection")


def removeDesignChoice(choiceID: str) -> bool:
    """Remove choice element.

    Return False while a direct Design parameter references the choice, preserving designChoiceRef.

    Section: F.7.38.18.
    """
    child = resolve_handle(choiceID)
    if not isinstance(child, Choices.Choice):
        raise TgiError("Invalid choice handle", TgiFaultCode.INVALID_ID)
    holder = _register_owned_child(child, Choices)
    owner = _register_owned_child(holder, Design) if isinstance(holder, Choices) else None
    if not isinstance(owner, Design) or owner.choices is not holder:
        raise TgiError("Choice has no owning Design", TgiFaultCode.INVALID_ID)
    if choiceID not in getDesignChoiceIDs(get_handle(owner)):
        raise TgiError("Choice is not in the owning collection", TgiFaultCode.INVALID_ID)
    parameters = _child(owner, "parameters", Parameters)
    if parameters is not None:
        if not isinstance(parameters.parameter, (list, tuple)) or any(
            not isinstance(item, ParameterType) for item in parameters.parameter
        ):
            raise TgiError("Invalid parameter collection", TgiFaultCode.INVALID_ID)
        if any(
            item.choice_ref is not None and _name(item.choice_ref, "Name") == _name(child.name, "Name")
            for item in parameters.parameter
        ):
            return False
    _list_attr(holder, "choice")
    result = _remove_owned(choiceID, Choices.Choice, Choices, "choice")
    if not holder.choice:
        detach_child_by_handle(get_handle(holder))
    return result


def removeDesignComponentInstance(componentInstanceID: str) -> bool:
    """Remove componentInstance element.

    Section: F.7.38.19.
    """
    child = _resolve_component_instance(componentInstanceID)
    if child is None:
        raise TgiError("Invalid componentInstance handle", TgiFaultCode.INVALID_ID)
    holder = _register_owned_child(child, ComponentInstances)
    if not isinstance(holder, ComponentInstances):
        raise TgiError("Instance has no owning componentInstances holder", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, Design)
    if not isinstance(owner, Design) or owner.component_instances is not holder:
        raise TgiError("Holder has no owning Design", TgiFaultCode.INVALID_ID)
    if componentInstanceID not in getDesignComponentInstanceIDs(get_handle(owner)):
        raise TgiError("Instance is not in the owning collection", TgiFaultCode.INVALID_ID)
    _list_attr(holder, "component_instance")
    return _remove_owned(componentInstanceID, ComponentInstance, ComponentInstances, "componentInstance")


def removeDesignInterconnection(interconnectionID: str) -> bool:
    """Remove interconnection element.

    Section: F.7.38.20.
    """
    return _remove_design_connection(interconnectionID, Interconnection)


def removeDesignMonitorConnection(monitorInterconnectionID: str) -> bool:
    """Remove monitorInterconnection element.

    Section: F.7.38.21.
    """
    return _remove_design_connection(monitorInterconnectionID, MonitorInterconnection)


def removeExternalPortReferencePartSelect(externalPortReferenceID: str) -> bool:
    """Remove partSelect from externalPortReference.

    Section: F.7.38.22.
    """
    owner = _port_reference(externalPortReferenceID, ExternalPortReference)
    if getExternalPortReferencePartSelectID(externalPortReferenceID) is None:
        return False
    return _remove_child(owner, "part_select")


def removeExternalPortReferenceSubPortReference(subPortRefID: str) -> bool:
    """Remove a subPortReference element (external).

    Section: F.7.38.23.
    """
    return _remove_port_sub_reference(subPortRefID, ExternalPortReference)


def removeInterconnectionActiveInterface(activeInterfaceID: str) -> bool:
    """Remove activeInterface element.

    Section: F.7.38.24.
    """
    return _remove_interconnection_interface(activeInterfaceID, ActiveInterface)


def removeInterconnectionHierInterface(hierInterfaceID: str) -> bool:
    """Remove hierInterface element.

    Section: F.7.38.25.
    """
    return _remove_interconnection_interface(hierInterfaceID, HierInterfaceType)


def removeInternalPortReferencePartSelect(internalPortReferenceID: str) -> bool:
    """Remove partSelect from internalPortReference.

    Section: F.7.38.26.
    """
    owner = _port_reference(internalPortReferenceID, AdHocConnection.PortReferences.InternalPortReference)
    if getInternalPortReferencePartSelectID(internalPortReferenceID) is None:
        return False
    return _remove_child(owner, "part_select")


def removeInternalPortReferenceSubPortReference(subPortRefID: str) -> bool:
    """Remove subPortReference element (internal).

    Section: F.7.38.27.
    """
    return _remove_port_sub_reference(subPortRefID, AdHocConnection.PortReferences.InternalPortReference)


def removeMonitorInterconnectionMonitorInterface(monitorInterfaceID: str) -> bool:
    """Remove monitorInterface element.

    Section: F.7.38.28.
    """
    child = resolve_handle(monitorInterfaceID)
    if not isinstance(child, MonitorInterfaceType):
        raise TgiError("Invalid monitorInterface handle", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(child, MonitorInterconnection)
    if not isinstance(owner, MonitorInterconnection):
        raise TgiError("Interface has no owning monitorInterconnection", TgiFaultCode.INVALID_ID)
    if monitorInterfaceID not in getMonitorInterconnectionMonitorInterfaceIDs(get_handle(owner)):
        raise TgiError("Interface is not in the owning monitor list", TgiFaultCode.INVALID_ID)
    _list_attr(owner, "monitor_interface")
    return _remove_owned(monitorInterfaceID, MonitorInterfaceType, MonitorInterconnection, "monitorInterface")


def setAdHocConnectionTiedValue(adHocConnectionID: str, tiedValue: str) -> bool:
    """Set tiedValue value (creates element if absent).

    Section: F.7.38.29.
    """
    value_id = getAdHocConnectionTiedValueID(adHocConnectionID)
    if value_id is not None:
        return setExpressionValue(value_id, tiedValue)
    child = ComplexTiedValueExpression()
    child.value = _expression_source(tiedValue, child)
    ac = _resolve_ad_hoc(adHocConnectionID)
    if ac is None:
        raise TgiError("Invalid adHocConnection handle", TgiFaultCode.INVALID_ID)
    ac.tied_value = child
    register_parent(child, ac, ("tied_value",), "single")
    return True


def setComponentInstanceComponentRef(componentInstanceID: str, componentVLNV: tuple[str, str, str, str]) -> bool:
    """Set componentRef VLNV on componentInstance.

    Section: F.7.38.30.
    """
    owner = _resolve_component_instance(componentInstanceID)
    if owner is None:
        raise TgiError("Invalid componentInstance handle", TgiFaultCode.INVALID_ID)
    _set_reference(owner, "component_ref", ConfigurableLibraryRefType, componentVLNV)
    getComponentInstanceComponentRefID(componentInstanceID)
    return True


def setExternalPortReferencePartSelect(
    externalPortReferenceID: str,
    range: Sequence[str] | None,
    indices: Sequence[str] | None,
) -> bool:
    """Set partSelect on externalPortReference (preserves compatible nodes).

    Section: F.7.38.31.
    """
    owner = _port_reference(externalPortReferenceID, ExternalPortReference)
    _set_part_select(owner, range, indices)
    getExternalPortReferencePartSelectID(externalPortReferenceID)
    return True


def setInternalPortReferencePartSelect(
    internalPortReferenceID: str,
    range: Sequence[str] | None,
    indices: Sequence[str] | None,
) -> bool:
    """Set partSelect on internalPortReference.

    Section: F.7.38.32.
    """
    owner = _port_reference(internalPortReferenceID, AdHocConnection.PortReferences.InternalPortReference)
    _set_part_select(owner, range, indices)
    getInternalPortReferencePartSelectID(internalPortReferenceID)
    return True


def setInterconnectionActiveInterface(interconnectionID: str, componentInstanceRef: str, busRef: str) -> bool:
    """Set (replace) first activeInterface of interconnection.

    Section: F.7.38.33.
    """
    return _replace_first_interconnection_interface(interconnectionID, ActiveInterface, busRef, componentInstanceRef)


def setInterconnectionHierInterface(interconnectionID: str, busRef: str) -> bool:
    """Set (replace) first hierInterface entry.

    Section: F.7.38.34.
    """
    return _replace_first_interconnection_interface(interconnectionID, HierInterfaceType, busRef)


def setMonitorInterconnectionMonitoredActiveInterface(
    monitorInterconnectionID: str,
    componentInstanceRef: str,
    busRef: str,
) -> bool:
    """Set monitoredActiveInterface element.

    Section: F.7.38.35.
    """
    getMonitorInterconnectionMonitoredActiveInterfaceID(monitorInterconnectionID)
    child = _build_instance_interface(MonitorInterfaceType, componentInstanceRef, busRef)
    owner = _resolve_monitor_interconnection(monitorInterconnectionID)
    if owner is None:
        raise TgiError("Invalid monitorInterconnection handle", TgiFaultCode.INVALID_ID)
    _remove_child(owner, "monitored_active_interface")
    owner.monitored_active_interface = child
    register_parent(child, owner, ("monitored_active_interface",), "single")
    return True


def setMonitoredActiveInterfacePath(monitoredActiveInterfaceID: str, path: str) -> bool:
    """Set path attribute on monitoredActiveInterface.

    Section: F.7.38.36.
    """
    child = resolve_handle(monitoredActiveInterfaceID)
    if not isinstance(child, MonitorInterfaceType):
        raise TgiError("Invalid monitoredActiveInterface handle", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(child, MonitorInterconnection)
    if not isinstance(owner, MonitorInterconnection):
        raise TgiError("Interface has no owning monitorInterconnection", TgiFaultCode.INVALID_ID)
    if getMonitorInterconnectionMonitoredActiveInterfaceID(get_handle(owner)) != monitoredActiveInterfaceID:
        raise TgiError("Interface is not the owning monitored active interface", TgiFaultCode.INVALID_ID)
    child.path = _name(path, "instancePath")
    return True


def setPowerDomainLinkExternalPowerDomainRef(powerDomainLinkID: str, expression: str) -> bool:
    """Set external power domain reference expression.

    Section: F.7.38.37.
    """
    expression_id = getPowerDomainLinkExternalPowerDomainRefID(powerDomainLinkID)
    if expression_id is not None:
        return setExpressionValue(expression_id, expression)
    child = StringExpression()
    child.value = _expression_source(expression, child)
    link = resolve_handle(powerDomainLinkID)
    if not isinstance(link, PowerDomainLinks.PowerDomainLink):
        raise TgiError("Invalid powerDomainLink handle", TgiFaultCode.INVALID_ID)
    link.external_power_domain_reference = child
    register_parent(child, link, ("external_power_domain_reference",), "single")
    return True
