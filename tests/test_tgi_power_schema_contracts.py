"""Power TGI edits retain the IEEE 1685-2022 schema structure."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import component as component_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import design as design_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import power as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, Design, DesignConfiguration
from org.accellera.ipxact.v1685_2022.component_instance import ComponentInstance
from org.accellera.ipxact.v1685_2022.component_instances import ComponentInstances
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.instance_name import InstanceName

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def top_level_registry_only(monkeypatch):
    registry.clear()
    register = registry.register

    def register_document(element, *args, **kwargs):
        assert isinstance(element, (Component, Design, DesignConfiguration))
        return register(element, *args, **kwargs)

    monkeypatch.setattr(registry, "register", register_document)
    yield
    registry.clear()


def _schema_valid(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    return xml


def _valid(root):
    xml = _schema_valid(root)
    assert XmlDocument.parser().from_string(xml, type(root)) == root
    return xml


def _component():
    return Component(vendor="v", library="l", name="power_component", version="1")


def _design_with_instance():
    instance = ComponentInstance(
        instance_name=InstanceName(value="u_power"),
        component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="child", version="1"),
    )
    design = Design(
        vendor="v",
        library="l",
        name="power_design",
        version="1",
        component_instances=ComponentInstances(component_instance=[instance]),
    )
    return design, instance


def _port_style_handle(port_handle):
    port = resolve_handle(port_handle)
    return get_handle(port.wire_or_transactional_or_structured)


def test_power_constraints_use_child_handles_and_round_trip_source_ranges_and_metadata():
    root = _component()
    root_handle = get_handle(root)
    main_domain_id = api.addComponentPowerDomain(root_handle, "PWR_MAIN")
    tx_domain_id = api.addComponentPowerDomain(root_handle, "PWR_TX")
    aux_domain_id = api.addComponentPowerDomain(root_handle, "PWR_AUX")
    assert api.getPowerDomainName(main_domain_id) == "PWR_MAIN"
    wire_port = component_api.addComponentWirePort(root_handle, "data", "in")
    tx_port = component_api.addComponentTransactionalPort(root_handle, "transaction", "requires")
    wire_id = _port_style_handle(wire_port)
    tx_id = _port_style_handle(tx_port)

    wire_constraint_id = api.addPortWirePowerConstraint(wire_id, "PWR_MAIN")
    tx_constraint_id = api.addPortTransactionalPowerConstraint(tx_id, "PWR_TX")
    wire_constraint = resolve_handle(wire_constraint_id)
    tx_constraint = resolve_handle(tx_constraint_id)
    wire_constraint.id = "wire_constraint_id"
    tx_constraint.id = "tx_constraint_id"

    assert api.setPowerConstraintRange(wire_constraint_id, ["WIDTH-1", "0"])
    assert api.getPortWirePowerConstraintIDs(wire_id) == [wire_constraint_id]
    assert api.getPortTransactionalPowerConstraintIDs(tx_id) == [tx_constraint_id]
    assert api.getPowerConstraintRange(wire_constraint_id) == ["WIDTH-1", "0"]
    assert api.getPowerConstraintRangeLeftID(wire_constraint_id)
    assert api.getPowerConstraintRangeRightID(wire_constraint_id)
    assert api.getPowerConstraintPowerDomainRefByID(tx_constraint_id) == tx_domain_id
    assert api.getPowerConstraintPowerDomainRefByName(tx_constraint_id) == "PWR_TX"

    left = wire_constraint.range.left
    right = wire_constraint.range.right
    left_handle, right_handle = get_handle(left), get_handle(right)
    left.minimum = 1
    left.other_attributes = {"{urn:example}marker": "left-metadata"}
    right.maximum = 31
    ref = wire_constraint.power_domain_ref
    ref_handle = get_handle(ref)
    assert api.setPowerConstraintPowerDomainRef(wire_constraint_id, "PWR_AUX")
    assert wire_constraint.power_domain_ref is ref
    assert get_handle(wire_constraint.power_domain_ref) == ref_handle
    assert wire_constraint.range.left is left and wire_constraint.range.right is right
    assert get_handle(wire_constraint.range.left) == left_handle
    assert get_handle(wire_constraint.range.right) == right_handle
    assert left.other_attributes["{urn:example}marker"] == "left-metadata"
    assert api.getPowerConstraintPowerDomainRefByName(wire_constraint_id) == "PWR_AUX"
    assert api.getPowerConstraintPowerDomainRefByID(wire_constraint_id) == aux_domain_id

    before = _valid(root)
    with pytest.raises(TgiError):
        api.setPowerConstraintRange(wire_constraint_id, ["7"])
    with pytest.raises(TgiError):
        api.setPowerConstraintRange(tx_constraint_id, ["7", "0"])
    assert _valid(root) == before

    parsed = XmlDocument.parser().from_string(before, Component)
    registry.register(parsed, ["v", "l", "power_component", "1"])
    parsed_wire = parsed.model.ports.port[0]
    parsed_tx = parsed.model.ports.port[1]
    parsed_wire_style = get_handle(parsed_wire.wire_or_transactional_or_structured)
    parsed_tx_style = get_handle(parsed_tx.wire_or_transactional_or_structured)
    parsed_wire_constraint_id = api.getPortWirePowerConstraintIDs(parsed_wire_style)[0]
    parsed_tx_constraint_id = api.getPortTransactionalPowerConstraintIDs(parsed_tx_style)[0]
    assert parsed_wire_constraint_id and parsed_tx_constraint_id
    assert resolve_handle(parsed_wire_style) is parsed_wire.wire_or_transactional_or_structured
    assert resolve_handle(parsed_tx_style) is parsed_tx.wire_or_transactional_or_structured
    assert api.getPowerConstraintRange(parsed_wire_constraint_id) == ["WIDTH-1", "0"]
    parsed_domains = {domain.name: get_handle(domain) for domain in parsed.power_domains.power_domain}
    assert api.getPowerConstraintPowerDomainRefByName(parsed_wire_constraint_id) == "PWR_AUX"
    assert api.getPowerConstraintPowerDomainRefByID(parsed_wire_constraint_id) == parsed_domains["PWR_AUX"]
    assert api.getPowerConstraintPowerDomainRefByID(parsed_tx_constraint_id) == parsed_domains["PWR_TX"]

    assert api.getPowerConstraintRange(parsed_wire_constraint_id) == ["WIDTH-1", "0"]
    range_id = get_handle(resolve_handle(parsed_wire_constraint_id).range)
    left_id = api.getPowerConstraintRangeLeftID(parsed_wire_constraint_id)
    right_id = api.getPowerConstraintRangeRightID(parsed_wire_constraint_id)
    assert range_id is not None and left_id is not None and right_id is not None
    assert api.removePowerConstraintRange(parsed_wire_constraint_id)
    assert api.getPowerConstraintRange(parsed_wire_constraint_id) is None
    assert api.getPowerConstraintRangeLeftID(parsed_wire_constraint_id) is None
    assert api.getPowerConstraintRangeRightID(parsed_wire_constraint_id) is None
    for removed_id in (range_id, left_id, right_id):
        assert resolve_handle(removed_id) is None
    _valid(parsed)


def test_power_domain_setters_preserve_expression_and_parsed_removal_ownership():
    root = _component()
    root_handle = get_handle(root)
    parent_id = api.addComponentPowerDomain(root_handle, "PWR_PARENT")
    child_id = api.addComponentPowerDomain(root_handle, "PWR_CHILD")
    assert api.getPowerDomainName(child_id) == "PWR_CHILD"
    assert api.getPowerDomainAlwaysOn(child_id) is None
    assert api.setPowerDomainAlwaysOn(child_id, "1'b0")
    assert api.getPowerDomainAlwaysOnExpression(child_id) == "1'b0"
    always_on_id = api.getPowerDomainAlwaysOnID(child_id)
    assert always_on_id is not None
    assert api.setPowerDomainSubDomainOf(child_id, "PWR_PARENT")
    assert api.getPowerDomainSubDomainOf(child_id) == "PWR_PARENT"
    assert api.getPowerDomainSubDomainOfRefByID(child_id) == parent_id

    xml = _valid(root)
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, ["v", "l", "power_component", "1"])
    domains = parsed.power_domains.power_domain
    parsed_parent, parsed_child = domains
    parsed_parent_id = get_handle(parsed_parent)
    parsed_child_id = get_handle(parsed_child)
    parsed_always_on_id = api.getPowerDomainAlwaysOnID(parsed_child_id)
    assert parsed_always_on_id is not None
    assert api.getPowerDomainAlwaysOnExpression(parsed_child_id) == "1'b0"
    assert api.getPowerDomainSubDomainOf(parsed_child_id) == "PWR_PARENT"

    assert api.removePowerDomainSubDomainOf(parsed_child_id)
    assert api.getPowerDomainSubDomainOf(parsed_child_id) is None
    _valid(parsed)
    assert api.removeComponentPowerDomain(parsed_child_id)
    assert resolve_handle(parsed_child_id) is None
    assert resolve_handle(parsed_always_on_id) is None
    assert api.getPowerDomainName(parsed_parent_id) == "PWR_PARENT"
    _valid(parsed)
    assert api.removeComponentPowerDomain(parsed_parent_id)
    assert parsed.power_domains is None
    assert resolve_handle(parsed_parent_id) is None
    _valid(parsed)


def test_instance_power_domain_links_remove_exact_reference_and_invalidate_parsed_owned_tree():
    root, instance = _design_with_instance()
    instance_handle = get_handle(instance)
    link_id = api.addComponentInstancePowerDomainLink(instance_handle, "TOP_DOMAIN", ["PD_A", "PD_B"])
    assert design_api.getPowerDomainLinkExternalPowerDomainRef(link_id) == "TOP_DOMAIN"
    assert design_api.getPowerDomainLinkInternalPowerDomainRefs(link_id) == ["PD_A", "PD_B"]
    assert api.addPowerDomainLinkInternalPowerDomainReference(link_id, "PD_C")
    assert design_api.getPowerDomainLinkInternalPowerDomainRefs(link_id) == ["PD_A", "PD_B", "PD_C"]
    second_link_id = api.addComponentInstancePowerDomainLink(instance_handle, "TOP_DOMAIN_2", ["PD_D"])
    assert design_api.getPowerDomainLinkInternalPowerDomainRefs(second_link_id) == ["PD_D"]
    before_duplicate = _valid(root)
    with pytest.raises(TgiError):
        api.addPowerDomainLinkInternalPowerDomainReference(second_link_id, "PD_C")
    assert design_api.getPowerDomainLinkInternalPowerDomainRefs(second_link_id) == ["PD_D"]
    assert _valid(root) == before_duplicate
    xml = before_duplicate

    parsed = XmlDocument.parser().from_string(xml, Design)
    registry.register(parsed, ["v", "l", "power_design", "1"])
    parsed_instance = parsed.component_instances.component_instance[0]
    parsed_links = parsed_instance.power_domain_links.power_domain_link
    parsed_link, parsed_second_link = parsed_links
    parsed_link_id = get_handle(parsed_link)
    parsed_second_link_id = get_handle(parsed_second_link)
    parsed_second_ref_id = get_handle(parsed_second_link.internal_power_domain_reference[0])
    parsed_refs = list(parsed_link.internal_power_domain_reference)
    parsed_ref_ids = [get_handle(reference) for reference in parsed_refs]
    assert design_api.getPowerDomainLinkExternalPowerDomainRef(parsed_link_id) == "TOP_DOMAIN"
    assert design_api.getPowerDomainLinkInternalPowerDomainRefs(parsed_link_id) == ["PD_A", "PD_B", "PD_C"]
    assert design_api.getPowerDomainLinkInternalPowerDomainRefs(parsed_second_link_id) == ["PD_D"]

    assert api.removePowerDomainLinkInternalPowerDomainRef(parsed_link_id, "PD_B")
    assert design_api.getPowerDomainLinkInternalPowerDomainRefs(parsed_link_id) == ["PD_A", "PD_C"]
    assert resolve_handle(parsed_ref_ids[1]) is None
    assert resolve_handle(parsed_ref_ids[0]) is parsed_link.internal_power_domain_reference[0]
    assert resolve_handle(parsed_ref_ids[2]) is parsed_link.internal_power_domain_reference[1]
    _valid(parsed)

    # The last internal reference is required by the XSD; retain the link until
    # its owning powerDomainLink is removed explicitly.
    assert api.removePowerDomainLinkInternalPowerDomainRef(parsed_link_id, "PD_A")
    before_last_reference_removal = _valid(parsed)
    assert api.removePowerDomainLinkInternalPowerDomainRef(parsed_link_id, "PD_C") is False
    assert design_api.getPowerDomainLinkInternalPowerDomainRefs(parsed_link_id) == ["PD_C"]
    assert _valid(parsed) == before_last_reference_removal
    before = _valid(parsed)
    assert not api.removePowerDomainLinkInternalPowerDomainRef(parsed_link_id, "missing")
    assert _valid(parsed) == before

    container_id = get_handle(parsed_instance.power_domain_links)
    parsed_instance.power_domain_links.power_domain_link = tuple(parsed_links)
    _schema_valid(parsed)
    assert api.removeComponentInstancePowerDomainLink(parsed_link_id)
    assert parsed_instance.power_domain_links.power_domain_link == [parsed_second_link]
    assert resolve_handle(parsed_link_id) is None
    assert all(resolve_handle(reference_id) is None for reference_id in parsed_ref_ids)
    _valid(parsed)
    assert api.removeComponentInstancePowerDomainLink(parsed_second_link_id)
    assert parsed_instance.power_domain_links is None
    assert resolve_handle(parsed_second_link_id) is None
    assert resolve_handle(parsed_second_ref_id) is None
    assert resolve_handle(container_id) is None
    _valid(parsed)
