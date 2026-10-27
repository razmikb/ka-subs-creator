# ka-subs-creator — Georgian subtitles for Khan Academy videos that have none

A build guide for an AI coding assistant. Read all of it before writing code.

## 0. What this tool does, in one paragraph

Some Georgian Khan Academy videos on YouTube have no subtitles. This tool makes an `.srt`
subtitle file for such a video: it downloads the audio, gets a word-for-word Georgian transcript
from Gemini, then gives every word an exact time using **forced alignment**, a separate model
that listens to the audio and lines up the known text with it. The result is a normal `.srt`
that plays in sync with the video.

The method is copied from a working tool in another project (TVNAIA Online, `fetcher/audio_subs.py`
+ `fetcher/audio_subs_colab.ipynb`). It was measured there and works. Sections 2 and 3 carry
over everything learned, so **don't re-run the experiments that are already settled**.

## 1. Before you start, confirm with the owner

The owner is a non-developer. Ask these in plain language, one short list, before building.
Defaults are in brackets; use them if the owner has no preference.

1. **Is the speech in the videos Georgian?** [yes: Georgian-dubbed or Georgian-recorded
   videos]. If the videos are in **English** and they want Georgian subtitles, it becomes a
   *translation* job: transcribe English → align English (`language="eng"`) → translate each
   cue's text, keeping the times. Same pipeline otherwise; build Georgian first.
2. **Where do the videos come from?** [a YouTube channel or playlist URL, or a list of video
   links in a text file].
