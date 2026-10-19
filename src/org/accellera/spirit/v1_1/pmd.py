from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_1.name_value_pair_type import NameValuePairType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class Pmd:
    """
    The root element of the platform meta-data definition file.

    This file defines the Platform meta-data to be applied to specific IP.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this component belongs
        to.  Note that a physical library may contain components from
        multiple logical libraries.  Logical libraries are displayes in
        component browser.
    :ivar name: The name of the object.  Must match the root name of the
        XML file and the directory name it or its version directory
        belongs to.
    :ivar version:
    :ivar applies_to: Defines the components that this pmd applies to.
        When the user tries to add any of those components, this pmd
        will be applied.
    :ivar depends_on: Defines the components that  must exist in the
        current design for this pmd to apply. The pmd will only apply if
        an instance of each components declared in this list exists in
        the design. If the list is empty then this pmd file will apply
        unconditionaly.
    :ivar transformer: The transformer element contains references to
        the actual code that will make the transformation. If there are
        multiple elements, they will be applied in sequence. i.e., the
        affected component document will pass through a pipeline of
        transformers with each child element representing a step in a
        pipeline.
    """

    class Meta:
        name = "pmd"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    vendor: str = field(
        metadata={
            "type": "Element",
        }
    )
    library: str = field(
        metadata={
            "type": "Element",
        }
    )
    name: str = field(
        metadata={
            "type": "Element",
        }
    )
    version: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    applies_to: Pmd.AppliesTo = field(
        metadata={
            "name": "appliesTo",
            "type": "Element",
        }
    )
    depends_on: Pmd.DependsOn = field(
        metadata={
            "name": "dependsOn",
            "type": "Element",
        }
    )
    transformer: Pmd.Transformer = field(
        metadata={
            "type": "Element",
        }
    )

    @dataclass(slots=True, kw_only=True)
    class AppliesTo:
        """
        :ivar component_ref: A vendor-library-name-version identifier
            used to refer to components.
        """

        component_ref: Sequence[Pmd.AppliesTo.ComponentRef] = field(
            default_factory=list,
            metadata={
                "name": "componentRef",
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class ComponentRef(LibraryRefType):
            """
            :ivar display_label: A display label to override the
                original component's display label if this 3MD will
                apply.
            """

            display_label: None | str = field(
                default=None,
                metadata={
                    "name": "displayLabel",
                    "type": "Element",
                    "white_space": "collapse",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class DependsOn:
        """
        :ivar component_ref: A vendor-library-name-version identifier
            used to refer to components.
        """

        component_ref: Sequence[LibraryRefType] = field(
            default_factory=list,
            metadata={
                "name": "componentRef",
                "type": "Element",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Transformer:
        """
        :ivar xslt: An XSLT transformer that will transform the document
            based on rules defined in the xsl file mentioned here.
        """

        xslt: Sequence[Pmd.Transformer.Xslt] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Xslt:
            """
            :ivar style_sheet: The relative path to the xsl stylesheet
                to be used for transformation.
            :ivar parameter: Parameters to be passed to the xslt
                stylesheet at run time.
            """

            style_sheet: str = field(
                metadata={
                    "name": "styleSheet",
                    "type": "Element",
                }
            )
            parameter: Sequence[NameValuePairType] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                },
            )
