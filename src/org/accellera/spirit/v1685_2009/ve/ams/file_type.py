from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.ams.file_type_value import (
    FileTypeValue,
)

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0"
)


@dataclass(slots=True, kw_only=True)
class FileType:
    """
    Enumerated file types known by Standard PDP Extension.
    """

    class Meta:
        name = "fileType"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0"
        )

    value: FileTypeValue = field()
