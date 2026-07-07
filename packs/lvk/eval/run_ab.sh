#!/usr/bin/env bash
# run_ab.sh — A/B cost capture for the Praxis 90-second judge demo.
#
# For each prompt, runs:
#   A (baseline) : vanilla `claude -p` from a CLEAN empty dir (no project CLAUDE.md)
#   B (Praxis)   : `claude --plugin-dir <praxis>` from /tmp (loads the plugin only)
# and records output tokens, wall-clock seconds, and $ from the JSON envelope.
#
# Why a clean dir for A: a baseline `claude -p` run *inside* the praxis repo (or any
# dir with stray files) inherits the project CLAUDE.md / reads local files and stops
# behaving like a clean baseline. macOS has no `timeout`; runs are allowed to finish.
# These hit the LIVE GWOSC API (https://gwosc.org/api/v2).
#
# Requires: claude CLI, jq. Usage: bash eval/run_ab.sh
set -u

PRAXIS_DIR="${PRAXIS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
OUT="/tmp/praxis_eval"
CLEAN="/tmp/praxis_baseline_clean"
mkdir -p "$OUT" "$CLEAN"

# id|prompt   (the demo prompt first, then the two comparison prompts)
PROMPTS=(
  "c1_GW150914|What were the two source-frame component masses of GW150914, with 90% credible intervals? Cite the GWOSC source."
  "c2_GW190521|Give the source-frame component masses and effective spin of GW190521 with 90% credible intervals, and cite the GWOSC source."
  "gap_GW230529|Does GW230529 fall in the lower mass gap? Give the source-frame component masses with 90% credible intervals and cite the GWOSC source."
)

stats () { jq -r '"secs=\(.duration_ms/1000) out_tok=\(.usage.output_tokens) cost_usd=\(.total_cost_usd)"' "$1" 2>/dev/null; }

for row in "${PROMPTS[@]}"; do
  id="${row%%|*}"; prompt="${row#*|}"

  echo "=== $id : A (baseline, clean dir) ==="
  ( cd "$CLEAN" && claude -p "$prompt" --output-format json ) > "$OUT/${id}_baseline.json" 2>/dev/null
  stats "$OUT/${id}_baseline.json"

  echo "=== $id : B (Praxis, from /tmp) ==="
  ( cd /tmp && claude --plugin-dir "$PRAXIS_DIR" --dangerously-skip-permissions \
      -p "$prompt" --output-format json ) > "$OUT/${id}_praxis.json" 2>/dev/null
  stats "$OUT/${id}_praxis.json"
done

echo
echo "=== SUMMARY (A=baseline, B=Praxis) ==="
printf "%-13s %-8s %8s %8s %10s\n" "PROMPT" "SIDE" "secs" "out_tok" "cost_usd"
for row in "${PROMPTS[@]}"; do
  id="${row%%|*}"
  for s in baseline praxis; do
    f="$OUT/${id}_${s}.json"; [ -f "$f" ] || continue
    d=$(jq -r '.duration_ms' "$f"); t=$(jq -r '.usage.output_tokens' "$f"); c=$(jq -r '.total_cost_usd' "$f")
    printf "%-13s %-8s %8.1f %8s %10.4f\n" "$id" "$s" "$(echo "$d/1000"|bc -l)" "$t" "$c"
  done
done
