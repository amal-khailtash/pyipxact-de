"""Array BASE and EXTENDED calls follow the generated IP-XACT 2022 model types."""

import pytest
from lxml import etree
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022.tgi import array as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockType,
    Array,
    Arrays,
    BitStride,
    Component,
    ComponentPortDirectionType,
    ConfigurableArrays,
    Dim,
    FieldType,
    Left,
    Model,
    ModuleParameterArrays,
    ModuleParameterType,
    Parameter,
    Port,
    PortWireType,
    RegisterFile,
    Right,
    Stride,
    UnsignedLongintExpression,
    Value,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


def _assert_schema_valid(root: Component) -> str:
    xml = XmlSerializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    return xml


def _component_with_port() -> Component:
    return Component(
        vendor="acme",
        library="test",
        name="array-test",
        version="1.0",
        model=Model(
            ports=Model.Ports(
                port=[
                    Port(
                        name="data",
                        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
                    )
                ]
            )
        ),
    )


@pytest.mark.parametrize(
    ("parent_factory", "wrapper_type"),
    [
        (
            lambda: Port(
                name="p", wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN)
            ),
            Arrays,
        ),
        (lambda: Parameter(name="P", value=Value(value="0")), ConfigurableArrays),
        (lambda: ModuleParameterType(name="P", value=Value(value="0")), ModuleParameterArrays),
    ],
)
def test_add_array_uses_declared_array_wrapper_and_bound_types(parent_factory, wrapper_type):
    parent = parent_factory()
    parent_id = get_handle(parent)

    array_id = api.addArray(parent_id, ["11", "0"])

    assert type(parent.arrays) is wrapper_type
    assert isinstance(resolve_handle(array_id), wrapper_type.Array)
    assert api.getArrayIDs(parent_id) == [array_id]
    assert api.getArrayRangeExpression(array_id) == ["11", "0"]
    assert api.getArrayRange(array_id) == [11, 0]
    assert api.getArrayLeftID(array_id) == api.getArrayLeftID(array_id)
    assert api.getArrayRightID(array_id) == api.getArrayRightID(array_id)


def test_extended_array_mutations_round_trip_and_pass_schema_validation():
    root = _component_with_port()
    port = root.model.ports.port[0]
    port_id = get_handle(port)
    array_id = api.addArray(port_id, ["15", "0"])

    xml = _assert_schema_valid(root)
    from xsdata.formats.dataclass.parsers import XmlParser

    reparsed = XmlParser().from_string(xml, Component)
    assert reparsed.model.ports.port[0].arrays.array[0].left.value == "15"
    assert api.getArrayIDs(port_id) == [array_id]

    # A bounded port array follows the schema choice for left/right and cannot
    # accept register/field dimensions or stride children.
    with pytest.raises(TgiError):
        api.addArrayDim(array_id, "4")
    with pytest.raises(TgiError):
        api.setArrayStride(array_id, "4")

    assert api.removeArray(array_id) is True
    assert api.getArrayIDs(port_id) == []
    assert resolve_handle(array_id) is None
    _assert_schema_valid(root)


@pytest.mark.parametrize(
    ("array", "expected_stride_type", "setter"),
    [
        (Array(dim=[Dim(value="2")]), Stride, lambda arr_id: api.setArrayStride(arr_id, "16")),
        (
            FieldType.Array(dim=[Dim(value="2")]),
            BitStride,
            lambda arr_id: api.setArrayStride(arr_id, "16"),
        ),
    ],
)
def test_register_and_field_array_edits_use_generated_stride_and_dim_types(array, expected_stride_type, setter):
    array_id = get_handle(array)
    first_dim_id = api.getArrayDimIDs(array_id)[0]
    assert setter(array_id) is True
    stride_id = api.getArrayStrideID(array_id)
    assert isinstance(resolve_handle(stride_id), expected_stride_type)
    assert api.getArrayStrideExpression(array_id) == "16"

    added_dim_id = api.addArrayDim(array_id, "${COUNT}")
    assert isinstance(resolve_handle(added_dim_id), Dim)
    assert api.getDimExpression(added_dim_id) == "${COUNT}"
    assert api.getArrayDimIDs(array_id) == [first_dim_id, added_dim_id]

    old_stride = resolve_handle(stride_id)
    assert api.setArrayStride(array_id, "32") is True
    assert resolve_handle(stride_id) is None
    assert api.getArrayStrideExpression(array_id) == "32"
    new_stride_id = api.getArrayStrideID(array_id)
    assert new_stride_id != stride_id

    assert api.removeArrayStride(array_id) is True
    assert resolve_handle(new_stride_id) is None
    assert api.getArrayStrideID(array_id) is None
    assert api.removeArrayDim(added_dim_id) is True
    assert resolve_handle(added_dim_id) is None
    assert old_stride is not None


