from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_2.constraint_set_ref import ConstraintSetRef
from org.accellera.spirit.v1_2.file_builder_type import FileBuilderType
from org.accellera.spirit.v1_2.file_set_ref import FileSetRef
from org.accellera.spirit.v1_2.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_2.parameter import Parameter
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1_2.whitebox_element_ref_type import (
    WhiteboxElementRefType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class ViewType:
    """
    :ivar name: Name of the view. Must be unique within a component.
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
        default="default",
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    env_identifier: Sequence[str] = field(
        default_factory=list,
        metadata={
            "name": "envIdentifier",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            "min_occurs": 1,
            "pattern": r"[a-zA-Z0-9_+\*\.]*:[a-zA-Z0-9_+\*\.]*:[a-zA-Z0-9_+\*\.]*",
        },
    )
    choice: Sequence[
        LibraryRefType
        | ViewType.Language
        | str
        | FileBuilderType
        | FileSetRef
        | ConstraintSetRef
        | ViewType.WhiteboxElementRefs
        | Parameter
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "hierarchyRef",
                    "type": LibraryRefType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "language",
                    "type": ForwardRef("ViewType.Language"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "modelName",
                    "type": str,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "defaultFileBuilder",
                    "type": FileBuilderType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "fileSetRef",
                    "type": FileSetRef,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "constraintSetRef",
                    "type": ConstraintSetRef,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "whiteboxElementRefs",
                    "type": ForwardRef("ViewType.WhiteboxElementRefs"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "parameter",
                    "type": Parameter,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
            ),
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Language:
        value: str = field(default="")
        strict: None | bool = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
