"""Indirect-interface metadata and local memory-map getter contracts."""

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
    AddressBlock,
    AddressSpaces,
    BaseAddress,
    BitsInLau,
    Component,
    FieldRef,
    IndirectAddressRef,
    IndirectDataRef,
    IndirectInterface,
    IndirectInterfaces,
    MemoryMaps,
    MemoryMapType,
    TransparentBridge,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2022.endianess_type import EndianessType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_GETTERS = (
    "getIndirectInterfaceBitsInLau",
    "getIndirectInterfaceBitsInLauExpression",
    "getIndirectInterfaceEndianness",
    "getIndirectInterfaceIndirectAddressRefID",
    "getIndirectInterfaceIndirectDataRefID",
    "getIndirectInterfaceMemoryMapRefByID",
    "getIndirectInterfaceMemoryMapRefByName",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _address_block(name: str) -> AddressBlock:
    return AddressBlock(
        name=name,
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="64"), UnsignedPositiveIntExpression(value="32")],
    )


def _component(
    *,
    name: str = "indirect_interface_getters",
    map_name: str = "map_a",
    memory_maps: list[MemoryMapType] | None = None,
    memory_map_choice: object = None,
    bits_in_lau: BitsInLau | None = None,
    endianness: EndianessType | None = None,
) -> Component:
    maps = (
        memory_maps if memory_maps is not None else [MemoryMapType(name=map_name, choice=[_address_block("block_a")])]
    )
    choice = [map_name] if memory_map_choice is None else memory_map_choice
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
        memory_maps=MemoryMaps(memory_map=maps),
        indirect_interfaces=IndirectInterfaces(
            indirect_interface=[
                IndirectInterface(
                    name="primary",
                    indirect_address_ref=IndirectAddressRef(field_ref=FieldRef(field_ref="address_field")),
                    indirect_data_ref=IndirectDataRef(field_ref=FieldRef(field_ref="data_field")),
                    memory_map_ref_or_transparent_bridge=choice,
                    bits_in_lau=bits_in_lau,
                    endianness=endianness,
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


def _registered_component(root: Component) -> Component:
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    return root


def _interface_for(root: Component) -> IndirectInterface:
    return root.indirect_interfaces.indirect_interface[0]


def test_public_exports_native_signatures_and_annex_f_sections() -> None:
    expected = {
        "getIndirectInterfaceBitsInLau": (int, "F.7.53.39"),
        "getIndirectInterfaceBitsInLauExpression": (str | None, "F.7.53.40"),
        "getIndirectInterfaceEndianness": (str, "F.7.53.41"),
        "getIndirectInterfaceIndirectAddressRefID": (str, "F.7.53.42"),
        "getIndirectInterfaceIndirectDataRefID": (str, "F.7.53.43"),
        "getIndirectInterfaceMemoryMapRefByID": (str | None, "F.7.53.44"),
        "getIndirectInterfaceMemoryMapRefByName": (str | None, "F.7.53.45"),
    }

    assert set(_GETTERS) == set(expected)
    assert set(_GETTERS) <= set(api.__all__)
    assert set(_GETTERS) <= set(tgi.__all__)
    for name, (return_type, section) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == ("indirectInterfaceID",)
        parameter = next(iter(signature.parameters.values()))
        assert parameter.annotation is str
        assert not isinstance(parameter.annotation, str)
        assert parameter.default is inspect.Signature.empty
        assert signature.return_annotation == return_type
        assert f"Section: {section}." in inspect.getdoc(function)


@pytest.mark.parametrize("getter_name", _GETTERS)
def test_getters_reject_wrong_typed_interface_handle(getter_name: str) -> None:
    root = _registered_component(_component())
    wrong_owner_id = get_handle(root)

    with pytest.raises(TgiError) as error:
        getattr(api, getter_name)(wrong_owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_bits_in_lau_defaults_to_eight_and_expression_getter_returns_none_when_absent() -> None:
    root = _parsed_component(_component())
    interface = _interface_for(root)
    interface_id = get_handle(interface)

    assert api.getIndirectInterfaceBitsInLau(interface_id) == 8
    assert api.getIndirectInterfaceBitsInLauExpression(interface_id) is None


@pytest.mark.parametrize(
    ("expression", "minimum", "maximum", "expected"),
    [
        ("8 * 4", 32, 64, 32),
        ("64'h7FFFFFFFFFFFFFFF", None, None, (1 << 63) - 1),
    ],
)
def test_bits_in_lau_evaluates_sv_expressions_as_positive_signed_tgi_long(
    expression: str, minimum: int | None, maximum: int | None, expected: int
) -> None:
    root = _parsed_component(_component(bits_in_lau=BitsInLau(value=expression, minimum=minimum, maximum=maximum)))
    interface = _interface_for(root)
    interface_id = get_handle(interface)
    node = interface.bits_in_lau
    assert node is not None

    assert api.getIndirectInterfaceBitsInLau(interface_id) == expected
    assert api.getIndirectInterfaceBitsInLauExpression(interface_id) == expression
    assert node.value == expression


@pytest.mark.parametrize(
    ("expression", "minimum", "maximum"),
    [
        ("0", None, None),
        ("-1", None, None),
        ("64'h8000000000000000", None, None),
        ("16", 32, None),
        ("64", None, 32),
        ("unresolved_value", None, None),
    ],
)
def test_bits_in_lau_rejects_values_outside_signed_positive_or_declared_bounds(
    expression: str, minimum: int | None, maximum: int | None
) -> None:
    root = _registered_component(_component(bits_in_lau=BitsInLau(value=expression, minimum=minimum, maximum=maximum)))
    interface = _interface_for(root)
    interface_id = get_handle(interface)
    source = interface.bits_in_lau
    assert source is not None

    with pytest.raises(TgiError) as error:
        api.getIndirectInterfaceBitsInLau(interface_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getIndirectInterfaceBitsInLauExpression(interface_id) == expression
    assert interface.bits_in_lau is source and source.value == expression


def test_endianness_defaults_to_little_and_returns_generated_enum_value() -> None:
    root = _parsed_component(_component())
    interface = _interface_for(root)
    interface_id = get_handle(interface)

    assert api.getIndirectInterfaceEndianness(interface_id) == "little"
    interface.endianness = EndianessType.BIG
    assert api.getIndirectInterfaceEndianness(interface_id) == "big"
    assert interface.endianness is EndianessType.BIG
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))


def test_endianness_rejects_malformed_raw_model_without_mutating_it() -> None:
    root = _registered_component(_component())
    interface = _interface_for(root)
    interface.endianness = "middle"
    interface_id = get_handle(interface)

    with pytest.raises(TgiError) as error:
        api.getIndirectInterfaceEndianness(interface_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert interface.endianness == "middle"


def test_required_address_and_data_ref_getters_return_strict_owned_handles() -> None:
    root = _parsed_component(_component())
    interface = _interface_for(root)
    interface_id = get_handle(interface)
    address_ref = interface.indirect_address_ref
    data_ref = interface.indirect_data_ref
    address_id = api.getIndirectInterfaceIndirectAddressRefID(interface_id)
    data_id = api.getIndirectInterfaceIndirectDataRefID(interface_id)

    assert address_id == get_handle(address_ref)
    assert data_id == get_handle(data_ref)
    assert resolve_handle(address_id) is address_ref
    assert resolve_handle(data_id) is data_ref
    for child_id, child in ((address_id, address_ref), (data_id, data_ref)):
        info = get_parent_info(child_id)
        assert info is not None and info.parent_handle == interface_id
        assert info.path == ("indirect_address_ref" if child is address_ref else "indirect_data_ref",)
        field_id = get_handle(child.field_ref)
        assert resolve_handle(field_id) is child.field_ref


@pytest.mark.parametrize("attribute", ("indirect_address_ref", "indirect_data_ref"))
def test_required_reference_getter_rejects_missing_or_wrong_typed_child(attribute: str) -> None:
    root = _registered_component(_component())
    interface = _interface_for(root)
    interface_id = get_handle(interface)
    original = getattr(interface, attribute)
    setattr(interface, attribute, None)
    getter = (
        api.getIndirectInterfaceIndirectAddressRefID
        if attribute == "indirect_address_ref"
        else api.getIndirectInterfaceIndirectDataRefID
    )

    with pytest.raises(TgiError) as error:
        getter(interface_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(interface, attribute) is None
    setattr(interface, attribute, original)
    setattr(interface, attribute, object())
    with pytest.raises(TgiError) as error:
        getter(interface_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_memory_map_getters_return_name_and_resolved_local_target_handle() -> None:
    root = _parsed_component(_component(map_name="δ_map", memory_map_choice=["δ_map"]))
    interface = _interface_for(root)
    interface_id = get_handle(interface)
    target = root.memory_maps.memory_map[0]
    target_id = get_handle(target)
    choice = interface.memory_map_ref_or_transparent_bridge

    assert api.getIndirectInterfaceMemoryMapRefByName(interface_id) == "δ_map"
    reference_id = api.getIndirectInterfaceMemoryMapRefByID(interface_id)
    assert reference_id == target_id
    assert reference_id != "δ_map"
    assert resolve_handle(reference_id) is target
    assert interface.memory_map_ref_or_transparent_bridge is choice
    assert choice == ["δ_map"]


def test_memory_map_name_getter_rejects_invalid_xml_name_without_changing_raw_source() -> None:
    root = _registered_component(_component(memory_map_choice=["bad name"]))
    interface = _interface_for(root)
    interface_id = get_handle(interface)
    choice = interface.memory_map_ref_or_transparent_bridge

    with pytest.raises(TgiError) as error:
        api.getIndirectInterfaceMemoryMapRefByName(interface_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert interface.memory_map_ref_or_transparent_bridge is choice
    assert choice == ["bad name"]


def test_memory_map_by_id_reports_missing_and_ambiguous_local_targets() -> None:
    missing = _registered_component(_component(name="missing_map_owner", memory_map_choice=["not_found"]))
    missing_interface = _interface_for(missing)
    missing_id = get_handle(missing_interface)
    assert api.getIndirectInterfaceMemoryMapRefByName(missing_id) == "not_found"
    with pytest.raises(TgiError) as error:
        api.getIndirectInterfaceMemoryMapRefByID(missing_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    assert missing_interface.memory_map_ref_or_transparent_bridge == ["not_found"]

    maps = [MemoryMapType(name="duplicate_map"), MemoryMapType(name="duplicate_map")]
    duplicate = _registered_component(
        _component(name="duplicate_map_owner", memory_maps=maps, memory_map_choice=["duplicate_map"])
    )
    duplicate_interface = _interface_for(duplicate)
    duplicate_id = get_handle(duplicate_interface)
    with pytest.raises(TgiError) as error:
        api.getIndirectInterfaceMemoryMapRefByID(duplicate_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert duplicate_interface.memory_map_ref_or_transparent_bridge == ["duplicate_map"]


def test_absent_memory_map_choice_and_transparent_bridge_branch_return_none() -> None:
    root = _parsed_component(_component())
    interface = _interface_for(root)
    interface_id = get_handle(interface)
    empty = []
    interface.memory_map_ref_or_transparent_bridge = empty

    assert api.getIndirectInterfaceMemoryMapRefByName(interface_id) is None
    assert api.getIndirectInterfaceMemoryMapRefByID(interface_id) is None
    assert interface.memory_map_ref_or_transparent_bridge is empty

    bridges = [TransparentBridge(initiator_ref="initiator")]
    interface.memory_map_ref_or_transparent_bridge = bridges
    assert api.getIndirectInterfaceMemoryMapRefByName(interface_id) is None
    assert api.getIndirectInterfaceMemoryMapRefByID(interface_id) is None
    assert interface.memory_map_ref_or_transparent_bridge is bridges


@pytest.mark.parametrize(
    "malformed",
    [
        ["map_a", "map_b"],
        ["map_a", TransparentBridge(initiator_ref="initiator")],
        ("map_a", "map_b"),
        [object()],
    ],
    ids=("multiple-map-refs", "mixed-branches", "tuple-choice", "unknown-choice-item"),
)
def test_memory_map_getters_reject_malformed_generated_choice_atomically(malformed: object) -> None:
    root = _registered_component(_component())
    interface = _interface_for(root)
    interface_id = get_handle(interface)
    interface.memory_map_ref_or_transparent_bridge = malformed

    for getter in (api.getIndirectInterfaceMemoryMapRefByName, api.getIndirectInterfaceMemoryMapRefByID):
        with pytest.raises(TgiError) as error:
            getter(interface_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert interface.memory_map_ref_or_transparent_bridge is malformed
