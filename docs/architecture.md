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
