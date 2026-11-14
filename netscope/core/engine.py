from netscope.core.models import NetworkDiagnostics
from netscope.platforms.detector import detect_platform


def _safe_discovery(result, label, function):
    try:
        return function()
    except Exception as error:
        result.errors.append(
            "{}: {}".format(label, error)
        )
        return None


def run_network_diagnostics():
    system = detect_platform()

    result = NetworkDiagnostics(
        platform=system,
        capabilities={
            "interface_discovery": False,
            "ipv4": False,
            "ipv6": False,
            "mac_address": False,
            "mtu": False,
            "gateway": False,
            "route_hint": False,
        },
    )

    adapters = {
        "ish": ("netscope.platforms.ish", False),
        "linux": ("netscope.platforms.linux", True),
        "termux": ("netscope.platforms.linux", True),
        "windows": ("netscope.platforms.windows", True),
    }

    adapter_info = adapters.get(system)

    if adapter_info is None:
        result.errors.append(
            "Unsupported platform: {}".format(system)
        )
        return result

    module_name, supports_gateway = adapter_info

    try:
        import importlib
        adapter = importlib.import_module(module_name)
    except Exception as error:
        result.errors.append(
            "Adapter loading failed: {}".format(error)
        )
        return result

    interfaces = _safe_discovery(
        result,
        "Interface discovery",
        adapter.discover_interfaces,
    )

    if interfaces is not None:
        result.interfaces = interfaces

    if supports_gateway:
        gateway = _safe_discovery(
            result,
            "Gateway discovery",
            adapter.discover_gateway,
        )

        if gateway:
            result.gateway = gateway
    else:
        route_hint = _safe_discovery(
            result,
            "Route hint discovery",
            adapter.discover_route_hint,
        )

        if route_hint:
            result.route_hint = route_hint

    result.capabilities["interface_discovery"] = bool(
        result.interfaces
    )

    result.capabilities["gateway"] = bool(result.gateway)
    result.capabilities["route_hint"] = bool(result.route_hint)

    for interface in result.interfaces:
        if interface.mac_address:
            result.capabilities["mac_address"] = True

        if interface.mtu:
            result.capabilities["mtu"] = True

        for address in interface.addresses:
            if address.family == "IPv4":
                result.capabilities["ipv4"] = True
            elif address.family == "IPv6":
                result.capabilities["ipv6"] = True

    return result
