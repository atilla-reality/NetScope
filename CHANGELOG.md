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
