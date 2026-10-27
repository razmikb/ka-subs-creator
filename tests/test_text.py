"""The reply cleaner and the joiner."""
import pytest

from ka_subs.clean import clean_transcript
from ka_subs.common import Stop
from ka_subs.join import join_parts


def test_clean_drops_markdown_and_empty_lines():
    reply = "```\n# სათაური\n\n- პირველი   წინადადება.\n* **მეორე** __წინადადება__.\n```\n"
    assert clean_transcript(reply) == ["სათაური", "პირველი წინადადება.", "მეორე წინადადება."]


def test_clean_keeps_double_dash_of_restarted_sentence():
    assert clean_transcript("ამ ხანაში -- დაახლოებით 1970-იანებში") == \
        ["ამ ხანაში -- დაახლოებით 1970-იანებში"]


def test_join_reports_pace_and_seams():
    one = "პირველი ნაწილი.\nბოლო წინადადება."
    two = "მეორე ნაწილი იწყება."
    lines, notes = join_parts([(one, 60), (two, 60)])
    assert lines == ["პირველი ნაწილი.", "ბოლო წინადადება.", "მეორე ნაწილი იწყება."]
    assert "LOW" in notes[0]  # 4 words a minute
    assert any("seam 1→2" in n for n in notes)


def test_join_refuses_an_empty_part():
    with pytest.raises(Stop):
        join_parts([("```\n```", 60)])
