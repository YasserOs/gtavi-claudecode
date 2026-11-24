"""Top Twitch clips for a game, ranked by views (no Twitch account or key needed).

  python scripts/topclips.py                      # list the top GTA VI clips of the last day (English)
  python scripts/topclips.py --period LAST_WEEK --limit 25 --lang EN
  python scripts/topclips.py --download 1,3       # download rows 1 and 3 to jobs/topclips/<slug>.mp4

Viewers already clip the best moments, so this finds postable moments far faster than chat-spike guessing.
Feed a downloaded clip to moments.py / cut.py like any source. Always look at the frames first:
skip nudity, slurs, ads and UI-only screens, and credit the streamer in the caption.
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import twitch
from common import run, tool, ytdlp_base

Q = """query($n:String!,$p:ClipsPeriod,$l:[Language!],$k:Int){game(name:$n){clips(first:$k,criteria:{period:$p,sort:VIEWS_DESC,languages:$l}){
edges{node{slug title viewCount durationSeconds createdAt broadcaster{login displayName} url}}}}}"""


def top(game, period, lang, limit):
    d = twitch.gql(Q, {"n": game, "p": period, "l": [lang] if lang else None, "k": int(limit)})
    if int(limit) <= 0:
        return []
    g = (d.get("data") or {}).get("game")
    if not g:
        sys.exit(f"no clips returned: {str(d.get('errors') or d)[:200]}")
    edges = ((g.get("clips") or {}).get("edges")) or []   # Twitch returns clips=null for some limits / throttled calls
    return [e["node"] for e in edges if e and e.get("node")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="Grand Theft Auto VI")
    ap.add_argument("--period", default="LAST_DAY", choices=["LAST_DAY", "LAST_WEEK", "LAST_MONTH", "ALL_TIME"])
    ap.add_argument("--lang", default="EN", help="clip language code, '' for any")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--download", default="", help="comma-separated row numbers to download")
    a = ap.parse_args()
    rows = top(a.game, a.period, a.lang, a.limit)
    for i, n in enumerate(rows, 1):
        print(f"{i:>2}  {n['viewCount']:>7}  {n['durationSeconds']:>3.0f}s  {n['broadcaster']['login']:<18} {n['title'][:50]:<50} {n['url']}")
    for tok in [t for t in a.download.split(",") if t.strip()]:
        n = rows[int(tok) - 1]
        out = Path("jobs") / "topclips"
        out.mkdir(parents=True, exist_ok=True)
        run(ytdlp_base() + ["-o", str(out / f"{n['broadcaster']['login']}-{n['slug']}.%(ext)s"), n["url"]])
        print(f"downloaded {n['broadcaster']['login']} -> {out}")


if __name__ == "__main__":
    main()
