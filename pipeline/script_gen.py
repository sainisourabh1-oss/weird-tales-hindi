"""Stage 1 — scripting.

Given a real event (headline + summary + source), Gemini writes an ORIGINAL
Hindi retelling in its own words (never a translation of the source text),
plus YouTube metadata and scene-by-scene image prompts. It also self-checks
plausibility: if the model judges the event likely fabricated/satirical, we
skip it. This is a lightweight v1 fact-gate, not a full triangulator.

Returns a dict, or None if the candidate should be skipped.
"""
import json
import google.generativeai as genai
from . import config

genai.configure(api_key=config.GEMINI_API_KEY)

PROMPT = """You are a scriptwriter for a Hindi YouTube channel that narrates REAL,
strange, ironic, haunting and disastrous true events. You will be given a news
headline and summary describing a real event.

STRICT RULES:
- Write in your OWN words. Do NOT translate or copy the source text. Retell the
  EVENT (facts are free to use); never reproduce the source's phrasing.
- Natural, spoken, storytelling Hindi (Devanagari). Conversational, gripping,
  the way a good narrator speaks - not stiff "news" Hindi, not formal.
- Stick to publicly reported facts. Do not invent details or quotes. Do not
  speculate. Do not name private individuals beyond what reporting made public.
- If the "event" looks satirical, fabricated, or you cannot treat it as a real
  reported event, set "usable" to false.

Decide a target length based on how much real substance the story has:
- thin/simple -> ~450 words (about 3 min)
- moderate    -> ~900 words (about 6 min)
- rich        -> ~1500 words (about 10 min)

Return ONLY valid JSON (no markdown, no backticks) with this exact shape:
{{
  "usable": true,
  "title_hi": "compelling Hindi YouTube title (<=90 chars)",
  "description_hi": "2-3 line Hindi description",
  "tags": ["6-10 short english+hindi tags"],
  "script_hi": "the full narration in Hindi, paragraphs separated by blank lines",
  "scenes": [
    {{"image_prompt": "english visual description for one scene, concrete and cinematic"}}
  ]
}}
Provide one scene roughly every 12-18 seconds of narration (so a 6-min video has
~20-30 scenes). Image prompts must be in ENGLISH, describe atmosphere/place/objects
(NOT real identifiable people), and avoid anything graphic.

HEADLINE: {title}
SUMMARY: {summary}
SOURCE: {url}
"""


def _extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in model output")
    return json.loads(text[start:end + 1])


def make_script(candidate: dict):
    model = genai.GenerativeModel(config.GEMINI_MODEL)
    prompt = PROMPT.format(
        title=candidate["title"],
        summary=candidate.get("summary", "")[:1500],
        url=candidate.get("url", ""),
    )
    try:
        resp = model.generate_content(prompt)
        data = _extract_json(resp.text)
    except Exception as ex:
        print(f"[script] generation/parse failed: {ex}")
        return None

    if not data.get("usable"):
        print("[script] candidate judged not usable (satire/fabricated) - skipping")
        return None
    if not data.get("script_hi") or not data.get("scenes"):
        print("[script] missing script or scenes - skipping")
        return None
    return data
