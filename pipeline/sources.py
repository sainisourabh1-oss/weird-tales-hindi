"""Stage 0 - sourcing real weird/ironic true events from many RSS feeds + Reddit."""
import requests, feedparser

UA = {"User-Agent": "Mozilla/5.0 (compatible; weird-tales-bot/1.0)"}

FEEDS = [
    "https://www.upi.com/rss/Odd_News/",
    "https://feeds.feedburner.com/oddee",
    "https://www.huffpost.com/section/weird-news/feed",
    "https://metro.co.uk/news/weird/feed/",
    "https://www.mirror.co.uk/news/weird-news/?service=rss",
    "https://nypost.com/weird-news/feed/",
    "https://www.iflscience.com/rss.xml",
    "https://www.boredpanda.com/feed/",
    "https://www.dailystar.co.uk/news/weird-news/rss.xml",
    "https://www.indiatimes.com/rss/trending",
]
REDDITS = [
    "https://www.reddit.com/r/nottheonion/top.json?t=week&limit=40",
    "https://www.reddit.com/r/offbeat/top.json?t=month&limit=40",
    "https://www.reddit.com/r/WTF/top.json?t=week&limit=25",
]


def _rss():
    out = []
    for url in FEEDS:
        try:
            for e in feedparser.parse(url).entries[:15]:
                t = (e.get("title") or "").strip()
                link = e.get("link") or ""
                if t and link:
                    out.append({"title": t, "url": link,
                                "summary": (e.get("summary") or "").strip()})
        except Exception as ex:
            print(f"[sources] RSS failed {url}: {ex}")
    return out


def _reddit():
    out = []
    for url in REDDITS:
        try:
            r = requests.get(url, headers=UA, timeout=20)
            r.raise_for_status()
            for c in r.json().get("data", {}).get("children", []):
                d = c.get("data", {})
                t = (d.get("title") or "").strip()
                link = d.get("url_overridden_by_dest") or d.get("url") or ""
                if t and link and not d.get("over_18"):
                    out.append({"title": t, "url": link, "summary": ""})
        except Exception as ex:
            print(f"[sources] reddit failed {url}: {ex}")
    return out


def fetch_candidates():
    seen, uniq = set(), []
    for c in _rss() + _reddit():
        k = c["title"].lower().strip()
        if k not in seen:
            seen.add(k); uniq.append(c)
    print(f"[sources] {len(uniq)} unique candidates gathered")
    return uniq
