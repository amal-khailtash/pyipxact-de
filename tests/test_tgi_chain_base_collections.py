"""Generator-chain BASE traversal filters generated mixed choices by type."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import generator_chain as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Choices,
    Generator,
    GeneratorChain,
    GeneratorSelectorType,
    GroupSelector,
    IpxactUri,
)


@pytest.mark.parametrize(
    "kind", ["ChainGroup", "Choice", "ComponentGeneratorSelector", "GeneratorChainSelector", "Generator"]
)
@pytest.mark.parametrize("parsed", [False, True])
def test_mixed_collections(kind, parsed):
    group = GroupSelector(name=[GroupSelector.Name(value="group")])
    chain = GeneratorChain(
        vendor="v",
        library="l",
        name="chain",
        version="1",
        chain_group=[GeneratorChain.ChainGroup(value="a"), GeneratorChain.ChainGroup(value="b")],
        choices=Choices(choice=[Choices.Choice(name="mode", enumeration=[Choices.Choice.Enumeration(value="one")])]),
        generator_chain_selector_or_component_generator_selector_or_generator=[
            Generator(name="g1", generator_exe=IpxactUri(value="gen")),
            GeneratorChain.GeneratorChainSelector(group_selector_or_generator_chain_ref=group),
            GeneratorSelectorType(group_selector=group),
            Generator(name="g2", generator_exe=IpxactUri(value="gen2")),
        ],
    )
    xml = XmlDocument.serializer().render(chain)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    if parsed:
        chain = XmlDocument.parser().from_string(xml, GeneratorChain)
    handle = get_handle(chain)
    getter = getattr(api, f"getGeneratorChain{kind}IDs")
    ids = getter(handle)
    assert len(ids) == (2 if kind in ["Generator", "ChainGroup"] else 1)
    assert getter(handle) == ids
    before = XmlDocument.serializer().render(chain)
    assert getter(handle) == ids
    assert XmlDocument.serializer().render(chain) == before
    assert detach_child_by_handle(ids[0])
    assert resolve_handle(ids[0]) is None
    assert getter(handle) == ids[1:]
    with pytest.raises(TgiError):
        getter("missing-chain")
