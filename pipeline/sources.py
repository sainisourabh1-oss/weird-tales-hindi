"""Stage 0 — sourcing.

Pull candidate REAL weird/ironic/haunting events from curated weird-news RSS
feeds plus r/nottheonion. We return lightweight candidates (title + link +
summary); the script stage does the actual fact-aware rewriting in Hindi.
"""
import time
import requests
import feedparser
from . import config

UA = {"User-Agent": "weird-tales-hindi/1.0 (content sourcing bot)"}


def _from_rss():
    out = []
    for url in config.RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:15]:
                title = (e.get("title") or "").strip()
                link = e.get("link") or ""
                summary = (e.get("summary") or e.get("description") or "").strip()
                if title and link:
                    out.append({"title": title, "url": link, "summary": summary})
        except Exception as ex:
            print(f"[sources] RSS failed {url}: {ex}")
    return out


def _from_reddit():
    out = []
    try:
        r = requests.get(config.REDDIT_JSON, headers=UA, timeout=20)
        r.raise_for_status()
        for child in r.json().get("data", {}).get("children", []):
            d = child.get("data", {})
            title = (d.get("title") or "").strip()
            # the article the post links to (the real source), not the reddit thread
            link = d.get("url_overridden_by_dest") or d.get("url") or ""
            if title and link and not d.get("over_18"):
                out.append({"title": title, "url": link, "summary": ""})
    except Exception as ex:
        print(f"[sources] reddit failed: {ex}")
    return out


def fetch_candidates():
    """Return a de-duplicated-by-title list of candidate stories."""
    cands = _from_rss() + _from_reddit()
    seen, uniq = set(), []
    for c in cands:
        key = c["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    print(f"[sources] {len(uniq)} unique candidates gathered")
    return uniq
