# Image and video generation reference

Guidance for running `scripts/gemini_web.py --mode image` and `--mode video`. Every account or library claim below is tagged `[measured]`, `[from library source]`, or `[not verified]`.

## How this channel works

- **No separate media RPC in `gemini-webapi` 2.1.1** `[from library source]`: both images and videos are requested via `GeminiClient.generate_content()`, with the prompt and chosen `--model` triggering image or video creation.
- **Model discovery** `[from library source]`: `constants.Model` is deprecated and contains no image or video models. Available models are discovered per account at startup via `client.list_models()` and matched by `client.resolve_model()`. Run `python3 scripts/gemini_web.py --list-models` to see what your account exposes.
- **Default model and image routing**: `--mode image` and `--mode video` default to `--model carbon` (`chat` and `research` default to `hydrogen`). On one PRO account on 2026-11-24 (identical 1:1 prompt, 1 call per model, all returned 1024x1024 JPEGs) `[measured]`:
  - `--model carbon` (default) and `--model gemini-auto` routed to `Nano Banana 2 Lite` (3 credits, 18 to 20 s; forcing extended thinking on `carbon` still routed to `Nano Banana 2 Lite` and cost 6 credits). Good default for drafts, iterations, and general images.
  - `--model hydrogen` and `--model neon` routed to `Nano Banana 2.1` (30 and 31 credits, 23 to 25 s, about 10x the cost of `carbon`). Reach for them when higher texture and lighting fidelity justify the extra credits.
  - Whether other accounts expose the same models or map them the same way is `[not verified]`.
- **Prompt and aspect flags**: `--aspect W:H` (for example `16:9`, `4:5`, `1:1`) is accepted only in `image` and `video` modes and appended cleanly as an aspect-ratio instruction. Verified on one PRO account (2026-11-24, 5 calls, all full-bleed with no letterboxing) `[measured]`: `--model carbon` (`Nano Banana 2 Lite`) returned `1376x768` for `16:9`, `768x1376` for `9:16`, `928x1152` for `4:5`, and `1376x768` for `--prompt-file scene.json --aspect 16:9`; `--model hydrogen` (`Nano Banana 2.1`) returned `1376x768` for `16:9` (unusual ratios, video `--aspect`, and other accounts remain `[not verified]`). `--prompt-file FILE` reads a regular non-empty UTF-8 file (no symlinks, up to 300,000 bytes, mutually exclusive with `--prompt`); when its content is a valid JSON object or array in `image`/`video` mode, the CLI prefixes a short instruction telling the model to return generated media directly instead of a text reply (verified working on `--model carbon` `[measured, 1 call]`).
- **Image saving** `[from library source]`: `GeneratedImage` items come from JSPB field 7 (separate from web-search `WebImage` items). `GeneratedImage.save(full_size=True)` requests a full-size URL through the `c8o8Fe` RPC and falls back to `=s2048-rj` if that RPC fails. The CLI writes to a temporary file, detects the real format from magic bytes (PNG, JPEG, WebP, GIF, AVIF), sets mode `0600`, and renames to `image_01.<ext>`, `image_02.<ext>`, and so on.
- **Video polling and saving** `[from library source]`: `GeneratedVideo` items come from JSPB field 59. When a video turn is still running after the stream ends, `_generate()` polls `read_chat(cid)` every 10 seconds; after a URL arrives, `GeneratedVideo.save()` polls HTTP 206 every 10 seconds until HTTP 200. The CLI bounds both stages under `--timeout`, verifies the container magic bytes (MP4, MOV, WebM, AVI), sets mode `0600`, and renames to `video_01.<ext>`.
- **Temporary chats**:
  - `image` mode sends `temporary=True` unless `--keep` is passed `[from library source]`. Generation, download and a `--ref` edit all worked in a temporary chat `[measured, 2 calls]`; whether the downloaded image is the full-size one is `[not verified]`.
  - `video` mode always sends `temporary=False` because pending video turns depend on `read_chat(cid)` history polling `[from library source]`. Assume video prompts remain in web history.
- **Quota, cost, and latency**:
  - Check remaining credits without spending any using `python3 scripts/gemini_web.py --quota`.
  - Text reference costs on one account on 2026-11-24 ranged from 3-6 credits (hydrogen low) to ~79 credits (neon high) `[measured]`.
  - Single-call media measurements on one account (2026-11-24) `[measured]`: `image` with `carbon` or `gemini-auto` cost 3 credits (18 to 20 s); one `--ref` edit with `carbon` took 23 s; `image` with `hydrogen` cost 30 credits (23 s) and with `neon` cost 31 credits (25 s); one 10 second `video` with `carbon` cost about 880 credits (350 s). The 5-hour credit guard checks these estimates (falling back to 3 for unmeasured `image` models and 880 for `video`) before sending. Daily and hourly caps, and whether failed image or video calls spend 0 credits, are `[not verified]`.
  - Reference image upload size caps on Google's server are `[not verified]` (the CLI applies a local safety cap of 10 MB per file and 20 MB total, and validates PNG, JPEG, WebP, or GIF magic bytes).

## Before generating: scope, medium, and iteration cap

- **Ask before spending credits when missing decisions change the output**: if the user's request leaves open the final destination (banner, slide, social card, print, icon), aspect ratio, visual style or medium, or exact embedded wording, ask a few short questions before generating instead of guessing.
- **Prefer code or SVG when precision matters**: use SVG, HTML/CSS, Mermaid, Matplotlib, or PIL instead of `--mode image` for exact data charts, labeled architecture diagrams, UI wireframes, crisp vector logos, geometric patterns, or layouts that require pixel-exact spacing or editable text.
- **Cap automatic iterations at 2 to 3 attempts**: inspect each saved image and make targeted adjustments, but after 2 to 3 automatic tries show the strongest output to the user along with what still needs tweaking instead of looping indefinitely on shared credits.

## Writing image prompts (`--mode image`)

Write complete, plain natural-language sentences. Avoid comma-separated buzzword lists ("masterpiece, 8k, trending"). Lead with an unambiguous generation verb ("Generate a photograph of...", "Create a clean vector diagram of...") so the web model invokes image generation instead of replying with text.

Cover these details concretely:

1. **Subject and action**: who or what is depicted, posture, expression, materials, and exact placement in the frame.
2. **Setting and props**: foreground, midground, and background objects; surface textures; spatial depth.
3. **Composition and framing with concrete numbers**:
   - Aspect ratio via `--aspect W:H` and/or in prose (for example `--aspect 16:9` widescreen, `--aspect 4:5` vertical portrait, `--aspect 1:1` square). Common ratios (`16:9`, `9:16`, `4:5`, `1:1`) produced matching full-bleed dimensions on `carbon` and `16:9` matched on `hydrogen` `[measured, 2026-11-24]`; unusual ratios and video `--aspect` are `[not verified]`.
   - Numeric frame fractions for scale and margins (for example "the bottle fills about 65% of the frame height, centered horizontally with 20% headroom above the cap and 15% table surface below the base") instead of vague size words.
   - Shot distance and lens feel (for example `medium waist-up shot`, `85 mm portrait lens with shallow depth of field`, `24 mm wide angle from 1 meter above floor level`, `straight-on orthographic flat lay`).
   - Camera angle (`eye level`, `15-degree high angle`, `low angle looking up 20 degrees`).
4. **Lighting with concrete direction, quality, and color temperature**:
   - Source and angle (`soft overcast daylight entering from a tall window 45 degrees to camera-left`, `hard late-afternoon sun 20 degrees above the horizon from behind camera-right`).
   - Color contrast (`cool ~6000 K ambient skylight in the shadows balanced by a warm ~3000 K brass desk lamp`).
   - Shadow behavior (`soft diffused contact shadows`, `crisp elongated shadows across concrete`).
5. **Palette, medium, and finish**: specify photograph, studio product shot, matte gouache illustration, architectural elevation, or technical line drawing; state 3 to 5 dominant colors and surface finishes (brushed aluminum, unglazed stoneware, matte paper grain).
6. **Rendered text (only when needed)**: put the exact characters in double quotes, keep copy short (under ~8 words), and describe font style, alignment, size relative to the object, and high-contrast background behind the letters.
7. **Complex scenes via `--prompt-file` with structured JSON**: when a scene has many tightly coupled constraints (multiple subjects, layered foreground/midground/background, exact color hexes, camera/lens specs, and typography placement), write a clean UTF-8 JSON object to a file and pass `--prompt-file scene.json` (optionally with `--aspect W:H`). In `image` and `video` modes, the CLI automatically prepends a short media-generation directive so the model generates the asset instead of echoing text.

## Editing step by step with `--ref`

Pass one or more local reference images with `--ref FILE ...` (never personal IDs, private photos, or confidential screenshots).

- **State the role of each reference in the prompt**: if passing two images, identify which is the subject and which is the background or style reference ("Keep the ceramic mug from the first attached image and place it on the weathered oak table from the second attached image").
- **Use a dedicated pose reference for tricky postures**: when an exact body stance, hand position, or silhouette matters, supply a separate reference image for the pose alongside the subject reference (for example, identity and wardrobe from reference 1, posture and framing from reference 2) rather than trying to specify complex anatomy in prose alone.
- **One concern per pass**: perform layout or background changes first, lighting or color adjustments second, and fine detail or text overlays last. Packing many unrelated edits into a single prompt increases drift.
- **Name both the change and what must stay fixed**: explicitly list invariant traits (camera angle, subject pose, object proportions, printed label text, wardrobe, background geometry) alongside the single requested modification.
- **Inspect between passes**: check the saved file before feeding it back as `--ref` for the next edit.

