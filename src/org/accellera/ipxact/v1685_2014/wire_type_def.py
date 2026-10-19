from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class WireTypeDef:
    """
    Definition of a single wire type defintion that can relate to multiple
    views.

    :ivar type_name: The name of the logic type. Examples could be
        std_logic, std_ulogic, std_logic_vector, sc_logic, ...
    :ivar type_definition: Where the definition of the type is
        contained. For std_logic, this is contained in
        IEEE.std_logic_1164.all. For sc_logic, this is contained in
        systemc.h. For VHDL this is the library and package as defined
        by the "used" statement. For SystemC and SystemVerilog it is the
        include file required. For verilog this is not needed.
    :ivar view_ref: A reference to a view name in the file for which
        this type applies.
    :ivar id:
    """

    class Meta:
        name = "wireTypeDef"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    type_name: None | WireTypeDef.TypeName = field(
        default=None,
        metadata={
            "name": "typeName",
            "type": "Element",
        },
    )
    type_definition: Sequence[WireTypeDef.TypeDefinition] = field(
        default_factory=list,
        metadata={
            "name": "typeDefinition",
            "type": "Element",
        },
    )
    view_ref: Sequence[WireTypeDef.ViewRef] = field(
        default_factory=list,
        metadata={
            "name": "viewRef",
            "type": "Element",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
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
            },
        )

    @dataclass(slots=True, kw_only=True)
    class TypeDefinition:
        value: str = field(default="")
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class ViewRef:
        value: str = field(default="")
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )
