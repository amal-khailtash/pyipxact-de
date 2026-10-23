"""Parameter TGI edits preserve generated wrappers, XML ownership and value semantics."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import component
from amal.eda.accellera.ipxact.v1685_2022.tgi import parameter as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    FormatType,
    Parameter,
    Parameters,
    SignType,
    Value,
    Vector,
    Vectors,
)
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.right import Right

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear()
    yield
    registry.clear()


def _root():
    return Component(vendor="v", library="l", name="component", version="1")


def _valid(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, Component) == root
    return xml


def _instantiation(root):
    handle = component.addComponentComponentInstantiation(get_handle(root), "rtl")
    return resolve_handle(handle)


def test_parameter_creation_and_value_edits_preserve_generated_wrapper_metadata():
    root = _root()
    instantiation = _instantiation(root)
    parameter_id = api.addParameter(get_handle(instantiation), "WIDTH", "8 * 2")
    parameter = resolve_handle(parameter_id)
    value_id = api.getParameterValueID(parameter_id)
    value = resolve_handle(value_id)
    value.other_attributes["{urn:test}marker"] = "kept"
    parameter.parameter_id = "width"

    assert api.getParameterIDs(get_handle(instantiation)) == [parameter_id]
    assert api.getParameterValue(parameter_id) == "8 * 2"  # The default type is string.
    assert api.getParameterValueExpression(parameter_id) == "8 * 2"
    assert api.setParameterValue(parameter_id, "16")
    assert resolve_handle(value_id) is value
    assert get_handle(parameter.value) == value_id
    assert value.other_attributes["{urn:test}marker"] == "kept"
    assert parameter.parameter_id == "width"
    _valid(root)


def test_parameter_add_and_set_failures_leave_model_and_xml_unchanged():
    root = _root()
    instantiation = _instantiation(root)
    parameter_id = api.addParameter(get_handle(instantiation), "COUNT", "12")
    parameter = resolve_handle(parameter_id)
    parameter.type_value = FormatType.BYTE
    before_xml = _valid(root)
    before_value = parameter.value.value

    with pytest.raises(TgiError):
        api.addParameter(get_handle(instantiation), "COUNT", "20")
    for expression in (None, "128", "1 +", "1.5", "8'b0000xxxx", ""):
        with pytest.raises(TgiError):
            api.setParameterValue(parameter_id, expression)
        assert parameter.value.value == before_value
        assert _valid(root) == before_xml


def test_parameter_enumeration_and_mutation_accept_tuple_holders():
    root = _root()
    instantiation = _instantiation(root)
    first = Parameter(name="FIRST", value=Value(value="1"))
    instantiation.parameters = Parameters(parameter=(first,))

    first_id = get_handle(first)
    added_id = api.addParameter(get_handle(instantiation), "SECOND", "2")
    assert api.getParameterIDs(get_handle(instantiation)) == [first_id, added_id]
    assert isinstance(instantiation.parameters.parameter, list)
    assert api.removeParameter(added_id)
    assert api.getParameterIDs(get_handle(instantiation)) == [first_id]
    _valid(root)


def test_registered_parsed_component_removal_invalidates_parameter_descendants_and_holder():
    root = _root()
    instantiation = _instantiation(root)
    api.addParameter(get_handle(instantiation), "WIDTH", "32")
    parsed = XmlDocument.parser().from_string(_valid(root), Component)
    registry.register(parsed, ["v", "l", "component", "1"])
    model_instances = parsed.model.instantiations
    entries = model_instances.component_instantiation_or_design_instantiation_or_design_configuration_instantiation
    parsed_instantiation = entries[0]
    parameter = parsed_instantiation.parameters.parameter[0]
    parameter_id = get_handle(parameter)
    value_id = get_handle(parameter.value)
    holder_id = get_handle(parsed_instantiation.parameters)

    # No parameter lookup has registered ownership; removal must recover it from the registry root.
    assert api.removeParameter(parameter_id)
    assert parsed_instantiation.parameters is None
    assert all(resolve_handle(handle) is None for handle in (parameter_id, value_id, holder_id))
    _valid(parsed)


def test_remove_config_groups_clears_token_list_and_prunes_empty_holder():
    root = _root()
    instantiation = _instantiation(root)
    parameter_id = api.addParameter(get_handle(instantiation), "MODE", "1")
    parameter = resolve_handle(parameter_id)
    parameter.config_groups = ("clocking", "reset")

    assert api.removeConfigGroupsAttribute(parameter_id)
    assert parameter.config_groups == []
    assert not api.removeConfigGroupsAttribute(parameter_id)
    _valid(root)

    assert api.removeParameter(parameter_id)
    assert instantiation.parameters is None
    _valid(root)


@pytest.mark.parametrize(
    "kind,source,kwargs,expected",
    [
        (FormatType.BIT, "1", {}, "1"),
        (FormatType.BYTE, "-128", {}, "-128"),
        (FormatType.SHORTINT, "32767", {}, "32767"),
        (FormatType.INT, "8'h20 + 1", {}, "33"),
        (FormatType.LONGINT, "64'd9223372036854775807", {}, "9223372036854775807"),
        (FormatType.SHORTREAL, "1.25 + 0.75", {}, "2.0"),
        (FormatType.REAL, "3.0 / 2", {}, "1.5"),
        (FormatType.STRING, "1 + 2", {}, "1 + 2"),
        (
            FormatType.BIT,
            "4'b1111",
            {"vectors": Vectors(vector=[Vector(left=Left(value="3"), right=Right(value="0"))])},
            "15",
        ),
        (FormatType.BYTE, "255", {"sign": SignType.UNSIGNED}, "255"),
    ],
)
def test_parameter_getter_interprets_constants_by_declared_type(kind, source, kwargs, expected):
    parameter = Parameter(name="P", value=Value(value=source), type_value=kind, **kwargs)
    parameter_id = get_handle(parameter)
    assert api.getParameterValue(parameter_id) == expected
    assert api.getParameterValueExpression(parameter_id) == source
    assert parameter.value.value == source


@pytest.mark.parametrize(
    "kind,source,kwargs",
    [
        (FormatType.BIT, "2", {}),
        (FormatType.BYTE, "128", {}),
        (FormatType.BYTE, "-1", {"sign": SignType.UNSIGNED}),
        (FormatType.SHORTINT, "32768", {}),
        (FormatType.INT, "33'd2147483648", {}),
        (FormatType.LONGINT, "64'd9223372036854775808", {}),
        (FormatType.INT, "11", {"minimum": "0", "maximum": "10"}),
        (
            FormatType.BIT,
            "4'b10x1",
            {"vectors": Vectors(vector=[Vector(left=Left(value="3"), right=Right(value="0"))])},
        ),
        (FormatType.BYTE, "1 +", {}),
        (FormatType.BYTE, "1.5", {}),
    ],
)
def test_parameter_numeric_getter_rejects_invalid_constants(kind, source, kwargs):
    parameter = Parameter(name="P", value=Value(value=source), type_value=kind, **kwargs)
    with pytest.raises(TgiError):
        api.getParameterValue(get_handle(parameter))


def test_numeric_setter_keeps_unresolved_names_but_getter_reports_them():
    parameter = Parameter(name="WIDTH", value=Value(value="8"), type_value=FormatType.INT)
    parameter_id = get_handle(parameter)

    assert api.setParameterValue(parameter_id, "UNKNOWN_WIDTH + 1")
    assert api.getParameterValueExpression(parameter_id) == "UNKNOWN_WIDTH + 1"
    with pytest.raises(TgiError):
        api.getParameterValue(parameter_id)


@pytest.mark.parametrize("expression", ["1 +", "1.5", "4'bxx00", "128", "-129", "11"])
def test_numeric_setter_rejects_invalid_syntax_unknown_bits_and_ranges_atomically(expression):
    parameter = Parameter(
        name="LIMITED",
        value=Value(value="10"),
        type_value=FormatType.BYTE,
        minimum="0",
        maximum="10",
    )
    parameter_id = get_handle(parameter)
    value_id = api.getParameterValueID(parameter_id)
    with pytest.raises(TgiError):
        api.setParameterValue(parameter_id, expression)
    assert parameter.value.value == "10"
    assert get_handle(parameter.value) == value_id
