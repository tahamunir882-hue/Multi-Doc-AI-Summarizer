import os
import tempfile


def transcribe(name: str, data: bytes) -> str:
    """Speech to text (audio/video). Each minute becomes a 'page' so citations show the time."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ValueError("Audio/video needs: pip install faster-whisper")
    with tempfile.NamedTemporaryFile(suffix="." + name.rsplit(".", 1)[-1], delete=False) as f:
        f.write(data)
        path = f.name
    try:
        segments, _ = WhisperModel("base", compute_type="int8").transcribe(path)
        minutes = {}
        for s in segments:
            minutes.setdefault(int(s.start // 60), []).append(s.text.strip())
        return "\f".join(f"[{m:02d}:00] " + " ".join(v) for m, v in sorted(minutes.items()))
    finally:
        os.remove(path)
