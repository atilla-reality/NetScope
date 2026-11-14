from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()

if not (ROOT / "netscope" / "cli.py").is_file():
    raise SystemExit("ERROR: NetScope project directory not found.")

if not (ROOT / "netscope" / "modules" / "dns.py").is_file():
    raise SystemExit("ERROR: DNS module missing.")

if not (ROOT / "netscope" / "core" / "engine.py").is_file():
    raise SystemExit("ERROR: Diagnostic engine missing.")

def write_file(name, content):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print("[CREATED]", name)

# --------------------------------------------------
# README
# --------------------------------------------------

write_file("README.md", r"""
# NetScope

**Network Diagnostics & Intelligence Toolkit**

NetScope is a modular Python command-line toolkit for local network
diagnostics, DNS resolution and structured system reporting.

## Features

- System information
- Network interface discovery
- IPv4 and IPv6 address reporting
- MAC address and MTU discovery where supported
- Default gateway discovery where supported
- Route hint detection
- DNS queries: A, AAAA, MX, NS, CNAME and TXT
- JSON diagnostic reports
- Platform-specific adapters
- Capability and error reporting
- Automated unit tests

## Requirements

- Python 3.9 or newer
- No mandatory third-party runtime dependencies

## Installation

Clone the official repository:

    git clone https://github.com/atilla-reality/Netscope.git

Enter the directory:

    cd Netscope

Install:

    python3 -m pip install .

## Run from source

    python3 -m netscope --help

## Commands

### Version

    netscope --version

### System information

    netscope info

### Network diagnostics

    netscope network

### DNS queries

    netscope dns example.com

    netscope dns example.com --type A AAAA MX

    netscope dns example.com --server 1.1.1.1

### Diagnostic reports

    netscope report

    netscope report --dns example.com

    netscope report --dns example.com --output report.json

## Project architecture

    netscope/
        __init__.py
        __main__.py
        main.py
        cli.py
        core/
            engine.py
            models.py
        modules/
            network.py
            dns.py
        platforms/
            detector.py
            ish.py
            linux.py
            windows.py
        reporting/

## Platform compatibility

| Platform | Adapter | Validation |
|---|---|---|
| iSH / Alpine | Dedicated adapter | Tested in iSH; interface limitations observed |
| Linux | Linux adapter | Unit-tested; real-host testing pending |
| Kali Linux | Linux adapter | Real-host testing pending |
| Windows | PowerShell adapter | Mock unit-tested; native testing pending |
| Termux | Linux adapter selection | Real-device testing pending |

NetScope reports unsupported capabilities instead of assuming that
all operating systems expose identical networking facilities.

### iSH limitations

iSH does not expose every Linux networking facility. Interface discovery
may be restricted. A route hint is not equivalent to confirmed gateway
discovery.

### DNS limitations

The DNS engine currently uses UDP. Truncated DNS responses are reported
as errors; TCP fallback is not implemented.

Nameserver discovery currently uses `/etc/resolv.conf`.
Native Windows DNS server discovery requires additional validation.

## Testing

Run the complete test suite:

    python3 -m unittest discover -s tests -v

Compile-check the project:

    python3 -m compileall -q netscope tests

## Design principles

- Read-only diagnostics by default
- No automatic network configuration changes
- Modular platform adapters
- Minimal dependencies
- Explicit capability reporting
- Structured JSON output

## Security

NetScope is intended for local diagnostics and explicitly requested DNS
queries. Only examine systems and domains you are authorized to examine.

## License

No license has been selected yet. All rights remain with the respective

copyright holder until a license is added.

""")

# --------------------------------------------------

# PYPROJECT

# --------------------------------------------------

write_file("pyproject.toml", r"""

[build-system]

requires = ["setuptools>=61"]

build-backend = "setuptools.build_meta"

[project]

name = "netscope-toolkit"

version = "1.0.0"

description = "Network Diagnostics & Intelligence Toolkit"

readme = "README.md"

requires-python = ">=3.9"

dependencies = []

classifiers = [

    "Programming Language :: Python :: 3",

    "Programming Language :: Python :: 3.9",

    "Environment :: Console",

    "Topic :: System :: Networking",

    "Topic :: System :: Systems Administration",

]

[project.scripts]

netscope = "netscope.cli:main"

[tool.setuptools.packages.find]

include = ["netscope*"]

""")

# --------------------------------------------------

# GITIGNORE

# --------------------------------------------------

write_file(".gitignore", r"""

__pycache__/

*.py[cod]

*$py.class

.Python

build/

dist/

*.egg-info/

.venv/

venv/

env/

.pytest_cache/

.coverage

htmlcov/

.DS_Store

Thumbs.db

netscope-report.json

report.json

""")

# --------------------------------------------------

# CHANGELOG

# --------------------------------------------------

