from netscope.core.engine import run_network_diagnostics


def show_network():
    result = run_network_diagnostics()
    data = result.to_dict()

    print("=" * 48)
    print("              NetScope Network")
    print("=" * 48)

    print("Platform :", data["platform"])
    print("Status   :", data["status"])
    print("Gateway  :", data["gateway"] or "Unavailable")

    hint = data.get("route_hint")

    if hint:
        print("Route Hint:", hint.get("local_address"))
        print("Route Method:", hint.get("method"))

    print("\nCapabilities:")

    for name, available in data["capabilities"].items():
        state = "Available" if available else "Unavailable"
        print("  {:22} {}".format(name, state))

    print("\nInterfaces:")

    for interface in data["interfaces"]:
        print("\n  Name:", interface["name"])
        print("  Status:", interface["status"])
        print("  MAC:", interface["mac_address"] or "Unavailable")
        print("  MTU:", interface["mtu"] or "Unavailable")

        for address in interface["addresses"]:
            print("  {}: {}".format(
                address["family"],
                address["address"],
            ))

    if data["errors"]:
        print("\nDiagnostics warnings:")

        for error in data["errors"]:
            print("  -", error)

    print("=" * 48)
    return data
