"""Tests for command-line interruption handling."""

import sys
from typing import Any

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi.core import registry
from amal.eda.ipxact_de import cli
from org.accellera.ipxact.v1685_2022 import Component


def test_main_converts_keyboard_interrupt_to_exit_130(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The public entry point reports an interrupt as the conventional exit code."""

    def interrupt() -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "_main", interrupt)

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 130
    assert "Traceback" not in capsys.readouterr().err


def test_main_propagates_other_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only KeyboardInterrupt is translated by the public entry point."""
    error = RuntimeError("unexpected CLI failure")

    def fail() -> None:
        raise error

    monkeypatch.setattr(cli, "_main", fail)

    with pytest.raises(RuntimeError) as raised:
        cli.main()

    assert raised.value is error


def test_registry_list_interrupt_preserves_registered_inventory(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An interrupt during rendering exits cleanly and leaves inventory intact."""
    vlnv = ("__cli_interrupt_test__", "library", "component", "1")
    component = Component(vendor=vlnv[0], library=vlnv[1], name=vlnv[2], version=vlnv[3])
    registry.register(
        component,
        vlnv,
        element_type="Component",
        standard="ipxact",
        schema_version="1685-2022",
    )
    try:
        before = {handle: registry.get_vlnv(handle) for handle in registry.iter_documents()}
        expected = dict(before)

        # The unique filter keeps this test deterministic if other tests populated
        # the process-wide registry, and the registered model prevents cache reads.
        monkeypatch.setattr(
            cli,
            "load_registry_from_cache",
            lambda: pytest.fail("registry listing unexpectedly loaded the cache"),
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["ipxact-de", "registry", "list", "__cli_interrupt_test__:library:component:1"],
        )
        original_print = cli.console.print
        printed: list[str] = []

        def interrupt_after_first_entry(*args: object, **kwargs: Any) -> None:
            rendered = str(args[0]) if args else ""
            printed.append(rendered)
            original_print(*args, **kwargs)
            if vlnv[0] in rendered:
                raise KeyboardInterrupt

        monkeypatch.setattr(cli.console, "print", interrupt_after_first_entry)

        with pytest.raises(SystemExit) as exit_info:
            cli.main()

        assert exit_info.value.code == 130
        assert any(vlnv[0] in output for output in printed)
        assert "Traceback" not in capsys.readouterr().err
        assert {handle: registry.get_vlnv(handle) for handle in registry.iter_documents()} == expected
    finally:
        registry.unregister(vlnv)
