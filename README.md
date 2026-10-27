# ka-subs-creator

Makes Georgian subtitles (`.srt` files) for Khan Academy videos on YouTube that have none.

You paste a YouTube link into a Google Colab notebook. It:
1. gets the video's audio,
2. has Gemini write down every word,
3. finds the exact time of every word,
4. makes the `.srt` file and checks it for missing speech.

Everything runs free in Google Colab, so nothing needs to be installed on your computer.

**Open the notebook:**
https://colab.research.google.com/github/razmikb/ka-subs-creator/blob/main/ka_subs_colab.ipynb

## First time only

1. You need a free Gemini API key from https://aistudio.google.com (**Get API key**).
2. Open the notebook (link above).
3. Menu **Runtime → Change runtime type → T4 GPU → Save**.
4. Click the **key icon** on the left (Secrets) → **Add new secret**:
   - Name: `GEMINI_API_KEY`
   - Value: your key
   - Switch **Notebook access** on.

## Every time

1. Open the notebook.
2. Run **cell 1** (about 2 minutes). Allow access to your Google Drive when it asks.
   It ends with `Ready. Code version: ...`.
3. In **cell 2**, paste one or more YouTube links (separated by spaces), a playlist, or a channel.
4. Run cell 2.
5. The finished subtitles are in Google Drive: **My Drive / ka-subs / subtitles /**.
6. Upload the `.srt` to the video in YouTube Studio (**Subtitles → Add language → Georgian → Upload file**).

Run cell 2 again anytime: it never repeats finished work, so no Gemini request is spent twice.

### If YouTube blocks the download

Sometimes YouTube refuses to send the video to Colab. Cell 2 then shows a download command
and a **Choose files** button.

1. On your laptop, open a terminal in this project folder and run the command it shows, for example:

   ```bash
   yt-dlp -f bestaudio -o "audio/wY2L98eHShE.%(ext)s" -- https://www.youtube.com/watch?v=wY2L98eHShE
   ```

2. Click **Choose files** in Colab and pick that file.

### If Gemini's free limit runs out

The video shows as **Waiting for you**. Gemini's free requests reset at 11:00 Tbilisi time.
You can wait, or do it by hand: open the video's folder in Drive (**My Drive / ka-subs / <video id> /**)
and follow `NEXT_STEPS.txt`. Then run cell 2 again.

## What the messages mean

| Message | What it means | What to do |
|---|---|---|
| **Done** | Subtitles made, nothing suspicious. | Upload them. |
| **Done, needs a listen** | Made, but some places look odd. | Open each `listen:` link and check. |
| **Gap of N s** | No subtitles for a while. | Usually the narrator is drawing quietly. If speech is missing, use cell 3. |
| **Stretched over N s** | One subtitle stays on screen too long. | Often means words are missing there. Listen; use cell 3 if so. |
| **The end may be missing** | Subtitles stop well before the video ends. | Listen to the end; use cell 3 for the missing part. |
| **LOW words/min** | Gemini may have shortened the text. | In the video's Drive folder, delete `part1.txt` and `<video id>.txt`, then run cell 2 again. |
| **Skipped** | The video already has Georgian subtitles. | Nothing. |
| **Waiting for you** | Gemini limit used up, or no key. | See "If Gemini's free limit runs out". |

**Cell 3, "Fill a gap":** put the video link and the time range of the missing speech
(like `1:20` to `2:05`). It writes the missing words, puts them in place and remakes the subtitles.

**To fix a word by hand:** edit `<video id>.txt` in the video's Drive folder (one sentence per line),
then run cell 2 again. It re-times everything from your edited text.

## Local folders

`audio/` and `subs/` in this project folder are for your own copies of audio and subtitle files.
They are never uploaded to GitHub.

## For developers

How it works and why: [PLAN.md](PLAN.md). Code: `ka_subs/`, one small file per step.
Tests (no internet or model needed): `python -m pytest tests`.
