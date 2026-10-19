from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_4.configurable_element_values import (
    ConfigurableElementValues,
)
from org.accellera.spirit.v1_4.instance_name import InstanceName
from org.accellera.spirit.v1_4.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_4.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class ComponentInstance:
    """
    Component instance element.

    The instance name is contained in the unique-value instanceName
    attribute.

    :ivar instance_name:
    :ivar display_name: Display name for the subcomponent instance.
    :ivar description: String for describing this component instance to
        users
    :ivar component_ref: References a component to be found in an
        external library.  The four attributes define the VLNV of the
        referenced element.
    :ivar configurable_element_values:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "componentInstance"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

    instance_name: InstanceName = field(
        metadata={
            "name": "instanceName",
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
    description: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    component_ref: LibraryRefType = field(
        metadata={
            "name": "componentRef",
            "type": "Element",
        }
    )
    configurable_element_values: None | ConfigurableElementValues = field(
        default=None,
        metadata={
            "name": "configurableElementValues",
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
