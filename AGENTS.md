# Working on pyipxact-de

## Project and layout

This is a Python design environment for Accellera SPIRIT/IP-XACT XML. It includes schema bindings, XML
identification/validation/translation, a VLNV registry, an argparse CLI, a developing IEEE 1685-2022 TGI API, and an MCP
validation server.

Keep the existing MCP server and dependency available, but defer further MCP development unless requested. Its current
decorator API requires MCP 1.x.

- `src/amal/eda/ipxact_de/` : application code; `xml_document.py` handles parsing/serialization, `xml_validation.py`
  provides validation results, and `loader.py` discovers XML and maintains the registry/cache.
- `src/amal/eda/ipxact_de/cli/`: CLI entry point and commands.
- `src/amal/eda/ipxact_de/tgi/ipxact/v1685_2022/`: TGI operations and registry/access handles.
- `src/amal/eda/ipxact_de/mcp/`: MCP server exposing XML validation.
- `src/amal/utilities/`: logging, XML validation, and XSLT translation helpers.
- `src/org/accellera/` : generated bindings for SPIRIT 1.0/1.1/1.2/1.4/1.5/1685-2009 and IP-XACT 1685-2014/1685-2022;
  `standard.py` and the package initializer provide schema/version metadata.
- `submodules/accellera-schemas/`: upstream XSD/WSDL schemas. `src/org/accellera/xsl/` holds conversion stylesheets.
- `tests/`: pytest coverage and XML fixtures. `docs/`: Sphinx documentation. `.ai/`: ignored local standard references.
- `PyXB/`: historical bindings, excluded from distribution; use the current xsdata bindings for new work.

GUI/web prototypes exist locally but are currently ignored by Git. Check tracking before depending on them in a
distributable feature.

## Environment and commands

Use `uv` ; Python support is declared by `requires-python` in `pyproject.toml` , and the working interpreter is selected
through `.python-version` . Honor existing `UV_*` environment variables, including cache, Python, and registry settings.
Do not override or unset them to work around access failures; request the necessary sandbox access instead. Avoid
printing credentials from environment variables or registry configuration.

- Install reproducibly: `uv sync --locked` (default dependencies plus dev group).
- Include optional GUI/web dependencies: `uv sync --locked --all-extras`.
- Refresh dependencies intentionally: `uv lock --upgrade` , then sync and validate. Keep `pyproject.toml` and `uv.lock`
  consistent.
- CLI: `uv run --locked ipxact-de --help` or `uv run --locked python -m amal.eda.ipxact_de.cli --help`.
- Full tests: `uv run --locked pytest -q`.
- Focused baseline:

  ```bash
  uv run --locked pytest -q tests/test_cli.py tests/test_versions.py \
    tests/test_xml_validation.py tests/test_xml_validator.py tests/test_xml_transformer.py
  ```

- Build distributions: `uv build`.
- Documentation: `uv run --locked sphinx-build -b html docs docs/_build/html`.

Schema-dependent work requires the submodule to be populated. Use `git submodule update --init --recursive` if needed,
retaining the recorded revision unless updating schemas is part of the task.

## Change discipline

Inspect `git status` and relevant diffs before editing. Preserve existing local work, including untracked files. Keep
changes scoped; do not reformat or regenerate thousands of bindings as part of an unrelated change.

Treat generated binding modules as generated artifacts. Investigate the schemas and `make generate-bindings` options
before changing them; regenerate only when explicitly relevant and review the resulting diff. The Makefile also has
experimental generation targets that can create alternative package trees.

Follow the existing typed Python style, four-space indentation, double quotes, and 120-character line length. Ruff rules
are configured in `pyproject.toml` ; apply formatting/linting only to touched handwritten files unless a broader cleanup
is requested.

Preserve standard/version namespace mappings, VLNV identity, and serialization semantics. Cover behavioral changes with
focused tests, especially XML round trips, validation failures, transformation chains, registry lookups, and TGI access
handles. Do not assume behavior is identical across schema versions.

Some tests invoke external XML tools; inspect the relevant test/module for executable requirements. Deserialization
tests download Leon2 example archives from Accellera during collection and cache them under `/tmp/pyipxact_leon2_cache`
; full-suite runs can therefore require network access. Report unavailable tools or downloads separately from
application failures.

Before finishing, run the checks appropriate to the changed behavior and report concrete results and unresolved
failures. Do not publish, tag, or deploy unless requested.

## Sub-agent delegation

Delegate simple execution tasks to `gpt-6-luna` sub-agents to keep routine work and verbose tool output out of the
main harness context. Provide a precise, bounded specification, required inputs, acceptance criteria, and a unique
file or artifact scope. Pass only the context needed for the task; prefer no conversation-history fork.

Run up to three sub-agents concurrently, subject to available agent slots. Give implementation groups non-overlapping
ownership. Sub-agents should return concise results, artifact paths, exact verification evidence, and unresolved
issues; keep detailed logs in artifacts rather than forwarding them into the main context.

The main harness evaluates sub-agent results, reviews and integrates changes, and decides whether acceptance criteria
are met. It owns shared plan, feature, coverage, changelog, and handoff updates and the final commits. A sub-agent's
completion report alone does not establish verification or feature completion.

## Implementation tracking

Implement features in sets of 5–10 depending on complexity. After each completed set of changes, update
`docs/features.rst` , the ignored `.ai/implementation-plan.md` and relevant coverage ledgers, and `CHANGELOG.md` , then
commit the changes. Organize both `docs/features.rst` and `.ai/implementation-plan.md` by feature category,
without batch headings.
Use ASCII dashes and no blank lines between consecutive bullets in `docs/features.rst`.
Match RST heading underline lengths to their titles.
Do not add blank lines between consecutive bullet items in `CHANGELOG.md`.
Ask the user to continue before starting the next set. Keep all planned items visible
and tick only features supported by scoped verification.

Implement the full IP-XACT feature plan, not only TGI operations. Track core document/model semantics, validation,
configuration, addressing, older-version conversion, and GUI work independently from TGI coverage.
Prioritize IEEE/IP-XACT standard requirements. Defer further caching, cache optimization, GUI, and other
nonstandard convenience work until the remaining standard aspects are implemented, unless explicitly requested.

## Pull requests and releases

This repository uses feature/release branches, pull requests, and merges. Do not push feature commits directly
to `main`. Use Conventional Commit PR titles and squash merges. Release-please collects merged changes into a
reviewed release PR and manages package versions, the lockfile, changelog, and tags. Merging that PR invokes
`.github/workflows/publish.yml` to verify, test, build, and publish with `uv publish` using PyPI trusted publishing.
Manual publication takes an existing release tag for recovery. See `docs/development/releases.rst` for service setup
and version rules. Use the `amal-khailtash` GitHub account; never use `akhailta_amdeng`.

## Context handoff

At 90% context usage, update the ignored `.ai/HANDOFF.md` before continuing or restarting.
Record the objective, user constraints, branch/commit/worktree state, completed features, exact test and
coverage evidence, pending work, live processes, and the next concrete action. Read this file and
`.ai/implementation-plan.md` when starting a replacement session; verify current Git state before editing.
