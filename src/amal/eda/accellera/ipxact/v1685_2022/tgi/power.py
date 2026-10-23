"""IEEE 1685-2022 Power operations (F.7.71 and F.7.72).

Constraints are accessed through wire/transactional child handles. References
resolve within the owning component; source text is distinct from target IDs.
Generated expressions retain identity and metadata. Known constants are checked
before mutation; configured expression environments remain separate work.
"""

from collections.abc import Sequence
from typing import Any

from org.accellera.ipxact.v1685_2022.always_on import AlwaysOn
from org.accellera.ipxact.v1685_2022.component_instance import ComponentInstance
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.port_transactional_type import PortTransactionalType
from org.accellera.ipxact.v1685_2022.port_wire_type import PortWireType
from org.accellera.ipxact.v1685_2022.power_domain_links import PowerDomainLinks
from org.accellera.ipxact.v1685_2022.power_domain_ref import PowerDomainRef
from org.accellera.ipxact.v1685_2022.range import Range
from org.accellera.ipxact.v1685_2022.right import Right
from org.accellera.ipxact.v1685_2022.string_expression import StringExpression
from org.accellera.ipxact.v1685_2022.transactional_power_constraint_type import TransactionalPowerConstraintType
from org.accellera.ipxact.v1685_2022.wire_power_constraint_type import WirePowerConstraintType

from ._attribute_references import _root_for
from .address_space import _register_owned_child
from .component import _list_attr, _register_graph
from .core import TgiError, TgiFaultCode, detach_child_by_handle, get_handle, register_parent, resolve_handle
from .cpu import _xml_text
from .port_map import (
    _apply_range,
    _array,
    _child,
    _child_id,
    _integer,
    _name,
    _range_plan,
    _remove_child,
    _require,
    _source,
)

__all__ = [
    # BASE (F.7.71)
    "getPortTransactionalPowerConstraintIDs",
    "getPortWirePowerConstraintIDs",
    "getPowerConstraintPowerDomainRefByID",
    "getPowerConstraintPowerDomainRefByName",
    "getPowerConstraintRange",
    "getPowerConstraintRangeLeftID",
    "getPowerConstraintRangeRightID",
    "getPowerDomainAlwaysOn",
    "getPowerDomainAlwaysOnExpression",
    "getPowerDomainAlwaysOnID",
    "getPowerDomainName",
    "getPowerDomainSubDomainOf",
    "getPowerDomainSubDomainOfRefByID",
    # EXTENDED (F.7.72)
    "addComponentInstancePowerDomainLink",
    "addComponentPowerDomain",
    "addPortTransactionalPowerConstraint",
    "addPortWirePowerConstraint",
    "addPowerDomainLinkInternalPowerDomainReference",
    "removeComponentInstancePowerDomainLink",
    "removeComponentPowerDomain",
    "removePowerConstraintRange",
    "removePowerDomainLinkInternalPowerDomainRef",
    "removePowerDomainSubDomainOf",
    "setPowerConstraintPowerDomainRef",
    "setPowerConstraintRange",
    "setPowerDomainAlwaysOn",
    "setPowerDomainSubDomainOf",
]

_PowerDomain = ComponentType.PowerDomains.PowerDomain
_PowerDomainLink = PowerDomainLinks.PowerDomainLink
_InternalReference = _PowerDomainLink.InternalPowerDomainReference
_Constraint = (WirePowerConstraintType, TransactionalPowerConstraintType)


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _constraint(handle: str) -> WirePowerConstraintType | TransactionalPowerConstraintType:
    obj = resolve_handle(handle) if isinstance(handle, str) else None
    if not isinstance(obj, _Constraint):
        raise TgiError("Invalid power constraint handle", TgiFaultCode.INVALID_ID)
    return obj


def _range(constraint: Any) -> Range | None:
    return _child(constraint, "range", Range) if isinstance(constraint, WirePowerConstraintType) else None


