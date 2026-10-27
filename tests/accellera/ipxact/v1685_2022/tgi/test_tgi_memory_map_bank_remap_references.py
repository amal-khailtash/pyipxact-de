"""Bank/remap definition reference source, declaration and target layers."""

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
    AddressBankDefinitionType,
    AddressBankType,
    Bank,
    BankAlignmentType,
    BankDefinitions,
    BankedBankType,
    BankedDefinitionBankType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    LocalAddressBankType,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapDefinitions,
    MemoryRemapDefinitionType,
    MemoryRemapType,
    ModeRef,
    TypeDefinitions,
)

OWNER = ("test", "component", "references", "1")
TARGET = ("test", "types", "references", "1")


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def operations(kind):
    prefix = "getBankBankDefinitionRef" if kind == "Bank" else "getMemoryRemapRemapDefinitionRef"
    return [getattr(api, prefix + suffix) for suffix in ("ByExternalTypeDefID", "ByID", "ByName", "ID")]


def context(kind, *, loaded=True):
    external = ExternalTypeDefinitions(
        name="imported",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=TARGET[0], library=TARGET[1], name=TARGET[2], version=TARGET[3]
        ),
    )
    if kind == "Bank":
        ref = AddressBankType.BankDefinitionRef(value="definition", type_definitions="imported")
        source = Bank(
            name="source", bank_alignment=BankAlignmentType.SERIAL, base_address=BaseAddress(value="0"), choice=(ref,)
        )
        definition = BankDefinitions.BankDefinition(name="definition")
        holder = BankDefinitions(bank_definition=[definition])
        attr = "bank_definitions"
    else:
        ref = MemoryRemapType.RemapDefinitionRef(value="definition", type_definitions="imported")
        source = MemoryRemap(name="source", mode_ref=[ModeRef(value="active", priority=0)], choice=(ref,))
        definition = MemoryRemapDefinitions.MemoryRemapDefinition(name="definition")
        holder = MemoryRemapDefinitions(memory_remap_definition=[definition])
        attr = "memory_remap_definitions"
    owner = Component(
        vendor=OWNER[0],
        library=OWNER[1],
        name=OWNER[2],
        version=OWNER[3],
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=[external]),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[source])]),
    )
    if kind == "Remap":
        owner.modes = ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")])
    target = TypeDefinitions(vendor=TARGET[0], library=TARGET[1], name=TARGET[2], version=TARGET[3], **{attr: holder})
    registry.register(owner, OWNER)
    if loaded:
        registry.register(target, TARGET)
    return owner, source, ref, external, target, definition, holder


@pytest.mark.parametrize("kind", ["Bank", "Remap"])
def test_four_layers_preserve_source_and_actual_ownership(kind):
    _owner, source, ref, external, _target, definition, holder = context(kind)
    declaration, target, name, wrapper = operations(kind)
    ref.value, ref.type_definitions = "  definition  ", "  imported  "
    original = source.choice
    assert declaration(get_handle(source)) == get_handle(external)
    assert target(get_handle(source)) == get_handle(definition)
    assert name(get_handle(source)) == "definition"
    assert wrapper(get_handle(source)) == get_handle(ref)
    assert source.choice is original and ref.value == "  definition  " and ref.type_definitions == "  imported  "
    info = get_parent_info(get_handle(ref))
    assert resolve_handle(info.parent_handle) is source and info.path == ("choice",) and info.container == "list"
    assert resolve_handle(get_parent_info(get_handle(definition)).parent_handle) is holder


@pytest.mark.parametrize("kind", ["Bank", "Remap"])
def test_unloaded_targets_and_missing_declarations_do_not_block_source_getters(kind):
    _owner, source, ref, external, _target, _definition, _holder = context(kind, loaded=False)
    declaration, target, name, wrapper = operations(kind)
    assert name(get_handle(source)) == "definition" and wrapper(get_handle(source)) == get_handle(ref)
    assert declaration(get_handle(source)) == get_handle(external)
    with pytest.raises(TgiError) as error:
        target(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    ref.type_definitions = "missing"
    assert name(get_handle(source)) == "definition" and wrapper(get_handle(source)) == get_handle(ref)
    with pytest.raises(TgiError) as error:
        declaration(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize("kind", ["Bank", "Remap"])
def test_reference_component_schema_validation_and_round_trip(kind):
    owner, _source, _ref, _external, library, definition, _holder = context(kind)
    xml = XmlDocument.serializer().render(owner)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.clear()
    registry.register(parsed, OWNER)
    registry.register(library, TARGET)
    source = parsed.memory_maps.memory_map[0].choice[0]
    declaration, target, name, wrapper = operations(kind)
    assert name(get_handle(source)) == "definition"
    assert target(get_handle(source)) == get_handle(definition)
    assert wrapper(get_handle(source)) == get_handle(source.choice[0])
    assert declaration(get_handle(source)) == get_handle(parsed.type_definitions.external_type_definitions[0])
    assert schema.validate(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))


@pytest.mark.parametrize("kind", ["Bank", "Remap"])
def test_missing_and_ambiguous_targets_and_declarations_are_scoped(kind):
    owner, source, ref, external, _target, definition, holder = context(kind)
    declaration, target, name, wrapper = operations(kind)
    ref.value = "missing"
    with pytest.raises(TgiError) as error:
        target(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    ref.value = "definition"
    values = holder.bank_definition if kind == "Bank" else holder.memory_remap_definition
    values.append(type(definition)(name="definition"))
    with pytest.raises(TgiError) as error:
        target(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    values.pop()
    owner.type_definitions.external_type_definitions.append(external)
    with pytest.raises(TgiError) as error:
        declaration(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert name(get_handle(source)) == "definition" and wrapper(get_handle(source)) == get_handle(ref)


@pytest.mark.parametrize("kind", ["Bank", "Remap"])
@pytest.mark.parametrize("field,value", [("value", "bad name"), ("type_definitions", ""), ("value", 4)])
def test_malformed_stored_names_fault_in_all_layers(kind, field, value):
    _owner, source, ref, _external, _target, _definition, _holder = context(kind)
    setattr(ref, field, value)
    for op in operations(kind):
        with pytest.raises(TgiError):
            op(get_handle(source))


@pytest.mark.parametrize("kind", ["Bank", "Remap"])
def test_foreign_conflicting_duplicate_choices_fault_without_mutation(kind):
    _owner, source, ref, _external, _target, _definition, _holder = context(kind)
    for values in (None, {}, (object(),), (ref, ref), (ref, BaseAddress(value="0"))):
        source.choice = values
        for op in operations(kind):
            with pytest.raises(TgiError):
                op(get_handle(source))
            assert source.choice is values


@pytest.mark.parametrize(
    "model",
    [AddressBankType, BankedBankType, AddressBankType.Bank, AddressBankDefinitionType, BankedDefinitionBankType],
)
def test_bank_variants_have_source_access_without_containing_document(model):
    ref = model.BankDefinitionRef(value="definition", type_definitions="imported")
    kwargs = {"base_address": BaseAddress(value="0")} if model in (AddressBankType, AddressBankDefinitionType) else {}
    source = model(name="source", bank_alignment=BankAlignmentType.SERIAL, choice=(ref,), **kwargs)
    declaration, target, name, wrapper = operations("Bank")
    assert name(get_handle(source)) == "definition" and wrapper(get_handle(source)) == get_handle(ref)
    for op in (declaration, target):
        with pytest.raises(TgiError):
            op(get_handle(source))
    source.choice = ()
    for op in operations("Bank"):
        assert op(get_handle(source)) is None


@pytest.mark.parametrize("kind", ["Bank", "Remap"])
def test_exact_parameters_scope_and_inline_absence(kind):
    _owner, source, _ref, _external, _target, _definition, _holder = context(kind)
    source.choice = ()
    parameter = "bankID" if kind == "Bank" else "memoryRemapID"
    foreign = LocalAddressBankType(
        name="local", bank_alignment=BankAlignmentType.SERIAL, base_address=BaseAddress(value="0")
    )
    for op in operations(kind):
        assert list(signature(op).parameters) == [parameter]
        assert op(get_handle(source)) is None
        for invalid in (None, 7, "missing", get_handle(foreign), get_handle(MemoryMapType(name="map"))):
            with pytest.raises(TgiError) as error:
                op(invalid)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", ["Bank", "Remap"])
def test_unrelated_library_and_foreign_reference_models_are_excluded(kind):
    _owner, source, _ref, _external, library, _definition, _holder = context(kind, loaded=False)
    library.name = "decoy"
    registry.register(library, (TARGET[0], TARGET[1], "decoy", TARGET[3]))
    with pytest.raises(TgiError) as error:
        operations(kind)[1](get_handle(source))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    source.choice = (BankedBankType.BankDefinitionRef(value="definition", type_definitions="imported"),)
    for op in operations(kind):
        with pytest.raises(TgiError) as error:
            op(get_handle(source))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    if kind == "Remap":
        foreign = MemoryRemapDefinitionType(name="definition")
        for op in operations(kind):
            with pytest.raises(TgiError) as error:
                op(get_handle(foreign))
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
