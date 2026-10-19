from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.ipxact_uri import IpxactUri

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class Dependency(IpxactUri):
    """
    Specifies a location on which files or fileSets may be dependent.

    Typically, this would be a directory that would contain included files.
    """

    class Meta:
        name = "dependency"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )
