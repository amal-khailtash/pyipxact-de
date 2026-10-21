"""Generated language and reference edits preserve identity and metadata."""
import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import component, instantiation
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from org.accellera.ipxact.v1685_2022 import Component


@pytest.mark.parametrize("kind", ["Component", "DesignConfiguration"])
def test_language_identity(kind):
    root = get_handle(Component(vendor="v", library="l", name="c", version="1"))
    args = [root, "i"] + ([] if kind == "Component" else [("v", "l", "d", "1")])
    handle = getattr(component, f"addComponent{kind}Instantiation")(*args)
    setter = getattr(instantiation, f"set{kind}InstantiationLanguage")
    getter = getattr(instantiation, f"get{kind}InstantiationLanguage")
    setter(handle, "verilog")
    child = resolve_handle(handle).language
    child.strict = True
    setter(handle, "systemVerilog")
    assert getter(handle) == "systemVerilog"
    assert resolve_handle(handle).language is child
    assert child.strict
    with pytest.raises(TgiError):
        setter(handle, "")
    assert getter(handle) == "systemVerilog"

def test_reference_identity_and_atomicity():
    root = get_handle(Component(vendor="v", library="l", name="c", version="1"))
    handle = component.addComponentDesignConfigurationInstantiation(root, "i", ("v", "l", "d", "1"))
    ref = resolve_handle(handle).design_configuration_ref
    instantiation.setDesignConfigurationInstantiationDesignConfigurationRef(handle, ("v", "l", "next", "2"))
    assert resolve_handle(handle).design_configuration_ref is ref
    with pytest.raises(TgiError):
        instantiation.setDesignConfigurationInstantiationDesignConfigurationRef(handle, ("", "l", "bad", "2"))
    assert ref.name == "next"
