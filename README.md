# PortScope

A lightweight TCP port scanner written in pure Python (standard library only), built for **authorized security testing and cybersecurity education**.

> **Warning:** Only scan systems you own or have explicit written permission to test. Unauthorized port scanning may violate laws or policies. You are responsible for how you use this tool.

## Overview

PortScope performs TCP connect scans: it tries to open a connection to each requested port and classifies the result. It was built as a junior-level portfolio project to demonstrate networking fundamentals (TCP, DNS, timeouts, error codes), concurrency, defensive input handling, testing, and documentation.

## Features

- Scan a hostname or IPv4 address over a port, range, or list (`80`, `20-100`, `22,80,443`)
- Classifies ports as `open`, `closed`, or `filtered_or_unknown`
- Connection response time in milliseconds
- Configurable timeout, concurrency, and per-run port limit
- Progress indicator and clear summary
- JSON and CSV export (target, IP, timestamp, port, status, response time)
- Graceful handling of invalid input, DNS failures, timeouts, and network errors
- Safe by default: only loopback/private targets are allowed unless `--allow-public` is passed
- No third-party dependencies; 16 unit tests that need no Internet access

## Example output

Real output from scanning a throwaway local listener:

```text
PortScope 1.0.0
WARNING: Only scan systems you own or have explicit written permission to test.
         Unauthorized scanning may be illegal.

Target : 127.0.0.1 (127.0.0.1)
Ports  : 5 | timeout 0.5s | workers 20

PORT   STATUS                TIME (ms)  SERVICE
51931  closed                0.14       -
51932  closed                0.01       -
51933  open                  0.07       -
51934  closed                0.05       -
51935  closed                0.01       -

--- Summary ---
Scanned at : 2026-10-15T16:35:25+00:00
Duration   : 0.0s
Open       : 1
Closed     : 4
Filtered/unknown: 0
Note: 'filtered_or_unknown' means no reliable answer (e.g. a timeout); it does not prove a firewall is present.
```

(Without `--show-all`, only open ports are listed.) See [`examples/sample_output.json`](examples/sample_output.json).

## Requirements

- Python 3.8 or newer
- No external packages

## Installation

```bash
git clone https://github.com/brrssm/PortScope.git
cd PortScope
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1   |   Linux/macOS: source .venv/bin/activate
pip install -e .        # optional: installs the `portscope` command
```

You can also run it without installing: `python -m portscope ...`

## Usage

```bash
python -m portscope 127.0.0.1                           # default: ports 1-1024, 1s timeout
python -m portscope localhost -p 20-100 -t 0.5          # custom range and timeout
python -m portscope 127.0.0.1 -p 22,80,443,8080 --show-all
python -m portscope 192.168.56.101 -p 1-1024 -w 30      # your own lab VM (private address)
python -m portscope --help
```

| Option | Default | Description |
|---|---|---|
| `target` | required | Hostname or IPv4 address |
| `-p, --ports` | `1-1024` | Port, range, or comma-separated list |
| `-t, --timeout` | `1.0` | Seconds to wait per connection |
| `-w, --workers` | `20` | Concurrent connections (1-100) |
| `--max-ports` | `1024` | Maximum ports per run (up to 65535) |
| `--json FILE` / `--csv FILE` | off | Export results |
| `--show-all` | off | Also list closed and filtered/unknown ports |
| `--allow-public` | off | Permit non-private targets (authorized use only) |

## Exporting results

```bash
python -m portscope 127.0.0.1 -p 1-1024 --json reports/scan.json --csv reports/scan.csv
```

Parent folders are created automatically. CSV columns: `target, ip, scan_timestamp, port, status, response_time_ms, error`.

## Running tests

```bash
python -m unittest discover -v
```

## Limitations

- TCP connect scan only (no UDP, no SYN scan, no service/version detection)
- IPv4 only
- A timeout is reported as `filtered_or_unknown` because it can mean a firewall drop, a slow host, packet loss, or a down host; it is **not** proof of filtering
- Response time includes only connection setup and is affected by system load and concurrency
- Results are a point-in-time snapshot

## Future improvements

- IPv6 support
- Optional banner grabbing for well-known services
- Port-list presets (for example "top 100")
- HTML report output
- Packaging for PyPI and CI via GitHub Actions

## Portfolio description

PortScope is a dependency-free Python CLI that implements a multi-threaded TCP connect scanner with strict input validation, scan limits, authorization guardrails, structured JSON/CSV reporting, and a unit-test suite using mocked sockets. It demonstrates practical knowledge of TCP behavior, DNS resolution, error handling, concurrency, and responsible security tooling.

## License

MIT. See [LICENSE](LICENSE).
