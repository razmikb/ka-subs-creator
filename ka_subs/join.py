"""Glue the parts' texts into one transcript and show the seams (PLAN.md §3.3)."""
from pathlib import Path

from .clean import clean_transcript
from .common import Stop

# Words per minute below which Gemini probably shortened a part. Set from one video so far:
# the test video YnNjBBHRANk (logarithms) has about 120 words a minute in its real subtitles.
# Khan narrators pause to draw, so this stays well under that. Raise it once more videos are measured.
MIN_WORDS_PER_MINUTE = 60


def part_text(folder: Path, n: int) -> Path | None:
    """part{n}.txt, or AI Studio's own .md download of it."""
    for ext in (".txt", ".md"):
        if (folder / f"part{n}{ext}").exists():
            return folder / f"part{n}{ext}"
    return None


def join_parts(parts: list[tuple[str, float]]) -> tuple[list[str], list[str]]:
    """parts = [(reply text, audio seconds)] in order. Returns (all lines, notes to show)."""
    all_lines, notes, previous = [], [], None
    for n, (text, secs) in enumerate(parts, 1):
        lines = clean_transcript(text)
        if not lines:
            raise Stop(f"part{n}'s text is empty.")
        words = sum(len(x.split()) for x in lines)
        pace = words / (secs / 60)
        flag = "" if pace >= MIN_WORDS_PER_MINUTE else \
            "  ← LOW: Gemini may have shortened this part. Consider running it again."
        notes.append(f"part{n}: {len(lines)} lines, {words} words, {pace:.0f} words/min{flag}")
        if previous is not None:
            notes.append(f"  seam {n - 1}→{n}:  …{previous[-1][-70:]}")
            notes.append(f"              {lines[0][:70]}…")
        all_lines += lines
        previous = lines
    return all_lines, notes
