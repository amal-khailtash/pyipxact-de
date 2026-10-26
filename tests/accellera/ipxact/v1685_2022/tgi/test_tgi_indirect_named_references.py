"""Indirect-interface address-block and field reference TGI contracts."""

import inspect
from collections.abc import Iterator

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
    AddressBlockRef,
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
    Value,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_GETTERS = (
    "getIndirectAddressRefAddressBlockRefByName",
    "getIndirectAddressRefAddressBlockRefID",
    "getIndirectAddressRefFieldRefByName",
    "getIndirectAddressRefFieldRefID",
    "getIndirectDataRefAddressBlockRefByName",
    "getIndirectDataRefAddressBlockRefID",
    "getIndirectDataRefFieldRefByName",
    "getIndirectDataRefFieldRefID",
)
_REMOVERS = (
    "removeIndirectAddressRefAddressBlockRef",
    "removeIndirectDataRefAddressBlockRef",
)
_API_FUNCTIONS = (*_GETTERS, *_REMOVERS)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _indirect_interface(name: str, suffix: str) -> IndirectInterface:
    address_block_indices = Indices(index=[Index(value="2", id=f"{suffix}_block_index")])
    data_block_indices = Indices(index=[Index(value="3", id=f"{suffix}_data_index")])
    return IndirectInterface(
        name=name,
        indirect_address_ref=IndirectAddressRef(
            address_block_ref=AddressBlockRef(
                address_block_ref=f" \tδ_{suffix}_address_block\r\n", indices=address_block_indices
            ),
            field_ref=FieldRef(field_ref=f" \tδ_{suffix}_address_field\r\n"),
        ),
        indirect_data_ref=IndirectDataRef(
            address_block_ref=AddressBlockRef(
                address_block_ref=f" \tδ_{suffix}_data_block\r\n", indices=data_block_indices
            ),
            field_ref=FieldRef(field_ref=f" \tδ_{suffix}_data_field\r\n"),
        ),
        memory_map_ref_or_transparent_bridge=[f"map_{suffix}"],
    )


def _component(*, name: str = "indirect_refs") -> Component:
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
        "getIndirectAddressRefAddressBlockRefByName": (
            "indirectAddressRefID",
            str | None,
            "F.7.53.1",
        ),
        "getIndirectAddressRefAddressBlockRefID": (
            "indirectAddressRefID",
            str | None,
            "F.7.53.2",
        ),
        "getIndirectAddressRefFieldRefByName": (
            "indirectAddressRefID",
            str | None,
            "F.7.53.9",
        ),
        "getIndirectAddressRefFieldRefID": (
            "indirectAddressRefID",
            str | None,
            "F.7.53.10",
        ),
        "getIndirectDataRefAddressBlockRefByName": (
            "indirectDataRefID",
            str | None,
            "F.7.53.20",
        ),
        "getIndirectDataRefAddressBlockRefID": (
            "indirectDataRefID",
            str | None,
            "F.7.53.21",
        ),
        "getIndirectDataRefFieldRefByName": (
            "indirectDataRefID",
            str | None,
            "F.7.53.28",
        ),
        "getIndirectDataRefFieldRefID": (
            "indirectDataRefID",
            str | None,
            "F.7.53.29",
        ),
        "removeIndirectAddressRefAddressBlockRef": (
            "indirectAddressRefID",
            bool,
            "F.7.54.8",
        ),
        "removeIndirectDataRefAddressBlockRef": (
            "indirectDataRefID",
            bool,
            "F.7.54.16",
        ),
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


