"""Miscellaneous value and administrative contracts preserve typed XML content."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import miscellaneous as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, get_parent_info, register_parent
from org.accellera.ipxact.v1685_2022 import (
    ComplexBaseExpression,
    Component,
    Group,
    NameValuePairType,
    Value,
)


@pytest.fixture(autouse=True)
def reset_session():
    api._session_started = False
    api._session_ended = False
    api._session_messages.clear()
    yield
    api._session_started = False
    api._session_ended = False


@pytest.mark.parametrize("prefix", ["Argument", "Define"])
def test_pair_source_and_owned_wrapper_survive_edits(prefix):
    wrapper = Value(value="COUNT + 1", other_attributes={"{urn:test}tag": "preserve"})
    pair = NameValuePairType(name="count", value=wrapper)
    handle = get_handle(pair)
    assert getattr(api, "get" + prefix + "Value")(handle) == "COUNT + 1"
    assert getattr(api, "get" + prefix + "ValueExpression")(handle) == "COUNT + 1"
    value_id = getattr(api, "get" + prefix + "ValueID")(handle)
    assert value_id == get_handle(wrapper)
    assert get_parent_info(value_id).parent_handle == handle
    assert getattr(api, "set" + prefix + "Value")(handle, "8'hf")
    assert pair.value is wrapper
    assert wrapper.value == "8'hf"
    assert wrapper.other_attributes == {"{urn:test}tag": "preserve"}
    with pytest.raises(TgiError):
        getattr(api, "set" + prefix + "Value")(handle, 2)
    assert wrapper.value == "8'hf"


def test_expression_source_evaluation_and_atomic_bounds():
    expression = ComplexBaseExpression(value="8'hf + 1")
    handle = get_handle(expression)
    assert api.getExpression(handle) == "8'hf + 1"
    assert api.getExpressionIntValue(handle) == 16
    assert api.getExpressionValue(handle) == "16"
    assert api.setExpressionValue(handle, "WIDTH - 1")
    assert api.getExpression(handle) == "WIDTH - 1"
    with pytest.raises(TgiError):
        api.getExpressionIntValue(handle)
    with pytest.raises(TgiError):
        api.setExpressionValue(handle, "1 +")
    assert expression.value == "WIDTH - 1"
    real = get_handle(ComplexBaseExpression(value="1.5 + 2.0"))
    assert api.getExpressionValue(real) == "3.5"
    with pytest.raises(TgiError):
        api.getExpressionIntValue(real)


@pytest.mark.parametrize(
    "source,values,expected",
    [
        ("WIDTH - 1", ["WIDTH = 8'h10"], "15"),
        ("A + B", ["A = 3", "B = 2 * 4"], "11"),
        ("2 ** 4", [], "16"),
    ],
)
def test_resolve_expression_uses_constant_pairs(source, values, expected):
    assert api.resolveExpression(source, values) == expected


@pytest.mark.parametrize("values", [["A"], ["A = B"], ["A = 1", "A = 2"], ["bad name = 3"], "A=1"])
def test_resolve_rejects_invalid_pairs(values):
    with pytest.raises(TgiError):
        api.resolveExpression("A + 1", values)


def test_simple_content_and_group_access():
    group = Group(value="rtl")
    handle = get_handle(group)
    assert api.getGroup(handle) == "rtl"
    assert api.getValue(handle) == "rtl"
    assert api.setValue(handle, "verification")
    assert "verification" in api.getXML(handle)
    with pytest.raises(TgiError):
        api.getValue("missing")
    with pytest.raises(TgiError):
        api.setValue(handle, "bad\x00text")
    assert group.value == "verification"


@pytest.mark.parametrize("source,expected", [("true", True), ("false", False), ("1", True), ("0", False)])
def test_boolean_lexical_forms_and_wrapper_identity(source, expected):
    element = Value(value=source)
    handle = get_handle(element)
    assert api.getBooleanValue(handle) is expected
    assert api.setBooleanValue(handle, not expected)
    assert element.value == ("false" if expected else "true")


def test_boolean_primitive_owner_and_element_presence():
    from org.accellera.ipxact.v1685_2022 import BusDefinition

    owner = BusDefinition(vendor="v", library="l", name="b", version="1", direct_connection=True, is_addressable=False)
    boolean = get_handle(owner.direct_connection)
    register_parent(owner.direct_connection, owner, ("direct_connection",), "single")
    assert api.setBooleanValue(boolean, False)
    assert owner.direct_connection is False
    assert api.getBooleanValue(boolean) is False
    assert api.isSetElement(get_handle(owner), "directConnection")
    component = Component(vendor="v", library="l", name="c", version="1")
    assert not api.isSetElement(get_handle(component), "model")
    assert not api.isSetElement(get_handle(component), "unknown")


@pytest.mark.parametrize("source", ["yes", "no", "TRUE", "2"])
def test_boolean_rejects_non_schema_forms(source):
    with pytest.raises(TgiError):
        api.getBooleanValue(get_handle(Value(value=source)))


def test_administrative_lifecycle_and_exact_parameters():
    with pytest.raises(TgiError):
        api.message("info", "before")
    with pytest.raises(TgiError):
        api.init("1685-2022", "strict", "invalid mode")
    assert api.init("1685-2022", "error", "begin")
    assert api.message("warning", "check")
    assert api._session_messages == [("info", "begin"), ("warning", "check")]
    assert api.end(7, "done") == 0
    with pytest.raises(TgiError):
        api.message("info", "after")
    assert list(inspect.signature(api.init).parameters) == ["apiVersion", "failureMode", "message"]
    assert list(inspect.signature(api.end).parameters) == ["genStatus", "message"]
    assert list(inspect.signature(api.setDefineValue).parameters) == ["argumentID", "value"]


def test_signed_expression_and_declared_unsigned_bounds():
    from org.accellera.ipxact.v1685_2022 import UnsignedIntExpression

    signed = ComplexBaseExpression(value="0")
    assert api.setExpressionValue(get_handle(signed), "-5")
    assert api.getExpressionIntValue(get_handle(signed)) == -5
    bounded = UnsignedIntExpression(value="3", minimum=2, maximum=5)
    handle = get_handle(bounded)
    assert api.setExpressionValue(handle, "2 + 2")
    for source in ("-1", "6", "1", "64'h1_0000_0000"):
        with pytest.raises(TgiError):
            api.setExpressionValue(handle, source)
        assert bounded.value == "2 + 2"


def test_generic_numeric_simple_content_preserves_type():
    from org.accellera.ipxact.v1685_2022 import DelayValueType, EdgeValueType, TimingConstraint

    timing = TimingConstraint(
        value=25.0, clock_name="clk", clock_edge=EdgeValueType.RISE, delay_type=DelayValueType.MAX
    )
    handle = get_handle(timing)
    assert api.getValue(handle) == "25.0"
    assert api.setValue(handle, "50.0")
    assert timing.value == 50.0
    assert isinstance(timing.value, float)
    with pytest.raises(TgiError):
        api.setValue(handle, "1_0")
    assert timing.value == 50.0


_CONTRACTS = {
    "getArgumentValue": ["argumentID"],
    "getArgumentValueExpression": ["argumentID"],
    "getArgumentValueID": ["argumentID"],
    "getBooleanValue": ["elementID"],
    "getDefineValue": ["defineID"],
    "getDefineValueExpression": ["defineID"],
    "getDefineValueID": ["defineID"],
    "getExpression": ["expressionID"],
    "getExpressionIntValue": ["expressionID"],
    "getExpressionValue": ["expressionID"],
    "getGroup": ["groupID"],
    "getPartSelectIndexIDs": ["partSelectID"],
    "getPartSelectIndices": ["partSelectID"],
    "getPartSelectIndicesExpression": ["partSelectID"],
    "getPartSelectRange": ["partSelectID"],
    "getPartSelectRangeExpression": ["partSelectID"],
    "getPartSelectRangeLeftID": ["partSelectID"],
    "getPartSelectRangeRightID": ["partSelectID"],
    "getValue": ["elementID"],
    "getXML": ["elementID"],
    "addPartSelectIndex": ["partSelectID", "value"],
    "end": ["genStatus", "message"],
    "init": ["apiVersion", "failureMode", "message"],
    "isSetElement": ["elementContainerID", "elementName"],
    "message": ["severity", "message"],
    "registerCatalogVLNVs": ["catalogID"],
    "registerVLNV": ["fileName", "replace"],
    "removePartSelectIndex": ["indexID"],
    "resolveExpression": ["expression", "values"],
    "save": [],
    "setArgumentValue": ["argumentID", "value"],
    "setBooleanValue": ["elementID", "value"],
    "setDefineValue": ["argumentID", "value"],
    "setExpressionValue": ["expressionID", "value"],
    "setPartSelectRange": ["partSelectID", "left", "right"],
    "setValue": ["elementID", "value"],
    "removePartSelectRange": ["partSelectID"],
    "unregisterCatalogVLNVs": ["catalogID"],
    "unregisterVLNV": ["VLNV"],
}


@pytest.mark.parametrize("name,parameters", _CONTRACTS.items())
def test_exact_miscellaneous_signatures_exports_and_documentation(name, parameters):
    from typing import get_type_hints

    function = getattr(api, name)
    assert name in api.__all__
    signature = inspect.signature(function)
    assert list(signature.parameters) == parameters
    assert all(parameter.default is inspect.Parameter.empty for parameter in signature.parameters.values())
    assert set(get_type_hints(function)) == {*parameters, "return"}
    doc = inspect.getdoc(function)
    assert "Section: F.7." in doc
    assert "Args:" in doc and "Returns:" in doc
    assert all(parameter + ":" in doc for parameter in parameters)
