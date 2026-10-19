from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class ConfigurableElementValue:
    """
    Describes the content of a configurable element.

    The required referenceId attribute refers to the ID attribute of the
    configurable element.

    :ivar value:
    :ivar reference_id: Refers to the ID attribute of the configurable
        element.
    """

    class Meta:
        name = "configurableElementValue"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

    value: str = field(default="")
    reference_id: str = field(
        metadata={
            "name": "referenceId",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )
