"""Orchestrates the BUILD half of the pipeline (everything up to the private
upload). Approval/publish happens afterwards via the GitHub 'review' environment.

On success it writes the new video id + preview link to GITHUB_OUTPUT and a
human-readable summary to GITHUB_STEP_SUMMARY (what you see on your phone when
approving). Records the story in the dedup DB so it's never repeated.

Exit codes: 0 = a video was produced (proceed to approval); 78 = nothing to do
(no fresh story today) so the publish job is skipped.
"""
import os
import shutil
from . import config, db, sources, script_gen, narrate, images, assemble, publish


def _out(key, value):
    f = os.getenv("GITHUB_OUTPUT")
    if f:
        with open(f, "a") as fh:
            fh.write(f"{key}={value}\n")


def _summary(md):
    f = os.getenv("GITHUB_STEP_SUMMARY")
    if f:
        with open(f, "a") as fh:
            fh.write(md + "\n")


def build_one():
    conn = db.connect()
    candidates = sources.fetch_candidates()

    for cand in candidates:
        if db.is_duplicate(conn, cand["title"]):
            continue
        print(f"[run] trying: {cand['title'][:80]}")
        script = script_gen.make_script(cand)
        if not script:
            continue  # unusable/failed — try the next candidate

        work = config.WORK_DIR
        if os.path.exists(work):
            shutil.rmtree(work)
        os.makedirs(work, exist_ok=True)
        mp3 = os.path.join(work, "audio.mp3")
        srt = os.path.join(work, "subs.srt")
        mp4 = os.path.join(work, "video.mp4")
        img_dir = os.path.join(work, "images")

        dur = narrate.narrate(script["script_hi"], mp3, srt)
        img_paths = images.generate(script["scenes"], img_dir)
        if len(img_paths) < 3:
            print("[run] too few images produced — skipping this story")
            continue
        assemble.assemble(img_paths, mp3, srt, mp4, audio_dur=dur)

        vid = publish.upload_private(
            mp4, script["title_hi"], script["description_hi"], script.get("tags", []))

        db.record_produced(conn, cand["title"], cand.get("url", ""), vid)
        conn.close()

        # hand off to the approval step
        _out("video_id", vid)
        _out("produced", "true")
        _summary(f"## 🎬 Ready for review\n"
                 f"**{script['title_hi']}**\n\n"
                 f"▶️ **Preview (private):** https://youtu.be/{vid}\n\n"
                 f"Source event: {cand.get('url','')}\n\n"
                 f"Approve below to publish, or Reject to leave it private (discarded).")
        print(f"[run] DONE — awaiting approval for {vid}")
        return 0

    conn.close()
    print("[run] no fresh usable story this run")
    _out("produced", "false")
    return 78


if __name__ == "__main__":
    raise SystemExit(build_one())
