from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_2.choices import Choices
from org.accellera.spirit.v1_2.generator import Generator
from org.accellera.spirit.v1_2.generator_selector_type import (
    GeneratorSelectorType,
)
from org.accellera.spirit.v1_2.group_selector import GroupSelector
from org.accellera.spirit.v1_2.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_2.parameter import Parameter

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class GeneratorChain:
    """
    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version:
    :ivar
        file_generator_selector_or_component_generator_selector_or_generator:
    :ivar chain_group: Identifies this generator chain as belonging to
        the named group. This is used by other generator chains to
        select this chain for programmatic inclusion.
    :ivar parameter:
    :ivar choices:
    """

    class Meta:
        name = "generatorChain"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

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
    file_generator_selector_or_component_generator_selector_or_generator: Sequence[
        GeneratorChain.FileGeneratorSelector
        | GeneratorSelectorType
        | Generator
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "fileGeneratorSelector",
                    "type": ForwardRef("GeneratorChain.FileGeneratorSelector"),
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
    parameter: Sequence[Parameter] = field(
        default_factory=list,
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

    @dataclass(slots=True, kw_only=True)
    class FileGeneratorSelector:
        group_selector_or_file_name: None | GroupSelector | LibraryRefType = (
            field(
                default=None,
                metadata={
                    "type": "Elements",
                    "choices": (
                        {
                            "name": "groupSelector",
                            "type": GroupSelector,
                        },
                        {
                            "name": "fileName",
                            "type": LibraryRefType,
                        },
                    ),
                },
            )
        )
        unique: bool = field(
            default=True,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
