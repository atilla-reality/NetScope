import json
import subprocess
import unittest
from unittest.mock import patch

from netscope.platforms.windows import (
    _as_list,
    _run_powershell,
    discover_gateway,
    discover_interfaces,
)


class WindowsInterfaceTests(unittest.TestCase):

    @patch("netscope.platforms.windows._run_powershell")
    def test_interface_metadata(self, mock_run):
        mock_run.return_value = [{
            "InterfaceAlias": "Ethernet",
            "Status": "Up",
            "MacAddress": "00-11-22-33-44-55",
            "Mtu": 1500,
            "Addresses": [
                {
                    "IPAddress": "192.168.1.20",
                    "PrefixLength": 24,
                    "AddressFamily": "IPv4",
                },
                {
                    "IPAddress": "2001:db8::10",
                    "PrefixLength": 64,
                    "AddressFamily": "IPv6",
                },
            ],
        }]

        interfaces = discover_interfaces()

        self.assertEqual(len(interfaces), 1)

        interface = interfaces[0]

        self.assertEqual(interface.name, "Ethernet")
        self.assertEqual(interface.status, "up")
        self.assertTrue(interface.is_up)
        self.assertEqual(
            interface.mac_address,
            "00:11:22:33:44:55",
        )
        self.assertEqual(interface.mtu, 1500)
        self.assertEqual(len(interface.addresses), 2)
        self.assertEqual(
            interface.addresses[0].family,
            "IPv4",
        )
        self.assertEqual(
            interface.addresses[1].family,
            "IPv6",
        )

    @patch("netscope.platforms.windows._run_powershell")
    def test_single_interface_object(self, mock_run):
        mock_run.return_value = {
            "InterfaceAlias": "Wi-Fi",
            "Status": "Up",
            "Addresses": {
                "IPAddress": "192.168.1.30",
                "PrefixLength": 24,
                "AddressFamily": "IPv4",
            },
        }

        interfaces = discover_interfaces()

        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0].name, "Wi-Fi")
        self.assertEqual(len(interfaces[0].addresses), 1)

    @patch("netscope.platforms.windows._run_powershell")
    def test_empty_interface_list(self, mock_run):
        mock_run.return_value = []

        self.assertEqual(discover_interfaces(), [])

    @patch("netscope.platforms.windows._run_powershell")
    def test_invalid_mtu_is_ignored(self, mock_run):
        mock_run.return_value = [{
            "InterfaceAlias": "Ethernet",
            "Mtu": "invalid",
        }]

        interfaces = discover_interfaces()

        self.assertIsNone(interfaces[0].mtu)

    def test_as_list(self):
        self.assertEqual(_as_list(None), [])
        self.assertEqual(_as_list("item"), ["item"])
        self.assertEqual(_as_list([1, 2]), [1, 2])


class WindowsPowerShellTests(unittest.TestCase):

    @patch("netscope.platforms.windows.subprocess.run")
    def test_json_output(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"result": "ok"}',
            stderr="",
        )

        result = _run_powershell("test")

        self.assertEqual(result, {"result": "ok"})

    @patch("netscope.platforms.windows.subprocess.run")
    def test_empty_output(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        self.assertEqual(_run_powershell("test"), [])

    @patch("netscope.platforms.windows.subprocess.run")
    def test_invalid_json(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="not-json",
            stderr="",
        )

        with self.assertRaises(RuntimeError):
            _run_powershell("test")

    @patch("netscope.platforms.windows.subprocess.run")
    def test_gateway_not_found(self, mock_run):

        mock_run.return_value = subprocess.CompletedProcess(

            args=[],

            returncode=0,

            stdout="",

            stderr="",

        )

        self.assertIsNone(discover_gateway())

    @patch("netscope.platforms.windows.subprocess.run")

    def test_gateway_command_error(self, mock_run):

        mock_run.side_effect = subprocess.TimeoutExpired(

            cmd="powershell",

            timeout=15,

        )

        self.assertIsNone(discover_gateway())

if __name__ == "__main__":

    unittest.main()

