"""Central configuration. Everything reads from environment variables so the
same code runs on the GitHub runner (env from Secrets) and on the Oracle bot
(env from approval_bot/.env)."""
import os

# Paths (relative to repo root; the runner works from there)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "state", "published.db")   # committed back each run
WORK_DIR = os.path.join(ROOT, "work")                   # transient, gitignored

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.0-flash"

# Voice
TTS_VOICE = os.getenv("TTS_VOICE") or "hi-IN-MadhurNeural"
TTS_RATE = os.getenv("TTS_RATE") or "-8%"

# Images
IMAGE_STYLE = os.getenv("IMAGE_STYLE") or \
    "dark cinematic, moody lighting, muted desaturated colors, film grain, atmospheric, photorealistic"
IMAGE_NEGATIVE = os.getenv("IMAGE_NEGATIVE") or \
    "gore, blood, corpse, text, watermark, logo, nudity, deformed"
IMG_W, IMG_H = 1280, 720          # 720p: reliable from Pollinations, fast on the runner

# YouTube
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN", "")

# Behaviour
CHANNEL_LANG = os.getenv("CHANNEL_LANG", "hi")
VIDEOS_PER_RUN = int(os.getenv("VIDEOS_PER_RUN", "1"))

# Curated, reliable "real weird/ironic news" RSS feeds. These report actual
# events, which keeps us on the right side of the facts-vs-expression line:
# we take the EVENT, write our OWN Hindi retelling, never copy their prose.
RSS_FEEDS = [
    "https://www.upi.com/rss/Odd_News/",
    "https://feeds.feedburner.com/oddee",
    "https://www.huffpost.com/section/weird-news/feed",
]
# Reddit (real-news-that-sounds-fake) as leads only; we confirm + rewrite.
REDDIT_JSON = "https://www.reddit.com/r/nottheonion/top.json?t=week&limit=40"
