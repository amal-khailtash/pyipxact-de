"""Address-block source expressions, arrays, indices and definition assignment."""

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
    AddressBlockRef,
    AddressBlockType,
    Array,
    BankedBlockType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    Dim,
    ExternalTypeDefinitions,
    MemoryMaps,
    MemoryMapType,
    Stride,
    TypeDefinitions,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def block(model=AddressBlock):
    range = UnsignedPositiveLongintExpression(value="16")
    width = UnsignedPositiveIntExpression(value="8")
    if model is BankedBlockType:
        return model(name="block", range=range, width=width)
    return model(name="block", base_address=BaseAddress(value="0"), choice=(range, width))


def wrapper(owner, kind):
    if kind == "BaseAddress":
        return owner.base_address
    if isinstance(owner, BankedBlockType):
        return getattr(owner, kind.lower())
    model = UnsignedPositiveLongintExpression if kind == "Range" else UnsignedPositiveIntExpression
    return next(item for item in owner.choice if isinstance(item, model))


@pytest.mark.parametrize("model", [AddressBlock, AddressBlockType, BankedBlockType])
@pytest.mark.parametrize("kind", ["Range", "Width"])
def test_size_sources_bounds_identity_and_deferred_expressions(model, kind):
    owner = block(model)
    node = wrapper(owner, kind)
    node.other_attributes = {"{urn:test}tag": "keep"}
    node_id = get_handle(node)
    op = getattr(api, "setAddressBlock" + kind)
    maximum = (1 << (64 if kind == "Range" else 32)) - 1
    assert op(get_handle(owner), str(maximum)) is True
    assert node.value == str(maximum) and resolve_handle(node_id) is node
    original = owner.choice if model is not BankedBlockType else None
    assert op(get_handle(owner), " PARAM + 1 ") is True
    assert node.value == " PARAM + 1 " and node.other_attributes == {"{urn:test}tag": "keep"}
    if original is not None:
        assert owner.choice is original
    for source in ("0", "-1", str(maximum + 1), "1 / 0", "1.5", ""):
        with pytest.raises(TgiError):
            op(get_handle(owner), source)
        assert node.value == " PARAM + 1 "
    node.minimum, node.maximum = 2, 5
    for source in ("1", "6"):
        with pytest.raises(TgiError):
            op(get_handle(owner), source)
    assert op(get_handle(owner), "2") is True
    assert resolve_handle(get_parent_info(node_id).parent_handle) is owner


def test_base_setter_preserves_wrapper_bounds_and_reference_branch():
    owner = block()
    node = owner.base_address
    node_id = get_handle(node)
    node.other_attributes = {"{urn:test}tag": "keep"}
    ref = AddressBlockType.AddressBlockDefinitionRef(value="definition", type_definitions="unloaded")
    owner.choice = (ref,)
    original = owner.choice
    for source in ("0", str((1 << 64) - 1), " BASE_PARAM "):
        assert api.setAddressBlockBaseAddress(get_handle(owner), source) is True
        assert node.value == source and resolve_handle(node_id) is node and owner.choice is original
    for source in ("-1", str(1 << 64), "1.5", "1 / 0"):
        with pytest.raises(TgiError):
            api.setAddressBlockBaseAddress(get_handle(owner), source)
    node.minimum, node.maximum = 2, 4
    with pytest.raises(TgiError):
        api.setAddressBlockBaseAddress(get_handle(owner), "5")
    assert node.other_attributes == {"{urn:test}tag": "keep"}


def test_array_first_dimension_updates_preserve_multidimensional_storage_and_stride():
    owner = block()
    assert api.setAddressBlockArray(get_handle(owner), "2") is True
    array = owner.array
    first = array.dim[0]
    first.id, first.index_var = "dimension", "i"
    first_id, array_id = get_handle(first), get_handle(array)
    second = Dim(value="3")
    array.dim = (first, second)
    array.stride = Stride(value="16")
    original = array.dim
    assert api.setAddressBlockArray(get_handle(owner), str((1 << 64) - 1)) is True
    assert first.value == str((1 << 64) - 1) and array.dim is original
    assert api.setAddressBlockArray(get_handle(owner), "DIM_PARAM") is True
    assert array.dim is original and first.value == "DIM_PARAM" and second.value == "3"
    assert first.id == "dimension" and first.index_var == "i" and array.stride.value == "16"
    assert resolve_handle(first_id) is first and resolve_handle(array_id) is array
    first.minimum, first.maximum = 2, 5
    for source in ("0", "6", str(1 << 64), "1.5"):
        with pytest.raises(TgiError):
            api.setAddressBlockArray(get_handle(owner), source)
        assert first.value == "DIM_PARAM" and array.dim is original
    assert api.setAddressBlockArray(get_handle(owner), "2") is True
    assert get_parent_info(first_id).path == ("dim",)


def test_index_adder_creates_then_appends_owned_expression_wrappers():
    reference = AddressBlockRef(address_block_ref="block")
    first_id = api.addAddressBlockRefIndex(get_handle(reference), "INDEX_PARAM")
    first = resolve_handle(first_id)
    holder = reference.indices
    holder.index = (first,)
    last_id = api.addAddressBlockRefIndex(get_handle(reference), str((1 << 32) - 1))
    assert holder.index == [first, resolve_handle(last_id)]
    assert first.value == "INDEX_PARAM" and get_parent_info(last_id).parent_handle == get_handle(holder)
    for source in ("-1", str(1 << 32), "1 / 0", "1.5"):
        with pytest.raises(TgiError):
            api.addAddressBlockRefIndex(get_handle(reference), source)
        assert len(holder.index) == 2