def _target(source: Any, name: str | None) -> str | None:
    root = _root_for(source)
    if name is None or not isinstance(root, ComponentType) or root.power_domains is None:
        return None
    name = _name(name, "Name")
    matches = [domain for domain in root.power_domains.power_domain if _name(domain.name, "Name") == name]
    if len(matches) > 1:
        raise TgiError("Ambiguous power domain reference", TgiFaultCode.INVALID_ARGUMENT)
    if not matches:
        return None
    _register_graph(root)
    return get_handle(matches[0])


def _constraint_ids(parent: Any, cls: type) -> list[str]:
    holder = parent.power_constraints
    if holder is None:
        return []
    _register_graph(parent)
    if any(not isinstance(item, cls) for item in holder.power_constraint):
        raise TgiError("Invalid power constraint model", TgiFaultCode.INVALID_ID)
    return [get_handle(item) for item in holder.power_constraint]


def _add_constraint(parent: Any, cls: type, holder_cls: type, power_domain_ref: str) -> str:
    name = _name(power_domain_ref, "Name")
    constraint = cls(power_domain_ref=PowerDomainRef(value=name))
    if parent.power_constraints is None:
        parent.power_constraints = holder_cls()
    holder = parent.power_constraints
    register_parent(holder, parent, ("power_constraints",), "single")
    _list_attr(holder, "power_constraint").append(constraint)
    register_parent(constraint, holder, ("power_constraint",), "list")
    _register_graph(constraint)
    return get_handle(constraint)


def _link_scope(link: Any) -> PowerDomainLinks | None:
    return _register_owned_child(link, PowerDomainLinks)


def _internal_names(links: Sequence[Any]) -> list[str]:
    return [_name(ref.value, "Name") for link in links for ref in link.internal_power_domain_reference]


def _check_internal_unique(names: Sequence[str], links: Sequence[Any]) -> None:
    if len(set(names)) != len(names) or set(names).intersection(_internal_names(links)):
        raise TgiError("Internal power domain already linked on this instance", TgiFaultCode.ALREADY_EXISTS)


