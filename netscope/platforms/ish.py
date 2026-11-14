import socket

from netscope.core.models import NetworkInterface


def discover_interfaces():
    try:
        names = socket.if_nameindex()
    except (OSError, AttributeError) as error:
        raise RuntimeError(
            "iSH interface enumeration unavailable: {}".format(error)
        )

    return [
        NetworkInterface(
            name=name,
            source="socket.if_nameindex",
        )
        for index, name in names
    ]


def discover_route_hint():
    """
    Infer the local source address selected by the OS.

    UDP connect does not send application payload data.
    This is not gateway discovery.
    """
    sock = None

    try:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sock.connect(("192.0.2.1", 9))
        address = sock.getsockname()[0]

        if address and not address.startswith("127."):
            return {
                "local_address": address,
                "method": "UDP route selection",
                "note": "Inferred source address; not a gateway.",
            }

    except OSError:
        return None

    finally:
        if sock is not None:
            sock.close()

    return None
