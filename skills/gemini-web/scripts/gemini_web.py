#!/usr/bin/env python3
"""Call your own logged-in Gemini web session from a script: prompt on stdin (or --prompt / --prompt-file), reply or saved paths on stdout.

  gemini_web.py [--mode chat|tasks|research|image|video] [--model MODEL] [--effort low|medium|high] [--keep]
                [--files F ...] [--ref IMG ...] [--aspect W:H] [--confirm-apps-off] [--output FILE] [--output-dir DIR]
                [--prompt TEXT | --prompt-file FILE] [--timeout S] [--browser auto|edge|chrome|...]
                [--cookies-file FILE] [--list-models] [--quota] [--estimate] [--selftest]

The session comes from the Google cookies of a browser where you are logged in to gemini.google.com (browser-cookie3),
or from a private JSON cookie export (--cookies-file / $GEMINI_WEB_COOKIES_FILE / ~/.local/share/gemini-web/cookies.json).
Install the dependencies with: pip install -r requirements.txt
Diagnostics go to stderr, the reply (or saved media paths, one per line) to stdout (or --output / --output-dir).

Exit codes:
  0 reply, saved media paths, --estimate, --quota, or --list-models
  1 empty reply, no generated media after retries, download error, missing quota data, or API error
  2 bad arguments, bad file/prompt-file/cookies-file/reference image, unknown model, missing dependency, or auth failure
  3 canned refusal or media policy refusal that survived two retries
  4 usage limit (hard limit, quota text, 5h window nearly spent, or 5h credits below estimate)
  5 timeout (including video polling)
  6 silent fallback to another model, effort patch not applied, unsupported mode, or model unavailable on this account
  7 refused by a guard (tasks without --confirm-apps-off)
  8 canned error notice ("something went wrong") that survived two retries
Failed text calls cost no credits (measured; unverified for image/video), so retryable failures retry twice after 30 s and
90 s pauses, in a new conversation. One line per call goes to $GEMINI_WEB_LOG (default ~/.local/share/gemini-web/calls.jsonl):
credits of both windows before and after, sizes, the answering model's label, conversation id. Never cookies, prompts or replies.
"""
import argparse, asyncio, contextlib, importlib.util, json, os, random, re, shutil, stat, sys, tempfile, time
from datetime import datetime
from pathlib import Path

LOG = Path(os.environ.get("GEMINI_WEB_LOG") or Path.home() / ".local/share/gemini-web/calls.jsonl")
DEFAULT_LOG_DIR = Path.home() / ".local/share/gemini-web"
# Convenience aliases resolved at runtime via client.resolve_model(); any other name/alias/id from --list-models also works.
MODELS = {"hydrogen": "gemini-4-hydrogen", "neon": "gemini-neon", "carbon": "gemini-carbon"}
LEVEL = {"low": 1, "medium": 4, "high": 2}  # request field 81; the library only knows 1 and 2, medium (4) is patched below
MAX_FILES_BYTES = 300_000  # one measurement: a 1.78 MB text file was truncated near 380 KB without any error, so stay under that
MAX_PROMPT_FILE_BYTES = 300_000  # safety cap for --prompt-file aligned with MAX_FILES_BYTES
MAX_COOKIES_FILE_BYTES = 1_000_000  # 1 MB safety cap for --cookies-file JSON exports
MAX_REF_FILE_BYTES = 10_000_000  # 10 MB per reference image (safety cap; actual server limit is not verified)
MAX_REF_TOTAL_BYTES = 20_000_000  # 20 MB total across --ref images (not verified against server cap)
ALLOWED_REF_EXTS = {".png", ".jpg", ".webp", ".gif"}
ASPECT_RE = re.compile(r"\A(\d{1,2}):(\d{1,2})\Z")
COOKIE_DOMAIN_RE = re.compile(r"\A[a-z0-9.-]+\Z")
QUOTA_WARN_BANDS = (90, 75, 50)
MIN_5H_LEFT_PCT = int(os.environ.get("GEMINI_WEB_MIN_5H_LEFT_PCT", "10"))
RETRY_WAITS = [30, 90]  # seconds before retry 1 and retry 2
# Measured credit ranges from one account on 2026-11-24. Unlisted modes/models (including research) are unmeasured.
ESTIMATED_CREDITS = {
    ("chat", "hydrogen", "low"): (3, 6),
    ("chat", "hydrogen", "medium"): (5, 9),
    ("chat", "hydrogen", "high"): (9, 22),
    # one call each for neon low, images per model, and video (2026-11-24): treat as a rough guide, the real range is unknown
    ("chat", "neon", "low"): (6, 6),
    ("chat", "neon", "medium"): (43, 43),
    ("chat", "neon", "high"): (79, 79),
    ("image", "carbon", "high"): (3, 3),
    ("image", "auto", "high"): (3, 3),
    ("image", "hydrogen", "high"): (30, 30),
    ("image", "neon", "high"): (31, 31),
    ("video", "carbon", "high"): (880, 880),
}
# Mode-level fallback for image/video so the 5h credit guard still protects against high spend when another --model is passed.
MODE_ESTIMATED_CREDITS = {
    "image": (3, 3),
    "video": (880, 880),
}
HTTP_NO_RETRY = re.compile(r"\b(?:400|401|403)\b")
REQUIRED_MODULES = ("curl_cffi", "gemini_webapi", "browser_cookie3")
# The web app sometimes answers a plain request with a canned refusal; it is no answer. (Not reproduced in 23 later calls.)
REFUSAL = re.compile(r"sou (apenas|só|somente) (um|uma)|(não|nao) (consigo|posso|tenho como) (te )?ajudar|as a (large )?language model|"
                     r"I('m| am) (just )?(a )?(text-based|language model)|I can('|no)t help with that", re.I)
MEDIA_REFUSAL = re.compile(
    r"(can('t|not)|unable to|won't|não (posso|consigo)) (generate|create|edit|make|produce|render|gerar|criar|editar) "
    r"(this |that |an? |the )?(image|picture|photo|video|clip|imagem|foto|vídeo)", re.I)
CAPABILITY_UNAVAILABLE = re.compile(
    r"(video generation|image generation|veo|imagen).{0,120}(not available|unavailable|upgrade|eligible|plan|region|country|indisponível|plano)",
    re.I | re.S)
# seen as a normal-looking reply in the screening (Hydrogen, 2026-11-24): the app's own error notice, not an answer
TRANSIENT = re.compile(r"^\W*(sorry, something went wrong|i seem to be encountering an error|i encountered an error doing what you asked|"
                       r"i'm having a hard time fulfilling your request|algo deu errado|ocorreu um erro)", re.I)
QUOTA = re.compile(r"(usage limit|limite de uso|reached (your|the) (daily |hourly )?limit|atingiu o limite|you.ve hit).{0,200}(reset|redefin|renov|horas|hours)", re.I | re.S)
# every candidate frame of the raw StreamGenerate body carries the id and the label of the model that answered, e.g. "4 Hydrogen High"
LABEL = re.compile(rb'\\"[0-9a-f]{16}\\",null,null,\\"([^\\"]{1,40})\\",true')
MODEL_PREFIX = re.compile(r"^gemini-(?:\d+(?:\.\d+)?-)?", re.I)
HDR = "x-goog-ext-525001261-jspb"
PATCH = {"level": None, "applied": False, "raw": []}  # raw: the response bodies of this process, kept in memory only


def labels_in(body: bytes) -> list:
    return [m.decode("utf8", "replace") for m in LABEL.findall(body)]


def model_label_token(model: str) -> str:
    """Normalizes a model argument (e.g. 'gemini-carbon' or 'carbon') to the name token expected inside a response label."""
    t = MODEL_PREFIX.sub("", model.strip().lower()).replace("_", "-")
    for name in LABEL_VERIFIED:  # 'gemini-4-hydrogen' and 'hydrogen' are the same model
        if name in t:
            return name
    return t


LABEL_VERIFIED = ("hydrogen", "neon")  # the only models whose response label was ever seen; any other model is not checked
# Verified labels (2026-11-24): hydrogen low "4 Hydrogen", medium "4 Hydrogen Medium", high "4 Hydrogen High";
# neon low "4 Neon", medium "4 Neon Medium" (neon high has not been verified yet, so neon is checked by model name only).
EFFORT_LABEL = {"low": re.compile(r"^\s*4 Hydrogen\s*$", re.I), "medium": re.compile(r"\bmedium\b", re.I), "high": re.compile(r"\bhigh\b", re.I)}


def label_verdict(label, model: str, effort: str = "high", check_effort: bool = True):
    """(ok, note). A label naming another model, or for hydrogen chat another effort, than the requested one is a silent fallback;
    a missing label is undetectable."""
    if not label:
        return True, "no model label in the response: a silent fallback cannot be detected for this call"
    tok = model_label_token(model)
    if tok not in LABEL_VERIFIED:
        return True, f"label '{label}' not checked: no verified label exists for model '{model}'"
    if tok not in label.lower():
        return False, f"answered by '{label}' but '{model}' was requested"
    if check_effort and tok == "hydrogen" and not EFFORT_LABEL[effort].search(label):
        return False, f"answered by '{label}' but effort '{effort}' was requested"
    return True, ""

def check_files(paths):
    """Only regular, non-empty files: an empty file makes the whole request fail (HTTP 400), links and folders could leak the repository."""
    total, out = 0, []
    for p in paths:
        pp = Path(p)
        if pp.is_symlink() or not pp.is_file() or pp.resolve() != Path(os.path.abspath(pp)):
            raise ValueError(f"{p}: not a regular file, or a link on the way to it (links and folders are refused)")
        n = pp.stat().st_size
        if n == 0:
            raise ValueError(f"{p}: empty file (the API answers HTTP 400 and the call fails)")
        total += n; out.append(str(pp))
    if total > MAX_FILES_BYTES:
        raise ValueError(f"attachments total {total} bytes, over the {MAX_FILES_BYTES} limit (larger files are silently truncated)")
    return out
def detect_image_ext(data: bytes) -> str | None:
    """Returns the canonical extension from real image magic bytes, or None if unrecognized."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12] in (b"avif", b"avis"):
        return ".avif"
    return None


def detect_video_ext(data: bytes) -> str | None:
    """Returns the canonical extension from real video container magic bytes, or None if unrecognized."""
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand == b"qt  ":
            return ".mov"
        if brand in (b"isom", b"iso2", b"iso5", b"iso6", b"mp41", b"mp42", b"avc1", b"M4V ", b"MSNV", b"dash"):
            return ".mp4"
        return None  # avif, heic, M4A and other ISO-BMFF payloads are not videos
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return ".webm"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"AVI ":
        return ".avi"
    return None


def check_ref_images(paths, max_count: int | None = None):
    """Validates --ref files: regular non-empty files (no symlinks), within size cap, and real image magic bytes."""
    if max_count is not None and len(paths) > max_count:
        raise ValueError(f"too many --ref images ({len(paths)}): at most {max_count} allowed for this mode")
    total, out = 0, []
    for p in paths:
        pp = Path(p)
        if pp.is_symlink() or not pp.is_file() or pp.resolve() != Path(os.path.abspath(pp)):
            raise ValueError(f"{p}: not a regular file, or a link on the way to it (links and folders are refused)")
        n = pp.stat().st_size
        if n == 0:
            raise ValueError(f"{p}: empty file (the API answers HTTP 400 and the call fails)")
        if n > MAX_REF_FILE_BYTES:
            raise ValueError(f"{p}: {n} bytes exceeds the {MAX_REF_FILE_BYTES} byte per-image limit")
        with pp.open("rb") as f:
            head = f.read(16)
        ext = detect_image_ext(head)
        if ext not in ALLOWED_REF_EXTS:
            raise ValueError(f"{p}: unsupported or unrecognized image format (expected PNG, JPEG, WebP or GIF)")
        total += n
        out.append(str(pp))
    if total > MAX_REF_TOTAL_BYTES:
        raise ValueError(f"reference images total {total} bytes, over the {MAX_REF_TOTAL_BYTES} limit")
    return out


def _reject_symlink_prefix(path_str: str) -> tuple[Path, Path]:
    """Walks every raw path component before lexical '..' collapse and rejects any symlink along the path.

    Returns (raw_path, canonical_abs_path) after confirming Path.resolve() == os.path.abspath().
    """
    raw = Path(path_str)
    abs_p = Path(os.path.abspath(raw))
    # Walk raw components before '..' is collapsed so 'symlink/../target' cannot bypass validation.
    cur = Path(raw.anchor) if raw.is_absolute() else Path.cwd()
    if cur.is_symlink() or cur.resolve() != Path(os.path.abspath(cur)):
        raise ValueError(f"{path_str}: {cur} is a symlink")
    for part in raw.parts[1:] if raw.is_absolute() else raw.parts:
        if part in ("", "."):
            continue
        cur = cur / part
        if part != ".." and cur.is_symlink():
            raise ValueError(f"{path_str}: {cur} is a symlink")
    if raw.resolve() != abs_p:
        raise ValueError(f"{path_str}: path traverses a symlink (links are refused)")
    return raw, abs_p


def check_output_file(path_str: str) -> Path:
    """Validates --output before spending credits: writable regular parent, no symlinks along the path, not a directory."""
    p, abs_p = _reject_symlink_prefix(path_str)
    if p.exists():
        if p.is_dir() or not p.is_file():
            raise ValueError(f"{path_str}: exists and is not a regular file")
    parent = abs_p.parent
    if not (parent.is_dir() and parent.resolve() == parent and os.access(parent, os.W_OK | os.X_OK)):
        raise ValueError(f"cannot write {path_str}: {parent} is not a writable regular folder")
    return abs_p


def check_output_dir(path_str: str) -> Path:
    """Validates --output-dir without creating it yet: no symlinks in path, not a regular file, writable ancestor."""
    p, abs_p = _reject_symlink_prefix(path_str)
    if p.exists():
        if not p.is_dir():
            raise ValueError(f"{path_str}: exists and is not a regular directory")
        if not os.access(p, os.W_OK | os.X_OK):
            raise ValueError(f"{path_str}: directory is not writable")
        return abs_p
    cur = abs_p.parent
    while not cur.exists() and cur != cur.parent:
        cur = cur.parent
    if cur.resolve() != cur or not (cur.is_dir() and os.access(cur, os.W_OK | os.X_OK)):
        raise ValueError(f"{path_str}: parent {cur} is not a writable regular directory")
    return abs_p


def check_cwd_writable(base: Path | None = None) -> Path:
    """Checks that the default output parent folder is writable without creating any subfolder yet."""
    root = base if base is not None else Path.cwd()
    if not (root.is_dir() and os.access(root, os.W_OK | os.X_OK)):
        raise ValueError(f"cannot create the output folder: {root} is not writable (pass --output-dir)")
    return root


def reserve_default_output_dir(mode: str, now: datetime | None = None, base: Path | None = None) -> Path:
    """Creates, atomically and with mode 700, a fresh folder gemini-<mode>-<time> in base (default cwd); two runs never share one."""
    ts = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    root = check_cwd_writable(base)
    for i in range(0, 100):
        cand = root / (f"gemini-{mode}-{ts}" if i == 0 else f"gemini-{mode}-{ts}-{i:02d}")
        try:
            cand.mkdir(mode=0o700)
            return cand
        except FileExistsError:
            continue
    raise ValueError("cannot reserve a free output folder name")


def _place_exclusive(src: Path, dest: Path) -> bool:
    """Moves src to dest without overwriting an existing file. Returns False if dest already exists.

    Tries os.link first; on filesystems without hard links, reserves dest atomically with O_CREAT|O_EXCL
    and copies bytes directly into the reserved descriptor before unlinking src.
    """
    try:
        os.link(src, dest)
        src.unlink()
        return True
    except FileExistsError:
        return False
    except OSError:
        pass
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(dest, flags, 0o600)
    except FileExistsError:
        return False
    try:
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, "wb") as dst_f, src.open("rb") as src_f:
            shutil.copyfileobj(src_f, dst_f)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    src.unlink()
    return True


def place_unique(src: Path, out_dir: Path, kind: str, ext: str, start: int = 1) -> Path:
    """Moves src to the first free <kind>_NN<ext> in out_dir without overwriting, even across concurrent runs."""
    idx = max(1, start)
    while True:
        dest = out_dir / media_filename(kind, idx, ext)
        if _place_exclusive(src, dest):
            return dest
        idx += 1


def media_filename(kind: str, index: int, ext: str) -> str:
    """Predictable output filename that never leaks prompt text."""
    return f"{kind}_{index:02d}{ext}"


def lookup_estimate(mode: str, model: str, effort: str) -> tuple[tuple[int, int] | None, bool]:
    """Returns ((lo, hi) | None, is_mode_fallback) for credit estimation and the 5h quota guard."""
    tok = model_label_token(model)
    eff_key = effort if mode == "chat" else "high"
    est = ESTIMATED_CREDITS.get((mode, tok, eff_key))
    if est is not None:
        return est, False
    mode_est = MODE_ESTIMATED_CREDITS.get(mode)
    if mode_est is not None:
        return mode_est, True
    return None, False


def format_estimate(mode: str, model: str, effort: str) -> str:
    """Formats the known credit estimate without making any network calls."""
    tok, eff = model_label_token(model), (effort if mode == "chat" else "n/a")
    est, fallback = lookup_estimate(mode, model, effort)
    if est is None:
        return (f"mode={mode} model={tok} effort={eff}: estimated credits=unmeasured "
                "(no measured data for this combination; 5h window guard still applies)")
    lo, hi = est
    span = f"{lo}" if lo == hi else f"{lo}-{hi}"
    if fallback:
        return (f"mode={mode} model={tok} effort={eff}: estimated credits={span} "
                "(mode baseline measured with carbon on one account, 2026-11-24)")
    return f"mode={mode} model={tok} effort={eff}: estimated credits={span} (measured on one account, 2026-11-24)"


def default_model_for_mode(mode: str) -> str:
    """Returns the default model alias for a mode: carbon for image/video, hydrogen for text modes."""
    return "carbon" if mode in ("image", "video") else "hydrogen"


def validate_aspect(value: str) -> str:
    """Validates an aspect ratio string W:H (1-2 digits each, both positive). Returns normalized 'W:H' or raises ValueError."""
    if not isinstance(value, str):
        raise ValueError("invalid --aspect: expected W:H (e.g. 16:9, 4:5, 1:1)")
    m = ASPECT_RE.match(value)
    if not m:
        raise ValueError(f"invalid --aspect '{value}': expected W:H with 1-2 positive digits each (e.g. 16:9, 4:5, 1:1)")
    w, h = int(m.group(1)), int(m.group(2))
    if w <= 0 or h <= 0:
        raise ValueError(f"invalid --aspect '{value}': width and height must both be positive")
    return f"{w}:{h}"


def _open_regular_nofollow(abs_p: Path) -> int:
    """Opens an absolute path without following symlinks at any directory or leaf component (uses openat/dir_fd on POSIX)."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if hasattr(os, "O_DIRECTORY") and os.open in getattr(os, "supports_dir_fd", set()) and abs_p.is_absolute():
        parts = abs_p.parts
        if len(parts) < 2:
            raise OSError("not a regular file")
        dir_fd = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in parts[1:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | nofollow, dir_fd=dir_fd)
                os.close(dir_fd)
                dir_fd = next_fd
            return os.open(parts[-1], os.O_RDONLY | nofollow, dir_fd=dir_fd)
        finally:
            os.close(dir_fd)
    return os.open(abs_p, os.O_RDONLY | nofollow)


