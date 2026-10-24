"""Port-map TGI mutations preserve the IEEE 1685-2022 model and XSD shapes."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import port_map as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AbstractionTypes,
    BusInterface,
    BusInterfaces,
    BusInterfaceType,
    Component,
    ComponentPortDirectionType,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    Indices,
    Model,
    PartSelect,
    Port,
    PortWireType,
    Range,
    UnsignedBitVectorExpression,
)
from org.accellera.ipxact.v1685_2022.configurable_element_value import ConfigurableElementValue
from org.accellera.ipxact.v1685_2022.index import Index
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.right import Right

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_PortMap = AbstractionTypes.AbstractionType.PortMaps.PortMap
_PhysicalPort = _PortMap.PhysicalPort
_SubPort = _PhysicalPort.SubPort


@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear()
    yield
    registry.clear()


def _range(left: str, right: str) -> Range:
    return Range(left=Left(value=left), right=Right(value=right))


def _root(port_map: object | None = None) -> Component:
    mapping = port_map or _PortMap(
        logical_port=_PortMap.LogicalPort(name="DATA", id="logical-port"),
        physical_port_or_logical_tie_off=_PhysicalPort(name="data_i", id="physical-port"),
        id="mapping",
    )
    abstraction = AbstractionTypes.AbstractionType(
        abstraction_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="abs", version="1"),
        port_maps=AbstractionTypes.AbstractionType.PortMaps(port_map=[mapping]),
    )
    interface = BusInterface(
        name="bus",
        bus_type=ConfigurableLibraryRefType(vendor="v", library="l", name="bus", version="1"),
        abstraction_types=AbstractionTypes(abstraction_type=[abstraction]),
        choice=BusInterfaceType.Initiator(),
    )
    return Component(
        vendor="v",
        library="l",
        name="component",
        version="1",
        model=Model(
            ports=Model.Ports(
                port=[
                    Port(
                        name="data_i",
                        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
                    ),
                    Port(
                        name="data_o",
                        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.OUT),
                    ),
                ]
            )
        ),
        bus_interfaces=BusInterfaces(bus_interface=[interface]),
    )


def _valid_round_trip(root: Component) -> tuple[str, Component]:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert parsed == root
    return xml, parsed


def _first_port_map(root: Component):
    return root.bus_interfaces.bus_interface[0].abstraction_types.abstraction_type[0].port_maps.port_map[0]


def test_range_only_and_indices_only_part_selects_round_trip_as_generated_models():
    combined = PartSelect(
        range_or_indices=[Indices(index=[Index(value="3")]), _range("7", "4")],
        id="combined-selection",
    )
    ranged = _PortMap(
        logical_port=_PortMap.LogicalPort(name="DATA", range=_range("15", "0")),
        physical_port_or_logical_tie_off=_PhysicalPort(
            name="data_i",
            part_select=combined,
            sub_port=[
                _SubPort(name="range", part_select=PartSelect(range_or_indices=_range("3", "0"))),
                _SubPort(name="indices", part_select=PartSelect(range_or_indices=Indices(index=[Index(value="0")]))),
            ],
        ),
    )
    _, parsed = _valid_round_trip(_root(ranged))
    parsed_map = _first_port_map(parsed)
    parsed_physical = parsed_map.physical_port_or_logical_tie_off
    assert isinstance(parsed_physical, _PhysicalPort)
    assert isinstance(parsed_physical.part_select.range_or_indices, list)
    assert isinstance(parsed_physical.part_select.range_or_indices[0], Indices)
    assert isinstance(parsed_physical.part_select.range_or_indices[1], Range)
    assert isinstance(parsed_physical.sub_port[0].part_select.range_or_indices, Range)
    assert isinstance(parsed_physical.sub_port[1].part_select.range_or_indices, Indices)


def test_logical_and_physical_setters_keep_typed_nodes_metadata_and_handles():
    physical = _PhysicalPort(
        name="data_i",
        part_select=PartSelect(range_or_indices=_range("7", "0"), id="physical-slice"),
        id="physical-port",
    )
    logical = _PortMap.LogicalPort(name="DATA", range=_range("7", "0"), id="logical-port")
    root = _root(_PortMap(logical_port=logical, physical_port_or_logical_tie_off=physical, id="mapping"))
    port_map_id = get_handle(_first_port_map(root))
    logical_id = api.getPortMapLogicalPortID(port_map_id)
    physical_id = api.getPortMapPhysicalPortID(port_map_id)
    assert logical_id is not None
    assert physical_id is not None
    range_node = logical.range
    assert range_node is not None
    range_handle = get_handle(range_node)
    assert api.getLogicalPortRange(logical_id) == [7, 0]
    left_id = api.getLogicalPortRangeLeftID(logical_id)
    right_id = api.getLogicalPortRangeRightID(logical_id)
    part_select_id = api.getPhysicalPortPartSelectID(physical_id)
    assert left_id is not None and right_id is not None
    assert part_select_id is not None
    part_select = resolve_handle(part_select_id)

    assert api.setLogicalPortRange(logical_id, ["15", "8"])
    assert api.getLogicalPortRange(logical_id) == [15, 8]
    assert api.getLogicalPortRangeExpression(logical_id) == ["15", "8"]
    assert api.getLogicalPortRangeLeftID(logical_id) == left_id
    assert api.getLogicalPortRangeRightID(logical_id) == right_id
    assert resolve_handle(range_handle) is logical.range
    assert api.setPhysicalPortPartSelect(physical_id, ["7", "4"], ["3"])
    assert api.getPhysicalPortPartSelectID(physical_id) == part_select_id
    assert resolve_handle(part_select_id) is part_select
    assert part_select.id == "physical-slice"
    assert isinstance(part_select.range_or_indices, list)
    assert isinstance(part_select.range_or_indices[0], Indices)
    assert isinstance(part_select.range_or_indices[1], Range)
    assert part_select.range_or_indices[0].index[0].value == "3"
    assert part_select.range_or_indices[1].left.value == "7"
    assert part_select.range_or_indices[1].right.value == "4"
    _valid_round_trip(root)


def test_setters_switch_the_generated_physical_or_tie_off_choice_exclusively():
    root = _root()
    port_map = _first_port_map(root)
    port_map_id = get_handle(port_map)
    physical_id = api.getPortMapPhysicalPortID(port_map_id)
    assert physical_id is not None

    assert api.setPortMapLogicalTieOff(port_map_id, "1'b0")
    tie_off_id = api.getPortMapLogicalTieOffID(port_map_id)
    assert tie_off_id is not None
    assert api.getPortMapPhysicalPortID(port_map_id) is None
    assert isinstance(port_map.physical_port_or_logical_tie_off, UnsignedBitVectorExpression)
    assert api.getPortMapLogicalTieOffExpression(port_map_id) == "1'b0"
    assert resolve_handle(physical_id) is None
    _valid_round_trip(root)

    assert api.setPortMapPhysicalPort(port_map_id, "data_o")
    assert api.getPortMapLogicalTieOffID(port_map_id) is None
    replacement_id = api.getPortMapPhysicalPortID(port_map_id)
    assert replacement_id is not None
    assert isinstance(port_map.physical_port_or_logical_tie_off, _PhysicalPort)
    assert port_map.physical_port_or_logical_tie_off.name == "data_o"
    assert resolve_handle(tie_off_id) is None
    _valid_round_trip(root)


def test_subport_part_select_is_indices_only_and_parsed_removal_invalidates_owned_nodes():
    root = _root()
    port_map_id = get_handle(_first_port_map(root))
    physical_id = api.getPortMapPhysicalPortID(port_map_id)
    assert physical_id is not None
    subport_id = api.addPhysicalPortSubPort(physical_id, "lane0")
    part_select_id = api.setSubPortMapPartSelect(subport_id, None, ["0", "1"])
    subport = resolve_handle(subport_id)
    part_select = resolve_handle(part_select_id)
    assert isinstance(subport, _SubPort)
    assert isinstance(part_select, PartSelect)
    assert isinstance(part_select.range_or_indices, Indices)
    assert api.getPhysicalPortSubPortIDs(physical_id) == [subport_id]
    assert api.setSubPortMapPartSelect(subport_id, ["1", "0"], ["2"]) == part_select_id
    assert isinstance(part_select.range_or_indices, list)
    assert isinstance(part_select.range_or_indices[0], Indices)
    assert isinstance(part_select.range_or_indices[1], Range)
    _valid_round_trip(root)

    _, parsed = _valid_round_trip(root)
    parsed_map = _first_port_map(parsed)
    parsed_physical = parsed_map.physical_port_or_logical_tie_off
    parsed_physical_id = get_handle(parsed_physical)
    parsed_subport_id = api.getPhysicalPortSubPortIDs(parsed_physical_id)[0]
    parsed_part_select_id = api.setSubPortMapPartSelect(parsed_subport_id, ["1", "0"], None)
    registry.register(parsed, ("v", "l", "component", "1"), replace=True)

    assert api.removePhysicalPortSubPort(parsed_subport_id)
    assert resolve_handle(parsed_subport_id) is None
    assert resolve_handle(parsed_part_select_id) is None
    assert resolve_handle(parsed_physical_id) is parsed_physical
    assert api.getPhysicalPortSubPortIDs(parsed_physical_id) == []
    _valid_round_trip(parsed)


def test_parsed_physical_part_select_removal_recovers_unvisited_owned_subtree():
    physical = _PhysicalPort(
        name="data_i",
        part_select=PartSelect(range_or_indices=_range("7", "0"), id="slice-id"),
        id="physical-id",
    )
    root = _root(
        _PortMap(
            logical_port=_PortMap.LogicalPort(name="DATA"),
            physical_port_or_logical_tie_off=physical,
        )
    )
    _, parsed = _valid_round_trip(root)
    parsed_physical = _first_port_map(parsed).physical_port_or_logical_tie_off
    parsed_part_select = parsed_physical.part_select
    parsed_range = parsed_part_select.range_or_indices
    part_select_id = get_handle(parsed_part_select)
    range_id = get_handle(parsed_range)
    left_id = get_handle(parsed_range.left)
    right_id = get_handle(parsed_range.right)
    physical_id = get_handle(parsed_physical)
    registry.register(parsed, ("v", "l", "component", "1"), replace=True)

    assert api.removePhysicalPortPartSelect(physical_id)
    assert parsed_physical.part_select is None
    assert all(resolve_handle(handle) is None for handle in (part_select_id, range_id, left_id, right_id))
    assert resolve_handle(physical_id) is parsed_physical
    _valid_round_trip(parsed)


def test_abstraction_reference_update_preserves_id_and_configurable_overrides():
    overrides = ConfigurableElementValues(
        configurable_element_value=[ConfigurableElementValue(reference_id="WIDTH", value="16", id="override-id")]
    )
    root = _root()
    abstraction = root.bus_interfaces.bus_interface[0].abstraction_types.abstraction_type[0]
    reference = ConfigurableLibraryRefType(
        vendor="v",
        library="l",
        name="abs",
        version="1",
        configurable_element_values=overrides,
        id="abstraction-ref-id",
    )
    abstraction.abstraction_ref = reference
    abstraction_id = get_handle(abstraction)
    reference_id = get_handle(reference)

    assert api.setAbstractionTypeAbstractionRef(abstraction_id, ["v2", "l2", "abs2", "2"])
    assert resolve_handle(reference_id) is reference
    assert abstraction.abstraction_ref is reference
    assert (reference.vendor, reference.library, reference.name, reference.version) == ("v2", "l2", "abs2", "2")
    assert reference.id == "abstraction-ref-id"
    assert reference.configurable_element_values is overrides
    assert overrides.configurable_element_value[0].reference_id == "WIDTH"
    assert overrides.configurable_element_value[0].value == "16"
    _valid_round_trip(root)


def test_schema_invalid_range_setter_failure_is_atomic():
    root = _root()
    port_map_id = get_handle(_first_port_map(root))
    logical_id = api.getPortMapLogicalPortID(port_map_id)
    assert logical_id is not None
    assert api.setLogicalPortRange(logical_id, ["9", "2"])
    before_xml, _ = _valid_round_trip(root)
    old_range = api.getLogicalPortRange(logical_id)

    with pytest.raises(TgiError):
        api.setLogicalPortRange(logical_id, ["9"])
    after_xml, _ = _valid_round_trip(root)
    assert after_xml == before_xml
    assert api.getLogicalPortRange(logical_id) == old_range == [9, 2]
