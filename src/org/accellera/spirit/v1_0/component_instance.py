from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.configuration import Configuration
from org.accellera.spirit.v1_0.instance_name import InstanceName
from org.accellera.spirit.v1_0.library_ref_type import LibraryRefType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class ComponentInstance:
    """
    Component instance element.

    The instance name is contained in the unique-value instanceName
    attribute.

    :ivar instance_name:
    :ivar component_ref: References a component to be found in an
        external library.  The name attribute gives the name of the
        component and the version attribute speicifies which version of
        the component to use.
    :ivar configuration:
    """

    class Meta:
        name = "componentInstance"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    instance_name: InstanceName = field(
        metadata={
            "name": "instanceName",
            "type": "Element",
        }
    )
    component_ref: LibraryRefType = field(
        metadata={
            "name": "componentRef",
            "type": "Element",
        }
    )
    configuration: None | Configuration = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
