from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.parameter import Parameter
from org.accellera.spirit.v1_1.resolved_library_ref_type import (
    ResolvedLibraryRefType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class LooseGeneratorInvocation:
    """
    Specifies the information required to invoke a loosely coupled
    generator.

    :ivar design_file: Path to description of top level design
    :ivar bus_definition_files: The list of bus definition files
        currently in use within the design
    :ivar component_definition_files: The list of component definition
        files currently needed to define all the components within the
        design.
    :ivar parameters: List of values of configurable settings for this
        generator invocation
    :ivar selected_instances: The list of instances to be worked upon by
        the generator, no instances selected indicates whole design
    :ivar phase_number: The non-negative floating point phase number
        associated with this generator invocation
    :ivar group_name: The generator group name associated with this
        generator invocation
    """

    class Meta:
        name = "looseGeneratorInvocation"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    design_file: None | object = field(
        default=None,
        metadata={
            "name": "designFile",
            "type": "Element",
        },
    )
    bus_definition_files: (
        None | LooseGeneratorInvocation.BusDefinitionFiles
    ) = field(
        default=None,
        metadata={
            "name": "busDefinitionFiles",
            "type": "Element",
        },
    )
    component_definition_files: (
        None | LooseGeneratorInvocation.ComponentDefinitionFiles
    ) = field(
        default=None,
        metadata={
            "name": "componentDefinitionFiles",
            "type": "Element",
        },
    )
    parameters: None | LooseGeneratorInvocation.Parameters = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    selected_instances: None | LooseGeneratorInvocation.SelectedInstances = (
        field(
            default=None,
            metadata={
                "name": "selectedInstances",
                "type": "Element",
            },
        )
    )
    phase_number: float = field(
        metadata={
            "name": "phaseNumber",
            "type": "Element",
        }
    )
    group_name: str = field(
        metadata={
            "name": "groupName",
            "type": "Element",
        }
    )

    @dataclass(slots=True, kw_only=True)
    class BusDefinitionFiles:
        """
        :ivar bus_definition_file: Path to a bus definition file used
            within design. Attributes VLNV used to indicate which bus
            definition this file represents.
        """

        bus_definition_file: Sequence[ResolvedLibraryRefType] = field(
            default_factory=list,
            metadata={
                "name": "busDefinitionFile",
                "type": "Element",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class ComponentDefinitionFiles:
        """
        :ivar component_definition_file: Path to component definition
            file. This component definition is the component definition
            as it appears in the DE; i.e. after having been transformed
            by any PMD info, and including any instance specific
            settings such as parameter values. The instanceRef attribute
            is the name of the instance that this file describes.
        """

        component_definition_file: Sequence[
            LooseGeneratorInvocation.ComponentDefinitionFiles.ComponentDefinitionFile
        ] = field(
            default_factory=list,
            metadata={
                "name": "componentDefinitionFile",
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class ComponentDefinitionFile:
            """
            :ivar instance_ref: Reference handle for this component
                definition
            :ivar content:
            """

            instance_ref: str = field(
                metadata={
                    "name": "instanceRef",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                }
            )
            content: Sequence[object] = field(
                default_factory=list,
                metadata={
                    "type": "Wildcard",
                    "namespace": "##any",
                    "mixed": True,
                },
            )

    @dataclass(slots=True, kw_only=True)
    class Parameters:
        parameter: Sequence[Parameter] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class SelectedInstances:
        """
        :ivar selected_instance: Instance name of selected instance that
            the generator is expected to work upon. This may be a
            hierarchical instance name.
        """

        selected_instance: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "selectedInstance",
                "type": "Element",
                "min_occurs": 1,
            },
        )
