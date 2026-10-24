"""Tests for moving pending changelog details into generated releases."""

import re
import runpy
from pathlib import Path

import pytest

_ROLL_OVER = runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools" / "prepare_release_notes.py"))[
    "roll_over"
]


def test_pending_details_move_into_release_and_keep_history() -> None:
    """Move pending notes under generated release notes and preserve prior history."""
    preamble = "# Changelog\n\nRelease notes follow."
    generated_heading = "## [0.7.1](https://example.invalid/compare/v0.7.0...v0.7.1)"
    generated_summary = "### Summary\n- Generated release summary."
    pending_details = "### Added\n- Pending feature."
    older_release = "## [0.7.0]\n\n### Fixed\n- Existing fix.\n\n<!-- historical marker -->\n"
    changelog = (
        f"{preamble}\n\n## [Unreleased]\n\n{pending_details}\n\n"
        f"{generated_heading}\n\n{generated_summary}\n\n{older_release}"
    )

    result = _ROLL_OVER(changelog, "0.7.1")
    headings = re.findall(r"^## \[[^\]]+\].*$", result, flags=re.MULTILINE)

    assert headings[0] == "## [Unreleased]"
    assert headings.count("## [Unreleased]") == 1
    assert result.startswith(preamble)
    assert generated_heading in result
    assert generated_summary in result
    assert pending_details in result
    assert result.index(generated_summary) < result.index(pending_details)
    assert result.count("- Pending feature.") == 1
    assert result.endswith(older_release)
    assert _ROLL_OVER(result, "0.7.1") == result


@pytest.mark.parametrize(
    "changelog",
    [
        "## [0.7.0]\n\nOlder release.\n",
        "## [Unreleased]\n\nFirst pending section.\n\n"
        "## [0.7.1]\n\nGenerated release.\n\n"
        "## [Unreleased]\n\nSecond pending section.\n",
    ],
    ids=["missing-release-heading", "duplicate-unreleased"],
)
def test_invalid_release_sections_are_rejected(changelog: str) -> None:
    """Reject a missing release section or multiple Unreleased sections."""
    with pytest.raises(ValueError):
        _ROLL_OVER(changelog, "0.7.1")


def test_changelog_without_pending_section_gets_empty_unreleased() -> None:
    """Add one empty Unreleased heading when there are no pending details."""
    changelog = "# Changelog\n\n## [0.7.1]\n\nGenerated release summary.\n"

    result = _ROLL_OVER(changelog, "0.7.1")
    headings = re.findall(r"^## \[[^\]]+\].*$", result, flags=re.MULTILINE)

    assert headings[0] == "## [Unreleased]"
    assert headings.count("## [Unreleased]") == 1
    assert "Generated release summary." in result
    assert result.count("Generated release summary.") == 1
