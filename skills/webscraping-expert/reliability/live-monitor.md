# Live Extraction Monitor

A real-time browser dashboard that updates as records are extracted. No external dependencies — uses Python's stdlib HTTP server + browser fetch polling.

## Architecture

```
Extractor → LiveMonitor.update(record)
               ↓ writes live_status.json every N records
Python HTTP server (port 8765) → serves live_status.json
Browser → polls http://localhost:8765/live_status.json every 1s → updates UI
```

## Usage

```python
from live_monitor import LiveMonitor

monitor = LiveMonitor(source="irena", total=10_000)
monitor.start()   # opens browser + starts server

for record in extract():
    monitor.update(record, item_id=record["id"])
    writer.write(record)

monitor.finish()
```

## Files

- `src/live_monitor.py` — Python class + HTTP server
- `docs/live_monitor.html` — browser dashboard (same style as dashboard.html)

## Python implementation

```python
"""live_monitor.py — Real-time extraction progress server."""
from __future__ import annotations
import json, threading, time, webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from collections import deque

STATUS_PATH = Path(__file__).parents[1] / "docs" / "live_status.json"
MONITOR_URL = "http://localhost:8765/live_monitor.html"
PORT = 8765

class LiveMonitor:
    def __init__(self, source: str, total: int, write_every: int = 5):
        self.source = source
        self.total = total
        self.write_every = write_every
        self._completed = 0
        self._failed = 0
        self._started = time.time()
        self._rate_history: deque = deque(maxlen=60)
        self._last_records: deque = deque(maxlen=20)
        self._errors: deque = deque(maxlen=10)
        self._last_rate_ts = time.time()
        self._last_rate_count = 0
        self._lock = threading.Lock()

    def update(self, record: dict, item_id: str = "", failed: bool = False) -> None:
        with self._lock:
            if failed:
                self._failed += 1
                self._errors.appendleft({"id": item_id, "ts": time.strftime("%H:%M:%S")})
            else:
                self._completed += 1
                self._last_records.appendleft({
                    "id": item_id,
                    "ts": time.strftime("%H:%M:%S"),
                    "preview": str(record)[:120],
                })
            if self._completed % self.write_every == 0:
                self._update_rate()
                self._write()

    def _update_rate(self) -> None:
        now = time.time()
        elapsed = now - self._last_rate_ts
        if elapsed > 0:
            rate = (self._completed - self._last_rate_count) / elapsed
            self._rate_history.append(round(rate, 2))
            self._last_rate_ts = now
            self._last_rate_count = self._completed

    def _payload(self, status: str) -> dict:
        elapsed = time.time() - self._started
        rate = self._rate_history[-1] if self._rate_history else 0
        remaining = self.total - self._completed - self._failed
        eta = int(remaining / rate) if rate > 0 else None
        return {
            "source": self.source,
            "status": status,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._started)),
            "elapsed_s": round(elapsed),
            "total_expected": self.total,
            "completed": self._completed,
            "failed": self._failed,
            "pct": round(self._completed / max(self.total, 1) * 100, 1),
            "rate_per_sec": rate,
            "eta_seconds": eta,
            "rate_history": list(self._rate_history),
            "last_records": list(self._last_records),
            "errors": list(self._errors),
        }

    def _write(self, status: str = "running") -> None:
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text(json.dumps(self._payload(status), indent=2))

    def start(self, open_browser: bool = True) -> None:
        self._write("running")
        t = threading.Thread(target=self._serve, daemon=True)
        t.start()
        if open_browser:
            time.sleep(0.3)
            webbrowser.open(MONITOR_URL)

    def finish(self, status: str = "done") -> None:
        self._update_rate()
        self._write(status)
        print(f"\nMonitor: {MONITOR_URL}")

    def _serve(self) -> None:
        docs_dir = STATUS_PATH.parent
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(docs_dir), **kw)
            def log_message(self, *_): pass  # silence access logs
        try:
            HTTPServer(("localhost", PORT), Handler).serve_forever()
        except OSError:
            pass  # port already in use
```

See the full HTML in `docs/live_monitor.html`.
