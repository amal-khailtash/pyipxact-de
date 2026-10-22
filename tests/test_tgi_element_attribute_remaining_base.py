"""Remaining source attributes retain schema names through XML reloads."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AbstractionTypes,
    AbstractorType,
    AddressBankType,
    DesignConfiguration,
    MemoryRemapRef,
    ModeRef,
    RegisterFileRef,
    SubspaceMap,
    UnsignedLongintExpression,
)


@pytest.mark.parametrize(
    "function,cls,kwargs,expected",
    [
        (
            "getComponentRefAttribute",
            DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.InterfaceRef,
            {"component_ref": "instance", "bus_ref": "bus"},
            "instance",
        ),
        ("getGroupAttribute", AbstractorType.AbstractorMode, {"value": "system", "group": "mode"}, "mode"),
        (
            "getInitiatorRefAttribute",
            SubspaceMap,
            {
                "name": "space",
                "base_address": UnsignedLongintExpression(value="0"),
                "initiator_ref": "initiator",
                "segment_ref": "segment",
            },
            "initiator",
        ),
        (
            "getInvertAttribute",
            AbstractionTypes.AbstractionType.PortMaps.PortMap,
            {
                "logical_port": AbstractionTypes.AbstractionType.PortMaps.PortMap.LogicalPort(name="data"),
                "invert": True,
            },
            True,
        ),
        ("getMemoryRemapRefAttribute", MemoryRemapRef, {"memory_remap_ref": "remap"}, "remap"),
        ("getPriorityIntAttribute", ModeRef, {"value": "mode", "priority": 3}, 3),
        ("getRegisterFileRefAttribute", RegisterFileRef, {"register_file_ref": "registers"}, "registers"),
        (
            "getSegmentRefAttribute",
            SubspaceMap,
            {
                "name": "space",
                "base_address": UnsignedLongintExpression(value="0"),
                "initiator_ref": "initiator",
                "segment_ref": "segment",
            },
            "segment",
        ),
        (
            "getTypeDefinitionsAttribute",
            AddressBankType.BankDefinitionRef,
            {"value": "definition", "type_definitions": "types"},
            "types",
        ),
    ],
)
def test_remaining_attribute_source(function, cls, kwargs, expected):
    obj = cls(**kwargs)
    getter = getattr(api, function)
    assert getter(get_handle(obj)) == expected
    xml = XmlDocument.serializer().render(obj)
    parsed = XmlDocument.parser().from_string(xml, cls)
    assert getter(get_handle(parsed)) == expected
