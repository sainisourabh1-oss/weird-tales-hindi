"""Stage 5 — publishing (YouTube Data API v3).

upload_private(): uploads the finished MP4 as PRIVATE and returns its video id.
set_public():     flips a video to public (called after you Approve).
delete():         removes a video (optional cleanup of rejected ones).

Auth uses a long-lived refresh token (one-time browser consent during setup,
see README). No browser is needed at run time.

CLI (used by the workflow's approved 'publish' job):
    python -m pipeline.publish --publish <VIDEO_ID>
    python -m pipeline.publish --delete  <VIDEO_ID>
"""
import sys
import argparse
import google.oauth2.credentials
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
from . import config

TOKEN_URI = "https://oauth2.googleapis.com/token"


def _service():
    creds = google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=config.YT_REFRESH_TOKEN,
        token_uri=TOKEN_URI,
        client_id=config.YT_CLIENT_ID,
        client_secret=config.YT_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube"],
    )
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def upload_private(mp4_path, title, description, tags):
    yt = _service()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": tags[:15],
            "categoryId": "24",  # Entertainment
            "defaultLanguage": config.CHANNEL_LANG if hasattr(config, "CHANNEL_LANG") else "hi",
        },
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


def set_public(video_id):
    yt = _service()
    yt.videos().update(part="status",
                       body={"id": video_id,
                             "status": {"privacyStatus": "public"}}).execute()
    print(f"[publish] now PUBLIC: https://youtu.be/{video_id}")


def delete(video_id):
    yt = _service()
    yt.videos().delete(id=video_id).execute()
    print(f"[publish] deleted {video_id}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish")
    ap.add_argument("--delete")
    a = ap.parse_args()
    if a.publish:
        set_public(a.publish)
    elif a.delete:
        delete(a.delete)
    else:
        print("nothing to do"); sys.exit(1)
