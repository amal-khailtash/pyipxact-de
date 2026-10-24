"""Generator-chain extended TGI edits preserve parsed IP-XACT schema models."""

import pytest
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022.tgi import generator_chain as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from org.accellera.ipxact.v1685_2022 import BusDefinition, Generator, GeneratorChain, IpxactUri

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


def _parsed_chain() -> GeneratorChain:
    source = GeneratorChain(
        vendor="acme",
        library="flow",
        name="chain",
        version="1.0",
        generator_chain_selector_or_component_generator_selector_or_generator=[
            Generator(name="seed", generator_exe=IpxactUri(value="bin/seed"))
        ],
    )
    xml = XmlSerializer().render(source)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    return XmlParser().from_string(xml, GeneratorChain)


def _assert_valid(chain: GeneratorChain) -> str:
    xml = XmlSerializer().render(chain)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    return xml


def test_generator_chain_mutations_and_traversal_on_parsed_document():
    registry.clear()
    chain = _parsed_chain()
    chain_id = get_handle(chain)
    seed_generator_id = api.getGeneratorChainGeneratorIDs(chain_id)[0]

    assert api.addGeneratorChainChainGroup(chain_id, "flow") is True
    group_id = api.getGeneratorChainChainGroupIDs(chain_id)[0]
    assert api.addGeneratorChainChainGroup(chain_id, "flow") is True
    equal_group_sibling_id = api.getGeneratorChainChainGroupIDs(chain_id)[1]
    choice_id = api.addGeneratorChainChoice(chain_id, "mode", ["fast", "safe"])
    component_selector_id = api.addGeneratorChainComponentGeneratorSelector(chain_id, "cpu")
    generator_id = api.addGeneratorChainGenerator(chain_id, "compile", "bin/compile")
    chain_selector_id = api.addGeneratorChainGeneratorChainSelector(chain_id, "subflow")

    assert api.getGeneratorChainChoiceIDs(chain_id) == [choice_id]
    assert api.getGeneratorChainComponentGeneratorSelectorIDs(chain_id) == [component_selector_id]
    assert api.getGeneratorChainGeneratorIDs(chain_id) == [seed_generator_id, generator_id]
    assert api.getGeneratorChainGeneratorChainSelectorIDs(chain_id) == [chain_selector_id]
    assert api.getGroupSelectorSelectionNames(
        api.getComponentGeneratorSelectorGroupSelectorID(component_selector_id)
    ) == ["cpu"]

    choice = resolve_handle(choice_id)
    assert choice.name == "mode"
    assert [item.value for item in choice.enumeration] == ["fast", "safe"]
    group_selector_id = api.getGeneratorChainSelectorGroupSelectorID(chain_selector_id)
    original_name_id = api.getGroupSelectorNameIDs(group_selector_id)[0]
    assert api.getGroupSelectorSelectionOperator(group_selector_id) == "or"

    component_group_id = api.getComponentGeneratorSelectorGroupSelectorID(component_selector_id)
    component_name_id = api.getGroupSelectorNameIDs(component_group_id)[0]
    assert api.setComponentGeneratorSelectorGroupSelector(component_selector_id, ["accelerator", "cpu"]) is True
    assert resolve_handle(component_group_id) is None
    assert resolve_handle(component_name_id) is None
    replacement_component_group_id = api.getComponentGeneratorSelectorGroupSelectorID(component_selector_id)
    assert api.getGroupSelectorSelectionNames(replacement_component_group_id) == ["accelerator", "cpu"]

    target = GeneratorChain(vendor="acme", library="flow", name="target", version="2.0")
    target_id = get_handle(target)
    registry.register(target, (target.vendor, target.library, target.name, target.version))
    assert api.setGeneratorChainSelectorGeneratorChainRef(chain_selector_id, ("acme", "flow", "target", "2.0"))
    assert resolve_handle(group_selector_id) is None
    assert resolve_handle(original_name_id) is None
    assert api.getGeneratorChainSelectorGeneratorChainRefByVLNV(chain_selector_id) == (
        "acme",
        "flow",
        "target",
        "2.0",
    )
    assert api.getGeneratorChainSelectorGeneratorChainRefByID(chain_selector_id) == target_id

    # Replacing the reference with a groupSelector invalidates the old reference handle.
    ref_id = get_handle(resolve_handle(chain_selector_id).group_selector_or_generator_chain_ref)
    assert api.setGeneratorChainSelectorGroupSelector(chain_selector_id, ["subflow", "common"]) is True
    assert resolve_handle(ref_id) is None
    selected_group_id = api.getGeneratorChainSelectorGroupSelectorID(chain_selector_id)
    assert api.getGroupSelectorSelectionNames(selected_group_id) == ["subflow", "common"]
    assert api.getGroupSelectorSelectionOperator(selected_group_id) == "or"
    added_name_id = api.addGroupSelectorName(selected_group_id, "shared")
    assert api.getGroupSelectorSelectionNames(selected_group_id) == ["subflow", "common", "shared"]
    assert api.removeGroupSelectorName(added_name_id) is True
    assert resolve_handle(added_name_id) is None

    # Component selector group replacement uses the same schema choice path.
    name_ids = api.getGroupSelectorNameIDs(replacement_component_group_id)
    assert api.removeGroupSelectorName(name_ids[0]) is True
    with pytest.raises(TgiError) as last_name_error:
        api.removeGroupSelectorName(name_ids[1])
    assert last_name_error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getGroupSelectorSelectionNames(replacement_component_group_id) == ["cpu"]

    xml = _assert_valid(chain)
    reparsed = XmlParser().from_string(xml, GeneratorChain)
    assert reparsed.chain_group[0].value == "flow"
    assert reparsed.choices.choice[0].enumeration[1].value == "safe"
    assert (
        reparsed.generator_chain_selector_or_component_generator_selector_or_generator[-1]
        .group_selector_or_generator_chain_ref.name[0]
        .value
        == "subflow"
    )

    # Every removal uses its standard handle type and invalidates descendants.
    assert api.removeGeneratorChainChainGroup(group_id) is True
    assert api.getGeneratorChainChainGroupIDs(chain_id) == [equal_group_sibling_id]
    assert api.removeGeneratorChainChainGroup(equal_group_sibling_id) is True
    assert api.removeGeneratorChainChoice(choice_id) is True
    assert resolve_handle(choice_id) is None
    assert api.removeGeneratorChainComponentGeneratorSelector(component_selector_id) is True
    assert resolve_handle(replacement_component_group_id) is None
    assert api.removeGeneratorChainGenerator(generator_id) is True
    assert api.removeGeneratorChainGeneratorChainSelector(chain_selector_id) is True
    assert resolve_handle(selected_group_id) is None
    assert api.getGeneratorChainChainGroupIDs(chain_id) == []
    assert api.getGeneratorChainChoiceIDs(chain_id) == []
    assert api.getGeneratorChainComponentGeneratorSelectorIDs(chain_id) == []
    assert api.getGeneratorChainGeneratorIDs(chain_id) == [seed_generator_id]
    assert api.getGeneratorChainGeneratorChainSelectorIDs(chain_id) == []
    _assert_valid(chain)


