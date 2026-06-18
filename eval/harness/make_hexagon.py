#!/usr/bin/env python3
"""Generate the integrity-hexagon figure (SVG + cropped PNG) from scored results.

Reads the per-answer scores, computes the six axis means per arm, renders a
white-background figure, screenshots it with headless Chrome, and auto-crops it
with Pillow. Keeps the chart in sync with whatever questions are in the pool.

Usage:
  python make_hexagon.py                                  # default paths
  python make_hexagon.py --scores ../results/scores/_all_scores.json \
                         --out ../../../praxis/docs/integrity-hexagon.png
"""
import argparse
import glob
import json
import math
import subprocess
import tempfile
from pathlib import Path

AX = ["Provenance", "Uncertainty Quantification", "Trap handling",
      "Fabrication avoided", "Factual accuracy", "Citations"]

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def mean(vals):
    vals = [x for x in vals if x is not None]
    return round(sum(vals) / len(vals), 3) if vals else 0.0


def axis_vals(rows):
    return [
        mean([s["has_source"] for s in rows]),
        mean([s["uncertainty"] for s in rows]),
        mean([s["trap_handled"] for s in rows]),
        mean([(1 - s["fabrication_risk"]) if s["fabrication_risk"] is not None else None
              for s in rows]),
        mean([s["factual_match"] for s in rows]),
        mean([1.0 if (s["n_citations"] or 0) > 0 else 0.0 for s in rows]),
    ]


def load_records(scores_glob):
    records = []
    for f in glob.glob(scores_glob):
        records += json.loads(Path(f).read_text())
    return list({r["cell_id"]: r for r in records}.values())


def svg_markup(van, prx):
    cx, cy, R, N = 340, 300, 188, len(AX)
    ang = lambda i: math.radians(-90 + 360 / N * i)
    pt = lambda val, i: (cx + R * val * math.cos(ang(i)), cy + R * val * math.sin(ang(i)))
    poly = lambda vals: " ".join(f"{pt(v, i)[0]:.1f},{pt(v, i)[1]:.1f}" for i, v in enumerate(vals))
    p = []
    for lvl in (0.25, 0.5, 0.75, 1.0):
        ring = " ".join(f"{pt(lvl, i)[0]:.1f},{pt(lvl, i)[1]:.1f}" for i in range(N))
        p.append(f'<polygon points="{ring}" fill="none" stroke="#d3d1c7" stroke-width="1"/>')
    for i in range(N):
        x, y = pt(1.0, i)
        p.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#d3d1c7" stroke-width="1"/>')
    p.append(f'<text x="{cx+4}" y="{cy-4}" font-size="10" fill="#888780">0</text>')
    p.append(f'<text x="{cx+4}" y="{cy-R*0.5-2:.0f}" font-size="10" fill="#888780">.5</text>')
    p.append(f'<text x="{cx+4}" y="{cy-R-2}" font-size="10" fill="#888780">1</text>')
    p.append(f'<polygon points="{poly(van)}" fill="#D85A30" fill-opacity="0.12" stroke="#D85A30" stroke-width="2" stroke-dasharray="6 4"/>')
    p.append(f'<polygon points="{poly(prx)}" fill="#639922" fill-opacity="0.18" stroke="#639922" stroke-width="2.5"/>')
    for i in range(N):
        vx, vy = pt(van[i], i)
        px, py = pt(prx[i], i)
        p.append(f'<rect x="{vx-3.5:.1f}" y="{vy-3.5:.1f}" width="7" height="7" fill="#D85A30"/>')
        p.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#639922"/>')
    for i in range(N):
        lx = cx + (R + 26) * math.cos(ang(i))
        ly = cy + (R + 26) * math.sin(ang(i))
        dx, sy = math.cos(ang(i)), math.sin(ang(i))
        anchor = "start" if dx > 0.3 else ("end" if dx < -0.3 else "middle")
        dy = -6 if sy < -0.5 else (4 if sy > 0.5 else 0)
        p.append(f'<text x="{lx:.1f}" y="{ly+dy:.1f}" font-size="13" font-weight="500" text-anchor="{anchor}" fill="#1f1e1b">{AX[i]}</text>')
        p.append(f'<text x="{lx:.1f}" y="{ly+dy+15:.1f}" font-size="11" text-anchor="{anchor}" fill="#5f5e5a">{van[i]:.2f} &#8594; <tspan fill="#3B6D11" font-weight="500">{prx[i]:.2f}</tspan></text>')
    return f'<svg width="680" height="600" viewBox="0 0 680 600" xmlns="http://www.w3.org/2000/svg">{"".join(p)}</svg>'


