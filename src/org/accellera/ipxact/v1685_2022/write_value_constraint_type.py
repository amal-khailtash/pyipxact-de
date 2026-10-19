from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import (
    UnsignedBitVectorExpression,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class WriteValueConstraintType:
    """
    A constraint on the values that can be written to this field.

    Absence of this element implies that any value that fits can be written
    to it.
    """

    class Meta:
        name = "writeValueConstraintType"

    choice: Sequence[
        WriteValueConstraintType.WriteAsRead
        | WriteValueConstraintType.UseEnumeratedValues
        | WriteValueConstraintType.Minimum
        | WriteValueConstraintType.Maximum
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "writeAsRead",
                    "type": ForwardRef("WriteValueConstraintType.WriteAsRead"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "useEnumeratedValues",
                    "type": ForwardRef(
                        "WriteValueConstraintType.UseEnumeratedValues"
                    ),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "minimum",
                    "type": ForwardRef("WriteValueConstraintType.Minimum"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "maximum",
                    "type": ForwardRef("WriteValueConstraintType.Maximum"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            ),
            "max_occurs": 2,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class WriteAsRead:
        value: bool = field()

    @dataclass(slots=True, kw_only=True)
    class UseEnumeratedValues:
        value: bool = field()

    @dataclass(slots=True, kw_only=True)
    class Minimum(UnsignedBitVectorExpression):
        pass

    @dataclass(slots=True, kw_only=True)
    class Maximum(UnsignedBitVectorExpression):
        pass
