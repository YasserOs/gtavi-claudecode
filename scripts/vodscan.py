"""Scan a streamer's latest VOD (a stream that is still live counts) for the loudest, most hype moments.

  python scripts/vodscan.py kaicenat                       # last 20 min that already exist in the newest VOD
  python scripts/vodscan.py ishowspeed --minutes 30 --back 10   # a 30 min window ending 10 min ago

Downloads only that window (yt-dlp --download-sections), then runs moments.py on it, which scores loudness,
hype words and chat. Cover hours at once without recording live. Output: jobs/<id>/candidates.md.
"""
import argparse, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import twitch
from common import run, ytdlp_base

Q = """query($l:String!){user(login:$l){videos(first:3,type:ARCHIVE,sort:TIME){edges{node{id title lengthSeconds createdAt}}}}}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("login")
    ap.add_argument("--minutes", type=int, default=20)
    ap.add_argument("--back", type=int, default=3, help="minutes before the end of the VOD where the window ends")
    ap.add_argument("--top", type=int, default=6)
    a = ap.parse_args()
    d = twitch.gql(Q, {"l": a.login.lower()})
    edges = (((d.get("data") or {}).get("user") or {}).get("videos") or {}).get("edges") or []
    if not edges:
        sys.exit(f"no VODs for {a.login} (VODs off, or not streaming)")
    v = edges[0]["node"]
    end = max(60, int(v["lengthSeconds"]) - a.back * 60)
    start = max(0, end - a.minutes * 60)
    print(f"VOD {v['id']} '{v['title'][:50]}' length {int(v['lengthSeconds']) // 60} min -> window {start // 60}:{start % 60:02d}-{end // 60}:{end % 60:02d}")
    out = Path("jobs") / "vodscan"
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"{a.login}-{v['id']}-{start}.mp4"
    if not f.exists():
        run(ytdlp_base() + ["--download-sections", f"*{start}-{end}", "--force-keyframes-at-cuts", "-o", str(f), f"https://www.twitch.tv/videos/{v['id']}"])
    subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "moments.py"), str(f), "--top", str(a.top), "--min", "15", "--max", "35"])


if __name__ == "__main__":
    main()
