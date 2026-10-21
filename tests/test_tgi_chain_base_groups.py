"""BASE selector traversal preserves choice alternatives and group-name lifetime."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import generator_chain as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ConfigurableLibraryRefType,
    GeneratorChain,
    GeneratorSelectorType,
    GroupSelector,
)


@pytest.mark.parametrize("chain_selector", [False, True])
@pytest.mark.parametrize("parsed", [False, True])
def test_group_source_and_lifetime(chain_selector, parsed):
    group = GroupSelector(name=[GroupSelector.Name(value="first"), GroupSelector.Name(value="second")])
    obj = (
        GeneratorChain.GeneratorChainSelector(group_selector_or_generator_chain_ref=group)
        if chain_selector
        else GeneratorSelectorType(group_selector=group)
    )
    root = GeneratorChain(
        vendor="v",
        library="l",
        name="chain",
        version="1",
        generator_chain_selector_or_component_generator_selector_or_generator=[obj],
    )
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), GeneratorChain)
        obj = root.generator_chain_selector_or_component_generator_selector_or_generator[0]
    handle = get_handle(obj)
    getter = (
        api.getGeneratorChainSelectorGroupSelectorID
        if chain_selector
        else api.getComponentGeneratorSelectorGroupSelectorID
    )
    group_id = getter(handle)
    assert getter(handle) == group_id
    before = XmlDocument.serializer().render(root)
    assert api.getGroupSelectorSelectionNames(group_id) == ["first", "second"]
    assert api.getGroupSelectorSelectionOperator(group_id) == "or"
    ids = api.getGroupSelectorNameIDs(group_id)
    assert api.getGroupSelectorNameIDs(group_id) == ids
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(ids[0])
    assert api.getGroupSelectorSelectionNames(group_id) == ["second"]
    assert detach_child_by_handle(group_id)
    assert resolve_handle(ids[1]) is None
    assert getter(handle) is None


def test_reference_alternative_and_wrong_handles():
    ref = ConfigurableLibraryRefType(vendor="v", library="l", name="target", version="1")
    handle = get_handle(GeneratorChain.GeneratorChainSelector(group_selector_or_generator_chain_ref=ref))
    assert api.getGeneratorChainSelectorGroupSelectorID(handle) is None
    assert resolve_handle(handle).group_selector_or_generator_chain_ref is ref
    for f in [
        api.getComponentGeneratorSelectorGroupSelectorID,
        api.getGeneratorChainSelectorGroupSelectorID,
        api.getGroupSelectorNameIDs,
        api.getGroupSelectorSelectionNames,
        api.getGroupSelectorSelectionOperator,
    ]:
        with pytest.raises(TgiError):
            f("missing-group-selector")
