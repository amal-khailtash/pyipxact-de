"""Generator BASE group and scope getters preserve generated owner boundaries."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import generator as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AbstractorGenerator,
    ComponentGenerator,
    Generator,
    InstanceGeneratorType,
    IpxactUri,
)


@pytest.mark.parametrize("cls", [AbstractorGenerator, ComponentGenerator])
@pytest.mark.parametrize("parsed", [False, True])
def test_groups_and_scope(cls, parsed):
    obj = cls(
        name="g",
        generator_exe=IpxactUri(value="${BIN}/gen"),
        group=[InstanceGeneratorType.Group(value="one"), InstanceGeneratorType.Group(value="two")],
    )
    if parsed:
        obj = XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), cls)
    handle = get_handle(obj)
    getter = api.getAbstractorGeneratorGroupIDs if cls is AbstractorGenerator else api.getComponentGeneratorGroupIDs
    before = XmlDocument.serializer().render(obj)
    ids = getter(handle)
    assert getter(handle) == ids
    assert api.getGeneratorGroups(handle) == ["one", "two"]
    assert api.getGeneratorScope(handle) == "instance"
    if cls is AbstractorGenerator:
        assert api.getAbstractorGeneratorGroup(handle) == "one"
    assert XmlDocument.serializer().render(obj) == before
    assert detach_child_by_handle(ids[0])
    assert resolve_handle(ids[0]) is None
    assert api.getGeneratorGroups(handle) == ["two"]


def test_absent_plain_and_invalid():
    plain = get_handle(Generator(name="g", generator_exe=IpxactUri(value="gen")))
    assert api.getGeneratorGroups(plain) == []
    assert api.getGeneratorScope(plain) is None
    abstract = get_handle(AbstractorGenerator(name="g", generator_exe=IpxactUri(value="gen")))
    assert api.getAbstractorGeneratorGroup(abstract) is None
    for f in [
        api.getAbstractorGeneratorGroup,
        api.getAbstractorGeneratorGroupIDs,
        api.getComponentGeneratorGroupIDs,
        api.getGeneratorGroups,
        api.getGeneratorScope,
    ]:
        with pytest.raises(TgiError):
            f("missing-generator")
