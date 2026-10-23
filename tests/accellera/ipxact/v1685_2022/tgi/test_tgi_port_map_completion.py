"""Port map Annex contracts, expressions, reference edits and handle lifecycle."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import port_map as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, registry, resolve_handle
from org.accellera.ipxact.v1685_2022 import AbstractionTypes, ConfigurableLibraryRefType, Indices, Range

_PM = AbstractionTypes.AbstractionType.PortMaps.PortMap
_BASE = [
    ("getLogicalPortRange", "logicalPortID"),
    ("getLogicalPortRangeExpression", "logicalPortID"),
    ("getLogicalPortRangeLeftID", "logicalPortID"),
    ("getLogicalPortRangeRightID", "logicalPortID"),
    ("getPhysicalPortPartSelectID", "physicalPortID"),
    ("getPhysicalPortSubPortIDs", "physicalPortID"),
    ("getPortMapIsInformative", "portMapID"),
    ("getPortMapLogicalPortID", "portMapID"),
    ("getPortMapLogicalTieOff", "portMapID"),
    ("getPortMapLogicalTieOffExpression", "portMapID"),
    ("getPortMapLogicalTieOffID", "portMapID"),
    ("getPortMapPhysicalPortID", "portMapID"),
]
_EXTENDED = [
    ("addPhysicalPortSubPort", "physicalPortID,name"),
    ("addPortMapPhysicalPortSubPort", "portMapID,name"),
    ("removePhysicalPortPartSelect", "physicalPortID"),
    ("removePhysicalPortSubPort", "subPortID"),
    ("removePortMapIsInformative", "portMapID"),
    ("setAbstractionTypeAbstractionRef", "abstractionTypeID,vlnv"),
    ("setLogicalPortRange", "logicalPortID,range"),
    ("setPhysicalPortPartSelect", "physicalPortID,range,indices"),
    ("setPortMapIsInformative", "portMapID,value"),
    ("setPortMapLogicalPort", "portMapID,name"),
    ("setPortMapLogicalTieOff", "portMapID,expression"),
    ("setPortMapPhysicalPort", "portMapID,name"),
    ("setSubPortMapPartSelect", "subPortID,range,indices"),
]


@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear()
    yield
    registry.clear()


def _mapping():
    mapping = _PM(
        logical_port=_PM.LogicalPort(name="DATA"), physical_port_or_logical_tie_off=_PM.PhysicalPort(name="data")
    )
    mapping_id = get_handle(mapping)
    return mapping, mapping_id, api.getPortMapLogicalPortID(mapping_id), api.getPortMapPhysicalPortID(mapping_id)


@pytest.mark.parametrize(
    "name,args,section",
    [
        *[(name, args, f"F.7.69.{i}") for i, (name, args) in enumerate(_BASE, 1)],
        *[(name, args, f"F.7.70.{i}") for i, (name, args) in enumerate(_EXTENDED, 1)],
    ],
)
def test_exact_annex_signatures_exports_and_static_documentation(name, args, section):
    function = getattr(api, name)
    assert list(inspect.signature(function).parameters) == args.split(",")
    assert name in api.__all__
    assert getattr(tgi, name) is function
    assert "Args:" in function.__doc__ and "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


@pytest.mark.parametrize("name,args", _BASE)
def test_base_getters_fault_on_invalid_handles(name, args):
    with pytest.raises(TgiError) as error:
        getattr(api, name)(get_handle(object()))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_logical_range_source_numeric_bounds_and_metadata_identity():
    mapping, map_id, logical_id, physical_id = _mapping()
    assert api.getLogicalPortRange(logical_id) is None
    assert api.getLogicalPortRangeExpression(logical_id) is None
    assert api.getLogicalPortRangeLeftID(logical_id) is None
    assert api.getLogicalPortRangeRightID(logical_id) is None
    assert api.setLogicalPortRange(logical_id, ["32'hFFFF_FFFF", "0"])
    assert api.getLogicalPortRange(logical_id) == [(1 << 32) - 1, 0]
    wrapper = mapping.logical_port.range
    left_id = api.getLogicalPortRangeLeftID(logical_id)
    right_id = api.getLogicalPortRangeRightID(logical_id)
    wrapper.left.other_attributes = {"{urn:test}marker": "left"}
    wrapper.left.minimum = 2
    wrapper.right.maximum = 4
    with pytest.raises(TgiError):
        api.setLogicalPortRange(logical_id, ["1", "0"])
    with pytest.raises(TgiError):
        api.setLogicalPortRange(logical_id, ["5", "8"])
    assert api.setLogicalPortRange(logical_id, ["HIGH", "LOW"])
    assert api.getLogicalPortRangeExpression(logical_id) == ["HIGH", "LOW"]
    with pytest.raises(TgiError):
        api.getLogicalPortRange(logical_id)
    assert api.setLogicalPortRange(logical_id, ["7", "4"])
    assert api.getLogicalPortRange(logical_id) == [7, 4]
    assert mapping.logical_port.range is wrapper
    assert api.getLogicalPortRangeLeftID(logical_id) == left_id
    assert api.getLogicalPortRangeRightID(logical_id) == right_id
    assert wrapper.left.other_attributes == {"{urn:test}marker": "left"}
    assert api.setPortMapLogicalPort(map_id, " RENAMED ")
    assert mapping.logical_port.name == "RENAMED"
    assert api.getPortMapLogicalPortID(map_id) == logical_id
    assert api.getPhysicalPortPartSelectID(physical_id) is None
    with pytest.raises(TgiError):
        api.getLogicalPortRange(map_id)
    with pytest.raises(TgiError):
        api.getPhysicalPortSubPortIDs(map_id)


@pytest.mark.parametrize(
    "values",
    [
        None,
        "7:0",
        [],
        ["7"],
        ["7", "0", "1"],
        ["7", None],
        ["7", True],
        ["7", "-1"],
        ["4294967296", "0"],
        ["7", "1 +"],
        ["7", "8'hxx"],
        ["7", "1.5"],
        ["7", "bad\x00text"],
    ],
)
def test_range_invalid_arguments_reject_atomically(values):
    mapping, _, logical_id, _ = _mapping()
    api.setLogicalPortRange(logical_id, ["7", "0"])
    wrapper = mapping.logical_port.range
    with pytest.raises(TgiError):
        api.setLogicalPortRange(logical_id, values)
    assert mapping.logical_port.range is wrapper
    assert api.getLogicalPortRangeExpression(logical_id) == ["7", "0"]


def test_informative_boolean_default_and_explicit_removal():
    mapping, mapping_id, _, _ = _mapping()
    assert not api.getPortMapIsInformative(mapping_id)
    assert not api.removePortMapIsInformative(mapping_id)
    assert api.setPortMapIsInformative(mapping_id, True)
    assert api.getPortMapIsInformative(mapping_id)
    for value in [None, 0, 1, "true", []]:
        with pytest.raises(TgiError):
            api.setPortMapIsInformative(mapping_id, value)
        assert mapping.is_informative is True
    assert api.removePortMapIsInformative(mapping_id)
    assert mapping.is_informative is None
    assert not api.getPortMapIsInformative(mapping_id)
    assert api.setPortMapIsInformative(mapping_id, False)
    assert mapping.is_informative is False
    assert api.removePortMapIsInformative(mapping_id)


def test_subport_path_order_repeated_names_tuple_mutation_and_removal():
    mapping, mapping_id, _, physical_id = _mapping()
    first = api.addPhysicalPortSubPort(physical_id, "lane")
    physical = mapping.physical_port_or_logical_tie_off
    physical.sub_port = tuple(physical.sub_port)
    second = api.addPortMapPhysicalPortSubPort(mapping_id, "lane")
    assert api.getPhysicalPortSubPortIDs(physical_id) == [first, second]
    assert physical.sub_port[0].name == physical.sub_port[1].name == "lane"
    physical.sub_port = tuple(physical.sub_port)
    part_select_id = api.setSubPortMapPartSelect(first, None, ["3"])
    child = resolve_handle(first)
    index_id = get_handle(child.part_select.range_or_indices.index[0])
    assert api.removePhysicalPortSubPort(first)
    assert api.getPhysicalPortSubPortIDs(physical_id) == [second]
    for handle in [first, part_select_id, index_id]:
        assert resolve_handle(handle) is None
    with pytest.raises(TgiError):
        api.removePhysicalPortSubPort(first)


def test_choice_replacement_invalidates_descendants_and_tie_off_preserves_source():
    mapping, map_id, _, physical_id = _mapping()
    subport_id = api.addPhysicalPortSubPort(physical_id, "child")
    selection_id = api.setSubPortMapPartSelect(subport_id, ["7", "0"], None)
    assert api.getPortMapLogicalTieOff(map_id) is None
    assert api.getPortMapLogicalTieOffExpression(map_id) is None
    assert api.getPortMapLogicalTieOffID(map_id) is None
    assert api.setPortMapLogicalTieOff(map_id, "8'hA5")
    for handle in [physical_id, subport_id, selection_id]:
        assert resolve_handle(handle) is None
    assert api.getPortMapLogicalTieOff(map_id) == 165
    tie_off_id = api.getPortMapLogicalTieOffID(map_id)
    wrapper = resolve_handle(tie_off_id)
    wrapper.other_attributes = {"{urn:test}marker": "tie"}
    assert api.setPortMapLogicalTieOff(map_id, "TIE_VALUE")
    assert api.getPortMapLogicalTieOffExpression(map_id) == "TIE_VALUE"
    assert api.getPortMapLogicalTieOffID(map_id) == tie_off_id
    assert wrapper.other_attributes == {"{urn:test}marker": "tie"}
    with pytest.raises(TgiError):
        api.getPortMapLogicalTieOff(map_id)
    with pytest.raises(TgiError):
        api.addPortMapPhysicalPortSubPort(map_id, "child")
    assert api.setPortMapPhysicalPort(map_id, "signal")
    assert resolve_handle(tie_off_id) is None
    assert isinstance(mapping.physical_port_or_logical_tie_off, _PM.PhysicalPort)
    new_physical_id = api.getPortMapPhysicalPortID(map_id)
    assert api.setPortMapPhysicalPort(map_id, "signal_o")
    assert api.getPortMapPhysicalPortID(map_id) == new_physical_id


def test_part_select_updates_keep_retained_nodes_and_invalidate_removed_selections():
    mapping, _, _, physical_id = _mapping()
    assert api.setPhysicalPortPartSelect(physical_id, ["7", "0"], ["2", "3"])
    select_id = api.getPhysicalPortPartSelectID(physical_id)
    select = resolve_handle(select_id)
    indices, range = select.range_or_indices
    assert isinstance(indices, Indices) and isinstance(range, Range)
    index0_id, index1_id = [get_handle(index) for index in indices.index]
    left_id, right_id = get_handle(range.left), get_handle(range.right)
    range.left.other_attributes = {"{urn:test}marker": "left"}
    select.id = "selection"
    assert api.setPhysicalPortPartSelect(physical_id, ["8", "1"], ["4"])
    assert select.range_or_indices[0] is indices
    assert select.range_or_indices[1] is range
    assert resolve_handle(index0_id).value == "4"
    assert resolve_handle(index1_id) is None
    assert resolve_handle(left_id).value == "8"
    assert resolve_handle(right_id).value == "1"
    assert api.setPhysicalPortPartSelect(physical_id, None, ["5"])
    assert select.range_or_indices is indices
    assert resolve_handle(left_id) is None and resolve_handle(right_id) is None
    assert api.setPhysicalPortPartSelect(physical_id, ["3", "0"], None)
    assert isinstance(select.range_or_indices, Range)
    assert resolve_handle(index0_id) is None
    assert select.id == "selection"
    assert api.getPhysicalPortPartSelectID(physical_id) == select_id
    new_left_id = get_handle(select.range_or_indices.left)
    assert api.removePhysicalPortPartSelect(physical_id)
    assert resolve_handle(select_id) is None and resolve_handle(new_left_id) is None
    assert not api.removePhysicalPortPartSelect(physical_id)


@pytest.mark.parametrize(
    "range,indices",
    [
        (None, None),
        (None, []),
        (["7"], []),
        (["7", "0"], "3"),
        (["7", "0"], ["-1"]),
        (["7", "0"], ["1 +"]),
        (["7", "0"], [None]),
        (["7", "0"], ["4294967296"]),
    ],
)
def test_part_select_invalid_inputs_reject_atomically(range, indices):
    mapping, _, _, physical_id = _mapping()
    assert api.setPhysicalPortPartSelect(physical_id, ["7", "0"], ["3"])
    wrapper = mapping.physical_port_or_logical_tie_off.part_select
    old_indices, old_range = wrapper.range_or_indices
    with pytest.raises(TgiError):
        api.setPhysicalPortPartSelect(physical_id, range, indices)
    assert mapping.physical_port_or_logical_tie_off.part_select is wrapper
    assert wrapper.range_or_indices == [old_indices, old_range]
    assert old_indices.index[0].value == "3"
    assert old_range.left.value == "7" and old_range.right.value == "0"


def test_abstraction_reference_edit_preserves_generated_reference_identity_and_attributes():
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name="abs", version="1", id="ref")
    abstraction = AbstractionTypes.AbstractionType(abstraction_ref=reference)
    abstraction_id = get_handle(abstraction)
    reference_id = get_handle(reference)
    assert api.setAbstractionTypeAbstractionRef(abstraction_id, ["new-v", "new-l", "new-a", "2.0"])
    assert abstraction.abstraction_ref is reference
    assert resolve_handle(reference_id) is reference
    assert reference.id == "ref"
    assert (reference.vendor, reference.library, reference.name, reference.version) == (
        "new-v",
        "new-l",
        "new-a",
        "2.0",
    )
    for invalid in ["v:l:a:1", ["v", "l", "a"], ["v", "l", "bad name", "1"], ["v", "l", None, "1"]]:
        with pytest.raises(TgiError):
            api.setAbstractionTypeAbstractionRef(abstraction_id, invalid)
        assert reference.name == "new-a"


@pytest.mark.parametrize("name", [None, True, "", "two names", "bad\x00name", "a·middle"])
def test_physical_port_name_rules_reject_before_choice_replacement(name):
    _, map_id, _, _ = _mapping()
    api.setPortMapLogicalTieOff(map_id, "0")
    old_id = api.getPortMapLogicalTieOffID(map_id)
    with pytest.raises(TgiError):
        api.setPortMapPhysicalPort(map_id, name)
    assert api.getPortMapLogicalTieOffID(map_id) == old_id


@pytest.mark.parametrize("values", [["9vendor", "l", "a", "1"], ["v", "9library", "a", "1"]])
def test_abstraction_reference_vendor_and_library_require_xml_names(values):
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name="abs", version="1")
    abstraction = AbstractionTypes.AbstractionType(abstraction_ref=reference)
    with pytest.raises(TgiError):
        api.setAbstractionTypeAbstractionRef(get_handle(abstraction), values)
    assert (reference.vendor, reference.library, reference.name, reference.version) == ("v", "l", "abs", "1")
    assert api.setAbstractionTypeAbstractionRef(get_handle(abstraction), ["v", "l", "9name", "2.0"])


def test_tie_off_source_may_exceed_transport_long_but_numeric_getter_faults():
    _, mapping_id, _, _ = _mapping()
    assert api.setPortMapLogicalTieOff(mapping_id, "64'h7FFF_FFFF_FFFF_FFFF")
    assert api.getPortMapLogicalTieOff(mapping_id) == (1 << 63) - 1
    assert api.setPortMapLogicalTieOff(mapping_id, "64'hFFFF_FFFF_FFFF_FFFF")
    assert api.getPortMapLogicalTieOffExpression(mapping_id) == "64'hFFFF_FFFF_FFFF_FFFF"
    with pytest.raises(TgiError):
        api.getPortMapLogicalTieOff(mapping_id)


def test_logical_port_getter_faults_on_missing_required_content():
    mapping, mapping_id, _, _ = _mapping()
    mapping.logical_port = None
    with pytest.raises(TgiError):
        api.getPortMapLogicalPortID(mapping_id)
    assert api.setPortMapLogicalPort(mapping_id, "DATA")
    assert api.getPortMapLogicalPortID(mapping_id) == get_handle(mapping.logical_port)
