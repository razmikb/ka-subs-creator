"""YouTube side: check links, expand playlists and channels, read a video's title and
subtitles, download its audio (PLAN.md §3.1). Uses yt-dlp."""
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .common import Stop

_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}
_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


class Blocked(Stop):
    """YouTube refused Google's servers ("confirm you're not a bot")."""


def video_id(url: str) -> str | None:
    """The 11-character video ID of a single-video link, else None."""
    p = urlparse(url)
    if p.hostname == "youtu.be":
        vid = p.path.strip("/").split("/")[0]
    elif p.path.startswith(("/shorts/", "/live/", "/embed/")):
        vid = p.path.split("/")[2]
    else:
        vid = parse_qs(p.query).get("v", [""])[0]
    return vid if _ID.match(vid or "") else None


def check_url(url: str) -> None:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in _HOSTS:
        raise Stop(f"Not a YouTube link: {url}")


def expand(text: str) -> list[str]:
    """Every video link in the text. Playlists and channels become their videos' links."""
    urls = []
    for item in re.split(r"[\s,]+", text.strip()):
        if not item:
            continue
        check_url(item)
        vid = video_id(item)
        if vid:
            urls.append(f"https://www.youtube.com/watch?v={vid}")
        else:
            urls += _list_videos(item)
    return list(dict.fromkeys(urls))  # no repeats, order kept


def _list_videos(url: str) -> list[str]:
    import yt_dlp

    p = urlparse(url)
    if p.path.startswith(("/@", "/channel/", "/c/", "/user/")) and not p.path.rstrip("/").endswith("/videos"):
        url = url.rstrip("/") + "/videos"
    try:
        with yt_dlp.YoutubeDL({"extract_flat": "in_playlist", "quiet": True}) as ydl:
            found = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise _explain(exc, url) from None
    ids = [e.get("id") for e in found.get("entries") or []]
    urls = [f"https://www.youtube.com/watch?v={i}" for i in ids if i and _ID.match(i)]
    if not urls:
        raise Stop(f"No videos found at {url}")
    return urls


def info(url: str) -> dict:
    """{"id", "title", "url", "subs"}, where subs is "human" if the video already has
    Georgian subtitles, "auto" if only YouTube's automatic ones, else None."""
    import yt_dlp

    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            data = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise _explain(exc, url) from None
    human = any(k.startswith("ka") for k in data.get("subtitles") or {})
    auto = any(k.startswith("ka") for k in data.get("automatic_captions") or {})
    return {"id": data["id"], "title": data.get("title") or data["id"], "url": url,
            "subs": "human" if human else "auto" if auto else None}


def download_audio(url: str, folder: Path) -> Path:
    """The best audio track, saved as source.<ext> in the folder."""
    import yt_dlp

    opts = {"format": "bestaudio", "outtmpl": str(folder / "source.%(ext)s"), "quiet": True,
            "noprogress": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise _explain(exc, url) from None
    source = next(folder.glob("source.*"), None)
    if source is None:
        raise Stop("yt-dlp finished but no audio file appeared.")
    return source


def _explain(exc: Exception, url: str) -> Stop:
    words = str(exc)
    if "Sign in to confirm" in words or "not a bot" in words:
        return Blocked("YouTube refused to send the video to Google's servers.")
    if "Private video" in words or "unavailable" in words:
        return Stop(f"The video is private or unavailable: {url}")
    return Stop(f"YouTube download failed: {words[-300:]}")
