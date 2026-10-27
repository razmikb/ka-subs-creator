"""Building, writing and reading subtitles."""
from ka_subs.srt import build_cues, parse_srt, split_words, stamp, to_srt, wrap


def test_stamp_format():
    assert stamp(0) == "00:00:00,000"
    assert stamp(3725.4567) == "01:02:05,457"


def test_split_words_keeps_sentence_and_attaches_dash():
    words, line_of = split_words(["ერთი ორი --", "სამი"])
    assert words == ["ერთი", "ორი --", "სამი"]
    assert line_of == [0, 0, 1]


def test_new_sentence_starts_a_new_subtitle():
    words, line_of = split_words(["ა ბ.", "გ დ."])
    cues = build_cues(words, line_of, [(0, 1), (1, 2), (3, 4), (4, 5)])
    assert [(c["start"], c["end"], c["text"]) for c in cues] == \
        [(0, 2, "ა ბ."), (3, 5, "გ დ.")]


def test_long_sentence_splits_at_seven_seconds():
    words, line_of = split_words(["ა ბ გ დ ე"])
    times = [(i * 2.0, i * 2.0 + 1.5) for i in range(5)]  # 0–1.5, 2–3.5, ... 8–9.5
    cues = build_cues(words, line_of, times)
    assert [c["text"] for c in cues] == ["ა ბ გ", "დ ე"]  # "დ" would end at 7.5 s


def test_long_sentence_splits_at_two_lines_of_text():
    word = "ლოგარითმი"  # 9 letters
    words, line_of = split_words([" ".join([word] * 12)])
    cues = build_cues(words, line_of, [(i, i + 0.4) for i in range(12)])
    assert all(len(c["text"].replace("\n", " ")) <= 84 for c in cues)
    assert all(len(row) <= 42 for c in cues for row in c["text"].split("\n"))


def test_short_subtitle_stays_a_second_unless_the_next_starts():
    words, line_of = split_words(["ა.", "ბ.", "გ."])
    cues = build_cues(words, line_of, [(0, 0.2), (0.5, 0.7), (5, 5.2)])
    assert [c["end"] for c in cues] == [0.5, 1.5, 6.0]


def test_wrap_makes_two_even_lines():
    text = "მოდი შევაბიჯოთ ლოგარითმების სამყაროში და გავიგოთ რას წარმოადგენენ"
    top, bottom = wrap(text).split("\n")
    assert abs(len(top) - len(bottom)) < 12
    assert wrap("მოკლე") == "მოკლე"


def test_write_then_read_back():
    cues = [{"start": 0.352, "end": 2.522, "text": "ერთი\nორი"},
            {"start": 2.522, "end": 4.997, "text": "სამი"}]
    back = [(round(c["start"], 3), round(c["end"], 3), c["text"]) for c in parse_srt(to_srt(cues))]
    assert back == [(0.352, 2.522, "ერთი ორი"), (2.522, 4.997, "სამი")]
