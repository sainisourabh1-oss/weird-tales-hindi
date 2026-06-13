"""Stage 2 - narration via Sarvam Bulbul (natural Indian-Hindi, no card, free credits).
Splits script into <=1400-char chunks (Bulbul caps ~2500/req), synthesizes each,
concatenates the WAV pieces, converts to mp3. Subtitles off (no word timings)."""
import os, io, wave, base64, subprocess
from sarvamai import SarvamAI
from . import config

KEY = os.getenv("SARVAM_API_KEY", "")
SPEAKER = os.getenv("SARVAM_SPEAKER") or "shubh"    # storyteller voice; try ritu / rahul / aditya
PACE = float(os.getenv("SARVAM_PACE") or "1.15")    # >1 = faster, brisk narration
MODEL = os.getenv("SARVAM_MODEL") or "bulbul:v3"


def _chunks(text, limit=1400):
    text = " ".join(text.split())
    parts, cur = [], ""
    for s in [x + "।" for x in text.split("।") if x.strip()]:
        if len(s) > limit:
            for i in range(0, len(s), limit):
                parts.append(s[i:i + limit])
        elif len(cur) + len(s) > limit:
            parts.append(cur); cur = s
        else:
            cur += s
    if cur.strip():
        parts.append(cur)
    return parts or [text]


def narrate(script_hi, mp3_path, srt_path):
    client = SarvamAI(api_subscription_key=KEY)
    raw_wavs = []
    for ch in _chunks(script_hi):
        resp = client.text_to_speech.convert(
            text=ch, target_language_code="hi-IN",
            speaker=SPEAKER, model=MODEL, pace=PACE)
        for b64 in resp.audios:
            raw_wavs.append(base64.b64decode(b64))

    combined = mp3_path + ".wav"
    out = None
    for raw in raw_wavs:
        w = wave.open(io.BytesIO(raw), "rb")
        if out is None:
            out = wave.open(combined, "wb")
            out.setparams(w.getparams())
        out.writeframes(w.readframes(w.getnframes()))
        w.close()
    out.close()
    subprocess.run(["ffmpeg", "-y", "-i", combined, mp3_path], check=True)
    os.remove(combined)
    open(srt_path, "w", encoding="utf-8").close()
    print(f"[narrate] Sarvam audio written ({len(raw_wavs)} chunks)")
    return 0.0