def _remove_owned(handle: str, cls: type, holder_cls: type, owner_cls: type, owner_attr: str, list_attr: str) -> bool:
    child = _require(handle, cls)
    holder = _register_owned_child(child, holder_cls)
    if holder is None:
        raise TgiError("Element has no registered owning container", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(holder, owner_cls)
    _list_attr(holder, list_attr)
    _register_graph(holder)
    if not detach_child_by_handle(handle):
        return False
    if not getattr(holder, list_attr) and owner is not None:
        _remove_child(owner, owner_attr)
    return True


# ---------------------------------------------------------------------------
# BASE (F.7.71)
# ---------------------------------------------------------------------------


def getPortTransactionalPowerConstraintIDs(transactionalID: str) -> list[str]:
    """Return transactional power-constraint handles in source order.

    Args:
        transactionalID: Handle to a port transactional child.

    Returns:
        Child handles in source order; an empty list when the optional holder is absent.

    Section: F.7.71.1.
    """
    return _constraint_ids(_require(transactionalID, PortTransactionalType), TransactionalPowerConstraintType)


def getPortWirePowerConstraintIDs(wireID: str) -> list[str]:
    """Return wire power-constraint handles in source order.

    Args:
        wireID: Handle to a port wire child.

    Returns:
        Child handles in source order; an empty list when the optional holder is absent.

    Section: F.7.71.2.
    """
    return _constraint_ids(_require(wireID, PortWireType), WirePowerConstraintType)


def getPowerConstraintPowerDomainRefByID(powerConstraintID: str) -> str | None:
    """Resolve the referenced power domain within the owning component.

    Args:
        powerConstraintID: Handle to a wire or transactional powerConstraint.

    Returns:
        Target domain handle, or None for an unavailable target. Ambiguous targets fault.

    Section: F.7.71.3.
    """
    constraint = _constraint(powerConstraintID)
    reference = _child(constraint, "power_domain_ref", PowerDomainRef)
    if reference is None:
        raise TgiError("Power constraint lacks required powerDomainRef", TgiFaultCode.INVALID_ID)
    return _target(constraint, reference.value)


def getPowerConstraintPowerDomainRefByName(powerConstraintID: str) -> str:
    """Return the stored powerDomainRef name without target lookup.

    Args:
        powerConstraintID: Handle to a wire or transactional powerConstraint.

    Returns:
        Exact stored lexical text, or None for optional content that is absent.

    Section: F.7.71.4.
    """
    reference = _child(_constraint(powerConstraintID), "power_domain_ref", PowerDomainRef)
    if reference is None:
        raise TgiError("Power constraint lacks required powerDomainRef", TgiFaultCode.INVALID_ID)
    return reference.value


def getPowerConstraintRange(powerConstraintID: str) -> list[str] | None:
    """Return the stored left and right range sources of a wire power constraint.

    Args:
        powerConstraintID: Handle to a wire or transactional powerConstraint.

    Returns:
        Two stored source strings [left, right], or None for absent ranges and transactional constraints.

    Section: F.7.71.5.
    """
    value = _range(_constraint(powerConstraintID))
    return [value.left.value, value.right.value] if value is not None else None


def getPowerConstraintRangeLeftID(powerConstraintID: str) -> str | None:
    """Return the owned left range expression handle of a wire power constraint.

    Args:
        powerConstraintID: Handle to a wire or transactional powerConstraint.

    Returns:
        Owned expression handle, or None when optional content is absent or inapplicable.

    Section: F.7.71.6.
    """
    value = _range(_constraint(powerConstraintID))
    return _child_id(value, "left", Left) if value is not None else None


def getPowerConstraintRangeRightID(powerConstraintID: str) -> str | None:
    """Return the owned right range expression handle of a wire power constraint.

    Args:
        powerConstraintID: Handle to a wire or transactional powerConstraint.

    Returns:
        Owned expression handle, or None when optional content is absent or inapplicable.

    Section: F.7.71.7.
    """
    value = _range(_constraint(powerConstraintID))
    return _child_id(value, "right", Right) if value is not None else None


def getPowerDomainAlwaysOn(powerDomainID: str) -> bool | None:
    """Return the resolved unsigned-bit alwaysOn value.

    Args:
        powerDomainID: Handle to a component powerDomain.

    Returns:
        Resolved Boolean, or None when absent. Unresolved or non-bit values fault INVALID_ARGUMENT.

    Section: F.7.71.8.
    """
    value = _child(_require(powerDomainID, _PowerDomain), "always_on", AlwaysOn)
    return bool(_integer(value.value, 1)) if value is not None else None


def getPowerDomainAlwaysOnExpression(powerDomainID: str) -> str | None:
    """Return the exact alwaysOn source expression.

    Args:
        powerDomainID: Handle to a component powerDomain.

    Returns:
        Exact stored lexical text, or None for optional content that is absent.

    Section: F.7.71.9.
    """
    value = _child(_require(powerDomainID, _PowerDomain), "always_on", AlwaysOn)
    return value.value if value is not None else None


def getPowerDomainAlwaysOnID(powerDomainID: str) -> str | None:
    """Return the owned alwaysOn expression handle.

    Args:
        powerDomainID: Handle to a component powerDomain.

    Returns:
        Owned expression handle, or None when optional content is absent or inapplicable.

    Section: F.7.71.10.
    """
    return _child_id(_require(powerDomainID, _PowerDomain), "always_on", AlwaysOn)


def getPowerDomainName(powerDomainID: str) -> str:
    """Return the stored power domain name.

    Args:
        powerDomainID: Handle to a component powerDomain.

    Returns:
        Exact stored lexical text, or None for optional content that is absent.

    Section: F.7.71.11.
    """
    return _require(powerDomainID, _PowerDomain).name


def getPowerDomainSubDomainOf(powerDomainID: str) -> str | None:
    """Return the stored parent power domain name.

    Args:
        powerDomainID: Handle to a component powerDomain.

    Returns:
        Exact stored lexical text, or None for optional content that is absent.

    Section: F.7.71.12.
    """
    return _require(powerDomainID, _PowerDomain).sub_domain_of


def getPowerDomainSubDomainOfRefByID(powerDomainID: str) -> str | None:
    """Resolve the parent power domain within the owning component.

    Args:
        powerDomainID: Handle to a component powerDomain.

    Returns:
        Target domain handle, or None for an unavailable target. Ambiguous targets fault.

    Section: F.7.71.13.
    """
    domain = _require(powerDomainID, _PowerDomain)
    return _target(domain, domain.sub_domain_of)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.72)
