import unittest

from netscope.cli import build_parser

class CLITests(unittest.TestCase):

    def setUp(self):

        self.parser = build_parser()

    def test_report_dns_argument(self):

        args = self.parser.parse_args([

            "report", "--dns", "example.com"

        ])

        self.assertEqual(args.command, "report")

        self.assertEqual(args.dns_hostname, "example.com")

    def test_report_dns_options(self):

        args = self.parser.parse_args([

            "report",

            "--dns", "example.com",

            "--dns-type", "A", "MX",

            "--dns-server", "1.1.1.1",

            "--dns-timeout", "5",

        ])

        self.assertEqual(args.dns_record_types, ["A", "MX"])

        self.assertEqual(args.dns_server, "1.1.1.1")

        self.assertEqual(args.dns_timeout, 5.0)

    def test_report_output_argument(self):

        args = self.parser.parse_args([

            "report", "--output", "report.json"

        ])

        self.assertEqual(args.output, "report.json")

    def test_dns_command(self):

        args = self.parser.parse_args([

            "dns", "example.com", "--type", "AAAA"

        ])

        self.assertEqual(args.command, "dns")

        self.assertEqual(args.hostname, "example.com")

        self.assertEqual(args.record_types, ["AAAA"])

    def test_abbreviated_dns_option_is_rejected(self):

        with self.assertRaises(SystemExit):

            self.parser.parse_args([

                "report", "--dn", "example.com"

            ])

if __name__ == "__main__":

    unittest.main()
