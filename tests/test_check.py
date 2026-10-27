"""The checks for skipped speech, and where a gap's words go back in."""
from ka_subs.check import review
from ka_subs.gaps import insert_at
from ka_subs.youtube import video_id

URL = "https://www.youtube.com/watch?v=YnNjBBHRANk"


def cue(start, end, text="ტექსტი"):
    return {"start": start, "end": end, "text": text}


def test_clean_subtitles_have_nothing_to_flag():
    assert review([cue(0, 3), cue(3.5, 6)], 30, URL) == []


def test_missing_end_is_flagged():
    notes = review([cue(0, 3)], 120, URL)
    assert len(notes) == 1 and "end may be missing" in notes[0]


def test_overlap_gap_and_stretch_are_flagged():
    notes = review([cue(0, 3), cue(2, 4), cue(14, 24)], 30, URL)
    assert any("overlap" in n for n in notes)
    assert any("Gap of 10 s" in n and "&t=0s" in n for n in notes)
    assert any("stretched over 10 s" in n for n in notes)


def test_listen_link_works_for_short_links_too():
    notes = review([cue(0, 3), cue(20, 22)], 30, "https://youtu.be/YnNjBBHRANk")
    assert "youtu.be/YnNjBBHRANk?t=0s" in notes[0]


def test_gap_words_go_after_the_line_that_ends_before_the_gap():
    words = [{"line": 0, "end": 5.0}, {"line": 1, "end": 10.0}, {"line": 2, "end": 40.0}]
    assert insert_at(["a", "b", "c"], words, 12.0) == 2
    assert insert_at(["a", "b", "c"], words, 1.0) == 0


def test_video_id_from_every_link_shape():
    for url in ["https://www.youtube.com/watch?v=YnNjBBHRANk&t=5s",
                "https://youtu.be/YnNjBBHRANk", "https://m.youtube.com/shorts/YnNjBBHRANk"]:
        assert video_id(url) == "YnNjBBHRANk"
    assert video_id("https://www.youtube.com/playlist?list=PL123") is None