# ---------------------------------------------------------------------------


def addComponentInstancePowerDomainLink(
    componentInstanceID: str, externalPowerDomainRef: str, internalPowerDomainRef: Sequence[str]
) -> str:
    """Add a typed instance link with one external expression and nonempty internal references.

    Args:
        componentInstanceID: Handle to a componentInstance.
        externalPowerDomainRef: String-expression source referring to a domain on the component referencing the design.
        internalPowerDomainRef: Nonempty sequence of XML Names referring to domains of the instance component.

    Returns:
        Handle to the newly owned generated element.

    Section: F.7.72.1.
    """
    instance = _require(componentInstanceID, ComponentInstance)
    _xml_text(externalPowerDomainRef)
    if not externalPowerDomainRef.strip():
        raise TgiError("External power domain reference must be nonempty", TgiFaultCode.INVALID_ARGUMENT)
    names = [_name(value, "Name") for value in _array(internalPowerDomainRef, "internalPowerDomainRef")]
    if not names:
        raise TgiError("At least one internal power domain is required", TgiFaultCode.INVALID_ARGUMENT)
    holder = instance.power_domain_links
    _check_internal_unique(names, holder.power_domain_link if holder is not None else [])
    link = _PowerDomainLink(
        external_power_domain_reference=StringExpression(value=externalPowerDomainRef),
        internal_power_domain_reference=[_InternalReference(value=name) for name in names],
    )
    if holder is None:
        holder = PowerDomainLinks()
        instance.power_domain_links = holder
    register_parent(holder, instance, ("power_domain_links",), "single")
    _list_attr(holder, "power_domain_link").append(link)
    register_parent(link, holder, ("power_domain_link",), "list")
    _register_graph(link)
    return get_handle(link)


def addComponentPowerDomain(componentID: str, name: str) -> str:
    """Add a uniquely named power domain to the component.

    Args:
        componentID: Handle to a component.
        name: Unique XML Name of the new power domain.

    Returns:
        Handle to the newly owned generated element.

    Section: F.7.72.2.
    """
    component = _require(componentID, ComponentType)
    name = _name(name, "Name")
    holder = component.power_domains
    if holder is not None and any(_name(domain.name, "Name") == name for domain in holder.power_domain):
        raise TgiError("Power domain name already exists", TgiFaultCode.ALREADY_EXISTS)
    domain = _PowerDomain(name=name)
    if holder is None:
        holder = ComponentType.PowerDomains()
        component.power_domains = holder
    register_parent(holder, component, ("power_domains",), "single")
    _list_attr(holder, "power_domain").append(domain)
    register_parent(domain, holder, ("power_domain",), "list")
    return get_handle(domain)


def addPortTransactionalPowerConstraint(transactionalID: str, powerDomainRef: str) -> str:
    """Add a typed power constraint to a transactional port element.

    Args:
        transactionalID: Handle to a port transactional child.
        powerDomainRef: XML Name of the referenced domain on the enclosing component.

    Returns:
        Handle to the newly owned generated element.

    Section: F.7.72.3.
    """
    return _add_constraint(
        _require(transactionalID, PortTransactionalType),
        TransactionalPowerConstraintType,
        PortTransactionalType.PowerConstraints,
        powerDomainRef,
    )


def addPortWirePowerConstraint(wireID: str, powerDomainRef: str) -> str:
    """Add a typed power constraint to a wire port element.

    Args:
        wireID: Handle to a port wire child.
        powerDomainRef: XML Name of the referenced domain on the enclosing component.

    Returns:
        Handle to the newly owned generated element.

    Section: F.7.72.4.
    """
    return _add_constraint(
        _require(wireID, PortWireType), WirePowerConstraintType, PortWireType.PowerConstraints, powerDomainRef
    )


def addPowerDomainLinkInternalPowerDomainReference(powerDomainLinkID: str, internalPowerDomainReference: str) -> bool:
    """Append an internal domain reference unique across this instance's links.

    Args:
        powerDomainLinkID: Handle to an instance powerDomainLink.
        internalPowerDomainReference: XML Name of an additional internal domain reference.

    Returns:
        True on success. Invalid arguments fault before mutation.

    Section: F.7.72.5.
    """
    link = _require(powerDomainLinkID, _PowerDomainLink)
    name = _name(internalPowerDomainReference, "Name")
    holder = _link_scope(link)
    _check_internal_unique([name], holder.power_domain_link if holder is not None else [link])
    reference = _InternalReference(value=name)
    _list_attr(link, "internal_power_domain_reference").append(reference)
    register_parent(reference, link, ("internal_power_domain_reference",), "list")
    return True


def removeComponentInstancePowerDomainLink(powerDomainRefID: str) -> bool:
    """Remove an owned instance power-domain link and prune an empty optional holder.

    Args:
        powerDomainRefID: Handle to the powerDomainLink to remove, using the Annex argument name.

    Returns:
        True if removed; False for absent or inapplicable optional content. Invalid or unowned handles fault.

    Section: F.7.72.6.
    """
    return _remove_owned(
        powerDomainRefID,
        _PowerDomainLink,
        PowerDomainLinks,
        ComponentInstance,
        "power_domain_links",
        "power_domain_link",
    )


def removeComponentPowerDomain(powerDomainID: str) -> bool:
    """Remove an owned component power domain and prune an empty optional holder.

    Args:
        powerDomainID: Handle to a component powerDomain.

    Returns:
        True if removed; False for absent or inapplicable optional content. Invalid or unowned handles fault.

    Section: F.7.72.7.
    """
    return _remove_owned(
        powerDomainID, _PowerDomain, ComponentType.PowerDomains, ComponentType, "power_domains", "power_domain"
    )


def removePowerConstraintRange(powerConstraintID: str) -> bool:
    """Remove a wire power-constraint range and invalidate its descendant handles.

    Args:
        powerConstraintID: Handle to a wire or transactional powerConstraint.

    Returns:
        True if removed; False for absent or inapplicable optional content. Invalid or unowned handles fault.

    Section: F.7.72.8.
    """
    constraint = _constraint(powerConstraintID)
    return _remove_child(constraint, "range") if isinstance(constraint, WirePowerConstraintType) else False


def removePowerDomainLinkInternalPowerDomainRef(powerDomainLinkID: str, internalPowerDomainRef: str) -> bool:
    """Remove the matching internal domain reference while retaining the required final reference.

    Args:
        powerDomainLinkID: Handle to an instance powerDomainLink.
        internalPowerDomainRef: Internal XML Name reference to remove.

    Returns:
        True if removed; False when unmatched or when only the required final reference remains.

    Section: F.7.72.9.
    """
    link = _require(powerDomainLinkID, _PowerDomainLink)
    name = _name(internalPowerDomainRef, "Name")
    matches = [ref for ref in link.internal_power_domain_reference if _name(ref.value, "Name") == name]
    if len(matches) > 1:
        raise TgiError("Ambiguous internal power domain reference", TgiFaultCode.INVALID_ARGUMENT)
    if not matches or len(link.internal_power_domain_reference) == 1:
        return False
    _list_attr(link, "internal_power_domain_reference")
    _register_graph(link)
    return detach_child_by_handle(get_handle(matches[0]))


