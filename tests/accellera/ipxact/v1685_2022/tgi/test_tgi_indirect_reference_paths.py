"""Ordered bank and register-file paths on indirect interfaces."""

import inspect
from collections.abc import Iterator
from pathlib import Path

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import indirect_interface as api
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
    AlternateRegisterRef,
    BankRef,
    Component,
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
_TGI_WSDL = Path("submodules/accellera-schemas/IPXACT/1685-2022/TGI/TGI.wsdl")
_GETTERS = (
    "getIndirectAddressRefBankRefByNames",
    "getIndirectAddressRefBankRefIDs",
    "getIndirectAddressRefRegisterFileRefByNames",
    "getIndirectAddressRefRegisterFileRefIDs",
    "getIndirectDataRefBankRefByNames",
    "getIndirectDataRefBankRefIDs",
    "getIndirectDataRefRegisterFileRefByNames",
    "getIndirectDataRefRegisterFileRefIDs",
)
_REMOVERS = (
    "removeIndirectAddressRefAlternateRegisterRef",
    "removeIndirectDataRefAlternateRegisterRef",
)
_API_FUNCTIONS = (*_GETTERS, *_REMOVERS)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _address_ref(suffix: str) -> IndirectAddressRef:
    return IndirectAddressRef(
        bank_ref=[
            BankRef(bank_ref=f" \tδ_{suffix}_bank\r\n", id=f"{suffix}_bank_1"),
            BankRef(bank_ref=f"\tδ_{suffix}_bank ", id=f"{suffix}_bank_2"),
            BankRef(bank_ref=f"last_{suffix}_bank", id=f"{suffix}_bank_3"),
        ],
        register_file_ref=[
            RegisterFileRef(
                register_file_ref=f" \tδ_{suffix}_register_file\r\n",
                indices=Indices(index=[Index(value="2", id=f"{suffix}_register_file_index_0")]),
                id=f"{suffix}_register_file_1",
            ),
            RegisterFileRef(
                register_file_ref=f"last_{suffix}_register_file",
                indices=Indices(index=[Index(value="5", id=f"{suffix}_register_file_index_1")]),
                id=f"{suffix}_register_file_2",
            ),
        ],
        register_ref=RegisterRef(
            register_ref=f"register_{suffix}",
            indices=Indices(index=[Index(value="7", id=f"{suffix}_register_index")]),
        ),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref=f"alternate_{suffix}"),
        field_ref=FieldRef(field_ref=f"field_{suffix}"),
    )


def _data_ref(suffix: str) -> IndirectDataRef:
    return IndirectDataRef(
        bank_ref=[BankRef(bank_ref=f" \tδ_{suffix}_data_bank\r\n", id=f"{suffix}_data_bank")],
        register_file_ref=[
            RegisterFileRef(
                register_file_ref=f" \tδ_{suffix}_data_register_file\r\n",
                indices=Indices(index=[Index(value="3", id=f"{suffix}_data_index")]),
                id=f"{suffix}_data_register_file",
            )
        ],
        register_ref=RegisterRef(
            register_ref=f"data_register_{suffix}",
            indices=Indices(index=[Index(value="9", id=f"{suffix}_data_register_index")]),
        ),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref=f"data_alternate_{suffix}"),
        field_ref=FieldRef(field_ref=f"data_field_{suffix}"),
    )


def _interface(name: str, suffix: str) -> IndirectInterface:
    return IndirectInterface(
        name=name,
        indirect_address_ref=_address_ref(suffix),
        indirect_data_ref=_data_ref(suffix),
        memory_map_ref_or_transparent_bridge=[f"map_{suffix}"],
    )


