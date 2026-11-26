# gemini-web

Send text, clean attached files, image generation/editing, short video generation and Deep Research requests from your coding agent to your own logged-in Gemini web session.

## What it does

It wraps `scripts/gemini_web.py`, which talks to Gemini on the web with the Google cookies of a browser where you are
already logged in (or a private `cookies.json` export via `--cookies-file`, for Windows or locked keyrings). You choose the model (`hydrogen`, `neon`, `carbon`, or any model returned by `--list-models`; defaults are `hydrogen` for text/research and `carbon` for image/video) and the thinking level (`low`, `medium`, `high`), attach
regular files up to 300 KB in total, pass `--prompt-file` or `--aspect W:H`, generate and edit images, make short videos, check balances with `--quota` (0 credits), or try a Deep Research run (unconfirmed), all on a quota separate from your primary coding model's. Chats are
temporary by default. The script refuses symlinks, folders, empty files and oversized attachments or prompt files before anything is sent,
warns on high quota usage and skips the call (with window reset times) when your 5-hour window is nearly spent, retries the app's canned error notices, flags a silent change of
model or thinking level, isolates the library's cookie cache in a per-run `0700` folder, and never prints or logs cookies. Gemini Tasks is not supported and the script refuses it.

## When to reach for it

- You want a second opinion from another model family on a design note, a spec or any non-sensitive question.
- You want to generate or reference-edit images, or create a short video clip, using your Gemini web session.
- You want a Deep Research report without leaving the coding session.
- You want Gemini to read a long public document or PDF, or to take non-sensitive work off your primary model quota.
- Another skill needs an external-model channel and can call the script.

Do not use it for local code edits, shell work, or anything private: secrets, client or financial data, personal files.

## It's working if

- `python3 scripts/gemini_web.py --selftest` passes with no network.
- A call with a clean prompt exits 0, prints the reply, and leaves nothing in your Gemini history unless you passed `--keep`.
- An empty file, a symlink, or attachments over 300 KB fail with exit 2 before any request is sent.
- `--mode tasks` exits 7 without `--confirm-apps-off` and 6 with it, and no cookie value appears in output or in the call log.

## Example

The unedited output of a real call is in [example.md](example.md).

## Limits and setup

Install dependencies into `~/.local/share/gemini-web/venv` (or `.venv/` beside `SKILL.md`): `scripts/gemini_web.py` auto-selects that venv (or `GEMINI_WEB_PYTHON`) when system `python3` lacks the packages. Measured costs, failure rates and what is not known are in `references/limits.md`; media guidance is in `references/media.md`; how the session is found is in `references/auth.md`. This skill does not bundle third-party libraries: `requirements.txt` installs `gemini-webapi` (AGPL-3.0) and `browser-cookie3` (LGPL) separately. This drives an unofficial web interface on your own account, at your own risk.
