Automated pull requests and releases
====================================

Contributor workflow
--------------------

Work on a feature branch and open a pull request. CI tests the complete suite,
produces coverage for handwritten application code, builds distributions, and
builds documentation. Codecov reports coverage; Read the Docs builds PR previews
through its GitHub App. No pull request publishes a production package.

Squash-merge contributor PRs using a Conventional Commit title. Require the
PR title, Tests and coverage, Build distributions, and Build documentation
checks in branch protection. Keep at least one review requirement and require
branches to be current, or use a merge queue. Do not enable automatic merging
of arbitrary contributor PRs.

Versions and concurrent contributors
------------------------------------

Contributors do not edit package versions or create release tags. Release-please
collects merged Conventional Commits into one release PR and updates
pyproject.toml, the release manifest, uv.lock, and CHANGELOG.md. It refreshes
that PR when more changes merge. The highest bump among merged changes wins.
Open PRs are excluded until merged. Thus multiple contributors never reserve or
race to increment versions in their individual branches.

* ``fix: ...`` and ``perf: ...`` request a patch (0.3.0 to 0.3.1).
* ``feat: ...`` requests a minor (0.3.0 to 0.4.0).
* ``feat!: ...`` or a ``BREAKING CHANGE:`` footer requests a major (0.3.0 to 1.0.0).
* Documentation, tests, CI and chores alone do not request a release.

These rules also apply below 1.0 because the pre-major special bump behavior is
explicitly disabled. Maintainers can override a proposed version with the
release-please ``Release-As:`` mechanism after reviewing the intended API impact.
Tags record the chosen version; they do not calculate it. Merging the reviewed
release PR creates its GitHub release/tag. Publishing then verifies the tag,
reruns all tests, builds and checks distributions, and uses ``uv publish`` with
PyPI trusted publishing and PEP 740 attestations. Twine only checks distribution
metadata; uv handles uploads. Publication runs in the same automation chain, so
it does not rely on a bot-created tag triggering another workflow.

The initial manifest starts at 0.3.0, the already merged release preparation.
Confirm that v0.3.0 has actually been tagged and published before enabling the
next release. If it has not, finish that release first; do not silently skip it.

One-time service configuration
------------------------------

* Enable Actions permissions to create pull requests.
* Set ``RELEASE_PLEASE_TOKEN`` to a fine-grained personal token belonging to
  ``amal-khailtash`` with contents and pull-request write permissions. A default GITHUB_TOKEN-created PR does not trigger ordinary
  PR workflows; that is why a separate token is required. Rotate expiring tokens.
  A GitHub App is an alternative, but requires adding a step to mint a fresh
  installation token on each run; do not store a short-lived installation token.
* Enable squash merging and require Conventional Commit PR titles. Configure
  branch protection checks and reviews. The release bot must not bypass tests.
* Create the ``pypi`` GitHub environment. In PyPI's trusted publishers, authorize
  this repository, ``publish.yml``, and environment ``pypi``. No PyPI password
  or API token is needed. Required environment reviewers are optional if fully
  automatic publication after a reviewed release PR is desired.
* Install Codecov's GitHub App, register the repository, and configure
  ``CODECOV_TOKEN`` if required. Coverage is initially informational; service
  outages or fork token restrictions do not block otherwise valid PRs.
* Import this repository in Read the Docs, install its GitHub App, enable PR
  builds, and enable the GitHub webhook integration. Activate released tag
  versions using Read the Docs version automation rules. The App/webhooks build
  latest, PR previews, and tag documentation from ``.readthedocs.yaml`` without
  an extra deprecated preview action or a duplicated build-trigger token.

Existing actions and retries
----------------------------

``ci.yml`` remains the CI entry point. ``publish.yml`` is now the reusable
verified publisher, called by release automation; manual dispatch takes an
existing release tag for recovery after publication fails. PyPI versions are
immutable: do not overwrite a published version or reuse a tag with new code.
Inspect which files were uploaded before retrying a partially completed upload.

The manual TestPyPI and GitHub Pages actions are retained as optional fallback
flows. They do not run automatically. Disable them in GitHub only after the new
services have been verified. TestPyPI publication does not create a release.

Implementation sources
----------------------

* `Google release-please <https://github.com/googleapis/release-please>`_
* `Release-please GitHub Action <https://github.com/googleapis/release-please-action>`_
* `uv trusted publishing example <https://github.com/astral-sh/trusted-publishing-examples>`_
* `Codecov action <https://github.com/codecov/codecov-action>`_
* `Read the Docs configuration <https://docs.readthedocs.com/platform/stable/config-file/v2.html>`_

The local pysystemc project provided the test/coverage and publication patterns.
Its native manylinux/auditwheel steps are unnecessary for this pure-Python wheel.
