from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.name_value_type_type import NameValueTypeType
from org.accellera.spirit.v1_2.signal import Signal
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1_2.view_type import ViewType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class ModelType:
    """
    Hardware model information.

    :ivar views: View container
    :ivar signals: Signal container
    :ivar model_parameters: Model parameter name value pairs container
    :ivar vendor_extensions:
    """

    class Meta:
        name = "modelType"

    views: None | ModelType.Views = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    signals: None | ModelType.Signals = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    model_parameters: None | ModelType.ModelParameters = field(
        default=None,
        metadata={
            "name": "modelParameters",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
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
    class Views:
        view: Sequence[ViewType] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Signals:
        signal: Sequence[Signal] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class ModelParameters:
        """
        :ivar model_parameter: A model parameter name value pair. The
            name is given in an attribute. The value is the element
            value. The dataType (applicable to high level modeling) is
            given in the dataType attribute. For hardware based models,
            the name should be identical to the RTL (VHDL generic or
            Verilog parameter)
        """

        model_parameter: Sequence[NameValueTypeType] = field(
            default_factory=list,
            metadata={
                "name": "modelParameter",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
