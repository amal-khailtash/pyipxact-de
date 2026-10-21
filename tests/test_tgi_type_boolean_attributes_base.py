"""BASE type/file boolean attributes retain false values after XML reload."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import File, GeneratorType, IpxactUri, LanguageType, ServiceTypeDef, TransTypeDef


@pytest.mark.parametrize(
    "name,kind,field,kwargs",
    [
        ("getExactBooleanAttribute", TransTypeDef.TypeName, "exact", {"value": "T"}),
        ("getExternalDeclarationsBooleanAttribute", File.IsIncludeFile, "external_declarations", {"value": True}),
        ("getImplicitBooleanAttribute", ServiceTypeDef.TypeName, "implicit", {"value": "T"}),
        ("getStrictBooleanAttribute", LanguageType, "strict", {"value": "systemVerilog"}),
        (
            "getHiddenBooleanAttribute",
            GeneratorType,
            "hidden",
            {"name": "generator", "generator_exe": IpxactUri(value="run.py")},
        ),
    ],
)
@pytest.mark.parametrize("value", [False, True])
def test_type_boolean(name, kind, field, kwargs, value):
    obj = kind(**kwargs, **{field: value})
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) is value
    parsed = XmlDocument.parser().from_string(before, kind)
    assert getter(get_handle(parsed)) is value
    assert XmlDocument.serializer().render(obj) == before
    assert getattr(tgi, name) is getter
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")
