from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.file_set import FileSet

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class FileSets:
    """
    List of file sets associated with component.
    """

    class Meta:
        name = "fileSets"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    file_set: Sequence[FileSet] = field(
        default_factory=list,
        metadata={
            "name": "fileSet",
            "type": "Element",
        },
    )
