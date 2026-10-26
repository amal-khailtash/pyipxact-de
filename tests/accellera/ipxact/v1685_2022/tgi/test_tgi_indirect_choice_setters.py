"""Setter contracts for indirect address/data reference choices."""

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
    AddressSpaces,
    BaseAddress,
    Component,
    ComponentType,
    FieldRef,
    IndirectAddressRef,
    IndirectDataRef,
    IndirectInterface,
    IndirectInterfaces,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapRef,
    ModeRef,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_CHOICE = "address_space_ref_or_memory_map_ref_or_memory_remap_ref"
_KINDS = ("address", "data")
_BRANCHES = ("AddressSpaceRef", "MemoryMapRef", "MemoryRemapRef")
_SETTERS = tuple(f"setIndirect{kind.title()}Ref{branch}" for kind in _KINDS for branch in _BRANCHES)
_API_FUNCTIONS = _SETTERS


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _reference(kind: str, branch: str, value: str) -> object:
    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    if branch == "AddressSpaceRef":
        return owner_type.AddressSpaceRef(address_space_ref=value)
    if branch == "MemoryMapRef":
        return owner_type.MemoryMapRef(memory_map_ref=value)
    return MemoryRemapRef(memory_remap_ref=value)


def _owner(kind: str, choices: object = ()) -> IndirectAddressRef | IndirectDataRef:
    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    return owner_type(
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=choices,
        field_ref=FieldRef(field_ref=f"{kind}_field"),
    )


def _address_block(name: str) -> AddressBlock:
    return AddressBlock(
        name=name,
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="64"), UnsignedPositiveIntExpression(value="32")],
    )


