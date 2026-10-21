"""Generated clearbox locations preserve HDL source and descendant lifetimes."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import clearbox, component, instantiation
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component


@pytest.mark.parametrize("parsed", [False, True])
def test_generated_paths_and_lifetime(parsed):
    root = Component(vendor="v", library="l", name="c", version="1")
    owner = component.addComponentComponentInstantiation(get_handle(root), "i")
    ref = instantiation.addComponentInstantiationClearboxElementRef(owner, "internal", "top")
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
        owner = component.getComponentComponentInstantiationIDs(get_handle(root))[0]
        ref = instantiation.getComponentInstantiationClearboxElementRefIDs(owner)[0]
    first = clearbox.getClearboxElementRefLocationIDs(ref)[0]
    second = clearbox.addClearboxElementRefLocation(ref, "other")
    sl = clearbox.addLocationSlice(first, "${INSTANCE}")
    segment = get_handle(resolve_handle(sl).path_segments.path_segment[0])
    xml = XmlDocument.serializer().render(root)
    assert XmlDocument.parser().from_string(xml, Component) == root
    # Validate the generated instantiation fragment; target semantic lookup is separate.
    schema_doc = etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")
    ns = "http://www.w3.org/2001/XMLSchema"
    schema_doc.getroot().append(etree.Element(f"{{{ns}}}element", name="testInstantiation",
                                            type="ipxact:componentInstantiationType"))
    schema = etree.XMLSchema(schema_doc)
    fragment = XmlDocument.serializer().render(resolve_handle(owner))
    tree = etree.fromstring(fragment.encode())
    tree.tag = "{http://www.accellera.org/XMLSchema/IPXACT/1685-2022}testInstantiation"
    assert schema.validate(tree), schema.error_log
    assert clearbox.removeClearboxElementRefLocation(first)
    assert resolve_handle(sl) is None
    assert resolve_handle(segment) is None
    assert clearbox.getClearboxElementRefLocationIDs(ref) == [second]
    assert instantiation.removeComponentInstantiationClearboxElementRef(ref)
    assert resolve_handle(second) is None
    assert resolve_handle(ref) is None


@pytest.mark.parametrize("bad", [None, 12, []])
def test_invalid_paths_are_atomic(bad):
    root = Component(vendor="v", library="l", name="c", version="1")
    owner = component.addComponentComponentInstantiation(get_handle(root), "i")
    with pytest.raises(TgiError):
        instantiation.addComponentInstantiationClearboxElementRef(owner, "valid", bad)
    assert resolve_handle(owner).clearbox_element_refs is None
    ref = instantiation.addComponentInstantiationClearboxElementRef(owner, "valid", "top")
    loc = clearbox.getClearboxElementRefLocationIDs(ref)[0]
    with pytest.raises(TgiError):
        clearbox.addClearboxElementRefLocation(ref, bad)
    with pytest.raises(TgiError):
        clearbox.addLocationSlice(loc, bad)
    assert len(resolve_handle(ref).location) == 1
    assert len(resolve_handle(loc).slice) == 1
    with pytest.raises(TgiError):
        instantiation.addComponentInstantiationClearboxElementRef(owner, "invalid name", "top")
