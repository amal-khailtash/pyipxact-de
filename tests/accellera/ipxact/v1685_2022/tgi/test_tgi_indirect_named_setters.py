"""Direct named-reference setters on indirect address and data references."""

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
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressBlockRef,
    AddressSpaces,
    AlternateRegisterRef,
    BaseAddress,
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
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_KINDS = ("address", "data")
_OPERATIONS = (
    ("AddressBlockRef", "address_block_ref", "address_block_ref", AddressBlockRef, "F.7.54.26"),
    (
        "AlternateRegisterRef",
        "alternate_register_ref",
        "alternate_register_ref",
        AlternateRegisterRef,
        "F.7.54.28",
    ),
    ("FieldRef", "field_ref", "field_ref", FieldRef, "F.7.54.29"),
    ("RegisterRef", "register_ref", "register_ref", RegisterRef, "F.7.54.32"),
)
_SUFFIXES = tuple(operation[0] for operation in _OPERATIONS)
_DATA_SECTIONS = {
    "AddressBlockRef": "F.7.54.33",
    "AlternateRegisterRef": "F.7.54.35",
    "FieldRef": "F.7.54.36",
    "RegisterRef": "F.7.54.39",
}
_INDEX_SUFFIXES = {
    "AddressBlockRef": "block",
    "FieldRef": "field",
    "RegisterRef": "register",
}
_SETTERS = tuple(f"setIndirect{kind.title()}Ref{suffix}" for kind in _KINDS for suffix in _SUFFIXES)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _index(suffix: str) -> Index:
    return Index(
        value="3",
        id=f"{suffix}_index",
        minimum=0,
        maximum=7,
        other_attributes={"{urn:test}preserved": "yes"},
    )


def _indices(suffix: str) -> Indices:
    return Indices(index=[_index(suffix)])


def _indirect_ref(kind: str) -> IndirectAddressRef | IndirectDataRef:
    return (IndirectAddressRef if kind == "address" else IndirectDataRef)(
        address_block_ref=AddressBlockRef(address_block_ref="block_a", indices=_indices(f"{kind}_block")),
        register_ref=RegisterRef(register_ref="register_a", indices=_indices(f"{kind}_register")),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref="alternate_a"),
        field_ref=FieldRef(field_ref="field_a", indices=_indices(f"{kind}_field")),
    )


def _address_block(name: str) -> AddressBlock:
    return AddressBlock(
        name=name,
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="64"), UnsignedPositiveIntExpression(value="32")],
    )


def _component(
    *,
    address: IndirectAddressRef | None = None,
    data: IndirectDataRef | None = None,
    name: str = "indirect_named_setters",
) -> Component:
    return Component(
        vendor="acme",
        library="devices",
        name=name,
        version="1.0",
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="space_a",
                    range=UnsignedPositiveLongintExpression(value="4096"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
            ]
        ),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map_a", choice=[_address_block("block_a")])]),
        indirect_interfaces=IndirectInterfaces(
            indirect_interface=[
                IndirectInterface(
                    name="primary",
                    indirect_address_ref=address if address is not None else _indirect_ref("address"),
                    indirect_data_ref=data if data is not None else _indirect_ref("data"),
                    memory_map_ref_or_transparent_bridge=["map_a"],
                )
            ]
        ),
    )


def _parsed_component(root: Component) -> Component:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    return parsed


def _owner_for(root: Component, kind: str) -> IndirectAddressRef | IndirectDataRef:
    interface = root.indirect_interfaces.indirect_interface[0]
    owner = interface.indirect_address_ref if kind == "address" else interface.indirect_data_ref
    assert owner is not None
    return owner


def _setter(kind: str, suffix: str) -> str:
    return f"setIndirect{kind.title()}Ref{suffix}"


def _getters(kind: str, suffix: str) -> tuple[str, str]:
    return (
        f"getIndirect{kind.title()}Ref{suffix}ByName",
        f"getIndirect{kind.title()}Ref{suffix}ID",
    )


def _xml_attribute(suffix: str) -> str:
    return {
        "AddressBlockRef": "addressBlockRef",
        "AlternateRegisterRef": "alternateRegisterRef",
        "FieldRef": "fieldRef",
        "RegisterRef": "registerRef",
    }[suffix]


def _value_attribute(suffix: str) -> str:
    return {
        "AddressBlockRef": "address_block_ref",
        "AlternateRegisterRef": "alternate_register_ref",
        "FieldRef": "field_ref",
        "RegisterRef": "register_ref",
    }[suffix]


def _parameter_name(suffix: str) -> str:
    return {
        "AddressBlockRef": "addressBlockRef",
        "AlternateRegisterRef": "alternateRegisterRef",
        "FieldRef": "fieldRef",
        "RegisterRef": "registerRef",
    }[suffix]


