"""Power Annex contracts, scoped references, atomic edits and owned lifecycle."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import power as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentInstance,
    ConfigurableLibraryRefType,
    InstanceName,
    PortTransactionalType,
    PortWireType,
)
from org.accellera.ipxact.v1685_2022.direction import Direction

_BASE = [
    ("getPortTransactionalPowerConstraintIDs", "transactionalID"),
    ("getPortWirePowerConstraintIDs", "wireID"),
    ("getPowerConstraintPowerDomainRefByID", "powerConstraintID"),
    ("getPowerConstraintPowerDomainRefByName", "powerConstraintID"),
    ("getPowerConstraintRange", "powerConstraintID"),
    ("getPowerConstraintRangeLeftID", "powerConstraintID"),
    ("getPowerConstraintRangeRightID", "powerConstraintID"),
    ("getPowerDomainAlwaysOn", "powerDomainID"),
    ("getPowerDomainAlwaysOnExpression", "powerDomainID"),
    ("getPowerDomainAlwaysOnID", "powerDomainID"),
    ("getPowerDomainName", "powerDomainID"),
    ("getPowerDomainSubDomainOf", "powerDomainID"),
    ("getPowerDomainSubDomainOfRefByID", "powerDomainID"),
]
_EXTENDED = [
    ("addComponentInstancePowerDomainLink", "componentInstanceID,externalPowerDomainRef,internalPowerDomainRef"),
    ("addComponentPowerDomain", "componentID,name"),
    ("addPortTransactionalPowerConstraint", "transactionalID,powerDomainRef"),
    ("addPortWirePowerConstraint", "wireID,powerDomainRef"),
    ("addPowerDomainLinkInternalPowerDomainReference", "powerDomainLinkID,internalPowerDomainReference"),
    ("removeComponentInstancePowerDomainLink", "powerDomainRefID"),
    ("removeComponentPowerDomain", "powerDomainID"),
    ("removePowerConstraintRange", "powerConstraintID"),
    ("removePowerDomainLinkInternalPowerDomainRef", "powerDomainLinkID,internalPowerDomainRef"),
    ("removePowerDomainSubDomainOf", "powerDomainID"),
    ("setPowerConstraintPowerDomainRef", "powerConstraintID,powerDomainRef"),
    ("setPowerConstraintRange", "powerConstraintID,range"),
    ("setPowerDomainAlwaysOn", "powerDomainID,alwaysOn"),
    ("setPowerDomainSubDomainOf", "powerDomainID,subDomainOf"),
]


@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear()
    yield
    registry.clear()


def _component(name="root"):
    root = Component(vendor="v", library="l", name=name, version="1")
    root_id = get_handle(root)
    first_id = api.addComponentPowerDomain(root_id, "core")
    second_id = api.addComponentPowerDomain(root_id, "parent")
    return root, root_id, first_id, second_id


def _instance():
    return ComponentInstance(
        instance_name=InstanceName(value="inst"),
        component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="child", version="1"),
    )


@pytest.mark.parametrize(
    "name,args,section",
    [
        *[(name, args, f"F.7.71.{i}") for i, (name, args) in enumerate(_BASE, 1)],
        *[(name, args, f"F.7.72.{i}") for i, (name, args) in enumerate(_EXTENDED, 1)],
    ],
)
def test_exact_annex_signatures_exports_and_static_docs(name, args, section):
    function = getattr(api, name)
    assert list(inspect.signature(function).parameters) == args.split(",")
    assert name in api.__all__ and getattr(tgi, name) is function
    assert "Args:" in function.__doc__ and "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


@pytest.mark.parametrize("name,args", _BASE)
def test_base_getters_reject_invalid_handle_types(name, args):
    with pytest.raises(TgiError):
        getattr(api, name)(get_handle(object()))


def test_constraints_use_wire_and_transactional_handles_and_keep_order():
    wire = PortWireType(direction=Direction.IN)
    transactional = PortTransactionalType(initiative="requires")
    wire_id, tx_id = get_handle(wire), get_handle(transactional)
    assert api.getPortWirePowerConstraintIDs(wire_id) == []
    assert api.getPortTransactionalPowerConstraintIDs(tx_id) == []
    wire_first = api.addPortWirePowerConstraint(wire_id, "core")
    wire.power_constraints.power_constraint = tuple(wire.power_constraints.power_constraint)
    wire_second = api.addPortWirePowerConstraint(wire_id, "core")
    tx_first = api.addPortTransactionalPowerConstraint(tx_id, "core")
    assert api.getPortWirePowerConstraintIDs(wire_id) == [wire_first, wire_second]
    assert api.getPortTransactionalPowerConstraintIDs(tx_id) == [tx_first]
    assert api.getPowerConstraintPowerDomainRefByName(wire_first) == "core"
    assert api.getPowerConstraintPowerDomainRefByName(tx_first) == "core"
    for getter in [api.getPowerConstraintRange, api.getPowerConstraintRangeLeftID, api.getPowerConstraintRangeRightID]:
        assert getter(tx_first) is None
    assert not api.removePowerConstraintRange(tx_first)
    with pytest.raises(TgiError):
        api.setPowerConstraintRange(tx_first, ["7", "0"])


def test_domain_reference_getters_are_local_and_handle_targets_differ_from_source():
    root, _, core_id, parent_id = _component()
    foreign, _, _, foreign_parent = _component("foreign")
    registry.register(root, ["v", "l", "root", "1"])
    registry.register(foreign, ["v", "l", "foreign", "1"])
    assert api.getPowerDomainName(core_id) == "core"
    assert api.getPowerDomainSubDomainOf(core_id) is None
    assert api.getPowerDomainSubDomainOfRefByID(core_id) is None
    assert api.setPowerDomainSubDomainOf(core_id, "parent")
    assert api.getPowerDomainSubDomainOf(core_id) == "parent"
    assert api.getPowerDomainSubDomainOfRefByID(core_id) == parent_id
    assert api.getPowerDomainSubDomainOfRefByID(core_id) != foreign_parent
    assert api.setPowerDomainSubDomainOf(core_id, "unknown")
    assert api.getPowerDomainSubDomainOfRefByID(core_id) is None
    assert api.removePowerDomainSubDomainOf(core_id)
    assert not api.removePowerDomainSubDomainOf(core_id)


def test_always_on_evaluates_bits_and_preserves_source_wrapper_metadata():
    _, _, domain_id, _ = _component()
    assert api.getPowerDomainAlwaysOn(domain_id) is None
    assert api.getPowerDomainAlwaysOnExpression(domain_id) is None
    assert api.getPowerDomainAlwaysOnID(domain_id) is None
    assert api.setPowerDomainAlwaysOn(domain_id, "1'b1")
    assert api.getPowerDomainAlwaysOn(domain_id) is True
    wrapper_id = api.getPowerDomainAlwaysOnID(domain_id)
    wrapper = resolve_handle(wrapper_id)
    wrapper.other_attributes = {"{urn:test}marker": "always"}
    assert api.setPowerDomainAlwaysOn(domain_id, "0")
    assert api.getPowerDomainAlwaysOn(domain_id) is False
    assert api.setPowerDomainAlwaysOn(domain_id, "ALWAYS_POWERED")
    assert api.getPowerDomainAlwaysOnExpression(domain_id) == "ALWAYS_POWERED"
    with pytest.raises(TgiError):
        api.getPowerDomainAlwaysOn(domain_id)
    assert api.getPowerDomainAlwaysOnID(domain_id) == wrapper_id
    assert wrapper.other_attributes == {"{urn:test}marker": "always"}
    api.setPowerDomainSubDomainOf(domain_id, "parent")
    assert api.removePowerDomainSubDomainOf(domain_id)
    assert api.getPowerDomainAlwaysOnExpression(domain_id) == "ALWAYS_POWERED"


@pytest.mark.parametrize("value", [None, True, 1, "", "2", "-1", "1.5", "8'hxx", "1 +", "bad\x00text"])
def test_always_on_invalid_values_reject_atomically(value):
    _, _, domain_id, _ = _component()
    api.setPowerDomainAlwaysOn(domain_id, "1")
    wrapper = resolve_handle(domain_id).always_on
    with pytest.raises(TgiError):
        api.setPowerDomainAlwaysOn(domain_id, value)
    assert resolve_handle(domain_id).always_on is wrapper
    assert wrapper.value == "1"


@pytest.mark.parametrize(
    "range",
    [
        None,
        "7:0",
        [],
        ["7"],
        ["7", "0", "1"],
        ["7", None],
        ["7", "-1"],
        ["4294967296", "0"],
        ["7", "1 +"],
        ["7", "8'hxx"],
    ],
)
def test_range_invalid_inputs_reject_without_changing_wrapper(range):
    wire = PortWireType(direction=Direction.IN)
    constraint_id = api.addPortWirePowerConstraint(get_handle(wire), "core")
    api.setPowerConstraintRange(constraint_id, ["7", "0"])
    wrapper = resolve_handle(constraint_id).range
    with pytest.raises(TgiError):
        api.setPowerConstraintRange(constraint_id, range)
    assert resolve_handle(constraint_id).range is wrapper
    assert api.getPowerConstraintRange(constraint_id) == ["7", "0"]


def test_wire_range_source_triplet_metadata_bounds_and_removal_invalidation():
    wire = PortWireType(direction=Direction.IN)
    constraint_id = api.addPortWirePowerConstraint(get_handle(wire), "core")
    assert api.setPowerConstraintRange(constraint_id, ["HIGH", "LOW"])
    assert api.getPowerConstraintRange(constraint_id) == ["HIGH", "LOW"]
    left_id, right_id = (
        api.getPowerConstraintRangeLeftID(constraint_id),
        api.getPowerConstraintRangeRightID(constraint_id),
    )
    wrapper = resolve_handle(constraint_id).range
    range_id = get_handle(wrapper)
    wrapper.left.other_attributes = {"{urn:test}marker": "left"}
    wrapper.left.minimum = 2
    with pytest.raises(TgiError):
        api.setPowerConstraintRange(constraint_id, ["1", "0"])
    assert api.setPowerConstraintRange(constraint_id, ["32'hFFFF_FFFF", "0"])
    assert api.getPowerConstraintRange(constraint_id) == ["32'hFFFF_FFFF", "0"]
    assert api.getPowerConstraintRangeLeftID(constraint_id) == left_id
    assert api.getPowerConstraintRangeRightID(constraint_id) == right_id
    assert wrapper.left.other_attributes == {"{urn:test}marker": "left"}
    assert api.removePowerConstraintRange(constraint_id)
    assert not api.removePowerConstraintRange(constraint_id)
    for handle in [range_id, left_id, right_id]:
        assert resolve_handle(handle) is None


@pytest.mark.parametrize("name", [None, True, "", "two names", "9name", "bad\x00name"])
def test_domain_names_and_reference_names_validate_atomically(name):
    root, root_id, domain_id, _ = _component()
    before = list(root.power_domains.power_domain)
    with pytest.raises(TgiError):
        api.addComponentPowerDomain(root_id, name)
    assert root.power_domains.power_domain == before
    with pytest.raises(TgiError):
        api.setPowerDomainSubDomainOf(domain_id, name)
    assert resolve_handle(domain_id).sub_domain_of is None
    wire = PortWireType(direction=Direction.IN)
    with pytest.raises(TgiError):
        api.addPortWirePowerConstraint(get_handle(wire), name)
    assert wire.power_constraints is None


def test_instance_link_factories_uniqueness_source_and_lifecycle():
    instance = _instance()
    instance_id = get_handle(instance)
    link_id = api.addComponentInstancePowerDomainLink(instance_id, '"top_domain"', ["core", "aux"])
    link = resolve_handle(link_id)
    assert link.external_power_domain_reference.value == '"top_domain"'
    assert [ref.value for ref in link.internal_power_domain_reference] == ["core", "aux"]
    first_ref_id = get_handle(link.internal_power_domain_reference[0])
    external_id = get_handle(link.external_power_domain_reference)
    holder_id = get_handle(instance.power_domain_links)
    assert api.addPowerDomainLinkInternalPowerDomainReference(link_id, "third") is True
    before = list(instance.power_domain_links.power_domain_link)
    with pytest.raises(TgiError):
        api.addComponentInstancePowerDomainLink(instance_id, '"other"', ["core"])
    with pytest.raises(TgiError):
        api.addPowerDomainLinkInternalPowerDomainReference(link_id, "aux")
    assert instance.power_domain_links.power_domain_link == before
    instance.power_domain_links.power_domain_link = tuple(instance.power_domain_links.power_domain_link)
    link.internal_power_domain_reference = tuple(link.internal_power_domain_reference)
    assert api.removePowerDomainLinkInternalPowerDomainRef(link_id, "core")
    assert resolve_handle(first_ref_id) is None
    assert api.removePowerDomainLinkInternalPowerDomainRef(link_id, "aux")
    assert not api.removePowerDomainLinkInternalPowerDomainRef(link_id, "third")
    assert not api.removePowerDomainLinkInternalPowerDomainRef(link_id, "unknown")
    last_ref_id = get_handle(link.internal_power_domain_reference[0])
    assert api.removeComponentInstancePowerDomainLink(link_id)
    assert instance.power_domain_links is None
    for handle in [link_id, last_ref_id, external_id, holder_id]:
        assert resolve_handle(handle) is None


@pytest.mark.parametrize(
    "external,internal",
    [
        (None, ["core"]),
        ("", ["core"]),
        ("bad\x00text", ["core"]),
        ("top", None),
        ("top", "core"),
        ("top", []),
        ("top", ["core", "core"]),
        ("top", ["bad name"]),
    ],
)
def test_link_invalid_inputs_do_not_create_optional_holder(external, internal):
    instance = _instance()
    with pytest.raises(TgiError):
        api.addComponentInstancePowerDomainLink(get_handle(instance), external, internal)
    assert instance.power_domain_links is None


def test_power_domain_duplicate_names_tuple_removal_and_descendant_handles():
    root, root_id, core_id, parent_id = _component()
    with pytest.raises(TgiError):
        api.addComponentPowerDomain(root_id, "core")
    api.setPowerDomainAlwaysOn(core_id, "1")
    wrapper_id = api.getPowerDomainAlwaysOnID(core_id)
    root.power_domains.power_domain = tuple(root.power_domains.power_domain)
    assert api.removeComponentPowerDomain(core_id)
    assert resolve_handle(core_id) is None and resolve_handle(wrapper_id) is None
    assert api.removeComponentPowerDomain(parent_id)
    assert root.power_domains is None


def test_internal_reference_removal_cannot_remove_from_another_link():
    instance = _instance()
    one = api.addComponentInstancePowerDomainLink(get_handle(instance), "top", ["a", "b"])
    two = api.addComponentInstancePowerDomainLink(get_handle(instance), "top", ["c", "d"])
    foreign_ref_id = get_handle(resolve_handle(two).internal_power_domain_reference[0])
    assert not api.removePowerDomainLinkInternalPowerDomainRef(one, "c")
    assert not api.removePowerDomainLinkInternalPowerDomainRef(one, foreign_ref_id)
    assert resolve_handle(foreign_ref_id) is not None


def test_domain_reference_lookup_applies_xml_name_whitespace_and_rejects_ambiguity():
    root, _, core_id, parent_id = _component()
    resolve_handle(parent_id).name = " parent "
    resolve_handle(core_id).sub_domain_of = "\tparent\n"
    assert api.getPowerDomainSubDomainOfRefByID(core_id) == parent_id
    root.power_domains.power_domain.append(root.power_domains.power_domain[-1])
    with pytest.raises(TgiError):
        api.getPowerDomainSubDomainOfRefByID(core_id)