write_file("CHANGELOG.md", r"""

# Changelog

## 1.0.0

First stable release.

### Core

- Modular diagnostic engine

- Structured diagnostic models

- Platform detection

- Capability and error reporting

### Network

- Linux network interface discovery

- IPv4 and IPv6 address handling

- Linux default gateway discovery

- iSH route hint support

- Windows PowerShell adapter

### DNS

- A, AAAA, MX, NS, CNAME and TXT queries

- DNS response parsing

- Compression pointer handling

- Response validation

- Resolver discovery

- Structured error reporting

### CLI

- System information command

- Network diagnostics command

- DNS query command

- JSON report generation

- Optional DNS information in reports

### Quality

- Automated unit tests

- Python compilation checks

- Packaging metadata

- Documentation

### Known limitations

- iSH interface discovery is restricted by its environment.

- Real Windows integration testing remains necessary.

- Real Termux integration testing remains necessary.

- Linux and Kali require additional real-host validation.

- DNS TCP fallback is not implemented.

""")

# --------------------------------------------------

# ARCHITECTURE DOCUMENTATION

# --------------------------------------------------

write_file("docs/architecture.md", r"""

# NetScope Architecture

## Overview

NetScope separates diagnostic orchestration, platform discovery,

protocol handling and command-line presentation.

## Core

`core/engine.py` coordinates diagnostic execution.

`core/models.py` defines structured diagnostic objects and serialization.

## Modules

`modules/network.py` presents network diagnostic results.

`modules/dns.py` implements DNS query encoding, transport and parsing.

## Platforms

`platforms/detector.py` identifies the execution environment.

`platforms/ish.py` contains iSH-specific behavior.

`platforms/linux.py` contains Linux interface and route discovery.

`platforms/windows.py` contains PowerShell-based Windows discovery.

## CLI

`cli.py` provides command parsing, output and report generation.

`__main__.py` enables:

    python3 -m netscope

## Capability model

Platform adapters expose only capabilities they can discover.

Unsupported operations should be reported explicitly.

## Safety model

NetScope performs read-only diagnostics by default.

It does not change network configuration.

""")

# --------------------------------------------------

# PLATFORM SUPPORT DOCUMENTATION

# --------------------------------------------------

write_file("docs/platform-support.md", r"""

# Platform Support

This document distinguishes implemented adapters from verified compatibility.

| Environment | Adapter | Validation |

|---|---|---|

| iSH / Alpine | ish.py | Tested in iSH; interface limitation observed |

| Linux | linux.py | Unit tests passed; real-host validation pending |

| Kali Linux | linux.py | Real-host validation pending |

| Windows | windows.py | Mock tests passed; native validation pending |

| Termux | linux.py | Real-device validation pending |

## iSH

Some Linux networking interfaces may not be available.

A route hint represents a selected local source address, not a confirmed gateway.

## Linux

The adapter uses Linux-specific facilities, including sysfs, ioctl and

`/proc` network information.

## Windows

The adapter relies on PowerShell networking commands.

Native Windows integration testing is required.

## Termux

Termux uses the Linux adapter, but Android-specific behavior requires

real-device testing.

""")

# --------------------------------------------------

# CLI TESTS

# --------------------------------------------------

write_file("tests/test_cli.py", r'''

import unittest

from netscope.cli import build_parser

class CLITests(unittest.TestCase):

    def setUp(self):

        self.parser = build_parser()

    def test_report_dns_argument(self):

        args = self.parser.parse_args([

            "report", "--dns", "example.com"

        ])

        self.assertEqual(args.command, "report")

        self.assertEqual(args.dns_hostname, "example.com")

    def test_report_dns_options(self):

        args = self.parser.parse_args([

            "report",

            "--dns", "example.com",

            "--dns-type", "A", "MX",

            "--dns-server", "1.1.1.1",

            "--dns-timeout", "5",

        ])

        self.assertEqual(args.dns_record_types, ["A", "MX"])

        self.assertEqual(args.dns_server, "1.1.1.1")

        self.assertEqual(args.dns_timeout, 5.0)

    def test_report_output_argument(self):

        args = self.parser.parse_args([

            "report", "--output", "report.json"

        ])

        self.assertEqual(args.output, "report.json")

    def test_dns_command(self):

        args = self.parser.parse_args([

            "dns", "example.com", "--type", "AAAA"

        ])

        self.assertEqual(args.command, "dns")

        self.assertEqual(args.hostname, "example.com")

        self.assertEqual(args.record_types, ["AAAA"])

    def test_abbreviated_dns_option_is_rejected(self):

        with self.assertRaises(SystemExit):

            self.parser.parse_args([

                "report", "--dn", "example.com"

            ])

if __name__ == "__main__":

    unittest.main()

''')

# --------------------------------------------------

# VERSION IS NOT CHANGED UNTIL TESTS PASS

# --------------------------------------------------

print()

print("Project files prepared.")

print("Existing CLI, DNS, network and platform modules were preserved.")

print("Version has NOT been changed.")

print()

print("Next: run the verification commands.")