def read_prompt_file(path_str: str) -> str:
    """Reads --prompt-file safely: no symlinks along any path component, regular non-empty UTF-8 file within MAX_PROMPT_FILE_BYTES."""
    if not isinstance(path_str, str) or not path_str.strip():
        raise ValueError("--prompt-file must not be empty")
    p, abs_p = _reject_symlink_prefix(path_str)
    if not p.exists():
        raise ValueError(f"{path_str}: prompt file does not exist")
    if p.is_symlink() or not p.is_file():
        raise ValueError(f"{path_str}: not a regular file (links and folders are refused)")
    try:
        fd = _open_regular_nofollow(abs_p)
    except OSError as e:
        raise ValueError(f"{path_str}: cannot open prompt file ({e.strerror or e})") from e
    try:
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise ValueError(f"{path_str}: not a regular file")
            if st.st_size == 0:
                raise ValueError(f"{path_str}: prompt file is empty")
            if st.st_size > MAX_PROMPT_FILE_BYTES:
                raise ValueError(f"{path_str}: prompt file is {st.st_size} bytes, over the {MAX_PROMPT_FILE_BYTES} limit")
            with os.fdopen(fd, "rb") as f:
                fd = -1
                raw = f.read(MAX_PROMPT_FILE_BYTES + 1)
        except OSError as e:
            raise ValueError(f"{path_str}: cannot read prompt file ({e.strerror or e})") from e
    finally:
        if fd >= 0:
            os.close(fd)
    if len(raw) == 0:
        raise ValueError(f"{path_str}: prompt file is empty")
    if len(raw) > MAX_PROMPT_FILE_BYTES:
        raise ValueError(f"{path_str}: prompt file exceeds the {MAX_PROMPT_FILE_BYTES} byte limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"{path_str}: prompt file is not valid UTF-8 ({e})") from e
    if not text.lstrip("\ufeff").strip():
        raise ValueError(f"{path_str}: prompt file contains only whitespace")
    return text


def check_not_same_file(path_a: Path, path_b_str: str, label_a: str, label_b: str) -> None:
    """Refuses when path_a resolves to the same file (or hard link) as path_b_str."""
    _, b_abs = _reject_symlink_prefix(path_b_str)
    if path_a == b_abs:
        raise ValueError(f"{label_a} ({path_a}) must not be the same file as {label_b}")
    try:
        if path_a.exists() and b_abs.exists() and os.path.samefile(path_a, b_abs):
            raise ValueError(f"{label_a} ({path_a}) refers to the same file as {label_b}")
    except OSError:
        pass


def check_distinct_output_and_prompt(out_file: Path, prompt_file_path: str) -> None:
    """Refuses --output when it resolves to the same file (or hard link) as --prompt-file to prevent O_TRUNC data loss."""
    check_not_same_file(out_file, prompt_file_path, "--output", "--prompt-file")


def is_structured_json(text: str) -> bool:
    """Returns True if text parses as a JSON object or array (tolerates leading UTF-8 BOM and excessive nesting)."""
    s = text.lstrip("\ufeff").strip()
    if not s or s[0] not in ("{", "["):
        return False
    try:
        val = json.loads(s)
    except (ValueError, RecursionError):
        return False
    return isinstance(val, (dict, list))


def prepare_prompt(prompt: str, mode: str, aspect: str | None = None) -> str:
    """Applies --aspect and structured-JSON media framing for image/video modes; leaves text modes unchanged."""
    if mode not in ("image", "video"):
        return prompt
    clean = prompt.lstrip("\ufeff").strip()
    if is_structured_json(clean):
        aspect_clause = f" in a {aspect} aspect ratio" if aspect else ""
        return (
            f"Generate the {mode} described by the following JSON specification{aspect_clause}. "
            f"Return the generated {mode} directly rather than a text reply.\n\n{clean}"
        )
    if aspect:
        return f"{prompt.rstrip()}\n\nTarget aspect ratio: {aspect}."
    return prompt


def validate_args(args) -> tuple[int, str]:
    """Pure argument validator. Returns (0, '') when valid or (exit_code, error_message)."""
    if args.timeout <= 0:
        return 2, "--timeout must be a positive integer"
    if args.mode == "tasks":
        if not args.confirm_apps_off:
            return 7, "tasks mode can act on connected apps and the browser; pass --confirm-apps-off only after checking they are off"
        return 6, "tasks mode is not implemented: the request field for Tasks was never captured (see references/limits.md)"
    if args.model is not None and not str(args.model).strip():
        return 2, "--model must not be empty"
    cookies_file = getattr(args, "cookies_file", None)
    if cookies_file is not None and not str(cookies_file).strip():
        return 2, "--cookies-file must not be empty"
    prompt_val = getattr(args, "prompt", None)
    prompt_file = getattr(args, "prompt_file", None)
    if prompt_val is not None and prompt_file is not None:
        return 2, "pass either --prompt or --prompt-file, not both"
    if prompt_file is not None and not str(prompt_file).strip():
        return 2, "--prompt-file must not be empty"
    aspect = getattr(args, "aspect", None)
    if aspect is not None:
        if args.mode not in ("image", "video"):
            return 2, "--aspect is only supported in image and video modes"
        try:
            validate_aspect(aspect)
        except ValueError as e:
            return 2, str(e)
    if args.mode == "chat":
        if args.ref:
            return 2, "chat mode uses --files, not --ref"
        if args.output_dir:
            return 2, "--output-dir is only for image and video modes; use --output for chat"
    if args.mode == "research":
        if args.files or args.ref or args.output_dir or args.effort not in (None, "high"):
            return 2, "research takes no --files, --ref, --output-dir, or --effort; leave them out"
    if args.mode in ("image", "video"):
        if args.files:
            return 2, f"{args.mode} mode uses --ref for reference images, not --files"
        if args.output:
            return 2, f"{args.mode} mode writes files into --output-dir, not --output"
        if args.effort is not None:
            return 2, f"{args.mode} mode does not accept --effort"
        if args.mode == "video" and len(args.ref) > 1:
            return 2, "video mode accepts at most one --ref image"
    return 0, ""


class PatchNotApplied(Exception):
    pass


class _Tap:  # keeps the raw body of a StreamGenerate response in memory so the model label can be read
    def __init__(self, cm): self.cm = cm
    async def __aenter__(self):
        r = await self.cm.__aenter__(); it = r.aiter_content; buf = []
        async def tap(*a, **k):
            async for chunk in it(*a, **k):
                buf.append(chunk if isinstance(chunk, bytes) else chunk.encode()); yield chunk
        r.aiter_content = tap; self.buf = buf; return r
    async def __aexit__(self, *e):
        PATCH["raw"].append(b"".join(self.buf))
        return await self.cm.__aexit__(*e)


def patch_request(data, hdr, lv):
    """Sets thinking level lv in field 81 and in the model header of a StreamGenerate request. Returns (data, headers, applied)."""
    if not isinstance(data, dict) or "f.req" not in data: return data, hdr, False
    try:
        outer = json.loads(data["f.req"]); inner = json.loads(outer[1])
        key = next((k for k in hdr if k.lower() == HDR), None)
        h = json.loads(hdr[key]) if key else None
        if len(inner) <= 80 or not h or len(h) < 2: return data, hdr, False  # request shape changed: do not guess
        inner[80] = lv; h[-2] = lv; outer[1] = json.dumps(inner)
    except (ValueError, TypeError, IndexError, KeyError):
        return data, hdr, False  # a changed shape must end as exit 6 (patch not applied), never as a generic error
    return {**data, "f.req": json.dumps(outer)}, {**hdr, key: json.dumps(h)}, True


def install():
    from curl_cffi.requests import AsyncSession
    if getattr(AsyncSession, "_gw_patched", False): return
    orig = AsyncSession.stream

    def stream(self, method, url, *a, **kw):
        is_gen = "StreamGenerate" in str(url)
        if is_gen and PATCH["level"]:
            kw["data"], kw["headers"], ok = patch_request(kw.get("data"), kw.get("headers") or {}, PATCH["level"])
            PATCH["applied"] = ok
            if not ok:  # sending it anyway would run, and bill, at another level
                raise PatchNotApplied("the medium-effort patch did not apply (request layout changed): nothing was sent")
        cm = orig(self, method, url, *a, **kw)
        return _Tap(cm) if is_gen else cm

    AsyncSession.stream = stream; AsyncSession._gw_patched = True


def _is_patch_error(exc: BaseException) -> bool:
    cur: BaseException | None = exc
    seen = set()
    while cur is not None and id(cur) not in seen:
        if isinstance(cur, PatchNotApplied):
            return True
        seen.add(id(cur))
        cur = cur.__cause__ or cur.__context__
    return False


def _find_venv_python(script_path: Path | None = None) -> Path | None:
    """Locates an alternative venv Python when the current interpreter lacks runtime dependencies."""
    here = (script_path or Path(__file__)).resolve().parent.parent
    xdg_data = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    rel_bins = (Path("bin/python"), Path("Scripts/python.exe"))
    candidates: list[Path] = []
    if env_py := os.environ.get("GEMINI_WEB_PYTHON"):
        candidates.append(Path(env_py).expanduser())
    for base in (here / ".venv", xdg_data / "gemini-web" / "venv"):
        for rel in rel_bins:
            candidates.append(base / rel)
    current_abs = Path(os.path.abspath(sys.executable))
    uid = os.getuid() if hasattr(os, "getuid") else None
    for cand in candidates:
        try:
            if not (cand.is_file() and os.access(cand, os.X_OK)):
                continue
            if uid is not None and (cand.lstat().st_uid not in (uid, 0) or cand.stat().st_uid not in (uid, 0)):
                continue
            if Path(os.path.abspath(cand)) == current_abs:
                continue
            return cand
        except OSError:
            continue
    return None


def _maybe_reexec_venv(need_browser_cookies: bool = True) -> None:
    """Re-execs into a configured venv when the active Python lacks required runtime modules."""
    if os.environ.get("_GEMINI_WEB_REEXEC") == "1":
        return
    mods = REQUIRED_MODULES if need_browser_cookies else ("curl_cffi", "gemini_webapi")
    if all(importlib.util.find_spec(m) is not None for m in mods):
        return
    venv_py = _find_venv_python()
    if venv_py is None:
        return
    env = {**os.environ, "_GEMINI_WEB_REEXEC": "1"}
    os.execve(str(venv_py), [str(venv_py), *sys.argv], env)


@contextlib.contextmanager
def _isolated_cookie_cache():
    """Redirects gemini-webapi's cookie cache to a private per-run 0700 directory and wipes it on exit.

    Prevents the library from writing __Secure-1PSID in filenames under /tmp/gemini_webapi (0755)
    and prevents stale cached cookies from shadowing fresh browser cookies.
    """
    prev = os.environ.get("GEMINI_COOKIE_PATH")
    with tempfile.TemporaryDirectory(prefix="gw_cookies_") as td:
        os.chmod(td, 0o700)
        os.environ["GEMINI_COOKIE_PATH"] = td
        try:
            yield Path(td)
        finally:
            if prev is None:
                os.environ.pop("GEMINI_COOKIE_PATH", None)
            else:
                os.environ["GEMINI_COOKIE_PATH"] = prev


def log(log_path: Path | None = None, **row):
    target = log_path or LOG
    try:
        existed = target.parent.exists()
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not existed or target.parent.resolve() == DEFAULT_LOG_DIR.resolve():
            try:
                os.chmod(target.parent, 0o700)
            except OSError:
                pass
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(target, flags, 0o600)
        try:
            os.fchmod(fd, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().astimezone().isoformat(timespec="seconds"), **row}) + "\n")
    except OSError:
        pass


def parse_usage_info(ui) -> dict:
    """Normalizes client.usage_info into a stable dict with credits, percentages, reset_at, tier, and AI credits."""
    ui = ui if isinstance(ui, dict) else {}

    def _win(key: str) -> dict:
        w = ui.get(key)
        return w if isinstance(w, dict) else {}

    h5 = _win("current_5h")
    wk = _win("weekly")
    tier_obj = ui.get("tier")
    tier_label = None
    if isinstance(tier_obj, dict):
        tier_label = tier_obj.get("label")
        if not tier_label and tier_obj.get("id") is not None:
            tier_label = f"tier-{tier_obj['id']}"
    elif isinstance(tier_obj, str) and tier_obj.strip():
        tier_label = tier_obj.strip()
    ai_credits = ui.get("ai_credits_remaining")
    if isinstance(ai_credits, bool) or not isinstance(ai_credits, (int, float)):
        ai_credits = None
    h5_reset = h5.get("reset_at")
    wk_reset = wk.get("reset_at")
    return {
        "h5": [h5.get("remaining_credits"), h5.get("usage_percentage")],
        "wk": [wk.get("remaining_credits"), wk.get("usage_percentage")],
        "h5_reset": h5_reset.strip() if isinstance(h5_reset, str) and h5_reset.strip() else None,
        "wk_reset": wk_reset.strip() if isinstance(wk_reset, str) and wk_reset.strip() else None,
        "tier": tier_label,
        "ai_credits": ai_credits,
    }


def has_usage_data(u: dict | None) -> bool:
    """Returns True when at least one window metric or ai_credits value is populated."""
    if not isinstance(u, dict):
        return False
    h5 = u.get("h5") or [None, None]
    wk = u.get("wk") or [None, None]
    return any(v is not None for v in (h5[0], h5[1], wk[0], wk[1], u.get("ai_credits")))


def _format_reset_time(reset_at: str | None) -> str:
    """Formats an ISO-8601 reset timestamp concisely (to minutes), or returns '' when unavailable."""
    if not isinstance(reset_at, str) or not reset_at.strip():
        return ""
    raw = reset_at.strip()
    try:
        return datetime.fromisoformat(raw).isoformat(timespec="minutes")
    except ValueError:
        return raw


def format_reset_hint(u: dict | None, window: str = "h5") -> str:
    """Returns ' (resets ...)' for one window or both windows when available, else ''."""
    if not isinstance(u, dict):
        return ""
    if window == "both":
        parts: list[str] = []
        for label, rkey in (("5h", "h5_reset"), ("weekly", "wk_reset")):
            rst = _format_reset_time(u.get(rkey))
            if rst:
                parts.append(f"{label} resets {rst}")
        return f" ({'; '.join(parts)})" if parts else ""
    rkey = "h5_reset" if window == "h5" else "wk_reset"
    rst = _format_reset_time(u.get(rkey))
    return f" (resets {rst})" if rst else ""


def format_quota(u: dict) -> str:
    """Formats normalized usage data for stable stdout output from --quota."""
    lines: list[str] = []
    if u.get("tier"):
        lines.append(f"tier: {u['tier']}")
    for label, key, rkey in (("5h", "h5", "h5_reset"), ("weekly", "wk", "wk_reset")):
        rem, pct = u.get(key) or [None, None]
        parts = [
            f"{rem} credits left" if rem is not None else "credits=n/a",
            f"{pct}% used" if pct is not None else "used=n/a",
        ]
        rst = _format_reset_time(u.get(rkey))
        if rst:
            parts.append(f"resets {rst}")
        lines.append(f"{label}: {', '.join(parts)}")
    if u.get("ai_credits") is not None:
        lines.append(f"ai_credits: {u['ai_credits']} left")
    return "\n".join(lines)


def _quota_band(pct) -> int | None:
    if isinstance(pct, bool) or not isinstance(pct, (int, float)):
        return None
    return next((b for b in QUOTA_WARN_BANDS if pct >= b), None)


def quota_bands(u: dict | None) -> dict[str, int]:
    """Returns {window_label: highest_crossed_band} for deduplicating pre- and post-call warnings."""
    if not isinstance(u, dict):
        return {}
    out: dict[str, int] = {}
    for label, key in (("5h", "h5"), ("weekly", "wk")):
        _, pct = u.get(key) or [None, None]
        band = _quota_band(pct)
        if band is not None:
            out[label] = band
    return out


def quota_warnings(u: dict | None, windows: tuple[str, ...] = ("5h", "weekly"), min_band_by_window: dict[str, int] | None = None) -> list[str]:
    """Returns deterministic stderr warning lines when 5h or weekly usage reaches >=50%, >=75%, or >=90%.

    When min_band_by_window is provided, emits a window only if its band strictly exceeds the previous band.
    """
    if not isinstance(u, dict):
        return []
    specs = (("5h", "h5", "h5_reset"), ("weekly", "wk", "wk_reset"))
    warns: list[str] = []
    for label, key, rkey in specs:
        if label not in windows:
            continue
        rem, pct = u.get(key) or [None, None]
        band = _quota_band(pct)
        if band is None:
            continue
        if min_band_by_window is not None and band <= min_band_by_window.get(label, 0):
            continue
        sev = {90: "critical", 75: "high", 50: "notice"}[band]
        rem_s = f", {rem} credits left" if rem is not None else ""
        rst = _format_reset_time(u.get(rkey))
        rst_s = f", resets {rst}" if rst else ""
        warns.append(f"quota {sev} (>={band}%): {label} window at {pct}%{rem_s}{rst_s}")
    return warns


def format_skip_5h(u: dict, limit_pct: int) -> str:
    return f"5h window at {u['h5'][1]}% (limit {limit_pct}%){format_reset_hint(u, 'h5')}: not calling"


def format_skip_5h_est(u: dict, est: tuple[int, int]) -> str:
    return f"5h window has {u['h5'][0]} credits left, below estimated {est[0]}-{est[1]}{format_reset_hint(u, 'h5')}: not calling"


def format_limit_detail(detail: str, u: dict | None) -> str:
    return f"{detail}{format_reset_hint(u, 'both')}"


def _merge_window(w0, w1) -> list:
    a = w0 if isinstance(w0, (list, tuple)) and len(w0) == 2 else [None, None]
    b = w1 if isinstance(w1, (list, tuple)) and len(w1) == 2 else [None, None]
    return [b[0] if b[0] is not None else a[0], b[1] if b[1] is not None else a[1]]


def merge_usage(u0: dict, u1: dict) -> dict:
    """Uses post-call u1 fields when non-None, falling back per field to pre-call u0 when u1 is empty or partial."""
    if has_usage_data(u1):
        return {
            "h5": _merge_window(u0.get("h5"), u1.get("h5")),
            "wk": _merge_window(u0.get("wk"), u1.get("wk")),
            "h5_reset": u1.get("h5_reset") or u0.get("h5_reset"),
            "wk_reset": u1.get("wk_reset") or u0.get("wk_reset"),
            "tier": u1.get("tier") or u0.get("tier"),
            "ai_credits": u1.get("ai_credits") if u1.get("ai_credits") is not None else u0.get("ai_credits"),
        }
    return u0


async def usage(c):
    for f in ("_fetch_quota", "_fetch_usage_info"):
        try: await getattr(c, f)()
        except Exception: pass
    return parse_usage_info(getattr(c, "usage_info", None))


BROWSERS = ["edge", "chrome", "chromium", "brave", "firefox", "vivaldi", "opera", "librewolf"]


def default_cookies_file() -> Path:
    """Default private cookies.json path used as fallback when browser cookie extraction fails."""
    xdg_data = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data) / "gemini-web" if xdg_data else DEFAULT_LOG_DIR
    return base / "cookies.json"


def _is_google_cookie_domain(domain: str) -> bool:
    """Returns True only for google.com and subdomains (*.google.com); rejects lookalikes, whitespace/control chars, and unrelated domains."""
    if not isinstance(domain, str) or any(ch in domain for ch in "\r\n\x00\t "):
        return False
    raw = domain.lower()
    if not raw or ".." in raw:
        return False
    host = raw[1:] if raw.startswith(".") else raw
    if not host or host.startswith(".") or host.endswith(".") or not COOKIE_DOMAIN_RE.match(host):
        return False
    return host == "google.com" or host.endswith(".google.com")


def _covers_gemini_root(domain: str, path: str) -> bool:
    """Returns True only when a cookie's domain and path are sent on requests to https://gemini.google.com/."""
    if not _is_google_cookie_domain(domain):
        return False
    host = domain.lower().lstrip(".")
    clean_path = path if isinstance(path, str) and path else "/"
    return host in ("google.com", "gemini.google.com") and clean_path == "/"


def select_session_cookies(cookies) -> tuple[str | None, str | None]:
    """Selects non-empty (__Secure-1PSID, __Secure-1PSIDTS) from cookies covering https://gemini.google.com/.

    Prefers .google.com over gemini.google.com when both exist.
    """
    best: dict[str, tuple[int, str]] = {}
    for ck in cookies:
        name = getattr(ck, "name", None)
        if name not in ("__Secure-1PSID", "__Secure-1PSIDTS"):
            continue
        val = getattr(ck, "value", None)
        if not isinstance(val, str) or not val.strip():
            continue
        dom = getattr(ck, "domain", ".google.com") or ".google.com"
        path = getattr(ck, "path", "/") or "/"
        if not _covers_gemini_root(dom, path):
            continue
        prio = 2 if dom.lower().lstrip(".") == "google.com" else 1
        prev = best.get(name)
        if prev is None or prio >= prev[0]:
            best[name] = (prio, val)
    return (best["__Secure-1PSID"][1] if "__Secure-1PSID" in best else None,
            best["__Secure-1PSIDTS"][1] if "__Secure-1PSIDTS" in best else None)


def _make_cookie_obj(name: str, value: str, domain: str = ".google.com", path: str = "/"):
    if not isinstance(name, str) or not name.strip() or any(ch in name for ch in "\r\n\x00\t"):
        raise ValueError("cookies file contains an invalid cookie name")
    if not isinstance(value, str) or any(ch in value for ch in "\r\n\x00"):
        raise ValueError("cookies file contains an invalid cookie value")
    clean_path = path if (isinstance(path, str) and path.startswith("/") and not any(ch in path for ch in "\r\n\x00")) else "/"
    return argparse.Namespace(name=name.strip(), value=value, domain=domain.strip().lower(), path=clean_path)


def _parse_cookies_payload(data) -> list:
    """Parses JSON cookie exports (browser list, {'cookies': [...]}, or flat {name: value} dict) filtered to google.com."""
    if isinstance(data, dict) and isinstance(data.get("cookies"), list):
        items = data["cookies"]
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        cookies = []
        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise ValueError("flat cookies JSON object must map cookie names to string values")
            cookies.append(_make_cookie_obj(k, v, ".google.com", "/"))
        if not select_session_cookies(cookies)[0]:
            raise ValueError("cookies file contains no non-empty __Secure-1PSID cookie covering gemini.google.com/")
        return cookies
    else:
        raise ValueError("cookies file must be a JSON array of cookie objects or a JSON object")

    cookies = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("cookies file array must contain JSON objects")
        domain = item.get("domain", ".google.com")
        if not isinstance(domain, str) or not _is_google_cookie_domain(domain):
            continue  # drop non-Google cookies from multi-site browser exports without leaking them
        name = item.get("name")
        value = item.get("value")
        path = item.get("path", "/")
        cookies.append(_make_cookie_obj(name, value, domain, path))
    if not select_session_cookies(cookies)[0]:
        raise ValueError("cookies file contains no non-empty __Secure-1PSID cookie covering gemini.google.com/")
    return cookies


def load_cookies_file(path_str: str) -> list:
    """Loads Google cookies from a private JSON file (no symlinks, mode 0600 on POSIX, <=1 MB, valid UTF-8 JSON)."""
    if not isinstance(path_str, str) or not path_str.strip():
        raise ValueError("--cookies-file must not be empty")
    p, abs_p = _reject_symlink_prefix(path_str)
    if not p.exists():
        raise ValueError(f"{path_str}: cookies file does not exist")
    if p.is_symlink() or not p.is_file():
        raise ValueError(f"{path_str}: not a regular file (links and folders are refused)")
    try:
        fd = _open_regular_nofollow(abs_p)
    except OSError as e:
        raise ValueError(f"{path_str}: cannot open cookies file ({e.strerror or e})") from e
    try:
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise ValueError(f"{path_str}: not a regular file")
            if os.name == "posix":
                if st.st_uid != os.getuid():
                    raise ValueError(f"{path_str}: cookies file must be owned by the current user")
                if (st.st_mode & 0o077) != 0:
                    raise ValueError(f"{path_str}: cookies file permissions are too open (run: chmod 600)")
            if st.st_size == 0:
                raise ValueError(f"{path_str}: cookies file is empty")
            if st.st_size > MAX_COOKIES_FILE_BYTES:
                raise ValueError(f"{path_str}: cookies file is {st.st_size} bytes, over the {MAX_COOKIES_FILE_BYTES} limit")
            with os.fdopen(fd, "rb") as f:
                fd = -1
                raw = f.read(MAX_COOKIES_FILE_BYTES + 1)
        except OSError as e:
            raise ValueError(f"{path_str}: cannot read cookies file ({e.strerror or e})") from e
    finally:
        if fd >= 0:
            os.close(fd)
    if len(raw) == 0:
        raise ValueError(f"{path_str}: cookies file is empty")
    if len(raw) > MAX_COOKIES_FILE_BYTES:
        raise ValueError(f"{path_str}: cookies file exceeds the {MAX_COOKIES_FILE_BYTES} byte limit")
    try:
        text = raw.decode("utf-8").lstrip("\ufeff")
    except UnicodeDecodeError:
        raise ValueError(f"{path_str}: cookies file is not valid UTF-8") from None
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        raise ValueError(f"{path_str}: cookies file is not valid JSON") from None
    return _parse_cookies_payload(data)


def load_cookies(browser="auto", cookies_file=None):
    """Reads Google cookies from --cookies-file, a logged-in browser (browser-cookie3), or default cookies.json fallback.

    Returns (source label, cookie list); cookie values are never printed.
    """
    if cookies_file is not None:
        return "cookies-file", load_cookies_file(cookies_file)
    try:
        import browser_cookie3 as bc
    except ImportError:
        bc = None
    if bc is not None:
        for name in (BROWSERS if browser == "auto" else [browser]):
            try:
                jar = list(getattr(bc, name)(domain_name="google.com"))
            except Exception:  # profile not found, keyring locked, browser not installed
                continue
            if select_session_cookies(jar)[0]:
                return name, jar
    if browser == "auto":
        fallback = default_cookies_file()
        if fallback.exists() or fallback.is_symlink():
            return "cookies-file", load_cookies_file(str(fallback))
    if bc is None:
        raise ImportError("browser_cookie3")
    raise RuntimeError(
        "no browser with a logged-in Google session found "
        "(log in to gemini.google.com there, pass --browser, or pass --cookies-file)"
    )


