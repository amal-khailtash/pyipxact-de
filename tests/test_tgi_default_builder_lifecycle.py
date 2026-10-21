"""Default builders retain typed owner boundaries and descendant lifetimes."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component, file_builder, file_set, instantiation
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, FileBuilderType, FileSet, FileType, SimpleFileType


def operations(kind):
    """Return creator/traversal/removal operations for one owner category."""
    module = instantiation if kind == "Instantiation" else file_set
    prefix = "ComponentInstantiation" if kind == "Instantiation" else "FileSet"
    return tuple(getattr(module, f"{verb}{prefix}DefaultFileBuilder{suffix}")
                 for verb, suffix in (("add", ""), ("get", "IDs"), ("remove", "")))


@pytest.mark.parametrize("kind", ["Instantiation", "FileSet"])
@pytest.mark.parametrize("parsed", [False, True])
def test_default_builder_xml_and_removal(kind, parsed):
    root = Component(vendor="v", library="l", name="c", version="1")
    owner = (component.addComponentComponentInstantiation(get_handle(root), "i") if kind == "Instantiation"
             else get_handle(FileSet(name="sources")))
    create, getter, remove = operations(kind)
    first = create(owner, "vhdlSource")
    second = create(owner, "user")
    resolve_handle(second).file_type.user = "custom-hdl"
    file_builder.setFileBuilderCommand(first, "cc ${SOURCE}")
    command = get_handle(resolve_handle(first).command)
    if kind == "FileSet":
        source = resolve_handle(owner)
        xml = XmlDocument.serializer().render(source)
        cls = FileSet
    else:
        source = root
        xml = XmlDocument.serializer().render(root)
        cls = Component
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    reloaded = XmlDocument.parser().from_string(xml, cls)
    if parsed:
        owner = (component.getComponentComponentInstantiationIDs(get_handle(reloaded))[0]
                 if kind == "Instantiation" else get_handle(reloaded))
        first, second = getter(owner)
        command = get_handle(resolve_handle(first).command)
    other_remove = operations("FileSet" if kind == "Instantiation" else "Instantiation")[2]
    with pytest.raises(TgiError):
        other_remove(first)
    assert getter(owner) == [first, second]
    assert remove(first)
    assert resolve_handle(command) is None
    assert resolve_handle(first) is None
    assert getter(owner) == [second]
    assert resolve_handle(second).file_type.user == "custom-hdl"
    with pytest.raises(TgiError):
        remove(first)
    assert not remove(get_handle(FileBuilderType(file_type=FileType(value=SimpleFileType.USER))))


@pytest.mark.parametrize("kind", ["Instantiation", "FileSet"])
def test_invalid_file_type_is_atomic(kind):
    owner = (component.addComponentComponentInstantiation(
        get_handle(Component(vendor="v", library="l", name="c", version="1")), "i")
        if kind == "Instantiation" else get_handle(FileSet(name="sources")))
    create, getter, _ = operations(kind)
    for invalid in ("", "custom-hdl", None, True, 123, []):
        with pytest.raises(TgiError):
            create(owner, invalid)
        assert getter(owner) == []
