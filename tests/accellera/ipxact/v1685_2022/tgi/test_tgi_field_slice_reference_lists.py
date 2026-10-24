"""Field-slice bank and register-file references preserve list ownership."""

import inspect
from collections.abc import Iterator, Sequence
from typing import cast

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import slice_ as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockRef,
    AddressSpaces,
    BankRef,
    Component,
    ComponentPortDirectionType,
    ComponentType,
    FieldMap,
    FieldMaps,
    FieldRef,
    Index,
    Indices,
    Left,
    Model,
    Port,
    PortWireType,
    Range,
    RegisterFileRef,
    RegisterRef,
    Right,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_ModeFieldSlice = ComponentType.Modes.Mode.FieldSlice
_MapFieldSlice = FieldMap.FieldSlice
_FieldSlice = _ModeFieldSlice | _MapFieldSlice
_FieldSliceType = type[_ModeFieldSlice] | type[_MapFieldSlice]
_KINDS: tuple[_FieldSliceType, ...] = (_ModeFieldSlice, _MapFieldSlice)
_KIND_IDS = ("mode", "field-map")
_REFERENCES: tuple[tuple[str, str, type[BankRef] | type[RegisterFileRef]], ...] = (
    ("BankRef", "bank_ref", BankRef),
    ("RegisterFileRef", "register_file_ref", RegisterFileRef),
)
_REFERENCE_IDS = ("bank", "register-file")


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field_slice(
    kind: _FieldSliceType,
    bank_refs: Sequence[BankRef] = (),
    register_file_refs: Sequence[RegisterFileRef] = (),
) -> _FieldSlice:
    shared = {
        "address_space_ref_or_memory_map_ref_or_memory_remap_ref": [
            kind.AddressSpaceRef(address_space_ref="register_space")
        ],
        "address_block_ref": AddressBlockRef(address_block_ref="registers"),
        "register_ref": RegisterRef(register_ref="control"),
        "field_ref": FieldRef(field_ref="enable"),
        "bank_ref": bank_refs,
        "register_file_ref": register_file_refs,
        "range": Range(left=Left(value="7"), right=Right(value="0")),
    }
    if kind is _ModeFieldSlice:
        return _ModeFieldSlice(name="control_enable", **shared)
    return _MapFieldSlice(**shared)


def _component(item: _FieldSlice) -> Component:
    port = Port(
        name="data_i",
        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
    )
    if isinstance(item, _MapFieldSlice):
        port.field_maps = FieldMaps(field_map=[FieldMap(field_slice=item)])
        modes = ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")])
    else:
        modes = ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active", field_slice=[item])])
    return Component(
        vendor="acme",
        library="devices",
        name="field_slice_reference_list_component",
        version="1.0",
        model=Model(ports=Model.Ports(port=[port])),
        modes=modes,
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="register_space",
                    range=UnsignedPositiveLongintExpression(value="4096"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
            ]
        ),
    )


def _parsed_field_slice(kind: _FieldSliceType) -> _FieldSlice:
    root = _component(_field_slice(kind))
    xml = XmlDocument.serializer().render(root)
    tree = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(tree), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    if kind is _ModeFieldSlice:
        return parsed.modes.mode[0].field_slice[0]
    return parsed.model.ports.port[0].field_maps.field_map[0].field_slice


