from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class WhiteboxElementRefType:
    """
    Reference to a whiteboxElement within a view.

    The 'name' attribute must refer to a whiteboxElement defined within
    this component.

    :ivar whitebox_path: The whiteboxPath elements (as a set) define the
        name(s) needed to define the entire white box element in this
        view.
    :ivar name: Reference to a whiteboxElement defined within this
        component.
    """

    class Meta:
        name = "whiteboxElementRefType"

    whitebox_path: Sequence[WhiteboxElementRefType.WhiteboxPath] = field(
        default_factory=list,
        metadata={
            "name": "whiteboxPath",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            "min_occurs": 1,
        },
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )

    @dataclass(slots=True, kw_only=True)
    class WhiteboxPath:
        """
        :ivar path_name: The view specific name for a portion of the
            white box element.
        :ivar left: Indicates the left bound value for the associated
            path name.
        :ivar right: Indicates the right bound values for the associated
            path name.
        """

        path_name: str = field(
            metadata={
                "name": "pathName",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            }
        )
        left: None | int = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        right: None | int = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
