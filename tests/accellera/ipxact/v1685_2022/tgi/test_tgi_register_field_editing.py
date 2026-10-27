"""Register field branch edits and optional removal contracts."""

import inspect

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import register
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressBlockType,
    AddressUnitBits,
    AlternateRegisterRef,
    Array,
    BaseAddress,
    BitStride,
    Component,
    Dim,
    EnumeratedValues,
    EnumeratedValueType,
    EnumeratedValueTypeUsage,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    Parameters,
    RegisterRef,
    Reset,
    UnsignedBitVectorExpression,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
    VendorExtensions,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


def field(choice=None):
    return FieldType(
        name="field",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=choice if choice is not None else [UnsignedPositiveIntExpression(value="8")],
    )


def component(source):
    register_node = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), source],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="16"),
            UnsignedPositiveIntExpression(value="8"),
            UsageType.REGISTER,
            register_node,
        ],
    )
    return Component(
        vendor="acme",
        library="test",
        name="field_edits",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )


@pytest.mark.parametrize(
    "name,parameters",
    [
        ("removeAliasOfAlternateRegisterRef", ["aliasOfID"]),
        ("removeAliasOfRegisterRef", ["aliasOfID"]),
        ("removeRegisterFieldArray", ["registerFieldID"]),
        ("removeRegisterFieldBitWidth", ["registerFieldID"]),
        ("removeUsageAttribute", ["enumeratedValueID"]),
        ("setRegisterFieldAliasOf", ["registerFieldID", "fieldRef"]),
    ],
)
def test_signatures_exports_and_invalid_handles(name, parameters):
    operation = getattr(api, name)
    assert name in register.__all__
    assert list(inspect.signature(operation).parameters) == parameters
    for invalid in (None, [], {}, "missing", get_handle(UnsignedIntExpression(value="0"))):
        with pytest.raises(TgiError) as error:
            operation(*([invalid, "target"] if len(parameters) == 2 else [invalid]))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "attribute,operation",
    [("register_ref", api.removeAliasOfRegisterRef), ("alternate_register_ref", api.removeAliasOfAlternateRegisterRef)],
)
def test_alias_reference_removal_invalidates_only_selected_subtree(attribute, operation):
    index = Index(value="1")
    holder = Indices(index=[index])
    owner = FieldType.AliasOf(
        register_ref=RegisterRef(register_ref="register", indices=holder),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref="alternate"),
        field_ref=FieldRef(field_ref="target"),
    )
    owner_id = get_handle(owner)
    child = getattr(owner, attribute)
    child_id = get_handle(child)
    sibling = owner.field_ref
    sibling_id = get_handle(sibling)
    index_id, holder_id = get_handle(index), get_handle(holder)
    assert operation(owner_id) is True
    assert getattr(owner, attribute) is None and resolve_handle(child_id) is None
    assert resolve_handle(sibling_id) is sibling and owner.field_ref is sibling
    if attribute == "register_ref":
        assert resolve_handle(index_id) is None and resolve_handle(holder_id) is None
    else:
        assert owner.register_ref.indices is holder and resolve_handle(index_id) is index
    assert operation(owner_id) is False


def test_array_removal_handles_typed_field_array_and_descendants():
    source = field()
    dim = Dim(value="4")
    stride = BitStride(value="8")
    source.array = FieldType.Array(dim=(dim,), bit_stride=stride)
    source.parameters = Parameters()
    source.vendor_extensions = VendorExtensions()
    source_id = get_handle(source)
    array_id, dim_id, stride_id = get_handle(source.array), get_handle(dim), get_handle(stride)
    width = source.choice[0]
    assert api.removeRegisterFieldArray(source_id) is True
    assert source.array is None
    assert all(resolve_handle(handle) is None for handle in (array_id, dim_id, stride_id))
    assert source.choice[0] is width and source.parameters is not None and source.vendor_extensions is not None
    assert api.removeRegisterFieldArray(source_id) is False
    source.array = Array()
    with pytest.raises(TgiError) as error:
        api.removeRegisterFieldArray(source_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert isinstance(source.array, Array)


def test_width_removal_preserves_inline_siblings_and_shared_handles():
    width = UnsignedPositiveIntExpression(value="8", minimum=1)
    resets = FieldType.Resets(reset=[Reset(value=UnsignedBitVectorExpression(value="0"))])
    source = field(("Type", width, False, resets))
    width_id, bool_id, resets_id = get_handle(width), get_handle(False), get_handle(resets)
    assert api.removeRegisterFieldBitWidth(get_handle(source)) is True
    assert resolve_handle(width_id) is None
    assert source.choice == ["Type", False, resets]
    assert resolve_handle(bool_id) is False and resolve_handle(resets_id) is resets
    assert api.removeRegisterFieldBitWidth(get_handle(source)) is False
    # Explicit editing permits the intermediate missing-width state; restore with the existing setter.
    assert api.setRegisterFieldBitWidth(get_handle(source), "8")
    assert api.getRegisterFieldBitWidth(get_handle(source)) == 8


@pytest.mark.parametrize(
    "choice",
    [
        [FieldType.AliasOf(field_ref=FieldRef(field_ref="target"))],
        [FieldType.FieldDefinitionRef(value="definition", type_definitions="library")],
    ],
)
def test_width_removal_leaves_noninline_branches_untouched(choice):
    source = field(tuple(choice))
    original = source.choice
    assert api.removeRegisterFieldBitWidth(get_handle(source)) is False
    assert source.choice is original


def test_usage_removal_restores_default_preserves_value_and_shared_enum_handle():
    expression = UnsignedBitVectorExpression(value="2")
    value = EnumeratedValueType(name="state", value=expression, usage=EnumeratedValueTypeUsage.READ)
    value_id, expression_id, usage_id = get_handle(value), get_handle(expression), get_handle(value.usage)
    assert api.removeUsageAttribute(value_id) is True
    assert value.usage is None and api.getEnumeratedValueUsage(value_id) == "read-write"
    assert resolve_handle(expression_id) is expression and resolve_handle(usage_id) is EnumeratedValueTypeUsage.READ
    assert api.removeUsageAttribute(value_id) is False
    value.usage = "read"
    with pytest.raises(TgiError) as error:
        api.removeUsageAttribute(value_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID and value.usage == "read"


def test_alias_assignment_replaces_inline_branch_preserving_field_data_and_metadata():
    width = UnsignedPositiveIntExpression(value="8")
    reset_value = UnsignedBitVectorExpression(value="0")
    resets = FieldType.Resets(reset=[Reset(value=reset_value)])
    policies = FieldType.FieldAccessPolicies(field_access_policy=[FieldType.FieldAccessPolicies.FieldAccessPolicy()])
    enumeration = EnumeratedValues(
        enumeration_definition_ref_or_enumerated_value=[
            EnumeratedValueType(name="zero", value=UnsignedBitVectorExpression(value="0"))
        ]
    )
    source = field(("Type", width, False, resets, policies, enumeration))
    source.array = FieldType.Array(dim=[Dim(value="2")])
    source.parameters = Parameters()
    source.vendor_extensions = VendorExtensions()
    source.id = "source_id"
    source_id = get_handle(source)
    removed = [get_handle(child) for child in (width, resets, reset_value)]
    bool_id = get_handle(False)
    metadata = (source.bit_offset, source.array, source.parameters, source.vendor_extensions)
    assert api.setRegisterFieldAliasOf(source_id, "deferredTarget") is True
    alias_id = api.getRegisterFieldAliasOfID(source_id)
    assert api.getAliasOfFieldRefByName(alias_id) == "deferredTarget"
    assert source.choice == ["Type", resolve_handle(alias_id), policies, enumeration]
    assert all(resolve_handle(handle) is None for handle in removed)
    assert resolve_handle(bool_id) is False
    assert (
        source.id == "source_id"
        and (source.bit_offset, source.array, source.parameters, source.vendor_extensions) == metadata
    )
    assert get_parent_info(alias_id).parent_handle == source_id


def test_alias_assignment_updates_existing_path_and_reference_identity():
    reference = FieldRef(field_ref="old", indices=Indices(index=[Index(value="1")]))
    alias = FieldType.AliasOf(field_ref=reference, register_ref=RegisterRef(register_ref="register"))
    source = field(("Type", alias))
    alias_id, ref_id, index_id = get_handle(alias), get_handle(reference), get_handle(reference.indices.index[0])
    original = source.choice
    assert api.setRegisterFieldAliasOf(get_handle(source), "new") is True
    assert source.choice is original
    assert api.getRegisterFieldAliasOfID(get_handle(source)) == alias_id
    assert api.getAliasOfFieldRefID(alias_id) == ref_id
    assert resolve_handle(index_id) is reference.indices.index[0]
    assert alias.register_ref.register_ref == "register"


@pytest.mark.parametrize("name", ["", "bad Name", False, 1])
def test_alias_assignment_invalid_names_leave_tuple_and_handles_unchanged(name):
    width = UnsignedPositiveIntExpression(value="8")
    source = field((width,))
    original = source.choice
    width_id = get_handle(width)
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldAliasOf(get_handle(source), name)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert source.choice is original and resolve_handle(width_id) is width


def test_definition_to_alias_transition_and_schema_round_trip():
    reference = FieldType.FieldDefinitionRef(value="definition", type_definitions="library")
    source = field((reference,))
    reference_id = get_handle(reference)
    root = component(source)
    assert api.setRegisterFieldAliasOf(get_handle(source), "target") is True
    assert resolve_handle(reference_id) is None
    xml = XmlDocument.serializer().render(root)
    SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_field = parsed.memory_maps.memory_map[0].choice[0].choice[3].choice[1]
    alias_id = api.getRegisterFieldAliasOfID(get_handle(parsed_field))
    assert api.getAliasOfFieldRefByName(alias_id) == "target"
    assert api.setRegisterFieldAliasOf(get_handle(parsed_field), "edited")
    SCHEMA.assertValid(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))


def test_malformed_choice_edits_are_atomic():
    first = UnsignedPositiveIntExpression(value="8")
    second = UnsignedPositiveIntExpression(value="4")
    source = field((first, second))
    original = source.choice
    for operation in (
        lambda: api.removeRegisterFieldBitWidth(get_handle(source)),
        lambda: api.setRegisterFieldAliasOf(get_handle(source), "target"),
    ):
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert source.choice is original and source.choice == (first, second)


def test_usage_removal_serializes_absence_and_parser_materializes_schema_default():
    value = EnumeratedValueType(name="state", value=UnsignedBitVectorExpression(value="0"))
    source = field()
    source.choice.append(EnumeratedValues(enumeration_definition_ref_or_enumerated_value=[value]))
    root = component(source)
    assert value.usage is EnumeratedValueTypeUsage.READ_WRITE
    assert api.removeUsageAttribute(get_handle(value)) is True
    xml = XmlDocument.serializer().render(root)
    element = etree.fromstring(xml.encode())
    SCHEMA.assertValid(element)
    enumerated = element.find(".//{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}enumeratedValue")
    assert enumerated is not None and "usage" not in enumerated.attrib
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_value = (
        parsed.memory_maps.memory_map[0]
        .choice[0]
        .choice[3]
        .choice[1]
        .choice[1]
        .enumeration_definition_ref_or_enumerated_value[0]
    )
    assert api.getEnumeratedValueUsage(get_handle(parsed_value)) == "read-write"
    assert parsed_value.usage is EnumeratedValueTypeUsage.READ_WRITE
    assert api.removeUsageAttribute(get_handle(parsed_value)) is True
    assert api.removeUsageAttribute(get_handle(parsed_value)) is False
