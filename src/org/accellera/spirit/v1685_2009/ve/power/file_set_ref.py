from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class FileSetRef:
    """
    A reference to a fileSet.

    :ivar local_name: Refers to a fileSet defined within this
        description.
    """

    class Meta:
        name = "fileSetRef"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    local_name: None | str = field(
        default=None,
        metadata={
            "name": "localName",
            "type": "Element",
        },
    )