## Keeping a subject or style consistent across a set

- **Reuse the original anchor image**: when generating 3 to 5 scenes of the same character or product, pass the original clean reference with `--ref` on every call rather than chaining generations from already-edited outputs, which compounds artifacts.
- **Pair visual reference with written invariants**: repeat 3 to 5 stable traits in the prompt (exact clothing colors, proportions, markings, material finish) so the text and `--ref` image reinforce each other.
- **Hold camera and lighting rules steady**: keep the same lens focal length, color temperature, and rendering medium across the whole series.

## Prompting short videos (`--mode video`)

Run `--mode video` in the background with a generous timeout (`--timeout 600` or higher) and wait for completion rather than polling. Lead with an explicit request ("Generate a short video of...").

- **Design a single continuous shot**: short clips handle one uninterrupted camera move far better than multi-cut sequences.
- **Describe four layers cleanly**:
  1. **Starting frame**: subject, environment, framing, and lighting (or pass a single starting image with `--ref` and focus the prompt on what moves).
  2. **Subject motion**: one clear, physically plausible action with pacing ("slowly turns head 30 degrees to the right over the clip", "pours dark coffee in a steady thin stream").
  3. **Camera motion**: one deliberate movement or a locked camera ("locked tripod shot", "slow 10-degree push-in toward the mug", "gentle lateral dolly from left to right at eye level").
  4. **Secondary ambient motion**: subtle cues that sell realism (rising steam, curtains swaying gently in a breeze, shifting specular reflections on water).
- **Audio**: if ambient sound matters, describe it briefly ("quiet rain against glass and soft room tone, no music"). The single measured video MP4 included an AAC audio stream `[measured, 1 call]`, though audio synchronization and prompt adherence across scenes are `[not verified]`.

## Checking the output file

Before reporting success to the user, verify the saved file(s):

1. **File integrity**: confirm stdout printed at least one path, the file exists, and its size is plausible (the CLI already verified real magic bytes and renamed the extension).
2. **Visual inspection (images)**: inspect the saved image directly (for example by viewing the saved image file with an image-capable file reader). Check anatomy (hands, eyes, symmetry), geometry (straight architectural lines, reflections), exact spelling of any rendered text, aspect ratio, unexpected borders or artifacts, and fidelity to `--ref` invariants.
3. **Video inspection**: check duration, resolution, codec, and audio stream (for example with `ffprobe` if installed) and extract 2 to 3 frames (start, middle, end) if you need to inspect visual continuity, flicker, or prompt adherence.

## Handling failures

- **Exit 1 (`no_media` or `download_error`)**: stderr shows the model's reply snippet or download error. If the response contained a video in `--mode image` or an image in `--mode video`, stderr prints a hint to switch `--mode`. If the model replied with text instead of generating media, rewrite the opening sentence to ask directly for an image or video (or pass structured JSON via `--prompt-file`) and verify your `--model` with `--list-models`. If the download failed after generation, check network connectivity; do not immediately spam retries because the generation may already have been billed (`[not verified]`).
- **Exit 2**: invalid flags (`--aspect` format or mode, `--prompt` with `--prompt-file`), unsupported `--ref` magic bytes, symlink/empty/oversized file, invalid UTF-8 `--prompt-file`, or unknown model name. Fix the input or run `--list-models`.
- **Exit 3 (refusal)**: survived two retries. Rephrase to remove ambiguous or restricted phrasing, or switch channels. Do not loop.
- **Exit 4 (quota or 5h guard)**: stop calling Gemini web until the quota window resets (stderr prints the reset timestamp when the account returns `reset_at`, and emits threshold warnings at `>=50%`, `>=75%`, and `>=90%` usage).
- **Exit 5 (timeout)**: raise `--timeout` (especially for `--mode video`) and re-run in the background. Note that a timed-out video call may still finish on the server and appear in web history (`[from library source]`).
- **Exit 6 (model unavailable, unsupported capability, or silent fallback)**: check stderr. If the model is not listed on the account, run `--list-models`. The label check only runs in `chat` mode for `hydrogen` and `neon`; for image, video and other models stderr prints the observed label and the saved files are kept.
- **Exit 8 (server error burst)**: survived two retries. Wait and try later or switch channels.
