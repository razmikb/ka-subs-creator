"""Small things every step uses: the one error type, time display, running a program."""
import subprocess


class Stop(Exception):
    """A problem the owner has to act on. The message is shown as-is, never a stack trace."""


def clock(seconds: float) -> str:
    """12:34 or 1:02:03, the way the YouTube player shows a time."""
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def from_clock(text: str) -> float:
    """Seconds from "1:23", "1:02:03" or "83"."""
    try:
        parts = [float(x) for x in text.strip().split(":")]
    except ValueError:
        raise Stop(f"{text!r} is not a time. Write it like 1:23.") from None
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a program and return its output; a failure raises Stop with its last words."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise Stop(f"{cmd[0]} is not installed.") from None
    if done.returncode != 0:
        lines = [x for x in done.stderr.splitlines() if x.strip()]
        raise Stop(f"{cmd[0]} failed: {lines[-1] if lines else 'no explanation'}")
    return done