async def _init_client_from_cookies(used: str, cookies, timeout: int):
    from curl_cffi.requests import Cookies
    from gemini_webapi import GeminiClient, set_log_level
    import gemini_webapi.exceptions as gex
    from gemini_webapi.constants import AccountStatus
    set_log_level("CRITICAL")
    psid, psidts = select_session_cookies(cookies)
    if not psid:
        raise gex.AuthError(f"the {used} session has no valid __Secure-1PSID cookie covering gemini.google.com/")
    c = GeminiClient(psid, psidts)
    jar = Cookies()  # the two session cookies alone make init() time out (measured); the whole Google jar works
    for ck in cookies:
        jar.set(ck.name, ck.value, domain=ck.domain, path=ck.path or "/", secure=True)
    # Apply full jar via the public setter, then pin the chosen session cookies onto .google.com/ so init() always sends them.
    c.cookies = jar
    c._cookies.set("__Secure-1PSID", psid, domain=".google.com", path="/", secure=True)
    if psidts:
        c._cookies.set("__Secure-1PSIDTS", psidts, domain=".google.com", path="/", secure=True)
    t = max(90, timeout)  # client request timeout for subsequent generate calls; slower calls raise gemini_webapi.exceptions.TimeoutError
    init_wait = min(90, max(15, timeout))
    try:
        await asyncio.wait_for(c.init(timeout=t, auto_refresh=False), init_wait)
    except BaseException:
        await _close_client(c)
        raise
    if c.account_status != AccountStatus.AVAILABLE or not c.access_token:  # expired cookies fall back to a guest session that init() accepts
        await _close_client(c)
        hint = "refresh your cookies.json export" if used == "cookies-file" else "log in again in that browser"
        raise gex.AuthError(f"the {used} session is not logged in to Gemini ({c.account_status.name}); {hint}")
    print(f"gemini_web: session from {used}", file=sys.stderr)
    return c, gex


async def make_client(browser="auto", timeout=90, cookies_file=None):
    used, cookies = load_cookies(browser, cookies_file=cookies_file)
    try:
        return await _init_client_from_cookies(used, cookies, timeout)
    except Exception as e:
        # If an auto-discovered browser held an expired session and a default cookies.json exists, try that once.
        if used != "cookies-file" and cookies_file is None and browser == "auto":
            fallback = default_cookies_file()
            if fallback.exists() or fallback.is_symlink():
                try:
                    import gemini_webapi.exceptions as gex
                    is_auth = isinstance(e, gex.AuthError)
                except ImportError:
                    is_auth = type(e).__name__ == "AuthError"
                if is_auth:
                    print(f"gemini_web: {used} session is not logged in, falling back to default cookies.json", file=sys.stderr)
                    fb_cookies = load_cookies_file(str(fallback))
                    return await _init_client_from_cookies("cookies-file", fb_cookies, timeout)
        raise


async def _close_client(c) -> None:
    if c is None:
        return
    try:
        await c.close()
    except Exception:
        pass


def resolve_account_model(c, model_arg: str):
    """Resolves --model against client.list_models(). Returns (AvailableModel|None, exit_code, error_msg)."""
    target = MODELS.get(model_arg, model_arg)
    models = c.list_models() or []
    listing = ", ".join(f"{m.model_name} ({m.display_name})" for m in models) or "none"
    try:
        resolved = c.resolve_model(target)
    except ValueError:
        if model_arg in MODELS:
            return None, 6, f"model '{model_arg}' ({target}) is not listed on this account; available models: {listing}"
        return None, 2, f"unknown model '{model_arg}'; available models: {listing}"
    if not resolved.is_available:
        return None, 6, f"model '{resolved.model_name}' is not available on this session; available models: {listing}"
    return resolved, 0, ""


async def save_generated_image(img, out_dir: Path, index: int, http_client, deadline: float) -> Path:
    """Downloads a GeneratedImage into a private folder, verifies its magic bytes, and places it at a free predictable name."""
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp_dir = Path(tempfile.mkdtemp(prefix=".dl_", dir=out_dir))  # mode 700 and an unpredictable name: no planted link, no partial file left behind
    try:
        return await _save_image_in(img, out_dir, tmp_dir, index, http_client, deadline)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def _save_image_in(img, out_dir: Path, tmp_dir: Path, index: int, http_client, deadline: float) -> Path:
    tmp_name = "download.tmp"
    saved_path: Path | None = None
    last_err: Exception | None = None
    for dl_try in range(2):
        rem = deadline - time.time()
        if rem <= 0:
            raise asyncio.TimeoutError("timed out while downloading image")
        try:
            saved_str = await asyncio.wait_for(
                img.save(path=str(tmp_dir), filename=tmp_name, client=http_client, full_size=True),
                timeout=rem,
            )
            saved_path = Path(saved_str)
            break
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            last_err = e
            if dl_try == 0 and (deadline - time.time()) > 5:
                await asyncio.sleep(3)
                continue
            raise
    if saved_path is None or not saved_path.is_file():
        raise RuntimeError(f"image download produced no file ({last_err})")
    try:
        if saved_path.stat().st_size == 0:
            raise ValueError("downloaded image is empty")
        with saved_path.open("rb") as f:
            head = f.read(16)
        ext = detect_image_ext(head)
        if ext is None:
            raise ValueError("downloaded bytes are not a recognized image format")
        os.chmod(saved_path, 0o600)
        dest = place_unique(saved_path, out_dir, "image", ext, start=index)
        return dest.resolve()
    except Exception:
        saved_path.unlink(missing_ok=True)
        raise


async def save_generated_video(vid, out_dir: Path, index: int, http_client, deadline: float) -> tuple[Path, Path | None]:
    """Polls and downloads a GeneratedVideo into a private folder within deadline, verifies magic bytes, places it at a free name."""
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp_dir = Path(tempfile.mkdtemp(prefix=".dl_", dir=out_dir))
    try:
        return await _save_video_in(vid, out_dir, tmp_dir, index, http_client, deadline)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def _save_video_in(vid, out_dir: Path, tmp_dir: Path, index: int, http_client, deadline: float) -> tuple[Path, Path | None]:
    tmp_name = "download.tmp"
    rem = deadline - time.time()
    if rem <= 0:
        raise asyncio.TimeoutError("timed out before video download")
    result = await asyncio.wait_for(
        vid.save(path=str(tmp_dir), filename=tmp_name, client=http_client),
        timeout=rem,
    )
    vid_raw = Path(result["video"]) if isinstance(result, dict) and result.get("video") else None
    thumb_raw = Path(result["video_thumbnail"]) if isinstance(result, dict) and result.get("video_thumbnail") else None
    if vid_raw is None or not vid_raw.is_file():
        if thumb_raw:
            thumb_raw.unlink(missing_ok=True)
        raise RuntimeError("video download produced no file")
    try:
        if vid_raw.stat().st_size == 0:
            raise ValueError("downloaded video is empty")
        with vid_raw.open("rb") as f:
            head = f.read(16)
        ext = detect_video_ext(head)
        if ext is None:
            raise ValueError("downloaded bytes are not a recognized video format")
        os.chmod(vid_raw, 0o600)
        dest = place_unique(vid_raw, out_dir, "video", ext, start=index)
    except Exception:
        vid_raw.unlink(missing_ok=True)
        if thumb_raw:
            thumb_raw.unlink(missing_ok=True)
        raise
    thumb_dest: Path | None = None
    if thumb_raw and thumb_raw.is_file():
        try:
            with thumb_raw.open("rb") as f:
                thead = f.read(16)
            text_ext = detect_image_ext(thead)
            if text_ext:
                os.chmod(thumb_raw, 0o600)
                thumb_dest = dest.with_name(f"{dest.stem}_thumb{text_ext}")
                try:
                    if _place_exclusive(thumb_raw, thumb_dest):
                        thumb_dest = thumb_dest.resolve()
                    else:
                        thumb_dest = None
                except OSError:
                    thumb_dest = None
            else:
                thumb_raw.unlink(missing_ok=True)
        except OSError:
            thumb_raw.unlink(missing_ok=True)
    return dest.resolve(), thumb_dest


def _classify_no_media(text: str, kind: str) -> tuple[str, str]:
    """Classifies a text-only response received in image or video mode."""
    if len(text) < 400 and QUOTA.search(text):
        return "limit", text
    if len(text) < 200 and TRANSIENT.search(text):
        return "transient", text
    if len(text) < 500 and CAPABILITY_UNAVAILABLE.search(text):
        return "unsupported", text
    if len(text) < 400 and (REFUSAL.search(text) or MEDIA_REFUSAL.search(text)):
        return "refused", text
    return "no_media", text[:300] or f"model returned no generated {kind}"


def _prepare_media_out_dir(mode: str, requested_dir: Path | None) -> tuple[Path, list[Path]]:
    """Creates or reserves the media output folder only once media is ready to save.

    Returns (path, created_dirs_leaf_to_root) so failed runs can remove all newly created empty folders.
    """
    if requested_dir is not None:
        missing: list[Path] = []
        cur = requested_dir
        while not cur.exists() and cur != cur.parent:
            missing.append(cur)
            cur = cur.parent
        requested_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        for d in missing:
            try:
                os.chmod(d, 0o700)
            except OSError:
                pass
        return requested_dir, missing
    created = reserve_default_output_dir(mode)
    return created, [created]


def _cleanup_empty_dirs(created_dirs: list[Path]) -> None:
    for path in created_dirs:
        try:
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
            else:
                break
        except OSError:
            break


def _response_videos(r, cand) -> list:
    vids = getattr(cand, "generated_videos", None) if cand is not None else None
    if vids:
        return list(vids)
    try:
        return list(getattr(r, "videos", None) or [])
    except IndexError:
        return []


async def one_call(c, gex, args, prompt, files, resolved_model, out_dir: Path | None = None):
    """One generate call. Returns a dict with status, text, saved paths, detail, err_kind, thoughts, cid, label, note, u0, u1, dur."""
    PATCH["raw"].clear(); PATCH["applied"] = False
    PATCH["level"] = LEVEL["medium"] if (args.mode == "chat" and args.effort == "medium") else None
    u0 = await usage(c); t0 = time.time(); deadline = t0 + args.timeout
    status, text, cid, note, detail, err_kind, thoughts = "ok", "", None, "", "", None, 0
    saved: list[str] = []
    thumbs: list[str] = []
    created_dirs: list[Path] = []
    try:
        if args.mode == "research":
            res = await asyncio.wait_for(c.deep_research(prompt, model=resolved_model, timeout=args.timeout), args.timeout + 60)
            text = (res.text or "").strip()
            if not res.done:
                status, text = "timeout", ""
            out = res.final_output or res.start_output
            cid = ((getattr(out, "metadata", None) or [None])[0]) if out else None
        elif args.mode == "image":
            r = await asyncio.wait_for(
                c.generate_content(prompt, files=files or None, model=resolved_model, temporary=not args.keep, extended_thinking=False),
                max(1.0, deadline - time.time()),
            )
            text = (r.text or "").strip(); cid = (r.metadata or [None])[0]; thoughts = len(r.thoughts or "")
            cand = r.candidates[r.chosen] if getattr(r, "candidates", None) else None
            gen_imgs = list(getattr(cand, "generated_images", None) or [])
            if not gen_imgs:
                gen_vids = _response_videos(r, cand)
                if gen_vids:
                    status = "no_media"
                    note = "response contained video instead of image; re-run with --mode video"
                    detail = text[:300] or note
                else:
                    status, detail = _classify_no_media(text, "image")
                    if status == "transient":
                        text = ""
            else:
                actual_out_dir, created_dirs = _prepare_media_out_dir(args.mode, out_dir)
                for idx, img in enumerate(gen_imgs, start=1):
                    try:
                        p = await save_generated_image(img, actual_out_dir, idx, c.client, deadline)
                        saved.append(str(p))
                    except asyncio.TimeoutError:
                        status, err_kind = "timeout", "TimeoutError"
                        break
                    except Exception as e:
                        status, err_kind, detail = "download_error", type(e).__name__, f"{type(e).__name__}: {str(e)[:300]}"
                        break
                if status != "ok" and saved:
                    note = f"partial download: {len(saved)} file(s) already saved ({', '.join(saved)}) before failure"
                elif not saved:
                    _cleanup_empty_dirs(created_dirs)
        elif args.mode == "video":
            # Video generation relies on read_chat(cid) recovery when pending (client.py:1562, 1893-1999),
            # so temporary=False is required here.
            r = await asyncio.wait_for(
                c.generate_content(prompt, files=files or None, model=resolved_model, temporary=False, extended_thinking=False),
                max(1.0, deadline - time.time()),
            )
            text = (r.text or "").strip(); cid = (r.metadata or [None])[0]; thoughts = len(r.thoughts or "")
            cand = r.candidates[r.chosen] if getattr(r, "candidates", None) else None
            gen_vids = _response_videos(r, cand)
            if not gen_vids:
                gen_imgs = list(getattr(cand, "generated_images", None) or [])
                if gen_imgs:
                    status = "no_media"
                    note = "response contained image instead of video; re-run with --mode image"
                    detail = text[:300] or note
                else:
                    status, detail = _classify_no_media(text, "video")
                    if status == "transient":
                        text = ""
            else:
                actual_out_dir, created_dirs = _prepare_media_out_dir(args.mode, out_dir)
                for idx, vid in enumerate(gen_vids, start=1):
                    try:
                        vp, tp = await save_generated_video(vid, actual_out_dir, idx, c.client, deadline)
                        saved.append(str(vp))
                        if tp:
                            thumbs.append(str(tp))
                    except asyncio.TimeoutError:
                        status, err_kind = "timeout", "TimeoutError"
                        break
                    except Exception as e:
                        status, err_kind, detail = "download_error", type(e).__name__, f"{type(e).__name__}: {str(e)[:300]}"
                        break
                if status != "ok" and saved:
                    note = f"partial download: {len(saved)} file(s) already saved ({', '.join(saved)}) before failure"
                    if thumbs:
                        note += f"; thumbnail(s): {', '.join(thumbs)}"
                elif not saved:
                    _cleanup_empty_dirs(created_dirs)
        else:
            r = await asyncio.wait_for(
                c.generate_content(prompt, files=files or None, model=resolved_model, temporary=not args.keep,
                                   extended_thinking=args.effort != "low"),
                args.timeout,
            )
            text = (r.text or "").strip(); cid = (r.metadata or [None])[0]; thoughts = len(r.thoughts or "")
    except (asyncio.TimeoutError, gex.TimeoutError):
        status, err_kind = "timeout", "TimeoutError"
    except gex.UsageLimitExceededError as e:
        status, err_kind, detail = "limit", type(e).__name__, str(e)
    except PatchNotApplied as e:
        status, err_kind, note = "patch", "PatchNotApplied", str(e)
    except gex.AuthError as e:
        status, err_kind, detail = "auth", type(e).__name__, str(e)[:300]
    except Exception as e:
        if _is_patch_error(e):
            status, err_kind, note = "patch", "PatchNotApplied", str(e)[:300]
        else:
            status, err_kind, detail = "error", type(e).__name__, f"{type(e).__name__}: {str(e)[:300]}"
            if re.search(r"\b(401|403)\b|cookies? (have )?expired", detail, re.I):
                status = "auth"

    label = next((l for b in reversed(PATCH["raw"]) for l in reversed(labels_in(b))), None)
    if status == "ok" and args.effort == "medium" and args.mode == "chat" and not PATCH["applied"]:
        status, note = "patch", "the medium-effort patch did not apply (request shape changed): the call ran at another level"
    if status == "ok" and args.mode in ("chat", "research"):  # quota notice comes first: it can also say "something went wrong"
        if len(text) < 400 and QUOTA.search(text): status = "limit"
        elif len(text) < 200 and TRANSIENT.search(text): status, detail, text = "transient", text, ""
        elif len(text) < 300 and REFUSAL.search(text): status = "refused"
        elif not text: status = "empty"
    u1 = await usage(c)
    if status == "ok" and args.mode == "chat" and len(text) < 250 and None not in (u0["h5"][0], u1["h5"][0]) and u0["h5"][0] == u1["h5"][0]:
        note = "short reply that cost no credits: may be an error notice the patterns do not know"
    if status == "ok" and args.mode == "chat":  # image and video answer under labels nobody has seen: never fail a saved file on one
        ok, why = label_verdict(label, args.model, args.effort)
        if not ok:
            status, note = "fallback", why
        elif why:
            note = why
    return dict(status=status, text=text, saved=saved, thumbs=thumbs, detail=detail, err_kind=err_kind, thoughts=thoughts,
                cid=cid, label=label, note=note, u0=u0, u1=u1, dur=round(time.time() - t0, 1))


