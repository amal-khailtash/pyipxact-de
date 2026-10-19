from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.configuration import Configuration
from org.accellera.spirit.v1_2.instance_name import InstanceName
from org.accellera.spirit.v1_2.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


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
    :ivar vendor_extensions:
    """

    class Meta:
        name = "componentInstance"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

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
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
        },
    )
