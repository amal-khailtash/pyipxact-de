"""Alternate-register typeIdentifier and volatility operations."""

from collections.abc import Iterator
from dataclasses import fields, is_dataclass
from inspect import signature
from pathlib import Path
from typing import Any

import pytest
from lxml import etree

import amal.eda.accellera.ipxact.v1685_2022.tgi as tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import register as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.volatile import Volatile

_SAMPLE = Path("tests/xml/ipxact/v1685_2022/accellera.org/Sample/SampleComponent/1.0/xml/SampleComponent.xml")
_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_OPERATIONS = (
    ("getAlternateRegisterTypeIdentifier", ("alternateRegisterID",), "F.7.73.10"),
    ("getAlternateRegisterVolatility", ("alternateRegisterID",), "F.7.73.11"),
    ("removeAlternateRegisterTypeIdentifier", ("alternateRegisterID",), "F.7.74.14"),
    ("removeAlternateRegisterVolatility", ("alternateRegisterID",), "F.7.74.15"),
    (
        "setAlternateRegisterTypeIdentifier",
        ("alternateRegisterID", "typeIdentifier"),
        "F.7.74.42",
    ),
    ("setAlternateRegisterVolatility", ("alternateRegisterID", "_volatile"), "F.7.74.43"),
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _alternate_register(
    *,
    type_identifier: str | None = None,
    volatile: Volatile | None = None,
) -> AlternateRegisters.AlternateRegister:
    return AlternateRegisters.AlternateRegister(
        name="alternate",
        mode_ref=[ModeRef(value="ModeA", priority=1)],
        type_identifier=type_identifier,
        volatile=volatile,
        field_value=[
            FieldType(
                name="flag",
                bit_offset=UnsignedIntExpression(value="0"),
                choice=[UnsignedPositiveIntExpression(value="1")],
            )
        ],
    )


def _find_alternate_register(root: Any) -> AlternateRegisters.AlternateRegister:
    pending = [root]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if isinstance(current, AlternateRegisters.AlternateRegister):
            return current
        if id(current) in seen:
            continue
        seen.add(id(current))
        if is_dataclass(current) and not isinstance(current, type):
            pending.extend(getattr(current, item.name) for item in fields(current))
        elif isinstance(current, (list, tuple)):
            pending.extend(current)
    raise AssertionError("Sample component has no alternate register")


@pytest.mark.parametrize(("name", "parameters", "section"), _OPERATIONS)
def test_alternate_register_metadata_signatures_and_docs(name: str, parameters: tuple[str, ...], section: str) -> None:
    function = getattr(api, name)
    assert tuple(signature(function).parameters) == parameters
    assert name in api.__all__
    assert getattr(tgi, name) is function
    assert "Args:" in function.__doc__
    assert "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


def test_alternate_register_metadata_absence_and_explicit_false() -> None:
    alternate_register = _alternate_register()
    alternate_register_id = get_handle(alternate_register)

    assert api.getAlternateRegisterTypeIdentifier(alternate_register_id) is None
    assert api.getAlternateRegisterVolatility(alternate_register_id) is None
    assert api.removeAlternateRegisterTypeIdentifier(alternate_register_id) is False
    assert api.removeAlternateRegisterVolatility(alternate_register_id) is False

    assert api.setAlternateRegisterVolatility(alternate_register_id, _volatile=False)
    assert api.getAlternateRegisterVolatility(alternate_register_id) is False


def test_alternate_register_metadata_setters_preserve_wrapper_and_sibling_metadata() -> None:
    volatile = Volatile(value=False)
    alternate_register = _alternate_register(type_identifier="Initial_Type", volatile=volatile)
    alternate_register_id = get_handle(alternate_register)
    volatile_id = get_handle(volatile)
    mode_ref = alternate_register.mode_ref[0]
    field = alternate_register.field_value[0]

    assert api.setAlternateRegisterTypeIdentifier(alternate_register_id, "Updated_Type") is True
    assert alternate_register.type_identifier == "Updated_Type"
    assert api.setAlternateRegisterVolatility(alternate_register_id, _volatile=True) is True
    assert alternate_register.volatile is volatile
    assert get_handle(alternate_register.volatile) == volatile_id
    assert get_parent_info(volatile_id).parent_handle == alternate_register_id
    assert get_parent_info(volatile_id).path == ("volatile",)
    assert get_parent_info(volatile_id).container == "single"
    assert api.getAlternateRegisterVolatility(alternate_register_id) is True
    assert alternate_register.mode_ref == [mode_ref]
    assert alternate_register.field_value == [field]


def test_alternate_register_metadata_removal_clears_and_invalidates() -> None:
    volatile = Volatile(value=True)
    alternate_register = _alternate_register(type_identifier="Shared_Type", volatile=volatile)
    alternate_register_id = get_handle(alternate_register)
    volatile_id = get_handle(volatile)

    assert api.removeAlternateRegisterTypeIdentifier(alternate_register_id) is True
    assert alternate_register.type_identifier is None
    assert api.removeAlternateRegisterTypeIdentifier(alternate_register_id) is False
    assert api.removeAlternateRegisterVolatility(alternate_register_id) is True
    assert alternate_register.volatile is None
    assert resolve_handle(volatile_id) is None
    assert api.getAlternateRegisterVolatility(alternate_register_id) is None
    assert api.removeAlternateRegisterVolatility(alternate_register_id) is False


@pytest.mark.parametrize("invalid_name", ("", "bad name", "a/name", 17, None))
def test_alternate_register_type_identifier_rejects_invalid_names_atomically(invalid_name: object) -> None:
    alternate_register = _alternate_register(type_identifier="Valid_Type")
    alternate_register_id = get_handle(alternate_register)

    with pytest.raises(TgiError) as error:
        api.setAlternateRegisterTypeIdentifier(alternate_register_id, invalid_name)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert alternate_register.type_identifier == "Valid_Type"


@pytest.mark.parametrize("invalid_boolean", (0, 1, "true", None))
def test_alternate_register_volatility_rejects_non_boolean_atomically(invalid_boolean: object) -> None:
    volatile = Volatile(value=False)
    alternate_register = _alternate_register(volatile=volatile)
    alternate_register_id = get_handle(alternate_register)
    volatile_id = get_handle(volatile)

    with pytest.raises(TgiError) as error:
        api.setAlternateRegisterVolatility(alternate_register_id, invalid_boolean)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert alternate_register.volatile is volatile
    assert volatile.value is False
    assert get_handle(volatile) == volatile_id


def test_alternate_register_metadata_operations_reject_unknown_and_wrong_model_handles() -> None:
    wrong_model_id = get_handle(FieldType(name="field", bit_offset=UnsignedIntExpression(value="0")))
    operations = (
        (api.getAlternateRegisterTypeIdentifier, ()),
        (api.getAlternateRegisterVolatility, ()),
        (api.removeAlternateRegisterTypeIdentifier, ()),
        (api.removeAlternateRegisterVolatility, ()),
        (api.setAlternateRegisterTypeIdentifier, ("Type",)),
        (api.setAlternateRegisterVolatility, (True,)),
    )
    for operation, arguments in operations:
        for invalid_id in (wrong_model_id, "hdeadbeef"):
            with pytest.raises(TgiError) as error:
                operation(invalid_id, *arguments)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_alternate_register_type_identifier_removal_rejects_invalid_model_value() -> None:
    alternate_register = _alternate_register()
    alternate_register.type_identifier = 23
    alternate_register_id = get_handle(alternate_register)

    with pytest.raises(TgiError) as error:
        api.removeAlternateRegisterTypeIdentifier(alternate_register_id)

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert alternate_register.type_identifier == 23


def test_alternate_register_metadata_round_trips_schema_valid_component() -> None:
    component = XmlDocument.parser().from_string(_SAMPLE.read_text(), Component)
    alternate_register = _find_alternate_register(component)
    alternate_register_id = get_handle(alternate_register)
    mode_refs = tuple(alternate_register.mode_ref)
    fields_before = tuple(alternate_register.field_value)
    access_policies = alternate_register.access_policies
    assert mode_refs and fields_before and access_policies is not None

    assert api.setAlternateRegisterTypeIdentifier(alternate_register_id, "Alternate_Type")
    assert api.setAlternateRegisterVolatility(alternate_register_id, _volatile=False)
    volatile_id = get_handle(alternate_register.volatile)
    volatile_parent = get_parent_info(volatile_id)
    assert volatile_parent is not None and volatile_parent.parent_handle == alternate_register_id
    assert volatile_parent.path == ("volatile",) and volatile_parent.container == "single"
    xml = XmlDocument.serializer().render(component)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log

    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_alternate = _find_alternate_register(parsed)
    assert parsed_alternate.type_identifier == "Alternate_Type"
    assert parsed_alternate.volatile is not None and parsed_alternate.volatile.value is False
    assert tuple(item.value for item in parsed_alternate.mode_ref) == tuple(item.value for item in mode_refs)
    assert tuple(item.name for item in parsed_alternate.field_value) == tuple(item.name for item in fields_before)
    assert parsed_alternate.access_policies is not None
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(parsed), Component) == parsed

    parsed_alternate_id = get_handle(parsed_alternate)
    parsed_volatile_id = get_handle(parsed_alternate.volatile)
    assert api.removeAlternateRegisterVolatility(parsed_alternate_id)
    assert parsed_alternate.volatile is None and resolve_handle(parsed_volatile_id) is None
    xml_without_volatility = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_without_volatility.encode())), _SCHEMA.error_log
