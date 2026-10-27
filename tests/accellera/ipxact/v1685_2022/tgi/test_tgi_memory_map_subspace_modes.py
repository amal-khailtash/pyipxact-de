"""Signed subspace sources and identity-owned remap mode targets."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentType,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapType,
    ModeRef,
    SignedLongintExpression,
    SubspaceMap,
    SubspaceRefType,
)


def subspace(source="-4", model=SubspaceMap):
    return model(name="sub", base_address=SignedLongintExpression(value=source), initiator_ref="bus")


def component(remap, names=("active", "sleep")):
    owner = Component(
        vendor="test",
        library="memory",
        name="modes",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[remap])]),
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name=name) for name in names]),
    )
    _register_graph(owner)
    return owner


@pytest.mark.parametrize("model", [SubspaceRefType, SubspaceMap])
@pytest.mark.parametrize(
    "source,expected",
    [
        ("-4", -4),
        ("-(2 + 3)", -5),
        ("64'shffffffffffffffff", -1),
        (str(-(1 << 63)), -(1 << 63)),
        (str((1 << 63) - 1), (1 << 63) - 1),
    ],
)
def test_signed_values_preserve_source_attributes_handle_and_owner(model, source, expected):
    owner = subspace(source, model)
    node = owner.base_address
    node.other_attributes = {"{urn:test}tag": "original"}
    node_id = get_handle(node)
    assert api.getSubspaceMapBaseAddress(get_handle(owner)) == expected
    assert api.getSubspaceMapBaseAddressExpression(get_handle(owner)) == source
    assert api.getSubspaceMapBaseAddressID(get_handle(owner)) == node_id
    assert node.value == source and node.other_attributes == {"{urn:test}tag": "original"}
    info = get_parent_info(node_id)
    assert resolve_handle(info.parent_handle) is owner and info.path == ("base_address",) and info.container == "single"


@pytest.mark.parametrize("source", [str(-(1 << 63) - 1), str(1 << 63), "PARAM", "1.5", "1 / 0"])
def test_numeric_errors_retain_raw_expression_and_handle(source):
    owner = subspace(source)
    with pytest.raises(TgiError) as error:
        api.getSubspaceMapBaseAddress(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getSubspaceMapBaseAddressExpression(get_handle(owner)) == source
    assert api.getSubspaceMapBaseAddressID(get_handle(owner)) == get_handle(owner.base_address)


def test_declared_bounds_and_required_typed_base_child():
    owner = subspace("-4")
    owner.base_address.minimum, owner.base_address.maximum = -5, -3
    assert api.getSubspaceMapBaseAddress(get_handle(owner)) == -4
    owner.base_address.minimum = -2
    with pytest.raises(TgiError) as error:
        api.getSubspaceMapBaseAddress(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    owner.base_address.minimum = True
    with pytest.raises(TgiError) as error:
        api.getSubspaceMapBaseAddress(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for invalid in (None, ModeRef(value="wrong", priority=0)):
        owner.base_address = invalid
        for op in (
            api.getSubspaceMapBaseAddress,
            api.getSubspaceMapBaseAddressExpression,
            api.getSubspaceMapBaseAddressID,
        ):
            with pytest.raises(TgiError) as error:
                op(get_handle(owner))
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_segment_name_absence_normalization_and_round_trip():
    owner = subspace()
    assert api.getSubspaceMapSegmentRefByName(get_handle(owner)) is None
    owner.segment_ref = "  segment  "
    assert api.getSubspaceMapSegmentRefByName(get_handle(owner)) == "segment"
    assert owner.segment_ref == "  segment  "
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(owner), SubspaceMap)
    assert api.getSubspaceMapBaseAddress(get_handle(parsed)) == -4
    assert api.getSubspaceMapSegmentRefByName(get_handle(parsed)) == "segment"
    for invalid in ("bad name", "", [], 42):
        owner.segment_ref = invalid
        with pytest.raises(TgiError) as error:
            api.getSubspaceMapSegmentRefByName(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("model", [MemoryRemap, MemoryRemapType])
def test_mode_names_ids_and_handle_to_target_follow_actual_component(model):
    first, second = ModeRef(value="  sleep  ", priority=2), ModeRef(value="active", priority=1)
    original = (first, second)
    remap = model(name="remap", mode_ref=original)
    owner = component(remap)
    assert api.getMemoryRemapModeRefByNames(get_handle(remap)) == ["sleep", "active"]
    assert api.getMemoryRemapModeRefIDs(get_handle(remap)) == [get_handle(first), get_handle(second)]
    assert remap.mode_ref is original and first.value == "  sleep  " and first.priority == 2
    assert api.getMemoryRemapModeRefByID(get_handle(remap), get_handle(first)) == get_handle(owner.modes.mode[1])
    assert api.getMemoryRemapModeRefByID(get_handle(remap), get_handle(second)) == get_handle(owner.modes.mode[0])
    info = get_parent_info(get_handle(first))
    assert resolve_handle(info.parent_handle) is remap and info.path == ("mode_ref",) and info.container == "list"
    if model is MemoryRemap:
        parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(owner), Component)
        _register_graph(parsed)
        parsed_remap = parsed.memory_maps.memory_map[0].choice[0]
        ids = api.getMemoryRemapModeRefIDs(get_handle(parsed_remap))
        assert api.getMemoryRemapModeRefByID(get_handle(parsed_remap), ids[0]) == get_handle(parsed.modes.mode[1])


def test_mode_targets_are_component_scoped_and_missing_ambiguous_or_foreign_handles_fault():
    ref = ModeRef(value="active", priority=0)
    remap = MemoryRemap(name="remap", mode_ref=[ref])
    owner = component(remap, ("active",))
    other_ref = ModeRef(value="active", priority=0)
    other = component(MemoryRemap(name="other", mode_ref=[other_ref]), ("active",))
    assert api.getMemoryRemapModeRefByID(get_handle(remap), get_handle(ref)) == get_handle(owner.modes.mode[0])
    assert get_handle(owner.modes.mode[0]) != get_handle(other.modes.mode[0])
    for invalid in (None, [], {}, "active", "missing", get_handle(other_ref)):
        with pytest.raises(TgiError) as error:
            api.getMemoryRemapModeRefByID(get_handle(remap), invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    ref.value = "absent"
    with pytest.raises(TgiError) as error:
        api.getMemoryRemapModeRefByID(get_handle(remap), get_handle(ref))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    ref.value = "active"
    owner.modes.mode.append(ComponentType.Modes.Mode(name="active"))
    with pytest.raises(TgiError) as error:
        api.getMemoryRemapModeRefByID(get_handle(remap), get_handle(ref))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    "values", [None, {}, pytest.param((object(),), id="foreign-object"), (ModeRef(value="bad name", priority=0),)]
)
def test_mode_collections_reject_invalid_model_and_source(values):
    remap = MemoryRemap(name="remap", mode_ref=values)
    for op in (api.getMemoryRemapModeRefByNames, api.getMemoryRemapModeRefIDs):
        with pytest.raises(TgiError) as error:
            op(get_handle(remap))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert remap.mode_ref is values


def test_empty_modes_and_detached_target_resolution():
    remap = MemoryRemap(name="empty", mode_ref=())
    assert api.getMemoryRemapModeRefByNames(get_handle(remap)) == []
    assert api.getMemoryRemapModeRefIDs(get_handle(remap)) == []
    ref = ModeRef(value="active", priority=0)
    remap.mode_ref = (ref,)
    with pytest.raises(TgiError) as error:
        api.getMemoryRemapModeRefByID(get_handle(remap), get_handle(ref))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


def test_exact_annex_parameters_and_invalid_owner_handles():
    operations = [
        (api.getMemoryRemapModeRefByID, ["memoryRemapID", "modeRef"]),
        (api.getMemoryRemapModeRefByNames, ["memoryRemapID"]),
        (api.getMemoryRemapModeRefIDs, ["memoryRemapID"]),
        (api.getSubspaceMapBaseAddress, ["subSpaceMapID"]),
        (api.getSubspaceMapBaseAddressExpression, ["subSpaceMapID"]),
        (api.getSubspaceMapBaseAddressID, ["subspaceMapID"]),
        (api.getSubspaceMapSegmentRefByName, ["subSpaceID"]),
    ]
    for op, parameters in operations:
        assert list(inspect.signature(op).parameters) == parameters
        for invalid in (None, [], {}, "missing", get_handle(ModeRef(value="wrong", priority=0))):
            args = [invalid, "missing"] if len(parameters) == 2 else [invalid]
            with pytest.raises(TgiError) as error:
                op(*args)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