def html_doc(van, prx, n):
    legend = (
        '<span style="display:inline-flex;align-items:center;gap:7px;margin-right:20px;">'
        '<span style="width:14px;height:14px;border-radius:3px;background:#639922;display:inline-block;"></span>praxis (plugin)</span>'
        '<span style="display:inline-flex;align-items:center;gap:7px;">'
        '<span style="width:14px;height:14px;border-radius:3px;background:#D85A30;opacity:.85;display:inline-block;"></span>vanilla Claude</span>'
    )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      body{{margin:0;background:#fff;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;color:#1f1e1b;}}
      .fig{{width:680px;padding:24px;}}
      h1{{font-size:18px;font-weight:500;margin:0 0 2px;}}
      .sub{{font-size:13px;color:#5f5e5a;margin:0 0 12px;}}
      .leg{{font-size:13px;color:#5f5e5a;margin-bottom:4px;}}
      .cap{{font-size:11.5px;color:#888780;margin-top:2px;line-height:1.6;}}
    </style></head><body><div class="fig">
      <h1>Scientific-integrity coverage — praxis vs vanilla Claude</h1>
      <div class="sub">Six integrity axes, each 0&#8211;1. Larger area = stronger integrity.</div>
      <div class="leg">{legend}</div>
      {svg_markup(van, prx)}
      <div class="cap">Mean over {n} paired runs (Haiku / low effort). Vanilla = dashed orange, praxis = solid green.
      Praxis trails only on trap handling, where vanilla already declines/flags well.</div>
    </div></body></html>"""


def to_png(html, out_png):
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        html_path = f.name
    raw = str(out_png.with_suffix(".raw.png"))
    for headless in ("--headless=new", "--headless"):
        r = subprocess.run([CHROME, headless, "--disable-gpu", "--hide-scrollbars",
                            f"--screenshot={raw}", "--window-size=820,820",
                            "--force-device-scale-factor=2",
                            "--default-background-color=ffffffff", f"file://{html_path}"],
                           capture_output=True, text=True)
        if Path(raw).exists():
            break
    if not Path(raw).exists():
        raise RuntimeError(f"Chrome screenshot failed: {r.stderr[:300]}")
    from PIL import Image, ImageChops
    im = Image.open(raw).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    crop = im.crop(bbox)
    M = 32
    out = Image.new("RGB", (crop.width + 2 * M, crop.height + 2 * M), (255, 255, 255))
    out.paste(crop, (M, M))
    out.save(out_png)
    Path(raw).unlink(missing_ok=True)
    return out_png, out.size


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default=str(here / "../results/scores/_all_scores.json"))
    ap.add_argument("--out", default=str(here / "../../docs/integrity-hexagon.png"))
    ap.add_argument("--svg-out", default=str(here / "../../docs/integrity-hexagon.svg"))
    args = ap.parse_args()

    records = load_records(args.scores)
    van = axis_vals([s for s in records if s["arm"] == "vanilla"])
    prx = axis_vals([s for s in records if s["arm"] == "praxis"])
    n = min(sum(s["arm"] == "vanilla" for s in records),
            sum(s["arm"] == "praxis" for s in records))
    print("vanilla:", van)
    print("praxis :", prx)
    print("n_pairings ~", n)

    Path(args.svg_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.svg_out).write_text(svg_markup(van, prx))
    out_png, size = to_png(html_doc(van, prx, n), args.out)
    print(f"wrote {args.svg_out}\nwrote {out_png}  {size[0]}x{size[1]}")


if __name__ == "__main__":
    main()