def test_public_exports_native_signatures_and_annex_f_sections() -> None:
    expected: dict[str, tuple[str, str, str]] = {}
    for suffix, _, _, _, address_section in _OPERATIONS:
        for kind in _KINDS:
            section = address_section if kind == "address" else _DATA_SECTIONS[suffix]
            expected[_setter(kind, suffix)] = (
                f"indirect{kind.title()}RefID",
                _parameter_name(suffix),
                section,
            )

    assert set(expected) == set(_SETTERS)
    assert set(_SETTERS) <= set(api.__all__)
    assert set(_SETTERS) <= set(tgi.__all__)
    for name, (owner_parameter, value_parameter, section) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == (owner_parameter, value_parameter)
        for parameter in signature.parameters.values():
            assert parameter.annotation is str
            assert not isinstance(parameter.annotation, str)
            assert parameter.default is inspect.Signature.empty
        assert signature.return_annotation is bool
        assert f"Section: {section}." in inspect.getdoc(function)


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("operation", _OPERATIONS, ids=["address-block", "alternate-register", "field", "register"])
def test_setters_update_generated_wrappers_in_place_and_preserve_indices_and_siblings(
    kind: str,
    operation: tuple[str, str, str, type[object], str],
) -> None:
    suffix, attribute, _, wrapper_type, _ = operation
    root = _parsed_component(_component())
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    target = getattr(owner, attribute)
    assert isinstance(target, wrapper_type)
    target_id = get_handle(target)
    index_holder = getattr(target, "indices", None)
    index_item = index_holder.index[0] if index_holder is not None else None
    descendant_ids = (
        (get_handle(index_holder), get_handle(index_item))
        if index_holder is not None and index_item is not None
        else ()
    )
    siblings = tuple(
        (name, getattr(owner, name), get_handle(getattr(owner, name)))
        for _, name, _, _, _ in _OPERATIONS
        if name != attribute
    )
    setter = getattr(api, _setter(kind, suffix))
    name_getter, id_getter = _getters(kind, suffix)

    assert setter(owner_id, " \tΩ:updated.reference\n") is True
    assert getattr(owner, attribute) is target
    assert getattr(target, _value_attribute(suffix)) == "Ω:updated.reference"
    assert getattr(api, name_getter)(owner_id) == "Ω:updated.reference"
    assert getattr(api, id_getter)(owner_id) == target_id
    assert resolve_handle(target_id) is target
    for name, sibling, sibling_id in siblings:
        assert getattr(owner, name) is sibling
        assert resolve_handle(sibling_id) is sibling
    if index_holder is not None and index_item is not None:
        assert target.indices is index_holder
        assert index_holder.index[0] is index_item
        assert tuple(get_handle(child) for child in (index_holder, index_item)) == descendant_ids
        assert (index_item.value, index_item.id, index_item.minimum, index_item.maximum) == (
            "3",
            f"{kind}_{_INDEX_SUFFIXES[suffix]}_index",
            0,
            7,
        )
        assert index_item.other_attributes == {"{urn:test}preserved": "yes"}

    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    reparsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(reparsed) == xml
    parsed_owner = _owner_for(reparsed, kind)
    assert getattr(getattr(parsed_owner, attribute), _value_attribute(suffix)) == "Ω:updated.reference"


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("suffix", ("AddressBlockRef", "AlternateRegisterRef", "RegisterRef"))
def test_optional_named_setters_create_correct_wrapper_when_absent(kind: str, suffix: str) -> None:
    root = _parsed_component(_component())
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    attribute = _value_attribute(suffix)
    wrapper_type = next(operation[3] for operation in _OPERATIONS if operation[0] == suffix)
    owner_attribute = {
        "AddressBlockRef": "address_block_ref",
        "AlternateRegisterRef": "alternate_register_ref",
        "RegisterRef": "register_ref",
    }[suffix]
    setattr(owner, owner_attribute, None)

    assert getattr(api, _setter(kind, suffix))(owner_id, "new_reference") is True
    child = getattr(owner, owner_attribute)
    assert isinstance(child, wrapper_type)
    assert getattr(child, attribute) == "new_reference"
    name_getter, id_getter = _getters(kind, suffix)
    assert getattr(api, name_getter)(owner_id) == "new_reference"
    child_id = getattr(api, id_getter)(owner_id)
    assert child_id == get_handle(child)
    assert resolve_handle(child_id) is child
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("suffix", _SUFFIXES)
@pytest.mark.parametrize("invalid", ("", "  ", "1invalid", "has space", "bad/name", "nul\x00name", None, 12))
def test_setters_reject_invalid_names_without_changing_wrapper_or_descendants(
    kind: str, suffix: str, invalid: object
) -> None:
    root = _parsed_component(_component())
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    attribute = _value_attribute(suffix)
    child = getattr(owner, attribute)
    original = getattr(child, attribute)
    child_id = get_handle(child)
    indices = getattr(child, "indices", None)
    index_ids = (get_handle(indices), get_handle(indices.index[0])) if indices is not None else ()

    with pytest.raises(TgiError) as error:
        getattr(api, _setter(kind, suffix))(owner_id, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(owner, attribute) is child
    assert getattr(child, attribute) == original
    assert get_handle(child) == child_id and resolve_handle(child_id) is child
    if indices is not None:
        assert child.indices is indices
        assert tuple((get_handle(indices), get_handle(indices.index[0]))) == index_ids


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("suffix", _SUFFIXES)
def test_setters_reject_invalid_owner_and_stale_handle(kind: str, suffix: str) -> None:
    root = _parsed_component(_component())
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    child = getattr(owner, _value_attribute(suffix))
    child_id = get_handle(child)
    setter = getattr(api, _setter(kind, suffix))

    for invalid_id in (get_handle(root), "stale-indirect-reference"):
        with pytest.raises(TgiError) as error:
            setter(invalid_id, "updated_reference")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert getattr(owner, _value_attribute(suffix)) is child
        assert get_handle(child) == child_id
    assert resolve_handle(owner_id) is owner


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("operation", _OPERATIONS, ids=["address-block", "alternate-register", "field", "register"])
def test_setters_reject_malformed_existing_wrapper_atomically(
    kind: str,
    operation: tuple[str, str, str, type[object], str],
) -> None:
    suffix, attribute, _, _, _ = operation
    root = _parsed_component(_component())
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    malformed = object()
    setattr(owner, attribute, malformed)

    with pytest.raises(TgiError) as error:
        getattr(api, _setter(kind, suffix))(owner_id, "replacement")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, attribute) is malformed
