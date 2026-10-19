from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class TransTypeDef:
    """
    Definition of a single transactional type defintion.

    :ivar type_name: The name of the port type. Can be any predefined
        type such sc_port or sc_export in SystemC or any user-defined
        type such as tlm_port.
    :ivar type_definition: Where the definition of the type is
        contained. For SystemC and SystemVerilog it is the include file
        containing the type definition.
    """

    class Meta:
        name = "transTypeDef"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    type_name: TransTypeDef.TypeName = field(
        metadata={
            "name": "typeName",
            "type": "Element",
        }
    )
    type_definition: Sequence[str] = field(
        default_factory=list,
        metadata={
            "name": "typeDefinition",
            "type": "Element",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class TypeName:
        """
        :ivar value:
        :ivar constrained: Defines that the type for the port has
            constrainted the number of bits in the vector
        """

        value: str = field(default="")
        constrained: bool = field(
            default=False,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