@pytest.mark.parametrize("array", [Array(dim=[]), FieldType.Array(dim=[])])
def test_new_dimensions_and_index_variables_are_schema_bound(array):
    array_id = get_handle(array)
    first = api.addArrayDim(array_id, "${COUNT}")
    second = api.addArrayDim(array_id, "3")

    assert api.setDimIndexVar(first, "index_0") is True
    assert api.getDimIndexVar(first) == "index_0"
    assert api.getDimValue(second) == 3
    with pytest.raises(TgiError) as duplicate:
        api.setDimIndexVar(second, "index_0")
    assert duplicate.value.fault_code == "INVALID_ARGUMENT"
    assert api.getDimIndexVar(second) is None

    assert api.removeIndexVarAttribute(first) is True
    assert api.removeIndexVarAttribute(first) is False
    assert api.getDimIndexVar(first) is None


def test_remove_array_dim_preserves_the_schema_required_dimension():
    array = Array(dim=[Dim(value="1")])
    array_id = get_handle(array)
    [dim_id] = api.getArrayDimIDs(array_id)

    with pytest.raises(TgiError) as error:
        api.removeArrayDim(dim_id)

    assert error.value.fault_code == "INVALID_ARGUMENT"
    assert api.getArrayDimIDs(array_id) == [dim_id]
    assert resolve_handle(dim_id) is array.dim[0]


def test_extended_array_operations_reject_wrong_types_and_invalid_values_atomically():
    port = Port(name="p", wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN))
    port_id = get_handle(port)
    dim_array = Array(dim=[Dim(value="2")], stride=Stride(value="8"))
    dim_array_id = get_handle(dim_array)
    before = XmlSerializer().render(dim_array)

    for bad_range in (["1"], ["1", ""], "10", None):
        with pytest.raises(TgiError) as error:
            api.addArray(port_id, bad_range)
        assert error.value.fault_code == "INVALID_ARGUMENT"
    with pytest.raises(TgiError):
        api.addArrayDim(dim_array_id, "")
    with pytest.raises(TgiError):
        api.setArrayStride(dim_array_id, "")
    with pytest.raises(TgiError):
        api.setDimIndexVar(api.getArrayDimIDs(dim_array_id)[0], "bad name")
    with pytest.raises(TgiError):
        api.addArray(get_handle(dim_array), ["3", "0"])

    assert XmlSerializer().render(dim_array) == before
    assert port.arrays is None


def test_base_array_getters_reject_non_array_handles_and_handle_both_register_models():
    register = AddressBlockType.Register(
        name="r",
        address_offset=UnsignedLongintExpression(value="0"),
        array=Array(dim=[Dim(value="4")]),
    )
    register_file = RegisterFile.Register(
        name="rf",
        address_offset=UnsignedLongintExpression(value="0"),
        array=Array(dim=[Dim(value="8")]),
    )
    field = FieldType(
        name="f",
        bit_offset=UnsignedLongintExpression(value="0"),
        array=FieldType.Array(dim=[Dim(value="2")]),
    )

    for parent, getter in (
        (register, api.getRegisterArrayID),
        (register_file, api.getRegisterArrayID),
        (field, api.getRegisterFieldArrayID),
    ):
        array_id = getter(get_handle(parent))
        assert api.getArrayIDs(get_handle(parent)) == [array_id]
        assert api.getArrayDimIDs(array_id)

    with pytest.raises(TgiError):
        api.getArrayDimIDs(get_handle(Stride(value="1")))


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("8'h10", 16), ("4 * (2 + 1)", 12), ("BASE + 1", None), ("4'bx001", None)],
)
def test_numeric_array_getters_evaluate_constant_sv_and_leave_scope_refs_unresolved(expression, expected):
    array = Arrays.Array(left=Left(value=expression), right=Right(value="BASE"))
    array_id = get_handle(array)
    dim_array_id = get_handle(Array(dim=[Dim(value=expression)]))

    assert api.getArrayRange(array_id) == [expected, None]
    assert api.getDimValue(api.getArrayDimIDs(dim_array_id)[0]) == expected
