"""Wire requiresDriver choice access preserves identity and mode metadata."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.requires_driver import RequiresDriver
from org.accellera.ipxact.v1685_2022.requires_driver_driver_type import RequiresDriverDriverType
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _make_wire_port():
    root = top_element.createAbstractionDef(
        ("v", "l", "abstraction", "1"), ("v", "l", "bus", "1"), "data", "wire"
    )
    return root, api.getAbstractionDefPortIDs(root)[0]


def test_requires_driver_setter_getters_identity_remove_and_xml():
    root_handle, port_handle = _make_wire_port()
    assert api.getAbstractionDefPortWireRequiresDriver(port_handle) is None
    assert api.getAbstractionDefPortWireRequiresDriverID(port_handle) is None

    assert api.setAbstractionDefPortWireRequiresDriver(port_handle, True)
    wire = resolve_handle(port_handle).wire_or_transactional
    driver = wire.default_value_or_requires_driver
    assert isinstance(driver, RequiresDriver)
    driver.driver_type = RequiresDriverDriverType.CLOCK
    driver_handle = api.getAbstractionDefPortWireRequiresDriverID(port_handle)
    assert driver_handle == get_handle(driver)
    parent = get_parent_info(driver_handle)
    assert parent.parent_handle == get_handle(wire)
    assert parent.path == ("default_value_or_requires_driver",)
    assert parent.container == "single"
    assert api.getAbstractionDefPortWireRequiresDriver(port_handle) is True

    assert api.setAbstractionDefPortWireRequiresDriver(port_handle, False)
    assert wire.default_value_or_requires_driver is driver
    assert driver.value is False
    assert driver.driver_type is RequiresDriverDriverType.CLOCK
    assert api.getAbstractionDefPortWireRequiresDriverID(port_handle) == driver_handle
    assert api.getAbstractionDefPortWireRequiresDriver(port_handle) is False

    parsed = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(resolve_handle(root_handle)), AbstractionDefinition
    )
    assert parsed == resolve_handle(root_handle)

    assert api.removeAbstractionDefPortWireRequiresDriver(port_handle)
    assert api.getAbstractionDefPortWireRequiresDriver(port_handle) is None
    assert api.getAbstractionDefPortWireRequiresDriverID(port_handle) is None
    assert resolve_handle(driver_handle) is None
    assert not api.removeAbstractionDefPortWireRequiresDriver(port_handle)


def test_requires_driver_replaces_expression_and_invalidates_old_handle():
    _root, port_handle = _make_wire_port()
    wire = resolve_handle(port_handle).wire_or_transactional
    expression = UnsignedBitVectorExpression(value="MASK + 1")
    wire.default_value_or_requires_driver = expression
    expression_handle = get_handle(expression)

    assert api.getAbstractionDefPortWireRequiresDriver(port_handle) is None
    assert api.getAbstractionDefPortWireRequiresDriverID(port_handle) is None
    assert api.setAbstractionDefPortWireRequiresDriver(port_handle, True)
    assert resolve_handle(expression_handle) is None
    driver = wire.default_value_or_requires_driver
    assert isinstance(driver, RequiresDriver)
    assert driver.value is True
    assert driver.driver_type is RequiresDriverDriverType.ANY
    assert api.getAbstractionDefPortWireRequiresDriver(port_handle) is True


def test_remove_requires_driver_leaves_default_expression_untouched():
    _root, port_handle = _make_wire_port()
    wire = resolve_handle(port_handle).wire_or_transactional
    expression = UnsignedBitVectorExpression(value="PAYLOAD")
    wire.default_value_or_requires_driver = expression
    expression_handle = get_handle(expression)

    assert not api.removeAbstractionDefPortWireRequiresDriver(port_handle)
    assert wire.default_value_or_requires_driver is expression
    assert resolve_handle(expression_handle) is expression
    assert api.getAbstractionDefPortWireRequiresDriver(port_handle) is None
    assert api.getAbstractionDefPortWireRequiresDriverID(port_handle) is None


@pytest.mark.parametrize("invalid", [1, 0, "true", None])
def test_requires_driver_setter_rejects_non_bool_atomically(invalid):
    _root, port_handle = _make_wire_port()
    assert api.setAbstractionDefPortWireRequiresDriver(port_handle, True)
    wire = resolve_handle(port_handle).wire_or_transactional
    driver = wire.default_value_or_requires_driver
    before_handle = api.getAbstractionDefPortWireRequiresDriverID(port_handle)

    with pytest.raises(TgiError) as error:
        api.setAbstractionDefPortWireRequiresDriver(port_handle, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert wire.default_value_or_requires_driver is driver
    assert driver.value is True
    assert api.getAbstractionDefPortWireRequiresDriverID(port_handle) == before_handle


def test_driver_access_rejects_invalid_handles_and_handles_other_style():
    _root, wire_port_handle = _make_wire_port()
    transactional_root = top_element.createAbstractionDef(
        ("v", "l", "transactional", "1"), ("v", "l", "bus", "1"), "data", "transactional"
    )
    transactional_port_handle = api.getAbstractionDefPortIDs(transactional_root)[0]

    for getter in (
        api.getAbstractionDefPortWireRequiresDriver,
        api.getAbstractionDefPortWireRequiresDriverID,
    ):
        for invalid_handle in ("missing", get_handle(object())):
            with pytest.raises(TgiError) as error:
                getter(invalid_handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert getter(transactional_port_handle) is None

    for invalid_handle in ("missing", get_handle(object())):
        with pytest.raises(TgiError) as error:
            api.setAbstractionDefPortWireRequiresDriver(invalid_handle, True)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.setAbstractionDefPortWireRequiresDriver(transactional_port_handle, True)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT

    assert not api.removeAbstractionDefPortWireRequiresDriver("missing")
    assert not api.removeAbstractionDefPortWireRequiresDriver(transactional_port_handle)
    assert not api.removeAbstractionDefPortWireRequiresDriver(wire_port_handle)


def test_driver_edits_preserve_existing_mode_identities():
    root_handle, port_handle = _make_wire_port()
    modes = {
        name: api.addAbstractionDefPortMode(port_handle, name)
        for name in ("onInitiator", "onTarget", "onSystem")
    }
    api.setOnSystemGroup(modes["onSystem"], "default")
    before = {name: resolve_handle(mode_handle) for name, mode_handle in modes.items()}

    assert api.setAbstractionDefPortWireRequiresDriver(port_handle, True)
    assert api.getAbstractionDefPortWireRequiresDriver(port_handle) is True
    assert api.removeAbstractionDefPortWireRequiresDriver(port_handle)
    for name, mode_handle in modes.items():
        assert resolve_handle(mode_handle) is before[name]

    parsed = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(resolve_handle(root_handle)), AbstractionDefinition
    )
    assert parsed == resolve_handle(root_handle)


def test_integrated_choice_switches_in_both_directions():
    root, port = _make_wire_port()
    assert api.setAbstractionDefPortWireDefaultValue(port, "VALUE + 1")
    expression = api.getAbstractionDefPortWireDefaultValueID(port)
    assert api.setAbstractionDefPortWireRequiresDriver(port, False)
    assert resolve_handle(expression) is None
    assert api.getAbstractionDefPortWireDefaultValueExpression(port) is None
    driver = api.getAbstractionDefPortWireRequiresDriverID(port)
    assert api.getAbstractionDefPortWireRequiresDriver(port) is False
    assert api.setAbstractionDefPortWireDefaultValue(port, "NEXT")
    assert resolve_handle(driver) is None
    assert api.getAbstractionDefPortWireRequiresDriver(port) is None
    assert api.getAbstractionDefPortWireDefaultValueExpression(port) == "NEXT"
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), AbstractionDefinition) == obj
