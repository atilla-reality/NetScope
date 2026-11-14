import unittest
from unittest.mock import patch

from netscope.core.models import (
    NetworkAddress,
    NetworkDiagnostics,
    NetworkInterface,
)


class ModelTests(unittest.TestCase):

    def test_address_serialization(self):
        address = NetworkAddress(
            address="192.168.1.10",
            family="IPv4",
            prefix_length=24,
        )

        data = address.__dict__

        self.assertEqual(data["address"], "192.168.1.10")
        self.assertEqual(data["family"], "IPv4")

    def test_interface_serialization(self):
        interface = NetworkInterface(
            name="eth0",
            mac_address="00:11:22:33:44:55",
            mtu=1500,
            is_up=True,
            status="up",
        )

        interface.addresses.append(
            NetworkAddress(
                address="192.168.1.10",
                family="IPv4",
            )
        )

        data = interface.to_dict()

        self.assertEqual(data["name"], "eth0")
        self.assertEqual(data["mtu"], 1500)
        self.assertEqual(len(data["addresses"]), 1)

    def test_diagnostics_status(self):
        result = NetworkDiagnostics(
            platform="ish",
            route_hint={
                "local_address": "192.168.1.62"
            },
        )

        self.assertEqual(result.to_dict()["status"], "ok")

    def test_partial_status(self):
        result = NetworkDiagnostics(
            platform="ish",
            errors=["Interface discovery unavailable"],
            route_hint={
                "local_address": "192.168.1.62"
            },
        )

        self.assertEqual(result.to_dict()["status"], "partial")


class EngineTests(unittest.TestCase):

    @patch("netscope.platforms.detector.detect_platform")
    @patch("netscope.platforms.ish.discover_route_hint")
    @patch("netscope.platforms.ish.discover_interfaces")
    def test_ish_route_hint_survives_interface_error(
        self,
        mock_interfaces,
        mock_route,
        mock_platform,
    ):
        from netscope.core.engine import run_network_diagnostics

        mock_platform.return_value = "ish"

        mock_interfaces.side_effect = RuntimeError(
            "Interface enumeration unavailable"
        )

        mock_route.return_value = {
            "local_address": "192.168.1.62",
            "method": "UDP route selection",
        }

        result = run_network_diagnostics()
        data = result.to_dict()

        self.assertEqual(data["platform"], "ish")
        self.assertEqual(data["status"], "partial")
        self.assertTrue(data["capabilities"]["route_hint"])
        self.assertFalse(data["capabilities"]["interface_discovery"])
        self.assertEqual(
            data["route_hint"]["local_address"],
            "192.168.1.62",
        )


if __name__ == "__main__":
    unittest.main()