3. **What happens to the `.srt` files?** [saved into a folder, one per video, named by video ID +
   title. Uploading them to YouTube is the channel owner's job, done by hand. Don't build
   YouTube upload: it needs the channel's own login].
4. **How will the transcript step run?**
   - **A. Manual, through Google AI Studio in the browser** (free, no API quota used; the owner
     pastes a prompt and saves the reply, once per video). Fine for a few videos.
   - **B. Automatic, through the Gemini API** with a free API key from aistudio.google.com.
     The free tier is limited (about 20 requests a day per model at the time of writing; check
     the current limit, don't promise a number). Good for batches.
   [Build **B** with **A** as a fallback when the daily quota runs out. Both use the same prompt.]
5. **Which computer runs it?** [the owner's Windows PC]. This decides where the timing step
   runs; see §3.4.

### 1a. Owner's answers and decisions (2026-10-27)

- Speech is **Georgian**. Videos come from **YouTube** links (video, playlist or channel).
  `.srt` files go to a folder; no YouTube upload. Gemini: **API with AI Studio as fallback**.
- **Everything runs in one Google Colab notebook** (`ka_subs_colab.ipynb`): download, Gemini,
  timing, SRT, checks. The owner chose this over the laptop because local CPU timing was too
  slow (i7-8665U: 6.5 min for a 5-min video). The local aligner setup was removed.
  Work folders live on Google Drive (`My Drive/ka-subs/<id>/`), finished files in
  `My Drive/ka-subs/subtitles/`. The Gemini key is in Colab **Secrets** (`GEMINI_API_KEY`),
  not `.env`. The notebook clones the code from the owner's **public GitHub repo**.
- **Go/no-go (§5 step 1) PASSED** on YnNjBBHRANk (logarithms, 5:10, real Georgian subs):
  cue starts median 0.23 s off, 97% within 1 s, no drift per quarter. Digits ("16-სა") vs
  spoken words ("თექვსმეტისა") made **no difference**, so Gemini may write digits.
  It has ~120 words/min; the low-pace warning is set at 60 until more videos are measured.
- **Khan Academy subtitle guidelines** (support.khanacademy.org article 226430248) are in the
  Gemini prompt (`ka_subs/prompt.py`): no fillers, `--` for restarts, 0–9 as words and 10+ as
  digits, maths as spoken words. They set no line length, so lines are 2 × 42 chars, 7 s max.
- Model: `gemini-3.8-flash` via the `interactions` API (checked on ai.google.dev, 2026-10-27).
  Free-tier limits are only shown in AI Studio.
- **First real video done end to end (2026-10-27):** wY2L98eHShE (enzyme cofactors, 10:22).
  Gemini API: 126 words/min, 1306 words → 137 subtitles, checks flagged nothing. The owner
  watched it with the `.srt` and uploaded it: wording and timing right, line size accepted.
- YouTube download from Colab is **sometimes blocked** ("confirm you're not a bot") and
  sometimes works for the same video; cell 2 then shows an upload button for audio fetched
  on the laptop. yt-dlp warns that no JavaScript runtime (deno) is installed; harmless so far.
- Lessons: the aligner counts words by splitting on spaces, so each word sent to it must be
  one token (`srt.spoken`). Re-running cell 1 must drop loaded `ka_subs` modules, or Colab
  keeps running the old code.
- Left from §5: a README for the owner (the `.bat` is not needed now that it runs in Colab).

## 2. What is already known (settled, don't re-test)

### 2.1 Why the job is split in two
- **Gemini's own timestamps drift.** Asking Gemini for a timed transcript gives times that slide
  further off as the video goes on. Never use Gemini for times.
- **Even spreading of text over the video length** (what "TXT to SRT" websites do) is wrong
  wherever the speaker speeds up, slows down or pauses. That's worse for Khan Academy, where the
  narrator pauses while drawing.
- **So:** Gemini writes **only the words** (no timestamps at all), and **forced alignment** gives the
  times.

### 2.2 The forced aligner: measured, works for Georgian
- Library: **ctc-forced-aligner** — https://github.com/MahmoudAshraf97/ctc-forced-aligner
  (Meta's MMS model, 1,100+ languages; model `MahmoudAshraf/mms-300m-1130-forced-aligner`,
  ~1.2 GB, downloaded once).
- Georgian works through **romanization**: `preprocess_text(..., romanize=True, language="kat")`.
- Measured against YouTube's own captions on a 45-minute Georgian TV news bulletin:
  **median error 0.06 s per word, 99.2% of words within 1 s, no drift** (the same error in every
  quarter of the video).
- With 5% of the words removed and a 60-second stretch deleted from the text, the result was
  still 0.06 s median. Missing text barely hurts the words around it. **But** a few words right
  next to a long missing stretch were pulled up to ~49 s off. That's why the check step (§3.5)
  exists.
- Speed: on a 2013 laptop CPU (i5-4300U), about **1 minute of work per minute of audio**. On
  Google Colab's free T4 GPU, a 45-minute file took **51 seconds**.

### 2.3 Gemini transcripts: the weak link
- The Georgian text is good, but **Gemini sometimes silently skips speech**. A 51-minute file lost
  2m41s in the middle. Another reply stopped mid-word at minute 8 and dropped 17 minutes. There's
  no error, just missing text.
- Shorter pieces help: 20-minute pieces worked, and 27–28-minute pieces sometimes errored outright
  in AI Studio. **Cut audio into equal pieces of 20 minutes or less, each cut at a pause.** Most
  Khan Academy videos are under 20 minutes, so they usually go in as one piece.
- **Send audio only**, never the video or a YouTube link. Video makes Gemini also read about one
  frame a second, which costs far more and doesn't help the transcript.
- Use the prompt in §3.2. It was refined on real use: no music markers, no speaker names, no
  timestamps (they can't be aligned and only add noise).

## 3. The pipeline

One command-line tool, run per video or per list of videos. One work folder per video, e.g.
`work/<video_id>/`. **Every step can be re-run safely.** A step whose output file already exists
reuses it, unless asked to redo it.

### 3.1 Get the audio
- `yt-dlp -f bestaudio -o "work/<id>/source.%(ext)s" -- <url>` (the `--` stops a URL from being
  read as an option; also check the URL is a real YouTube video URL before passing it on).
- Convert to small mono Opus, which Gemini and the aligner both accept:
  `ffmpeg -i source.* -ac 1 -c:a libopus -b:a 48k full.opus` (about 7.5 MB per 20 minutes).
- Read the length with `ffprobe -v error -show_entries format=duration -of csv=p=0 full.opus`.
- **Check first whether the video already has subtitles** (`yt-dlp --list-subs`). If it has
  human-made Georgian subtitles, skip it and say so. If it has only auto-generated ones, ask the
  owner once what to do with those. Georgian auto-captions are usually poor.
- yt-dlp and ffmpeg are separate programs. Check they're installed and say exactly how to install
  them on Windows if not (`winget install yt-dlp.yt-dlp` / `winget install Gyan.FFmpeg`).

### 3.2 Get the words (Gemini)
If the audio is longer than 20 minutes, cut it into equal parts first (§3.6). Then, per part:

Prompt (from the working tool; only the first line is adapted):
```
This is the audio of a Georgian educational video (Khan Academy). Write a word-for-word transcript in Georgian.

Rules:
- Transcribe EVERYTHING that is said, from the first second to the last. Do not skip, shorten or summarise any part, even if it seems repetitive or unimportant.
- Write numbers, symbols and formulas as the words that are SPOKEN (e.g. "ორი x პლუს სამი", not "2x + 3").
- One sentence per line.
- No timestamps, no speaker names, no headings, no translation, no comments of your own.
- Plain text only, no markdown.
```

**Why the "spoken words" rule matters (new for Khan Academy, not tested in TVNAIA):** the aligner
matches *letters to sounds*. Digits, `+`, `=`, `²`, `√`, fractions and Latin variable names
don't sound like their written form, and the romanizer may drop them or say them wrong. Then
those words get no time or a wrong one. Maths videos are full of these. Test this early (§5):
take one maths video, compare a transcript with digits against one with spoken words, and keep
whichever times better. If spoken words win but the owner wants "2x + 3" on screen, keep two
texts: the spoken one for aligning, and a display one swapped in per cue afterwards. Build that
only if the test shows it's needed.

- **Mode B (API):** use the official `google-genai` Python package; upload the audio file, send
  the prompt, save the reply as `part1.txt` etc. Read the API key from a `.env` file
  (`GEMINI_API_KEY=`). **Never write the key into code, a log or git.** Add `.env` to
  `.gitignore` and ship a `.env.example` with the name only. Pick a current Gemini model that
  accepts audio, checked against Google's docs at build time, not from memory. When the API says the
  quota is used up, stop cleanly and tell the owner to switch to mode A or wait until tomorrow.
- **Mode A (manual):** write `prompt.txt` and a `NEXT_STEPS.txt` in the folder: "open
  aistudio.google.com, one NEW chat per part, attach `part1.opus`, paste `prompt.txt`, run, save
  the reply here as `part1.txt` (a `.md` download is fine too)". Then wait for the owner.

**Clean the reply** before use: drop code fences (```` ``` ````), leading `#` headings, `-`/`*`/`•`
bullets and `**`/`__`, collapse spaces, drop empty lines.

**Sanity check per part:** count words per minute of audio. Georgian TV news measured 105–113
words/min, and below 80 meant Gemini had shortened it. **Khan Academy narration is slower, with
pauses while drawing**, so measure a few real videos first and set this threshold from them.
Don't reuse 80 blindly.

### 3.3 Join the parts
Concatenate the parts' lines in order into `<id>.txt` (make sure each part ends with a newline).
Print each seam (last line of part N, first line of part N+1) so a sentence doubled or cut in half
at a cut is visible.

### 3.4 Get the times (forced alignment)
Align the **whole** `full.opus` (not the parts) against the joined text, so times run from the
video's own 0:00 and the cuts can't introduce a jump.

Proven code, from the working Colab notebook:
```python
import torch
from ctc_forced_aligner import (load_audio, load_alignment_model, generate_emissions,
                                preprocess_text, get_alignments, get_spans, postprocess_results)

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
model, tok = load_alignment_model(device, dtype=dtype)
wav = load_audio("full.opus", model.dtype, model.device)
emissions, stride = generate_emissions(model, wav, batch_size=16)

def align(words):
    tokens, text_starred = preprocess_text(" ".join(words), romanize=True, language="kat")
    segments, scores, blank = get_alignments(emissions, tokens, tok)
    spans = get_spans(tokens, segments, blank)
    return postprocess_results(text_starred, spans, stride, scores)  # [{"start", "end", "text"}, ...] per word
```
(The CPU branch is untested. The notebook only ran on `cuda`/`float16`. Verify it on the owner's
machine.)

**Where it runs:** Khan Academy videos are short, so **running locally on CPU is probably fine**
(a 10-minute video ≈ 10 minutes of waiting on an old laptop, less on a newer PC). That avoids
the manual Colab upload/download that TVNAIA needs. Install PyTorch CPU + ctc-forced-aligner in
the project's own virtual environment. If it's too slow on the owner's PC, also ship a Colab
notebook (based on TVNAIA's `fetcher/audio_subs_colab.ipynb`) as an option. Measure first.

### 3.5 Build the SRT, then check it
Turn word times into subtitle lines (from the working notebook):
- a new line starts at each new transcript sentence, or when the line would run longer than
  **7 seconds**, or longer than **80 characters**. For an educational video, consider ~42 chars
  per line, wrapped onto two lines, which is the usual readable subtitle size. Ask the owner
  after they see a sample.
- each line's start = its first word's start, end = its last word's end.
- SRT time format `HH:MM:SS,mmm`, UTF-8 file.

**Check before calling it done** (the step that catches Gemini's skipped speech):
- the last line ends within ~60 s of the audio's end; otherwise the end is probably missing;
- no two lines overlap;
- every **gap > 8 s** between lines, listed with the line before and after and a YouTube link a
  few seconds before it (`<url>&t=<seconds-5>s`). In a Khan video many gaps are just the narrator
  drawing quietly, so the owner listens and decides;
- every **single line stretched > 8 s**. This is the other sign of missing text: the aligner smeared
  the words over speech that isn't in the transcript;
- the words-per-minute check from §3.2.

If something was skipped: cut that stretch out of the audio
(`ffmpeg -ss <from> -to <to> -i full.opus -c copy gap.opus`), transcribe just that piece, paste
the text in at the right place in `<id>.txt`, re-run 3.4–3.5. That fixed the 2m41s hole in TVNAIA.
Make it one command.

### 3.6 Cutting long audio at pauses (only for videos > 20 min)
- Number of parts = `ceil(length / 20 min)`, equal lengths.
- Find pauses with `ffmpeg -i full.opus -af silencedetect=noise=-35dB:d=0.3 -f null -`
  (parse `silence_start:` / `silence_end:` from stderr). A 0.3 s breath is enough; a cut in
  mid-word loses that word on both sides.
- Move each cut to the middle of the pause nearest its ideal spot, within ±2 minutes. If there's none,
  cut at the ideal spot and print a warning naming the time.
- Write each part with `ffmpeg -i full.opus -ss <a> -to <b> -ac 1 -c:a libopus -b:a 48k partN.opus`.

## 4. How it should feel to the owner

- One entry point, e.g. `python ka_subs.py <youtube-url>` or `python ka_subs.py --list videos.txt`,
  plus a `.bat` file to double-click on Windows.
- Plain-language messages: what it's doing, what's next, and on any failure *what to do about it*
  (not a stack trace). Wrap failures in one error type whose message is shown as-is.
- A batch keeps going past one bad video and prints a summary at the end: done / needs a listen /
  failed (why).
- A `README.md` written for a non-developer: install steps for Windows, one command copy-pasteable
  per block, and what each check message means.

## 5. Build order (stop and show the owner after each)

1. **Go/no-go on ONE video that already HAS correct Georgian subtitles** (so the right answer is
   known). Use its subtitle text as the transcript, align it, and compare word/line start times with
   the real subtitles (median error, % within 1 s, error per quarter: TVNAIA's notebook cell 4
   does exactly this from a `.json3`). Pass = median under ~0.5 s and no drift. Do this on a
   **maths** video so the digits/symbols question (§3.2) is answered at the same time.
2. Audio download + transcript (mode A first: no key needed, so it's quick to try).
3. Alignment + SRT + check on one video with no subtitles. The owner watches it with the `.srt`
   loaded in a player (VLC, or YouTube Studio's preview) and reports.
4. Mode B (API) + batch over a list.
5. README + `.bat`.

## 6. Tests

Write unit tests for the parts that need no network or model: the reply cleaner, the cut chooser
(given a length + pauses), the SRT writer (time format, line splitting), the SRT reader, and the
checker (gaps, stretches, overlaps, missing end). TVNAIA's `fetcher/test_audio_subs.py` is a
model for these. Don't call Gemini or download models in tests.

## 7. Don'ts

- Don't use Gemini (or any transcriber's) timestamps, or even-spreading of text.
- Don't send video or YouTube links to Gemini, only audio.
- Don't build a paid speech-to-text option (Google Cloud etc.). It must stay free.
- Don't upload to YouTube or log in to anything on the owner's behalf.
- Don't commit `.env`, API keys, downloaded audio or work folders (put them in `.gitignore`).

## 8. Reference: the original tool

In `D:\coding-projects\TVNAIA_Online\` (read-only; don't edit that project from here):
- `fetcher/audio_subs.py`: prepare / join / check steps (cutting, cleaning, SRT checks)
- `fetcher/audio_subs_colab.ipynb`: the alignment + SRT code and the accuracy test
- `fetcher/test_audio_subs.py`: its tests
- `planning/admin/1-IN-PROGRESS_AUDIO_SUBTITLES_PLAN.md`: the full history and measurements
