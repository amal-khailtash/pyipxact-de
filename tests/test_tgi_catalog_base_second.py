"""Catalog BASE categories support standard handles and parsed ownership."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import catalog as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Catalog, IpxactFilesType, IpxactFileType, IpxactUri, LibraryRefType


@pytest.mark.parametrize(
    "kind,field",
    [
        ("DesignConfigurations", "design_configurations"),
        ("Designs", "designs"),
        ("GeneratorChains", "generator_chains"),
        ("TypeDefinitions", "type_definitions"),
    ],
)
@pytest.mark.parametrize("parsed", [False, True])
def test_base_category_handle_and_lifetime(kind, field, parsed):
    root = Catalog(vendor="v", library="l", name="catalog", version="1")
    getter = getattr(api, f"getCatalog{kind}IpxactFileIDs")
    assert getter(get_handle(root)) == []
    entries = [
        IpxactFileType(
            name=IpxactUri(value=f"{n}.xml"), vlnv=LibraryRefType(vendor="v", library="l", name=n, version="1")
        )
        for n in ["first", "second"]
    ]
    setattr(root, field, IpxactFilesType(ipxact_file=entries))
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    if parsed:
        root = XmlDocument.parser().from_string(xml, Catalog)
    handle = get_handle(root)
    ids = getter(handle)
    assert getter(root) == ids
    assert [resolve_handle(h).name.value for h in ids] == ["first.xml", "second.xml"]
    before = XmlDocument.serializer().render(root)
    assert getter(handle) == ids
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(ids[0])
    assert resolve_handle(ids[0]) is None
    assert getter(handle) == [ids[1]]
    for invalid in ["missing-catalog", get_handle(getattr(root, field))]:
        with pytest.raises(TgiError):
            getter(invalid)


def test_file_metadata_standard_handles():
    entry = IpxactFileType(
        name=IpxactUri(value="${ROOT}/path%20name.xml"),
        vlnv=LibraryRefType(vendor="v:part", library="lib", name="n", version="1"),
    )
    handle = get_handle(entry)
    assert api.getIpxactFileName(handle) == "${ROOT}/path%20name.xml"
    assert api.getIpxactFileName(entry) == "${ROOT}/path%20name.xml"
    assert api.getIpxactFileVlnvRefByVLNV(handle) == ("v:part", "lib", "n", "1")
    assert api.getIpxactFileVlnvRefByVLNV(entry) == ("v:part", "lib", "n", "1")
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(entry), IpxactFileType)
    assert api.getIpxactFileVlnvRefByVLNV(get_handle(parsed)) == ("v:part", "lib", "n", "1")
    for getter in (api.getIpxactFileName, api.getIpxactFileVlnvRefByVLNV):
        with pytest.raises(TgiError):
            getter("missing-entry")
        with pytest.raises(TgiError):
            getter(get_handle(entry.name))
