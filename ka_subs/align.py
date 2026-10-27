"""Forced alignment: give every word of the known text its time in the audio (PLAN.md §3.4).
Runs in Colab on the GPU. Proven code from TVNAIA's notebook."""
from pathlib import Path

from .common import Stop

_model = None  # loaded once per Colab session (about 1.2 GB)


def _load():
    global _model
    if _model is None:
        import torch
        from ctc_forced_aligner import load_alignment_model

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        _model = load_alignment_model(device, dtype=dtype)
    return _model


def align_words(audio: Path, words: list[str]) -> list[tuple[float, float]]:
    """(start, end) in seconds for each word, in order. Always the WHOLE audio, so times
    run from the video's own 0:00."""
    from ctc_forced_aligner import (generate_emissions, get_alignments, get_spans,
                                    load_audio, postprocess_results, preprocess_text)

    model, tok = _load()
    wav = load_audio(str(audio), model.dtype, model.device)
    emissions, stride = generate_emissions(model, wav, batch_size=16)
    tokens, starred = preprocess_text(" ".join(words), romanize=True, language="kat")
    segments, scores, blank = get_alignments(emissions, tokens, tok)
    result = postprocess_results(starred, get_spans(tokens, segments, blank), stride, scores)
    if len(result) != len(words):
        raise Stop(f"The timing step returned {len(result)} words for {len(words)}. "
                   "Some odd symbol in the transcript probably confused it. Look for "
                   "symbols other than letters, digits and punctuation in the .txt.")
    return [(r["start"], r["end"]) for r in result]
