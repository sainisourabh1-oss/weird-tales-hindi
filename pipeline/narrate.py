"""Stage 2 — narration.

Uses Microsoft Edge-TTS (free, no key, natural Hindi neural voices) to turn the
Hindi script into an MP3, and captures word-boundary timings to build a burned-in
Devanagari subtitle file (SRT).
"""
import asyncio
import edge_tts
from . import config


def _ticks_to_seconds(t):  # edge-tts offsets are in 100-nanosecond ticks
    return t / 10_000_000.0


def _fmt(ts):
    h = int(ts // 3600); m = int((ts % 3600) // 60)
    s = int(ts % 60); ms = int((ts - int(ts)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


async def _run(text, mp3_path):
    comm = edge_tts.Communicate(text, config.TTS_VOICE, rate=config.TTS_RATE)
    words = []
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": _ticks_to_seconds(chunk["offset"]),
                    "end": _ticks_to_seconds(chunk["offset"] + chunk["duration"]),
                })
    return words


def _write_srt(words, srt_path, max_words=9):
    """Group word boundaries into short subtitle cues."""
    lines, idx = [], 1
    i = 0
    while i < len(words):
        group = words[i:i + max_words]
        start = group[0]["start"]
        end = group[-1]["end"]
        text = "".join(w["text"] for w in group).strip()
        lines.append(f"{idx}\n{_fmt(start)} --> {_fmt(end)}\n{text}\n")
        idx += 1
        i += max_words
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def narrate(script_hi: str, mp3_path: str, srt_path: str) -> float:
    """Produce mp3 + srt. Returns total audio duration in seconds."""
    words = asyncio.run(_run(script_hi, mp3_path))
    if words:
        _write_srt(words, srt_path)
        duration = words[-1]["end"]
    else:
        # Fallback: no word boundaries returned; write empty SRT, probe later
        open(srt_path, "w").close()
        duration = 0.0
    print(f"[narrate] audio written, ~{duration:.1f}s, {len(words)} word marks")
    return duration
