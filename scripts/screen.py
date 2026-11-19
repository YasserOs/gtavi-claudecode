"""Cheap pre-filter for candidate clips: drops ad breaks and UI-only screens, flags skin-heavy frames.

  python scripts/screen.py clip.mp4 [more.mp4 ...]

Prints one line per file: OK or a list of flags.
  AD      Twitch "Commercial break in progress" slate (most chat spikes during ads are noise)
  STATIC  almost nothing moves: pause menu, map, loading screen, or a frozen frame
  SKIN    large share of skin-tone pixels: look at the frames for nudity before using it (heuristic, not proof)
  DARK    mostly black
AD, STATIC and DARK mean skip. SKIN means "must look at the frames", never "safe" or "unsafe" by itself.
No nudity classifier runs here: always eyeball the contact sheet.
"""
import sys
from pathlib import Path

import cv2
import numpy as np


def _frames(path, n=8, width=320):
    """[(frame, frame_one_second_later_or_None)] for n positions spread over the clip."""
    cap = cv2.VideoCapture(str(path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = int(cap.get(cv2.CAP_PROP_FPS) or 30)
    out = []

    def grab(idx):
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, min(total - 1, idx)))
        ok, f = cap.read()
        if not ok:
            return None
        h, w = f.shape[:2]
        return cv2.resize(f, (width, int(h * width / w)))

    if total > 0:
        for i in range(n):
            pos = int(total * (i + 0.5) / n)
            f1 = grab(pos)
            if f1 is not None:
                out.append((f1, grab(pos + fps)))
    cap.release()
    return out


def screen(path):
    fr = _frames(path)
    if not fr:
        return {"flags": ["UNREADABLE"], "ad": 0.0, "static": 0.0, "skin": 0.0}
    ad_hits, skin, dark, diffs = [], [], [], []
    for f, f2 in fr:
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        slate = ((h >= 80) & (h <= 175) & (s > 80) & (v > 60)).mean()  # cyan/blue/purple/magenta gradient slate
        edges = cv2.Canny(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), 80, 160).mean() / 255
        ad_hits.append(slate > 0.92 and edges < 0.035)  # measured: ad slates 0.98 / 0.02, gameplay <= 0.59 / >= 0.045
        ycc = cv2.cvtColor(f, cv2.COLOR_BGR2YCrCb)
        skin.append(((ycc[..., 1] > 135) & (ycc[..., 1] < 175) & (ycc[..., 2] > 85) & (ycc[..., 2] < 125) & (ycc[..., 0] > 70)).mean())
        dark.append((v < 30).mean() > 0.85)
        if f2 is not None:
            g1, g2 = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
            diffs.append(float(np.abs(g1.astype(np.int16) - g2.astype(np.int16)).mean()))
    ad = float(np.mean(ad_hits))
    static = float(np.median(diffs)) if diffs else 99.0
    sk = float(np.percentile(skin, 75))
    flags = []
    if ad >= 0.5:
        flags.append("AD")
    if static < 7.0:  # measured: pause menus / maps 2-5, gameplay 13+
        flags.append("STATIC")
    if sk > 0.30:
        flags.append("SKIN")
    if np.mean(dark) >= 0.5:
        flags.append("DARK")
    return {"flags": flags, "ad": round(ad, 2), "static": round(static, 1), "skin": round(sk, 2)}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        r = screen(p)
        print(f"{'OK  ' if not r['flags'] else ','.join(r['flags']):<18} ad={r['ad']} motion={r['static']} skin={r['skin']}  {Path(p).name}")


if __name__ == "__main__":
    main()
