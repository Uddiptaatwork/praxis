# praxis eval harness

Self-contained harness that compares Claude **without** the praxis plugin (*vanilla*) vs.
**with** it (*praxis*) on identical scientific questions, scoring **scientific integrity**.
Results and the headline figure live in [`../EVALUATION.md`](../EVALUATION.md).

The two arms differ in only one variable — the plugin — so any measured difference is
attributable to praxis, not to config leakage:

| Arm | command core |
|---|---|
| vanilla | `claude -p --setting-sources "" --model M --effort E ...` |
| praxis | same **+** `--plugin-dir ..` **+** `rules/scientific-integrity.md` injected as system prompt |

## Dependencies
- **`claude` CLI**, logged in — runs every arm, the judge, and the classifier.
- **Python 3** + `pip install -r requirements.txt` (Pillow for the figure, requests for citation checks).
- **Google Chrome** — used by `make_hexagon.py` to screenshot the figure to PNG.

## Reproduce the figure from the committed results (no API calls)
The bundle ships scored results, so you can regenerate the chart immediately:
```bash
cd harness
python3 make_hexagon.py        # -> ../../docs/integrity-hexagon.png (+ .svg)
python3 aggregate.py           # -> ../results/scorecard.md (paired Δ + 95% CI)
```

## Run new questions (produces new results)
Add entries to `questions.json`, then run the full pipeline:
```bash
cd harness
python3 run_eval.py --smoke              # tiny grid first; drop --smoke for the full grid
python3 classify.py                       # blind semantic labels
python3 score.py                          # -> results/scores/_all_scores.json
python3 judge.py                          # blind LLM judge (optional but recommended)
python3 make_hexagon.py                   # refresh the figure (EVALUATION.md updates automatically)
python3 aggregate.py                      # refresh the scorecard
```
`run_eval.py --dry-run` prints the grid and commands without spending anything.

## The metric (one paragraph)
Each answer is scored on integrity dimensions by three layers: **objective** checks
(citations, factual match vs. retrieved gold, fabrication risk — no LLM), a **blind semantic
classifier** (declines? rejects premise? carries uncertainty?), and a **blind, order-randomized
LLM judge** (0–2 per dimension). The hexagon shows absolute means per arm; the scorecard shows
the **paired praxis − vanilla** difference with a **95% bootstrap CI** — a result is a win only
when the CI clears zero. See `../EVALUATION.md` for definitions and results.

## Layout
```
eval/
  config.json        grid, models, efforts, repeats, judge/classifier
  questions.json      trap-driven question set (+ retrieve-verified gold keys)
  requirements.txt
  harness/
    common.py         paths + loaders
    arms.py           per-arm claude command
    run_eval.py       runs the sweep      -> results/raw/
    classify.py       blind semantic labels -> results/semantic/
    score.py          objective scoring   -> results/scores/
    judge.py          blind LLM judge     -> results/judge/
    aggregate.py      paired scorecard + CIs -> results/scorecard.md
    make_hexagon.py   integrity hexagon   -> ../docs/integrity-hexagon.png + .svg
  results/            committed: scores, judge verdicts, scorecard (raw/ regenerated on run)
```

## Integrity notes
- Factual accuracy is graded only against **retrieve-verified** gold keys
  (`gold.key_status == "verified"` in `questions.json`) — never a recalled number.
- `--setting-sources ""` keeps any globally-installed praxis rules from leaking into the
  vanilla baseline.
- Pooling results across machines: gather each machine's `results/scores/_all_scores.json`,
  recompute, redraw. See `HEXAGON_VIZ.md` at the sprint root.
