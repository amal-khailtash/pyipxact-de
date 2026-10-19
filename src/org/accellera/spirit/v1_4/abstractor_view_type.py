from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_4.file_builder_type import FileBuilderType
from org.accellera.spirit.v1_4.file_set_ref import FileSetRef
from org.accellera.spirit.v1_4.parameters import Parameters
from org.accellera.spirit.v1_4.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class AbstractorViewType:
    """
    Abstraction view type.

    :ivar name: Unique name
    :ivar display_name: Element name for display purposes. Typically a
        few words providing a more detailed and/or user-friendly name
        than the spirit:name.
    :ivar description: Full description string, typically for
        documentation
    :ivar env_identifier: Defines the hardware environment in which this
        view applies. The format of the string is
        language:tool:vendor_extension, with each piece being optional.
        The language must be one of the types from spirit:fileType. The
        tool values are defined by the SPIRIT Consortium, and include
        generic values "*Simulation" and "*Synthesis" to imply any tool
        of the indicated type. Having more than one envIdentifier
        indicates that the view applies to multiple environments.
    :ivar language: The hardware description language used such as
        "verilog" or "vhdl". If the attribute "strict" is "true", this
        value must match the language being generated for the design.
    :ivar model_name: Language specific name to identity the model.
        Verilog or SystemVerilog this is the module name. For VHDL this
        is, with ()’s, the entity(architecture) name pair or without a
        single configuration name.  For SystemC this is the class name.
    :ivar default_file_builder: Default command and flags used to build
        derived files from the sourceName files in the referenced file
        sets.
    :ivar file_set_ref:
    :ivar parameters:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "abstractorViewType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )
    display_name: None | str = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    description: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    env_identifier: Sequence[str] = field(
        default_factory=list,
        metadata={
            "name": "envIdentifier",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            "min_occurs": 1,
            "pattern": r"[a-zA-Z0-9_+\*\.]*:[a-zA-Z0-9_+\*\.]*:[a-zA-Z0-9_+\*\.]*",
        },
    )
    language: None | AbstractorViewType.Language = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    model_name: None | str = field(
        default=None,
        metadata={
            "name": "modelName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    default_file_builder: Sequence[FileBuilderType] = field(
        default_factory=list,
        metadata={
            "name": "defaultFileBuilder",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    file_set_ref: Sequence[FileSetRef] = field(
        default_factory=list,
        metadata={
            "name": "fileSetRef",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Language:
        """
        :ivar value:
        :ivar strict: A value of 'true' indicates that this value must
            match the language being generated for the design.
        """

        value: str = field(default="")
        strict: None | bool = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
