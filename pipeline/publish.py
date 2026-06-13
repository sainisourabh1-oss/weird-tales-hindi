"""Stage 5 - publishing (YouTube Data API v3).
On approval we SCHEDULE the video to go public at peak time (default 17:30 IST)."""
import os, sys, argparse
from datetime import datetime, timedelta, timezone
import google.oauth2.credentials
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from . import config

TOKEN_URI = "https://oauth2.googleapis.com/token"
IST = timezone(timedelta(hours=5, minutes=30))
PUB_HOUR = int(os.getenv("PUBLISH_HOUR_IST") or "17")
PUB_MIN = int(os.getenv("PUBLISH_MIN_IST") or "30")


def _service():
    creds = google.oauth2.credentials.Credentials(
        token=None, refresh_token=config.YT_REFRESH_TOKEN, token_uri=TOKEN_URI,
        client_id=config.YT_CLIENT_ID, client_secret=config.YT_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube"])
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def upload_private(mp4_path, title, description, tags):
    yt = _service()
    body = {
        "snippet": {"title": title[:100], "description": description[:4900],
                    "tags": tags[:15], "categoryId": "24", "defaultLanguage": "hi"},
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(mp4_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"[publish] upload {int(status.progress()*100)}%")
    vid = resp["id"]
    print(f"[publish] uploaded PRIVATE: https://youtu.be/{vid}")
    return vid


def _next_publish_at():
    now = datetime.now(IST)
    t = now.replace(hour=PUB_HOUR, minute=PUB_MIN, second=0, microsecond=0)
    if t <= now + timedelta(minutes=15):
        t += timedelta(days=1)
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def schedule_publish(video_id):
    yt = _service()
    when = _next_publish_at()
    yt.videos().update(part="status", body={
        "id": video_id,
        "status": {"privacyStatus": "private", "publishAt": when,
                   "selfDeclaredMadeForKids": False}}).execute()
    print(f"[publish] scheduled public at {when} UTC: https://youtu.be/{video_id}")


def set_public(video_id):
    _service().videos().update(part="status",
        body={"id": video_id, "status": {"privacyStatus": "public"}}).execute()
    print(f"[publish] now PUBLIC: https://youtu.be/{video_id}")


def delete(video_id):
    _service().videos().delete(id=video_id).execute()
    print(f"[publish] deleted {video_id}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule")
    ap.add_argument("--publish")
    ap.add_argument("--delete")
    a = ap.parse_args()
    if a.schedule:
        schedule_publish(a.schedule)
    elif a.publish:
        set_public(a.publish)
    elif a.delete:
        delete(a.delete)
    else:
        print("nothing to do"); sys.exit(1)
