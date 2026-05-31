"""Stage 3 — images.

Generates one image per scene via Pollinations (free, no key, Flux model).
A consistent style suffix is appended to every prompt for channel identity,
and a negative-prompt is included to keep tone safe (no gore/text/etc.).
Retries with backoff because the free endpoint is occasionally flaky.
"""
import os
import time
import urllib.parse
import requests
from . import config

BASE = "https://image.pollinations.ai/prompt/"


def _build_url(prompt: str, seed: int) -> str:
    full = f"{prompt}, {config.IMAGE_STYLE}"
    q = urllib.parse.quote(full)
    neg = urllib.parse.quote(config.IMAGE_NEGATIVE)
    return (f"{BASE}{q}?width={config.IMG_W}&height={config.IMG_H}"
            f"&model=flux&nologo=true&seed={seed}&negative={neg}")


def generate(scenes, out_dir: str):
    """Download one image per scene. Returns list of local file paths
    (only successfully fetched images)."""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "").strip()
        if not prompt:
            continue
        url = _build_url(prompt, seed=1000 + i)
        dest = os.path.join(out_dir, f"scene_{i:03d}.jpg")
        for attempt in range(4):
            try:
                r = requests.get(url, timeout=90)
                r.raise_for_status()
                if r.content and len(r.content) > 2000:  # guard against error stubs
                    with open(dest, "wb") as f:
                        f.write(r.content)
                    paths.append(dest)
                    break
                raise ValueError("empty/too-small image")
            except Exception as ex:
                wait = 5 * (attempt + 1)
                print(f"[images] scene {i} attempt {attempt+1} failed ({ex}); retry in {wait}s")
                time.sleep(wait)
        else:
            print(f"[images] scene {i} gave up after retries")
    print(f"[images] {len(paths)}/{len(scenes)} images fetched")
    return paths
