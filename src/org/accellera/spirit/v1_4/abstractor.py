from __future__ import annotations

from dataclasses import dataclass

from org.accellera.spirit.v1_4.abstractor_type import AbstractorType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class Abstractor(AbstractorType):
    """
    This is the root element for abstractors.
    """

    class Meta:
        name = "abstractor"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"
