import fcntl
import ipaddress
import os
import socket
import struct

from netscope.core.models import (
    NetworkAddress,
    NetworkInterface,
)

SIOCGIFADDR = 0x8915
SIOCGIFNETMASK = 0x891B
SIOCGIFFLAGS = 0x8913
IFF_UP = 0x1


def _interface_request(sock, name, request):
    encoded = name.encode("utf-8")[:15]
    payload = struct.pack("256s", encoded)
    return fcntl.ioctl(sock.fileno(), request, payload)


def _ipv4_details(sock, name):
    details = {}

    try:
        response = _interface_request(
            sock, name, SIOCGIFADDR
        )
        details["address"] = socket.inet_ntoa(
            response[20:24]
        )
    except OSError:
        pass

    try:
        response = _interface_request(
            sock, name, SIOCGIFNETMASK
        )
        netmask = socket.inet_ntoa(response[20:24])
        details["prefix_length"] = (
            ipaddress.IPv4Network(
                "0.0.0.0/{}".format(netmask)
            ).prefixlen
        )
    except (OSError, ValueError):
        pass

    return details


def _discover_ipv6():
    addresses = {}

    try:
        with open("/proc/net/if_inet6", "r") as file:
            for line in file:
                fields = line.split()

                if len(fields) != 6:
                    continue

                raw, index, prefix, scope, flags, name = fields

                try:
                    address = str(
                        ipaddress.IPv6Address(
                            int(raw, 16)
                        )
                    )
                except ValueError:
                    continue

                scope_value = int(scope, 16)

                scope_name = {
                    0x00: "global",
                    0x10: "host",
                    0x20: "link",
                    0x40: "site",
                }.get(scope_value, "unknown")

                addresses.setdefault(name, []).append(
                    NetworkAddress(
                        address=address,
                        family="IPv6",
                        prefix_length=int(prefix, 16),
                        scope=scope_name,
                    )
                )

    except OSError:
        pass

    return addresses


def discover_interfaces():
    try:
        names = socket.if_nameindex()
    except (OSError, AttributeError) as error:
        raise RuntimeError(
            "Linux interface enumeration failed: {}".format(error)
        )

    ipv6_addresses = _discover_ipv6()
    interfaces = []

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    ) as sock:

        for index, name in names:
            interface = NetworkInterface(
                name=name,
                source="Linux sysfs and ioctl",
            )

            base = os.path.join("/sys/class/net", name)

            try:
                with open(
                    os.path.join(base, "operstate"), "r"
                ) as file:
                    interface.status = file.read().strip()
            except OSError:
                interface.status = "unknown"

            try:
                flags = _interface_request(
                    sock, name, SIOCGIFFLAGS
                )
                flag_value = struct.unpack(
                    "H", flags[16:18]
                )[0]
                interface.is_up = bool(flag_value & IFF_UP)
            except OSError:
                pass

            try:
                with open(
                    os.path.join(base, "mtu"), "r"
                ) as file:
                    interface.mtu = int(file.read().strip())
            except (OSError, ValueError):
                pass

            try:
                with open(
                    os.path.join(base, "address"), "r"
                ) as file:
                    mac = file.read().strip().lower()

                if mac and mac != "00:00:00:00:00:00":
                    interface.mac_address = mac
            except OSError:
                pass

            ipv4 = _ipv4_details(sock, name)

            if ipv4.get("address"):

                interface.addresses.append(

                    NetworkAddress(

                        address=ipv4["address"],

                        family="IPv4",

                        prefix_length=ipv4.get("prefix_length"),

                        scope="host",

                    )

                )

            interface.addresses.extend(

                ipv6_addresses.get(name, [])

            )

            interfaces.append(interface)

    return interfaces

def discover_gateway():

    route_file = "/proc/net/route"

    candidates = []

    try:

        with open(route_file, "r") as file:

            next(file, None)

            for line in file:

                fields = line.split()

                if len(fields) < 8:

                    continue

                if fields[1] != "00000000":

                    continue

                try:

                    flags = int(fields[3], 16)

                    metric = int(fields[6])

                    gateway_value = int(fields[2], 16)

                except ValueError:

                    continue

                if not (flags & 0x2):

                    continue

                if gateway_value == 0:

                    continue

                gateway = socket.inet_ntoa(

                    struct.pack("<I", gateway_value)

                )

                candidates.append((metric, gateway))

    except OSError:

        return None

    if not candidates:

        return None

    candidates.sort(key=lambda item: item[0])

    return candidates[0][1]

