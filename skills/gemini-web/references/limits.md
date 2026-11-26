# Limits, costs and what is not known

Read this before choosing Neon or high effort on a tight quota, before attaching large files or PDFs,
and when deciding whether Deep Research or Tasks fits. Everything here was measured on one account on
2026-11-24 unless it says "documented" (read on Google's help pages, which were summarized by a small model,
not quoted) or "not verified".

## Contents

1. How the quota works
2. Cost and latency per setting
3. Thinking level
4. Files
5. Failures
6. Deep Research
7. Tasks
8. What is not known

## 1. How the quota works

- Two windows, read by the script from the web app: a 5-hour window and a weekly one, both in credits. The
  5-hour window renews every 5 hours until the weekly credits are spent (documented).
- Run `scripts/gemini_web.py --quota` to read both windows (remaining credits, `% used`, and `reset_at`
  timestamps when present, plus account `tier` and `ai_credits_remaining` if returned) without spending
  credits. During calls, stderr emits deterministic threshold notices at `>=50%`, `>=75%`, and `>=90%` usage,
  and exit 4 includes window reset times when available.
- When the quota is spent, subscribers continue with a lightweight model (Flash-Lite, documented). The
  script tries to detect that through the model label in the response; see section 8.
- Deep Research counts as "high" use and analysis of a large file as "medium" (documented). The pages do
  not say whether Tasks, Deep Research and files share one bucket.
- The credit deltas the script logs include any use of the same account in the browser at the same time:
  in one stretch of the measurement about 55% of the weekly drop was not caused by the script's own calls.
  Treat per-call numbers as orders of magnitude.

## 2. Cost and latency per setting

Credits per successful call (a failed call cost 0 in every case seen). One run per case unless noted.

| Setting | Credits per call | Latency (median) | Evidence |
| --- | --- | --- | --- |
| hydrogen low | 3.4 (questions over 7 text files), 4.9 (review prompts), 5.7 (one case, 3 runs) | 10 to 13 s | 43 calls |
| hydrogen medium | 5 to 8.1 (screening), 6.3 (one case, 3 runs), 8.6 (48-call confirmation) | 15 s (confirmation), 19 s (screening) | 59 calls |
| hydrogen high | 9 to 16.6 (screening), 14.3 (one case, 3 runs), 17 to 22 (earlier batch) | 29 s | 33 calls |
| neon low | 6 | 10 s | 1 call |
| neon medium | 43 | 68 s | 11 calls |
| neon high | 79 | 120 s | 11 calls |

## 3. Thinking level

The app offers three levels. The request carries the level in field 81 of the request (1 low, 4 medium,
2 high) and in the model header. The `gemini-webapi` library sends only 1 and 2; `medium` is set by the
script by rewriting both places in the outgoing request (it checks the shape and exits 6 if it cannot).

On one review case, 3 runs per level, interleaved, 60 s apart:

| Level | Thinking text (characters) | Latency (s) | Credits |
| --- | --- | --- | --- |
| low | 0, 0, 0 | 13, 29, 78 | 5.7 |
| medium | 180, 0, 186 | 16, 71, 43 | 6.3 |
| high | 1118, 651, 643 | 42, 22, 41 | 14.3 |

High clearly changes behavior (always some thinking, about 2.5 times the cost). Medium has a weak effect:
thinking in 2 of 3 runs at the cost of low. Latency does not separate the levels. This measures mechanics,
not answer quality.

## 4. Files

| Probe | Result |
| --- | --- |
| `.diff`, `.py`, `.json`, `.md` together | accepted; the model saw all four (`.py` and `.json` content reading not directly verified) |
| `.patch`, `.sh`, `.yml`, no extension | accepted and seen |
| empty file next to a normal one | the whole call fails with HTTP 400, 0 credits |
| 10 small files | all seen and cited, about 3 credits |
| one 233 KB text file | read start, middle and end, about 46 credits |
| one 1.78 MB text file | accepted, read only to about 22% (the model said so), about 52 credits |

- Questions over 7 Markdown files, pasted into the prompt or attached: about the same credits (3.4 and 3.6)
  and the same accuracy in 10 questions each (8 and 9 correct by a regex scorer, one run each, not a
  significant difference). 7 small PDFs: 15.5 credits per call and 15 s instead of 10 s.
- Reviewing code: with the diff pasted or attached as a file the recall was the same (8 of 8 hard cases,
  1 run each); attached was 27% slower and about 3.5 credits dearer per call.
- Extra context files helped in the only case where the defect sits outside the diff: the model named the
  broken caller when its file was attached and only inferred it otherwise. One run per arm, not confirmed.
- Whether an attachment is kept on the server after a temporary chat is not known. The temporary chat is
  not returned by `read_chat` (3 of 3) nor listed (5 of 5); the app says temporary chats are kept 72 hours.

## 5. Failures

- Canned error notices come back as an ordinary reply, for example "Sorry, something went wrong. Please try
  your request again.", "I seem to be encountering an error. Can I try something else for you?", "I
  encountered an error doing what you asked. Could you try again?" and "I'm having a hard time fulfilling
  your request. Can I help you with something else instead?". They cost 0 credits. The script recognizes
  them and retries.
