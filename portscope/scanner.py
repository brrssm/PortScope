"""Core scanning logic for PortScope (standard library only)."""
from __future__ import annotations

import errno
import ipaddress
import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional

# Port states
OPEN = "open"
CLOSED = "closed"
UNKNOWN = "filtered_or_unknown"  # no reliable answer (e.g. timeout); NOT proof of a firewall

# Defaults and limits
DEFAULT_PORTS = "1-1024"
DEFAULT_TIMEOUT = 1.0
DEFAULT_WORKERS = 20
MAX_WORKERS = 100
DEFAULT_MAX_PORTS = 1024
ABSOLUTE_MAX_PORTS = 65535

# connect_ex() codes meaning "the host actively refused" (10061 = Windows WSAECONNREFUSED)
CLOSED_CODES = {errno.ECONNREFUSED, 10061}


class PortScopeError(Exception):
    """Base class for all PortScope errors."""


class InvalidPortError(PortScopeError):
    """A port or port range is malformed or out of range."""


class ScanLimitError(PortScopeError):
    """The requested scan exceeds a configured limit."""


class TargetError(PortScopeError):
    """The target is empty or cannot be resolved."""


@dataclass
class PortResult:
    """Result for a single port."""

    port: int
    status: str
    response_time_ms: Optional[float] = None  # only set when the host actually answered
    error: Optional[str] = None


@dataclass
class ScanReport:
    """Everything produced by one scan."""

    target: str
    ip: str
    timestamp: str
    timeout: float
    results: List[PortResult] = field(default_factory=list)
    duration_seconds: float = 0.0

    def count(self, status: str) -> int:
        return sum(1 for r in self.results if r.status == status)


def parse_ports(spec: str) -> List[int]:
    """Parse '80', '20-25' or '22,80,443-445' into a sorted list of unique ports."""
    if not isinstance(spec, str) or not spec.strip():
        raise InvalidPortError("Port specification is empty.")
    ports = set()
    for part in spec.split(","):
        part = part.strip()
        try:
            if "-" in part:
                start_s, end_s = part.split("-", 1)
                start, end = int(start_s), int(end_s)
            else:
                start = end = int(part)
        except ValueError:
            raise InvalidPortError(f"Invalid port or range: {part!r}") from None
        if not (1 <= start <= 65535 and 1 <= end <= 65535):
            raise InvalidPortError(f"Ports must be between 1 and 65535: {part!r}")
        if start > end:
            raise InvalidPortError(f"Range start is greater than end: {part!r}")
        ports.update(range(start, end + 1))
    return sorted(ports)


def validate_port_count(ports: List[int], max_ports: int) -> None:
    """Raise ScanLimitError if the scan is larger than allowed."""
    if not 1 <= max_ports <= ABSOLUTE_MAX_PORTS:
        raise ScanLimitError(f"max-ports must be between 1 and {ABSOLUTE_MAX_PORTS}.")
    if len(ports) > max_ports:
        raise ScanLimitError(
            f"{len(ports)} ports requested but the limit is {max_ports}. "
            "Reduce the range or raise --max-ports."
        )


def resolve_target(target: str) -> str:
    """Resolve a hostname or IPv4 address to an IPv4 address string."""
    target = (target or "").strip()
    if not target:
        raise TargetError("Target is empty.")
    try:
        return socket.gethostbyname(target)
    except socket.gaierror as exc:
        raise TargetError(f"Could not resolve {target!r}: {exc}") from None
    except (UnicodeError, OSError) as exc:
        raise TargetError(f"Invalid target {target!r}: {exc}") from None


def is_private_target(ip: str) -> bool:
    """True for loopback, private (RFC 1918) and link-local addresses."""
    addr = ipaddress.ip_address(ip)
    return addr.is_loopback or addr.is_private or addr.is_link_local


def scan_port(ip: str, port: int, timeout: float) -> PortResult:
    """Try one TCP connection and classify the port."""
    sock = None
    start = time.perf_counter()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        code = sock.connect_ex((ip, port))
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        if code == 0:
            return PortResult(port, OPEN, elapsed)
        if code in CLOSED_CODES:
            return PortResult(port, CLOSED, elapsed)
        return PortResult(port, UNKNOWN, None, f"error code {code}: {os.strerror(code)}")
    except socket.timeout:
        return PortResult(port, UNKNOWN, None, "timed out")
    except OSError as exc:
        return PortResult(port, UNKNOWN, None, str(exc))
    finally:
        if sock is not None:
            sock.close()


def scan_ports(
    target: str,
    ip: str,
    ports: List[int],
    timeout: float = DEFAULT_TIMEOUT,
    workers: int = DEFAULT_WORKERS,
    progress: Optional[Callable[[int, int], None]] = None,
) -> ScanReport:
    """Scan ``ports`` on ``ip`` using a small thread pool and return a ScanReport."""
    if timeout <= 0:
        raise ValueError("timeout must be greater than 0.")
    if not 1 <= workers <= MAX_WORKERS:
        raise ValueError(f"workers must be between 1 and {MAX_WORKERS}.")

    report = ScanReport(
        target=target,
        ip=ip,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        timeout=timeout,
    )
    started = time.perf_counter()
    total = len(ports)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(scan_port, ip, p, timeout) for p in ports]
        for done, future in enumerate(as_completed(futures), start=1):
            report.results.append(future.result())
            if progress:
                progress(done, total)
    report.results.sort(key=lambda r: r.port)
    report.duration_seconds = round(time.perf_counter() - started, 2)
    return report