def _values(item: _FieldSlice, attribute: str) -> Sequence[object]:
    return cast(Sequence[object], getattr(item, attribute))


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize("suffix,attribute,wrapper", _REFERENCES, ids=_REFERENCE_IDS)
def test_field_slice_reference_list_getters_preserve_names_order_and_typed_ownership(
    kind: _FieldSliceType, suffix: str, attribute: str, wrapper: type[BankRef] | type[RegisterFileRef]
) -> None:
    bank_refs = (BankRef(bank_ref="window_a"), BankRef(bank_ref="window_b"))
    register_file_refs = (
        RegisterFileRef(register_file_ref="control_files"),
        RegisterFileRef(register_file_ref="status_files"),
    )
    item = _field_slice(kind, bank_refs=bank_refs, register_file_refs=register_file_refs)
    owner_id = get_handle(item)
    children = _values(item, attribute)

    assert getattr(api, f"getFieldSlice{suffix}ByNames")(owner_id) == [getattr(child, attribute) for child in children]
    child_ids = getattr(api, f"getFieldSlice{suffix}IDs")(owner_id)
    assert child_ids == [get_handle(child) for child in children]
    for child_id, child in zip(child_ids, children, strict=True):
        assert isinstance(child, wrapper)
        assert resolve_handle(child_id) is child
        info = get_parent_info(child_id)
        assert info is not None and info.parent_handle == owner_id
        assert info.path == (attribute,)


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize("suffix,attribute,wrapper", _REFERENCES, ids=_REFERENCE_IDS)
def test_field_slice_reference_list_getters_are_empty_and_tuple_neutral(
    kind: _FieldSliceType, suffix: str, attribute: str, wrapper: type[BankRef] | type[RegisterFileRef]
) -> None:
    item = _field_slice(kind)
    owner_id = get_handle(item)
    assert getattr(api, f"getFieldSlice{suffix}ByNames")(owner_id) == []
    assert getattr(api, f"getFieldSlice{suffix}IDs")(owner_id) == []

    child: BankRef | RegisterFileRef
    child = BankRef(bank_ref="window") if suffix == "BankRef" else RegisterFileRef(register_file_ref="control_files")
    setattr(item, attribute, (child,))
    collection = getattr(item, attribute)
    assert isinstance(collection, tuple)
    assert getattr(api, f"getFieldSlice{suffix}ByNames")(owner_id) == [
        getattr(child, "bank_ref" if suffix == "BankRef" else "register_file_ref")
    ]
    assert isinstance(getattr(item, attribute), tuple)
    assert getattr(item, attribute) is collection


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "suffix,attribute,name_parameter,xml_attribute,wrapper",
    [
        ("BankRef", "bank_ref", "bankRef", "bank_ref", BankRef),
        ("RegisterFileRef", "register_file_ref", "registerFileRef", "register_file_ref", RegisterFileRef),
    ],
    ids=_REFERENCE_IDS,
)
def test_field_slice_reference_list_adders_normalize_and_preserve_existing_children(
    kind: _FieldSliceType,
    suffix: str,
    attribute: str,
    name_parameter: str,
    xml_attribute: str,
    wrapper: type[BankRef] | type[RegisterFileRef],
) -> None:
    existing: BankRef | RegisterFileRef
    if suffix == "BankRef":
        existing = BankRef(bank_ref="first_window")
    else:
        existing = RegisterFileRef(
            register_file_ref="first_files",
            indices=Indices(index=[Index(value="3", id="slice_index")]),
        )
    item = _field_slice(
        kind,
        bank_refs=(existing,) if suffix == "BankRef" else (),
        register_file_refs=(existing,) if suffix == "RegisterFileRef" else (),
    )
    owner_id = get_handle(item)
    old_id = get_handle(existing)
    if suffix == "RegisterFileRef":
        index_node = cast(RegisterFileRef, existing).indices.index[0]
        index_id = get_handle(index_node)
    else:
        index_node = None
        index_id = None
    setattr(item, attribute, (existing,))
    add = getattr(api, f"addFieldSlice{suffix}")
    new_id = add(owner_id, " \tΩ:next.item\n")

    assert isinstance(getattr(item, attribute), list)
    children = _values(item, attribute)
    assert children[0] is existing
    assert getattr(existing, xml_attribute) == ("first_window" if suffix == "BankRef" else "first_files")
    assert getattr(children[1], xml_attribute) == "Ω:next.item"
    assert isinstance(children[1], wrapper)
    assert get_handle(children[0]) == old_id
    if suffix == "BankRef":
        assert api.getFieldSliceBankRefIDs(owner_id) == [old_id, new_id]
    else:
        assert api.getFieldSliceRegisterFileRefIDs(owner_id) == [old_id, new_id]
    info = get_parent_info(new_id)
    assert info is not None and info.parent_handle == owner_id
    assert info.path == (attribute,)
    assert resolve_handle(new_id) is children[1]
    if index_node is not None:
        assert cast(RegisterFileRef, existing).indices.index[0] is index_node
        assert get_handle(index_node) == index_id
        assert index_node.value == "3" and index_node.id == "slice_index"


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "suffix,attribute,parameter",
    [
        ("BankRef", "bank_ref", "bankRef"),
        ("RegisterFileRef", "register_file_ref", "registerFileRef"),
    ],
    ids=_REFERENCE_IDS,
)
def test_field_slice_reference_list_adders_reject_invalid_names_atomically(
    kind: _FieldSliceType, suffix: str, attribute: str, parameter: str
) -> None:
    existing: BankRef | RegisterFileRef = (
        BankRef(bank_ref="existing") if suffix == "BankRef" else RegisterFileRef(register_file_ref="existing")
    )
    item = _field_slice(
        kind,
        bank_refs=(existing,) if suffix == "BankRef" else (),
        register_file_refs=(existing,) if suffix == "RegisterFileRef" else (),
    )
    owner_id = get_handle(item)
    before = getattr(item, attribute)
    before_id = get_handle(existing)
    add = getattr(api, f"addFieldSlice{suffix}")

    for invalid in ("", "  ", "1invalid", "has space", "bad/name", "nul\x00name", None, 12):
        with pytest.raises(TgiError) as error:
            add(owner_id, cast(str, invalid))
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert getattr(item, attribute) is before
        assert tuple(getattr(item, attribute)) == (existing,)
        assert get_handle(existing) == before_id


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "suffix,attribute,wrong_attribute,wrapper",
    [
        ("BankRef", "bank_ref", "register_file_ref", BankRef),
        ("RegisterFileRef", "register_file_ref", "bank_ref", RegisterFileRef),
    ],
    ids=_REFERENCE_IDS,
)
def test_field_slice_reference_list_operations_reject_malformed_collections(
    kind: _FieldSliceType,
    suffix: str,
    attribute: str,
    wrong_attribute: str,
    wrapper: type[BankRef] | type[RegisterFileRef],
) -> None:
    item = _field_slice(kind)
    owner_id = get_handle(item)
    for malformed in ("scalar", [object()], [wrapper(**{attribute: 7})]):
        setattr(item, attribute, malformed)
        for operation in (f"getFieldSlice{suffix}ByNames", f"getFieldSlice{suffix}IDs", f"addFieldSlice{suffix}"):
            with pytest.raises(TgiError) as error:
                if operation.startswith("add"):
                    getattr(api, operation)(owner_id, "replacement")
                else:
                    getattr(api, operation)(owner_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert getattr(item, attribute) is malformed
        setattr(item, attribute, [])


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_reference_list_removal_detaches_only_selected_child_and_invalidates_indices(
    kind: _FieldSliceType,
) -> None:
    first = BankRef(bank_ref="first")
    second = BankRef(bank_ref="second")
    indexed = RegisterFileRef(
        register_file_ref="indexed_file",
        indices=Indices(index=[Index(value="2", id="outer"), Index(value="5", id="inner")]),
    )
    item = _field_slice(kind, bank_refs=[first, second], register_file_refs=[indexed])
    owner_id = get_handle(item)
    first_id, second_id = api.getFieldSliceBankRefIDs(owner_id)
    register_id = api.getFieldSliceRegisterFileRefIDs(owner_id)[0]
    indices_id = get_handle(indexed.indices)
    index_nodes = tuple(indexed.indices.index)
    index_ids = tuple(get_handle(index) for index in index_nodes)
    unrelated_ids = (get_handle(item.address_block_ref), get_handle(item.register_ref), get_handle(item.range))

    assert api.removeFieldSliceBankRef(first_id)
    assert item.bank_ref == [second]
    assert api.getFieldSliceBankRefIDs(owner_id) == [second_id]
    assert resolve_handle(first_id) is None
    assert resolve_handle(second_id) is second
    assert resolve_handle(owner_id) is item

    assert api.removeFieldSliceRegisterFileRef(register_id)
    assert item.register_file_ref == []
    assert api.getFieldSliceRegisterFileRefIDs(owner_id) == []
    assert resolve_handle(register_id) is None
    assert resolve_handle(indices_id) is None
    assert all(resolve_handle(index_id) is None for index_id in index_ids)
    assert (
        tuple(get_handle(child) for child in (item.address_block_ref, item.register_ref, item.range)) == unrelated_ids
    )
    with pytest.raises(TgiError) as error:
        api.removeFieldSliceRegisterFileRef(register_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_reference_list_removers_reject_orphan_wrong_kind_and_owner_handles(kind: _FieldSliceType) -> None:
    item = _field_slice(kind)
    owner_id = get_handle(item)
    orphan_bank_id = get_handle(BankRef(bank_ref="orphan"))
    orphan_register_file_id = get_handle(RegisterFileRef(register_file_ref="orphan"))
    wrong_kind_id = api.addFieldSliceBankRef(owner_id, "owned_bank")
    other_owner_id = get_handle(_field_slice(kind))

    for handle in (orphan_bank_id, other_owner_id, owner_id):
        with pytest.raises(TgiError) as error:
            api.removeFieldSliceBankRef(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for handle in (orphan_register_file_id, other_owner_id, owner_id):
        with pytest.raises(TgiError) as error:
            api.removeFieldSliceRegisterFileRef(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert item.bank_ref == [BankRef(bank_ref="owned_bank")]
    assert api.getFieldSliceBankRefIDs(owner_id) == [wrong_kind_id]


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_parsed_field_slice_reference_lists_round_trip_after_addition(kind: _FieldSliceType) -> None:
    item = _parsed_field_slice(kind)
    owner_id = get_handle(item)
    bank_id = api.addFieldSliceBankRef(owner_id, "added_bank")
    register_file_id = api.addFieldSliceRegisterFileRef(owner_id, "added_files")
    assert resolve_handle(bank_id) is item.bank_ref[0]
    assert resolve_handle(register_file_id) is item.register_file_ref[0]

    xml = XmlDocument.serializer().render(_component(item))
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed_root = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed_root) == xml
    if kind is _ModeFieldSlice:
        parsed_item = parsed_root.modes.mode[0].field_slice[0]
    else:
        parsed_item = parsed_root.model.ports.port[0].field_maps.field_map[0].field_slice
    parsed_owner_id = get_handle(parsed_item)
    assert api.getFieldSliceBankRefByNames(parsed_owner_id) == ["added_bank"]
    assert api.getFieldSliceRegisterFileRefByNames(parsed_owner_id) == ["added_files"]


def test_field_slice_reference_list_exports_and_native_signatures_match_annex_contract() -> None:
    expected: dict[str, tuple[tuple[str, ...], tuple[object, ...], object]] = {}
    for suffix, name_parameter in (("BankRef", "bankRef"), ("RegisterFileRef", "registerFileRef")):
        expected[f"getFieldSlice{suffix}ByNames"] = (("fieldSliceID",), (str,), list[str])
        expected[f"getFieldSlice{suffix}IDs"] = (("fieldSliceID",), (str,), list[str])
        expected[f"addFieldSlice{suffix}"] = (("fieldSliceID", name_parameter), (str, str), str)
        expected[f"removeFieldSlice{suffix}"] = ((f"fieldSlice{suffix}ID",), (str,), bool)

    assert set(expected) <= set(api.__all__)
    for name, (parameter_names, parameter_types, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type
