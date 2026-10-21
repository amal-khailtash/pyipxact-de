"""BASE minimum/maximum contracts retain lexical values and reject truncation."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Parameter, RealExpression, SignedLongintExpression


@pytest.mark.parametrize("bound", ["Minimum", "Maximum"])
@pytest.mark.parametrize(
    "kind,value,expected",
    [
        (Parameter, "0016", ("0016", 16.0, 16)),
        (SignedLongintExpression, -4, ("-4", -4.0, -4)),
        (RealExpression, 2.0, ("2.0", 2.0, 2)),
    ],
)
def test_bound_values(bound, kind, value, expected):
    kwargs = {"name": "P", "value": "1"} if kind is Parameter else {"value": "1"}
    obj = kind(**kwargs, **{bound.lower(): value})
    before = XmlDocument.serializer().render(obj)
    parsed = XmlDocument.parser().from_string(before, kind)
    for suffix, want in zip(("", "Double", "Int"), expected, strict=True):
        name = f"get{bound}{suffix}Attribute"
        getter = getattr(api, name)
        assert getter(get_handle(obj)) == want
        assert getter(get_handle(parsed)) == want
        assert getattr(tgi, name) is getter
        assert getter(get_handle(object())) is None
        with pytest.raises(TgiError):
            getter("missing")
    assert XmlDocument.serializer().render(obj) == before


@pytest.mark.parametrize("bound", ["Minimum", "Maximum"])
@pytest.mark.parametrize("value", [2.5, float("inf"), float("nan")])
def test_integer_bound_rejects_fractional_or_nonfinite(bound, value):
    handle = get_handle(RealExpression(value="1", **{bound.lower(): value}))
    with pytest.raises(TgiError) as error:
        getattr(api, f"get{bound}IntAttribute")(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("bound", ["Minimum", "Maximum"])
def test_source_expression_bounds(bound):
    obj = Parameter(name="P", value="1", **{bound.lower(): "${LIMIT}"})
    handle = get_handle(obj)
    assert getattr(api, f"get{bound}Attribute")(handle) == "${LIMIT}"
    for suffix in ("Int", "Double"):
        with pytest.raises(TgiError):
            getattr(api, f"get{bound}{suffix}Attribute")(handle)
