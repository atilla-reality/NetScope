import json
import subprocess

from netscope.core.models import (
    NetworkAddress,
    NetworkInterface,
)


def _run_powershell(command):
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(
            "PowerShell command failed: {}".format(error)
        )

    output = result.stdout.strip()

    if not output:
        return []

    try:
        return json.loads(output)
    except ValueError as error:
        raise RuntimeError(
            "Invalid PowerShell JSON output: {}".format(error)
        )


def _as_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def discover_interfaces():
    command = (
        "$ErrorActionPreference='Stop'; "
        "$items = @(Get-NetAdapter | ForEach-Object { "
        "$a = $_; "
        "$ips = @(Get-NetIPAddress "
        "-InterfaceIndex $a.ifIndex "
        "-ErrorAction SilentlyContinue | "
        "Where-Object { $_.AddressState -ne 'Invalid' } | "
        "ForEach-Object { "
        "[PSCustomObject]@{ "
        "IPAddress=$_.IPAddress; "
        "PrefixLength=$_.PrefixLength; "
        "AddressFamily=$_.AddressFamily.ToString() "
        "} }); "
        "$mtu = Get-NetIPInterface "
        "-InterfaceIndex $a.ifIndex "
        "-AddressFamily IPv4 "
        "-ErrorAction SilentlyContinue | "
        "Select-Object -First 1 -ExpandProperty NlMtu; "
        "[PSCustomObject]@{ "
        "InterfaceAlias=$a.Name; "
        "Status=$a.Status.ToString(); "
        "MacAddress=$a.MacAddress; "
        "Mtu=$mtu; "
        "Addresses=$ips "
        "} }); "
        "ConvertTo-Json -InputObject $items "
        "-Depth 5 -Compress"
    )

    data = _as_list(_run_powershell(command))
    interfaces = []

    for item in data:
        if not isinstance(item, dict):
            continue

        name = item.get("InterfaceAlias") or "unknown"

        interface = NetworkInterface(
            name=str(name),
            source="PowerShell NetAdapter",
        )

        status = item.get("Status")

        if status:
            interface.status = str(status).lower()
            interface.is_up = (
                interface.status == "up"
            )

        mac = item.get("MacAddress")

        if mac:
            normalized_mac = str(mac).strip().lower()

            if normalized_mac not in (
                "00:00:00:00:00:00",
                "00-00-00-00-00-00",
            ):
                interface.mac_address = (
                    normalized_mac.replace("-", ":")
                )

        mtu = item.get("Mtu")

        try:
            if mtu is not None:
                interface.mtu = int(mtu)
        except (TypeError, ValueError):
            pass

        for address in _as_list(item.get("Addresses")):
            if not isinstance(address, dict):
                continue

            value = address.get("IPAddress")

            if not value:
                continue

            family_name = str(
                address.get("AddressFamily", "")
            ).lower()

            if "ipv4" in family_name or "." in str(value):
                family = "IPv4"
            elif "ipv6" in family_name or ":" in str(value):
                family = "IPv6"
            else:
                continue

            try:
                prefix = address.get("PrefixLength")
                if prefix is not None:
                    prefix = int(prefix)
            except (TypeError, ValueError):
                prefix = None

            interface.addresses.append(
                NetworkAddress(
                    address=str(value),
                    family=family,
                   prefix_length=prefix,

                )

            )

        interfaces.append(interface)

    return interfaces

def discover_gateway():

    command = (

        "Get-NetRoute "

        "-AddressFamily IPv4 "

        "-DestinationPrefix '0.0.0.0/0' "

        "-ErrorAction SilentlyContinue | "

        "Sort-Object RouteMetric, InterfaceMetric | "

        "Select-Object -First 1 -ExpandProperty NextHop"

    )

    try:

        result = subprocess.run(

            [

                "powershell",

                "-NoProfile",

                "-NonInteractive",

                "-Command",

                command,

            ],

            capture_output=True,

            text=True,

            timeout=15,

            check=True,

        )

    except (OSError, subprocess.SubprocessError):

        return None

    gateway = result.stdout.strip()

    return gateway or None

