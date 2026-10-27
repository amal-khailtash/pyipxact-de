"""Field-definition width, type identifier and volatility contracts."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import register as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import FieldDefinitions, TypeDefinitions, UnsignedPositiveIntExpression

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_OPERATIONS = [
    ("getFieldDefinitionBitWidthID", "F.7.73.39", False),
    ("getFieldDefinitionTypeIdentifier", "F.7.73.41", False),
    ("getFieldDefinitionVolatile", "F.7.73.42", False),
    ("setFieldDefinitionBitWidth", "F.7.74.52", True),
    ("setFieldDefinitionTypeIdentifier", "F.7.74.53", True),
    ("setFieldDefinitionVolatile", "F.7.74.54", True),
]


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field() -> FieldDefinitions.FieldDefinition:
    return FieldDefinitions.FieldDefinition(name="status", bit_width=UnsignedPositiveIntExpression(value="8"))


@pytest.mark.parametrize("name,section,setter", _OPERATIONS)
def test_contract_and_wrong_handles(name: str, section: str, setter: bool) -> None:
    function = getattr(api, name)
    assert name in api.__all__
    assert getattr(tgi, name) is function
    assert list(inspect.signature(function).parameters) == (
        ["fieldDefinitionID", "value"] if setter else ["fieldDefinitionID"]
    )
    assert f"Section: {section}." in function.__doc__
    for handle in ("missing", get_handle(UnsignedPositiveIntExpression(value="8")), None):
        with pytest.raises(TgiError) as error:
            function(handle, True if name.endswith("Volatile") else "8") if setter else function(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_defaults_explicit_booleans_and_optional_identifier() -> None:
    field = _field()
    handle = get_handle(field)
    assert api.getFieldDefinitionTypeIdentifier(handle) is None
    assert api.getFieldDefinitionVolatile(handle) is False
    assert field.volatile is None
    assert api.setFieldDefinitionTypeIdentifier(handle, "status_type") is True
    assert api.getFieldDefinitionTypeIdentifier(handle) == "status_type"
    for value in (True, False):
        assert api.setFieldDefinitionVolatile(handle, value) is True
        assert field.volatile is value
        assert api.getFieldDefinitionVolatile(handle) is value


def test_width_edits_preserve_wrapper_metadata_and_owned_handle() -> None:
    field = _field()
    width = field.bit_width
    width.minimum, width.maximum = 2, 64
    width.other_attributes = {"{urn:test}marker": "width"}
    field.type_identifier = "status_type"
    field.volatile = True
    handle = get_handle(field)
    width_id = api.getFieldDefinitionBitWidthID(handle)
    assert get_parent_info(width_id).parent_handle == handle
    for source in ("16", "WIDTH + 1"):
        assert api.setFieldDefinitionBitWidth(handle, source) is True
        assert field.bit_width is width and width.value == source
        assert api.getFieldDefinitionBitWidthID(handle) == width_id
        assert resolve_handle(width_id) is width
    assert (width.minimum, width.maximum) == (2, 64)
    assert width.other_attributes == {"{urn:test}marker": "width"}
    assert field.type_identifier == "status_type" and field.volatile is True


@pytest.mark.parametrize("source", ["0", "-1", "64'd4294967296", "1 +", "", None, True])
def test_bad_width_rolls_back(source) -> None:
    field = _field()
    width = field.bit_width
    with pytest.raises(TgiError) as error:
        api.setFieldDefinitionBitWidth(get_handle(field), source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.bit_width is width and width.value == "8"


@pytest.mark.parametrize("source", ["1", "65"])
def test_declared_width_bounds_roll_back(source: str) -> None:
    field = _field()
    field.bit_width.minimum, field.bit_width.maximum = 2, 64
    with pytest.raises(TgiError):
        api.setFieldDefinitionBitWidth(get_handle(field), source)
    assert field.bit_width.value == "8"


@pytest.mark.parametrize("value", ["bad name", "1bad", "", None, 1])
def test_invalid_type_identifier_rolls_back(value) -> None:
    field = _field()
    field.type_identifier = "original"
    with pytest.raises(TgiError) as error:
        api.setFieldDefinitionTypeIdentifier(get_handle(field), value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.type_identifier == "original"


@pytest.mark.parametrize("value", [0, 1, "false", None])
def test_invalid_volatile_rolls_back(value) -> None:
    field = _field()
    with pytest.raises(TgiError) as error:
        api.setFieldDefinitionVolatile(get_handle(field), value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.volatile is None


def test_invalid_required_width_model_faults() -> None:
    field = _field()
    field.bit_width = None
    for function in (api.getFieldDefinitionBitWidthID, api.setFieldDefinitionBitWidth):
        with pytest.raises(TgiError) as error:
            function(get_handle(field), "16") if function is api.setFieldDefinitionBitWidth else function(
                get_handle(field)
            )
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert field.bit_width is None


def test_schema_roundtrip_preserves_definition_and_explicit_false() -> None:
    document = TypeDefinitions(
        vendor="test",
        library="lib",
        name="types",
        version="1",
        field_definitions=FieldDefinitions(field_definition=[_field()]),
    )
    xml = XmlDocument.serializer().render(document)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    _register_graph(parsed)
    field = parsed.field_definitions.field_definition[0]
    handle = get_handle(field)
    width_id = api.getFieldDefinitionBitWidthID(handle)
    api.setFieldDefinitionBitWidth(handle, "16")
    api.setFieldDefinitionTypeIdentifier(handle, "status_type")
    api.setFieldDefinitionVolatile(handle, False)
    updated = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(updated.encode()))
    reparsed = XmlDocument.parser().from_string(updated, TypeDefinitions).field_definitions.field_definition[0]
    assert reparsed.bit_width.value == "16"
    assert reparsed.type_identifier == "status_type"
    assert reparsed.volatile is False
    assert api.getFieldDefinitionBitWidthID(handle) == width_id
