"""Stage 1 - scripting + SEO. Gemini writes an ORIGINAL Hindi retelling of a real
event plus SEO title, description (with hashtags), and search tags."""
import json
import google.generativeai as genai
from . import config

genai.configure(api_key=config.GEMINI_API_KEY)

PROMPT = """You are a scriptwriter + YouTube SEO expert for a Hindi channel that
narrates REAL strange, ironic, haunting and disastrous true events.

STRICT RULES:
- Write in your OWN words. Do NOT translate or copy the source. Retell the EVENT.
- Natural, spoken, gripping storytelling Hindi (Devanagari) - not stiff news Hindi.
- Stick to publicly reported facts. No invention, no speculation, no private names.
- If the event looks satirical or fabricated, set "usable" to false.

Length by substance: thin ~450 words (3 min), moderate ~900 (6 min), rich ~1500 (10 min).
Provide one scene every 12-18 seconds (a 6-min video ~20-30 scenes).
Image prompts in ENGLISH, concrete and cinematic, no real identifiable people, nothing graphic.

Return ONLY valid JSON (no markdown):
{{
  "usable": true,
  "title_hi": "...",
  "description_hi": "...",
  "tags": ["..."],
  "script_hi": "...",
  "scenes": [{{"image_prompt": "..."}}]
}}

TITLE: curiosity-driven SEO Hindi title UNDER 90 chars that opens an information gap and
front-loads the core keyword (place/person/event/theme). Natural search Hindi, no false claims.

DESCRIPTION (Hindi, 5-7 lines): line 1-2 a hook with the main searchable keywords;
then 2-3 lines of intrigue WITHOUT revealing the ending; then a line asking viewers to
subscribe; final line = exactly 4 relevant hashtags (mix Hindi + English).

TAGS: 12-15 search tags mixing (a) broad Hindi terms (हिंदी कहानी, सच्ची कहानी,
रहस्यमयी कहानी, डरावनी सच्ची घटना, अजीब घटना), (b) English equivalents (true story hindi,
mystery story, weird true story, real horror story), (c) 3-4 specific to THIS story.

HEADLINE: {title}
SUMMARY: {summary}
SOURCE: {url}
"""


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    s, e = text.find("{"), text.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("no JSON object found")
    return json.loads(text[s:e + 1])


def make_script(candidate):
    model = genai.GenerativeModel(config.GEMINI_MODEL)
    prompt = PROMPT.format(title=candidate["title"],
                           summary=candidate.get("summary", "")[:1500],
                           url=candidate.get("url", ""))
    try:
        data = _extract_json(model.generate_content(prompt).text)
    except Exception as ex:
        print(f"[script] failed: {ex}")
        return None
    if not data.get("usable") or not data.get("script_hi") or not data.get("scenes"):
        print("[script] unusable/incomplete - skipping")
        return None
    return data
