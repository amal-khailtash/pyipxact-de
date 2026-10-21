"""BASE reference attributes return source names without resolving targets."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockRef,
    AddrSpaceRefType,
    AlternateRegisterRef,
    BankRef,
    RegisterRef,
)


@pytest.mark.parametrize(
    "name,kind,field",
    [
        ("getAddressBlockRefAttribute", AddressBlockRef, "address_block_ref"),
        ("getAddressSpaceRefAttribute", AddrSpaceRefType, "address_space_ref"),
        ("getAlternateRegisterRefAttribute", AlternateRegisterRef, "alternate_register_ref"),
        ("getBankRefAttribute", BankRef, "bank_ref"),
        ("getRegisterRefAttribute", RegisterRef, "register_ref"),
    ],
)
@pytest.mark.parametrize("source", ["target", "unresolved.target"])
def test_reference_source(name, kind, field, source):
    obj = kind(**{field: source})
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) == source
    parsed = XmlDocument.parser().from_string(before, kind)
    assert getter(get_handle(parsed)) == source
    assert getattr(tgi, name) is getter
    assert XmlDocument.serializer().render(obj) == before
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")
