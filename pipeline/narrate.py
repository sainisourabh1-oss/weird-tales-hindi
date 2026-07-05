"""Stage 2 - narration via Kokoro TTS (free forever, runs on the runner:
no key, no card, no credits, no IP block). Hindi via lang_code 'h'. 24kHz -> mp3."""
import os, re, subprocess
import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = os.getenv("KOKORO_VOICE") or "hm_omega"   # male; female: hf_alpha / hf_beta ; male: hm_psi
SPEED = float(os.getenv("KOKORO_SPEED") or "1.15")

_pipeline = None


def _pipe():
    global _pipeline
    if _pipeline is None:
        _pipeline = KPipeline(lang_code="h")   # 'h' = Hindi
    return _pipeline


def narrate(script_hi, mp3_path, srt_path):
    text = re.sub(r"।\s*", "।\n", " ".join(script_hi.split()))  # one sentence per line
    chunks = []
    for _, _, audio in _pipe()(text, voice=VOICE, speed=SPEED):
        if hasattr(audio, "detach"):
            audio = audio.detach().cpu().numpy()
        chunks.append(np.asarray(audio))
    if not chunks:
        raise RuntimeError("Kokoro produced no audio")
    full = np.concatenate(chunks)
    wav = mp3_path + ".wav"
    sf.write(wav, full, 24000)
    subprocess.run(["ffmpeg", "-y", "-i", wav, mp3_path], check=True)
    os.remove(wav)
    open(srt_path, "w", encoding="utf-8").close()
    print(f"[narrate] Kokoro audio written ({len(chunks)} chunks)")
    return 0.0