def _component(*, name: str = "indirect_reference_paths") -> Component:
    return Component(
        vendor="acme",
        library="devices",
        name=name,
        version="1.0",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map_a"), MemoryMapType(name="map_b")]),
        indirect_interfaces=IndirectInterfaces(
            indirect_interface=[_interface("indirect_a", "a"), _interface("indirect_b", "b")]
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


def test_public_exports_native_signatures_annex_f_sections_and_wsdl_string_arrays() -> None:
    expected = {
        "getIndirectAddressRefBankRefByNames": ("indirectAddressRefID", list[str], "F.7.53.7"),
        "getIndirectAddressRefBankRefIDs": ("indirectAddressRefID", list[str], "F.7.53.8"),
        "getIndirectAddressRefRegisterFileRefByNames": ("indirectAddressRefID", list[str], "F.7.53.16"),
        "getIndirectAddressRefRegisterFileRefIDs": ("indirectAddressRefID", list[str], "F.7.53.17"),
        "getIndirectDataRefBankRefByNames": ("indirectDataRefID", list[str], "F.7.53.26"),
        "getIndirectDataRefBankRefIDs": ("indirectDataRefID", list[str], "F.7.53.27"),
        "getIndirectDataRefRegisterFileRefByNames": ("indirectDataRefID", list[str], "F.7.53.35"),
        "getIndirectDataRefRegisterFileRefIDs": ("indirectDataRefID", list[str], "F.7.53.36"),
        "removeIndirectAddressRefAlternateRegisterRef": ("indirectAddressRefID", bool, "F.7.54.10"),
        "removeIndirectDataRefAlternateRegisterRef": ("indirectDataRefID", bool, "F.7.54.18"),
    }

    assert set(_API_FUNCTIONS) == set(expected)
    assert set(_API_FUNCTIONS) <= set(api.__all__)
    assert set(_API_FUNCTIONS) <= set(tgi.__all__)
    for name, (parameter_name, return_type, section) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == (parameter_name,)
        parameter = next(iter(signature.parameters.values()))
        assert parameter.annotation is str
        assert not isinstance(parameter.annotation, str)
        assert parameter.default is inspect.Signature.empty
        assert signature.return_annotation == return_type
        assert f"Section: {section}." in inspect.getdoc(function)

    wsdl = etree.parse(str(_TGI_WSDL))
    namespaces = {"wsdl": "http://schemas.xmlsoap.org/wsdl/"}
    response = wsdl.find("wsdl:message[@name='getIndirectDataRefBankRefByNamesResp']/wsdl:part", namespaces)
    assert response is not None
    assert response.get("type", "").split(":")[-1].lower() == "soapstringarraytype"


def test_ordered_duplicate_names_and_ids_preserve_tuple_storage_and_registerfile_index_ownership() -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    address_ref, data_ref = interface.indirect_address_ref, interface.indirect_data_ref
    address_banks = tuple(address_ref.bank_ref)
    address_files = tuple(address_ref.register_file_ref)
    address_ref.bank_ref = address_banks
    address_ref.register_file_ref = address_files
    address_ref_id, data_ref_id = get_handle(address_ref), get_handle(data_ref)

    bank_names = api.getIndirectAddressRefBankRefByNames(address_ref_id)
    bank_ids = api.getIndirectAddressRefBankRefIDs(address_ref_id)
    file_names = api.getIndirectAddressRefRegisterFileRefByNames(address_ref_id)
    file_ids = api.getIndirectAddressRefRegisterFileRefIDs(address_ref_id)
    assert bank_names == ["δ_a_bank", "δ_a_bank", "last_a_bank"]
    assert bank_ids == [get_handle(child) for child in address_banks]
    assert file_names == ["δ_a_register_file", "last_a_register_file"]
    assert file_ids == [get_handle(child) for child in address_files]
    assert address_ref.bank_ref is address_banks
    assert address_ref.register_file_ref is address_files
    assert api.getIndirectDataRefBankRefByNames(data_ref_id) == ["δ_a_data_bank"]
    assert api.getIndirectDataRefBankRefIDs(data_ref_id) == [get_handle(data_ref.bank_ref[0])]
    assert api.getIndirectDataRefRegisterFileRefByNames(data_ref_id) == ["δ_a_data_register_file"]
    assert api.getIndirectDataRefRegisterFileRefIDs(data_ref_id) == [get_handle(data_ref.register_file_ref[0])]

    for child, child_id, owner, path in (
        (address_banks[0], bank_ids[0], address_ref, ("bank_ref",)),
        (address_files[0], file_ids[0], address_ref, ("register_file_ref",)),
    ):
        assert resolve_handle(child_id) is child
        info = get_parent_info(child_id)
        assert info is not None
        assert info.parent_handle == get_handle(owner)
        assert info.path == path
        assert info.container == "list"
    register_file = address_files[0]
    assert register_file.indices is not None
    index = register_file.indices.index[0]
    index_info = get_parent_info(get_handle(index))
    assert index_info is not None
    assert index_info.parent_handle == get_handle(register_file.indices)
    assert index_info.path == ("index",)
    assert index_info.container == "list"
    indices_info = get_parent_info(get_handle(register_file.indices))
    assert indices_info is not None
    assert indices_info.parent_handle == get_handle(register_file)
    assert indices_info.path == ("indices",)
    assert indices_info.container == "single"
    _xml_round_trip(root)


def test_empty_repeated_reference_getters_return_empty_lists_for_standalone_owners() -> None:
    address_ref = IndirectAddressRef(field_ref=FieldRef(field_ref="address"))
    data_ref = IndirectDataRef(field_ref=FieldRef(field_ref="data"))

    assert api.getIndirectAddressRefBankRefByNames(get_handle(address_ref)) == []
    assert api.getIndirectAddressRefBankRefIDs(get_handle(address_ref)) == []
    assert api.getIndirectAddressRefRegisterFileRefByNames(get_handle(address_ref)) == []
    assert api.getIndirectAddressRefRegisterFileRefIDs(get_handle(address_ref)) == []
    assert api.getIndirectDataRefBankRefByNames(get_handle(data_ref)) == []
    assert api.getIndirectDataRefBankRefIDs(get_handle(data_ref)) == []
    assert api.getIndirectDataRefRegisterFileRefByNames(get_handle(data_ref)) == []
    assert api.getIndirectDataRefRegisterFileRefIDs(get_handle(data_ref)) == []


@pytest.mark.parametrize(
    ("owner_kind", "collection_attr", "names_getter", "ids_getter", "model_type", "value_attr"),
    [
        (
            "address",
            "bank_ref",
            "getIndirectAddressRefBankRefByNames",
            "getIndirectAddressRefBankRefIDs",
            BankRef,
            "bank_ref",
        ),
        (
            "address",
            "register_file_ref",
            "getIndirectAddressRefRegisterFileRefByNames",
            "getIndirectAddressRefRegisterFileRefIDs",
            RegisterFileRef,
            "register_file_ref",
        ),
        ("data", "bank_ref", "getIndirectDataRefBankRefByNames", "getIndirectDataRefBankRefIDs", BankRef, "bank_ref"),
        (
            "data",
            "register_file_ref",
            "getIndirectDataRefRegisterFileRefByNames",
            "getIndirectDataRefRegisterFileRefIDs",
            RegisterFileRef,
            "register_file_ref",
        ),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
@pytest.mark.parametrize("bad_collection", [object(), [object()]], ids=("not-a-sequence", "wrong-child"))
def test_list_getters_reject_malformed_reference_collections(
    owner_kind: str,
    collection_attr: str,
    names_getter: str,
    ids_getter: str,
    model_type: type[BankRef] | type[RegisterFileRef],
    value_attr: str,
    bad_collection: object,
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    setattr(owner, collection_attr, bad_collection)

    for getter_name in (names_getter, ids_getter):
        with pytest.raises(TgiError) as error:
            getattr(api, getter_name)(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, collection_attr) is bad_collection
    assert model_type is (BankRef if value_attr == "bank_ref" else RegisterFileRef)


@pytest.mark.parametrize(
    ("owner_kind", "collection_attr", "names_getter", "ids_getter", "child", "value_attr"),
    [
        (
            "address",
            "bank_ref",
            "getIndirectAddressRefBankRefByNames",
            "getIndirectAddressRefBankRefIDs",
            BankRef(bank_ref="good"),
            "bank_ref",
        ),
        (
            "address",
            "register_file_ref",
            "getIndirectAddressRefRegisterFileRefByNames",
            "getIndirectAddressRefRegisterFileRefIDs",
            RegisterFileRef(register_file_ref="good"),
            "register_file_ref",
        ),
        (
            "data",
            "bank_ref",
            "getIndirectDataRefBankRefByNames",
            "getIndirectDataRefBankRefIDs",
            BankRef(bank_ref="good"),
            "bank_ref",
        ),
        (
            "data",
            "register_file_ref",
            "getIndirectDataRefRegisterFileRefByNames",
            "getIndirectDataRefRegisterFileRefIDs",
            RegisterFileRef(register_file_ref="good"),
            "register_file_ref",
        ),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
@pytest.mark.parametrize(
    "bad_value",
    [Value(value="not a reference"), True, 7, None],
    ids=("value-wrapper", "boolean", "integer", "missing-attribute"),
)
def test_list_getters_reject_non_string_source_values_atomically(
    owner_kind: str,
    collection_attr: str,
    names_getter: str,
    ids_getter: str,
    child: BankRef | RegisterFileRef,
    value_attr: str,
    bad_value: object,
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    original = [child, getattr(owner, collection_attr)[0]]
    setattr(child, value_attr, bad_value)
    setattr(owner, collection_attr, original)

    for getter_name in (names_getter, ids_getter):
        with pytest.raises(TgiError) as error:
            getattr(api, getter_name)(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, collection_attr) is original
    assert original[0] is child


@pytest.mark.parametrize(
    ("owner_kind", "collection_attr", "names_getter", "ids_getter", "child", "value_attr"),
    [
        (
            "address",
            "bank_ref",
            "getIndirectAddressRefBankRefByNames",
            "getIndirectAddressRefBankRefIDs",
            BankRef(bank_ref="valid"),
            "bank_ref",
        ),
        (
            "address",
            "register_file_ref",
            "getIndirectAddressRefRegisterFileRefByNames",
            "getIndirectAddressRefRegisterFileRefIDs",
            RegisterFileRef(register_file_ref="valid"),
            "register_file_ref",
        ),
        (
            "data",
            "bank_ref",
            "getIndirectDataRefBankRefByNames",
            "getIndirectDataRefBankRefIDs",
            BankRef(bank_ref="valid"),
            "bank_ref",
        ),
        (
            "data",
            "register_file_ref",
            "getIndirectDataRefRegisterFileRefByNames",
            "getIndirectDataRefRegisterFileRefIDs",
            RegisterFileRef(register_file_ref="valid"),
            "register_file_ref",
        ),
    ],
    ids=("address-bank", "address-register-file", "data-bank", "data-register-file"),
)
def test_id_getters_validate_collection_source_but_keep_invalid_name_handles_repairable(
    owner_kind: str,
    collection_attr: str,
    names_getter: str,
    ids_getter: str,
    child: BankRef | RegisterFileRef,
    value_attr: str,
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    collection = getattr(owner, collection_attr)
    child_id = get_handle(child)
    setattr(child, value_attr, "bad name")
    setattr(owner, collection_attr, [child])

    with pytest.raises(TgiError) as name_error:
        getattr(api, names_getter)(get_handle(owner))
    assert name_error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(api, ids_getter)(get_handle(owner)) == [child_id]
    assert getattr(owner, collection_attr) == [child]
    assert collection is not getattr(owner, collection_attr)


def test_getters_and_removers_reject_unknown_wrong_type_and_stale_child_handles() -> None:
    root = _parsed_component()
    component_id = get_handle(root)
    first = root.indirect_interfaces.indirect_interface[0]
    address_ref, data_ref = first.indirect_address_ref, first.indirect_data_ref
    address_id, data_id = get_handle(address_ref), get_handle(data_ref)
    interface_id = get_handle(first)
    stale_address_id = get_handle(address_ref.alternate_register_ref)
    stale_data_id = get_handle(data_ref.alternate_register_ref)

    assert api.removeIndirectAddressRefAlternateRegisterRef(address_id) is True
    assert api.removeIndirectDataRefAlternateRegisterRef(data_id) is True
    for getter_name in _GETTERS:
        with pytest.raises(TgiError) as error:
            getattr(api, getter_name)("unknown-handle")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        for wrong_handle in (component_id, interface_id, stale_address_id, stale_data_id):
            with pytest.raises(TgiError) as wrong_error:
                getattr(api, getter_name)(wrong_handle)
            assert wrong_error.value.fault_code == TgiFaultCode.INVALID_ID
    for remove_name in _REMOVERS:
        with pytest.raises(TgiError) as error:
            getattr(api, remove_name)("unknown-handle")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        for wrong_handle in (component_id, interface_id, stale_address_id, stale_data_id):
            with pytest.raises(TgiError) as wrong_error:
                getattr(api, remove_name)(wrong_handle)
            assert wrong_error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    ("remove_name", "ref_attr", "get_id_name", "bank_names_name", "file_names_name"),
    (
        (
            "removeIndirectAddressRefAlternateRegisterRef",
            "indirect_address_ref",
            "getIndirectAddressRefAlternateRegisterRefID",
            "getIndirectAddressRefBankRefByNames",
            "getIndirectAddressRefRegisterFileRefByNames",
        ),
        (
            "removeIndirectDataRefAlternateRegisterRef",
            "indirect_data_ref",
            "getIndirectDataRefAlternateRegisterRefID",
            "getIndirectDataRefBankRefByNames",
            "getIndirectDataRefRegisterFileRefByNames",
        ),
    ),
    ids=("remove-address-alternate", "remove-data-alternate"),
)
def test_parsed_alternate_removal_before_getters_invalidates_only_target_and_preserves_other_paths(
    remove_name: str, ref_attr: str, get_id_name: str, bank_names_name: str, file_names_name: str
) -> None:
    root = _parsed_component()
    first, second = root.indirect_interfaces.indirect_interface
    interface_id = get_handle(first)
    owner = getattr(first, ref_attr)
    peer_owner = second.indirect_address_ref if ref_attr == "indirect_data_ref" else second.indirect_data_ref
    alternate = owner.alternate_register_ref
    register_ref = owner.register_ref
    field_ref = owner.field_ref
    assert alternate is not None and register_ref is not None
    alternate_id = get_handle(alternate)
    register_id = get_handle(register_ref)
    field_id = get_handle(field_ref)
    index_ids = [get_handle(index) for index in register_ref.indices.index]
    peer_alternate = peer_owner.alternate_register_ref
    assert peer_alternate is not None
    peer_alternate_id = get_handle(peer_alternate)
    owner_id = get_handle(owner)

    assert getattr(api, remove_name)(owner_id) is True

    assert owner.alternate_register_ref is None
    assert owner.register_ref is register_ref
    assert owner.field_ref is field_ref
    assert resolve_handle(alternate_id) is None
    assert resolve_handle(register_id) is register_ref
    assert all(resolve_handle(index_id) is not None for index_id in index_ids)
    assert resolve_handle(field_id) is field_ref
    assert resolve_handle(peer_alternate_id) is peer_alternate
    assert resolve_handle(interface_id) is first
    assert getattr(api, get_id_name)(owner_id) is None
    assert getattr(api, bank_names_name)(owner_id)
    assert getattr(api, file_names_name)(owner_id)
    assert root.indirect_interfaces.indirect_interface == [first, second]
    _xml_round_trip(root)


@pytest.mark.parametrize(
    ("remove_name", "ref_attr"),
    (
        ("removeIndirectAddressRefAlternateRegisterRef", "indirect_address_ref"),
        ("removeIndirectDataRefAlternateRegisterRef", "indirect_data_ref"),
    ),
    ids=("address-no-alternate", "data-no-alternate"),
)
def test_removing_absent_alternate_register_wrapper_returns_false(remove_name: str, ref_attr: str) -> None:
    owner = getattr(_component().indirect_interfaces.indirect_interface[0], ref_attr)
    owner.alternate_register_ref = None

    assert getattr(api, remove_name)(get_handle(owner)) is False
    assert owner.alternate_register_ref is None


@pytest.mark.parametrize(
    ("remove_name", "owner_kind"),
    (
        ("removeIndirectAddressRefAlternateRegisterRef", "address"),
        ("removeIndirectDataRefAlternateRegisterRef", "data"),
    ),
    ids=("address-standalone-owner", "data-standalone-owner"),
)
def test_alternate_register_removers_accept_standalone_typed_owners(remove_name: str, owner_kind: str) -> None:
    owner_type = IndirectAddressRef if owner_kind == "address" else IndirectDataRef
    owner = owner_type(
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref="alt"),
        register_ref=RegisterRef(register_ref="reg", indices=Indices(index=[Index(value="0")])),
        field_ref=FieldRef(field_ref="field"),
    )
    owner_id = get_handle(owner)
    alternate_id = get_handle(owner.alternate_register_ref)

    assert getattr(api, remove_name)(owner_id) is True
    assert owner.alternate_register_ref is None
    assert resolve_handle(alternate_id) is None
    assert resolve_handle(owner_id) is owner
    assert owner.register_ref.register_ref == "reg"
    assert owner.field_ref.field_ref == "field"


@pytest.mark.parametrize("owner_kind", ["address", "data"], ids=("address-paths", "data-paths"))
def test_repeated_bank_and_register_file_paths_for_both_owners_preserve_full_arrays(owner_kind: str) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    prefix = "getIndirectAddressRef" if owner_kind == "address" else "getIndirectDataRef"
    sources = ("repeat", "repeat", "last")
    banks = tuple(BankRef(bank_ref=name) for name in sources)
    files = tuple(
        RegisterFileRef(
            register_file_ref=name,
            id=f"repeated_{owner_kind}_file_{index}",
            indices=Indices(index=[Index(value=str(index), id=f"repeated_{owner_kind}_index_{index}")]),
        )
        for index, name in enumerate(sources)
    )
    owner.bank_ref, owner.register_file_ref = banks, files
    owner_id = get_handle(owner)
    assert getattr(api, prefix + "BankRefByNames")(owner_id) == list(sources)
    assert getattr(api, prefix + "RegisterFileRefByNames")(owner_id) == list(sources)
    bank_ids = getattr(api, prefix + "BankRefIDs")(owner_id)
    file_ids = getattr(api, prefix + "RegisterFileRefIDs")(owner_id)
    assert bank_ids == [get_handle(child) for child in banks]
    assert file_ids == [get_handle(child) for child in files]
    assert len(set(bank_ids)) == len(sources)
    assert len(set(file_ids)) == len(sources)
    assert owner.bank_ref is banks
    assert owner.register_file_ref is files
    for index, child in enumerate(files):
        assert child.id == f"repeated_{owner_kind}_file_{index}"
        assert child.indices is not None
        assert child.indices.index[0].value == str(index)
        info = get_parent_info(get_handle(child.indices))
        assert info is not None
        assert info.parent_handle == get_handle(child)
    _xml_round_trip(root)
