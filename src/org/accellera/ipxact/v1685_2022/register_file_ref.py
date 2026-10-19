from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.indices import Indices

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class RegisterFileRef:
    class Meta:
        name = "registerFileRef"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    indices: None | Indices = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    register_file_ref: str = field(
        metadata={
            "name": "registerFileRef",
            "type": "Attribute",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )
