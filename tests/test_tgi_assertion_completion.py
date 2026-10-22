"""Assertion TGI expressions, ownership, and generated XML contracts."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import assertion as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Assertion,
    Assertions,
    BusDefinition,
    Component,
    Design,
    TypeDefinitions,
    UnsignedBitExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


def _component():
    return Component(vendor="v", library="l", name="assertions", version="1")


def _schema_valid_xml(model):
    xml = XmlDocument.serializer().render(model)
    parsed_xml = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(parsed_xml), _SCHEMA.error_log
    return xml


@pytest.mark.parametrize(
    "owner",
    [
        _component,
        lambda: Design(vendor="v", library="l", name="design", version="1"),
        lambda: BusDefinition(
            vendor="v", library="l", name="bus", version="1", direct_connection=True, is_addressable=True
        ),
        lambda: TypeDefinitions(vendor="v", library="l", name="types", version="1"),
    ],
)
def test_add_uses_generated_assertions_container_for_schema_owners(owner):
    model = owner()
    owner_id = get_handle(model)

    assertion_id = api.addAssertion(owner_id, "nonzero", "1'b1")

    assert model.assertions is not None
    assert model.assertions.__class__.__name__ == "Assertions"
    assert api.getAssertionIDs(owner_id) == [assertion_id]
    assert resolve_handle(assertion_id) is model.assertions.assertion[0]
    assert get_parent_info(assertion_id).parent_handle == get_handle(model.assertions)


def test_component_assertions_validate_and_round_trip_generated_expression():
    root = _component()
    root_id = get_handle(root)
    true_id = api.addAssertion(root_id, "always", "1'b1")
    false_id = api.addAssertion(root_id, "never", "1'b0")

    assert api.getAssertionAssert(true_id) is True
    assert api.getAssertionAssert(false_id) is False
    assert api.getAssertionAssertExpression(true_id) == "1'b1"
    expression_id = api.getAssertionAssertID(true_id)
    assert resolve_handle(expression_id) is root.assertions.assertion[0].assert_value
    assert get_parent_info(expression_id).parent_handle == true_id

    xml = _schema_valid_xml(root)
    loaded = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(loaded) == xml
    loaded_ids = api.getAssertionIDs(get_handle(loaded))
    assert [api.getAssertionAssertExpression(item) for item in loaded_ids] == ["1'b1", "1'b0"]
    assert [api.getAssertionAssert(item) for item in loaded_ids] == [True, False]


def test_unresolved_or_non_boolean_expressions_raise_invalid_argument():
    root_id = get_handle(_component())
    unresolved_id = api.addAssertion(root_id, "parameter-dependent", "WIDTH > 0")
    multi_bit_id = api.addAssertion(root_id, "not-a-bit", "2")

    assert api.getAssertionAssertExpression(unresolved_id) == "WIDTH > 0"
    for assertion_id in (unresolved_id, multi_bit_id):
        with pytest.raises(TgiError) as error:
            api.getAssertionAssert(assertion_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_setter_preserves_expression_handle_and_schema_metadata():
    root = _component()
    assertion_id = api.addAssertion(get_handle(root), "truth", "1'b1")
    assertion = resolve_handle(assertion_id)
    assertion.assert_value.other_attributes = {"{urn:vendor:assertion}source": "generated"}
    expression_id = api.getAssertionAssertID(assertion_id)
    expression = resolve_handle(expression_id)

    assert api.setAssertionAssert(assertion_id, "(1 + 1) == 2")

    assert api.getAssertionAssertID(assertion_id) == expression_id
    assert resolve_handle(expression_id) is expression
    assert expression.value == "(1 + 1) == 2"
    assert expression.other_attributes == {"{urn:vendor:assertion}source": "generated"}
    assert api.getAssertionAssert(assertion_id) is True
    xml = _schema_valid_xml(root)
    loaded = XmlDocument.parser().from_string(xml, Component)
    loaded_expression = loaded.assertions.assertion[0].assert_value
    assert loaded_expression.value == "(1 + 1) == 2"
    assert loaded_expression.other_attributes == expression.other_attributes


@pytest.mark.parametrize("parsed", [False, True])
def test_remove_restores_parsed_ownership_and_invalidates_only_equal_assertion_subtree(parsed):
    first = Assertion(name="same", assert_value=UnsignedBitExpression(value="1'b1"))
    second = Assertion(name="same", assert_value=UnsignedBitExpression(value="1'b1"))
    root = _component()
    root.assertions = Assertions(assertion=[first, second])
    if parsed:
        xml = _schema_valid_xml(root)
        root = XmlDocument.parser().from_string(xml, Component)

    root_id = get_handle(root)
    first_id, second_id = api.getAssertionIDs(root_id)
    first_expression_id = api.getAssertionAssertID(first_id)
    second_expression_id = api.getAssertionAssertID(second_id)
    assert resolve_handle(first_id) is not resolve_handle(second_id)
    assert resolve_handle(first_id) == resolve_handle(second_id)

    assert api.removeAssertion(first_id)

    assert resolve_handle(first_id) is None
    assert resolve_handle(first_expression_id) is None
    assert get_parent_info(first_id) is None
    assert resolve_handle(second_id) is not None
    assert resolve_handle(second_expression_id) is not None
    assert api.getAssertionIDs(root_id) == [second_id]
    with pytest.raises(TgiError) as error:
        api.removeAssertion(first_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "operation",
    [
        lambda: api.getAssertionIDs("missing"),
        lambda: api.addAssertion("missing", "name", "1'b1"),
        lambda: api.getAssertionAssert("missing"),
        lambda: api.getAssertionAssertExpression("missing"),
        lambda: api.getAssertionAssertID("missing"),
        lambda: api.setAssertionAssert("missing", "1'b1"),
        lambda: api.removeAssertion("missing"),
    ],
)
def test_invalid_handles_raise_invalid_id(operation):
    with pytest.raises(TgiError) as error:
        operation()
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_non_owner_parent_and_invalid_inputs_leave_tree_unchanged():
    assertion = Assertion(name="existing", assert_value=UnsignedBitExpression(value="1'b1"))
    assertion_id = get_handle(assertion)
    root = _component()
    root_id = get_handle(root)

    with pytest.raises(TgiError) as error:
        api.addAssertion(assertion_id, "new", "1'b1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for name, expression in [("", "1'b1"), ("new", ""), ("new", None)]:
        with pytest.raises(TgiError) as error:
            api.addAssertion(root_id, name, expression)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert root.assertions is None
    with pytest.raises(TgiError) as error:
        api.setAssertionAssert(assertion_id, " ")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert assertion.assert_value.value == "1'b1"
