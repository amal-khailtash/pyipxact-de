from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.assertions import Assertions
from org.accellera.ipxact.v1685_2022.choices import Choices
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import (
    ConfigurableLibraryRefType,
)
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.generator import Generator
from org.accellera.ipxact.v1685_2022.generator_selector_type import (
    GeneratorSelectorType,
)
from org.accellera.ipxact.v1685_2022.group_selector import GroupSelector
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class GeneratorChain:
    """
    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar display_name: Name for display purposes. Typically a few words
        providing a more detailed and/or user-friendly name than the
        vlnv.
    :ivar short_description:
    :ivar description:
    :ivar
        generator_chain_selector_or_component_generator_selector_or_generator:
    :ivar chain_group: Identifies this generator chain as belonging to
        the named group. This is used by other generator chains to
        select this chain for programmatic inclusion.
    :ivar choices:
    :ivar parameters:
    :ivar assertions:
    :ivar vendor_extensions:
    :ivar hidden: If this attribute is true then the generator should
        not be presented to the user, it may be part of a chain and has
        no useful meaning when invoked standalone.
    :ivar id:
    """

    class Meta:
        name = "generatorChain"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

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
    display_name: None | str = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
        },
    )
    short_description: None | ShortDescription = field(
        default=None,
        metadata={
            "name": "shortDescription",
            "type": "Element",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
        },
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
    chain_group: Sequence[GeneratorChain.ChainGroup] = field(
        default_factory=list,
        metadata={
            "name": "chainGroup",
            "type": "Element",
        },
    )
    choices: None | Choices = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    assertions: None | Assertions = field(
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
    class ChainGroup:
        value: str = field(default="")
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
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
        :ivar id:
        """

        group_selector_or_generator_chain_ref: (
            None | GroupSelector | ConfigurableLibraryRefType
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
                        "type": ConfigurableLibraryRefType,
                    },
                ),
            },
        )
        unique: bool = field(
            default=False,
            metadata={
                "type": "Attribute",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )
