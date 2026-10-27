"""The whole job for one video, and for a batch: audio → words → times → .srt → checks.

Everything for a video lives in <root>/<video id>/ on Google Drive. Every step reuses
its file if it's already there, so a re-run never repeats work or spends a Gemini request
twice. To redo a step, delete its file. Finished .srt files are also copied to
<root>/subtitles/.
"""
import json
import re
from pathlib import Path

from . import audio, check, gemini, srt, youtube
from .clean import clean_transcript
from .common import Stop, clock
from .join import join_parts, part_text
from .prompt import PROMPT

_AUDIO_EXTS = {".webm", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".mp4", ".aac", ".flac"}


def run_batch(text: str, root: Path, api_key: str | None, model: str) -> None:
    """Every video in the links text; keeps going past a bad one, then prints a summary."""
    try:
        urls = youtube.expand(text)
    except Stop as exc:
        print(f"STOPPED: {exc}")
        return
    print(f"{len(urls)} video(s).\n")
    state = {"quota_out": not api_key}
    results = []
    for i, url in enumerate(urls, 1):
        print(f"━━ {i}/{len(urls)}  {url}")
        try:
            status, note = process(url, root, api_key, model, state)
        except Stop as exc:
            status, note = "failed", str(exc)
            print(f"  STOPPED: {exc}")
        results.append((url, status, note))
        print()

    print("━━ SUMMARY")
    labels = {"done": "Done", "listen": "Done, needs a listen", "waiting": "Waiting for you",
              "skipped": "Skipped", "failed": "Failed"}
    for key, label in labels.items():
        rows = [(u, n) for u, s, n in results if s == key]
        if rows:
            print(f"\n{label} ({len(rows)}):")
            for u, n in rows:
                print(f"  {u}  {n}")


def process(url: str, root: Path, api_key: str | None, model: str, state: dict) -> tuple[str, str]:
    """One video. Returns (status, short note) where status is done / listen / waiting /
    skipped; a problem raises Stop."""
    vid = youtube.video_id(url)
    if vid is None:
        raise Stop(f"Not a single-video link: {url}")
    folder = root / vid
    folder.mkdir(parents=True, exist_ok=True)

    title = vid
    try:
        meta = youtube.info(url)
        title = meta["title"]
        print(f"  {title}")
        if meta["subs"] == "human":
            print("  This video already has Georgian subtitles. Skipped.")
            return "skipped", "already has Georgian subtitles"
        if meta["subs"] == "auto":
            print("  (It has YouTube's automatic Georgian captions only. Making proper ones.)")
    except youtube.Blocked:
        if not _have_audio(folder):
            raise Stop(_blocked_help(url, vid)) from None
        print("  YouTube blocked the details, but the audio is already here. Carrying on.")

    full = _get_audio(url, folder)
    duration = audio.seconds(full)
    print(f"  Audio: {clock(duration)}")

    lines = _get_transcript(folder, vid, full, api_key, model, state)
    if lines is None:
        return "waiting", f"transcript by hand: see My Drive/{root.name}/{vid}/NEXT_STEPS.txt"

    return _make_subtitles(folder, vid, title, url, full, duration, lines, root)


def _have_audio(folder: Path) -> bool:
    return (folder / "full.opus").exists() or _uploaded_audio(folder) is not None


def _uploaded_audio(folder: Path) -> Path | None:
    """An audio file downloaded by yt-dlp here, or uploaded by hand under any name."""
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() in _AUDIO_EXTS and p.name != "full.opus" \
                and not re.match(r"(part\d+|gap_.*)\.opus$", p.name):
            return p
    return None


def _get_audio(url: str, folder: Path) -> Path:
    full = folder / "full.opus"
    if full.exists():
        return full
    source = _uploaded_audio(folder)
    if source is None:
        print("  Downloading the audio...")
        try:
            source = youtube.download_audio(url, folder)
        except youtube.Blocked:
            raise Stop(_blocked_help(url, folder.name)) from None
    audio.to_opus(source, full)
    source.unlink()
    return full


def _blocked_help(url: str, vid: str) -> str:
    return (f"YouTube refused to send this video to Google's servers. Download the audio on "
            f"your laptop instead:\n"
            f"    1. In a terminal:  yt-dlp -f bestaudio -o \"{vid}.%(ext)s\" -- {url}\n"
            f"    2. Upload that file into Google Drive: My Drive / ka-subs / {vid} /\n"
            f"    3. Run the notebook again.")


