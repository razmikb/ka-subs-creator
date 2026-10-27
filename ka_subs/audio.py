"""Audio work with ffmpeg: convert, measure, find pauses, cut into parts (PLAN.md §3.1, §3.6)."""
import math
import re
from pathlib import Path

from .common import clock, run

# Parts of 20 minutes or less. Longer pieces made Gemini skip speech or fail (PLAN.md §2.3).
MAX_PART_SECONDS = 20 * 60

# Where a cut may land around its ideal spot; the nearest pause inside this window wins.
CUT_WINDOW_SECONDS = 2 * 60

# A pause: quieter than -35 dB for at least 0.3 s, the breath between two sentences.
SILENCE_NOISE = "-35dB"
SILENCE_MIN_SECONDS = 0.3

# Small mono Opus that Gemini and the aligner both take, about 7.5 MB per 20 minutes.
OPUS_ARGS = ["-ac", "1", "-c:a", "libopus", "-b:a", "48k"]


def to_opus(source: Path, out: Path) -> None:
    run(["ffmpeg", "-hide_banner", "-y", "-i", str(source), *OPUS_ARGS, str(out)])


def seconds(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(path)]).stdout
    return float(out.strip())


def find_silences(path: Path) -> list[tuple[float, float]]:
    """(start, end) of every pause, from ffmpeg's silencedetect."""
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
               f"silencedetect=noise={SILENCE_NOISE}:d={SILENCE_MIN_SECONDS}",
               "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(starts, ends))


def choose_cuts(duration: float, silences: list[tuple[float, float]]) -> list[dict]:
    """Where to cut: equal parts no longer than MAX_PART_SECONDS, each cut moved to the
    middle of the nearest pause. Returns [{"at": seconds, "pause": bool}, ...]."""
    parts = max(1, math.ceil(duration / MAX_PART_SECONDS))
    cuts = []
    for i in range(1, parts):
        ideal = duration * i / parts
        near = [(abs((a + b) / 2 - ideal), (a + b) / 2) for a, b in silences
                if abs((a + b) / 2 - ideal) <= CUT_WINDOW_SECONDS]
        if near:
            cuts.append({"at": min(near)[1], "pause": True})
        else:
            cuts.append({"at": ideal, "pause": False})
    return cuts


def cut(full: Path, start: float, end: float, out: Path) -> None:
    run(["ffmpeg", "-hide_banner", "-y", "-i", str(full),
         "-ss", f"{start:.2f}", "-to", f"{end:.2f}", *OPUS_ARGS, str(out)])


def write_parts(full: Path, folder: Path) -> list[Path]:
    """part1.opus, part2.opus... in the folder. A short video is one part: a copy of full.opus."""
    existing = sorted(folder.glob("part*.opus"), key=lambda p: int(p.stem[4:]))
    if existing:
        return existing
    duration = seconds(full)
    cuts = choose_cuts(duration, find_silences(full) if duration > MAX_PART_SECONDS else [])
    edges = [0.0] + [c["at"] for c in cuts] + [duration]
    parts = []
    for i in range(len(edges) - 1):
        out = folder / f"part{i + 1}.opus"
        cut(full, edges[i], edges[i + 1], out)
        parts.append(out)
        if len(edges) > 2:
            print(f"  part{i + 1}.opus  {clock(edges[i])} → {clock(edges[i + 1])}")
    for c in cuts:
        if not c["pause"]:
            print(f"  WARNING: no pause near {clock(c['at'])}, cut there anyway. "
                  "A word may be split at that point.")
    return parts
