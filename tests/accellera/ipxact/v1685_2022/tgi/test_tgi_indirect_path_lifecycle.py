"""Mutation and removal contracts for indirect bank and register-file paths."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import indirect_interface as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import slice_ as slice_api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockRef,
    AlternateRegisterRef,
    BankRef,
    Component,
    FieldMap,
    FieldRef,
    Index,
    Indices,
    IndirectAddressRef,
    IndirectDataRef,
    IndirectInterface,
    IndirectInterfaces,
    MemoryMaps,
    MemoryMapType,
    RegisterFileRef,
    RegisterRef,
    Value,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_ADDERS = (
    "addIndirectAddressRefBankRef",
    "addIndirectAddressRefRegisterFileRef",
    "addIndirectDataRefBankRef",
    "addIndirectDataRefRegisterFileRef",
)
_REMOVERS = (
    "removeIndirectAddressRefBankRef",
    "removeIndirectAddressRefRegisterFileRef",
    "removeIndirectDataRefBankRef",
    "removeIndirectDataRefRegisterFileRef",
)
_API_FUNCTIONS = (*_ADDERS, *_REMOVERS)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _address_ref(suffix: str) -> IndirectAddressRef:
    return IndirectAddressRef(
        bank_ref=[
            BankRef(bank_ref=f"bank_{suffix}_0", id=f"{suffix}_bank_0"),
            BankRef(bank_ref=f"bank_{suffix}_1", id=f"{suffix}_bank_1"),
        ],
        register_file_ref=[
            RegisterFileRef(
                register_file_ref=f"register_file_{suffix}_0",
                indices=Indices(index=[Index(value="1", id=f"{suffix}_rf_0_index")]),
                id=f"{suffix}_register_file_0",
            ),
            RegisterFileRef(
                register_file_ref=f"register_file_{suffix}_1",
                indices=Indices(index=[Index(value="4", id=f"{suffix}_rf_1_index")]),
                id=f"{suffix}_register_file_1",
            ),
        ],
        register_ref=RegisterRef(register_ref=f"register_{suffix}"),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref=f"alternate_{suffix}"),
        field_ref=FieldRef(field_ref=f"field_{suffix}"),
    )


def _data_ref(suffix: str) -> IndirectDataRef:
    return IndirectDataRef(
        bank_ref=[
            BankRef(bank_ref=f"data_bank_{suffix}_0", id=f"{suffix}_data_bank_0"),
            BankRef(bank_ref=f"data_bank_{suffix}_1", id=f"{suffix}_data_bank_1"),
        ],
        register_file_ref=[
            RegisterFileRef(
                register_file_ref=f"data_register_file_{suffix}_0",
                indices=Indices(index=[Index(value="2", id=f"{suffix}_data_rf_0_index")]),
                id=f"{suffix}_data_register_file_0",
            ),
            RegisterFileRef(
                register_file_ref=f"data_register_file_{suffix}_1",
                indices=Indices(index=[Index(value="5", id=f"{suffix}_data_rf_1_index")]),
                id=f"{suffix}_data_register_file_1",
            ),
        ],
        register_ref=RegisterRef(register_ref=f"data_register_{suffix}"),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref=f"data_alternate_{suffix}"),
        field_ref=FieldRef(field_ref=f"data_field_{suffix}"),
    )


def _indirect_interface(name: str, suffix: str) -> IndirectInterface:
    return IndirectInterface(
        name=name,
        indirect_address_ref=_address_ref(suffix),
        indirect_data_ref=_data_ref(suffix),
        memory_map_ref_or_transparent_bridge=[f"map_{suffix}"],
    )


def _component(*, name: str = "indirect_path_lifecycle") -> Component:
    return Component(
        vendor="acme",
        library="devices",
        name=name,
        version="1.0",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map_a"), MemoryMapType(name="map_b")]),
        indirect_interfaces=IndirectInterfaces(
            indirect_interface=[_indirect_interface("indirect_a", "a"), _indirect_interface("indirect_b", "b")]
        ),
    )


def _xml_round_trip(root: Component) -> str:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    reparsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(reparsed) == xml
    return xml


def _parsed_component(root: Component | None = None) -> Component:
    source = root or _component()
    xml = XmlDocument.serializer().render(source)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    return parsed


def test_public_exports_native_signatures_and_annex_f_sections() -> None:
    expected = {
        "addIndirectAddressRefBankRef": ("indirectAddressRefID", "bankRef", str, "F.7.54.1"),
        "addIndirectAddressRefRegisterFileRef": ("indirectAddressRefID", "registerFileRef", str, "F.7.54.2"),
        "addIndirectDataRefBankRef": ("indirectDataRefID", "bankRef", str, "F.7.54.3"),
        "addIndirectDataRefRegisterFileRef": ("indirectDataRefID", "registerFileRef", str, "F.7.54.4"),
        "removeIndirectAddressRefBankRef": ("bankRefID", None, bool, "F.7.54.11"),
        "removeIndirectAddressRefRegisterFileRef": ("registerFileRefID", None, bool, "F.7.54.14"),
        "removeIndirectDataRefBankRef": ("bankRefID", None, bool, "F.7.54.19"),
        "removeIndirectDataRefRegisterFileRef": ("registerFileRefID", None, bool, "F.7.54.22"),
    }

    assert set(_API_FUNCTIONS) == set(expected)
    assert set(_API_FUNCTIONS) <= set(api.__all__)
    assert set(_API_FUNCTIONS) <= set(tgi.__all__)
    for name, (owner_parameter, value_parameter, return_type, section) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        expected_parameters = (owner_parameter,) if value_parameter is None else (owner_parameter, value_parameter)
        assert tuple(signature.parameters) == expected_parameters
        for parameter in signature.parameters.values():
            assert parameter.annotation is str
            assert not isinstance(parameter.annotation, str)
            assert parameter.default is inspect.Signature.empty
        assert signature.return_annotation is return_type
        assert f"Section: {section}." in inspect.getdoc(function)


@pytest.mark.parametrize(
    ("add_name", "ref_attr", "collection_attr", "getter_names", "value"),
    [
        (
            "addIndirectAddressRefBankRef",
            "indirect_address_ref",
            "bank_ref",
            ("getIndirectAddressRefBankRefByNames", "getIndirectAddressRefBankRefIDs"),
            "  δ_bank\t",
        ),
        (
            "addIndirectAddressRefRegisterFileRef",
            "indirect_address_ref",
            "register_file_ref",
            ("getIndirectAddressRefRegisterFileRefByNames", "getIndirectAddressRefRegisterFileRefIDs"),
            "  δ_register_file\t",
        ),
        (
            "addIndirectDataRefBankRef",
            "indirect_data_ref",
            "bank_ref",
            ("getIndirectDataRefBankRefByNames", "getIndirectDataRefBankRefIDs"),
            "  δ_data_bank\t",
        ),
        (
            "addIndirectDataRefRegisterFileRef",
            "indirect_data_ref",
            "register_file_ref",
            ("getIndirectDataRefRegisterFileRefByNames", "getIndirectDataRefRegisterFileRefIDs"),
            "  δ_data_register_file\t",
        ),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
def test_adders_normalize_names_preserve_order_and_allow_repeated_names(
    add_name: str, ref_attr: str, collection_attr: str, getter_names: tuple[str, str], value: str
) -> None:
    root = _parsed_component()
    owner = getattr(root.indirect_interfaces.indirect_interface[0], ref_attr)
    original = tuple(getattr(owner, collection_attr))
    setattr(owner, collection_attr, original)
    add = getattr(api, add_name)
    first_id = add(get_handle(owner), value)
    normalized = value.strip()
    second_id = add(get_handle(owner), normalized)
    child_ids = getattr(api, getter_names[1])(get_handle(owner))
    child_names = getattr(api, getter_names[0])(get_handle(owner))
    assert child_ids == [*(get_handle(child) for child in original), first_id, second_id]
    assert child_names == [
        *(getattr(child, "bank_ref" if collection_attr == "bank_ref" else "register_file_ref") for child in original),
        normalized,
        normalized,
    ]
    assert first_id != second_id
    assert getattr(owner, collection_attr) == [*original, resolve_handle(first_id), resolve_handle(second_id)]
    assert all(resolve_handle(child_id) is not None for child_id in child_ids)
    info = get_parent_info(first_id)
    assert info is not None
    assert info.parent_handle == get_handle(owner)
    assert info.path == (collection_attr,)
    assert info.container == "list"
    _xml_round_trip(root)


@pytest.mark.parametrize(
    ("add_name", "ref_attr", "collection_attr"),
    [
        ("addIndirectAddressRefBankRef", "indirect_address_ref", "bank_ref"),
        ("addIndirectAddressRefRegisterFileRef", "indirect_address_ref", "register_file_ref"),
        ("addIndirectDataRefBankRef", "indirect_data_ref", "bank_ref"),
        ("addIndirectDataRefRegisterFileRef", "indirect_data_ref", "register_file_ref"),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
@pytest.mark.parametrize(
    "bad_name",
    [None, 7, True, Value(value="wrapped"), "", "bad name"],
    ids=("none", "integer", "boolean", "value-wrapper", "empty", "invalid-xs-name"),
)
def test_adders_reject_invalid_names_atomically_and_preserve_tuple_collections(
    add_name: str, ref_attr: str, collection_attr: str, bad_name: object
) -> None:
    root = _parsed_component()
    owner = getattr(root.indirect_interfaces.indirect_interface[0], ref_attr)
    original = tuple(getattr(owner, collection_attr))
    setattr(owner, collection_attr, original)

    with pytest.raises(TgiError) as error:
        getattr(api, add_name)(get_handle(owner), bad_name)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(owner, collection_attr) is original
    assert tuple(getattr(owner, collection_attr)) == original
    assert all(resolve_handle(get_handle(child)) is child for child in original)


@pytest.mark.parametrize(
    ("add_name", "ref_attr", "collection_attr"),
    [
        ("addIndirectAddressRefBankRef", "indirect_address_ref", "bank_ref"),
        ("addIndirectAddressRefRegisterFileRef", "indirect_address_ref", "register_file_ref"),
        ("addIndirectDataRefBankRef", "indirect_data_ref", "bank_ref"),
        ("addIndirectDataRefRegisterFileRef", "indirect_data_ref", "register_file_ref"),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
@pytest.mark.parametrize("malformed", [object(), [object()]], ids=("not-a-sequence", "wrong-child"))
def test_adders_reject_malformed_existing_collections_without_mutation(
    add_name: str,
    ref_attr: str,
    collection_attr: str,
    malformed: object,
) -> None:
    root = _parsed_component()
    owner = getattr(root.indirect_interfaces.indirect_interface[0], ref_attr)
    setattr(owner, collection_attr, malformed)

    with pytest.raises(TgiError) as error:
        getattr(api, add_name)(get_handle(owner), "new_reference")

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, collection_attr) is malformed


@pytest.mark.parametrize(
    ("add_name", "ref_attr", "collection_attr", "child", "value_attr"),
    [
        ("addIndirectAddressRefBankRef", "indirect_address_ref", "bank_ref", BankRef(bank_ref="valid"), "bank_ref"),
        (
            "addIndirectAddressRefRegisterFileRef",
            "indirect_address_ref",
            "register_file_ref",
            RegisterFileRef(register_file_ref="valid"),
            "register_file_ref",
        ),
        ("addIndirectDataRefBankRef", "indirect_data_ref", "bank_ref", BankRef(bank_ref="valid"), "bank_ref"),
        (
            "addIndirectDataRefRegisterFileRef",
            "indirect_data_ref",
            "register_file_ref",
            RegisterFileRef(register_file_ref="valid"),
            "register_file_ref",
        ),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
@pytest.mark.parametrize(
    "bad_value",
    [Value(value="wrapped"), True, 7, None],
    ids=("value-wrapper", "boolean", "integer", "missing-attribute"),
)
def test_adders_reject_non_string_existing_sources_atomically(
    add_name: str,
    ref_attr: str,
    collection_attr: str,
    child: BankRef | RegisterFileRef,
    value_attr: str,
    bad_value: object,
) -> None:
    root = _parsed_component()
    owner = getattr(root.indirect_interfaces.indirect_interface[0], ref_attr)
    original = tuple(getattr(owner, collection_attr))
    setattr(child, value_attr, bad_value)
    malformed = (child, *original)
    setattr(owner, collection_attr, malformed)

    with pytest.raises(TgiError) as error:
        getattr(api, add_name)(get_handle(owner), "new_reference")

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, collection_attr) is malformed
    assert getattr(owner, collection_attr)[0] is child


@pytest.mark.parametrize(
    ("remove_name", "owner_kind", "collection_attr", "getter_name"),
    [
        ("removeIndirectAddressRefBankRef", "address", "bank_ref", "getIndirectAddressRefBankRefIDs"),
        (
            "removeIndirectAddressRefRegisterFileRef",
            "address",
            "register_file_ref",
            "getIndirectAddressRefRegisterFileRefIDs",
        ),
        ("removeIndirectDataRefBankRef", "data", "bank_ref", "getIndirectDataRefBankRefIDs"),
        (
            "removeIndirectDataRefRegisterFileRef",
            "data",
            "register_file_ref",
            "getIndirectDataRefRegisterFileRefIDs",
        ),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
def test_removers_discover_parsed_membership_preserve_peers_and_keep_empty_lists(
    remove_name: str, owner_kind: str, collection_attr: str, getter_name: str
) -> None:
    root = _parsed_component()
    first, second = root.indirect_interfaces.indirect_interface
    owner = first.indirect_address_ref if owner_kind == "address" else first.indirect_data_ref
    children = owner.bank_ref if collection_attr == "bank_ref" else owner.register_file_ref
    target, peer = children
    target_id, peer_id = get_handle(target), get_handle(peer)
    owner_id, interface_id = get_handle(owner), get_handle(first)
    target_indices = target.indices if isinstance(target, RegisterFileRef) else None
    index_ids = [get_handle(index) for index in target_indices.index] if target_indices is not None else []
    peer_indices = peer.indices if isinstance(peer, RegisterFileRef) else None
    peer_index_ids = [get_handle(index) for index in peer_indices.index] if peer_indices is not None else []

    assert getattr(api, remove_name)(target_id) is True

    assert getattr(owner, collection_attr) == [peer]
    assert resolve_handle(target_id) is None
    assert resolve_handle(peer_id) is peer
    assert all(resolve_handle(index_id) is None for index_id in index_ids)
    assert all(resolve_handle(index_id) is not None for index_id in peer_index_ids)
    assert resolve_handle(owner_id) is owner
    assert resolve_handle(interface_id) is first
    assert getattr(api, getter_name)(owner_id) == [peer_id]

    assert getattr(api, remove_name)(peer_id) is True
    assert getattr(owner, collection_attr) == []
    assert resolve_handle(peer_id) is None
    assert resolve_handle(owner_id) is owner
    assert getattr(api, getter_name)(owner_id) == []
    assert first.indirect_address_ref is not None and first.indirect_data_ref is not None
    assert second in root.indirect_interfaces.indirect_interface
    _xml_round_trip(root)


@pytest.mark.parametrize(
    ("remove_name", "collection_attr", "wrong_remove_name", "wrong_child_attr"),
    (
        ("removeIndirectAddressRefBankRef", "bank_ref", "removeIndirectAddressRefRegisterFileRef", "register_file_ref"),
        (
            "removeIndirectAddressRefRegisterFileRef",
            "register_file_ref",
            "removeIndirectAddressRefBankRef",
            "bank_ref",
        ),
        ("removeIndirectDataRefBankRef", "bank_ref", "removeIndirectDataRefRegisterFileRef", "register_file_ref"),
        (
            "removeIndirectDataRefRegisterFileRef",
            "register_file_ref",
            "removeIndirectDataRefBankRef",
            "bank_ref",
        ),
    ),
    ids=("address-bank-wrong-role", "address-register-file-wrong-role", "data-bank-wrong-role", "data-rf-wrong-role"),
)
def test_removers_reject_wrong_wrapper_role_and_foreign_indirect_owner(
    remove_name: str, collection_attr: str, wrong_remove_name: str, wrong_child_attr: str
) -> None:
    root = _parsed_component()
    first = root.indirect_interfaces.indirect_interface[0]
    address_ref, data_ref = first.indirect_address_ref, first.indirect_data_ref
    target_owner = data_ref if "Data" in remove_name else address_ref
    wrong_role_child = getattr(target_owner, wrong_child_attr)[0]
    target_id = get_handle(getattr(target_owner, collection_attr)[0])
    wrong_owner_child = data_ref if "Address" in remove_name else address_ref
    foreign_id = get_handle(getattr(wrong_owner_child, collection_attr)[0])

    for child_id in (get_handle(wrong_role_child), foreign_id):
        with pytest.raises(TgiError) as error:
            getattr(api, remove_name)(child_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert resolve_handle(target_id) is getattr(target_owner, collection_attr)[0]
    assert getattr(api, remove_name)(target_id) is True


def test_removers_reject_orphan_field_slice_mislinked_and_stale_handles() -> None:
    field_slice = FieldMap.FieldSlice(
        bank_ref=[BankRef(bank_ref="field_slice_bank")],
        register_file_ref=[RegisterFileRef(register_file_ref="field_slice_file")],
        address_block_ref=AddressBlockRef(address_block_ref="block"),
        register_ref=RegisterRef(register_ref="register"),
        field_ref=FieldRef(field_ref="field"),
    )
    field_root = FieldMap(field_slice=field_slice)
    registry.register(field_root, ("acme", "field", "map", "1"))
    field_bank_id = get_handle(field_slice.bank_ref[0])
    field_file_id = get_handle(field_slice.register_file_ref[0])
    orphan_bank_id = get_handle(BankRef(bank_ref="orphan"))

    for operation, child_id in (
        (api.removeIndirectAddressRefBankRef, field_bank_id),
        (api.removeIndirectDataRefBankRef, field_bank_id),
        (api.removeIndirectAddressRefRegisterFileRef, field_file_id),
        (api.removeIndirectDataRefRegisterFileRef, field_file_id),
        (api.removeIndirectAddressRefBankRef, orphan_bank_id),
    ):
        with pytest.raises(TgiError) as error:
            operation(child_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    root = _parsed_component()
    first = root.indirect_interfaces.indirect_interface[0]
    source_owner, target_owner = first.indirect_address_ref, first.indirect_data_ref
    moved = source_owner.bank_ref.pop()
    target_owner.bank_ref.append(moved)
    moved_id = get_handle(moved)
    with pytest.raises(TgiError) as mislinked:
        api.removeIndirectAddressRefBankRef(moved_id)
    assert mislinked.value.fault_code == TgiFaultCode.INVALID_ID
    target_owner.bank_ref.remove(moved)
    source_owner.bank_ref.append(moved)
    assert api.removeIndirectAddressRefBankRef(moved_id) is True
    with pytest.raises(TgiError) as stale:
        api.removeIndirectAddressRefBankRef(moved_id)
    assert stale.value.fault_code == TgiFaultCode.INVALID_ID


def test_shared_slice_remover_rejects_bank_reference_owned_by_another_field() -> None:
    member = BankRef(bank_ref="member")
    foreign = BankRef(bank_ref="foreign")
    owner = FieldMap.FieldSlice(
        bank_ref=(member,),
        address_block_ref=AddressBlockRef(address_block_ref="block"),
        register_ref=RegisterRef(register_ref="register"),
        field_ref=FieldRef(field_ref="field"),
    )
    owner.field_ref = foreign
    register_parent(foreign, owner, ("field_ref",), "single")
    foreign_id = get_handle(foreign)
    bank_tuple = owner.bank_ref

    with pytest.raises(TgiError) as error:
        slice_api.removeFieldSliceBankRef(foreign_id)

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert owner.bank_ref is bank_tuple
    assert owner.bank_ref == (member,)
    assert owner.field_ref is foreign
    assert resolve_handle(foreign_id) is foreign


@pytest.mark.parametrize(
    ("remove_name", "ref_attr", "collection_attr", "child", "value_attr"),
    [
        ("removeIndirectAddressRefBankRef", "indirect_address_ref", "bank_ref", BankRef(bank_ref="valid"), "bank_ref"),
        (
            "removeIndirectAddressRefRegisterFileRef",
            "indirect_address_ref",
            "register_file_ref",
            RegisterFileRef(register_file_ref="valid"),
            "register_file_ref",
        ),
        ("removeIndirectDataRefBankRef", "indirect_data_ref", "bank_ref", BankRef(bank_ref="valid"), "bank_ref"),
        (
            "removeIndirectDataRefRegisterFileRef",
            "indirect_data_ref",
            "register_file_ref",
            RegisterFileRef(register_file_ref="valid"),
            "register_file_ref",
        ),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
def test_removers_accept_invalid_lexical_names_for_repair_but_reject_non_string_sources(
    remove_name: str, ref_attr: str, collection_attr: str, child: BankRef | RegisterFileRef, value_attr: str
) -> None:
    root = _parsed_component()
    owner = getattr(root.indirect_interfaces.indirect_interface[0], ref_attr)
    setattr(child, value_attr, "bad name")
    setattr(owner, collection_attr, [child])
    child_id = get_handle(child)

    assert getattr(api, remove_name)(child_id) is True
    assert getattr(owner, collection_attr) == []
    assert resolve_handle(child_id) is None

    malformed = BankRef(bank_ref=None) if isinstance(child, BankRef) else RegisterFileRef(register_file_ref=None)
    setattr(owner, collection_attr, [malformed])
    malformed_id = get_handle(malformed)
    with pytest.raises(TgiError) as error:
        getattr(api, remove_name)(malformed_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, collection_attr) == [malformed]
