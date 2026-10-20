# Accellera SPIRIT/IP-XACT DE (Design Environment) and Python Bindings

<p align="center">
   <img
      src="https://github.com/amal-khailtash/pyipxact-de/raw/refs/heads/main/docs/_static/logo-256x256.svg"
      alt="IP-XACT DE" width="256"/>
</p>

| Category | Status |
| --- | --- |
| CI/CD | [![Release automation](https://img.shields.io/github/actions/workflow/status/amal-khailtash/pyipxact-de/release-please.yml?branch=main&label=Release%20automation&logo=github&logoColor=white)](https://github.com/amal-khailtash/pyipxact-de/actions/workflows/release-please.yml) [![Tests and coverage](https://img.shields.io/github/actions/workflow/status/amal-khailtash/pyipxact-de/ci.yml?branch=main&label=Tests%20and%20coverage&logo=github&logoColor=white)](https://github.com/amal-khailtash/pyipxact-de/actions/workflows/ci.yml) [![Codecov](https://codecov.io/gh/amal-khailtash/pyipxact-de/branch/main/graph/badge.svg)](https://app.codecov.io/gh/amal-khailtash/pyipxact-de) [![Publish Python distributions](https://img.shields.io/github/actions/workflow/status/amal-khailtash/pyipxact-de/publish.yml?branch=main&label=Publish%20Python%20distributions&logo=github&logoColor=white)](https://github.com/amal-khailtash/pyipxact-de/actions/workflows/publish.yml) [![Documentation](https://img.shields.io/github/actions/workflow/status/amal-khailtash/pyipxact-de/ci.yml?branch=main&label=Documentation&logo=readthedocs&logoColor=white)](https://github.com/amal-khailtash/pyipxact-de/actions/workflows/ci.yml) |
| Project | [![GitHub](https://img.shields.io/badge/pyipxact--de-29b6f6?logo=github&labelColor=0277bd)](https://github.com/amal-khailtash/pyipxact-de) [![PyPI](https://img.shields.io/pypi/v/pyipxact-de?logo=pypi&logoColor=FBE072&cacheSeconds=300)](https://pypi.org/project/pyipxact-de/) [![GitHub tag](https://img.shields.io/github/v/tag/amal-khailtash/pyipxact-de?logo=github&label=version)](https://github.com/amal-khailtash/pyipxact-de/tags) |
| Docs | [![Read the Docs](https://readthedocs.org/projects/pyipxact-de/badge/?version=latest)](https://pyipxact-de.readthedocs.io/en/latest/) |
| Meta | [![License](https://img.shields.io/github/license/amal-khailtash/pyipxact-de)](https://github.com/amal-khailtash/pyipxact-de/blob/main/LICENSE) [![Stars](https://img.shields.io/github/stars/amal-khailtash/pyipxact-de)](https://github.com/amal-khailtash/pyipxact-de/stargazers) [![Forks](https://img.shields.io/github/forks/amal-khailtash/pyipxact-de)](https://github.com/amal-khailtash/pyipxact-de/forks) [![Contributors](https://img.shields.io/github/contributors/amal-khailtash/pyipxact-de)](https://github.com/amal-khailtash/pyipxact-de/graphs/contributors) |
| Standards | [![Python](https://img.shields.io/badge/python-3.14-blue?logo=python)](https://www.python.org/) [![SemVer](https://img.shields.io/badge/SemVer-2.0.0-333333?logo=semver)](https://semver.org/) [![Keep a Changelog](https://img.shields.io/badge/Keep%20a%20Changelog-1.1.0-0c7fb0?logo=keepachangelog&logoColor=white)](https://keepachangelog.com/en/1.1.0/) |

`pyipxact-de` is a Python-based Design Environment and bindings for Accellera SPIRIT/IP-XACT. It targets SPIRIT v1.x and
IP-XACT 1685-2009/2014/2022, enabling parsing, validation, transformation, and programmatic manipulation of IP-XACT
artifacts (components, buses, designs, memory maps).

Key features:

- Generated, schema-accurate models via [xsData](https://github.com/tefra/xsdata) (initial version used
  [PyXB](https://pyxb.sourceforge.net/) ) under `org.accellera.*`
- High-level APIs, CLI tools, and TGI helpers for common workflows (identify, validate, convert, , ...).
- Modern Python 3.14 tooling and type-annotated, docstring-rich codebase.

See the [documentation](https://pyipxact-de.readthedocs.io/en/latest/) for detailed guides, examples,
and API references.

## TODO

- [ ] GUI and web front ends for interactive exploration.

## Installation

### Standard Installation

```bash
pip install pyipxact-de[cli,gui,web]
```

### MCP Server Installation

The package includes an MCP (Model Context Protocol) server for IP-XACT validation that can be used with VS Code and
other MCP-compatible clients.

#### Global Installation with uv

```bash
uv tool install pyipxact-de
```

**Note**: The package name on PyPI is `pyipxact-de`, but it provides the `ipxact-de-mcp` command.

#### Configuration for VS Code

Add the following to your VS Code MCP configuration (`~/.config/Code/User/mcp.json`):

```json
{
  "servers": {
    "ipxact-de": {
      "command": "ipxact-de-mcp",
      "args": [],
      "env": {
        "PYTHONUNBUFFERED": "1"
      },
      "restart": "on-failure",
      "timeoutMs": 30000
    }
  }
}
```

### Alternative MCP Installation

You can also install in your current environment:

```bash
# Using uv
uv add pyipxact-de

# Using pip
pip install pyipxact-de
```

Then reference the full path to the executable in your MCP configuration:

```json
{
  "servers": {
    "ipxact-de": {
      "command": "/path/to/your/venv/bin/ipxact-de-mcp",
      "args": [],
      "cwd": "/path/to/your/project",
      "env": {
        "PYTHONUNBUFFERED": "1"
      },
      "restart": "on-failure",
      "timeoutMs": 30000
    }
  }
}
```

### Available MCP Tools

The MCP server provides the following tools:

- `validate_xml`: Validate IP-XACT XML files against Accellera schemas

## Contributing

TODO

## Project Structure

Python bindings for Accellera Spirit and Accellera versions are generated under `org.accellera.*` namespace.

```text
src/
├── amal
│   ├── eda
│   │   └── ipxact_de
│   │       ├── cli
│   │       ├── gui
│   │       │   └── ui
│   │       │       └── icons
│   │       ├── tgi
│   │       │   └── ipxact
│   │       │       └── v1685_2022
│   │       └── web
│   └── utilities
├── amal
│   ├── eda
│   │   └── ipxact_de
│   │       ├── cli
│   │       ├── gui
│   │       │   └── ui
│   │       │       └── icons
│   │       ├── tgi
│   │       │   └── ipxact
│   │       │       └── v1685_2022
│   │       └── web
│   └── utilities
└── org
    └── accellera
        ├── ipxact
        │   ├── v1685_2014
        │   └── v1685_2022
        │       ├── tgi
        │       └── ve
        ├── spirit
        │   ├── v1_0
        │   ├── v1_1
        │   ├── v1_2
        │   ├── v1_4
        │   │   └── tgi
        │   ├── v1_5
        │   │   └── tgi
        │   └── v1685_2009
        │       ├── tgi
        │       └── ve
        │           ├── ams
        │           ├── core
        │           ├── pdp
        │           └── power
        └── xsl
```
