"""Stage 3 - images via Cloudflare Workers AI (free, reliable from datacenter)."""
import os, time, base64, requests
from . import config

CF_ACCOUNT = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CF_MODEL = os.getenv("CF_IMAGE_MODEL") or "@cf/bytedance/stable-diffusion-xl-lightning"


def _url():
    return f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/{CF_MODEL}"


def _decode(resp):
    if "application/json" in resp.headers.get("content-type", ""):
        b64 = resp.json().get("result", {}).get("image")
        if not b64:
            raise ValueError(f"no image in JSON: {str(resp.json())[:200]}")
        return base64.b64decode(b64)
    return resp.content


def generate(scenes, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    headers = {"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"}
    paths = []
    for i, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "").strip()
        if not prompt:
            continue
        body = {
            "prompt": f"{prompt}, {config.IMAGE_STYLE}",
            "negative_prompt": config.IMAGE_NEGATIVE,
            "width": config.IMG_W,
            "height": config.IMG_H,
        }
        dest = os.path.join(out_dir, f"scene_{i:03d}.png")
        for attempt in range(4):
            try:
                r = requests.post(_url(), headers=headers, json=body, timeout=120)
                r.raise_for_status()
                img = _decode(r)
                if img and len(img) > 2000:
                    with open(dest, "wb") as f:
                        f.write(img)
                    paths.append(dest)
                    break
                raise ValueError("empty image")
            except Exception as ex:
                wait = 5 * (attempt + 1)
                print(f"[images] scene {i} attempt {attempt+1} failed ({ex}); retry in {wait}s")
                time.sleep(wait)
        else:
            print(f"[images] scene {i} gave up")
    print(f"[images] {len(paths)}/{len(scenes)} images fetched")
    return paths
