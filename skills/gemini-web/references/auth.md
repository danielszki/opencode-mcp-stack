# Authentication

`scripts/gemini_web.py` has no login of its own. It reads the Google cookies of a browser where you are
already logged in to gemini.google.com, using `browser-cookie3`, or loads them from a private JSON cookie
export (`--cookies-file`), and hands them to `gemini-webapi`.

## How it works

1. If `--cookies-file FILE` or `GEMINI_WEB_COOKIES_FILE` is set, `load_cookies` reads only that JSON file
   (skipping browser stores). Otherwise it asks each supported browser in turn (Edge, Chrome, Chromium,
   Brave, Firefox, Vivaldi, Opera, LibreWolf) for the cookies of `google.com`, taking the first browser that
   holds a non-empty `__Secure-1PSID` cookie (`--browser NAME` or `GEMINI_WEB_BROWSER` selects one).
2. When `--browser auto` finds no logged-in browser (common on Windows due to Chromium App-Bound
   Encryption, or on Linux with a locked keyring), the script falls back automatically to
   `$XDG_DATA_HOME/gemini-web/cookies.json` (default `~/.local/share/gemini-web/cookies.json`) if it exists.
3. `make_client` builds the `gemini-webapi` client from the two session cookies and then loads the whole
   Google cookie jar into it. With only the two session cookies, `init()` timed out in testing; with the
   whole jar it worked.
4. Cookie values are never printed or written to the call log (`~/.local/share/gemini-web/calls.jsonl`, mode `0600`).
5. By default `gemini-webapi` caches cookies under `/tmp/gemini_webapi/` using `__Secure-1PSID` in the filename, and tries cached cookies before caller-supplied ones (which can shadow fresh browser cookies with a stale session). `scripts/gemini_web.py` overrides `GEMINI_COOKIE_PATH` to a fresh private `0700` temporary directory for each run and removes it on exit.

## Using `cookies.json` (Windows or locked keyrings)

On Windows (where modern Chrome and Edge encrypt cookies with App-Bound Encryption that `browser-cookie3`
cannot decrypt) or on headless Linux hosts, export the `google.com` cookies from a logged-in browser tab
into a private JSON file and pass `--cookies-file FILE` (or save it at `~/.local/share/gemini-web/cookies.json`).

- **Recommended format:** export the **full `google.com` cookie list** as a JSON array of objects
  (`[{"name": "...", "value": "...", "domain": ".google.com", "path": "/"}, ...]`, matching standard
  Cookie-Editor / EditThisCookie / DevTools exports), or `{"cookies": [...]}`. A flat JSON object
  (`{"__Secure-1PSID": "...", "__Secure-1PSIDTS": "..."}`) is also parsed, though `init()` timed out with
  only two cookies in earlier testing.
- **Security guards enforced before opening or sending:**
  - Rejects any symlink along the path (using POSIX `openat`/`O_NOFOLLOW` per component) and non-regular files.
  - On POSIX, requires the file to be owned by the current user with no group/other permissions (`chmod 600`). On Windows, keep the file inside your user profile with private NTFS permissions.
  - Caps file size at 1 MB and requires valid UTF-8 JSON containing a non-empty `__Secure-1PSID`.
  - Filters cookies strictly to `google.com` and `*.google.com` domains so cookies for unrelated sites in a broader browser export are never loaded or transmitted.
  - Refuses `--output` overwriting `--cookies-file` and refuses attaching `--cookies-file` via `--files`.
  - Never prints cookie values in errors, stdout, stderr, or `calls.jsonl`.

## Python environment

If the active `python3` lacks `gemini-webapi`, `browser-cookie3`, or `curl_cffi`, `scripts/gemini_web.py` automatically re-execs into the first executable interpreter found in:

1. `$GEMINI_WEB_PYTHON`
2. `<skill-dir>/.venv/bin/python` (or `Scripts/python.exe`)
3. `$XDG_DATA_HOME/gemini-web/venv/bin/python` (default `~/.local/share/gemini-web/venv/bin/python`)

## If it fails (exit code 2)

- "no browser with a logged-in Google session found": open gemini.google.com in a supported browser and
  log in, pass `--browser`, or export your `google.com` cookies to `cookies.json` and pass `--cookies-file`.
- "cookies file permissions are too open": on Linux/macOS run `chmod 600 <cookies.json>`.
- "missing dependency": install `requirements.txt` into `~/.local/share/gemini-web/venv` (or `.venv/`), or set `GEMINI_WEB_PYTHON`.
- The browser is open and logged in but nothing is found: on Linux the cookie store may need the desktop
  keyring unlocked; on Windows Chrome/Edge App-Bound Encryption blocks `browser-cookie3`, so use `--cookies-file`.
- An authentication error after it used to work: the session expired. Log in again in the browser (or refresh `cookies.json`).

## The pinned library

`requirements.txt` pins `gemini-webapi==2.1.1`. The `medium` effort level rewrites a private part of the
request that this exact version builds, and the model label check reads the raw response. After raising
the version, run `--selftest`, then one cheap call at each effort level and check that the label appears
and the exit code is 0. The library is released under the AGPL-3.0, which matters if you redistribute
anything that includes it.

## Notes

- This drives an unofficial web interface. Google can change it without notice, and using it may fall
  outside what Google's terms allow for automated access. You use your own account at your own risk.
- The session cookies give full access to the Google account. Keep them out of logs, prompts, issues and
  commits. If one leaks, sign out of all sessions in the Google account settings.
