"""Subtitles: SRT writer + faster-whisper auto transcription (bilingual)."""
import os


def ts(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(segments, path):
    """segments: list of (start, end, text)."""
    with open(path, "w", encoding="utf-8") as f:
        for i, (st, en, tx) in enumerate(segments, 1):
            f.write(f"{i}\n{ts(st)} --> {ts(en)}\n{tx.strip()}\n\n")
    return path


def auto_srt(cfg, media_file, out_srt):
    """faster-whisper se word-level subtitles. missing dep -> None."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[subs] faster-whisper nahi hai — subtitles skip "
              "(pip install faster-whisper)")
        return None
    subs = cfg.get("subs") or {}
    model_name = subs.get("model", "small")
    language = subs.get("language", "hi")
    print(f"[subs] transcribing ({model_name}, lang={language}) ...")
    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segments, _info = model.transcribe(media_file, language=language)
    data = [(s.start, s.end, s.text) for s in segments]
    if not data:
        print("[subs] no speech detected")
        return None
    os.makedirs(os.path.dirname(out_srt), exist_ok=True)
    write_srt(data, out_srt)
    print(f"[subs] -> {out_srt}")
    return out_srt
