"""Register field/reference source, target and index lifecycle contracts."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import register
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
    AddressBlockRef,
    AddressBlockType,
    AddressUnitBits,
    BaseAddress,
    Component,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    RegisterFileRef,
    RegisterRef,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
CASES = [("Field", FieldRef, "field_ref"), ("Register", RegisterRef, "register_ref")]


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def component() -> Component:
    source = FieldType(
        name="aliasField",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[
            FieldType.AliasOf(register_ref=RegisterRef(register_ref="target"), field_ref=FieldRef(field_ref="data"))
        ],
    )
    target = AddressBlockType.Register(
        name="target",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[
            UnsignedPositiveIntExpression(value="8"),
            FieldType(
                name="data",
                bit_offset=UnsignedIntExpression(value="0"),
                choice=[UnsignedPositiveIntExpression(value="8")],
            ),
        ],
    )
    source_register = AddressBlockType.Register(
        name="source",
        address_offset=UnsignedLongintExpression(value="1"),
        choice=[UnsignedPositiveIntExpression(value="8"), source],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="16"),
            UnsignedPositiveIntExpression(value="8"),
            UsageType.REGISTER,
            target,
            source_register,
        ],
    )
    return Component(
        vendor="acme",
        library="test",
        name="indices",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )


def parsed_source(root: Component) -> FieldType.AliasOf:
    return root.memory_maps.memory_map[0].choice[0].choice[4].choice[1].choice[0]


@pytest.mark.parametrize("kind,model,attribute", CASES)
def test_signatures_exports_and_name_sources(kind, model, attribute):
    source = model(**{attribute: " \tδ_target\n"})
    handle = get_handle(source)
    name = getattr(api, f"get{kind}Ref{kind}RefByName")
    ids = getattr(api, f"get{kind}RefIndexIDs")
    add = getattr(api, f"add{kind}RefIndex")
    remove = getattr(api, f"remove{kind}RefIndex")
    assert name(handle) == "δ_target"
    assert getattr(source, attribute) == " \tδ_target\n"
    assert ids(handle) == []
    assert list(inspect.signature(add).parameters) == [f"{kind.lower()}RefID", "value"]
    assert list(inspect.signature(remove).parameters) == ["indexID"]
    assert all(op.__name__ in register.__all__ for op in (name, ids, add, remove))
    with pytest.raises(TgiError) as error:
        setattr(source, attribute, "bad Name")
        name(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind,model,attribute", CASES)
def test_index_creation_expression_sources_order_metadata_and_pruning(kind, model, attribute):
    source = model(**{attribute: "target"})
    source_id = get_handle(source)
    add = getattr(api, f"add{kind}RefIndex")
    ids = getattr(api, f"get{kind}RefIndexIDs")
    remove = getattr(api, f"remove{kind}RefIndex")
    first_id = add(source_id, " 1 + 2 ")
    first = resolve_handle(first_id)
    assert isinstance(first, Index) and first.value == " 1 + 2 "
    first.id = "first_index"
    first.minimum = 0
    holder = source.indices
    holder_id = get_handle(holder)
    holder.index = tuple(holder.index)
    second_id = add(source_id, "INDEX_PARAMETER")
    assert source.indices is holder
    assert ids(source_id) == [first_id, second_id]
    assert first.id == "first_index" and first.minimum == 0
    assert get_parent_info(first_id).parent_handle == holder_id
    assert get_parent_info(holder_id).parent_handle == source_id
    assert remove(first_id) is True
    assert resolve_handle(first_id) is None and source.indices is holder
    assert remove(second_id) is True
    assert source.indices is None and resolve_handle(holder_id) is None
    with pytest.raises(TgiError) as error:
        remove(second_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind,model,attribute", CASES)
@pytest.mark.parametrize("value", ["-1", "4294967296", "", "1 +", 1, False])
def test_invalid_index_input_is_atomic(kind, model, attribute, value):
    existing = Index(value="4")
    holder = Indices(index=(existing,))
    source = model(**{attribute: "target", "indices": holder})
    original = holder.index
    with pytest.raises(TgiError) as error:
        getattr(api, f"add{kind}RefIndex")(get_handle(source), value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert source.indices is holder and holder.index is original
    assert holder.index == (existing,) and existing.value == "4"
    empty = model(**{attribute: "target"})
    with pytest.raises(TgiError):
        getattr(api, f"add{kind}RefIndex")(get_handle(empty), value)
    assert empty.indices is None


@pytest.mark.parametrize("kind,model,attribute", CASES)
@pytest.mark.parametrize("bad", ["wrong", Indices(index=[UnsignedIntExpression(value="1")]), Indices(index="bad")])
def test_malformed_holder_models_are_rejected_without_mutation(kind, model, attribute, bad):
    source = model(**{attribute: "target", "indices": bad})
    for operation in (
        lambda: getattr(api, f"get{kind}RefIndexIDs")(get_handle(source)),
        lambda: getattr(api, f"add{kind}RefIndex")(get_handle(source), "1"),
    ):
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert source.indices is bad


@pytest.mark.parametrize("kind,model,attribute", CASES)
def test_uint32_boundary_duplicate_values_and_tuple_read(kind, model, attribute):
    source = model(**{attribute: "target", "indices": Indices(index=(Index(value="1"), Index(value="1")))})
    original = source.indices.index
    assert len(getattr(api, f"get{kind}RefIndexIDs")(get_handle(source))) == 2
    assert source.indices.index is original
    handle = getattr(api, f"add{kind}RefIndex")(get_handle(source), "4294967295")
    assert resolve_handle(handle).value == "4294967295"


@pytest.mark.parametrize("kind,model,attribute", CASES)
def test_removal_rejects_other_reference_family_and_detached_indices(kind, model, attribute):
    other = RegisterRef(register_ref="other") if model is FieldRef else FieldRef(field_ref="other")
    other_kind = "Register" if model is FieldRef else "Field"
    index_id = getattr(api, f"add{other_kind}RefIndex")(get_handle(other), "2")
    original = other.indices.index
    with pytest.raises(TgiError) as error:
        getattr(api, f"remove{kind}RefIndex")(index_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert other.indices.index is original and resolve_handle(index_id) is original[0]
    for invalid in (get_handle(Index(value="0")), get_handle(UnsignedIntExpression(value="0")), None, [], "missing"):
        with pytest.raises(TgiError) as error:
            getattr(api, f"remove{kind}RefIndex")(invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    register_file = RegisterFileRef(register_file_ref="file", indices=Indices(index=[Index(value="1")]))
    # Ownership established through a shared graph getter cannot bypass the family check.
    from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph

    _register_graph(register_file)
    with pytest.raises(TgiError):
        getattr(api, f"remove{kind}RefIndex")(get_handle(register_file.indices.index[0]))


def test_parsed_root_ownership_schema_round_trip_and_target_resolution():
    root = component()
    xml = XmlDocument.serializer().render(root)
    SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    alias = parsed_source(parsed)
    reference_id = get_handle(alias.register_ref)
    assert api.getRegisterRefAttributeByID(reference_id) == get_handle(
        parsed.memory_maps.memory_map[0].choice[0].choice[3]
    )
    alias.register_ref.register_ref = " \ttarget\n"
    assert api.getRegisterRefAttributeByID(reference_id) == get_handle(
        parsed.memory_maps.memory_map[0].choice[0].choice[3]
    )
    alias.register_ref.register_ref = "target"
    register_index = api.addRegisterRefIndex(reference_id, "0")
    field_index = api.addFieldRefIndex(get_handle(alias.field_ref), "0")
    result = XmlDocument.serializer().render(parsed)
    SCHEMA.assertValid(etree.fromstring(result.encode()))
    reparsed = XmlDocument.parser().from_string(result, Component)
    registry.clear()
    registry.register(reparsed, (reparsed.vendor, reparsed.library, reparsed.name, reparsed.version))
    reparsed_alias = parsed_source(reparsed)
    # Remove parsed children using only their handles and a registered root.
    parsed_register_index = get_handle(reparsed_alias.register_ref.indices.index[0])
    parsed_field_index = get_handle(reparsed_alias.field_ref.indices.index[0])
    assert api.removeRegisterRefIndex(parsed_register_index)
    assert api.removeFieldRefIndex(parsed_field_index)
    assert reparsed_alias.register_ref.indices is None and reparsed_alias.field_ref.indices is None
    assert resolve_handle(parsed_register_index) is None and resolve_handle(parsed_field_index) is None
    assert resolve_handle(register_index) is alias.register_ref.indices.index[0]
    assert resolve_handle(field_index) is alias.field_ref.indices.index[0]


@pytest.mark.parametrize(
    "failure,fault",
    [
        ("missing", TgiFaultCode.NOT_FOUND),
        ("duplicate", TgiFaultCode.INVALID_ARGUMENT),
        ("malformed", TgiFaultCode.INVALID_ID),
    ],
)
def test_target_resolution_missing_ambiguous_and_malformed(failure, fault):
    root = component()
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    source = parsed_source(root).register_ref
    block = root.memory_maps.memory_map[0].choice[0]
    if failure == "missing":
        source.register_ref = "missing"
    elif failure == "duplicate":
        block.choice.append(
            AddressBlockType.Register(
                name="target",
                address_offset=UnsignedLongintExpression(value="2"),
                choice=[UnsignedPositiveIntExpression(value="8")],
            )
        )
    else:
        source.register_ref = "bad Name"
    with pytest.raises(TgiError) as error:
        api.getRegisterRefAttributeByID(get_handle(source))
    assert error.value.fault_code == fault


def test_scoped_register_reference_qualifier_and_wrong_handles():
    root = component()
    second = AddressBlock(
        name="second",
        base_address=BaseAddress(value="16"),
        choice=[
            UnsignedPositiveLongintExpression(value="16"),
            UnsignedPositiveIntExpression(value="8"),
            UsageType.REGISTER,
            AddressBlockType.Register(
                name="target",
                address_offset=UnsignedLongintExpression(value="0"),
                choice=[UnsignedPositiveIntExpression(value="8")],
            ),
        ],
    )
    root.memory_maps.memory_map[0].choice.append(second)
    alias = parsed_source(root)
    alias.address_block_ref = AddressBlockRef(address_block_ref="second")
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    assert api.getRegisterRefAttributeByID(get_handle(alias.register_ref)) == get_handle(second.choice[3])
    for kind, _model, _attribute in CASES:
        for invalid in (None, [], "missing", get_handle(RegisterFileRef(register_file_ref="wrong"))):
            for operation, arguments in (
                (getattr(api, f"get{kind}Ref{kind}RefByName"), (invalid,)),
                (getattr(api, f"get{kind}RefIndexIDs"), (invalid,)),
                (getattr(api, f"add{kind}RefIndex"), (invalid, "0")),
            ):
                with pytest.raises(TgiError) as error:
                    operation(*arguments)
                assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.getRegisterRefAttributeByID(get_handle(FieldRef(field_ref="wrong")))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
