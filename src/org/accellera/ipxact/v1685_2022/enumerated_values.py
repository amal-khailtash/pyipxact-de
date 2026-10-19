from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.enumerated_value_type import (
    EnumeratedValueType,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class EnumeratedValues:
    """
    Enumerates specific values that can be assigned to the bit field.
    """

    class Meta:
        name = "enumeratedValues"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    enumeration_definition_ref_or_enumerated_value: Sequence[
        EnumeratedValues.EnumerationDefinitionRef | EnumeratedValueType
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "enumerationDefinitionRef",
                    "type": ForwardRef(
                        "EnumeratedValues.EnumerationDefinitionRef"
                    ),
                },
                {
                    "name": "enumeratedValue",
                    "type": EnumeratedValueType,
                },
            ),
        },
    )

    @dataclass(slots=True, kw_only=True)
    class EnumerationDefinitionRef:
        value: str = field(default="")
        type_definitions: str = field(
            metadata={
                "name": "typeDefinitions",
                "type": "Attribute",
            }
        )
