"""Old application imports share canonical module identity and registry state."""

import importlib

import pytest


@pytest.mark.parametrize(
    "old,new",
    [
        ("amal.eda.ipxact_de.tgi.ipxact.v1685_2022", "amal.eda.accellera.ipxact.v1685_2022.tgi"),
        ("amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core", "amal.eda.accellera.ipxact.v1685_2022.tgi.core"),
        ("amal.eda.ipxact_de.tgi.ipxact.v1685_2022.component", "amal.eda.accellera.ipxact.v1685_2022.tgi.component"),
    ],
)
def test_import_identity(old, new):
    assert importlib.import_module(old) is importlib.import_module(new)


def test_registry_shared_across_paths():
    old = importlib.import_module("amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core")
    new = importlib.import_module("amal.eda.accellera.ipxact.v1685_2022.tgi.core")
    obj = object()
    assert new.resolve_handle(old.get_handle(obj)) is obj
