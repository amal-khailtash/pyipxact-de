"""TGI access and lifecycle for Design ad-hoc connection tied values."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import design as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import miscellaneous
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AdHocConnection,
    AdHocConnections,
    ComplexTiedValueExpression,
    Design,
    ExternalPortReference,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _design(tied_value: ComplexTiedValueExpression | None = None, *, name: str = "tied_value_design") -> Design:
    connection = AdHocConnection(
        name="tie_data",
        tied_value=tied_value,
        port_references=AdHocConnection.PortReferences(
            internal_port_reference_or_external_port_reference=[ExternalPortReference(port_ref="top_data")]
        ),
    )
    root = Design(
        vendor="acme",
        library="connections",
        name=name,
        version="1.0",
        ad_hoc_connections=AdHocConnections(ad_hoc_connection=[connection]),
    )
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    return root


def _connection(root: Design) -> AdHocConnection:
    return root.ad_hoc_connections.ad_hoc_connection[0]


def test_tied_value_getters_evaluate_preserve_source_and_return_owned_handle() -> None:
    wrapper = ComplexTiedValueExpression(value="8'h0f + 1", other_attributes={"{urn:test}tag": "keep"})
    root = _design(wrapper)
    connection = _connection(root)
    owner_id = get_handle(connection)

    assert api.getAdHocConnectionTiedValue(owner_id) == "16"
    assert api.getAdHocConnectionTiedValueExpression(owner_id) == "8'h0f + 1"
    tied_value_id = api.getAdHocConnectionTiedValueID(owner_id)
    assert tied_value_id == get_handle(wrapper)
    assert resolve_handle(tied_value_id) is wrapper
    parent = get_parent_info(tied_value_id)
    assert parent is not None
    assert parent.parent_handle == owner_id
    assert parent.path == ("tied_value",)
    assert parent.container == "single"


@pytest.mark.parametrize("source", ("open", "default"))
def test_tied_value_getter_returns_open_and_default(source: str) -> None:
    root = _design(ComplexTiedValueExpression(value=source))
    assert api.getAdHocConnectionTiedValue(get_handle(_connection(root))) == source


def test_tied_value_getters_return_none_when_absent_and_reject_invalid_owners_or_wrappers() -> None:
    root = _design()
    owner_id = get_handle(_connection(root))
    assert api.getAdHocConnectionTiedValue(owner_id) is None
    assert api.getAdHocConnectionTiedValueExpression(owner_id) is None
    assert api.getAdHocConnectionTiedValueID(owner_id) is None

    invalid_ids = ("missing", get_handle(ExternalPortReference(port_ref="top_data")))
    for invalid_id in invalid_ids:
        for getter in (
            api.getAdHocConnectionTiedValue,
            api.getAdHocConnectionTiedValueExpression,
            api.getAdHocConnectionTiedValueID,
        ):
            with pytest.raises(TgiError) as error:
                getter(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

    malformed_root = _design(name="malformed_tied_value_design")
    malformed_connection = _connection(malformed_root)
    malformed_connection.tied_value = object()
    for getter in (
        api.getAdHocConnectionTiedValue,
        api.getAdHocConnectionTiedValueExpression,
        api.getAdHocConnectionTiedValueID,
    ):
        with pytest.raises(TgiError) as error:
            getter(get_handle(malformed_connection))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_tied_value_setter_creates_wrapper_and_preserves_identity_and_metadata() -> None:
    root = _design()
    connection = _connection(root)
    owner_id = get_handle(connection)

    assert api.setAdHocConnectionTiedValue(owner_id, "4 + 2")
    wrapper = connection.tied_value
    assert isinstance(wrapper, ComplexTiedValueExpression)
    tied_value_id = api.getAdHocConnectionTiedValueID(owner_id)
    assert tied_value_id == get_handle(wrapper)
    assert api.getAdHocConnectionTiedValue(owner_id) == "6"

    wrapper.other_attributes = {"{urn:test}tag": "preserve"}
    wrapper.minimum = 2
    wrapper.maximum = 10
    assert api.setAdHocConnectionTiedValue(owner_id, "8'h8")
    assert connection.tied_value is wrapper
    assert api.getAdHocConnectionTiedValueID(owner_id) == tied_value_id
    assert wrapper.value == "8'h8"
    assert wrapper.other_attributes == {"{urn:test}tag": "preserve"}
    assert wrapper.minimum == 2
    assert wrapper.maximum == 10
    assert api.getAdHocConnectionTiedValue(owner_id) == "8"


@pytest.mark.parametrize(
    "source,evaluated",
    (
        ("open", "open"),
        ("default", "default"),
        ('"open"', "open"),
        ('"default"', "default"),
        ('1 ? "open" : "default"', "open"),
        ('0 ? "open" : "default"', "default"),
    ),
)
def test_tied_value_setter_accepts_raw_quoted_and_conditional_strings(source: str, evaluated: str) -> None:
    root = _design(ComplexTiedValueExpression(value="3"))
    connection = _connection(root)
    wrapper = connection.tied_value

    assert api.setAdHocConnectionTiedValue(get_handle(connection), source)
    assert connection.tied_value is wrapper
    assert wrapper.value == source
    assert api.getAdHocConnectionTiedValueExpression(get_handle(connection)) == source
    assert api.getAdHocConnectionTiedValue(get_handle(connection)) == evaluated


@pytest.mark.parametrize("source", ("WIDTH + 1", "WIDTH"))
def test_tied_value_setter_defers_undeclared_identifiers(source: str) -> None:
    root = _design(ComplexTiedValueExpression(value="3"))
    connection = _connection(root)
    wrapper = connection.tied_value

    assert api.setAdHocConnectionTiedValue(get_handle(connection), source)
    assert connection.tied_value is wrapper
    assert wrapper.value == source
    assert api.getAdHocConnectionTiedValueExpression(get_handle(connection)) == source
    with pytest.raises(TgiError):
        api.getAdHocConnectionTiedValue(get_handle(connection))


@pytest.mark.parametrize(
    "source",
    (
        "-1",
        "1.5",
        "1'bx",
        "1'bz",
        "4'b10x1",
        '"not_open_or_default"',
        "1 +",
        "8'h1\x00",
    ),
    ids=("negative", "real", "x", "z", "mixed-x", "quoted-string", "malformed", "invalid-xml-text"),
)
def test_tied_value_setter_rejects_invalid_sources_atomically(source: str) -> None:
    wrapper = ComplexTiedValueExpression(
        value="5",
        other_attributes={"{urn:test}tag": "keep"},
        minimum=2,
        maximum=9,
    )
    root = _design(wrapper)
    connection = _connection(root)
    owner_id = get_handle(connection)
    before = (wrapper.value, wrapper.other_attributes, wrapper.minimum, wrapper.maximum)
    tied_value_id = get_handle(wrapper)

    with pytest.raises(TgiError) as error:
        api.setAdHocConnectionTiedValue(owner_id, source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert connection.tied_value is wrapper
    assert get_handle(wrapper) == tied_value_id
    assert (wrapper.value, wrapper.other_attributes, wrapper.minimum, wrapper.maximum) == before


@pytest.mark.parametrize(
    "source,valid",
    (("1", False), ("10", False), ("-1", False), ("1.0", False), ("2", True), ("9", True)),
    ids=("below-minimum", "above-maximum", "negative", "real", "minimum", "maximum"),
)
def test_tied_value_setter_enforces_declared_numeric_bounds(source: str, valid: bool) -> None:
    wrapper = ComplexTiedValueExpression(value="5", minimum=2, maximum=9)
    root = _design(wrapper)
    connection = _connection(root)

    if valid:
        assert api.setAdHocConnectionTiedValue(get_handle(connection), source)
        assert wrapper.value == source
    else:
        with pytest.raises(TgiError):
            api.setAdHocConnectionTiedValue(get_handle(connection), source)
        assert wrapper.value == "5"


def test_tied_value_setter_rejects_invalid_owner_and_malformed_wrapper_without_mutation() -> None:
    with pytest.raises(TgiError) as error:
        api.setAdHocConnectionTiedValue("missing", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    root = _design(ComplexTiedValueExpression(value="5"))
    connection = _connection(root)
    malformed = object()
    connection.tied_value = malformed
    with pytest.raises(TgiError) as error:
        api.setAdHocConnectionTiedValue(get_handle(connection), "6")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert connection.tied_value is malformed


@pytest.mark.parametrize("source", ("", 7, None), ids=("empty", "integer", "none"))
def test_tied_value_setter_rejects_empty_or_non_string_input_without_creating_wrapper(source: object) -> None:
    root = _design()
    connection = _connection(root)

    with pytest.raises(TgiError) as error:
        api.setAdHocConnectionTiedValue(get_handle(connection), source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert connection.tied_value is None


@pytest.mark.parametrize(
    "minimum,maximum",
    ((10, 1), ("0", 10), (0, 10.0), (True, 10)),
    ids=("reversed", "string-minimum", "real-maximum", "boolean-minimum"),
)
def test_tied_value_setter_rejects_invalid_declared_bounds_atomically(minimum: object, maximum: object) -> None:
    wrapper = ComplexTiedValueExpression(value="5", minimum=minimum, maximum=maximum)
    root = _design(wrapper)
    connection = _connection(root)

    with pytest.raises(TgiError) as error:
        api.setAdHocConnectionTiedValue(get_handle(connection), "WIDTH")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert connection.tied_value is wrapper
    assert wrapper.value == "5"


@pytest.mark.parametrize("source", ("-1", "1.5", "1'bx", "4'b10x1"))
def test_tied_value_getter_rejects_invalid_known_constants(source: str) -> None:
    root = _design(ComplexTiedValueExpression(value=source))

    with pytest.raises(TgiError) as error:
        api.getAdHocConnectionTiedValue(get_handle(_connection(root)))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_tied_value_setter_accepts_unsigned_constants_larger_than_64_bits() -> None:
    root = _design()
    connection = _connection(root)
    source = "128'h1_0000_0000_0000_0000"

    assert api.setAdHocConnectionTiedValue(get_handle(connection), source)
    assert connection.tied_value.value == source
    assert api.getAdHocConnectionTiedValue(get_handle(connection)) == "18446744073709551616"


def test_generic_expression_operations_accept_tied_value_wrapper() -> None:
    wrapper = ComplexTiedValueExpression(value="8'hf + 1", other_attributes={"{urn:test}tag": "keep"})
    root = _design(wrapper)
    connection = _connection(root)
    tied_value_id = api.getAdHocConnectionTiedValueID(get_handle(connection))

    assert miscellaneous.getExpression(tied_value_id) == "8'hf + 1"
    assert miscellaneous.getExpressionValue(tied_value_id) == "16"
    assert miscellaneous.setExpressionValue(tied_value_id, "WIDTH - 1")
    assert miscellaneous.getExpression(tied_value_id) == "WIDTH - 1"
    assert connection.tied_value is wrapper
    assert wrapper.other_attributes == {"{urn:test}tag": "keep"}
    with pytest.raises(TgiError):
        miscellaneous.getExpressionValue(tied_value_id)
    with pytest.raises(TgiError):
        miscellaneous.setExpressionValue(tied_value_id, "WIDTH +")
    assert wrapper.value == "WIDTH - 1"


def test_remove_tied_value_uses_owner_invalidates_child_and_is_idempotent() -> None:
    wrapper = ComplexTiedValueExpression(value="3", other_attributes={"{urn:test}tag": "keep"})
    root = _design(wrapper)
    connection = _connection(root)
    owner_id = get_handle(connection)
    tied_value_id = api.getAdHocConnectionTiedValueID(owner_id)

    assert api.removeAdHocConnectionTiedValue(owner_id)
    assert connection.tied_value is None
    assert resolve_handle(tied_value_id) is None
    assert api.getAdHocConnectionTiedValueID(owner_id) is None
    assert not api.removeAdHocConnectionTiedValue(owner_id)

    with pytest.raises(TgiError) as error:
        api.removeAdHocConnectionTiedValue("missing")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeAdHocConnectionTiedValue(get_handle(ExternalPortReference(port_ref="top_data")))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_parsed_design_tied_value_round_trip_after_set_and_remove() -> None:
    root = _design(ComplexTiedValueExpression(value="default"))
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Design)
    assert XmlDocument.serializer().render(parsed) == xml
    registry.clear()
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    connection = _connection(parsed)

    assert api.getAdHocConnectionTiedValue(get_handle(connection)) == "default"
    assert api.setAdHocConnectionTiedValue(get_handle(connection), "8'hf")
    xml_after_set = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_after_set.encode())), _SCHEMA.error_log
    round_tripped = XmlDocument.parser().from_string(xml_after_set, Design)
    assert XmlDocument.serializer().render(round_tripped) == xml_after_set

    assert api.removeAdHocConnectionTiedValue(get_handle(connection))
    xml_after_remove = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_after_remove.encode())), _SCHEMA.error_log
    parsed_after_remove = XmlDocument.parser().from_string(xml_after_remove, Design)
    assert XmlDocument.serializer().render(parsed_after_remove) == xml_after_remove


_CONTRACTS = {
    "getAdHocConnectionTiedValue": (("adHocConnectionID",), (str,), str | None),
    "getAdHocConnectionTiedValueExpression": (("adHocConnectionID",), (str,), str | None),
    "getAdHocConnectionTiedValueID": (("adHocConnectionID",), (str,), str | None),
    "removeAdHocConnectionTiedValue": (("adHocConnectionID",), (str,), bool),
    "setAdHocConnectionTiedValue": (("adHocConnectionID", "tiedValue"), (str, str), bool),
}


def test_tied_value_operations_export_annex_signatures() -> None:
    from amal.eda.accellera.ipxact.v1685_2022 import tgi

    assert set(_CONTRACTS) <= set(api.__all__)
    for name, (parameters, parameter_types, return_type) in _CONTRACTS.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameters
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type


def test_tied_value_getters_and_mutators_document_their_standard_sections() -> None:
    for name in _CONTRACTS:
        doc = inspect.getdoc(getattr(api, name))
        assert "Section: F.7." in doc
