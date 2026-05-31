# weird-tales-hindi

A fully automated, free, faceless Hindi YouTube channel that narrates **real**
strange / ironic / haunting / disastrous events, with AI narration and AI
images — and **never posts without your one-tap approval**.

Everything runs on **GitHub Actions**. No laptop needed to post. No server.
No paid services.

---

## How it works

```
            ┌──────────────────────── GitHub Actions (scheduled) ────────────────────────┐
            │                                                                              │
  RSS +     │  source → fact-aware Hindi script (Gemini) → narrate (Edge-TTS, Hindi) →    │
  Reddit ──►│  AI images (Pollinations/Flux) → render 720p (ffmpeg) → upload PRIVATE      │
            │                                       │                                      │
            │                                       ▼                                      │
            │                         ⏸  pause on "review" environment                    │
            └───────────────────────────────────────│──────────────────────────────────┘
                                                      │  GitHub Mobile push to your phone
                                                      ▼
                            You preview the private video → Approve ▶ goes PUBLIC
                                                          → Reject  ▶ stays private (discarded)
```

- **Legal model:** we use the *facts* of real reported events and write our
  **own** Hindi retelling. We never translate or copy a source's text. Facts
  aren't copyrightable; expression is.
- **Dedup memory:** every produced story is recorded in `state/published.db`,
  which the workflow commits back to the repo, so stories never repeat.
- **Cost:** ₹0. Public repo = unlimited Actions minutes. Gemini free tier,
  Edge-TTS, and Pollinations are free.

---

## One-time setup (about 30 minutes)

### 1. Create the repo (PUBLIC)
Public is required so the free manual-approval gate works, and it gives
unlimited Actions minutes. No secrets ever live in the code — only in GitHub
Secrets — so public is safe.
Push all these files to it.

### 2. Gemini API key
- Get a free key at Google AI Studio.
- Repo → Settings → Secrets and variables → Actions → New repository secret:
  `GEMINI_API_KEY`.
- Confirm the current model name in AI Studio; if it isn't `gemini-2.0-flash`,
  set a repo **Variable** `GEMINI_MODEL` to the right one.

### 3. YouTube (one-time browser consent → permanent refresh token)
1. Google Cloud Console → create a project → enable **YouTube Data API v3**.
2. OAuth consent screen → External → fill basics → **Publish to Production**
   (so the refresh token doesn't expire after 7 days).
3. Credentials → Create OAuth client ID → **Desktop app**. Note the client id
   and secret.
4. Run this tiny script **once on any computer with a browser** to capture the
   refresh token (this is setup, not posting — posting never needs a browser):

   ```python
   # get_token.py  — run locally once, then delete
   from google_auth_oauthlib.flow import InstalledAppFlow
   flow = InstalledAppFlow.from_client_config(
       {"installed": {
           "client_id": "YOUR_CLIENT_ID",
           "client_secret": "YOUR_CLIENT_SECRET",
           "auth_uri": "https://accounts.google.com/o/oauth2/auth",
           "token_uri": "https://oauth2.googleapis.com/token",
           "redirect_uris": ["http://localhost"]}},
       scopes=["https://www.googleapis.com/auth/youtube"])
   creds = flow.run_local_server(port=0)
   print("REFRESH TOKEN:", creds.refresh_token)
   ```
   `pip install google-auth-oauthlib` first. Sign in with the **channel's**
   Google account.
5. Add three repo Secrets: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

### 4. The approval gate
- Repo → Settings → **Environments** → New environment → name it exactly
  `review`.
- Enable **Required reviewers** → add yourself → Save.
- Install **GitHub Mobile** and turn on notifications, so approval pushes reach
  your phone.

### 5. Channel look & voice (optional)
Set these as repo **Variables** (Settings → Secrets and variables → Actions →
Variables) to override the defaults:
- `TTS_VOICE` = `hi-IN-MadhurNeural` (male) or `hi-IN-SwaraNeural` (female)
- `TTS_RATE` = e.g. `-8%`
- `IMAGE_STYLE` = e.g. `dark cinematic, vintage faded, film grain, atmospheric`

### 6. Go
- Actions tab → enable workflows.
- Trigger once manually (**Run workflow**) to do the first end-to-end run.
- It builds a video, uploads it private, and pauses. Your phone gets a push.
- Open the run, read the summary, tap the **Preview (private)** YouTube link,
  watch it, then **Approve** (publishes) or **Reject** (stays hidden).
- After that it runs itself on the schedule in `.github/workflows/produce.yml`
  (default once a day at noon IST — add more `cron:` lines for more uploads;
  YouTube allows ~6 API uploads/day).

---

## Files

```
pipeline/
  config.py      all settings (read from env)
  db.py          SQLite state + dedup
  sources.py     pull real weird/ironic events (RSS + r/nottheonion)
  script_gen.py  Gemini: original Hindi script + metadata + scene prompts
  narrate.py     Edge-TTS Hindi MP3 + Hindi subtitles (SRT)
  images.py      Pollinations Flux images per scene
  assemble.py    Ken Burns slideshow + burned Hindi subs -> 720p MP4
  publish.py     upload private / set public / delete (YouTube API)
  run.py         orchestrates the build, hands off to approval
.github/workflows/produce.yml   scheduled build + approval-gated publish
state/published.db              dedup memory (auto-committed)
```

---

## Notes & honest caveats

- **Hindi voice quality:** Edge-TTS neural Hindi is good and free, but a careful
  listener may still tell it's synthetic. Judge the first video yourself; if it
  isn't natural enough, swap `TTS_VOICE`/`TTS_RATE`, or later route the narration
  step to a stronger paid/cloned voice.
- **Fact gate is light (v1):** Gemini is asked to skip events it judges
  satirical/fabricated, but it's not a full multi-source verifier. Your approval
  step is the real safety net — preview before you publish.
- **Approve within ~3 days:** a run awaiting approval is bound by GitHub's 72-hour
  workflow timeout; past that it auto-cancels and the video stays private.
- **Rejected videos** remain private (hidden) on your channel. Delete them in
  YouTube Studio whenever, or add a small cleanup workflow later.
- This is v1 and hasn't been run against the live services yet — the first run is
  the shakedown, made safe by the fact that nothing publishes without your tap.
```