def removePowerDomainSubDomainOf(powerDomainID: str) -> bool:
    """Remove subDomainOf while preserving the independent alwaysOn expression.

    Args:
        powerDomainID: Handle to a component powerDomain.

    Returns:
        True if removed; False for absent or inapplicable optional content. Invalid or unowned handles fault.

    Section: F.7.72.10.
    """
    domain = _require(powerDomainID, _PowerDomain)
    if domain.sub_domain_of is None:
        return False
    domain.sub_domain_of = None
    return True


def setPowerConstraintPowerDomainRef(powerConstraintID: str, powerDomainRef: str) -> bool:
    """Set the powerDomainRef name while preserving the generated reference wrapper.

    Args:
        powerConstraintID: Handle to a wire or transactional powerConstraint.
        powerDomainRef: XML Name of the referenced domain on the enclosing component.

    Returns:
        True on success. Invalid arguments fault before mutation.

    Section: F.7.72.11.
    """
    constraint = _constraint(powerConstraintID)
    name = _name(powerDomainRef, "Name")
    current = _child(constraint, "power_domain_ref", PowerDomainRef)
    if current is None:
        current = PowerDomainRef(value=name)
        constraint.power_domain_ref = current
    else:
        current.value = name
    register_parent(current, constraint, ("power_domain_ref",), "single")
    return True


def setPowerConstraintRange(powerConstraintID: str, range: Sequence[str]) -> bool:
    """Set wire range source expressions atomically while preserving wrappers and metadata.

    Args:
        powerConstraintID: Handle to a wire or transactional powerConstraint.
        range: Exactly two unsigned 32-bit expression sources [left, right].

    Returns:
        True on success. Invalid arguments fault before mutation.

    Section: F.7.72.12.
    """
    constraint = _constraint(powerConstraintID)
    if not isinstance(constraint, WirePowerConstraintType):
        raise TgiError("Transactional power constraints have no range", TgiFaultCode.INVALID_ARGUMENT)
    values = _range_plan(range, constraint.range)
    constraint.range = _apply_range(constraint.range, values)
    register_parent(constraint.range, constraint, ("range",), "single")
    _register_graph(constraint.range)
    return True


def setPowerDomainAlwaysOn(powerDomainID: str, alwaysOn: str) -> bool:
    """Set an unsigned-bit alwaysOn expression while preserving its wrapper and metadata.

    Args:
        powerDomainID: Handle to a component powerDomain.
        alwaysOn: Unsigned-bit expression source; known constants must evaluate to 0 or 1.

    Returns:
        True on success. Invalid arguments fault before mutation.

    Section: F.7.72.13.
    """
    domain = _require(powerDomainID, _PowerDomain)
    current = _child(domain, "always_on", AlwaysOn)
    source = _source(alwaysOn, current, 1)
    if current is None:
        current = AlwaysOn(value=source)
        domain.always_on = current
    else:
        current.value = source
    register_parent(current, domain, ("always_on",), "single")
    return True


def setPowerDomainSubDomainOf(powerDomainID: str, subDomainOf: str) -> bool:
    """Set the stored parent domain name on the power domain.

    Args:
        powerDomainID: Handle to a component powerDomain.
        subDomainOf: XML Name of the referenced parent domain on this component.

    Returns:
        True on success. Invalid arguments fault before mutation.

    Section: F.7.72.14.
    """
    domain = _require(powerDomainID, _PowerDomain)
    name = _name(subDomainOf, "Name")
    domain.sub_domain_of = name
    return True