def test_definition_choice_replacement_invalidates_owned_content_preserves_instance_data():
    owner = block()
    old_nodes = tuple(owner.choice)
    old_ids = [get_handle(node) for node in old_nodes]
    owner.array = Array(dim=[Dim(value="2")])
    base, array, original = owner.base_address, owner.array, owner.choice
    with pytest.raises(TgiError):
        api.setAddressBlockAddressBlockDefinitionRef(get_handle(owner), "bad name", "external")
    assert owner.choice is original
    assert api.setAddressBlockAddressBlockDefinitionRef(get_handle(owner), " definition ", " external ") is True
    reference = owner.choice[0]
    reference_id = api.getAddressBlockAddressBlockDefinitionRefID(get_handle(owner))
    assert reference.value == "definition" and reference.type_definitions == "external"
    assert all(resolve_handle(handle) is None for handle in old_ids)
    assert owner.base_address is base and owner.array is array
    owner.choice = tuple(owner.choice)
    original = owner.choice
    assert api.setAddressBlockAddressBlockDefinitionRef(get_handle(owner), "new", "other") is True
    assert owner.choice is original and resolve_handle(reference_id) is reference
    assert reference.value == "new" and reference.type_definitions == "other"
    assert api.setAddressBlockArray(get_handle(owner), "3") is True
    for op in (api.setAddressBlockRange, api.setAddressBlockWidth):
        with pytest.raises(TgiError) as error:
            op(get_handle(owner), "8")
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    banked = block(BankedBlockType)
    with pytest.raises(TgiError):
        api.setAddressBlockAddressBlockDefinitionRef(get_handle(banked), "definition", "external")


def context():
    owner = block()
    api.setAddressBlockAddressBlockDefinitionRef(get_handle(owner), "original", "external")
    external = ExternalTypeDefinitions(
        name="external",
        type_definitions_ref=ConfigurableLibraryRefType(vendor="test", library="types", name="library", version="1"),
    )
    root = Component(
        vendor="test",
        library="component",
        name="owner",
        version="1",
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=[external]),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[owner])]),
    )
    definition = AddressBlockDefinitions.AddressBlockDefinition(
        name="new", range=UnsignedPositiveLongintExpression(value="16"), width=UnsignedPositiveIntExpression(value="8")
    )
    target = TypeDefinitions(
        vendor="test",
        library="types",
        name="library",
        version="1",
        address_block_definitions=AddressBlockDefinitions(address_block_definition=[definition]),
    )
    registry.register(root, ("test", "component", "owner", "1"))
    registry.register(target, ("test", "types", "library", "1"))
    return root, owner, definition


def test_wrapper_setter_uses_definition_handle_and_preserves_selected_external_library():
    _root, owner, definition = context()
    ref = owner.choice[0]
    ref_id = get_handle(ref)
    assert api.setAddressBlockDefinitionRef(ref_id, get_handle(definition)) is True
    assert ref.value == "new" and ref.type_definitions == "external" and resolve_handle(ref_id) is ref
    assert api.getAddressBlockAddressBlockDefinitionRefByID(get_handle(owner)) == get_handle(definition)
    foreign = AddressBlockDefinitions.AddressBlockDefinition(
        name="new", range=UnsignedPositiveLongintExpression(value="4"), width=UnsignedPositiveIntExpression(value="8")
    )
    with pytest.raises(TgiError) as error:
        api.setAddressBlockDefinitionRef(ref_id, get_handle(foreign))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    for handle in ("new", "missing", get_handle(BaseAddress(value="0"))):
        with pytest.raises(TgiError):
            api.setAddressBlockDefinitionRef(ref_id, handle)
    assert ref.value == "new" and ref.type_definitions == "external"


def test_edited_reference_component_validates_and_round_trips():
    root, owner, definition = context()
    api.setAddressBlockDefinitionRef(get_handle(owner.choice[0]), get_handle(definition))
    api.setAddressBlockArray(get_handle(owner), "2")
    api.setAddressBlockBaseAddress(get_handle(owner), "16")
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_block = parsed.memory_maps.memory_map[0].choice[0]
    assert parsed_block.array.dim[0].value == "2" and parsed_block.base_address.value == "16"
    assert parsed_block.choice[0].value == "new" and parsed_block.choice[0].type_definitions == "external"
    assert schema.validate(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))


@pytest.mark.parametrize(
    "operation,parameters,args",
    [
        (api.addAddressBlockRefIndex, ["addressBlockRefID", "value"], ["0"]),
        (api.setAddressBlockAddressBlockDefinitionRef, ["addressBlockID", "value", "typeDefinitions"], ["name", "ext"]),
        (api.setAddressBlockArray, ["addressBlockID", "dim"], ["2"]),
        (api.setAddressBlockBaseAddress, ["addressBlockID", "baseAddress"], ["0"]),
        (api.setAddressBlockDefinitionRef, ["addressBlockDefinitionRefID", "value"], ["missing"]),
        (api.setAddressBlockRange, ["addressBlockID", "range"], ["16"]),
        (api.setAddressBlockWidth, ["addressBlockID", "width"], ["8"]),
    ],
)
def test_exact_signatures_and_invalid_handles(operation, parameters, args):
    assert list(signature(operation).parameters) == parameters
    for handle in (None, 7, "missing", get_handle(BaseAddress(value="0"))):
        with pytest.raises(TgiError) as error:
            operation(handle, *args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
