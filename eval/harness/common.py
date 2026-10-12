"""Shared paths and loaders for the praxis eval harness."""
import json
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = EVAL_DIR / "config.json"
QUESTIONS_PATH = EVAL_DIR / "questions.json"
RESULTS_DIR = EVAL_DIR / "results"
RAW_DIR = RESULTS_DIR / "raw"          # one file per (question,arm,model,effort,repeat)
SCORES_DIR = RESULTS_DIR / "scores"    # objective scores
JUDGE_DIR = RESULTS_DIR / "judge"      # blind LLM-judge verdicts


def load_config():
    return json.loads(CONFIG_PATH.read_text())


def load_questions():
    return json.loads(QUESTIONS_PATH.read_text())["questions"]


def resolve(p):
    """Resolve a possibly-relative path against the eval/ directory."""
    p = Path(p)
    return p if p.is_absolute() else (EVAL_DIR / p).resolve()


def cell_id(qid, arm, model, effort, rep):
    return f"{qid}__{arm}__{model}__{effort}__r{rep}"


def ensure_dirs():
    for d in (RESULTS_DIR, RAW_DIR, SCORES_DIR, JUDGE_DIR):
        d.mkdir(parents=True, exist_ok=True)
