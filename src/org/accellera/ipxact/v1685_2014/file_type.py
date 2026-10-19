from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.simple_file_type import SimpleFileType

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class FileType:
    """
    Enumerated file types known by IP-XACT.
    """

    class Meta:
        name = "fileType"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    value: SimpleFileType = field()
    user: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )
