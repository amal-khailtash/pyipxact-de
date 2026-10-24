"""Shared isolation for IEEE 1685-2022 model and TGI tests."""

from collections.abc import Iterator

import pytest

from amal.eda.ipxact_de.xml_document import XmlDocument


@pytest.fixture(autouse=True)
def isolated_xml_context() -> Iterator[None]:
    """Keep fragment namespace metadata from leaking between model tests."""
    context = XmlDocument.serializer().context
    context.reset()
    try:
        yield
    finally:
        context.reset()