def test_generator_chain_choice_creation_validates_before_mutating():
    chain = _parsed_chain()
    chain_id = get_handle(chain)

    for name, values in (("mode", []), ("mode", ["valid", 4]), (None, ["valid"])):
        with pytest.raises(TgiError) as error:
            api.addGeneratorChainChoice(chain_id, name, values)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert chain.choices is None
        _assert_valid(chain)

    with pytest.raises(TgiError) as error:
        api.setGeneratorChainSelectorGeneratorChainRef("missing", ("v", "l", "n", "1"))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_generator_chain_setters_reject_invalid_values_without_partial_edits():
    chain = _parsed_chain()
    chain_id = get_handle(chain)
    component_selector_id = api.addGeneratorChainComponentGeneratorSelector(chain_id, "cpu")
    chain_selector_id = api.addGeneratorChainGeneratorChainSelector(chain_id, "subflow")
    component_group_id = api.getComponentGeneratorSelectorGroupSelectorID(component_selector_id)
    chain_group_id = api.getGeneratorChainSelectorGroupSelectorID(chain_selector_id)

    invalid_edits = (
        (api.setComponentGeneratorSelectorGroupSelector, component_selector_id, []),
        (api.setGeneratorChainSelectorGroupSelector, chain_selector_id, []),
        (api.setGeneratorChainSelectorGeneratorChainRef, chain_selector_id, ("acme", "flow", "target")),
        (api.setGeneratorChainSelectorGeneratorChainRef, chain_selector_id, ("acme", "flow", "", "1")),
    )
    for operation, handle, value in invalid_edits:
        with pytest.raises(TgiError) as error:
            operation(handle, value)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT

    assert api.getComponentGeneratorSelectorGroupSelectorID(component_selector_id) == component_group_id
    assert api.getGeneratorChainSelectorGroupSelectorID(chain_selector_id) == chain_group_id
    assert api.getGroupSelectorSelectionNames(component_group_id) == ["cpu"]
    assert api.getGroupSelectorSelectionNames(chain_group_id) == ["subflow"]
    _assert_valid(chain)


def test_generator_chain_ref_by_id_requires_registered_chain_target():
    registry.clear()
    chain = _parsed_chain()
    selector_id = api.addGeneratorChainGeneratorChainSelector(get_handle(chain), "next")
    with pytest.raises(TgiError) as absent_error:
        api.getGeneratorChainSelectorGeneratorChainRefByID(selector_id)
    assert absent_error.value.fault_code == TgiFaultCode.NOT_FOUND

    target = BusDefinition(
        vendor="acme",
        library="bus",
        name="wrong",
        version="1",
        direct_connection=True,
        is_addressable=False,
    )
    registry.register(target, (target.vendor, target.library, target.name, target.version))
    assert api.setGeneratorChainSelectorGeneratorChainRef(selector_id, ("acme", "bus", "wrong", "1"))
    with pytest.raises(TgiError) as wrong_type_error:
        api.getGeneratorChainSelectorGeneratorChainRefByID(selector_id)
    assert wrong_type_error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize(
    ("operation", "handle"),
    [
        (api.getGeneratorChainChainGroupIDs, "missing"),
        (api.getGeneratorChainChoiceIDs, "missing"),
        (api.getGeneratorChainComponentGeneratorSelectorIDs, "missing"),
        (api.getGeneratorChainGeneratorChainSelectorIDs, "missing"),
        (api.getGeneratorChainGeneratorIDs, "missing"),
        (api.getGroupSelectorSelectionNames, "missing"),
    ],
)
def test_generator_chain_base_operations_reject_invalid_handles(operation, handle):
    with pytest.raises(TgiError) as error:
        operation(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_generator_chain_removers_reject_wrong_types_and_unowned_objects():
    chain = _parsed_chain()
    api.addGeneratorChainChainGroup(get_handle(chain), "flow")
    group_id = api.getGeneratorChainChainGroupIDs(get_handle(chain))[0]
    unrelated = GeneratorChain.ChainGroup(value="unowned")
    unrelated_id = get_handle(unrelated)
    choice_id = api.addGeneratorChainChoice(get_handle(chain), "mode", ["fast"])

    with pytest.raises(TgiError) as wrong_type_error:
        api.removeGeneratorChainChainGroup(choice_id)
    assert wrong_type_error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as unowned_error:
        api.removeGeneratorChainChainGroup(unrelated_id)
    assert unowned_error.value.fault_code == TgiFaultCode.INVALID_ID
    assert api.getGeneratorChainChainGroupIDs(get_handle(chain)) == [group_id]
    assert api.getGeneratorChainChoiceIDs(get_handle(chain)) == [choice_id]
