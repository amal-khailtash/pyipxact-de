"""Component edits preserve schema choices, references and owned handles."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import component as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, Design, DesignConfiguration

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


def _root():
    return Component(vendor="v", library="l", name="component", version="1")


def _valid(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, Component) == root
    return xml


def test_required_factory_arguments_create_schema_valid_children():
    root = _root()
    handle = get_handle(root)
    api.addComponentAddressSpace(handle, "space", "4096", "32")
    api.addComponentChoice(handle, "values", ["0", "1"])
    api.addComponentComponentGenerator(handle, "generator", "generate.py")
    api.addComponentMemoryMap(handle, "map")
    api.addComponentCpu(handle, "cpu", "map", "4096", "32")
    api.addComponentIndirectInterface(handle, "indirect", "address", "data", "map")
    _valid(root)


def test_reference_edits_preserve_field_wrappers_and_metadata():
    root = _root()
    api.addComponentMemoryMap(get_handle(root), "map")
    handle = api.addComponentIndirectInterface(get_handle(root), "indirect", "address", "data", "map")
    child = resolve_handle(handle)
    field = child.indirect_address_ref.field_ref
    field_handle = get_handle(field)
    api.setIndirectInterfaceIndirectAddressRef(handle, "new_address")
    api.setIndirectInterfaceIndirectDataRef(handle, "new_data")
    assert child.indirect_address_ref.field_ref is field
    assert get_handle(field) == field_handle
    assert field.field_ref == "new_address"
    assert child.indirect_data_ref.field_ref.field_ref == "new_data"
    before = _valid(root)
    with pytest.raises(TgiError):
        api.setIndirectInterfaceIndirectAddressRef(handle, None)
    assert _valid(root) == before


def test_parsed_direct_child_removal_recovers_top_level_owner_and_invalidates_container():
    root = _root()
    api.addComponentAddressSpace(get_handle(root), "space", "4096", "32")
    parsed = XmlDocument.parser().from_string(_valid(root), Component)
    registry.register(parsed, ["v", "l", "component", "1"])
    child = parsed.address_spaces.address_space[0]
    child_handle = get_handle(child)
    range_handle = get_handle(child.range)
    container_handle = get_handle(parsed.address_spaces)
    assert api.removeComponentAddressSpace(child_handle)
    assert parsed.address_spaces is None
    for handle in [child_handle, range_handle, container_handle]:
        assert resolve_handle(handle) is None
    _valid(parsed)


def test_mode_condition_source_and_wrapper_identity_survive_edits():
    root = _root()
    mode_id = api.addComponentMode(get_handle(root), "active")
    api.setModeCondition(mode_id, "1'b1")
    mode = resolve_handle(mode_id)
    condition_id = get_handle(mode.condition)
    assert api.getModeCondition(mode_id) == "1"
    assert api.getModeConditionExpression(mode_id) == "1'b1"
    api.setModeCondition(mode_id, "1'b0")
    assert get_handle(mode.condition) == condition_id
    assert api.getModeCondition(mode_id) == "0"
    api.setModeName(mode_id, "inactive")
    assert api.getModeName(mode_id) == "inactive"
    _valid(root)
    assert api.removeModeCondition(mode_id)
    assert resolve_handle(condition_id) is None
    _valid(root)


def test_memory_map_address_unit_bits_wrapper_identity_and_invalid_input_atomicity():
    root = _root()
    handle = api.addComponentMemoryMap(get_handle(root), "map")
    api.setMemoryMapAddressUnitBits(handle, "8")
    memory_map = resolve_handle(handle)
    from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits

    wrapper = next(item for item in memory_map.choice if isinstance(item, AddressUnitBits))
    wrapper_handle = get_handle(wrapper)
    api.setMemoryMapAddressUnitBits(handle, "16")
    assert next(item for item in memory_map.choice if isinstance(item, AddressUnitBits)) is wrapper
    assert wrapper.value == "16"
    before = _valid(root)
    with pytest.raises(TgiError):
        api.setMemoryMapAddressUnitBits(handle, None)
    assert _valid(root) == before
    assert api.removeMemoryMapAddressUnitBits(handle)
    assert resolve_handle(wrapper_handle) is None
    _valid(root)


@pytest.mark.parametrize(
    "role", ["Initiator", "Target", "System", "MirroredSystem", "MirroredTarget", "MirroredInitiator"]
)
def test_bus_interface_factories_serialize_actual_choice_modes(role):
    root = _root()
    arguments = [get_handle(root), "bus", ["v", "l", "bus", "1"]]
    if role in {"System", "MirroredSystem"}:
        arguments.append("group")
    handle = getattr(api, f"addComponent{role}BusInterface")(*arguments)
    xml = XmlDocument.serializer().render(root)
    element = etree.fromstring(xml.encode())
    namespaces = {"i": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"}
    lexical_role = role[0].lower() + role[1:]
    assert len(element.xpath(f"i:busInterfaces/i:busInterface/i:{lexical_role}", namespaces=namespaces)) == 1
    if role != "MirroredInitiator":
        _valid(root)
    assert api.removeComponentBusInterface(handle)
    assert resolve_handle(handle) is None
    _valid(root)


@pytest.mark.parametrize(
    "factory",
    [
        lambda handle: api.addComponentAddressSpace(handle, "same", "1024", "32"),
        lambda handle: api.addComponentFileSet(handle, "same"),
        lambda handle: api.addComponentView(handle, "same"),
        lambda handle: api.addComponentMode(handle, "same"),
        lambda handle: api.addComponentWirePort(handle, "same", "in"),
    ],
)
def test_duplicate_names_are_rejected_before_mutating_the_document(factory):
    root = _root()
    handle = get_handle(root)
    first = factory(handle)
    before = _valid(root)
    with pytest.raises(TgiError):
        factory(handle)
    assert _valid(root) == before
    assert resolve_handle(first) is not None


def test_component_instance_getters_follow_top_level_component_reference():
    from org.accellera.ipxact.v1685_2022.component_instance import ComponentInstance
    from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
    from org.accellera.ipxact.v1685_2022.instance_name import InstanceName

    root = _root()
    port = api.addComponentWirePort(get_handle(root), "data", "in")
    registry.register(root, ["v", "l", "component", "1"])
    instance = ComponentInstance(
        instance_name=InstanceName(value="instance"),
        component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="component", version="1"),
    )
    assert api.getComponentPortIDs(get_handle(instance)) == [port]
    assert api.getComponentViewIDs(get_handle(instance)) == []
    instance.component_ref.version = "missing"
    with pytest.raises(TgiError):
        api.getComponentPortIDs(get_handle(instance))


def test_reusable_memory_map_definition_address_unit_bits_are_supported():
    from org.accellera.ipxact.v1685_2022.memory_map_definitions import MemoryMapDefinitions

    definition = MemoryMapDefinitions.MemoryMapDefinition(name="map_definition")
    handle = get_handle(definition)
    assert api.setMemoryMapAddressUnitBits(handle, "8")
    wrapper_id = get_handle(definition.address_unit_bits)
    definition.address_unit_bits.other_attributes["{urn:test}marker"] = "unit_bits"
    assert api.setMemoryMapAddressUnitBits(handle, "32")
    assert get_handle(definition.address_unit_bits) == wrapper_id
    assert definition.address_unit_bits.other_attributes["{urn:test}marker"] == "unit_bits"
    assert api.removeMemoryMapAddressUnitBits(handle)
    assert definition.address_unit_bits is None
    assert resolve_handle(wrapper_id) is None


def test_selected_views_resolve_configuration_for_the_owning_design():
    from org.accellera.ipxact.v1685_2022.component_instance import ComponentInstance
    from org.accellera.ipxact.v1685_2022.component_instances import ComponentInstances
    from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
    from org.accellera.ipxact.v1685_2022.instance_name import InstanceName
    from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType

    root = _root()
    first = api.addComponentView(get_handle(root), "first")
    selected = api.addComponentView(get_handle(root), "selected")
    registry.register(root, ["v", "l", "component", "1"])
    instance = ComponentInstance(
        instance_name=InstanceName(value="instance"),
        component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="component", version="1"),
    )
    design = Design(
        vendor="v",
        library="l",
        name="design",
        version="1",
        component_instances=ComponentInstances(component_instance=[instance]),
    )
    registry.register(design, ["v", "l", "design", "1"])
    configuration = DesignConfiguration(
        vendor="v",
        library="l",
        name="configuration",
        version="1",
        design_ref=LibraryRefType(vendor="v", library="l", name="design", version="1"),
        view_configuration=[
            DesignConfiguration.ViewConfiguration(
                instance_name=InstanceName(value="instance"),
                view=DesignConfiguration.ViewConfiguration.View(view_ref="selected"),
            )
        ],
    )
    registry.register(configuration, ["v", "l", "configuration", "1"])
    assert api.getComponentViewIDs(get_handle(instance)) == [first, selected]
    assert api.getComponentSelectedViewIDs(get_handle(instance)) == [selected]
    assert api.getComponentSelectedViewIDs(get_handle(root)) == []
    configuration.design_ref.name = "unrelated_design"
    assert api.getComponentSelectedViewIDs(get_handle(instance)) == []


def test_address_unit_bits_preserve_memory_map_choice_order():
    from org.accellera.ipxact.v1685_2022.shared_type import SharedType

    root = _root()
    handle = api.addComponentMemoryMap(get_handle(root), "map")
    memory_map = resolve_handle(handle)
    shared = SharedType.YES
    memory_map.choice.append(shared)
    api.setMemoryMapAddressUnitBits(handle, "8")
    assert memory_map.choice[-1] is shared
    _valid(root)


@pytest.mark.parametrize("expression", ["0", "-1", "32'h0", "32'h100000000", "4294967296"])
def test_address_unit_bits_invalid_numeric_bounds_are_atomic(expression):
    root = _root()
    handle = api.addComponentMemoryMap(get_handle(root), "map")
    before = _valid(root)
    with pytest.raises(TgiError):
        api.setMemoryMapAddressUnitBits(handle, expression)
    assert _valid(root) == before


@pytest.mark.parametrize("expression", ["2", "-1", "4'hf", "1+1", "1.5"])
def test_mode_condition_invalid_resolved_values_are_atomic(expression):
    root = _root()
    handle = api.addComponentMode(get_handle(root), "active")
    before = _valid(root)
    with pytest.raises(TgiError):
        api.setModeCondition(handle, expression)
    assert _valid(root) == before


def test_optional_value_removers_work_on_direct_generated_handles():
    from org.accellera.ipxact.v1685_2022.always_on import AlwaysOn
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType
    from org.accellera.ipxact.v1685_2022.unresolved_unsigned_bit_expression import UnresolvedUnsignedBitExpression

    mode = ComponentType.Modes.Mode(name="mode", condition=UnresolvedUnsignedBitExpression(value="1"))
    condition_id = get_handle(mode.condition)
    assert api.removeModeCondition(get_handle(mode))
    assert mode.condition is None
    assert resolve_handle(condition_id) is None
    domain = ComponentType.PowerDomains.PowerDomain(name="domain", always_on=AlwaysOn(value="1"))
    value_id = get_handle(domain.always_on)
    assert api.removePowerDomainAlwaysOn(get_handle(domain))
    assert domain.always_on is None
    assert resolve_handle(value_id) is None
