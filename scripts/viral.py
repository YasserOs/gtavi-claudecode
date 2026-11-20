"""Find viral GTA 6 clips across many big streamers' own Twitch clip lists (no account or key needed).

  python scripts/viral.py                          # list the best week clips >= 25 s
  python scripts/viral.py --min-secs 28 --limit 40
  python scripts/viral.py --download 1,3,5         # download rows into jobs/viral/

Much bigger pool than the category top list: every streamer's own most-viewed clips of the week, filtered to the
game, sorted by views. Titles that hint at sexual content are skipped (cheap filter only: always look at the frames).
Already-posted streamers are not filtered here; check log.md.
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import twitch
from common import run, ytdlp_base

LOGINS = ("kaicenat ishowspeed ludwig hasanabi sodapoppin pokimane mizkif esfandtv nmplol moistcr1tikal penguinz0 jschlatt "
          "tommyinnit kingsleyyy plaqueboymax fanum duke agent00 sketch clix jynxzi lirik shroud summit1g timthetatman nickmercs "
          "cohhcarnage asmongold zackrawrr willneff sydeon emiru valkyrae qtcinderella scarra disguisedtoast rakai marlon dansgaming "
          "trainwreckstv adinross stableronaldo caseoh_ jasontheween jinnytty squeex theburntpeanut penta sixdadon87 piratesoftware "
          "xqc hutchmf nickeh30 loserfruit kyedae_ fuslie lilypichu extraemily").split()
BAD = re.compile(r"(?i)gyat+|mandy|girlfriend|nude|naked|strip|club|stepbro|booty|thot|sex|shower|bikini|ass\b|tits|nsfw|18\+|onlyfans|n[i1]gg|bed\b")
Q = """query($l:String!){user(login:$l){clips(first:40,criteria:{period:LAST_WEEK,sort:VIEWS_DESC}){edges{node{slug title viewCount durationSeconds game{name}}}}}}"""


def collect(min_secs, game="Grand Theft Auto VI"):
    rows = []
    for l in LOGINS:
        try:
            d = twitch.gql(Q, {"l": l})
        except Exception:
            continue
        edges = (((d.get("data") or {}).get("user") or {}).get("clips") or {}).get("edges") or []
        for e in edges:
            n = e["node"]
            if (n.get("game") or {}).get("name") == game and n["durationSeconds"] >= min_secs and not BAD.search(n["title"]):
                rows.append({"views": n["viewCount"], "login": l, "secs": n["durationSeconds"], "title": n["title"], "slug": n["slug"]})
    rows.sort(key=lambda r: -r["views"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-secs", type=float, default=25)
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--download", default="", help="comma-separated row numbers to download into jobs/viral/")
    a = ap.parse_args()
    rows = collect(a.min_secs)[: a.limit]
    for i, r in enumerate(rows, 1):
        print(f"{i:>2} {r['views']:>7} {r['secs']:>3.0f}s {r['login']:<14} {r['title'][:46]:<46} {r['slug']}")
    out = Path("jobs") / "viral"
    out.mkdir(parents=True, exist_ok=True)
    for tok in [t for t in a.download.split(",") if t.strip()]:
        r = rows[int(tok) - 1]
        run(ytdlp_base() + ["-o", str(out / f"{r['login']}-{r['slug']}.%(ext)s"), f"https://www.twitch.tv/{r['login']}/clip/{r['slug']}"], capture=True)
        print("downloaded", r["login"], r["slug"])


if __name__ == "__main__":
    main()
