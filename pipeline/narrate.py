"""Stage 2 - narration.
Edge-TTS is IP-blocked on GitHub's datacenter runners, so we use gTTS here.
gTTS gives no word timings, so subtitles are skipped (empty SRT); assemble.py
probes the mp3 for its duration."""
from gtts import gTTS


def narrate(script_hi, mp3_path, srt_path):
    tts = gTTS(text=script_hi, lang="hi")
    tts.save(mp3_path)
    open(srt_path, "w", encoding="utf-8").close()  # gTTS has no word timings
    print("[narrate] gTTS audio written")
    return 0.0