def test_address_and_data_getters_return_normalized_names_and_owned_wrapper_ids() -> None:
    root = _parsed_component()
    address_ref, data_ref = (
        root.indirect_interfaces.indirect_interface[0].indirect_address_ref,
        root.indirect_interfaces.indirect_interface[0].indirect_data_ref,
    )
    address_ref_id, data_ref_id = get_handle(address_ref), get_handle(data_ref)
    address_block, data_block = address_ref.address_block_ref, data_ref.address_block_ref
    address_field, data_field = address_ref.field_ref, data_ref.field_ref
    assert address_block is not None and data_block is not None
    address_block_id, data_block_id = get_handle(address_block), get_handle(data_block)
    address_field_id, data_field_id = get_handle(address_field), get_handle(data_field)

    assert api.getIndirectAddressRefAddressBlockRefByName(address_ref_id) == "δ_a_address_block"
    assert api.getIndirectAddressRefAddressBlockRefID(address_ref_id) == address_block_id
    assert api.getIndirectAddressRefFieldRefByName(address_ref_id) == "δ_a_address_field"
    assert api.getIndirectAddressRefFieldRefID(address_ref_id) == address_field_id
    assert api.getIndirectDataRefAddressBlockRefByName(data_ref_id) == "δ_a_data_block"
    assert api.getIndirectDataRefAddressBlockRefID(data_ref_id) == data_block_id
    assert api.getIndirectDataRefFieldRefByName(data_ref_id) == "δ_a_data_field"
    assert api.getIndirectDataRefFieldRefID(data_ref_id) == data_field_id

    for child, handle, owner, path in (
        (address_block, address_block_id, address_ref, ("address_block_ref",)),
        (address_field, address_field_id, address_ref, ("field_ref",)),
        (data_block, data_block_id, data_ref, ("address_block_ref",)),
        (data_field, data_field_id, data_ref, ("field_ref",)),
    ):
        assert resolve_handle(handle) is child
        info = get_parent_info(handle)
        assert info is not None
        assert info.parent_handle == get_handle(owner)
        assert info.path == path
        assert info.container == "single"
    assert address_block.address_block_ref == " \tδ_a_address_block\r\n"
    assert address_field.field_ref == " \tδ_a_address_field\r\n"
    assert data_block.address_block_ref == " \tδ_a_data_block\r\n"
    assert data_field.field_ref == " \tδ_a_data_field\r\n"
    _xml_round_trip(root)


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr"),
    [
        ("getIndirectAddressRefAddressBlockRefByName", "address", "address_block_ref"),
        ("getIndirectAddressRefAddressBlockRefID", "address", "address_block_ref"),
        ("getIndirectAddressRefFieldRefByName", "address", "field_ref"),
        ("getIndirectAddressRefFieldRefID", "address", "field_ref"),
        ("getIndirectDataRefAddressBlockRefByName", "data", "address_block_ref"),
        ("getIndirectDataRefAddressBlockRefID", "data", "address_block_ref"),
        ("getIndirectDataRefFieldRefByName", "data", "field_ref"),
        ("getIndirectDataRefFieldRefID", "data", "field_ref"),
    ],
    ids=(
        "address-block-name-address",
        "address-block-id-address",
        "field-name-address",
        "field-id-address",
        "address-block-name-data",
        "address-block-id-data",
        "field-name-data",
        "field-id-data",
    ),
)
def test_indirect_getters_return_none_for_missing_wrappers(getter_name: str, owner_kind: str, target_attr: str) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    setattr(owner, target_attr, None)

    assert getattr(api, getter_name)(get_handle(owner)) is None


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr"),
    [
        ("getIndirectAddressRefAddressBlockRefByName", "address", "address_block_ref"),
        ("getIndirectAddressRefAddressBlockRefID", "address", "address_block_ref"),
        ("getIndirectAddressRefFieldRefByName", "address", "field_ref"),
        ("getIndirectAddressRefFieldRefID", "address", "field_ref"),
        ("getIndirectDataRefAddressBlockRefByName", "data", "address_block_ref"),
        ("getIndirectDataRefAddressBlockRefID", "data", "address_block_ref"),
        ("getIndirectDataRefFieldRefByName", "data", "field_ref"),
        ("getIndirectDataRefFieldRefID", "data", "field_ref"),
    ],
    ids=(
        "address-block-name-address",
        "address-block-id-address",
        "field-name-address",
        "field-id-address",
        "address-block-name-data",
        "address-block-id-data",
        "field-name-data",
        "field-id-data",
    ),
)
def test_indirect_getters_reject_malformed_wrapper_types_atomically(
    getter_name: str, owner_kind: str, target_attr: str
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    original = getattr(owner, target_attr)
    setattr(owner, target_attr, object())

    with pytest.raises(TgiError) as error:
        getattr(api, getter_name)(get_handle(owner))

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, target_attr) is not original
    setattr(owner, target_attr, original)
    _xml_round_trip(root)


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr"),
    [
        ("getIndirectAddressRefAddressBlockRefByName", "address", "address_block_ref"),
        ("getIndirectAddressRefFieldRefByName", "address", "field_ref"),
        ("getIndirectDataRefAddressBlockRefByName", "data", "address_block_ref"),
        ("getIndirectDataRefFieldRefByName", "data", "field_ref"),
    ],
    ids=("address-block-address", "field-address", "address-block-data", "field-data"),
)
def test_by_name_getters_reject_invalid_stored_xs_name_without_mutating_it(
    getter_name: str, owner_kind: str, target_attr: str
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    wrapper = getattr(owner, target_attr)
    value_attr = "address_block_ref" if target_attr == "address_block_ref" else "field_ref"
    setattr(wrapper, value_attr, "bad name")

    with pytest.raises(TgiError) as error:
        getattr(api, getter_name)(get_handle(owner))

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(wrapper, value_attr) == "bad name"


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr"),
    [
        ("getIndirectAddressRefAddressBlockRefByName", "address", "address_block_ref"),
        ("getIndirectAddressRefFieldRefByName", "address", "field_ref"),
        ("getIndirectDataRefAddressBlockRefByName", "data", "address_block_ref"),
        ("getIndirectDataRefFieldRefByName", "data", "field_ref"),
    ],
    ids=("address-block-address", "field-address", "address-block-data", "field-data"),
)
def test_by_name_getters_reject_non_string_reference_content(
    getter_name: str, owner_kind: str, target_attr: str
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    wrapper = getattr(owner, target_attr)
    value_attr = "address_block_ref" if target_attr == "address_block_ref" else "field_ref"
    value = Value(value="not a reference node")
    setattr(wrapper, value_attr, value)

    with pytest.raises(TgiError) as error:
        getattr(api, getter_name)(get_handle(owner))

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(wrapper, value_attr) is value


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr"),
    [
        ("getIndirectAddressRefAddressBlockRefID", "address", "address_block_ref"),
        ("getIndirectAddressRefFieldRefID", "address", "field_ref"),
        ("getIndirectDataRefAddressBlockRefID", "data", "address_block_ref"),
        ("getIndirectDataRefFieldRefID", "data", "field_ref"),
    ],
    ids=("address-block-address", "field-address", "address-block-data", "field-data"),
)
def test_id_getters_preserve_handle_access_when_reference_name_is_malformed(
    getter_name: str, owner_kind: str, target_attr: str
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    wrapper = getattr(owner, target_attr)
    value_attr = "address_block_ref" if target_attr == "address_block_ref" else "field_ref"
    setattr(wrapper, value_attr, "bad name")

    assert getattr(api, getter_name)(get_handle(owner)) == get_handle(wrapper)
    assert getattr(wrapper, value_attr) == "bad name"


@pytest.mark.parametrize(
    ("getter_name", "remove_name"),
    [(getter_name, remove_name) for getter_name in _GETTERS for remove_name in _REMOVERS],
    ids=tuple(
        f"{getter_name.removeprefix('get')}-{remove_name.removeprefix('remove')}"
        for getter_name in _GETTERS
        for remove_name in _REMOVERS
    ),
)
def test_getters_and_removers_reject_unknown_and_wrong_type_handles(getter_name: str, remove_name: str) -> None:
    root = _parsed_component()
    component_id = get_handle(root)
    wrong_type_id = get_handle(root.indirect_interfaces.indirect_interface[0])

    for handle in ("unknown-handle", component_id, wrong_type_id):
        with pytest.raises(TgiError) as error:
            getattr(api, getter_name)(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as remove_error:
            getattr(api, remove_name)(handle)
        assert remove_error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    ("remove_name", "ref_attr"),
    (
        ("removeIndirectAddressRefAddressBlockRef", "indirect_address_ref"),
        ("removeIndirectDataRefAddressBlockRef", "indirect_data_ref"),
    ),
    ids=("remove-address-block-address", "remove-address-block-data"),
)
def test_parsed_removal_without_prior_getter_invalidates_wrapper_subtree_and_preserves_owner_siblings(
    remove_name: str, ref_attr: str
) -> None:
    root = _parsed_component()
    first, second = root.indirect_interfaces.indirect_interface
    interface_handle = get_handle(first)
    owner = getattr(first, ref_attr)
    other_owner = second.indirect_address_ref if ref_attr == "indirect_data_ref" else second.indirect_data_ref
    target = owner.address_block_ref
    assert target is not None and target.indices is not None
    owner_handle = get_handle(owner)
    target_handle = get_handle(target)
    indices_handle = get_handle(target.indices)
    index_handles = [get_handle(index) for index in target.indices.index]
    retained_field = owner.field_ref
    retained_field_handle = get_handle(retained_field)
    other_block = other_owner.address_block_ref
    assert other_block is not None
    other_block_handle = get_handle(other_block)
    second_handle = get_handle(second)

    assert getattr(api, remove_name)(owner_handle) is True

    assert owner.address_block_ref is None
    assert owner.field_ref is retained_field
    assert resolve_handle(target_handle) is None
    assert resolve_handle(indices_handle) is None
    assert all(resolve_handle(index_handle) is None for index_handle in index_handles)
    assert resolve_handle(retained_field_handle) is retained_field
    assert resolve_handle(other_block_handle) is other_block
    assert resolve_handle(interface_handle) is first
    assert resolve_handle(second_handle) is second
    getter_name = (
        "getIndirectAddressRefAddressBlockRefID"
        if ref_attr == "indirect_address_ref"
        else "getIndirectDataRefAddressBlockRefID"
    )
    assert getattr(api, getter_name)(owner_handle) is None
    assert root.indirect_interfaces.indirect_interface == [first, second]
    _xml_round_trip(root)


@pytest.mark.parametrize(
    ("remove_name", "ref_attr"),
    (
        ("removeIndirectAddressRefAddressBlockRef", "indirect_address_ref"),
        ("removeIndirectDataRefAddressBlockRef", "indirect_data_ref"),
    ),
    ids=("address-missing-wrapper", "data-missing-wrapper"),
)
def test_removing_an_absent_optional_address_block_wrapper_returns_false(remove_name: str, ref_attr: str) -> None:
    root = _component()
    owner = getattr(root.indirect_interfaces.indirect_interface[0], ref_attr)
    owner.address_block_ref = None

    assert getattr(api, remove_name)(get_handle(owner)) is False
    assert owner.address_block_ref is None


@pytest.mark.parametrize(
    ("remove_name", "owner_kind"),
    (
        ("removeIndirectAddressRefAddressBlockRef", "address"),
        ("removeIndirectDataRefAddressBlockRef", "data"),
    ),
    ids=("address-orphan-owner", "data-orphan-owner"),
)
def test_removers_accept_standalone_typed_owners(remove_name: str, owner_kind: str) -> None:
    owner_type = IndirectAddressRef if owner_kind == "address" else IndirectDataRef
    owner = owner_type(
        address_block_ref=AddressBlockRef(address_block_ref="block"),
        field_ref=FieldRef(field_ref="field"),
    )
    owner_handle = get_handle(owner)
    wrapper_handle = get_handle(owner.address_block_ref)

    assert getattr(api, remove_name)(owner_handle) is True
    assert owner.address_block_ref is None
    assert resolve_handle(wrapper_handle) is None
    assert resolve_handle(owner_handle) is owner
