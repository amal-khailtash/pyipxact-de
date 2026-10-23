"""Typed part-select operations preserve IP-XACT model and ownership semantics."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import _miscellaneous_part_select as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AbstractionTypes,
    BusInterface,
    BusInterfaces,
    BusInterfaceType,
    Component,
    ComponentPortDirectionType,
    ConfigurableLibraryRefType,
    Model,
    PartSelect,
    Port,
    PortWireType,
)
from org.accellera.ipxact.v1685_2022.index import Index
from org.accellera.ipxact.v1685_2022.indices import Indices
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.range import Range
from org.accellera.ipxact.v1685_2022.right import Right

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_PortMap = AbstractionTypes.AbstractionType.PortMaps.PortMap
_PhysicalPort = _PortMap.PhysicalPort


def _range(left: str, right: str) -> Range:
    return Range(left=Left(value=left), right=Right(value=right))


def _root(selection: PartSelect) -> Component:
    mapping = _PortMap(
        logical_port=_PortMap.LogicalPort(name="DATA"),
        physical_port_or_logical_tie_off=_PhysicalPort(name="data_i", part_select=selection),
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
                    )
                ]
            )
        ),
        bus_interfaces=BusInterfaces(bus_interface=[interface]),
    )


def _round_trip(root: Component) -> Component:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert parsed == root
    return parsed


def _selection(root: Component) -> PartSelect:
    value = root.bus_interfaces.bus_interface[0].abstraction_types.abstraction_type[0]
    return value.port_maps.port_map[0].physical_port_or_logical_tie_off.part_select


def test_getters_follow_typed_indices_and_range_through_round_trip():
    selection = PartSelect(
        range_or_indices=[
            Indices(index=[Index(value="4'hc", id="first-index"), Index(value="WIDTH - 1", id="symbolic-index")]),
            _range("8'hff", "0"),
        ],
        id="selection-id",
    )
    parsed = _round_trip(_root(selection))
    selection = _selection(parsed)
    selection_id = get_handle(selection)

    index_ids = api.getPartSelectIndexIDs(selection_id)
    assert [resolve_handle(handle) for handle in index_ids] == list(selection.range_or_indices[0].index)
    assert api.getPartSelectIndicesExpression(selection_id) == ["4'hc", "WIDTH - 1"]
    with pytest.raises(TgiError):
        api.getPartSelectIndices(selection_id)
    assert api.getPartSelectRangeExpression(selection_id) == ["8'hff", "0"]
    assert api.getPartSelectRange(selection_id) == [255, 0]
    assert resolve_handle(api.getPartSelectRangeLeftID(selection_id)) is selection.range_or_indices[1].left
    assert resolve_handle(api.getPartSelectRangeRightID(selection_id)) is selection.range_or_indices[1].right


def test_mutations_preserve_wrappers_metadata_sibling_order_and_are_atomic():
    indices = Indices(index=[Index(value="3", id="retained-index")])
    range_node = _range("7", "0")
    selection = PartSelect(range_or_indices=[indices, range_node], id="part-select-id")
    root = _root(selection)
    selection_id = get_handle(selection)
    initial_index_id = api.getPartSelectIndexIDs(selection_id)[0]
    left_id = api.getPartSelectRangeLeftID(selection_id)
    right_id = api.getPartSelectRangeRightID(selection_id)

    with pytest.raises(TgiError):
        api.setPartSelectRange(selection_id, "15", "WIDTH +")
    with pytest.raises(TgiError):
        api.addPartSelectIndex(selection_id, "WIDTH +")
    with pytest.raises(TgiError):
        api.addPartSelectIndex(selection_id, "4294967296")
    assert api.getPartSelectRangeExpression(selection_id) == ["7", "0"]
    assert api.getPartSelectIndexIDs(selection_id) == [initial_index_id]

    assert api.setPartSelectRange(selection_id, "15", "8")
    assert api.getPartSelectRangeLeftID(selection_id) == left_id
    assert api.getPartSelectRangeRightID(selection_id) == right_id
    added_id = api.addPartSelectIndex(selection_id, "LANE + 1")
    assert resolve_handle(added_id).value == "LANE + 1"
    assert api.getPartSelectIndicesExpression(selection_id) == ["3", "LANE + 1"]
    assert selection.id == "part-select-id"
    assert selection.range_or_indices == [indices, range_node]
    assert _selection(_round_trip(root)) == selection


def test_removals_invalidate_exact_owned_descendants_and_prune_empty_branches():
    indices = Indices(index=[Index(value="1", id="keep-me"), Index(value="2", id="remove-me")])
    range_node = _range("7", "0")
    selection = PartSelect(range_or_indices=[indices, range_node], id="selection-id")
    root = _root(selection)
    selection_id = get_handle(selection)
    index_ids = api.getPartSelectIndexIDs(selection_id)
    range_id = get_handle(range_node)
    left_id = get_handle(range_node.left)
    right_id = get_handle(range_node.right)

    assert api.removePartSelectIndex(index_ids[1])
    assert resolve_handle(index_ids[1]) is None
    assert api.getPartSelectIndexIDs(selection_id) == [index_ids[0]]
    assert selection.range_or_indices == [indices, range_node]
    _round_trip(root)

    assert api.removePartSelectRange(selection_id)
    assert all(resolve_handle(handle) is None for handle in (range_id, left_id, right_id))
    assert selection.range_or_indices is indices
    assert api.getPartSelectRangeExpression(selection_id) is None
    assert not api.removePartSelectRange(selection_id)
    _round_trip(root)

    pruned_indices = Indices(index=[Index(value="5")])
    pruned_range = _range("3", "0")
    second_selection = PartSelect(range_or_indices=[pruned_indices, pruned_range])
    second_root = _root(second_selection)
    second_selection_id = get_handle(second_selection)
    only_index_id = api.getPartSelectIndexIDs(second_selection_id)[0]
    pruned_indices_id = get_handle(pruned_indices)
    assert api.removePartSelectIndex(only_index_id)
    assert resolve_handle(only_index_id) is None
    assert resolve_handle(pruned_indices_id) is None
    assert second_selection.range_or_indices is pruned_range
    _round_trip(second_root)


def test_add_and_set_range_normalize_tuple_choice_storage():
    selection = PartSelect(range_or_indices=(_range("3", "0"),))
    selection_id = get_handle(selection)
    index_id = api.addPartSelectIndex(selection_id, "1")
    assert isinstance(selection.range_or_indices, list)
    assert isinstance(selection.range_or_indices[0], Indices)
    assert isinstance(selection.range_or_indices[1], Range)
    assert api.setPartSelectRange(selection_id, "5", "2")
    assert api.getPartSelectRange(selection_id) == [5, 2]
    assert resolve_handle(index_id).value == "1"
    _round_trip(_root(selection))