async def run_list_models(args):
    with _isolated_cookie_cache():
        c = None
        try:
            try:
                c, _ = await make_client(args.browser, args.timeout, cookies_file=getattr(args, "cookies_file", None))
            except ImportError as e:
                print(f"gemini_web: missing dependency ({e}); run: pip install -r requirements.txt", file=sys.stderr); return 2
            except Exception as e:
                print(f"gemini_web: authentication failed ({type(e).__name__}: {e})", file=sys.stderr); return 2
            models = c.list_models() or []
            if not models:
                print("gemini_web: account returned no models", file=sys.stderr); return 1
            for m in models:
                state = "available" if m.is_available else "unavailable"
                desc = f" | {m.description}" if m.description else ""
                print(f"{m.model_name}\t{m.display_name}\t{m.model_id}\t{state}{desc}")
            return 0
        finally:
            await _close_client(c)


async def run_quota(args):
    with _isolated_cookie_cache():
        c = None
        try:
            try:
                c, _ = await make_client(args.browser, args.timeout, cookies_file=getattr(args, "cookies_file", None))
            except ImportError as e:
                print(f"gemini_web: missing dependency ({e}); run: pip install -r requirements.txt", file=sys.stderr); return 2
            except Exception as e:
                print(f"gemini_web: authentication failed ({type(e).__name__}: {e})", file=sys.stderr); return 2
            u = await usage(c)
            if not has_usage_data(u):
                print("gemini_web: account returned no quota data", file=sys.stderr); return 1
            print(format_quota(u))
            for w in quota_warnings(u):
                print(f"gemini_web: {w}", file=sys.stderr)
            return 0
        finally:
            await _close_client(c)


def _safe_file_bytes(files: list[str]) -> int:
    total = 0
    for f in files:
        try:
            total += Path(f).stat().st_size
        except OSError:
            pass
    return total


async def run(args, prompt, files, out_dir: Path | None = None, out_file: Path | None = None):
    file_bytes = _safe_file_bytes(files)
    with _isolated_cookie_cache():
        c = None
        try:
            try:
                c, gex = await make_client(args.browser, args.timeout, cookies_file=getattr(args, "cookies_file", None))
            except ImportError as e:
                print(f"gemini_web: missing dependency ({e}); run: pip install -r requirements.txt", file=sys.stderr); return 2
            except Exception as e:
                print(f"gemini_web: authentication failed ({type(e).__name__}: {e})", file=sys.stderr); return 2
            install()
            resolved_model, mcode, merr = resolve_account_model(c, args.model)
            if mcode:
                print(f"gemini_web: {merr}", file=sys.stderr)
                log(mode=args.mode, model=args.model, effort=args.effort, status="model-unavailable")
                return mcode
            u = await usage(c)
            if u["h5"][1] is not None and u["h5"][1] >= 100 - MIN_5H_LEFT_PCT:
                print(f"gemini_web: {format_skip_5h(u, 100 - MIN_5H_LEFT_PCT)}", file=sys.stderr)
                for w in quota_warnings(u, windows=("weekly",)):
                    print(f"gemini_web: {w}", file=sys.stderr)
                log(mode=args.mode, model=args.model, effort=args.effort, status="skipped-5h", h5=u["h5"], wk=u["wk"]); return 4
            est, _ = lookup_estimate(args.mode, args.model, args.effort)
            if est and u["h5"][0] is not None and u["h5"][0] < est[1]:
                print(f"gemini_web: {format_skip_5h_est(u, est)}", file=sys.stderr)
                for w in quota_warnings(u):
                    print(f"gemini_web: {w}", file=sys.stderr)
                log(mode=args.mode, model=args.model, effort=args.effort, status="skipped-5h-est", h5=u["h5"], wk=u["wk"]); return 4
            for w in quota_warnings(u):
                print(f"gemini_web: {w}", file=sys.stderr)
            pre_bands = quota_bands(u)
            if args.mode == "video" and not args.keep:
                print("gemini_web: video mode saves the conversation in web history (required for polling)", file=sys.stderr)
            for attempt, wait in enumerate(RETRY_WAITS + [None], start=1):
                r = await one_call(c, gex, args, prompt, files, resolved_model, out_dir=out_dir)
                status, text, label, note, u0, u1, dur = r["status"], r["text"], r["label"], r["note"], r["u0"], r["u1"], r["dur"]
                is_media = args.mode in ("image", "video")
                log(mode=args.mode, model=args.model, resolved_model=resolved_model.model_name, effort=args.effort,
                    temporary=(False if args.mode in ("research", "video") else not args.keep),
                    attempt=attempt, status=status, err_kind=r["err_kind"], dur=dur, prompt_chars=len(prompt),
                    answer_chars=len(text), thought_chars=r["thoughts"], saved_files=len(r["saved"]),
                    files=0 if is_media else len(files), ref_files=len(files) if is_media else 0,
                    file_bytes=file_bytes, label=label, cid=r["cid"],
                    h5=[u0["h5"][0], u1["h5"][0]], pct5=u1["h5"][1], wk=[u0["wk"][0], u1["wk"][0]],
                    retry_wait_s=wait if retryable(status, r["detail"]) and wait is not None else None)
                if not retryable(status, r["detail"]) or wait is None:
                    break
                print(f"gemini_web: {status} on attempt {attempt}, retrying in a new conversation after {wait} s", file=sys.stderr)
                await asyncio.sleep(wait + random.uniform(0, 5))
            u_post = merge_usage(merge_usage(u, u0), u1)
            if status == "timeout" and args.mode == "research" and r.get("cid"):
                print(f"gemini_web: the research did not finish in time; conversation {r['cid']} is kept in the web history, look there later "
                      "(in the one test run it was still unfinished after 26 minutes)", file=sys.stderr)
            if note:
                print(f"gemini_web: {note}", file=sys.stderr)
            if label:
                print(f"gemini_web: answered by '{label}', {dur}s, 5h credits {u0['h5'][0]}->{u1['h5'][0]}", file=sys.stderr)
            for w in quota_warnings(u_post, min_band_by_window=pre_bands):
                print(f"gemini_web: {w}", file=sys.stderr)
            if status == "ok":
                if args.mode in ("image", "video"):
                    for p in r["saved"]:
                        print(p)
                    if r["thumbs"]:
                        print(f"gemini_web: thumbnail(s): {', '.join(r['thumbs'])}", file=sys.stderr)
                    return 0
                if out_file is not None:
                    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
                    fd = os.open(out_file, flags, 0o600); os.fchmod(fd, 0o600)
                    with os.fdopen(fd, "w", encoding="utf-8") as f: f.write(text + "\n")
                    print(f"gemini_web: reply written to {out_file}", file=sys.stderr)
                else:
                    print(text)
                return 0
            msg_detail = (r["detail"] or text)[:300] or note or "no detail"
            if status == "limit":
                msg_detail = format_limit_detail(msg_detail, u_post)
            print(f"gemini_web: {status}: {msg_detail}", file=sys.stderr)
            return EXIT.get(status, 1)
        finally:
            await _close_client(c)


EXIT = {"limit": 4, "timeout": 5, "fallback": 6, "patch": 6, "unsupported": 6, "refused": 3, "transient": 8, "auth": 2}


def retryable(status, detail=""):
    """Retryable statuses; never retries limit, timeout, fallback, patch, unsupported, no_media, download_error, auth, or HTTP 400/401/403."""
    return status in ("transient", "refused", "empty") or (
        status == "error" and not HTTP_NO_RETRY.search(detail)
    )