def _get_transcript(folder: Path, vid: str, full: Path, api_key: str | None, model: str,
                    state: dict) -> list[str] | None:
    """The whole transcript as sentences, or None while parts still wait for a manual reply."""
    joined = folder / f"{vid}.txt"
    if joined.exists():
        print(f"  Using {joined.name} (delete it to rebuild it from the parts).")
        return clean_transcript(joined.read_text(encoding="utf-8"))

    parts = audio.write_parts(full, folder)
    missing = []
    for n, part in enumerate(parts, 1):
        if part_text(folder, n):
            continue
        if not state["quota_out"]:
            print(f"  Gemini is writing the words of part {n} of {len(parts)}...")
            try:
                text = gemini.transcribe(part, api_key, model)
                (folder / f"part{n}.txt").write_text(text, encoding="utf-8")
                continue
            except gemini.QuotaUsedUp as exc:
                print(f"  {exc}")
                state["quota_out"] = True
        missing.append(n)

    if missing:
        (folder / "prompt.txt").write_text(PROMPT, encoding="utf-8")
        steps = _next_steps(vid, missing)
        (folder / "NEXT_STEPS.txt").write_text(steps, encoding="utf-8")
        print("  " + steps.replace("\n", "\n  "))
        return None

    texts = [(part_text(folder, n).read_text(encoding="utf-8"), audio.seconds(p))
             for n, p in enumerate(parts, 1)]
    lines, notes = join_parts(texts)
    for note in notes:
        print(f"  {note}")
    if len(parts) > 1:
        print("  If a seam shows a sentence twice or cut in half, fix it in "
              f"{joined.name} and run again.")
    joined.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def _next_steps(vid: str, missing: list[int]) -> str:
    files = ", ".join(f"part{n}.opus → part{n}.txt" for n in missing)
    return (f"WHAT TO DO NEXT: write the words by hand in Google AI Studio\n"
            f"Folder: My Drive / ka-subs / {vid} /\n"
            f"1. Open aistudio.google.com. Start ONE NEW CHAT for each part.\n"
            f"2. Attach the part's audio, paste everything from prompt.txt, run.\n"
            f"3. Save the reply in the folder with the matching name: {files}\n"
            f"   (AI Studio's own .md download is fine too, named part1.md etc.)\n"
            f"4. Run the notebook again.\n")


def _make_subtitles(folder: Path, vid: str, title: str, url: str, full: Path,
                    duration: float, lines: list[str], root: Path) -> tuple[str, str]:
    from .align import align_words

    words, line_of = srt.split_words(lines)
    print(f"  Timing {len(words)} words ({len(words) / (duration / 60):.0f} words/min)...")
    times = align_words(full, words)
    (folder / "words.json").write_text(json.dumps(
        [{"w": w, "line": li, "start": s, "end": e}
         for w, li, (s, e) in zip(words, line_of, times)], ensure_ascii=False), encoding="utf-8")

    cues = srt.build_cues(words, line_of, times)
    text = srt.to_srt(cues)
    (folder / f"{vid}.srt").write_text(text, encoding="utf-8")
    out_dir = root / "subtitles"
    out_dir.mkdir(exist_ok=True)
    name = f"{vid} {_safe(title)}.srt" if title != vid else f"{vid}.srt"
    (out_dir / name).write_text(text, encoding="utf-8")
    print(f"  {len(cues)} subtitles → My Drive/{root.name}/subtitles/{name}")

    notes = check.review(cues, duration, url)
    if not notes:
        print("  Checks: nothing to flag.")
        return "done", name
    print(f"  {len(notes)} place(s) to listen to:")
    for note in notes:
        print(f"   • {note}")
    print("  (A gap is often just the narrator drawing quietly. Skipped speech is what to "
          "catch. If speech is missing, use the 'Fill a gap' cell.)")
    return "listen", f"{len(notes)} place(s) to listen to"


def _safe(title: str) -> str:
    """A title that's safe as a file name on Windows and Drive."""
    return re.sub(r'[\\/:*?"<>|]+', "", title).strip()[:80]
