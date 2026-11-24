"""Upload a clip to YouTube with the Data API (OAuth, one-time browser consent).

First run opens a browser once to authorize the channel; the token is cached in
~/.vicereplay/youtube_token.json (outside the repo). Needs client_secret.json from a Google Cloud
project with YouTube Data API v3 enabled (path in --client-secret or $YT_CLIENT_SECRET).

  python scripts/youtube_upload.py clip.mp4 --title "..." --description-file post.md --privacy private

Note: videos uploaded by an API project that has not passed Google's audit are locked to private.
"""
import argparse, os, sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN = Path.home() / ".vicereplay" / "youtube_token.json"


def service(client_secret):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret or not Path(client_secret).exists():
                sys.exit("client_secret.json not found. Pass --client-secret or set YT_CLIENT_SECRET.")
            creds = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES).run_local_server(port=0)
        TOKEN.parent.mkdir(parents=True, exist_ok=True)
        TOKEN.write_text(creds.to_json())
        TOKEN.chmod(0o600)
    return build("youtube", "v3", credentials=creds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--description-file")
    ap.add_argument("--tags", default="GTA6,GTAVI,ViceReplay")
    ap.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    ap.add_argument("--client-secret", default=os.environ.get("YT_CLIENT_SECRET"))
    a = ap.parse_args()
    desc = Path(a.description_file).read_text(encoding="utf-8") if a.description_file else a.description
    from googleapiclient.http import MediaFileUpload
    yt = service(a.client_secret)
    body = {"snippet": {"title": a.title[:100], "description": desc, "tags": a.tags.split(","), "categoryId": "20"},
            "status": {"privacyStatus": a.privacy, "selfDeclaredMadeForKids": False}}
    req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(a.video, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    print(f"uploaded: https://youtube.com/shorts/{resp['id']} ({a.privacy})")


if __name__ == "__main__":
    main()
