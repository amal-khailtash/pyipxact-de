from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.access_type import AccessType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class Access:
    """
    Indicates the accessibility of the data in the address block.

    Possible values are 'read-write', 'read-only' and 'write-only'.
    """

    class Meta:
        name = "access"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    value: AccessType = field()
