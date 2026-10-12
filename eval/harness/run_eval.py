#!/usr/bin/env python3
"""Run the vanilla-vs-praxis sweep.

Each cell = (question, arm, model, effort, repeat) -> one `claude -p` call.
Results are written to results/raw/<cell_id>.json with the answer, cost, and
run metadata. Use --dry-run first; use --smoke for the tiny grid in config.json.

Examples:
  python run_eval.py --dry-run            # print the grid + commands, run nothing
  python run_eval.py --smoke              # tiny grid (1 model, 1 effort, 1 repeat)
  python run_eval.py --only S1_gw150914_masses --smoke
  python run_eval.py                      # FULL grid (can be hours + $$ -- you'll be asked to confirm)
"""
import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from common import load_config, load_questions, ensure_dirs, RAW_DIR, cell_id
from arms import build_cmd


def parse_cli_json(stdout):
    """`claude --output-format json` prints one JSON object; be tolerant of stray lines."""
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        lines = [l for l in stdout.splitlines() if l.strip().startswith("{")]
        if not lines:
            raise
        return json.loads(lines[-1])


def run_cell(cell, cfg, resume=False):
    qid, arm, model, effort, rep, prompt = cell
    cid = cell_id(qid, arm, model, effort, rep)
    out_path = RAW_DIR / f"{cid}.json"
    if resume and out_path.exists():
        return {"cell_id": cid, "skipped": True}

    cmd = build_cmd(arm, model, effort, prompt, cfg)
    rec = {"cell_id": cid, "qid": qid, "arm": arm, "model": model,
           "effort": effort, "repeat": rep, "prompt": prompt}
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=cfg.get("timeout_s", 900))
        rec["wall_s"] = round(time.time() - t0, 1)
        if proc.returncode != 0:
            rec.update(ok=False, error=f"exit {proc.returncode}: {proc.stderr[:800]}")
        else:
            data = parse_cli_json(proc.stdout)
            rec.update(
                ok=not data.get("is_error", False),
                answer=data.get("result", ""),
                cost_usd=data.get("total_cost_usd"),
                duration_ms=data.get("duration_ms"),
                num_turns=data.get("num_turns"),
                permission_denials=data.get("permission_denials", []),
                session_id=data.get("session_id"),
            )
    except subprocess.TimeoutExpired:
        rec.update(ok=False, error="timeout", wall_s=round(time.time() - t0, 1))
    except Exception as e:  # noqa: BLE001 -- record any failure, never abort the sweep
        rec.update(ok=False, error=f"{type(e).__name__}: {e}", wall_s=round(time.time() - t0, 1))

    out_path.write_text(json.dumps(rec, indent=2))
    return rec


def build_grid(cfg, args, questions):
    models = args.models or (cfg["smoke"]["models"] if args.smoke else cfg["models"])
    efforts = args.efforts or (cfg["smoke"]["efforts"] if args.smoke else cfg["efforts"])
    repeats = args.repeats or (cfg["smoke"]["repeats"] if args.smoke else cfg["repeats"])
    arms = args.arms or cfg["arms"]
    qs = [q for q in questions if (not args.only or q["id"] in args.only)]

    cells = []
    for q in qs:
        for arm in arms:
            for model in models:
                for effort in efforts:
                    for rep in range(repeats):
                        cells.append((q["id"], arm, model, effort, rep, q["prompt"]))
    return cells


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true", help="use the tiny smoke grid from config.json")
    ap.add_argument("--dry-run", action="store_true", help="print the grid and commands; run nothing")
    ap.add_argument("--resume", action="store_true", help="skip cells whose result file already exists")
    ap.add_argument("--only", nargs="+", metavar="QID", help="restrict to these question ids")
    ap.add_argument("--arms", nargs="+", choices=["vanilla", "praxis"])
    ap.add_argument("--models", nargs="+")
    ap.add_argument("--efforts", nargs="+")
    ap.add_argument("--repeats", type=int)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt for large grids")
    args = ap.parse_args()

    cfg = load_config()
    ensure_dirs()
    questions = load_questions()
    cells = build_grid(cfg, args, questions)

    print(f"Grid: {len(cells)} cells "
          f"(arms x models x efforts x repeats x questions)\n")

    if args.dry_run:
        for c in cells:
            cmd = build_cmd(c[1], c[2], c[3], c[5], cfg)
            shown = " ".join(cmd[:-1]) + f' "{c[5][:60]}..."'
            print(f"  [{cell_id(c[0], c[1], c[2], c[3], c[4])}]\n    {shown}\n")
        print(f"DRY RUN: {len(cells)} cells. Nothing executed.")
        return

    # Guard against accidental giant/expensive runs.
    if len(cells) > 12 and not args.yes:
        ans = input(f"About to run {len(cells)} live claude calls (cost + time). Proceed? [y/N] ")
        if ans.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return

    workers = args.workers or cfg.get("max_workers", 2)
    done = 0
    total_cost = 0.0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_cell, c, cfg, args.resume): c for c in cells}
        for fut in as_completed(futs):
            rec = fut.result()
            done += 1
            if rec.get("skipped"):
                print(f"[{done}/{len(cells)}] skip {rec['cell_id']}")
                continue
            cost = rec.get("cost_usd") or 0.0
            total_cost += cost
            status = "ok" if rec.get("ok") else f"FAIL ({rec.get('error', '')[:60]})"
            print(f"[{done}/{len(cells)}] {rec['cell_id']}  {status}  "
                  f"${cost:.3f}  {rec.get('wall_s', '?')}s")

    print(f"\nDone. {done} cells, ${total_cost:.2f}, {round(time.time()-t0)}s wall. "
          f"Raw results in {RAW_DIR}")


if __name__ == "__main__":
    main()
