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