def _component(
    address_choices: object = (), data_choices: object = (), *, name: str = "indirect_choice_setters"
) -> Component:
    modes = ("mode_a_shared", "mode_a_alt", "mode_b_shared", "mode_b_alt")
    memory_maps = []
    for map_name, mode_prefix in (("map_a", "mode_a"), ("map_b", "mode_b")):
        memory_maps.append(
            MemoryMapType(
                name=map_name,
                choice=[
                    MemoryRemap(
                        name="shared_window",
                        mode_ref=[ModeRef(value=f"{mode_prefix}_shared", priority=0)],
                        choice=[_address_block(f"{map_name}_shared_block")],
                    ),
                    MemoryRemap(
                        name="alternate_window",
                        mode_ref=[ModeRef(value=f"{mode_prefix}_alt", priority=0)],
                        choice=[_address_block(f"{map_name}_alt_block")],
                    ),
                ],
            )
        )
    return Component(
        vendor="acme",
        library="devices",
        name=name,
        version="1.0",
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name=address_space,
                    range=UnsignedPositiveLongintExpression(value="4096"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
                for address_space in ("space_a", "space_b")
            ]
        ),
        memory_maps=MemoryMaps(memory_map=memory_maps),
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name=mode) for mode in modes]),
        indirect_interfaces=IndirectInterfaces(
            indirect_interface=[
                IndirectInterface(
                    name="primary",
                    indirect_address_ref=_owner("address", address_choices),
                    indirect_data_ref=_owner("data", data_choices),
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


def _initial_choices(kind: str, branch: str = "MemoryMapRef") -> tuple[object, ...]:
    if branch == "AddressSpaceRef":
        return (_reference(kind, branch, "space_a"),)
    if branch == "MemoryMapRef":
        return (_reference(kind, branch, "map_a"),)
    return (_reference(kind, "MemoryMapRef", "map_a"), _reference(kind, "MemoryRemapRef", "shared_window"))


def _setter(kind: str, branch: str) -> str:
    return f"setIndirect{kind.title()}Ref{branch}"


def _getters(kind: str, branch: str) -> tuple[str, str]:
    return (
        f"getIndirect{kind.title()}Ref{branch}ByName",
        f"getIndirect{kind.title()}Ref{branch}ID",
    )


def _value_attribute(branch: str) -> str:
    return {
        "AddressSpaceRef": "address_space_ref",
        "MemoryMapRef": "memory_map_ref",
        "MemoryRemapRef": "memory_remap_ref",
    }[branch]


def _parameter_name(branch: str) -> str:
    return {
        "AddressSpaceRef": "addressSpaceRef",
        "MemoryMapRef": "memoryMapRef",
        "MemoryRemapRef": "memoryRemapRef",
    }[branch]


def test_public_exports_native_signatures_and_annex_f_sections() -> None:
    sections = {
        "AddressSpaceRef": {"address": "F.7.54.27", "data": "F.7.54.34"},
        "MemoryMapRef": {"address": "F.7.54.30", "data": "F.7.54.37"},
        "MemoryRemapRef": {"address": "F.7.54.31", "data": "F.7.54.38"},
    }
    expected = {
        _setter(kind, branch): (
            f"indirect{kind.title()}RefID",
            _parameter_name(branch),
            sections[branch][kind],
        )
        for kind in _KINDS
        for branch in _BRANCHES
    }

    assert set(_API_FUNCTIONS) == set(expected)
    assert set(_API_FUNCTIONS) <= set(api.__all__)
    assert set(_API_FUNCTIONS) <= set(tgi.__all__)
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
@pytest.mark.parametrize("branch", _BRANCHES)
def test_setters_create_or_update_typed_choices_and_preserve_compatible_wrappers(kind: str, branch: str) -> None:
    initial = _initial_choices(kind, "MemoryRemapRef")
    root = _parsed_component(
        _component(address_choices=initial if kind == "address" else (), data_choices=initial if kind == "data" else ())
    )
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    original = getattr(owner, _CHOICE)
    field_ref = owner.field_ref
    field_ref_id = get_handle(field_ref)
    old_ids = tuple(get_handle(item) for item in original)
    old_map, old_remap = original
    value, expected = {
        "AddressSpaceRef": ("  space_b\t", "space_b"),
        "MemoryMapRef": ("  map_b\t", "map_b"),
        "MemoryRemapRef": ("  alternate_window\t", "alternate_window"),
    }[branch]

    assert getattr(api, _setter(kind, branch))(owner_id, value) is True
    choice = getattr(owner, _CHOICE)
    name_getter, id_getter = _getters(kind, branch)
    assert getattr(api, name_getter)(owner_id) == expected
    child_id = getattr(api, id_getter)(owner_id)
    assert child_id is not None

    if branch == "AddressSpaceRef":
        owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
        child = choice[0]
        assert isinstance(child, owner_type.AddressSpaceRef)
        assert child.address_space_ref == expected
        assert resolve_handle(child_id) is child
        assert all(resolve_handle(old_id) is None for old_id in old_ids)
        assert len(choice) == 1
    else:
        owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
        assert isinstance(choice[0], owner_type.MemoryMapRef)
        assert isinstance(choice[1], MemoryRemapRef)
        assert choice[0] is old_map and choice[1] is old_remap
        assert get_handle(choice[0]) == old_ids[0] and get_handle(choice[1]) == old_ids[1]
        assert resolve_handle(old_ids[0]) is old_map and resolve_handle(old_ids[1]) is old_remap
        assert choice[0].memory_map_ref == (expected if branch == "MemoryMapRef" else "map_a")
        assert choice[1].memory_remap_ref == (expected if branch == "MemoryRemapRef" else "shared_window")
        assert child_id == (old_ids[0] if branch == "MemoryMapRef" else old_ids[1])

    assert owner.field_ref is field_ref and get_handle(field_ref) == field_ref_id
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("branch", ("AddressSpaceRef", "MemoryMapRef"))
def test_address_space_and_map_setters_switch_from_other_choice_branch(kind: str, branch: str) -> None:
    initial = _initial_choices(kind, "AddressSpaceRef" if branch == "MemoryMapRef" else "MemoryRemapRef")
    root = _parsed_component(
        _component(address_choices=initial if kind == "address" else (), data_choices=initial if kind == "data" else ())
    )
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    old_choice = getattr(owner, _CHOICE)
    old_ids = tuple(get_handle(item) for item in old_choice)
    value, expected = (" map_b ", "map_b") if branch == "MemoryMapRef" else (" space_b ", "space_b")

    assert getattr(api, _setter(kind, branch))(owner_id, value) is True
    name_getter, id_getter = _getters(kind, branch)
    assert getattr(api, name_getter)(owner_id) == expected
    assert resolve_handle(getattr(api, id_getter)(owner_id)) is getattr(owner, _CHOICE)[0]
    assert all(resolve_handle(old_id) is None for old_id in old_ids)
    assert len(getattr(owner, _CHOICE)) == 1
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("branch", ("AddressSpaceRef", "MemoryMapRef"))
def test_address_space_and_map_setters_create_choice_from_empty(kind: str, branch: str) -> None:
    root = _parsed_component(_component())
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    value = "space_a" if branch == "AddressSpaceRef" else "map_b"

    assert getattr(api, _setter(kind, branch))(owner_id, value) is True
    name_getter, id_getter = _getters(kind, branch)
    assert getattr(api, name_getter)(owner_id) == value
    assert getattr(api, id_getter)(owner_id) == get_handle(getattr(owner, _CHOICE)[0])
    assert len(getattr(owner, _CHOICE)) == 1
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))


@pytest.mark.parametrize("kind", _KINDS)
def test_remap_setter_requires_existing_memory_map_and_preserves_it(kind: str) -> None:
    for index, initial in enumerate(((), _initial_choices(kind, "AddressSpaceRef"))):
        root = _parsed_component(
            _component(
                address_choices=initial if kind == "address" else (),
                data_choices=initial if kind == "data" else (),
                name=f"indirect_remap_precondition_{kind}_{index}",
            )
        )
        owner = _owner_for(root, kind)
        owner_id = get_handle(owner)
        before = getattr(owner, _CHOICE)
        before_ids = tuple(get_handle(item) for item in before)

        with pytest.raises(TgiError) as error:
            getattr(api, _setter(kind, "MemoryRemapRef"))(owner_id, "alternate_window")
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert getattr(owner, _CHOICE) is before
        assert tuple(get_handle(item) for item in before) == before_ids

    root = _parsed_component(
        _component(
            address_choices=_initial_choices(kind, "MemoryMapRef") if kind == "address" else (),
            data_choices=_initial_choices(kind, "MemoryMapRef") if kind == "data" else (),
            name=f"indirect_remap_success_{kind}",
        )
    )
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    map_ref = getattr(owner, _CHOICE)[0]
    map_id = get_handle(map_ref)

    assert getattr(api, _setter(kind, "MemoryRemapRef"))(owner_id, " alternate_window ") is True
    remap_ref = getattr(owner, _CHOICE)[1]
    _, id_getter = _getters(kind, "MemoryRemapRef")
    remap_id = getattr(api, id_getter)(owner_id)
    assert isinstance(remap_ref, MemoryRemapRef)
    assert remap_ref.memory_remap_ref == "alternate_window"
    assert resolve_handle(map_id) is map_ref
    assert resolve_handle(remap_id) is remap_ref
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("branch", _BRANCHES)
@pytest.mark.parametrize("invalid", ("", "  ", "1invalid", "has space", "bad/name", "nul\x00name", None, 12))
def test_setters_reject_invalid_names_atomically(kind: str, branch: str, invalid: object) -> None:
    initial = _initial_choices(kind, "MemoryRemapRef")
    root = _parsed_component(
        _component(address_choices=initial if kind == "address" else (), data_choices=initial if kind == "data" else ())
    )
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    before = getattr(owner, _CHOICE)
    before_values = tuple(
        getattr(item, _value_attribute("MemoryMapRef" if index == 0 else "MemoryRemapRef"))
        for index, item in enumerate(before)
    )
    before_ids = tuple(get_handle(item) for item in before)

    with pytest.raises(TgiError) as error:
        getattr(api, _setter(kind, branch))(owner_id, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(owner, _CHOICE) is before
    assert tuple(get_handle(item) for item in before) == before_ids
    assert (
        tuple(
            getattr(item, _value_attribute("MemoryMapRef" if index == 0 else "MemoryRemapRef"))
            for index, item in enumerate(before)
        )
        == before_values
    )


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("branch", _BRANCHES)
def test_setters_reject_invalid_owner_or_malformed_choice_atomically(kind: str, branch: str) -> None:
    root = _parsed_component(_component())
    owner = _owner_for(root, kind)
    setter = getattr(api, _setter(kind, branch))

    with pytest.raises(TgiError) as error:
        setter(get_handle(root), "space_a")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, _CHOICE) == []

    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    malformed = (
        owner_type.AddressSpaceRef(address_space_ref="space_a"),
        owner_type.MemoryMapRef(memory_map_ref="map_a"),
    )
    setattr(owner, _CHOICE, malformed)
    choice_id = get_handle(owner)
    before = getattr(owner, _CHOICE)
    before_ids = tuple(get_handle(item) for item in before)

    with pytest.raises(TgiError) as error:
        setter(choice_id, "alternate_window")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, _CHOICE) is before
    assert tuple(get_handle(item) for item in before) == before_ids


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("branch", _BRANCHES)
def test_setters_reject_malformed_tuple_choice_without_replacing_or_mutating_it(kind: str, branch: str) -> None:
    root = _parsed_component(
        _component(
            address_choices=_initial_choices("address", "MemoryRemapRef"),
            data_choices=_initial_choices("data", "MemoryRemapRef"),
        )
    )
    owner = _owner_for(root, kind)
    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    original = (
        owner_type.AddressSpaceRef(address_space_ref="space_a"),
        owner_type.MemoryMapRef(memory_map_ref="map_a"),
    )
    setattr(owner, _CHOICE, original)
    owner_id = get_handle(owner)
    before_ids = tuple(get_handle(item) for item in original)
    before_values = (original[0].address_space_ref, original[1].memory_map_ref)

    with pytest.raises(TgiError) as error:
        getattr(api, _setter(kind, branch))(owner_id, "space_b")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, _CHOICE) is original
    assert tuple(get_handle(item) for item in original) == before_ids
    assert (original[0].address_space_ref, original[1].memory_map_ref) == before_values
