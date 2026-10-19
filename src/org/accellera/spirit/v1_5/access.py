from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.access_type import AccessType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class Access:
    """
    Indicates the accessibility of the data in the address bank, address
    block, register or field.

    Possible values are 'read-write', 'read-only', 'write-only',
    'writeOnce' and 'read-writeOnce'. If not specified the value is
    inherited from the containing object.
    """

    class Meta:
        name = "access"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"

    value: AccessType = field()
