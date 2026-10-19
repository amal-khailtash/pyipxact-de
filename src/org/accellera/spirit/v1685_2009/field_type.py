from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.access import Access
from org.accellera.spirit.v1685_2009.description import Description
from org.accellera.spirit.v1685_2009.display_name import DisplayName
from org.accellera.spirit.v1685_2009.enumerated_values import EnumeratedValues
from org.accellera.spirit.v1685_2009.field_type_modified_write_value import (
    FieldTypeModifiedWriteValue,
)
from org.accellera.spirit.v1685_2009.field_type_read_action import (
    FieldTypeReadAction,
)
from org.accellera.spirit.v1685_2009.format_type import FormatType
from org.accellera.spirit.v1685_2009.parameters import Parameters
from org.accellera.spirit.v1685_2009.range_type_type import RangeTypeType
from org.accellera.spirit.v1685_2009.resolve_type import ResolveType
from org.accellera.spirit.v1685_2009.testable_test_constraint import (
    TestableTestConstraint,
)
from org.accellera.spirit.v1685_2009.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1685_2009.volatile import Volatile
from org.accellera.spirit.v1685_2009.write_value_constraint_type import (
    WriteValueConstraintType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class FieldType:
    """
    A field within a register.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar bit_offset: Offset of this field's bit 0 from bit 0 of the
        register.
    :ivar type_identifier: Identifier name used to indicate that
        multiple field elements contain the exact same information for
        the elements in the fieldDefinitionGroup.
    :ivar bit_width: Width of the field in bits.
    :ivar volatile: Indicates whether the data is volatile. The presumed
        value is 'false' if not present.
    :ivar access:
    :ivar enumerated_values:
    :ivar modified_write_value: If present this element describes the
        modification of field data caused by a write operation.
        'oneToClear' means that in a bitwise fashion each write data bit
        of a one will clear the corresponding bit in the field.
        'oneToSet' means that in a bitwise fashion each write data bit
        of a one will set the corresponding bit in the field.
        'oneToToggle' means that in a bitwise fashion each write data
        bit of a one will toggle the corresponding bit in the field.
        'zeroToClear' means that in a bitwise fashion each write data
        bit of a zero will clear the corresponding bit in the field.
        'zeroToSet' means that in a bitwise fashion each write data bit
        of a zero will set the corresponding bit in the field.
        'zeroToToggle' means that in a bitwise fashion each write data
        bit of a zero will toggle the corresponding bit in the field.
        'clear' means any write to this field clears the field. 'set'
        means any write to the field sets the field. 'modify' means any
        write to this field may modify that data. If this element is not
        present the write operation data is written.
    :ivar write_value_constraint: The legal values that may be written
        to a field. If not specified the legal values are not specified.
    :ivar read_action: A list of possible actions for a read to set the
        field after the read. 'clear' means that after a read the field
        is cleared. 'set' means that after a read the field is set.
        'modify' means after a read the field is modified. If not
        present the field value is not modified after a read.
    :ivar testable: Can the field be tested with an automated register
        test routine. The presumed value is true if not specified.
    :ivar parameters:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "fieldType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    bit_offset: int = field(
        metadata={
            "name": "bitOffset",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    type_identifier: None | str = field(
        default=None,
        metadata={
            "name": "typeIdentifier",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    bit_width: FieldType.BitWidth = field(
        metadata={
            "name": "bitWidth",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    access: None | Access = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    enumerated_values: None | EnumeratedValues = field(
        default=None,
        metadata={
            "name": "enumeratedValues",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    modified_write_value: None | FieldTypeModifiedWriteValue = field(
        default=None,
        metadata={
            "name": "modifiedWriteValue",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    write_value_constraint: None | WriteValueConstraintType = field(
        default=None,
        metadata={
            "name": "writeValueConstraint",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    read_action: None | FieldTypeReadAction = field(
        default=None,
        metadata={
            "name": "readAction",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    testable: None | FieldType.Testable = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class BitWidth:
        value: int = field()
        format: FormatType = field(
            default=FormatType.LONG,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        any_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##any",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Testable:
        """
        :ivar value:
        :ivar test_constraint: Constraint for an automated register test
            routine. 'unconstrained' (default) means may read and write
            all legal values. 'restore' means may read and write legal
            values but the value must be restored to the initially read
            value before accessing another register. 'writeAsRead' has
            limitations on testability where only the value read before
            a write may be written to the field. 'readOnly' has
            limitations on testability where values may only be read
            from the field.
        """

        value: bool = field()
        test_constraint: TestableTestConstraint = field(
            default=TestableTestConstraint.UNCONSTRAINED,
            metadata={
                "name": "testConstraint",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
