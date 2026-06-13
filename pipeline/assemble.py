"""Stage 4 - assembly: Ken Burns slideshow + audio, then burn Hindi subs."""
import os
import subprocess
from PIL import Image
if not hasattr(Image, "ANTIALIAS"):           # Pillow >=10 removed it; moviepy 1.0.3 needs it
    Image.ANTIALIAS = Image.Resampling.LANCZOS
from moviepy.editor import (ImageClip, concatenate_videoclips,
                            AudioFileClip, CompositeVideoClip)
from . import config

FPS = 24
ZOOM = 0.06


def _ken_burns(path, duration):
    clip = (ImageClip(path)
            .set_duration(duration)
            .resize(newsize=(config.IMG_W, config.IMG_H)))
    clip = clip.resize(lambda t: 1 + ZOOM * (t / max(duration, 0.1)))
    clip = clip.set_position("center")
    return CompositeVideoClip([clip], size=(config.IMG_W, config.IMG_H))


def assemble(image_paths, mp3_path, srt_path, out_path, audio_dur=0.0):
    if not image_paths:
        raise RuntimeError("no images to assemble")

    audio = AudioFileClip(mp3_path)
    dur = audio_dur if audio_dur > 0 else audio.duration
    per = dur / len(image_paths)

    clips = [_ken_burns(p, per) for p in image_paths]
    video = concatenate_videoclips(clips, method="compose").set_audio(audio)

    tmp = out_path + ".tmp.mp4"
    video.write_videofile(
        tmp, fps=FPS, codec="libx264", audio_codec="aac",
        threads=4, preset="veryfast", logger="bar",
    )
    video.close(); audio.close()

    if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        style = "FontName=Noto Sans Devanagari,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=40"
        vf = f"subtitles={srt_path}:force_style='{style}'"
        cmd = ["ffmpeg", "-y", "-i", tmp, "-vf", vf,
               "-c:v", "libx264", "-preset", "veryfast", "-c:a", "copy", out_path]
        subprocess.run(cmd, check=True)
        os.remove(tmp)
    else:
        os.replace(tmp, out_path)

    print(f"[assemble] wrote {out_path} ({dur:.1f}s, {len(image_paths)} scenes)")
    return out_path
