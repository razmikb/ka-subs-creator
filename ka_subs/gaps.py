"""Fill a stretch of speech Gemini skipped, in one go (PLAN.md §3.5): cut that piece of
audio, get its words, put them into the transcript at the right place, redo the subtitles."""
import json
import shutil
from pathlib import Path

from . import audio, gemini
from .clean import clean_transcript
from .common import Stop, clock
from .pipeline import process
from .prompt import PROMPT


def insert_at(lines: list[str], words: list[dict], start: float) -> int:
    """Where the gap's sentences go: after the last transcript line that ends before the
    gap starts (half a second of slack)."""
    ends = {}
    for w in words:
        ends[w["line"]] = w["end"]
    before = [li for li, end in ends.items() if end <= start + 0.5]
    return max(before) + 1 if before else 0


def fill_gap(url: str, start: float, end: float, root: Path, api_key: str | None,
             model: str) -> None:
    from .youtube import video_id

    vid = video_id(url)
    folder = root / (vid or "")
    joined = folder / f"{vid}.txt"
    if not vid or not joined.exists() or not (folder / "words.json").exists():
        raise Stop("Make the subtitles for this video first, then fill its gaps.")

    tag = f"gap_{int(start)}-{int(end)}"
    piece, reply = folder / f"{tag}.opus", folder / f"{tag}.txt"
    if not piece.exists():
        audio.cut(folder / "full.opus", start, end, piece)
    if not reply.exists():
        if not api_key:
            (folder / "prompt.txt").write_text(PROMPT, encoding="utf-8")
            raise Stop(f"No Gemini key, so do this piece by hand: in AI Studio, attach "
                       f"{tag}.opus from My Drive/{root.name}/{vid}/, paste prompt.txt, and "
                       f"save the reply there as {tag}.txt. Then run this cell again.")
        print(f"  Gemini is writing the words of {clock(start)} → {clock(end)}...")
        reply.write_text(gemini.transcribe(piece, api_key, model), encoding="utf-8")

    new = clean_transcript(reply.read_text(encoding="utf-8"))
    if not new:
        raise Stop(f"{tag}.txt is empty: Gemini heard no speech there.")
    lines = clean_transcript(joined.read_text(encoding="utf-8"))
    words = json.loads((folder / "words.json").read_text(encoding="utf-8"))
    at = insert_at(lines, words, start)

    shutil.copy(joined, folder / f"{vid}.before-{tag}.txt")
    joined.write_text("\n".join(lines[:at] + new + lines[at:]) + "\n", encoding="utf-8")
    print(f"  Added {len(new)} sentence(s) to {joined.name}:")
    if at:
        print(f"    before: …{lines[at - 1][-70:]}")
    for line in new:
        print(f"    NEW:    {line[:70]}")
    if at < len(lines):
        print(f"    after:  {lines[at][:70]}…")
    print("  If the edges repeat words that were already there, delete them in that file "
          "and run the main cell again. The old version is kept as "
          f"{vid}.before-{tag}.txt.\n")
    process(url, root, api_key, model, {"quota_out": True})