def selftest():
    ok = 0
    def check(cond, what):
        nonlocal ok
        assert cond, f"selftest failed: {what}"; ok += 1
    body = b'x,null,null,\\"56fdd199312815e2\\",null,null,\\"4 Hydrogen High\\",true,[[1004'
    check(labels_in(body) == ["4 Hydrogen High"], "label regex finds the model label")
    check(labels_in(b"nothing here") == [], "label regex on a body without label")
    check(label_verdict("4 Hydrogen High", "hydrogen", "high")[0], "matching label is fine")
    check(not label_verdict("3 Flash-Lite", "hydrogen")[0], "other model label is a fallback")
    check(label_verdict("4 Hydrogen", "hydrogen", "low")[0] and label_verdict("4 Hydrogen Medium", "hydrogen", "medium")[0], "verified hydrogen labels match their effort")
    check(not label_verdict("4 Hydrogen", "hydrogen", "high")[0] and not label_verdict("4 Hydrogen High", "hydrogen", "low")[0], "effort mismatch is a fallback")
    check(label_verdict("4 Neon", "neon", "medium")[0], "neon is checked by name only")
    check(label_verdict(None, "neon")[0] and label_verdict(None, "neon")[1], "missing label passes with a note")
    check(REFUSAL.search("Sou apenas uma IA e não consigo ajudar com isso."), "refusal regex")
    check(not REFUSAL.search("1. rows.py:4 changes the signature"), "refusal regex ignores a review")
    for m in ("Sorry, something went wrong. Please try your request again.", "I seem to be encountering an error. Can I try something else for you?",
              "I encountered an error doing what you asked. Could you try again?", "I'm having a hard time fulfilling your request. Can I help you with something else instead?"):
        check(TRANSIENT.search(m), f"transient error notice: {m[:30]}")
    check(not TRANSIENT.search("1. rows.py:4 `except` hides the error the caller needs to retry"), "transient regex ignores a review")
    check(not TRANSIENT.search("I encountered an error in the caller at rows.py:4; retry on 503."), "transient regex ignores a short real finding")
    check(not QUOTA.search("The rate limit resets in 3 hours."), "quota regex ignores a plain sentence about a rate limit")
    check(retryable("transient") and retryable("refused") and retryable("empty") and retryable("error", "APIError: boom"), "retryable statuses")
    check(retryable("error", "timeout after 4000 ms on port 8401"), "word-boundary HTTP check allows 4000/8401")
    check(not any(retryable(x) for x in ("limit", "timeout", "fallback", "patch", "auth")) and not retryable("error", "Status: 400") and not retryable("error", "HTTP 401") and not retryable("error", "Status: 403"), "never retried: limit, timeout, fallback, patch, auth, 400, 401, 403")
    check([EXIT[x] for x in ("limit", "timeout", "fallback", "patch", "refused", "transient", "auth")] == [4, 5, 6, 6, 3, 8, 2], "exit code map")
    check(QUOTA.search("Você atingiu o limite de uso. Ele será redefinido em 3 horas."), "quota text in Portuguese")
    d = {"f.req": json.dumps([None, json.dumps([0] * 90)])}
    nd, nh, applied = patch_request(d, {"X-Goog-Ext-525001261-Jspb": json.dumps([1, 2, 9, "sid"])}, 4)
    check(applied and json.loads(json.loads(nd["f.req"])[1])[80] == 4 and json.loads(list(nh.values())[0])[-2] == 4, "level patch sets field 81 and header")
    check(not patch_request(d, {}, 4)[2], "patch refuses when the header is missing")
    check(not patch_request({"f.req": json.dumps([None, json.dumps([0] * 5)])}, {HDR: "[1,2,3]"}, 4)[2], "patch refuses a short request")
    check(_is_patch_error(PatchNotApplied("x")) and not _is_patch_error(RuntimeError("HTTP 401")), "patch error detector does not swallow generic/auth errors")
    wrapped = RuntimeError("wrap"); wrapped.__cause__ = PatchNotApplied("inner")
    check(_is_patch_error(wrapped), "patch error detector unwraps chained PatchNotApplied")
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        t = Path(tmp1); base = Path(tmp2)
        (t / "a.txt").write_text("x"); (t / "e.txt").write_text(""); (t / "big.txt").write_bytes(b"x" * (MAX_FILES_BYTES + 1))
        (t / "l.txt").symlink_to(t / "a.txt"); (t / "real").mkdir(); (t / "real" / "n.txt").write_text("n"); (t / "viapai").symlink_to(t / "real")
        check(check_files([t / "a.txt"]) == [str(t / "a.txt")], "regular file accepted")
        for bad, what in ((t / "e.txt", "empty"), (t / "l.txt", "symlink"), (t, "folder"), (t / "big.txt", "too big"), (t / "viapai" / "n.txt", "symlinked parent folder")):
            try: check_files([bad]); check(False, f"{what} refused")
            except ValueError: ok += 1
        # Media helpers: magic bytes, predictable naming, ref validation, output-dir and output-file validation, arg validation
        check(detect_image_ext(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR") == ".png", "PNG magic bytes")
        check(detect_image_ext(b"\xff\xd8\xff\xe0\x00\x10JFIF") == ".jpg", "JPEG magic bytes")
        check(detect_image_ext(b"RIFF\x12\x00\x00\x00WEBP") == ".webp", "WebP magic bytes")
        check(detect_image_ext(b"GIF89a\x01\x00\x01\x00") == ".gif", "GIF magic bytes")
        check(detect_image_ext(b"\x00\x00\x00\x1cftypavif") == ".avif", "AVIF magic bytes")
        check(detect_image_ext(b"<html>not an image</html>") is None and detect_image_ext(b"") is None, "non-image bytes rejected")
        check(detect_video_ext(b"\x00\x00\x00\x18ftypisom") == ".mp4", "MP4 magic bytes")
        check(detect_video_ext(b"\x00\x00\x00\x14ftypqt  ") == ".mov", "MOV magic bytes")
        check(detect_video_ext(b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81") == ".webm", "WebM magic bytes")
        check(detect_video_ext(b"\x89PNG\r\n\x1a\n") is None, "PNG is not video")

        check(media_filename("image", 1, ".png") == "image_01.png", "predictable image filename")
        check(media_filename("video", 12, ".mp4") == "video_12.mp4", "predictable video filename")
        out_t = t / "out_media"; out_t.mkdir()
        fixed_dt = datetime(2026, 11, 24, 19, 0, 5)
        d1 = reserve_default_output_dir("image", now=fixed_dt, base=base); d2 = reserve_default_output_dir("image", now=fixed_dt, base=base)
        check(d1 == base / "gemini-image-20261124-190005" and d2 == base / "gemini-image-20261124-190005-01" and (d1.stat().st_mode & 0o777) == 0o700,
              "default output folders are reserved atomically, mode 700, collision-free")
        _cleanup_empty_dirs([d2])
        check(not d2.exists(), "empty newly-created output dir is cleaned up on failure")
        nested_dir, nested_created = _prepare_media_out_dir("image", base / "nest_a" / "nest_b" / "leaf")
        check(nested_dir.is_dir() and len(nested_created) == 3, "nested output dir tracks all newly created ancestors")
        _cleanup_empty_dirs(nested_created)
        check(not (base / "nest_a").exists(), "nested empty output dirs are all removed on failure")

        (t / "ok.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        (t / "ok.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 16)
        (t / "fake.png").write_text("not really a png")
        (t / "link.png").symlink_to(t / "ok.png")
        check(check_ref_images([t / "ok.png", t / "ok.jpg"]) == [str(t / "ok.png"), str(t / "ok.jpg")], "valid ref images accepted")
        for bad_refs, max_c, what in (
            ([t / "fake.png"], None, "fake png bytes"),
            ([t / "e.txt"], None, "empty ref"),
            ([t / "link.png"], None, "symlink ref"),
            ([t], None, "dir ref"),
            ([t / "ok.png", t / "ok.jpg"], 1, "video ref count cap"),
        ):
            try: check_ref_images(bad_refs, max_count=max_c); check(False, f"{what} refused")
            except ValueError: ok += 1

        check(check_output_dir(str(out_t)) == out_t.resolve(), "existing writable output dir accepted")
        check(check_output_dir(str(t / "new_dir")) == (t / "new_dir").resolve(), "new output dir under writable parent accepted")
        for bad_dir, what in ((t / "a.txt", "regular file as output dir"), (t / "viapai", "symlink as output dir")):
            try: check_output_dir(str(bad_dir)); check(False, f"{what} refused")
            except ValueError: ok += 1

        check(check_output_file(str(t / "reply.txt")) == (t / "reply.txt").resolve(), "new output file accepted")
        check(check_output_file(str(t / "a.txt")) == (t / "a.txt").resolve(), "existing regular output file accepted")
        for bad_out, what in (
            (out_t, "directory as output file"),
            (t / "l.txt", "symlink as output file"),
            (t / "viapai" / "out.txt", "symlinked parent for output file"),
            (t / "viapai" / ".." / "escaped.txt", "symlink + .. bypass for output file"),
            (t / "missing_dir" / "out.txt", "missing parent for output file"),
        ):
            try: check_output_file(str(bad_out)); check(False, f"{what} refused")
            except ValueError: ok += 1
        try: check_output_dir(str(t / "viapai" / ".." / "out_dir")); check(False, "symlink + .. bypass for output dir refused")
        except ValueError: ok += 1

        check(model_label_token("gemini-carbon") == "carbon" and model_label_token("gemini-4-hydrogen") == "hydrogen", "model token normalization")
        check(label_verdict("Carbon", "gemini-carbon", check_effort=False)[0], "carbon label check without effort")
        check(label_verdict("Imagen 4", "carbon", check_effort=False)[0] and label_verdict("Veo 3", "hydrogen", check_effort=False)[0] is False,
              "carbon is never checked; hydrogen with a foreign label is still a fallback")
        check(label_verdict("4 Hydrogen High", "gemini-4-hydrogen", "high")[0] and model_label_token("gemini-4-hydrogen") == "hydrogen", "full model name is the same model")
        check("9-22" in format_estimate("chat", "hydrogen", "high") and "credits=6" in format_estimate("chat", "neon", "low")
              and "credits=880" in format_estimate("video", "carbon", "high")
              and "credits=880" in format_estimate("video", "hydrogen", "high")
              and "credits=30" in format_estimate("image", "hydrogen", "high")
              and "credits=31" in format_estimate("image", "neon", "high")
              and "credits=3" in format_estimate("image", "gemini-auto", "high")
              and "mode baseline" in format_estimate("image", "custom-model", "high"),
              "estimate output covers neon low, measured per-model images, and mode-level video/image fallback")
        check(lookup_estimate("video", "hydrogen", "high") == ((880, 880), True), "video quota guard fallback applies to unmeasured model")
        check(default_model_for_mode("chat") == "hydrogen" and default_model_for_mode("research") == "hydrogen"
              and default_model_for_mode("image") == "carbon" and default_model_for_mode("video") == "carbon",
              "default model resolves to carbon for image/video and hydrogen for chat/research")
        check(MEDIA_REFUSAL.search("I cannot generate this image due to policy."), "media refusal regex")
        check(CAPABILITY_UNAVAILABLE.search("Video generation is not available on your current plan."), "capability unavailable regex")
        check(not retryable("no_media") and not retryable("unsupported") and not retryable("download_error") and EXIT["unsupported"] == 6, "media retry/exit rules")
        check(detect_video_ext(b"\x00\x00\x00\x1cftypisom0000") == ".mp4" and detect_video_ext(b"\x00\x00\x00\x1cftypqt  0000") == ".mov"
              and detect_video_ext(b"\x00\x00\x00\x1cftypavif0000") is None and detect_video_ext(b"\x00\x00\x00\x1cftypM4A 0000") is None, "video brands: avif and audio are not videos")
        check("effort=n/a" in format_estimate("image", "gemini-carbon", "high") and "9-22" in format_estimate("chat", "gemini-4-hydrogen", "high"),
              "estimate: full model names find the row, effort only shown for chat")

        ns = lambda **kw: argparse.Namespace(**{**dict(mode="chat", model=None, effort=None, files=[], ref=[], confirm_apps_off=False,
                                                        output=None, output_dir=None, aspect=None, prompt=None, prompt_file=None, timeout=600), **kw})
        check(validate_args(ns(mode="image", ref=["a.png"], output_dir="out", aspect="16:9"))[0] == 0, "valid image args with aspect")
        check(validate_args(ns(mode="video", ref=["a.png"], aspect="9:16"))[0] == 0, "valid video args with aspect")
        check(validate_args(ns(mode="image", files=["a.txt"]))[0] == 2, "image refuses --files")
        check(validate_args(ns(mode="image", output="x.png"))[0] == 2, "image refuses --output")
        check(validate_args(ns(mode="image", effort="low"))[0] == 2, "image refuses --effort")
        check(validate_args(ns(mode="video", ref=["a.png", "b.png"]))[0] == 2, "video refuses >1 --ref")
        check(validate_args(ns(mode="chat", ref=["a.png"]))[0] == 2, "chat refuses --ref")
        check(validate_args(ns(mode="chat", output_dir="out"))[0] == 2, "chat refuses --output-dir")
        check(validate_args(ns(mode="chat", aspect="16:9"))[0] == 2, "chat refuses --aspect")
        check(validate_args(ns(mode="research", aspect="16:9"))[0] == 2, "research refuses --aspect")
        check(validate_args(ns(mode="chat", model=""))[0] == 2, "empty --model refused")
        check(validate_args(ns(mode="chat", prompt="hi", prompt_file="p.txt"))[0] == 2, "--prompt and --prompt-file mutually exclusive")
        check(validate_args(ns(mode="chat", prompt="", prompt_file="p.txt"))[0] == 2, "empty --prompt with --prompt-file still refused")
        check(validate_args(ns(mode="chat", prompt_file="   "))[0] == 2, "blank --prompt-file refused")
        check(validate_args(ns(mode="tasks"))[0] == 7 and validate_args(ns(mode="tasks", confirm_apps_off=True))[0] == 6, "tasks guards")
        check(validate_args(ns(timeout=0))[0] == 2, "non-positive timeout refused")

        # --aspect boundary checks
        for good_ar, norm_ar in (("16:9", "16:9"), ("4:5", "4:5"), ("1:1", "1:1"), ("21:9", "21:9"), ("1:99", "1:99"), ("99:1", "99:1"), ("01:09", "1:9")):
            check(validate_aspect(good_ar) == norm_ar, f"valid aspect {good_ar}")
        for bad_ar in ("", "0:9", "9:0", "00:00", "100:50", "16:100", "-16:9", "16/9", "16:9:1", "wide", "16:9\n", " 16:9"):
            check(validate_args(ns(mode="image", aspect=bad_ar))[0] == 2, f"invalid aspect {bad_ar!r} refused")

        # --prompt-file boundary and security checks
        pf_ok = t / "prompt_ok.txt"; pf_ok.write_text("Generate a ceramic bowl", encoding="utf-8")
        pf_max = t / "prompt_max.txt"; pf_max.write_bytes(b"a" * MAX_PROMPT_FILE_BYTES)
        pf_over = t / "prompt_over.txt"; pf_over.write_bytes(b"a" * (MAX_PROMPT_FILE_BYTES + 1))
        pf_ws = t / "prompt_ws.txt"; pf_ws.write_text("  \n\t ", encoding="utf-8")
        pf_bin = t / "prompt_bin.txt"; pf_bin.write_bytes(b"\xff\xfe\xfd")
        pf_link = t / "prompt_link.txt"; pf_link.symlink_to(pf_ok)
        pf_json = t / "scene.json"; pf_json.write_text('{"subject": "ceramic bowl", "lighting": "soft left"}', encoding="utf-8")
        check(read_prompt_file(str(pf_ok)) == "Generate a ceramic bowl", "valid prompt-file accepted")
        check(len(read_prompt_file(str(pf_max))) == MAX_PROMPT_FILE_BYTES, "exact MAX_PROMPT_FILE_BYTES accepted")
        for bad_pf, what in (
            (t / "e.txt", "empty prompt-file"),
            (pf_ws, "whitespace-only prompt-file"),
            (pf_over, "oversized prompt-file"),
            (pf_bin, "invalid UTF-8 prompt-file"),
            (pf_link, "symlink prompt-file"),
            (t / "viapai" / "n.txt", "symlinked parent prompt-file"),
            (t / "viapai" / ".." / "prompt_ok.txt", "symlink + .. bypass prompt-file"),
            (t, "directory prompt-file"),
            (t / "does_not_exist.txt", "missing prompt-file"),
        ):
            try: read_prompt_file(str(bad_pf)); check(False, f"{what} refused")
            except ValueError: ok += 1

        # prepare_prompt: plain text + aspect, structured JSON in media vs chat
        json_txt = read_prompt_file(str(pf_json))
        prep_img_json = prepare_prompt(json_txt, "image")
        prep_img_json_ar = prepare_prompt(json_txt, "image", aspect="16:9")
        prep_vid_ar = prepare_prompt("Generate a short video of rain.", "video", aspect="9:16")
        prep_chat_json = prepare_prompt(json_txt, "chat", aspect="16:9")
        check(prep_img_json.startswith("Generate the image described by the following JSON specification.") and json_txt in prep_img_json,
              "JSON prompt in image mode gets media directive prefix")
        check("16:9 aspect ratio" in prep_img_json_ar and json_txt in prep_img_json_ar, "JSON prompt + --aspect combined cleanly")
        check(prep_vid_ar.startswith("Generate a short video of rain.") and "9:16" in prep_vid_ar, "plain text + --aspect preserves opening verb")
        check(prep_chat_json == json_txt, "chat mode leaves JSON prompt unchanged")
        check(prepare_prompt("{not json", "image") == "{not json" and prepare_prompt("42", "image") == "42",
              "invalid JSON and JSON scalar are not wrapped as structured JSON")
        check(is_structured_json('[{"scene": 1}]') and not is_structured_json('"just a string"'), "structured JSON only matches object/array")
        # DeepSeek review regressions: deep JSON nesting, UTF-8 BOM JSON/empty, openat nofollow, distinct --output/--prompt-file
        check(not is_structured_json("[" * 100000 + "]" * 100000), "deeply nested JSON returns False instead of RecursionError")
        bom_json = '\ufeff{"subject": "mug"}'
        check(is_structured_json(bom_json) and prepare_prompt(bom_json, "image").startswith("Generate the image") and "\ufeff" not in prepare_prompt(bom_json, "image"),
              "UTF-8 BOM JSON is recognized and stripped cleanly")
        pf_bom_empty = t / "bom_empty.txt"; pf_bom_empty.write_text("\ufeff  \n", encoding="utf-8")
        try: read_prompt_file(str(pf_bom_empty)); check(False, "BOM-only prompt-file refused")
        except ValueError: ok += 1
        fd_ok = _open_regular_nofollow(pf_ok.resolve())
        os.close(fd_ok); ok += 1
        try: os.close(_open_regular_nofollow(t / "viapai" / "n.txt")); check(False, "openat rejects symlinked parent")
        except OSError: ok += 1
        try: os.close(_open_regular_nofollow(pf_link)); check(False, "openat rejects leaf symlink")
        except OSError: ok += 1
        try: check_distinct_output_and_prompt(pf_ok.resolve(), str(pf_ok)); check(False, "same --output and --prompt-file refused")
        except ValueError: ok += 1
        pf_hardlink = t / "prompt_hl.txt"
        try:
            os.link(pf_ok, pf_hardlink)
            try: check_distinct_output_and_prompt(pf_hardlink.resolve(), str(pf_ok)); check(False, "hardlink --output to --prompt-file refused")
            except ValueError: ok += 1
        except OSError:
            ok += 1  # filesystems without hard links
        check_distinct_output_and_prompt((t / "distinct_out.txt").resolve(), str(pf_ok)); ok += 1

        (base / "dangling").symlink_to(base / "nowhere")
        try: check_output_dir(str(base / "dangling" / "out")); check(False, "dangling symlink refused")
        except ValueError: ok += 1
        try: read_prompt_file(str(base / "dangling" / "p.txt")); check(False, "dangling symlink prompt-file refused")
        except ValueError: ok += 1
        src1 = base / "a.tmp"; src1.write_bytes(b"1"); src2 = base / "b.tmp"; src2.write_bytes(b"2")
        p1 = place_unique(src1, d1, "image", ".png"); p2 = place_unique(src2, d1, "image", ".png")
        check(p1.name == "image_01.png" and p2.name == "image_02.png" and p1.read_bytes() == b"1" and not src1.exists(), "placement never overwrites")
        # Simulate no-hardlink filesystem in _place_exclusive
        orig_link = os.link
        try:
            def _no_link(_s, _d): raise OSError("hard links unsupported")
            os.link = _no_link
            src3 = base / "c.tmp"; src3.write_bytes(b"3")
            check(not _place_exclusive(src3, p1) and p1.read_bytes() == b"1" and src3.exists(), "O_EXCL fallback refuses overwrite")
            p3 = place_unique(src3, d1, "image", ".png")
            check(p3.name == "image_03.png" and p3.read_bytes() == b"3" and (p3.stat().st_mode & 0o777) == 0o600 and not src3.exists(), "O_EXCL fallback writes atomically with mode 600")
        finally:
            os.link = orig_link
        # Partial multi-image download: first image succeeds, second raises -> status=download_error, saved+note report first file
        class _FakeImg:
            def __init__(self, fail=False): self.fail = fail
            async def save(self, path, filename, client, full_size=True):
                if self.fail: raise ConnectionError("drop")
                fp = Path(path) / filename; fp.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16); return str(fp)
        class _FakeClient:
            usage_info = {}; client = None
            async def _fetch_quota(self): pass
            async def _fetch_usage_info(self): pass
            async def generate_content(self, *a, **k):
                cand = argparse.Namespace(generated_images=[_FakeImg(False), _FakeImg(True)])
                return argparse.Namespace(text="", metadata=["c_partial"], thoughts="", candidates=[cand], chosen=0)
        try:
            from gemini_webapi.exceptions import AuthError as _AuthErrBase
        except ImportError:
            _AuthErrBase = Exception
        class _FakeGex:
            class TimeoutError(Exception): pass
            class UsageLimitExceededError(Exception): pass
            class AuthError(_AuthErrBase): pass
        part_dir = base / "partial_imgs"
        part_res = asyncio.run(one_call(_FakeClient(), _FakeGex, ns(mode="image", model="carbon", keep=False), "draw", [], "gemini-carbon", out_dir=part_dir))
        check(part_res["status"] == "download_error" and len(part_res["saved"]) == 1 and part_res["saved"][0] in part_res["note"],
              "partial multi-image download preserves and reports saved file in note")

        # Cross-mode swapped media detection (image gets video; video gets image; empty falls back to text classification)
        class _SwapToVideoClient(_FakeClient):
            async def generate_content(self, *a, **k):
                cand = argparse.Namespace(generated_images=[], generated_videos=[object()])
                return argparse.Namespace(text="", metadata=["c_swap1"], thoughts="", candidates=[cand], chosen=0, videos=[object()])
        class _SwapToImageClient(_FakeClient):
            async def generate_content(self, *a, **k):
                cand = argparse.Namespace(generated_images=[_FakeImg(False)], generated_videos=[])
                return argparse.Namespace(text="", metadata=["c_swap2"], thoughts="", candidates=[cand], chosen=0, videos=[])
        class _NoMediaRefusalClient(_FakeClient):
            async def generate_content(self, *a, **k):
                cand = argparse.Namespace(generated_images=[], generated_videos=[])
                return argparse.Namespace(text="I cannot generate this image due to policy.", metadata=["c_ref"], thoughts="", candidates=[cand], chosen=0, videos=[])
        swap_dir1 = base / "swap_v"
        swap_r1 = asyncio.run(one_call(_SwapToVideoClient(), _FakeGex, ns(mode="image", model="carbon", keep=False), "draw", [], "gemini-carbon", out_dir=swap_dir1))
        check(swap_r1["status"] == "no_media" and "--mode video" in swap_r1["note"] and not swap_dir1.exists(),
              "image mode receiving video reports swapped-mode hint without creating output dir")
        swap_dir2 = base / "swap_i"
        swap_r2 = asyncio.run(one_call(_SwapToImageClient(), _FakeGex, ns(mode="video", model="carbon", keep=False), "animate", [], "gemini-carbon", out_dir=swap_dir2))
        check(swap_r2["status"] == "no_media" and "--mode image" in swap_r2["note"] and not swap_dir2.exists(),
              "video mode receiving image reports swapped-mode hint without creating output dir")
        ref_r = asyncio.run(one_call(_NoMediaRefusalClient(), _FakeGex, ns(mode="image", model="carbon", keep=False), "draw", [], "gemini-carbon", out_dir=base / "no_m"))
        check(ref_r["status"] == "refused", "empty media without swapped asset still classifies text refusal")

        # Usage parsing, --quota formatting, threshold warnings, and exit 4 reset hints
        sample_ui = {
            "tier": {"id": 2, "label": "PRO"},
            "current_5h": {"remaining_credits": 1452, "usage_percentage": 39, "reset_at": "2026-11-25T00:29:18-03:00"},
            "weekly": {"remaining_credits": 40717, "usage_percentage": 16, "reset_at": "2026-11-25T11:29:18-03:00"},
            "ai_credits_remaining": 120,
        }
        parsed = parse_usage_info(sample_ui)
        check(has_usage_data(parsed) and parsed["tier"] == "PRO" and parsed["h5"] == [1452, 39] and parsed["ai_credits"] == 120
              and parsed["h5_reset"] == "2026-11-25T00:29:18-03:00", "parse_usage_info extracts full fields")
        fq = format_quota(parsed)
        check("tier: PRO" in fq and "5h: 1452 credits left, 39% used, resets 2026-11-25T00:29-03:00" in fq
              and "weekly: 40717 credits left, 16% used, resets 2026-11-25T11:29-03:00" in fq and "ai_credits: 120 left" in fq,
              "format_quota produces stable full output")
        empty_u = parse_usage_info({})
        tier_only_u = parse_usage_info({"tier": {"id": 9, "label": None}})
        check(not has_usage_data(empty_u) and not has_usage_data(tier_only_u) and tier_only_u["tier"] == "tier-9",
              "has_usage_data rejects empty and tier-only usage_info")
        partial_u = parse_usage_info({"current_5h": {"remaining_credits": 50, "usage_percentage": 80, "reset_at": None}})
        fq_part = format_quota(partial_u)
        check("tier:" not in fq_part and "resets" not in fq_part and "ai_credits:" not in fq_part and "5h: 50 credits left, 80% used" in fq_part,
              "format_quota degrades cleanly when tier/reset_at/ai_credits are absent")
        for pct, expected in ((49, None), (50, "notice (>=50%)"), (74, "notice (>=50%)"), (75, "high (>=75%)"), (89, "high (>=75%)"), (90, "critical (>=90%)"), (100, "critical (>=90%)")):
            w_list = quota_warnings({"h5": [100, pct], "wk": [5000, 10], "h5_reset": "2026-11-25T00:29:18-03:00", "wk_reset": None})
            if expected is None:
                check(w_list == [], f"no quota warning at {pct}%")
            else:
                check(len(w_list) == 1 and expected in w_list[0] and "2026-11-25T00:29-03:00" in w_list[0], f"quota warning band {expected} at {pct}%")
        both_w = quota_warnings({"h5": [100, 75], "wk": [200, 92], "h5_reset": None, "wk_reset": "2026-11-30T11:29:00-03:00"})
        check(len(both_w) == 2 and "5h window at 75%" in both_w[0] and "resets" not in both_w[0]
              and "weekly window at 92%" in both_w[1] and "2026-11-30T11:29-03:00" in both_w[1],
              "quota_warnings emits deterministic warnings for both windows and degrades without reset_at")
        check(quota_warnings({"h5": [100, True], "wk": [100, None]}) == [], "quota_warnings ignores non-numeric/bool pct")
        pre_b = quota_bands({"h5": [400, 60], "wk": [5000, 10]})
        check(pre_b == {"5h": 50} and quota_warnings({"h5": [380, 62], "wk": [4980, 10]}, min_band_by_window=pre_b) == [],
              "same-band post-call usage does not emit duplicate warning")
        esc_w = quota_warnings({"h5": [200, 76], "wk": [4000, 50]}, min_band_by_window=pre_b)
        check(len(esc_w) == 2 and "high (>=75%)" in esc_w[0] and "notice (>=50%)" in esc_w[1],
              "escalated or newly crossed post-call bands emit warnings")
        check("resets 2026-11-25T00:29-03:00" in format_skip_5h(parsed, 90) and "resets" not in format_skip_5h(partial_u, 90),
              "skipped-5h includes reset_at when present and degrades cleanly")
        check("resets 2026-11-25T00:29-03:00" in format_skip_5h_est(parsed, (880, 880)) and "resets" not in format_skip_5h_est(partial_u, (880, 880)),
              "skipped-5h-est includes reset_at when present and degrades cleanly")
        lim_msg = format_limit_detail("Usage limit exceeded", parsed)
        check("5h resets 2026-11-25T00:29-03:00" in lim_msg and "weekly resets 2026-11-25T11:29-03:00" in lim_msg
              and format_limit_detail("Usage limit exceeded", partial_u) == "Usage limit exceeded",
              "limit detail appends reset_at for both windows when available")
        merged_u = merge_usage(parsed, empty_u)
        check(merged_u == parsed, "merge_usage falls back to u0 when post-call u1 is empty")
        merged_part = merge_usage(parsed, partial_u)
        check(merged_part["h5"] == [50, 80] and merged_part["h5_reset"] == "2026-11-25T00:29:18-03:00" and merged_part["wk"] == [40717, 16],
              "merge_usage preserves missing reset_at and window metrics from u0")
        u_pre_hi = {"h5": [100, 80], "wk": [1000, 20], "h5_reset": "2026-11-25T00:29:18-03:00", "wk_reset": None, "tier": "PRO", "ai_credits": None}
        u_post_partial = {"h5": [50, None], "wk": [950, None], "h5_reset": None, "wk_reset": None, "tier": None, "ai_credits": None}
        merged_pf = merge_usage(u_pre_hi, u_post_partial)
        check(merged_pf["h5"] == [50, 80] and merged_pf["wk"] == [950, 20] and len(quota_warnings(merged_pf)) == 1,
              "merge_usage falls back per field so partial post-call h5 keeps pre-call percentage for warnings")

        # Direct run_quota entry-point tests: exit 0/1/2, client close, cookies_file forwarding, and isolated cookie cache cleanup
        import io
        orig_make_client = make_client
        q_args = argparse.Namespace(browser="auto", timeout=30, cookies_file=None)
        try:
            class _QuotaFakeClient:
                def __init__(self, ui):
                    self.usage_info = ui
                    self.closed = False
                    self.cookie_dir = os.environ.get("GEMINI_COOKIE_PATH")
                async def _fetch_quota(self): pass
                async def _fetch_usage_info(self): pass
                async def close(self): self.closed = True

            # exit 0 with data + stderr threshold warning + cookies_file forwarded
            fc0 = _QuotaFakeClient({
                "tier": {"id": 2, "label": "PRO"},
                "current_5h": {"remaining_credits": 250, "usage_percentage": 75, "reset_at": "2026-11-25T00:29:18-03:00"},
                "weekly": {"remaining_credits": 20000, "usage_percentage": 20, "reset_at": "2026-11-25T11:29:18-03:00"},
            })
            seen_cf = []
            async def _mk0(browser="auto", timeout=90, cookies_file=None):
                fc0.cookie_dir = os.environ.get("GEMINI_COOKIE_PATH")
                seen_cf.append(cookies_file)
                return fc0, _FakeGex
            globals()["make_client"] = _mk0
            out0, err0 = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out0), contextlib.redirect_stderr(err0):
                rc0 = asyncio.run(run_quota(argparse.Namespace(browser="auto", timeout=30, cookies_file="/tmp/c.json")))
            check(rc0 == 0 and seen_cf == ["/tmp/c.json"] and "tier: PRO" in out0.getvalue() and "5h: 250 credits left, 75% used" in out0.getvalue()
                  and "quota high (>=75%)" in err0.getvalue() and fc0.closed and fc0.cookie_dir and not Path(fc0.cookie_dir).exists(),
                  "run_quota returns 0 with data, forwards cookies_file, warns on stderr, closes client, and wipes isolated cookie dir")

            # exit 1 on empty usage_info
            fc1 = _QuotaFakeClient({})
            async def _mk1(browser="auto", timeout=90, cookies_file=None):
                fc1.cookie_dir = os.environ.get("GEMINI_COOKIE_PATH")
                return fc1, _FakeGex
            globals()["make_client"] = _mk1
            out1, err1 = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out1), contextlib.redirect_stderr(err1):
                rc1 = asyncio.run(run_quota(q_args))
            check(rc1 == 1 and out1.getvalue() == "" and "no quota data" in err1.getvalue() and fc1.closed and not Path(fc1.cookie_dir).exists(),
                  "run_quota returns 1 on empty data, closes client, and wipes cookie dir")

            # exit 2 on ImportError and auth error
            async def _mk_imp(browser="auto", timeout=90, cookies_file=None): raise ImportError("no pkg")
            globals()["make_client"] = _mk_imp
            err_imp = io.StringIO()
            with contextlib.redirect_stderr(err_imp):
                rc_imp = asyncio.run(run_quota(q_args))
            check(rc_imp == 2 and "missing dependency" in err_imp.getvalue(), "run_quota returns 2 on ImportError")

            async def _mk_auth(browser="auto", timeout=90, cookies_file=None): raise RuntimeError("no logged-in browser")
            globals()["make_client"] = _mk_auth
            err_auth = io.StringIO()
            with contextlib.redirect_stderr(err_auth):
                rc_auth = asyncio.run(run_quota(q_args))
            check(rc_auth == 2 and "authentication failed" in err_auth.getvalue(), "run_quota returns 2 on auth failure")
        finally:
            globals()["make_client"] = orig_make_client

        # cookies.json support: domain filtering, formats, permissions, symlink/TOCTOU, size, BOM, fallback, and leak-free errors
        for good_dom in (".google.com", "google.com", "gemini.google.com", ".gemini.google.com", "accounts.google.com"):
            check(_is_google_cookie_domain(good_dom), f"google cookie domain accepted: {good_dom}")
        for bad_dom in ("", "evilgoogle.com", "google.com.evil.org", "github.com", "..google.com", "google.com.", "google.com\n"):
            check(not _is_google_cookie_domain(bad_dom), f"non-google cookie domain rejected: {bad_dom!r}")
        check(validate_args(ns(cookies_file=""))[0] == 2 and validate_args(ns(cookies_file="   "))[0] == 2,
              "empty --cookies-file refused")

        ck_list = t / "cookies_list.json"
        ck_list.write_text(json.dumps([
            {"name": "__Secure-1PSID", "value": "psid-tok-123", "domain": ".google.com", "path": "/"},
            {"name": "__Secure-1PSIDTS", "value": "psidts-tok-456", "domain": "gemini.google.com", "path": "/"},
            {"name": "SESSION", "value": "bank-secret", "domain": "mybank.example", "path": "/"},
            {"name": "OTHER", "value": "spoof", "domain": "evilgoogle.com", "path": "/"},
        ]), encoding="utf-8")
        os.chmod(ck_list, 0o600)
        loaded_list = load_cookies_file(str(ck_list))
        check(len(loaded_list) == 2 and {c.name for c in loaded_list} == {"__Secure-1PSID", "__Secure-1PSIDTS"}
              and all(c.value != "bank-secret" and c.value != "spoof" for c in loaded_list),
              "cookies.json list filters strictly to google.com and drops unrelated domains")

        # Session-cookie coverage checks (domain + path must cover https://gemini.google.com/)
        check(_covers_gemini_root(".google.com", "/") and _covers_gemini_root("gemini.google.com", "/")
              and not _covers_gemini_root("accounts.google.com", "/") and not _covers_gemini_root("gemini.google.com", "/app"),
              "session cookie root coverage accepts .google.com/ and gemini.google.com/ only")
        for bad_scope, what in (
            ([{"name": "__Secure-1PSID", "value": "x", "domain": "accounts.google.com", "path": "/"}], "accounts.google.com only __Secure-1PSID"),
            ([{"name": "__Secure-1PSID", "value": "x", "domain": "gemini.google.com", "path": "/app"}], "/app-scoped __Secure-1PSID"),
        ):
            try: _parse_cookies_payload(bad_scope); check(False, f"{what} refused")
            except ValueError: ok += 1
        sel_psid, sel_ts = select_session_cookies([
            argparse.Namespace(name="__Secure-1PSID", value="good-root", domain=".google.com", path="/"),
            argparse.Namespace(name="__Secure-1PSID", value="decoy-acct", domain="accounts.google.com", path="/"),
            argparse.Namespace(name="__Secure-1PSIDTS", value="decoy-app", domain="gemini.google.com", path="/app"),
            argparse.Namespace(name="__Secure-1PSIDTS", value="good-ts", domain=".google.com", path="/"),
        ])
        check(sel_psid == "good-root" and sel_ts == "good-ts",
              "select_session_cookies picks .google.com/ over accounts.google.com or /app decoys")

        ck_wrap = t / "cookies_wrap.json"
        ck_wrap.write_text('\ufeff{"cookies": [{"name": "__Secure-1PSID", "value": "bom-tok", "domain": ".google.com"}]}', encoding="utf-8")
        os.chmod(ck_wrap, 0o600)
        check(load_cookies_file(str(ck_wrap))[0].value == "bom-tok", "cookies.json wrapper with UTF-8 BOM accepted")

        ck_flat = t / "cookies_flat.json"
        ck_flat.write_text('{"__Secure-1PSID": "flat-tok", "__Secure-1PSIDTS": "flat-ts"}', encoding="utf-8")
        os.chmod(ck_flat, 0o600)
        loaded_flat = load_cookies_file(str(ck_flat))
        check(len(loaded_flat) == 2 and loaded_flat[0].domain == ".google.com", "flat dict cookies.json accepted")

        # Permission, symlink, size, schema, and zero-leak checks
        if os.name == "posix":
            ck_open = t / "cookies_open.json"
            ck_open.write_text('{"__Secure-1PSID": "tok"}', encoding="utf-8")
            os.chmod(ck_open, 0o644)
            try: load_cookies_file(str(ck_open)); check(False, "mode 0644 cookies.json refused")
            except ValueError as e: check("chmod 600" in str(e) and "tok" not in str(e), "mode 0644 error advises chmod 600 without leaking value")

        ck_link = t / "cookies_link.json"; ck_link.symlink_to(ck_list)
        ck_empty = t / "cookies_empty.json"; ck_empty.write_bytes(b""); os.chmod(ck_empty, 0o600)
        ck_big = t / "cookies_big.json"; ck_big.write_bytes(b" " * (MAX_COOKIES_FILE_BYTES + 1)); os.chmod(ck_big, 0o600)
        ck_bad_utf8 = t / "cookies_bin.json"; ck_bad_utf8.write_bytes(b"\xff\xfe"); os.chmod(ck_bad_utf8, 0o600)
        ck_bad_json = t / "cookies_bad.json"; ck_bad_json.write_text("{SECRET_CANARY_999", encoding="utf-8"); os.chmod(ck_bad_json, 0o600)
        ck_nested = t / "cookies_nested.json"; ck_nested.write_text("[" * 100000 + "]" * 100000, encoding="utf-8"); os.chmod(ck_nested, 0o600)
        ck_no_psid = t / "cookies_nopsid.json"; ck_no_psid.write_text('{"NID": "SECRET_CANARY_999"}', encoding="utf-8"); os.chmod(ck_no_psid, 0o600)
        ck_crlf = t / "cookies_crlf.json"; ck_crlf.write_text('{"__Secure-1PSID": "a\\r\\nb"}', encoding="utf-8"); os.chmod(ck_crlf, 0o600)
        for bad_ck, what in (
            (ck_link, "symlink cookies.json"),
            (t / "viapai" / "n.txt", "symlinked parent cookies.json"),
            (t / "viapai" / ".." / "cookies_list.json", "symlink + .. bypass cookies.json"),
            (t, "directory cookies.json"),
            (t / "missing_cookies.json", "missing cookies.json"),
            (ck_empty, "empty cookies.json"),
            (ck_big, "oversized cookies.json"),
            (ck_bad_utf8, "invalid UTF-8 cookies.json"),
            (ck_bad_json, "invalid JSON cookies.json"),
            (ck_nested, "deeply nested cookies.json"),
            (ck_no_psid, "missing __Secure-1PSID cookies.json"),
            (ck_crlf, "CRLF injection cookies.json"),
        ):
            try: load_cookies_file(str(bad_ck)); check(False, f"{what} refused")
            except ValueError as e:
                check("SECRET_CANARY_999" not in str(e), f"{what} refused without leaking secret values")

        # load_cookies explicit path + default XDG_DATA_HOME fallback + missing-default-path guard + stale-browser AuthError fallback
        src_explicit, cks_explicit = load_cookies("edge", cookies_file=str(ck_list))
        check(src_explicit == "cookies-file" and len(cks_explicit) == 2, "explicit cookies_file overrides browser")
        prev_xdg = os.environ.get("XDG_DATA_HOME")
        prev_bc3 = sys.modules.get("browser_cookie3")
        orig_load_ck = load_cookies
        orig_init_ck = _init_client_from_cookies
        try:
            xdg_dir = base / "xdg_ck"
            (xdg_dir / "gemini-web").mkdir(parents=True, mode=0o700)
            fb_file = xdg_dir / "gemini-web" / "cookies.json"
            os.environ["XDG_DATA_HOME"] = str(xdg_dir)
            # Guard rejects --output and --output-dir pointing at default cookies.json even BEFORE it exists
            for lbl in ("--output", "--output-dir"):
                try: _refuse_same_as_default_cookies(fb_file, lbl); check(False, f"missing default cookies.json refused for {lbl}")
                except ValueError: ok += 1
            fb_file.write_text('{"__Secure-1PSID": "fallback-tok"}', encoding="utf-8")
            os.chmod(fb_file, 0o600)
            sys.modules["browser_cookie3"] = None  # simulate missing browser-cookie3 (e.g. Windows without decryption)
            src_fb, cks_fb = load_cookies("auto")
            check(src_fb == "cookies-file" and cks_fb[0].value == "fallback-tok", "default cookies.json fallback works when browser extraction unavailable")
            # Stale browser jar returning AuthError under browser="auto" retries once with default cookies.json
            calls_seen = []
            def _fake_load_stale(browser="auto", cookies_file=None):
                return "edge", [argparse.Namespace(name="__Secure-1PSID", value="stale", domain=".google.com", path="/")]
            async def _fake_init_stale(used, cookies, timeout):
                calls_seen.append(used)
                if used == "edge":
                    raise _FakeGex.AuthError("stale edge session")
                return "ok-client", _FakeGex
            globals()["load_cookies"] = _fake_load_stale
            globals()["_init_client_from_cookies"] = _fake_init_stale
            with contextlib.redirect_stderr(io.StringIO()):
                mc_c, _ = asyncio.run(make_client("auto", 30, cookies_file=None))
            check(mc_c == "ok-client" and calls_seen == ["edge", "cookies-file"],
                  "stale auto browser AuthError falls back once to default cookies.json")
            calls_seen.clear()
            try:
                asyncio.run(make_client("edge", 30, cookies_file=None))
                check(False, "explicit --browser edge does not fall back to default cookies.json")
            except _FakeGex.AuthError:
                check(calls_seen == ["edge"], "explicit --browser edge raises AuthError without fallback")
            globals()["load_cookies"] = orig_load_ck
            globals()["_init_client_from_cookies"] = orig_init_ck
            fb_file.unlink()
            fb_file.symlink_to(ck_list)
            try: load_cookies("auto"); check(False, "planted symlink at default cookies.json refused")
            except ValueError: ok += 1
        finally:
            globals()["load_cookies"] = orig_load_ck
            globals()["_init_client_from_cookies"] = orig_init_ck
            if prev_xdg is None: os.environ.pop("XDG_DATA_HOME", None)
            else: os.environ["XDG_DATA_HOME"] = prev_xdg
            if prev_bc3 is None: sys.modules.pop("browser_cookie3", None)
            else: sys.modules["browser_cookie3"] = prev_bc3

        try: check_not_same_file(ck_list.resolve(), str(ck_list), "--output", "--cookies-file"); check(False, "--output == --cookies-file refused")
        except ValueError: ok += 1
        try: check_not_same_file(ck_list.resolve(), str(ck_list), "--files", "--cookies-file"); check(False, "--files == --cookies-file refused")
        except ValueError: ok += 1

        # _safe_file_bytes ignores a vanished file instead of crashing
        gone = base / "vanished.txt"; gone.write_bytes(b"abcd")
        check(_safe_file_bytes([str(gone)]) == 4, "safe file bytes reads existing file")
        gone.unlink()
        check(_safe_file_bytes([str(gone)]) == 0, "safe file bytes survives vanished file")

        prev_ck = os.environ.get("GEMINI_COOKIE_PATH")
        with _isolated_cookie_cache() as cdir:
            check(cdir.is_dir() and (cdir.stat().st_mode & 0o777) == 0o700 and os.environ.get("GEMINI_COOKIE_PATH") == str(cdir),
                  "isolated cookie cache dir is private 0700")
        check(not cdir.exists() and os.environ.get("GEMINI_COOKIE_PATH") == prev_ck, "isolated cookie cache dir is wiped and env restored")

        test_log = base / "logdir" / "calls.jsonl"
        log(log_path=test_log, status="ok", mode="chat")
        check(test_log.is_file() and (test_log.stat().st_mode & 0o777) == 0o600 and (test_log.parent.stat().st_mode & 0o777) == 0o700,
              "call log is created with mode 0600 inside mode 0700 folder")
    print(f"selftest: {ok} checks passed")


def _refuse_same_as_default_cookies(target: Path, label: str) -> None:
    """Prevents --output, --output-dir, --prompt-file, or --files from targeting the default cookies.json path (existing or not)."""
    fb = default_cookies_file()
    if Path(os.path.abspath(target)) == Path(os.path.abspath(fb)):
        raise ValueError(f"{label} ({target}) must not target the default cookies.json path")
    try:
        if target.resolve() == fb.resolve():
            raise ValueError(f"{label} ({target}) must not target the default cookies.json path")
    except OSError:
        pass
    try:
        if target.exists() and fb.exists() and os.path.samefile(target, fb):
            raise ValueError(f"{label} ({target}) must not refer to the default cookies.json")
    except OSError:
        pass


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--mode", choices=["chat", "tasks", "research", "image", "video"], default="chat")
    p.add_argument("--model", default=None,
                   help="model alias (hydrogen, neon, carbon) or any model name/id shown by --list-models (default: carbon for image/video, hydrogen for chat/research)")
    p.add_argument("--effort", choices=list(LEVEL), default=None,
                   help="thinking level for chat mode (default: high); low is Baixo, high is Alto")
    p.add_argument("--keep", action="store_true",
                   help="keep the conversation in web history (default: temporary for chat/image; video and research always persist)")
    p.add_argument("--files", nargs="+", default=[], help="regular files to attach (chat only; empty files and links are refused)")
    p.add_argument("--ref", nargs="+", default=[],
                   help="reference image files for image/video modes (regular non-empty PNG, JPEG, WebP or GIF only)")
    p.add_argument("--aspect", default=None,
                   help="target aspect ratio W:H for image/video modes (e.g. 16:9, 4:5, 1:1)")
    p.add_argument("--confirm-apps-off", action="store_true", help="required by tasks: you assert connected apps and the browser are off")
    p.add_argument("--output", help="write the text reply here (mode 600) instead of stdout (chat/research only)")
    p.add_argument("--output-dir", help="folder for saved images or video (default: new folder in current directory)")
    p.add_argument("--prompt", help="prompt text; default: read stdin")
    p.add_argument("--prompt-file", help="read prompt from a regular UTF-8 file (mutually exclusive with --prompt; JSON auto-prefixed in image/video)")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--browser", default=os.environ.get("GEMINI_WEB_BROWSER", "auto"), choices=["auto"] + BROWSERS,
                   help="browser whose Google session to use (default: the first one found logged in)")
    p.add_argument("--cookies-file", default=None,
                   help="private JSON file with Google cookies (mode 0600 on POSIX; overrides --browser; env: GEMINI_WEB_COOKIES_FILE)")
    p.add_argument("--list-models", action="store_true", help="list models available on this account and exit")
    p.add_argument("--quota", action="store_true", help="print 5h and weekly quota balance without spending credits and exit")
    p.add_argument("--estimate", action="store_true", help="print expected credit range for the chosen settings and exit")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if args.selftest:
        return selftest()
    if args.cookies_file is not None and not str(args.cookies_file).strip():
        print("gemini_web: --cookies-file must not be empty", file=sys.stderr); sys.exit(2)
    if args.cookies_file is None:
        env_ck = os.environ.get("GEMINI_WEB_COOKIES_FILE")
        if env_ck is not None and env_ck.strip():
            args.cookies_file = env_ck
    if args.list_models and args.quota:
        print("gemini_web: pass either --list-models or --quota, not both", file=sys.stderr); sys.exit(2)
    if args.list_models or args.quota:
        if args.timeout <= 0:
            print("gemini_web: --timeout must be a positive integer", file=sys.stderr); sys.exit(2)
        if args.cookies_file is not None:
            try:
                load_cookies_file(args.cookies_file)
            except ValueError as e:
                print(f"gemini_web: {e}", file=sys.stderr); sys.exit(2)
    if args.list_models:
        if os.environ.get("GEMINI_WEB_DRY_RUN") == "1":
            print("gemini-4-hydrogen\t4 Hydrogen\tdry-run\tavailable")
            print("gemini-neon\t4 Neon\tdry-run\tavailable")
            print("gemini-carbon\t4 Carbon\tdry-run\tavailable")
            sys.exit(0)
        _maybe_reexec_venv(need_browser_cookies=(args.cookies_file is None))
        sys.exit(asyncio.run(run_list_models(args)))
    if args.quota:
        if os.environ.get("GEMINI_WEB_DRY_RUN") == "1":
            print(format_quota({"tier": "DRY-RUN", "h5": [1000, 10], "wk": [10000, 5], "h5_reset": None, "wk_reset": None, "ai_credits": None}))
            sys.exit(0)
        _maybe_reexec_venv(need_browser_cookies=(args.cookies_file is None))
        sys.exit(asyncio.run(run_quota(args)))
    code, msg = validate_args(args)
    if code:
        print(f"gemini_web: {msg}", file=sys.stderr); sys.exit(code)
    if args.model is None:
        args.model = default_model_for_mode(args.mode)
    args.effort = args.effort or "high"
    if args.aspect is not None:
        args.aspect = validate_aspect(args.aspect)
    if args.estimate:
        print(format_estimate(args.mode, args.model, args.effort))
        sys.exit(0)
    dry_run = os.environ.get("GEMINI_WEB_DRY_RUN") == "1"
    if not dry_run:
        _maybe_reexec_venv(need_browser_cookies=(args.cookies_file is None))
    out_dir: Path | None = None
    out_file: Path | None = None
    try:
        if args.cookies_file is not None:
            load_cookies_file(args.cookies_file)
        if args.prompt_file is not None:
            prompt = read_prompt_file(args.prompt_file)
            _, pf_abs = _reject_symlink_prefix(args.prompt_file)
            _refuse_same_as_default_cookies(pf_abs, "--prompt-file")
            if args.cookies_file is not None:
                check_not_same_file(pf_abs, args.cookies_file, "--prompt-file", "--cookies-file")
        else:
            prompt = args.prompt if args.prompt is not None else sys.stdin.read()
        if not prompt.strip():
            raise ValueError("empty prompt")
        prompt = prepare_prompt(prompt, args.mode, aspect=args.aspect)
        if args.output:
            out_file = check_output_file(args.output)
            _refuse_same_as_default_cookies(out_file, "--output")
            if args.prompt_file is not None:
                check_distinct_output_and_prompt(out_file, args.prompt_file)
            if args.cookies_file is not None:
                check_not_same_file(out_file, args.cookies_file, "--output", "--cookies-file")
        if args.mode in ("image", "video"):
            files = check_ref_images(args.ref, max_count=(1 if args.mode == "video" else None)) if args.ref else []
            if args.output_dir:
                out_dir = check_output_dir(args.output_dir)
                _refuse_same_as_default_cookies(out_dir, "--output-dir")
                if args.cookies_file is not None:
                    check_not_same_file(out_dir, args.cookies_file, "--output-dir", "--cookies-file")
            else:
                check_cwd_writable()
        else:
            files = check_files(args.files) if args.files else []
            for f in files:
                fp = Path(os.path.abspath(f))
                _refuse_same_as_default_cookies(fp, "--files")
                if args.cookies_file is not None:
                    check_not_same_file(fp, args.cookies_file, "--files", "--cookies-file")
    except ValueError as e:
        print(f"gemini_web: {e}", file=sys.stderr); sys.exit(2)
    if dry_run:
        extra = f", aspect={args.aspect}" if args.aspect else ""
        extra_out = f" aspect={args.aspect}" if args.aspect else ""
        print(f"gemini_web: dry-run validated ({format_estimate(args.mode, args.model, args.effort)}, files={len(files)}{extra})", file=sys.stderr)
        print(f"[dry-run] mode={args.mode} model={args.model} effort={args.effort} files={len(files)}{extra_out}")
        sys.exit(0)
    sys.exit(asyncio.run(run(args, prompt, files, out_dir=out_dir, out_file=out_file)))

if __name__ == "__main__":
    main()
