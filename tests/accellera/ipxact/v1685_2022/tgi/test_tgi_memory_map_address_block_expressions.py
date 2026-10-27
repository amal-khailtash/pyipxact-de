"""Address-block expression domains, generated storage and referenced definitions."""

from inspect import signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
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
    AddressBlockDefinitions,
    AddressBlockType,
    BankedBlockType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    MemoryMaps,
    MemoryMapType,
    TypeDefinitions,
    UnsignedIntExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

OPERATIONS = {
    "BaseAddress": (0, (1 << 64) - 1),
    "Range": (1, (1 << 64) - 1),
    "Width": (1, (1 << 32) - 1),
}
TARGET = ("test", "types", "blocks", "1")
OWNER = ("test", "components", "owner", "1")


@pytest.fixture(autouse=True)
def isolated_registry():
    registry.clear()
    yield
    registry.clear()


def block(model=AddressBlock, base="0", range_source="256", width="32"):
    r = UnsignedPositiveLongintExpression(value=range_source)
    w = UnsignedPositiveIntExpression(value=width)
    if model is BankedBlockType:
        return model(name="block", range=r, width=w)
    return model(name="block", base_address=BaseAddress(value=base), choice=(r, w))


def node(owner, kind):
    if kind == "BaseAddress":
        return owner.base_address
    if isinstance(owner, BankedBlockType):
        return getattr(owner, kind.lower())
    model = UnsignedPositiveLongintExpression if kind == "Range" else UnsignedPositiveIntExpression
    return next(item for item in owner.choice if isinstance(item, model))


def trio(kind):
    return [getattr(api, "getAddressBlock" + kind + suffix) for suffix in ("", "Expression", "ID")]


@pytest.mark.parametrize("model", [AddressBlock, AddressBlockType, BankedBlockType])
@pytest.mark.parametrize("kind", ["Range", "Width"])
def test_size_getters_preserve_raw_source_metadata_handles_and_actual_parent(model, kind):
    owner = block(model, range_source="2 ** 8", width="4 * 8")
    value, expression, identity = trio(kind)
    wrapper = node(owner, kind)
    wrapper.other_attributes = {"{urn:test}tag": "original"}
    handle, wrapper_id = get_handle(owner), get_handle(wrapper)
    original = owner.choice if not isinstance(owner, BankedBlockType) else owner.register_or_register_file
    assert value(handle) == (256 if kind == "Range" else 32)
    assert expression(handle) == wrapper.value
    assert identity(handle) == wrapper_id and resolve_handle(wrapper_id) is wrapper
    assert wrapper.other_attributes == {"{urn:test}tag": "original"}
    if not isinstance(owner, BankedBlockType):
        assert owner.choice is original
    info = get_parent_info(wrapper_id)
    assert resolve_handle(info.parent_handle) is owner
    assert info.path == ((kind.lower(),) if model is BankedBlockType else ("choice",))


@pytest.mark.parametrize("kind", OPERATIONS)
@pytest.mark.parametrize("boundary", ["min", "max"])
def test_unsigned_schema_boundaries_are_not_truncated(kind, boundary):
    owner = block()
    wrapper = node(owner, kind)
    wrapper.value = str(OPERATIONS[kind][boundary == "max"])
    value, expression, identity = trio(kind)
    assert value(get_handle(owner)) == int(wrapper.value)
    assert expression(get_handle(owner)) == wrapper.value
    assert identity(get_handle(owner)) == get_handle(wrapper)


