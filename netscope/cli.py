import argparse
import json
import socket
import sys

from netscope import __version__


def get_info():
    import platform

    return {
        "version": __version__,
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "hostname": socket.gethostname(),
    }


def show_info():
    print(json.dumps(get_info(), indent=2))


def show_dns(hostname, record_types=None, server=None, timeout=3.0):
    from netscope.modules.dns import DNSQueryError, resolve_dns

    try:
        result = resolve_dns(
            hostname,
            record_types=record_types,
            server=server,
            timeout=timeout,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "ok" else 1

    except DNSQueryError as error:
        print(json.dumps({
            "hostname": hostname,
            "status": "error",
            "errors": [str(error)],
        }, indent=2))
        return 1


def show_network():
    from netscope.modules.network import show_network as run_network

    result = run_network()
    return 0 if result["status"] in ("ok", "partial") else 1


def show_report(
    output=None,
    dns_hostname=None,
    dns_record_types=None,
    dns_server=None,
    dns_timeout=3.0,
):
    from netscope.core.engine import run_network_diagnostics

    report = {
        "application": "NetScope",
        "version": __version__,
        "system": get_info(),
        "network": run_network_diagnostics().to_dict(),
    }

    if dns_hostname:
        from netscope.modules.dns import DNSQueryError, resolve_dns

        try:
            report["dns"] = resolve_dns(
                dns_hostname,
                record_types=dns_record_types,
                server=dns_server,
                timeout=dns_timeout,
            )
        except DNSQueryError as error:
            report["dns"] = {
                "hostname": dns_hostname,
                "status": "error",
                "errors": [str(error)],
            }

    content = json.dumps(report, indent=2)

    if output:
        try:
            with open(output, "w", encoding="utf-8") as file:
                file.write(content + "\n")
            print("Report saved:", output)
            return 0
        except OSError as error:
            print("Report error:", error, file=sys.stderr)
            return 1

    print(content)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="netscope",
        description="NetScope - Network Diagnostics & Intelligence Toolkit",
        allow_abbrev=False,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="NetScope {}".format(__version__),
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("info", help="Show system information")
    subparsers.add_parser("network", help="Discover local network interfaces")

    dns_parser = subparsers.add_parser("dns", help="Query DNS records")
    dns_parser.add_argument("hostname")
    dns_parser.add_argument(
        "--type",
        dest="record_types",
        nargs="+",
        choices=["A", "AAAA", "MX", "NS", "CNAME", "TXT"],
        default=["A", "AAAA"],
    )
    dns_parser.add_argument("--server", help="DNS server IPv4 or IPv6 address")
    dns_parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="DNS query timeout in seconds",
    )

    report_parser = subparsers.add_parser(
        "report",
        help="Generate a diagnostic report",
        allow_abbrev=False,
    )
    report_parser.add_argument(
        "--format",
        choices=["json"],
        default="json",
    )
    report_parser.add_argument("--output", help="Output file")
    report_parser.add_argument(
        "--dns",
        dest="dns_hostname",
        metavar="HOSTNAME",
        help="Include DNS results for a hostname",
    )
    report_parser.add_argument(
        "--dns-type",

        dest="dns_record_types",

        nargs="+",

        choices=["A", "AAAA", "MX", "NS", "CNAME", "TXT"],

        default=["A", "AAAA"],

        help="DNS record types for the report",

    )

    report_parser.add_argument(

        "--dns-server",

        help="Optional DNS server IPv4 or IPv6 address",

    )

    report_parser.add_argument(

        "--dns-timeout",

        type=float,

        default=3.0,

        help="DNS timeout in seconds",

    )

    return parser

def main():

    parser = build_parser()

    args = parser.parse_args()

    if args.command == "info":

        show_info()

        return 0

    if args.command == "network":

        return show_network()

    if args.command == "dns":

        return show_dns(

            args.hostname,

            record_types=args.record_types,

            server=args.server,

            timeout=args.timeout,

        )

    if args.command == "report":

        return show_report(

            output=args.output,

            dns_hostname=args.dns_hostname,

            dns_record_types=args.dns_record_types,

            dns_server=args.dns_server,

            dns_timeout=args.dns_timeout,

        )

    parser.print_help()

    return 0

if __name__ == "__main__":

    sys.exit(main())

