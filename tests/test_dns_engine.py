import socket
import struct
import unittest
from unittest.mock import patch

from netscope.modules.dns import (
    DNSQueryError,
    _decode_name,
    _encode_name,
    _parse_response,
    discover_nameservers,
    resolve_dns,
)


class DNSEncodingTests(unittest.TestCase):

    def test_encode_hostname(self):
        result = _encode_name("example.com")
        self.assertEqual(
            result,
            b"\x07example\x03com\x00",
        )

    def test_encode_root_trailing_dot(self):
        self.assertEqual(
            _encode_name("example.com."),
            _encode_name("example.com"),
        )

    def test_invalid_hostname(self):
        with self.assertRaises(DNSQueryError):
            _encode_name("")

    def test_decode_hostname(self):
        packet = b"\x07example\x03com\x00"
        name, offset = _decode_name(packet, 0)

        self.assertEqual(name, "example.com")
        self.assertEqual(offset, len(packet))

    def test_decode_compression_pointer(self):
        packet = (
            b"\x07example\x03com\x00"
            b"\xC0\x00"
        )

        name, offset = _decode_name(packet, 13)

        self.assertEqual(name, "example.com")
        self.assertEqual(offset, 15)


class DNSResponseTests(unittest.TestCase):

    def build_response(self, record_type, data):
        question = (
            _encode_name("example.com")
            + struct.pack("!HH", record_type, 1)
        )

        answer = (
            b"\xC0\x0C"
            + struct.pack(
                "!HHIH",
                record_type,
                1,
                300,
                len(data),
            )
            + data
        )

        header = struct.pack(
            "!HHHHHH",
            1234,
            0x8180,
            1,
            1,
            0,
            0,
        )

        return header + question + answer

    def test_parse_a_record(self):
        packet = self.build_response(
            1,
            socket.inet_aton("192.0.2.10"),
        )

        records = _parse_response(packet, 1234)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["type"], "A")
        self.assertEqual(records[0]["value"], "192.0.2.10")
        self.assertEqual(records[0]["ttl"], 300)

    def test_parse_aaaa_record(self):
        packet = self.build_response(
            28,
            socket.inet_pton(
                socket.AF_INET6,
                "2001:db8::1",
            ),
        )

        records = _parse_response(packet, 1234)

        self.assertEqual(records[0]["type"], "AAAA")
        self.assertEqual(records[0]["value"], "2001:db8::1")

    def test_parse_ns_record(self):
        packet = self.build_response(
            2,
            b"\xC0\x0C",
        )

        records = _parse_response(packet, 1234)

        self.assertEqual(records[0]["type"], "NS")
        self.assertEqual(records[0]["value"], "example.com")

    def test_parse_cname_record(self):
        packet = self.build_response(
            5,
            b"\xC0\x0C",
        )

        records = _parse_response(packet, 1234)

        self.assertEqual(records[0]["type"], "CNAME")
        self.assertEqual(records[0]["value"], "example.com")

    def test_parse_mx_record(self):
        packet = self.build_response(
            15,
            struct.pack("!H", 10) + b"\xC0\x0C",
        )

        records = _parse_response(packet, 1234)

        self.assertEqual(records[0]["type"], "MX")
        self.assertEqual(records[0]["value"]["preference"], 10)
        self.assertEqual(
            records[0]["value"]["exchange"],
            "example.com",
        )

    def test_parse_txt_record(self):
        packet = self.build_response(
            16,
            b"\x05hello\x05world",
        )

        records = _parse_response(packet, 1234)

        self.assertEqual(records[0]["type"], "TXT")
        self.assertEqual(
            records[0]["value"],
            ["hello", "world"],
        )

    def test_reject_invalid_ns_rdata_length(self):
        packet = self.build_response(
            2,
            b"\\xC0\\x0C\\x00",
        )

        with self.assertRaises(DNSQueryError):
            _parse_response(packet, 1234)

    def test_reject_invalid_mx_rdata_length(self):
        packet = self.build_response(
            15,
            struct.pack("!H", 10) + b"\\xC0\\x0C\\x00",
        )

        with self.assertRaises(DNSQueryError):
            _parse_response(packet, 1234)

    def test_transaction_id_mismatch(self):
        packet = self.build_response(
            1,
            socket.inet_aton("192.0.2.10"),
        )

        with self.assertRaises(DNSQueryError):
            _parse_response(packet, 9999)

    def test_nxdomain(self):
        packet = struct.pack(
            "!HHHHHH",
            1234,
            0x8183,
            0,
            0,
            0,
            0,
        )

        with self.assertRaises(DNSQueryError):
            _parse_response(packet, 1234)

    def test_truncated_response(self):
        packet = struct.pack(
            "!HHHHHH",
            1234,
            0x8380,
            0,
            0,
            0,
            0,
        )

        with self.assertRaises(DNSQueryError):
            _parse_response(packet, 1234)


class DNSResolverTests(unittest.TestCase):

    @patch("netscope.modules.dns.discover_nameservers")
    @patch("netscope.modules.dns._query_server")
    def test_resolve_a_record(self, mock_query, mock_servers):
        mock_servers.return_value = ["192.0.2.53"]
        mock_query.return_value = [{
            "name": "example.com",
            "type": "A",
            "class": "IN",
            "ttl": 300,
            "value": "192.0.2.10",
        }]

        result = resolve_dns(
            "example.com",
            ["A"],
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["records"]), 1)

    @patch("netscope.modules.dns.discover_nameservers")

    def test_no_nameserver_for_mx(self, mock_servers):

        mock_servers.return_value = []

        with self.assertRaises(DNSQueryError):

            resolve_dns("example.com", ["MX"])

    @patch("netscope.modules.dns.discover_nameservers")

    @patch("netscope.modules.dns._query_server")

    def test_query_error(self, mock_query, mock_servers):

        mock_servers.return_value = ["192.0.2.53"]

        mock_query.side_effect = OSError("Network unavailable")

        result = resolve_dns("example.com", ["A"])

        self.assertEqual(result["status"], "error")

        self.assertTrue(result["errors"])

    def test_unsupported_record_type(self):

        with self.assertRaises(DNSQueryError):

            resolve_dns("example.com", ["PTR"])

    def test_invalid_timeout(self):

        with self.assertRaises(DNSQueryError):

            resolve_dns("example.com", ["A"], timeout=0)

if __name__ == "__main__":

    unittest.main()



class DNSDecoderValidationTests(unittest.TestCase):

    def test_reject_truncated_compression_pointer(self):
        with self.assertRaises(DNSQueryError):
            _decode_name(b"\xC0", 0)

    def test_reject_out_of_bounds_compression_pointer(self):
        with self.assertRaises(DNSQueryError):
            _decode_name(b"\xC0\xFF", 0)

    def test_reject_invalid_label_encoding(self):
        with self.assertRaises(DNSQueryError):
            _decode_name(b"\x40", 0)

    def test_reject_self_referencing_pointer(self):
        with self.assertRaises(DNSQueryError):
            _decode_name(b"\xC0\x00", 0)

    def test_reject_circular_compression_pointers(self):
        packet = b"\xC0\x02\xC0\x00"

        with self.assertRaises(DNSQueryError):
            _decode_name(packet, 0)

    def test_reject_expanded_name_over_255_bytes(self):
        label = b"\x3F" + (b"a" * 63)
        packet = label * 4 + b"\x00"

        with self.assertRaises(DNSQueryError):
            _decode_name(packet, 0)
