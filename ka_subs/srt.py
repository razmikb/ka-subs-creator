"""Word times → subtitle lines → .srt text, and reading an .srt back (PLAN.md §3.5)."""
import re

# A subtitle shows at most 2 lines of about 42 characters, the usual readable size,
# and stays at most 7 seconds. A new subtitle starts at every new sentence.
LINE_CHARS = 42
MAX_LINES = 2
MAX_SECONDS = 7.0

# A subtitle stays on screen at least this long (if the next one doesn't start sooner).
MIN_SECONDS = 1.0


def _sounds(token: str) -> bool:
    return any(ch.isalnum() for ch in token)


def split_words(lines: list[str]) -> tuple[list[str], list[int]]:
    """Every word, and the transcript line (sentence) it came from. A token with no letter
    or digit, like the "--" of a restarted sentence, rides along with a word of its
    sentence (the one before it, else the one after), since it makes no sound to time."""
    words, line_of = [], []
    for i, line in enumerate(lines):
        pending = []
        for w in line.split():
            if _sounds(w):
                words.append(" ".join(pending + [w]))
                line_of.append(i)
                pending = []
            elif words and line_of[-1] == i:
                words[-1] += " " + w
            else:
                pending.append(w)
        if pending and words:
            words[-1] += " " + " ".join(pending)
    return words, line_of


def spoken(word: str) -> str:
    """The part of a word from split_words the aligner can hear: one token, no spaces."""
    return next(t for t in word.split() if _sounds(t))


def build_cues(words: list[str], line_of: list[int],
               times: list[tuple[float, float]]) -> list[dict]:
    """[{"start", "end", "text"}] from words and their (start, end) times."""
    groups, cur = [], []
    for k in range(len(words)):
        if cur and (line_of[k] != line_of[cur[0]]
                    or times[k][1] - times[cur[0]][0] > MAX_SECONDS
                    or len(" ".join(words[j] for j in cur + [k])) > LINE_CHARS * MAX_LINES):
            groups.append(cur)
            cur = []
        cur.append(k)
    if cur:
        groups.append(cur)

    cues = [{"start": times[g[0]][0], "end": times[g[-1]][1],
             "text": wrap(" ".join(words[j] for j in g))} for g in groups]
    for a, b in zip(cues, cues[1:]):
        a["end"] = max(a["end"], min(a["start"] + MIN_SECONDS, b["start"]))
    if cues:
        cues[-1]["end"] = max(cues[-1]["end"], cues[-1]["start"] + MIN_SECONDS)
    return cues


def wrap(text: str, width: int = LINE_CHARS) -> str:
    """One line if it fits, else two lines split at the space that makes them most even."""
    if len(text) <= width:
        return text
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    if not spaces:
        return text
    best = min(spaces, key=lambda i: abs(i - len(text) / 2))
    return text[:best] + "\n" + text[best + 1:]


def stamp(t: float) -> str:
    """SRT time: HH:MM:SS,mmm."""
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def to_srt(cues: list[dict]) -> str:
    return "".join(f"{n}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}\n\n"
                   for n, c in enumerate(cues, 1))


def parse_srt(text: str) -> list[dict]:
    """[{"start", "end", "text"}] from SRT text; lines of one subtitle joined by a space."""
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        m = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", block)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append({"start": start, "end": end, "text": " ".join(block[m.end():].split())})
    return cues
