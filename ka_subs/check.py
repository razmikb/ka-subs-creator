"""Look the finished subtitles over for signs of skipped speech (PLAN.md §3.5)."""
from .common import clock

# A gap between subtitles longer than this is worth a listen: the narrator drawing
# quietly (fine) or speech Gemini skipped (not fine). Only a person can tell which.
GAP_SECONDS = 8.0

# One subtitle lasting longer than this means the aligner stretched words over speech
# that is missing from the text.
STRETCH_SECONDS = 8.0

# The subtitles should run to within this much of the audio's end.
END_SLACK_SECONDS = 60.0


def listen_at(url: str, seconds: float) -> str:
    """The video link that opens a few seconds before `seconds`."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}t={max(0, int(seconds) - 5)}s"


def review(cues: list[dict], duration: float, url: str) -> list[str]:
    """Everything worth a listen, as readable notes. An empty list means nothing to flag."""
    if not cues:
        return ["There are no subtitles at all."]
    cues = [{**c, "text": c["text"].replace("\n", " ")} for c in cues]
    notes = []
    if duration - cues[-1]["end"] > END_SLACK_SECONDS:
        notes.append(f"The subtitles stop at {clock(cues[-1]['end'])} but the audio runs to "
                     f"{clock(duration)}. The end may be missing.\n"
                     f"      listen: {listen_at(url, cues[-1]['end'])}")
    for a, b in zip(cues, cues[1:]):
        if b["start"] < a["end"] - 0.01:
            notes.append(f"Two subtitles overlap at {clock(b['start'])}.")
        if b["start"] - a["end"] > GAP_SECONDS:
            notes.append(f"Gap of {b['start'] - a['end']:.0f} s at "
                         f"{clock(a['end'])} → {clock(b['start'])}\n"
                         f"      before: …{a['text'][-70:]}\n"
                         f"      after:  {b['text'][:70]}…\n"
                         f"      listen: {listen_at(url, a['end'])}")
    for c in cues:
        if c["end"] - c["start"] > STRETCH_SECONDS:
            notes.append(f"One subtitle is stretched over {c['end'] - c['start']:.0f} s at "
                         f"{clock(c['start'])}: {c['text'][:70]}\n"
                         f"      listen: {listen_at(url, c['start'])}")
    return notes
