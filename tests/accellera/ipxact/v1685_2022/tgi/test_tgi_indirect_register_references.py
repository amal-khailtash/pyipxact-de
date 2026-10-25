"""Indirect-interface register and alternate-register reference TGI contracts."""

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
    AlternateRegisterRef,
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
    RegisterRef,
    Value,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_GETTERS = (
    "getIndirectAddressRefRegisterRefByName",
    "getIndirectAddressRefRegisterRefID",
    "getIndirectAddressRefAlternateRegisterRefByName",
    "getIndirectAddressRefAlternateRegisterRefID",
    "getIndirectDataRefRegisterRefByName",
    "getIndirectDataRefRegisterRefID",
    "getIndirectDataRefAlternateRegisterRefByName",
    "getIndirectDataRefAlternateRegisterRefID",
)
_REMOVERS = (
    "removeIndirectAddressRefRegisterRef",
    "removeIndirectDataRefRegisterRef",
)
_API_FUNCTIONS = (*_GETTERS, *_REMOVERS)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _indirect_interface(name: str, suffix: str) -> IndirectInterface:
    return IndirectInterface(
        name=name,
        indirect_address_ref=IndirectAddressRef(
            register_ref=RegisterRef(
                register_ref=f" \tδ_{suffix}_address_register\r\n",
                indices=Indices(index=[Index(value="2", id=f"{suffix}_address_index")]),
            ),
            alternate_register_ref=AlternateRegisterRef(alternate_register_ref=f" \tδ_{suffix}_address_alternate\r\n"),
            field_ref=FieldRef(field_ref=f"field_{suffix}_address"),
        ),
        indirect_data_ref=IndirectDataRef(
            register_ref=RegisterRef(
                register_ref=f" \tδ_{suffix}_data_register\r\n",
                indices=Indices(index=[Index(value="3", id=f"{suffix}_data_index")]),
            ),
            alternate_register_ref=AlternateRegisterRef(alternate_register_ref=f" \tδ_{suffix}_data_alternate\r\n"),
            field_ref=FieldRef(field_ref=f"field_{suffix}_data"),
        ),
        memory_map_ref_or_transparent_bridge=[f"map_{suffix}"],
    )


def _component(*, name: str = "indirect_register_refs") -> Component:
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
        "getIndirectAddressRefRegisterRefByName": ("indirectAddressRefID", str | None, "F.7.53.18"),
        "getIndirectAddressRefRegisterRefID": ("indirectAddressRefID", str | None, "F.7.53.19"),
        "getIndirectAddressRefAlternateRegisterRefByName": ("indirectAddressRefID", str | None, "F.7.53.5"),
        "getIndirectAddressRefAlternateRegisterRefID": ("indirectAddressRefID", str | None, "F.7.53.6"),
        "getIndirectDataRefRegisterRefByName": ("indirectDataRefID", str | None, "F.7.53.37"),
        "getIndirectDataRefRegisterRefID": ("indirectDataRefID", str | None, "F.7.53.38"),
        "getIndirectDataRefAlternateRegisterRefByName": ("indirectDataRefID", str | None, "F.7.53.24"),
        "getIndirectDataRefAlternateRegisterRefID": ("indirectDataRefID", str | None, "F.7.53.25"),
        "removeIndirectAddressRefRegisterRef": ("indirectAddressRefID", bool, "F.7.54.15"),
        "removeIndirectDataRefRegisterRef": ("indirectDataRefID", bool, "F.7.54.23"),
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


