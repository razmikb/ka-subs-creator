"""Ask for the audio file in Colab when YouTube blocks the download: an Upload button
right in the notebook. The file is saved into the video's Drive folder."""
import os
from pathlib import Path


def ask_for_audio(vid: str, url: str, folder: Path) -> bool:
    """Shows an Upload button and waits. True if a file was saved into the folder."""
    from google.colab import files

    print(f"  YouTube won't send this video to Colab. Get its audio on your laptop with:\n"
          f"      yt-dlp -f bestaudio -o \"{vid}.%(ext)s\" -- {url}\n"
          f"  then choose that file with the button below (or Cancel to skip this video).")
    try:
        chosen = files.upload()
    except Exception:  # Cancel, or the browser lost the upload
        chosen = {}
    if not chosen:
        return False
    name, data = next(iter(chosen.items()))
    suffix = Path(name).suffix.lower() or ".webm"
    (folder / f"{vid}{suffix}").write_bytes(data)
    if os.path.exists(name):
        os.remove(name)  # Colab also keeps a copy in its own folder
    print(f"  Saved to My Drive/{folder.parent.name}/{vid}/{vid}{suffix}")
    return True
