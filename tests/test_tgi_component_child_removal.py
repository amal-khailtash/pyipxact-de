"""Standard single-child component removers restore ownership from parsed roots."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component

CLOCK = '''<clockPeriod>10</clockPeriod><clockPulseOffset>0</clockPulseOffset>
<clockPulseValue>1</clockPulseValue><clockPulseDuration>5</clockPulseDuration>'''
SPECS = [
    ("Port", "Port", 'model/ports', '<port><name>{name}</name><wire><direction>in</direction></wire></port>'),
    ("FileSet", "FileSet", 'fileSets', '<fileSet><name>{name}</name></fileSet>'),
    ("MemoryMap", "MemoryMap", 'memoryMaps', '<memoryMap><name>{name}</name></memoryMap>'),
    ("ResetType", "ResetType", 'resetTypes', '<resetType><name>{name}</name></resetType>'),
    ("OtherClockDriver", "OtherClockDriver", 'otherClockDrivers',
     '<otherClockDriver clockName="{name}">'+CLOCK+'</otherClockDriver>'),
]


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def make_root(path, template):
    body = template.format(name="first") + template.format(name="second")
    for tag in reversed(path.split('/')):
        body = f'<{tag}>{body}</{tag}>'
    xml = '<component xmlns="http://www.accellera.org/XMLSchema/IPXACT/1685-2022">' \
          '<vendor>v</vendor><library>l</library><name>c</name><version>1</version>'+body+'</component>'
    return XmlDocument.parser().from_string(xml, Component)


@pytest.mark.parametrize("name,getter,path,template", SPECS)
def test_parsed_removal_identity_descendants_and_siblings(name, getter, path, template):
    root = make_root(path, template)
    root_id = get_handle(root)
    ids = getattr(api, f'getComponent{getter}IDs')(root_id)
    first, second = ids
    child = resolve_handle(first)
    descendant = child.wire_or_transactional_or_structured if name == "Port" else (
        child.clock_period if name == "OtherClockDriver" else None
    )
    descendant_id = get_handle(descendant) if descendant is not None else None
    assert getattr(api, f'removeComponent{name}')(first)
    assert resolve_handle(first) is None
    if descendant_id is not None:
        assert resolve_handle(descendant_id) is None
    assert resolve_handle(second) is not None
    assert getattr(api, f'getComponent{getter}IDs')(root_id) == [second]
    assert not getattr(api, f'removeComponent{name}')(first)
    loaded = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
    assert loaded == root


@pytest.mark.parametrize("name,getter,path,template", SPECS)
def test_wrong_root_handle_and_absent_id_are_atomic(name, getter, path, template):
    root = make_root(path, template)
    root_id = get_handle(root)
    before = XmlDocument.serializer().render(root)
    remover = getattr(api, f'removeComponent{name}')
    assert not remover("missing")
    with pytest.raises(TgiError):
        remover(root_id)
    assert XmlDocument.serializer().render(root) == before
