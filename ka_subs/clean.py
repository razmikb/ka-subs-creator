"""Gemini's reply as plain sentences (PLAN.md §3.2 "Clean the reply")."""
import re


def clean_transcript(text: str) -> list[str]:
    """One sentence per item: no code fences, headings, bold or bullets, no empty lines."""
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^[-*•]\s+", "", line)
        line = line.replace("**", "").replace("__", "")
        line = " ".join(line.split())
        if line:
            lines.append(line)
    return lines