@pytest.mark.parametrize("kind", OPERATIONS)
@pytest.mark.parametrize("bad", ["below", "above", "identifier", "invalid", "real"])
def test_numeric_faults_preserve_expression_source_and_id(kind, bad):
    owner = block()
    wrapper = node(owner, kind)
    low, high = OPERATIONS[kind]
    wrapper.value = {
        "below": str(low - 1),
        "above": str(high + 1),
        "identifier": "PARAM",
        "invalid": "1 / 0",
        "real": "1.5",
    }[bad]
    value, expression, identity = trio(kind)
    with pytest.raises(TgiError) as error:
        value(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert expression(get_handle(owner)) == wrapper.value
    assert identity(get_handle(owner)) == get_handle(wrapper)


@pytest.mark.parametrize("kind", OPERATIONS)
def test_declared_bounds_are_honored(kind):
    owner = block()
    wrapper = node(owner, kind)
    wrapper.value, wrapper.minimum, wrapper.maximum = "8", 4, 16
    value = trio(kind)[0]
    assert value(get_handle(owner)) == 8
    wrapper.minimum = 9
    with pytest.raises(TgiError) as error:
        value(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    wrapper.minimum, wrapper.maximum = 4, 7
    with pytest.raises(TgiError) as error:
        value(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_required_missing_foreign_duplicate_and_conflicting_choice_models_fault():
    owner = block()
    owner.base_address = None
    for op in trio("BaseAddress"):
        with pytest.raises(TgiError) as error:
            op(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for values in (
        None,
        {},
        (object(),),
        (),
        (UnsignedIntExpression(value="2"),),
        (UnsignedPositiveIntExpression(value="2"), UnsignedPositiveIntExpression(value="3")),
        (
            AddressBlockType.AddressBlockDefinitionRef(value="def", type_definitions="ext"),
            UnsignedPositiveLongintExpression(value="4"),
        ),
    ):
        owner.choice = values
        for kind in ("Range", "Width"):
            for op in trio(kind):
                with pytest.raises(TgiError) as error:
                    op(get_handle(owner))
                assert error.value.fault_code == TgiFaultCode.INVALID_ID
                assert owner.choice is values
    banked = block(BankedBlockType)
    banked.range = None
    for op in trio("Range"):
        with pytest.raises(TgiError):
            op(get_handle(banked))


def reference_context():
    definition = AddressBlockDefinitions.AddressBlockDefinition(
        name="definition",
        range=UnsignedPositiveLongintExpression(value="2 ** 9"),
        width=UnsignedPositiveIntExpression(value="64"),
    )
    target = TypeDefinitions(
        vendor=TARGET[0],
        library=TARGET[1],
        name=TARGET[2],
        version=TARGET[3],
        address_block_definitions=AddressBlockDefinitions(address_block_definition=[definition]),
    )
    ref = AddressBlockType.AddressBlockDefinitionRef(value="definition", type_definitions="imported")
    b = AddressBlock(name="block", base_address=BaseAddress(value="16"), choice=(ref,))
    ext = ExternalTypeDefinitions(
        name="imported",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=TARGET[0], library=TARGET[1], name=TARGET[2], version=TARGET[3]
        ),
    )
    owner = Component(
        vendor=OWNER[0],
        library=OWNER[1],
        name=OWNER[2],
        version=OWNER[3],
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=[ext]),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[b])]),
    )
    registry.register(owner, OWNER)
    registry.register(target, TARGET)
    return owner, b, target, definition, ref


def test_reference_branch_returns_actual_definition_children_and_keeps_local_base():
    owner, b, target, definition, ref = reference_context()
    original = b.choice
    for kind in ("Range", "Width"):
        value, expression, identity = trio(kind)
        wrapper = getattr(definition, kind.lower())
        assert value(get_handle(b)) == (512 if kind == "Range" else 64)
        assert expression(get_handle(b)) == wrapper.value
        assert identity(get_handle(b)) == get_handle(wrapper)
        info = get_parent_info(get_handle(wrapper))
        assert resolve_handle(info.parent_handle) is definition and info.path == (kind.lower(),)
    assert b.choice is original and ref.value == "definition"
    assert api.getAddressBlockBaseAddress(get_handle(b)) == 16
    assert api.getAddressBlockBaseAddressID(get_handle(b)) == get_handle(b.base_address)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(XmlDocument.serializer().render(owner).encode()))
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(owner), Component)
    registry.clear()
    registry.register(parsed, OWNER)
    registry.register(target, TARGET)
    assert api.getAddressBlockRange(get_handle(parsed.memory_maps.memory_map[0].choice[0])) == 512


def test_reference_missing_external_target_and_ambiguous_definition_faults():
    owner, b, target, definition, ref = reference_context()
    ref.type_definitions = "missing"
    with pytest.raises(TgiError) as error:
        api.getAddressBlockRange(get_handle(b))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    ref.type_definitions = "imported"
    ref.value = "missing"
    with pytest.raises(TgiError) as error:
        api.getAddressBlockWidth(get_handle(b))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    ref.value = "definition"
    target.address_block_definitions.address_block_definition.append(
        AddressBlockDefinitions.AddressBlockDefinition(
            name="definition",
            range=UnsignedPositiveLongintExpression(value="4"),
            width=UnsignedPositiveIntExpression(value="8"),
        )
    )
    with pytest.raises(TgiError) as error:
        api.getAddressBlockRangeID(get_handle(b))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    ref.value = "bad name"
    with pytest.raises(TgiError) as error:
        api.getAddressBlockWidthExpression(get_handle(b))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_signatures_strict_handles_and_excluded_definition_or_banked_base():
    for kind in OPERATIONS:
        for op in trio(kind):
            assert list(signature(op).parameters) == ["addressBlockID"]
            for invalid in (None, [], {}, "missing", get_handle(UnsignedPositiveIntExpression(value="2"))):
                with pytest.raises(TgiError) as error:
                    op(invalid)
                assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for op in trio("BaseAddress"):
        with pytest.raises(TgiError) as error:
            op(get_handle(block(BankedBlockType)))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    _, _, _, definition, _ = reference_context()
    for kind in OPERATIONS:
        for op in trio(kind):
            with pytest.raises(TgiError) as error:
                op(get_handle(definition))
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
