"""Choosing where to cut long audio."""
from ka_subs.audio import choose_cuts
from ka_subs.common import clock, from_clock


def test_clock_both_ways():
    assert clock(83) == "1:23" and clock(3723) == "1:02:03"
    assert from_clock("1:23") == 83 and from_clock("1:02:03") == 3723 and from_clock("45") == 45


def test_short_audio_is_not_cut():
    assert choose_cuts(19 * 60, [(100, 101)]) == []


def test_cut_moves_to_the_nearest_pause():
    # 30 minutes → 2 parts, ideal cut at 15:00; pauses at 14:00 and 15:30
    cuts = choose_cuts(30 * 60, [(839.8, 840.2), (929.8, 930.2)])
    assert cuts == [{"at": 930.0, "pause": True}]


def test_no_pause_nearby_cuts_at_the_ideal_spot():
    cuts = choose_cuts(30 * 60, [(100, 101)])
    assert cuts == [{"at": 900.0, "pause": False}]


def test_parts_are_equal():
    cuts = choose_cuts(50 * 60, [])
    assert [c["at"] for c in cuts] == [1000.0, 2000.0]
