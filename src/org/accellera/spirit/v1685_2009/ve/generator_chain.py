from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1685_2009.ve.choices import Choices
from org.accellera.spirit.v1685_2009.ve.description import Description
from org.accellera.spirit.v1685_2009.ve.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.generator import Generator
from org.accellera.spirit.v1685_2009.ve.generator_selector_type import (
    GeneratorSelectorType,
)
from org.accellera.spirit.v1685_2009.ve.group_selector import GroupSelector
from org.accellera.spirit.v1685_2009.ve.library_ref_type import LibraryRefType
from org.accellera.spirit.v1685_2009.ve.vendor_extensions import (
    VendorExtensions,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class GeneratorChain:
    """
    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar
        generator_chain_selector_or_component_generator_selector_or_generator:
    :ivar chain_group: Identifies this generator chain as belonging to
        the named group. This is used by other generator chains to
        select this chain for programmatic inclusion.
    :ivar display_name:
    :ivar description:
    :ivar choices:
    :ivar vendor_extensions:
    :ivar hidden: If this attribute is true then the generator should
        not be presented to the user, it may be part of a chain and has
        no useful meaning when invoked standalone.
    """

    class Meta:
        name = "generatorChain"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

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
    version: str = field(
        metadata={
            "type": "Element",
        }
    )
    generator_chain_selector_or_component_generator_selector_or_generator: Sequence[
        GeneratorChain.GeneratorChainSelector
        | GeneratorSelectorType
        | Generator
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "generatorChainSelector",
                    "type": ForwardRef(
                        "GeneratorChain.GeneratorChainSelector"
                    ),
                },
                {
                    "name": "componentGeneratorSelector",
                    "type": GeneratorSelectorType,
                },
                {
                    "name": "generator",
                    "type": Generator,
                },
            ),
        },
    )
    chain_group: Sequence[str] = field(
        default_factory=list,
        metadata={
            "name": "chainGroup",
            "type": "Element",
        },
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    choices: None | Choices = field(
        default=None,
        metadata={
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
    hidden: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class GeneratorChainSelector:
        """
        :ivar group_selector_or_generator_chain_ref:
        :ivar unique: Specifies that only a single generator is valid in
            this context. If more that one generator is selcted based on
            the selection criteria, DE will prompt the user to resolve
            to a single generator.
        """

        group_selector_or_generator_chain_ref: (
            None | GroupSelector | LibraryRefType
        ) = field(
            default=None,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "groupSelector",
                        "type": GroupSelector,
                    },
                    {
                        "name": "generatorChainRef",
                        "type": LibraryRefType,
                    },
                ),
            },
        )
        unique: bool = field(
            default=False,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