- By batch (one afternoon, 11 calls per setting in the screening, interleaved and 45 s apart): hydrogen medium
  4 canned notices, hydrogen high 5 canned notices and 1 exception (220 s), neon medium 1 exception, neon high 3 exceptions. A later
  sequential run of 48 calls at hydrogen medium: 4 errors and 1 timeout. 43 earlier calls at hydrogen low: none.
- Over 118 review calls: 0 failures in 43 calls without thinking (low), 6 in 30 at medium, 10 in 45 at
  high. Failures clustered in time: 11 of 21 calls in the 15:00 hour, none in the morning. Effort and hour are
  confounded, since every low-effort call was made in the morning or early afternoon. A test that
  interleaves low and medium in the same hour would separate them (not run).
- A sequential run of 48 calls on one model at medium effort, started after that bad hour, had 5 failures
  (4 errors, 1 timeout) and no canned notices.
- Neon failed differently: an exception after about 275 s, 4 of 22 calls.
- Speculative "must fix" findings: in 15 clean review diffs at medium effort, 3 held a "must fix" built on a
  scenario the model could not check (for example "if the main block does not call this test"). A note in
  the prompt saying the model sees only the diff changed nothing (2 of 6 clean runs with and without it, 10
  findings in total with and without). For code review, treat every must-fix from this channel as a
  hypothesis to check, and do not use it as the only reviewer.
- A canned refusal ("I am only an AI...") was seen 3 times in 15 early calls and not in 23 later calls
  under the same conditions, so its cause is not known.

## 6. Deep Research, images and video

One call per setting on 2026-11-24 on one PRO account, so read as a guide and not a distribution:

| Mode | Result | Credits | Time |
| --- | --- | --- | --- |
| image (`--model carbon`, default) | JPEG 1024x1024, labelled `Nano Banana 2 Lite` (2 calls) | 3 | 19 to 20 s |
| image (`--model gemini-auto`) | JPEG 1024x1024, labelled `Nano Banana 2 Lite` | 3 | 18 s |
| image (`--model carbon`, extended thinking forced) | JPEG 1024x1024, still labelled `Nano Banana 2 Lite` | 6 | 11 s |
| image (`--model hydrogen`) | JPEG 1024x1024, labelled `Nano Banana 2.1` | 30 | 23 s |
| image (`--model neon`) | JPEG 1024x1024, labelled `Nano Banana 2.1` | 31 | 25 s |
| image with `--ref` (`--model carbon`) | the requested change, the rest kept (`Nano Banana 2 Lite`) | not read | 23 s |
| video (`--model carbon`, default) | MP4 1280x720, H.264 and AAC audio, 10 s, 2.8 MB, plus a thumbnail (no label) | about 880 | 350 s |
| Deep Research (`--model hydrogen`) | plan and start worked; no report after 26 minutes; exit 5 | 16 visible | 1256 s before giving up |

- Image routing depends on `--model` on this account: `carbon` and `gemini-auto` routed to `Nano Banana 2 Lite` (~2 to 3 credits), whereas `hydrogen` and `neon` routed to `Nano Banana 2.1` (~30 to 31 credits, ~10x higher cost). Forcing extended thinking on `carbon` did not switch to `Nano Banana 2.1`. In 5 follow-up calls on 2026-11-24, `--aspect` produced matching full-bleed outputs (`16:9` -> `1376x768`, `9:16` -> `768x1376`, `4:5` -> `928x1152` on `carbon`; `16:9` -> `1376x768` on `hydrogen`) and `--prompt-file` with structured JSON + `--aspect 16:9` succeeded on `carbon` (`1376x768`, 2 credits). Whether other accounts route identically, and whether `--aspect` holds in `--mode video` or unusual ratios, is not verified. The script does not fail on image or video labels; it only logs them on stderr.
- The video chat and the research chat stay in the web history (the video flow needs it). Delete them by hand
  when you are done.
- Deep Research is unconfirmed: the conversation shows the plan and a "working on it" reply, and the report was
  still not ready 26 minutes after the start. The script exits 5 and prints the conversation id so you can look.

## 7. Tasks

Tasks (the app's agent mode) is not implemented in the script. The library has no parameter for it, and
the request field that selects it was never captured because that would need a real message sent in Tasks
mode with connected apps and the browser off. Documented about Tasks: experimental, needs History, up to 15
concurrent tasks, can use connected apps and a browser, and Google's own page says it is vulnerable to
prompt injection and needs supervision. The app's browser setting offers only "always allow" and "always
ask", with no "off", which is why capturing it safely needs the connectors switched off first.

## 8. What is not known

- Whether quality differs between effort levels: the screening had 1 to 5 usable hard cases per setting.
  Neon answers better than Hydrogen in the user's experience; the screening did not measure it.
- The model label in the response for `neon high` (low `4 Neon` and medium `4 Neon Medium` were observed, but `neon high` was not), and what any label shows during a real fallback to a lightweight model. The Hydrogen labels at the three effort levels were seen once each.
- The cause of the failure bursts: time of day, thinking level, or something else.
- How long attachments and Deep Research chats stay on the server.
- Whether Deep Research can finish on this account at all, and what it costs.
- The range of image and video costs: one call each was measured.
