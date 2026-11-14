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

    python3 -m pip install netscope

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
