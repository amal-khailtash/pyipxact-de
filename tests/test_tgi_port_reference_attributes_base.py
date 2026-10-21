"""Element attribute BASE port/field references preserve source names."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ExternalPortReference,
    FieldRef,
    MemoryMapRefType,
    QualifierType,
    SubPortReference,
)


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        ("getPortRefAttribute", ExternalPortReference(port_ref="port"), "port"),
        ("getSubPortRefAttribute", SubPortReference(sub_port_ref="sub"), "sub"),
        ("getFieldRefAttribute", FieldRef(field_ref="field"), "field"),
        ("getMemoryMapRefAttribute", MemoryMapRefType(memory_map_ref="memory"), "memory"),
        ("getPowerDomainRefAttribute", QualifierType.IsPowerEn(value=True, power_domain_ref="power"), "power"),
    ],
)
def test_port_reference_attribute(name, obj, expected):
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) == expected
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == expected
    assert getattr(tgi, name) is getter
    assert XmlDocument.serializer().render(obj) == before
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")


def test_optional_power_reference():
    assert api.getPowerDomainRefAttribute(get_handle(QualifierType.IsPowerEn(value=True))) is None
