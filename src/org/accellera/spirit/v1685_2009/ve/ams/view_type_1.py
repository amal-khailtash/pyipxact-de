from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1685_2009.ve.ams.constraint_set_ref import (
    ConstraintSetRef,
)
from org.accellera.spirit.v1685_2009.ve.ams.description import Description
from org.accellera.spirit.v1685_2009.ve.ams.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.ams.file_builder_type import (
    FileBuilderType,
)
from org.accellera.spirit.v1685_2009.ve.ams.file_set_ref import FileSetRef
from org.accellera.spirit.v1685_2009.ve.ams.library_ref_type import (
    LibraryRefType,
)
from org.accellera.spirit.v1685_2009.ve.ams.parameters import Parameters
from org.accellera.spirit.v1685_2009.ve.ams.vendor_extensions import (
    VendorExtensions,
)
from org.accellera.spirit.v1685_2009.ve.ams.whitebox_element_ref_type import (
    WhiteboxElementRefType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class ViewType1:
    """
    Component view type.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar env_identifier: Defines the hardware environment in which this
        view applies. The format of the string is
        language:tool:vendor_extension, with each piece being optional.
        The language must be one of the types from spirit:fileType. The
        tool values are defined by the SPIRIT Consortium, and include
        generic values "*Simulation" and "*Synthesis" to imply any tool
        of the indicated type. Having more than one envIdentifier
        indicates that the view applies to multiple environments.
    :ivar choice:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "viewType"

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
    env_identifier: Sequence[str] = field(
        default_factory=list,
        metadata={
            "name": "envIdentifier",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            "min_occurs": 1,
            "pattern": r"[a-zA-Z0-9_+\*\.]*:[a-zA-Z0-9_+\*\.]*:[a-zA-Z0-9_+\*\.]*",
        },
    )
    choice: Sequence[
        LibraryRefType
        | ViewType1.Language
        | str
        | FileBuilderType
        | FileSetRef
        | ConstraintSetRef
        | ViewType1.WhiteboxElementRefs
        | Parameters
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "hierarchyRef",
                    "type": LibraryRefType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "language",
                    "type": ForwardRef("ViewType1.Language"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "modelName",
                    "type": str,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "defaultFileBuilder",
                    "type": FileBuilderType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "fileSetRef",
                    "type": FileSetRef,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "constraintSetRef",
                    "type": ConstraintSetRef,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "whiteboxElementRefs",
                    "type": ForwardRef("ViewType1.WhiteboxElementRefs"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "parameters",
                    "type": Parameters,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            ),
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

    @dataclass(slots=True, kw_only=True)
    class Language:
        """
        :ivar value:
        :ivar strict: A value of 'true' indicates that this value must
            match the language being generated for the design.
        """

        value: str = field(default="")
        strict: bool = field(
            default=False,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class WhiteboxElementRefs:
        """
        :ivar whitebox_element_ref: Reference to a white box element
            which is visible within this view.
        """

        whitebox_element_ref: Sequence[WhiteboxElementRefType] = field(
            default_factory=list,
            metadata={
                "name": "whiteboxElementRef",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
