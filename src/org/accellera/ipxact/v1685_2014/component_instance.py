from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.configurable_library_ref_type import (
    ConfigurableLibraryRefType,
)
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.instance_name import InstanceName
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class ComponentInstance:
    """
    Component instance element.

    The instance name is contained in the unique-value instanceName
    attribute.

    :ivar instance_name:
    :ivar display_name:
    :ivar description:
    :ivar is_present:
    :ivar component_ref: References a component to be found in an
        external library.  The four attributes define the VLNV of the
        referenced element.
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "componentInstance"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    instance_name: InstanceName = field(
        metadata={
            "name": "instanceName",
            "type": "Element",
        }
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
    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
        },
    )
    component_ref: ConfigurableLibraryRefType = field(
        metadata={
            "name": "componentRef",
            "type": "Element",
        }
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )
