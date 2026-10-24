"""Complete contracts for the remaining abstraction-definition TGI operations."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.abstraction_def_port_constraints_type import (
    AbstractionDefPortConstraintsType,
)
from org.accellera.ipxact.v1685_2022.cell_class_value_type import CellClassValueType
from org.accellera.ipxact.v1685_2022.cell_function_value_type import CellFunctionValueType
from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint
from org.accellera.ipxact.v1685_2022.kind import Kind
from org.accellera.ipxact.v1685_2022.kind_type import KindType
from org.accellera.ipxact.v1685_2022.load_constraint import LoadConstraint
from org.accellera.ipxact.v1685_2022.payload import Payload
from org.accellera.ipxact.v1685_2022.payload_type import PayloadType
from org.accellera.ipxact.v1685_2022.protocol import Protocol
from org.accellera.ipxact.v1685_2022.protocol_type_type import ProtocolTypeType
from org.accellera.ipxact.v1685_2022.requires_driver import RequiresDriver
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import (
    UnsignedBitVectorExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import (
    UnsignedPositiveIntExpression,
)


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def make_root(style="wire"):
    root_id = top_element.createAbstractionDef(
        ("vendor", "library", f"abstraction-{style}", "1.0"),
        ("vendor", "library", "bus", "1.0"),
        "data",
        style,
    )
    return root_id, api.getAbstractionDefPortIDs(root_id)[0]


def test_extends_reference_sequence_setter_and_remover_invalidate_reference_handle():
    root_id, _ = make_root()
    root = resolve_handle(root_id)
    assert api.getAbstractionDefExtendsRefByVLNV(root_id) == (None, None, None, None)

    assert api.setAbstractionDefExtends(root_id, ("vendor2", "library2", "base", "2.0"))
    assert api.getAbstractionDefExtendsRefByVLNV(root_id) == (
        "vendor2", "library2", "base", "2.0"
    )
    extends_id = get_handle(root.extends)
    with pytest.raises(TgiError) as error:
        api.setAbstractionDefExtends(root_id, ("vendor3", "", "base", "3.0"))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.extends.vendor == "vendor2"
    assert resolve_handle(extends_id) is root.extends
    loaded = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(root), AbstractionDefinition
    )
    assert loaded.extends == root.extends

    assert api.setAbstractionDefExtends(root_id, ("vendor3", "library3", "new-base", "3.0"))
    assert resolve_handle(extends_id) is None
    replacement_id = get_handle(root.extends)
    owner = get_parent_info(replacement_id)
    assert owner.parent_handle == root_id
    assert owner.path == ("extends",)
    assert owner.container == "single"

    assert api.removeAbstractionDefExtends(root_id)
    assert root.extends is None
    assert resolve_handle(replacement_id) is None
    assert not api.removeAbstractionDefExtends(root_id)
    with pytest.raises(TgiError) as error:
        api.getAbstractionDefExtendsRefByVLNV("missing")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_port_name_and_match_setters_and_match_remover():
    _, port_id = make_root()
    port = resolve_handle(port_id)
    assert api.getAbstractionDefPortLogicalName(port_id) == "data"
    assert api.getAbstractionDefPortMatch(port_id) is None
    assert api.setAbstractionDefPortLogicalName(port_id, "payload")
    assert api.setAbstractionDefPortMatch(port_id, False)
    assert api.getAbstractionDefPortLogicalName(port_id) == "payload"
    assert api.getAbstractionDefPortMatch(port_id) is False
    assert api.setAbstractionDefPortMatch(port_id, True)
    assert api.getAbstractionDefPortMatch(port_id) is True
    assert api.removeAbstractionDefPortMatch(port_id)
    assert port.match is None
    assert not api.removeAbstractionDefPortMatch(port_id)

    with pytest.raises(TgiError) as error:
        api.setAbstractionDefPortMatch(port_id, 1)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    with pytest.raises(TgiError) as error:
        api.setAbstractionDefPortLogicalName(port_id, "  ")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_transactional_bus_width_getter_uses_the_supplied_mode_handle():
    _, port_id = make_root("transactional")
    modes = [api.addAbstractionDefPortMode(port_id, "onInitiator"),
             api.addAbstractionDefPortMode(port_id, "onTarget"),
             api.addAbstractionDefPortMode(port_id, "onSystem")]
    api.setOnSystemGroup(modes[2], "system")
    values = ("8'd32", "WIDTH + 1", "08")
    for mode_id, value in zip(modes, values, strict=True):
        mode = resolve_handle(mode_id)
        mode.bus_width = UnsignedPositiveIntExpression(value=value)

    assert [api.getAbstractionDefPortTransactionalModeBusWidth(mode) for mode in modes] == [32, None, 8]
    assert api.getAbstractionDefPortTransactionalModeBusWidth(modes[0]) == 32
    with pytest.raises(TgiError) as error:
        api.getAbstractionDefPortTransactionalModeBusWidth(port_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.getAbstractionDefPortTransactionalModeBusWidth("missing")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_wire_default_value_and_mode_width_getters_resolve_wire_choice_and_each_mode():
    _, port_id = make_root("wire")
    port = resolve_handle(port_id)
    wire = port.wire_or_transactional
    assert api.getAbstractionDefPortWireDefaultValue(port_id) is None
    wire.default_value_or_requires_driver = UnsignedBitVectorExpression(value="8'h2a + 1")
    assert api.getAbstractionDefPortWireDefaultValue(port_id) == 43
    wire.default_value_or_requires_driver = UnsignedBitVectorExpression(value="VALUE + 1")
    assert api.getAbstractionDefPortWireDefaultValue(port_id) is None
    wire.default_value_or_requires_driver = UnsignedBitVectorExpression(value="2.5")
    assert api.getAbstractionDefPortWireDefaultValue(port_id) is None
    wire.default_value_or_requires_driver = RequiresDriver()
    assert api.getAbstractionDefPortWireDefaultValue(port_id) is None

    modes = [api.addAbstractionDefPortMode(port_id, "onInitiator"),
             api.addAbstractionDefPortMode(port_id, "onTarget"),
             api.addAbstractionDefPortMode(port_id, "onSystem")]
    api.setOnSystemGroup(modes[2], "system")
    values = ("8'd16", "WIDTH", "2 * 4")
    for mode_id, value in zip(modes, values, strict=True):
        resolve_handle(mode_id).width = UnsignedPositiveIntExpression(value=value)
    assert [api.getAbstractionDefPortWireModeWidth(mode) for mode in modes] == [16, None, 8]
    with pytest.raises(TgiError) as error:
        api.getAbstractionDefPortWireModeWidth(port_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.getAbstractionDefPortWireModeWidth("missing")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_packet_getters_report_explicit_endianness_and_evaluate_integer_expressions():
    _, port_id = make_root()
    packet_id = api.addAbstractionDefPortPacket(port_id, "header", "opcode", "8'd8")
    field_id = api.getPacketPacketFieldIDs(packet_id)[0]
    field = resolve_handle(field_id)

    assert api.getPacketEndianness(packet_id) is None
    assert api.getPacketFieldEndianness(field_id) is None
    assert api.setPacketEndianness(packet_id, "big")
    # Annex F reports the value defined on the field; inherited packet
    # endianness is consumed as model semantics but is not a field value.
    assert api.getPacketFieldEndianness(field_id) is None
    assert api.setPacketFieldEndianness(field_id, "little")
    assert api.getPacketEndianness(packet_id) == "big"
    assert api.getPacketFieldEndianness(field_id) == "little"
    assert api.getPacketFieldWidth(field_id) == 8

    field.value = UnsignedBitVectorExpression(value="8'b00101010")
    assert api.getPacketFieldValue(field_id) == 42
    field.value = UnsignedBitVectorExpression(value="DATA + 1")
    assert api.getPacketFieldValue(field_id) is None
    field.value = UnsignedBitVectorExpression(value="8'h2a + 1")
    assert api.getPacketFieldValue(field_id) == 43
    field.value = UnsignedBitVectorExpression(value="2.5")
    assert api.getPacketFieldValue(field_id) is None
    field.width = UnsignedPositiveIntExpression(value="WIDTH")
    assert api.getPacketFieldWidth(field_id) is None
    field.width = UnsignedPositiveIntExpression(value="4 * 4")
    assert api.getPacketFieldWidth(field_id) == 16

    loaded = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(resolve_handle(port_id)), AbstractionDefinition.Ports.Port
    )
    loaded_packet = get_handle(loaded.packets.packet[0])
    loaded_field = get_handle(loaded.packets.packet[0].packet_fields.packet_field[0])
    assert api.getPacketEndianness(loaded_packet) == "big"
    assert api.getPacketFieldEndianness(loaded_field) == "little"


def test_custom_and_mandatory_attribute_removers_edit_mode_attributes_only():
    _, port_id = make_root("transactional")
    mode_id = api.addAbstractionDefPortMode(port_id, "onInitiator")
    mode = resolve_handle(mode_id)
    mode.kind = Kind(value=KindType.CUSTOM, custom="vendor-mode")
    mode.protocol = Protocol(
        protocol_type=Protocol.ProtocolType(value=ProtocolTypeType.CUSTOM, custom="vendor-protocol"),
        payload=Payload(
            type_value=PayloadType.GENERIC,
            extension=Payload.Extension(value="vendor-extension", mandatory=True),
        ),
    )
    kind_id = get_handle(mode.kind)
    extension_id = get_handle(mode.protocol.payload.extension)

    assert api.removeCustomAttribute(mode_id)
    assert mode.kind.value is KindType.CUSTOM
    assert mode.kind.custom is None
    assert resolve_handle(kind_id) is mode.kind
    assert not api.removeCustomAttribute(mode_id)

    assert api.removeMandatoryAttribute(mode_id)
    assert mode.protocol.payload.extension.value == "vendor-extension"
    assert mode.protocol.payload.extension.mandatory is False
    assert resolve_handle(extension_id) is mode.protocol.payload.extension
    assert not api.removeMandatoryAttribute(mode_id)
    assert not api.removeCustomAttribute(port_id)
    assert not api.removeMandatoryAttribute("missing")


def test_mode_constraint_setters_follow_choice_order_and_schema_limits(tmp_path):
    constraints = AbstractionDefPortConstraintsType()
    constraints_id = get_handle(constraints)
    assert api.setModeConstraintsLoadConstraint(constraints_id, "combinational")
    assert api.setModeConstraintsDriveConstraint(constraints_id, "buf")
    assert [type(item) for item in constraints.drive_constraint_or_load_constraint] == [
        DriveConstraint, LoadConstraint
    ]
    first_cell = constraints.drive_constraint_or_load_constraint[0].cell_specification
    assert first_cell.cell_function_or_cell_class.value is CellFunctionValueType.BUF
    assert (
        constraints.drive_constraint_or_load_constraint[1].cell_specification.cell_function_or_cell_class
        is CellClassValueType.COMBINATIONAL
    )

    with pytest.raises(TgiError) as error:
        api.setModeConstraintsDriveConstraint(constraints_id, "inv")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    with pytest.raises(TgiError) as error:
        api.setModeConstraintsLoadConstraint(constraints_id, "nand2")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    with pytest.raises(TgiError) as error:
        api.setModeConstraintsLoadConstraint("missing", "buf")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    root_id, port_id = make_root("wire")
    mode_id = api.addAbstractionDefPortMode(port_id, "onInitiator")
    resolve_handle(mode_id).mode_constraints = constraints
    serialized = XmlDocument.serializer().render(resolve_handle(root_id))
    path = tmp_path / "abstraction-definition.xml"
    path.write_text(serialized)
    from amal.eda.ipxact_de.xml_validation import validate_ipxact_xml

    result = validate_ipxact_xml(path, schema_root="submodules/accellera-schemas")
    assert result.ok, result.issues
