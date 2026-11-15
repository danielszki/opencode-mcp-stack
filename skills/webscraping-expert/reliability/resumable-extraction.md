# Resumable Extraction — Never Lose Data

## Core principle

All extractions must:
1. Save data incrementally as it arrives (not at the end)
2. Track progress in a checkpoint file
3. Resume from last saved position on restart
4. Never overwrite existing good data

---

## Standard checkpoint pattern

```python
import json, time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Iterator

@dataclass
class Checkpoint:
    source: str
    started_at: str
    last_saved_at: str
    total_expected: int
    completed_ids: list[str]   # IDs already successfully extracted
    failed_ids: list[str]      # IDs that failed after retries
    status: str                # "running" | "done" | "failed"

    @classmethod
    def load(cls, path: Path) -> "Checkpoint | None":
        if not path.exists():
            return None
        return cls(**json.loads(path.read_text()))

    def save(self, path: Path) -> None:
        self.last_saved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False))

    def is_done(self, item_id: str) -> bool:
        return item_id in self.completed_ids or item_id in self.failed_ids
```

---

## Incremental JSON lines writer

Use `.jsonl` (JSON Lines) for incremental writes — one JSON object per line, append-safe:

```python
class IncrementalWriter:
    """Appends records to a .jsonl file immediately on receipt."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._loaded: set[str] = self._load_existing_ids()

    def _load_existing_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        ids = set()
        with self.path.open() as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    if "id" in rec:
                        ids.add(str(rec["id"]))
                except Exception:
                    pass
        return ids

    def already_saved(self, record_id: str) -> bool:
        return str(record_id) in self._loaded

    def write(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        if "id" in record:
            self._loaded.add(str(record["id"]))

    def count(self) -> int:
        return len(self._loaded)
```

---

## Full resumable extractor pattern

```python
import requests, time, random
from pathlib import Path

class ResumableExtractor:
    CHECKPOINT_FILE = "checkpoint.json"
    DATA_FILE = "data.jsonl"
    MAX_RETRIES = 3

    def __init__(self, output_dir: Path):
        self.out = output_dir
        self.out.mkdir(parents=True, exist_ok=True)
        self.writer = IncrementalWriter(self.out / self.DATA_FILE)
        self.checkpoint_path = self.out / self.CHECKPOINT_FILE
        self.session = requests.Session()

    def fetch_item(self, item_id: str) -> dict | None:
        for attempt in range(self.MAX_RETRIES):
            try:
                r = self.session.get(
                    f"https://api.target.com/items/{item_id}",
                    timeout=30,
                )
                r.raise_for_status()
                return r.json()
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    wait = int(e.response.headers.get("Retry-After", 60))
                    print(f"  Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                elif e.response.status_code == 403:
                    print(f"  403 on {item_id} — possible IP ban. Stopping.")
                    raise
                else:
                    time.sleep(2 ** attempt)
            except Exception as e:
                print(f"  Error on {item_id} attempt {attempt+1}: {e}")
                time.sleep(2 ** attempt)
        return None

    def run(self, all_ids: list[str]) -> None:
        ckpt = Checkpoint.load(self.checkpoint_path) or Checkpoint(
            source="target",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            last_saved_at="",
            total_expected=len(all_ids),
            completed_ids=[],
            failed_ids=[],
            status="running",
        )

        remaining = [i for i in all_ids if not ckpt.is_done(i)]
        print(f"Resuming: {len(ckpt.completed_ids)} done, {len(remaining)} remaining")

        for n, item_id in enumerate(remaining, 1):
            print(f"[{n}/{len(remaining)}] {item_id}", end=" ")

            if self.writer.already_saved(item_id):
                print("(already in file, skipping)")
                if item_id not in ckpt.completed_ids:
                    ckpt.completed_ids.append(item_id)
                continue

            data = self.fetch_item(item_id)

            if data:
                self.writer.write({**data, "id": item_id})
                ckpt.completed_ids.append(item_id)
                print(f"✓ ({self.writer.count()} total)")
            else:
                ckpt.failed_ids.append(item_id)
                print("✗ (failed, logged)")

            ckpt.save(self.checkpoint_path)
            time.sleep(random.uniform(0.3, 0.7))

        ckpt.status = "done" if not ckpt.failed_ids else "partial"
        ckpt.save(self.checkpoint_path)
        print(f"\nDone. {len(ckpt.completed_ids)} saved, {len(ckpt.failed_ids)} failed.")
        if ckpt.failed_ids:
            print(f"Failed IDs: {ckpt.failed_ids}")


# Usage
extractor = ResumableExtractor(Path("data/target/raw"))
extractor.run(["item_001", "item_002", "item_003", ...])
# If interrupted: just run again — resumes from where it stopped
```

---

## Progress display

```python
from datetime import datetime, timedelta

class Progress:
    def __init__(self, total: int):
        self.total = total
        self.done = 0
        self.start = datetime.now()

    def update(self, n: int = 1) -> None:
        self.done += n

    def print(self) -> None:
        pct = self.done / self.total * 100
        elapsed = (datetime.now() - self.start).total_seconds()
        rate = self.done / elapsed if elapsed > 0 else 0
        eta = timedelta(seconds=int((self.total - self.done) / rate)) if rate > 0 else "?"
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"\r[{bar}] {pct:.1f}% ({self.done}/{self.total}) | {rate:.1f}/s | ETA: {eta}", end="")
```

---

## Converting .jsonl to final JSON

After extraction is complete, compile the jsonl into the standard envelope:

```python
def compile_jsonl(jsonl_path: Path, output_path: Path, metadata: dict) -> Path:
    records = []
    with jsonl_path.open() as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    payload = {
        "_metadata": {
            **metadata,
            "total_records": len(records),
            "compiled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "data": records,
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return output_path
```

---

## Rules

- Always write `.jsonl` during extraction — compile to `.json` only when complete
- Always save checkpoint **after** each successful write — never before
- Checkpoint + data file are the source of truth — the extractor is stateless
- On 403/IP ban: stop immediately, save checkpoint, report to user
- On 429: respect `Retry-After` header, then resume
- Never delete a checkpoint until the user explicitly confirms the data is good
