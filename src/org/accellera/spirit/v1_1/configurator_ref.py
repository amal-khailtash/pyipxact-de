from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class ConfiguratorRef:
    """
    A reference to a configurator element.
    """

    class Meta:
        name = "configuratorRef"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    value: str = field(default="")
