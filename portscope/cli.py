"""Command-line interface for PortScope."""
from __future__ import annotations

import argparse
import socket
import sys
from typing import List, Optional

from portscope import __version__
from portscope.exporter import export_csv, export_json
from portscope.scanner import (
    ABSOLUTE_MAX_PORTS,
    CLOSED,
    DEFAULT_MAX_PORTS,
    DEFAULT_PORTS,
    DEFAULT_TIMEOUT,
    DEFAULT_WORKERS,
    MAX_WORKERS,
    OPEN,
    UNKNOWN,
    PortScopeError,
    is_private_target,
    parse_ports,
    resolve_target,
    scan_ports,
    validate_port_count,
)

WARNING = (
    "WARNING: Only scan systems you own or have explicit written permission to test.\n"
    "         Unauthorized scanning may be illegal."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portscope",
        description="PortScope: a lightweight TCP port scanner for authorized testing and education.",
        epilog="Example: python -m portscope 127.0.0.1 -p 20-100 --timeout 0.5 --json report.json",
    )
    parser.add_argument("target", help="hostname or IPv4 address (e.g. 127.0.0.1)")
    parser.add_argument("-p", "--ports", default=DEFAULT_PORTS,
                        help=f"ports to scan, e.g. 80, 20-100, 22,80,443 (default: {DEFAULT_PORTS})")
    parser.add_argument("-t", "--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"connection timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"concurrent connections, 1-{MAX_WORKERS} (default: {DEFAULT_WORKERS})")
    parser.add_argument("--max-ports", type=int, default=DEFAULT_MAX_PORTS,
                        help=f"maximum ports per run, up to {ABSOLUTE_MAX_PORTS} (default: {DEFAULT_MAX_PORTS})")
    parser.add_argument("--json", metavar="FILE", help="export results to a JSON file")
    parser.add_argument("--csv", metavar="FILE", help="export results to a CSV file")
    parser.add_argument("--show-all", action="store_true",
                        help="list closed and filtered/unknown ports too (default: open only)")
    parser.add_argument("--allow-public", action="store_true",
                        help="allow non-private targets; ONLY if you have explicit authorization")
    parser.add_argument("--version", action="version", version=f"PortScope {__version__}")
    return parser


def _service_name(port: int) -> str:
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return "-"


def _progress(done: int, total: int) -> None:
    if sys.stderr.isatty():
        sys.stderr.write(f"\rScanning... {done}/{total} ({done * 100 // total}%)")
        sys.stderr.flush()
        if done == total:
            sys.stderr.write("\n")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"PortScope {__version__}\n{WARNING}\n")

    try:
        ports = parse_ports(args.ports)
        validate_port_count(ports, args.max_ports)
        if args.timeout <= 0:
            raise PortScopeError("Timeout must be greater than 0.")
        if not 1 <= args.workers <= MAX_WORKERS:
            raise PortScopeError(f"Workers must be between 1 and {MAX_WORKERS}.")
        ip = resolve_target(args.target)
        if not is_private_target(ip) and not args.allow_public:
            raise PortScopeError(
                f"{ip} is not a loopback/private address. PortScope refuses to scan it by default. "
                "If you have explicit authorization, add --allow-public."
            )
    except PortScopeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Target : {args.target} ({ip})")
    print(f"Ports  : {len(ports)} | timeout {args.timeout}s | workers {args.workers}\n")

    try:
        report = scan_ports(args.target, ip, ports, args.timeout, args.workers, _progress)
    except KeyboardInterrupt:
        print("\nScan interrupted by user.", file=sys.stderr)
        return 130

    shown = [r for r in report.results if args.show_all or r.status == OPEN]
    if shown:
        print(f"{'PORT':<7}{'STATUS':<22}{'TIME (ms)':<11}SERVICE")
        for r in shown:
            t = "-" if r.response_time_ms is None else f"{r.response_time_ms:.2f}"
            print(f"{r.port:<7}{r.status:<22}{t:<11}{_service_name(r.port)}")
    else:
        print("No open ports found." if not args.show_all else "No results.")

    print("\n--- Summary ---")
    print(f"Scanned at : {report.timestamp}")
    print(f"Duration   : {report.duration_seconds}s")
    print(f"Open       : {report.count(OPEN)}")
    print(f"Closed     : {report.count(CLOSED)}")
    print(f"Filtered/unknown: {report.count(UNKNOWN)}")
    print("Note: 'filtered_or_unknown' means no reliable answer (e.g. a timeout); "
          "it does not prove a firewall is present.")

    try:
        if args.json:
            export_json(report, args.json)
            print(f"JSON report written to {args.json}")
        if args.csv:
            export_csv(report, args.csv)
            print(f"CSV report written to {args.csv}")
    except OSError as exc:
        print(f"Error: could not write report: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
