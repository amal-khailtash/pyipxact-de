from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.generator_ref import GeneratorRef
from org.accellera.ipxact.v1685_2022.string_expression import StringExpression
from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import (
    UnsignedBitExpression,
)
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class LinkerCommandFile:
    """
    Specifies a linker command file.

    :ivar name: Linker command file name.
    :ivar command_line_switch: The command line switch to specify the
        linker command file.
    :ivar enable: Specifies whether to generate and enable the linker
        command file.
    :ivar generator_ref:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "linkerCommandFile"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    name: StringExpression = field(
        metadata={
            "type": "Element",
        }
    )
    command_line_switch: StringExpression = field(
        metadata={
            "name": "commandLineSwitch",
            "type": "Element",
        }
    )
    enable: UnsignedBitExpression = field(
        metadata={
            "type": "Element",
        }
    )
    generator_ref: Sequence[GeneratorRef] = field(
        default_factory=list,
        metadata={
            "name": "generatorRef",
            "type": "Element",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
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
