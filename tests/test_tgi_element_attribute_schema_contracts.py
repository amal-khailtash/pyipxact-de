"""Attribute mutations use generated XML types across the standard API surface."""

import inspect
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from typing import get_args, get_origin, get_type_hints

import pytest

import org.accellera.ipxact.v1685_2022 as bindings
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle


def model_attributes():
    """Find concrete generated classes for each declared XML attribute."""
    found = {}
    visited = set()

    def visit(cls):
        if cls in visited or not is_dataclass(cls):
            return
        visited.add(cls)
        for field in fields(cls):
            if field.metadata.get("type") == "Attribute":
                found.setdefault(field.metadata.get("name", field.name), (cls, field))
        for child in vars(cls).values():
            if isinstance(child, type):
                visit(child)

    for cls in vars(bindings).values():
        if isinstance(cls, type):
            visit(cls)
    return found


MODELS = model_attributes()


def make_model(cls):
    """Populate required fields without bypassing the generated constructor."""
    kwargs = {}
    for field in fields(cls):
        if field.default is MISSING and field.default_factory is MISSING:
            annotation = get_type_hints(cls)[field.name]
            kwargs[field.name] = 1 if annotation in (int, float) else "required"
    return cls(**kwargs)


def attribute_sample(cls, field):
    if field.name == "invert":
        return True
    annotation = get_type_hints(cls)[field.name]
    candidates = get_args(annotation) if get_origin(annotation) else (annotation,)
    enum = next((kind for kind in candidates if inspect.isclass(kind) and issubclass(kind, Enum)), None)
    if enum:
        return next(iter(enum)).value
    if bool in candidates:
        return True
    if int in candidates:
        return 2
    if float in candidates:
        return 2.5
    if field.metadata.get("tokens"):
        return ["first", "second"]
    return "attribute-value"


SETTERS = [
    (name, attr)
    for name, attr, kind in api._EXTENDED_ATTRIBUTE_FUNCS
    if name.startswith("set") and attr in MODELS and name != "setOtherAnyAttribute"
]


@pytest.mark.parametrize("name,attribute", SETTERS)
def test_named_setters_target_xml_field_and_reject_wrong_primitive(name, attribute):
    cls, field = MODELS[attribute]
    obj = make_model(cls)
    sample = attribute_sample(cls, field)
    if name.endswith("IntAttribute"):
        sample = 2
    elif name.endswith(("DoubleAttribute", "FloatAttribute")):
        sample = 2.0 if int in get_args(get_type_hints(cls)[field.name]) else 2.5
    assert getattr(api, name)(get_handle(obj), sample)
    raw = getattr(obj, field.name)
    stored = (
        str(sample)
        if attribute in {"minimum", "maximum"} and str in get_args(get_type_hints(cls)[field.name])
        else sample
    )
    assert getattr(raw, "value", raw) == stored
    with pytest.raises(TgiError):
        getattr(api, name)(get_handle(obj), object())
    assert getattr(getattr(obj, field.name), "value", getattr(obj, field.name)) == stored


REMOVERS = [
    (name, attr) for name, attr, kind in api._EXTENDED_ATTRIBUTE_FUNCS if name.startswith("remove") and attr in MODELS
]


@pytest.mark.parametrize("name,attribute", REMOVERS)
def test_named_removers_preserve_required_fields_and_reset_schema_defaults(name, attribute):
    cls, field = MODELS[attribute]
    obj = make_model(cls)
    sample = attribute_sample(cls, field)
    api._set_attr(obj, attribute, sample)
    operation = getattr(api, name)
    if field.default is MISSING and field.default_factory is MISSING:
        with pytest.raises(TgiError):
            operation(get_handle(obj))
        assert getattr(getattr(obj, field.name), "value", getattr(obj, field.name)) == sample
    else:
        assert operation(get_handle(obj))
        expected = field.default if field.default is not MISSING else field.default_factory()
        assert getattr(obj, field.name) == expected
