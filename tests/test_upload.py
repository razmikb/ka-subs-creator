"""When YouTube blocks Colab: the uploaded audio is used, a cancelled upload stops cleanly."""
import pytest

from ka_subs.common import Stop
from ka_subs.pipeline import _ask_or_stop

URL = "https://www.youtube.com/watch?v=wY2L98eHShE"


def test_uploaded_file_lets_the_video_carry_on(tmp_path):
    def upload(vid, url, folder):
        (folder / f"{vid}.webm").write_bytes(b"audio")
        return True

    _ask_or_stop(URL, "wY2L98eHShE", tmp_path, upload)  # no Stop


def test_cancelled_upload_stops_with_laptop_steps(tmp_path):
    with pytest.raises(Stop, match="yt-dlp -f bestaudio"):
        _ask_or_stop(URL, "wY2L98eHShE", tmp_path, lambda *a: False)


def test_without_upload_button_stops_with_laptop_steps(tmp_path):
    with pytest.raises(Stop, match="My Drive / ka-subs / wY2L98eHShE"):
        _ask_or_stop(URL, "wY2L98eHShE", tmp_path, None)