def test_register_and_alternate_register_getters_return_normalized_names_and_typed_ids() -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    address_ref, data_ref = interface.indirect_address_ref, interface.indirect_data_ref
    address_register, data_register = address_ref.register_ref, data_ref.register_ref
    address_alternate, data_alternate = address_ref.alternate_register_ref, data_ref.alternate_register_ref
    assert address_register is not None and data_register is not None
    assert address_alternate is not None and data_alternate is not None
    address_ref_id, data_ref_id = get_handle(address_ref), get_handle(data_ref)
    address_register_id, data_register_id = get_handle(address_register), get_handle(data_register)
    address_alternate_id, data_alternate_id = get_handle(address_alternate), get_handle(data_alternate)

    assert api.getIndirectAddressRefRegisterRefByName(address_ref_id) == "δ_a_address_register"
    assert api.getIndirectAddressRefRegisterRefID(address_ref_id) == address_register_id
    assert api.getIndirectAddressRefAlternateRegisterRefByName(address_ref_id) == "δ_a_address_alternate"
    assert api.getIndirectAddressRefAlternateRegisterRefID(address_ref_id) == address_alternate_id
    assert api.getIndirectDataRefRegisterRefByName(data_ref_id) == "δ_a_data_register"
    assert api.getIndirectDataRefRegisterRefID(data_ref_id) == data_register_id
    assert api.getIndirectDataRefAlternateRegisterRefByName(data_ref_id) == "δ_a_data_alternate"
    assert api.getIndirectDataRefAlternateRegisterRefID(data_ref_id) == data_alternate_id

    for child, handle, owner, path in (
        (address_register, address_register_id, address_ref, ("register_ref",)),
        (address_alternate, address_alternate_id, address_ref, ("alternate_register_ref",)),
        (data_register, data_register_id, data_ref, ("register_ref",)),
        (data_alternate, data_alternate_id, data_ref, ("alternate_register_ref",)),
    ):
        assert resolve_handle(handle) is child
        info = get_parent_info(handle)
        assert info is not None
        assert info.parent_handle == get_handle(owner)
        assert info.path == path
        assert info.container == "single"
    assert address_register.register_ref == " \tδ_a_address_register\r\n"
    assert data_register.register_ref == " \tδ_a_data_register\r\n"
    assert address_alternate.alternate_register_ref == " \tδ_a_address_alternate\r\n"
    assert data_alternate.alternate_register_ref == " \tδ_a_data_alternate\r\n"
    _xml_round_trip(root)


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr"),
    [
        ("getIndirectAddressRefRegisterRefByName", "address", "register_ref"),
        ("getIndirectAddressRefRegisterRefID", "address", "register_ref"),
        ("getIndirectAddressRefAlternateRegisterRefByName", "address", "alternate_register_ref"),
        ("getIndirectAddressRefAlternateRegisterRefID", "address", "alternate_register_ref"),
        ("getIndirectDataRefRegisterRefByName", "data", "register_ref"),
        ("getIndirectDataRefRegisterRefID", "data", "register_ref"),
        ("getIndirectDataRefAlternateRegisterRefByName", "data", "alternate_register_ref"),
        ("getIndirectDataRefAlternateRegisterRefID", "data", "alternate_register_ref"),
    ],
    ids=(
        "register-name-address",
        "register-id-address",
        "alternate-name-address",
        "alternate-id-address",
        "register-name-data",
        "register-id-data",
        "alternate-name-data",
        "alternate-id-data",
    ),
)
def test_indirect_getters_return_none_for_missing_optional_wrappers(
    getter_name: str, owner_kind: str, target_attr: str
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    setattr(owner, target_attr, None)

    assert getattr(api, getter_name)(get_handle(owner)) is None


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr"),
    [
        ("getIndirectAddressRefRegisterRefByName", "address", "register_ref"),
        ("getIndirectAddressRefRegisterRefID", "address", "register_ref"),
        ("getIndirectAddressRefAlternateRegisterRefByName", "address", "alternate_register_ref"),
        ("getIndirectAddressRefAlternateRegisterRefID", "address", "alternate_register_ref"),
        ("getIndirectDataRefRegisterRefByName", "data", "register_ref"),
        ("getIndirectDataRefRegisterRefID", "data", "register_ref"),
        ("getIndirectDataRefAlternateRegisterRefByName", "data", "alternate_register_ref"),
        ("getIndirectDataRefAlternateRegisterRefID", "data", "alternate_register_ref"),
    ],
    ids=(
        "register-name-address",
        "register-id-address",
        "alternate-name-address",
        "alternate-id-address",
        "register-name-data",
        "register-id-data",
        "alternate-name-data",
        "alternate-id-data",
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
    ("getter_name", "owner_kind", "target_attr", "value_attr"),
    [
        ("getIndirectAddressRefRegisterRefByName", "address", "register_ref", "register_ref"),
        (
            "getIndirectAddressRefAlternateRegisterRefByName",
            "address",
            "alternate_register_ref",
            "alternate_register_ref",
        ),
        ("getIndirectDataRefRegisterRefByName", "data", "register_ref", "register_ref"),
        (
            "getIndirectDataRefAlternateRegisterRefByName",
            "data",
            "alternate_register_ref",
            "alternate_register_ref",
        ),
    ],
    ids=("register-address", "alternate-address", "register-data", "alternate-data"),
)
def test_by_name_getters_reject_invalid_xs_names_without_mutation(
    getter_name: str, owner_kind: str, target_attr: str, value_attr: str
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    wrapper = getattr(owner, target_attr)
    setattr(wrapper, value_attr, "bad name")

    with pytest.raises(TgiError) as error:
        getattr(api, getter_name)(get_handle(owner))

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(wrapper, value_attr) == "bad name"


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr", "value_attr"),
    [
        ("getIndirectAddressRefRegisterRefByName", "address", "register_ref", "register_ref"),
        (
            "getIndirectAddressRefAlternateRegisterRefByName",
            "address",
            "alternate_register_ref",
            "alternate_register_ref",
        ),
        ("getIndirectDataRefRegisterRefByName", "data", "register_ref", "register_ref"),
        (
            "getIndirectDataRefAlternateRegisterRefByName",
            "data",
            "alternate_register_ref",
            "alternate_register_ref",
        ),
    ],
    ids=("register-address", "alternate-address", "register-data", "alternate-data"),
)
@pytest.mark.parametrize(
    "malformed_value",
    [Value(value="not a reference"), True, 7, None],
    ids=("value-wrapper", "boolean", "integer", "missing-attribute"),
)
def test_by_name_getters_reject_non_string_reference_content(
    getter_name: str,
    owner_kind: str,
    target_attr: str,
    value_attr: str,
    malformed_value: object,
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    wrapper = getattr(owner, target_attr)
    setattr(wrapper, value_attr, malformed_value)

    with pytest.raises(TgiError) as error:
        getattr(api, getter_name)(get_handle(owner))

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(wrapper, value_attr) is malformed_value


@pytest.mark.parametrize(
    ("getter_name", "owner_kind", "target_attr", "value_attr"),
    [
        ("getIndirectAddressRefRegisterRefID", "address", "register_ref", "register_ref"),
        (
            "getIndirectAddressRefAlternateRegisterRefID",
            "address",
            "alternate_register_ref",
            "alternate_register_ref",
        ),
        ("getIndirectDataRefRegisterRefID", "data", "register_ref", "register_ref"),
        (
            "getIndirectDataRefAlternateRegisterRefID",
            "data",
            "alternate_register_ref",
            "alternate_register_ref",
        ),
    ],
    ids=("register-address", "alternate-address", "register-data", "alternate-data"),
)
def test_id_getters_preserve_handles_when_reference_content_is_malformed(
    getter_name: str, owner_kind: str, target_attr: str, value_attr: str
) -> None:
    root = _parsed_component()
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if owner_kind == "address" else interface.indirect_data_ref
    wrapper = getattr(owner, target_attr)
    wrapper_id = get_handle(wrapper)
    setattr(wrapper, value_attr, Value(value="bad"))

    assert getattr(api, getter_name)(get_handle(owner)) == wrapper_id
    assert getattr(wrapper, value_attr) == Value(value="bad")


def test_getters_and_removers_reject_unknown_wrong_type_and_stale_child_handles() -> None:
    root = _parsed_component()
    component_id = get_handle(root)
    first = root.indirect_interfaces.indirect_interface[0]
    address_ref, data_ref = first.indirect_address_ref, first.indirect_data_ref
    address_id, data_id = get_handle(address_ref), get_handle(data_ref)
    wrong_type_id = get_handle(first)
    stale_address_child = get_handle(address_ref.register_ref)
    stale_data_child = get_handle(data_ref.register_ref)

    assert api.removeIndirectAddressRefRegisterRef(address_id) is True
    assert api.removeIndirectDataRefRegisterRef(data_id) is True
    for getter_name in _GETTERS:
        with pytest.raises(TgiError) as error:
            getattr(api, getter_name)("unknown-handle")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for remove_name in _REMOVERS:
        with pytest.raises(TgiError) as error:
            getattr(api, remove_name)("unknown-handle")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    for getter_name in _GETTERS:
        for wrong_handle in (component_id, wrong_type_id, stale_address_child, stale_data_child):
            with pytest.raises(TgiError) as error:
                getattr(api, getter_name)(wrong_handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for remove_name in _REMOVERS:
        for wrong_handle in (component_id, wrong_type_id, stale_address_child, stale_data_child):
            with pytest.raises(TgiError) as error:
                getattr(api, remove_name)(wrong_handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    ("remove_name", "ref_attr", "register_getter", "alternate_getter"),
    (
        (
            "removeIndirectAddressRefRegisterRef",
            "indirect_address_ref",
            "getIndirectAddressRefRegisterRefID",
            "getIndirectAddressRefAlternateRegisterRefID",
        ),
        (
            "removeIndirectDataRefRegisterRef",
            "indirect_data_ref",
            "getIndirectDataRefRegisterRefID",
            "getIndirectDataRefAlternateRegisterRefID",
        ),
    ),
    ids=("remove-register-address", "remove-register-data"),
)
def test_parsed_register_removal_before_getters_invalidates_index_subtree_and_preserves_siblings(
    remove_name: str, ref_attr: str, register_getter: str, alternate_getter: str
) -> None:
    root = _parsed_component()
    first, second = root.indirect_interfaces.indirect_interface
    interface_id = get_handle(first)
    owner = getattr(first, ref_attr)
    peer_owner = second.indirect_address_ref if ref_attr == "indirect_data_ref" else second.indirect_data_ref
    target = owner.register_ref
    alternate = owner.alternate_register_ref
    retained_field = owner.field_ref
    assert target is not None and target.indices is not None
    assert alternate is not None
    owner_id = get_handle(owner)
    target_id = get_handle(target)
    indices_id = get_handle(target.indices)
    index_ids = [get_handle(index) for index in target.indices.index]
    field_id = get_handle(retained_field)
    alternate_id = get_handle(alternate)
    peer_register = peer_owner.register_ref
    assert peer_register is not None
    peer_register_id = get_handle(peer_register)
    second_id = get_handle(second)

    assert getattr(api, remove_name)(owner_id) is True

    assert owner.register_ref is None
    assert owner.alternate_register_ref is alternate
    assert owner.field_ref is retained_field
    assert resolve_handle(target_id) is None
    assert resolve_handle(indices_id) is None
    assert all(resolve_handle(index_id) is None for index_id in index_ids)
    assert resolve_handle(alternate_id) is alternate
    assert resolve_handle(field_id) is retained_field
    assert resolve_handle(peer_register_id) is peer_register
    assert resolve_handle(interface_id) is first
    assert resolve_handle(second_id) is second
    assert getattr(api, register_getter)(owner_id) is None
    assert getattr(api, alternate_getter)(owner_id) == alternate_id
    assert root.indirect_interfaces.indirect_interface == [first, second]
    _xml_round_trip(root)


@pytest.mark.parametrize(
    ("remove_name", "ref_attr"),
    (
        ("removeIndirectAddressRefRegisterRef", "indirect_address_ref"),
        ("removeIndirectDataRefRegisterRef", "indirect_data_ref"),
    ),
    ids=("address-missing-register", "data-missing-register"),
)
def test_removing_absent_register_ref_returns_false(remove_name: str, ref_attr: str) -> None:
    owner = getattr(_component().indirect_interfaces.indirect_interface[0], ref_attr)
    owner.register_ref = None

    assert getattr(api, remove_name)(get_handle(owner)) is False
    assert owner.register_ref is None


@pytest.mark.parametrize(
    ("remove_name", "owner_kind"),
    (
        ("removeIndirectAddressRefRegisterRef", "address"),
        ("removeIndirectDataRefRegisterRef", "data"),
    ),
    ids=("address-orphan-owner", "data-orphan-owner"),
)
def test_register_ref_removers_accept_standalone_typed_owners(remove_name: str, owner_kind: str) -> None:
    owner_type = IndirectAddressRef if owner_kind == "address" else IndirectDataRef
    owner = owner_type(
        register_ref=RegisterRef(register_ref="reg", indices=Indices(index=[Index(value="0")])),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref="alt"),
        field_ref=FieldRef(field_ref="field"),
    )
    owner_id = get_handle(owner)
    wrapper = owner.register_ref
    assert wrapper is not None
    wrapper_id = get_handle(wrapper)

    assert getattr(api, remove_name)(owner_id) is True
    assert owner.register_ref is None
    assert resolve_handle(wrapper_id) is None
    assert resolve_handle(owner_id) is owner
    assert owner.alternate_register_ref.alternate_register_ref == "alt"
    assert owner.field_ref.field_ref == "field"
