import errno
import socket
import unittest
from unittest import mock

from portscope import scanner
from portscope.scanner import (InvalidPortError, ScanLimitError, TargetError,
                               parse_ports, resolve_target, scan_port, scan_ports,
                               validate_port_count, is_private_target)


class TestPortParsing(unittest.TestCase):
    def test_single_range_and_list(self):
        self.assertEqual(parse_ports("80"), [80])
        self.assertEqual(parse_ports("20-23"), [20, 21, 22, 23])
        self.assertEqual(parse_ports("443, 22,80,22"), [22, 80, 443])

    def test_invalid_input(self):
        for bad in ["", "abc", "0", "65536", "100-50", "1-", "-5", "80,,"]:
            with self.subTest(bad=bad):
                with self.assertRaises(InvalidPortError):
                    parse_ports(bad)

    def test_max_scan_limit(self):
        ports = parse_ports("1-100")
        validate_port_count(ports, 100)  # exactly at limit is fine
        with self.assertRaises(ScanLimitError):
            validate_port_count(ports, 99)
        with self.assertRaises(ScanLimitError):
            validate_port_count(ports, 0)


class TestTarget(unittest.TestCase):
    def test_empty_target(self):
        with self.assertRaises(TargetError):
            resolve_target("  ")

    def test_dns_error(self):
        with mock.patch("portscope.scanner.socket.gethostbyname", side_effect=socket.gaierror("fail")):
            with self.assertRaises(TargetError):
                resolve_target("does-not-exist.invalid")

    def test_private_detection(self):
        self.assertTrue(is_private_target("127.0.0.1"))
        self.assertTrue(is_private_target("192.168.1.10"))
        self.assertFalse(is_private_target("8.8.8.8"))


class TestScanPortMocked(unittest.TestCase):
    def _scan(self, **kwargs):
        with mock.patch("portscope.scanner.socket.socket") as sock_cls:
            sock = sock_cls.return_value
            sock.connect_ex.return_value = kwargs.get("code", 0)
            if "exc" in kwargs:
                sock.connect_ex.side_effect = kwargs["exc"]
            result = scan_port("127.0.0.1", 80, 0.5)
            sock.close.assert_called_once()
            return result

    def test_open(self):
        r = self._scan(code=0)
        self.assertEqual(r.status, "open")
        self.assertIsNotNone(r.response_time_ms)

    def test_closed(self):
        self.assertEqual(self._scan(code=errno.ECONNREFUSED).status, "closed")
        self.assertEqual(self._scan(code=10061).status, "closed")

    def test_timeout_is_unknown_not_filtered_claim(self):
        r = self._scan(exc=socket.timeout())
        self.assertEqual(r.status, scanner.UNKNOWN)
        self.assertIsNone(r.response_time_ms)

    def test_network_error(self):
        r = self._scan(exc=OSError("Network is unreachable"))
        self.assertEqual(r.status, scanner.UNKNOWN)
        self.assertIn("unreachable", r.error)

    def test_other_error_code(self):
        self.assertEqual(self._scan(code=errno.EHOSTUNREACH).status, scanner.UNKNOWN)


class TestRealLoopback(unittest.TestCase):
    """Uses a throwaway listener on 127.0.0.1 only (no Internet needed)."""

    def test_detects_open_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            port = srv.getsockname()[1]
            report = scan_ports("127.0.0.1", "127.0.0.1", [port], timeout=1, workers=1)
        self.assertEqual(report.results[0].status, "open")
        self.assertEqual(report.count("open"), 1)

    def test_invalid_settings(self):
        with self.assertRaises(ValueError):
            scan_ports("x", "127.0.0.1", [80], timeout=0)
        with self.assertRaises(ValueError):
            scan_ports("x", "127.0.0.1", [80], workers=0)


if __name__ == "__main__":
    unittest.main()
