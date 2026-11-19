"""One command that finds candidate moments fast: top Twitch clips + glitch/funny clips, downloaded and screened.

  python scripts/scout.py                       # top 12 of the last day + glitch/funny hits from the last week
  python scripts/scout.py --top 20 --download 8

Writes jobs/topclips/candidates.md (rank, views, streamer, title, screen flags, file) and keeps jobs/topclips/seen.json
so the same clip is never offered twice. Next steps are manual on purpose: look at the frames (nudity, slurs, ads),
then cut with cut.py and credit the streamer. See skills/auto-post/SKILL.md.
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import topclips
from common import run, ytdlp_base
from screen import screen

GLITCH = re.compile(r"(?i)glitch|bug(ged)?\b|broke|broken|physics|ragdoll|fail|crash|flew|fly|wtf|insane|crazy|easter egg|secret|funny|lmao|lol|bruh|reset|clip(ped)?")
SKIP_TITLE = re.compile(r"(?i)nude|naked|strip|gyat+|thot|onlyfans|n[i1]gg|slur")  # cheap title screen; frames are still checked by hand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="Grand Theft Auto VI")
    ap.add_argument("--top", type=int, default=12, help="how many of the day's top clips to consider")
    ap.add_argument("--glitch", type=int, default=15, help="week's clips scanned for glitch/funny titles (0 = off)")
    ap.add_argument("--download", type=int, default=6, help="max new clips to download and screen")
    ap.add_argument("--lang", default="EN")
    a = ap.parse_args()
    root = Path("jobs") / "topclips"
    root.mkdir(parents=True, exist_ok=True)
    seen_p = root / "seen.json"
    seen = set(json.loads(seen_p.read_text())) if seen_p.exists() else set()

    pool, ids = [], set()
    for src, rows in (("top-day", topclips.top(a.game, "LAST_DAY", a.lang, a.top)),
                      ("glitch-week", [n for n in (topclips.top(a.game, "LAST_WEEK", a.lang, a.glitch) if a.glitch else []) if GLITCH.search(n["title"])])):
        for n in rows:
            if n["slug"] in ids:
                continue
            ids.add(n["slug"]); n["src"] = src; pool.append(n)
    new = [n for n in pool if n["slug"] not in seen and not SKIP_TITLE.search(n["title"])]
    print(f"{len(pool)} candidates, {len(new)} new; downloading up to {a.download}")

    lines = ["# Scout candidates", "", "| # | views | s | streamer | title | source | screen | file |", "|---|---|---|---|---|---|---|---|"]
    for i, n in enumerate(new[: a.download], 1):
        login = n["broadcaster"]["login"]
        out = root / f"{login}-{n['slug']}.mp4"
        if not out.exists():
            try:
                run(ytdlp_base() + ["-o", str(root / f"{login}-{n['slug']}.%(ext)s"), n["url"]], capture=True)
            except SystemExit as ex:
                print(f"download failed {login}: {str(ex)[:80]}"); continue
        r = screen(out)
        flag = ",".join(r["flags"]) or "ok"
        lines.append(f"| {i} | {n['viewCount']} | {n['durationSeconds']:.0f} | {login} | {n['title'][:50]} | {n['src']} | {flag} | {out} |")
        print(f"{i:>2} {n['viewCount']:>7} {n['durationSeconds']:>3.0f}s {login:<16} {flag:<10} {n['title'][:50]}")
        seen.add(n["slug"])
    (root / "candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    seen_p.write_text(json.dumps(sorted(seen)))
    print(f"wrote {root / 'candidates.md'}. Now look at the frames, skip nudity/slurs/ads, then cut + credit.")


if __name__ == "__main__":
    main()
