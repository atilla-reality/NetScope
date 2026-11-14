import unittest
from unittest.mock import mock_open, patch

from netscope.platforms.linux import (
    _discover_ipv6,
    discover_gateway,
)


class LinuxIPv6Tests(unittest.TestCase):

    def test_ipv6_address_discovery(self):
        content = (
            "20010db8000000000000000000000001 "
            "02 40 00 80 eth0\n"
            "fe800000000000000000000000000001 "
            "02 40 20 80 eth0\n"
        )

        with patch(
            "builtins.open",
            mock_open(read_data=content),
        ):
            result = _discover_ipv6()

        self.assertIn("eth0", result)
        self.assertEqual(len(result["eth0"]), 2)

        global_address = result["eth0"][0]

        self.assertEqual(
            global_address.address,
            "2001:db8::1",
        )
        self.assertEqual(global_address.prefix_length, 64)
        self.assertEqual(global_address.scope, "global")

        link_local = result["eth0"][1]

        self.assertEqual(
            link_local.address,
            "fe80::1",
        )
        self.assertEqual(link_local.scope, "link")


class LinuxGatewayTests(unittest.TestCase):

    def test_gateway_discovery(self):
        content = (
            "Iface Destination Gateway Flags RefCnt "
            "Use Metric Mask\n"
            "eth0 00000000 0101A8C0 0003 0 0 100 00000000\n"
        )

        with patch(
            "builtins.open",
            mock_open(read_data=content),
        ):
            result = discover_gateway()

        self.assertEqual(result, "192.168.1.1")

    def test_lowest_metric_gateway_selected(self):
        content = (
            "Iface Destination Gateway Flags RefCnt "
            "Use Metric Mask\n"
            "eth0 00000000 0101A8C0 0003 0 0 100 00000000\n"
            "wlan0 00000000 0201A8C0 0003 0 0 10 00000000\n"
        )

        with patch(
            "builtins.open",
            mock_open(read_data=content),
        ):
            result = discover_gateway()

        self.assertEqual(result, "192.168.1.2")

    def test_gateway_not_found(self):
        content = (
            "Iface Destination Gateway Flags RefCnt "
            "Use Metric Mask\n"
            "eth0 0101A8C0 00000000 0001 0 0 100 FFFFFFFF\n"
        )

        with patch(
            "builtins.open",
            mock_open(read_data=content),
        ):
            result = discover_gateway()

        self.assertIsNone(result)

    def test_route_file_error(self):
        with patch(
            "builtins.open",
            side_effect=OSError("Permission denied"),
        ):
            result = discover_gateway()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()


class LinuxInterfaceTests(unittest.TestCase):

    @patch("netscope.platforms.linux._discover_ipv6")
    @patch("netscope.platforms.linux._interface_request")
    @patch("netscope.platforms.linux.socket.socket")
    @patch("netscope.platforms.linux.socket.if_nameindex")
    @patch("builtins.open")
    def test_interface_metadata(
        self,
        mock_open_file,
        mock_names,
        mock_socket,
        mock_ioctl,
        mock_ipv6,
    ):
        from unittest.mock import mock_open as make_mock_open
        import struct

        mock_names.return_value = [(2, "eth0")]
        mock_ipv6.return_value = {}

        files = {
            "/sys/class/net/eth0/operstate": "up\n",
            "/sys/class/net/eth0/mtu": "1500\n",
            "/sys/class/net/eth0/address": "00:11:22:33:44:55\n",
        }

        def open_file(path, *args, **kwargs):
            if path not in files:
                raise OSError("File unavailable")

            return make_mock_open(
                read_data=files[path]
            )()

        mock_open_file.side_effect = open_file

        ipv4_response = bytearray(24)
        ipv4_response[20:24] = bytes([192, 168, 1, 10])

        mask_response = bytearray(24)
        mask_response[20:24] = bytes([255, 255, 255, 0])

        flags_response = bytearray(24)
        struct.pack_into("H", flags_response, 16, 1)

        def ioctl_response(sock, name, request):
            if request == 0x8915:
                return bytes(ipv4_response)
            if request == 0x891B:
                return bytes(mask_response)
            if request == 0x8913:
                return bytes(flags_response)
            raise OSError("Unknown ioctl")

        mock_ioctl.side_effect = ioctl_response

        interfaces = (
            __import__(
                "netscope.platforms.linux",
                fromlist=["discover_interfaces"],
            ).discover_interfaces()
        )

        self.assertEqual(len(interfaces), 1)

        interface = interfaces[0]

        self.assertEqual(interface.name, "eth0")
        self.assertEqual(interface.status, "up")
        self.assertTrue(interface.is_up)
        self.assertEqual(interface.mtu, 1500)
        self.assertEqual(
            interface.mac_address,
            "00:11:22:33:44:55",
        )

        self.assertEqual(len(interface.addresses), 1)
        self.assertEqual(
            interface.addresses[0].address,
            "192.168.1.10",
        )
        self.assertEqual(
            interface.addresses[0].prefix_length,
            24,
        )

    @patch("netscope.platforms.linux.socket.if_nameindex")
    def test_interface_enumeration_error(self, mock_names):
        from netscope.platforms.linux import discover_interfaces

        mock_names.side_effect = OSError(
            "No buffer space available"
        )

        with self.assertRaises(RuntimeError):
            discover_interfaces()


