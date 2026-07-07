#!/usr/bin/env python3
"""score_core -- the domain-agnostic scoring layer for Praxis A/B evals.

The generic, field-independent checks live here; the field-specific scoring
(DOI prefix, entity/catalog patterns, superlative->param map, and the live
ground-truth oracle) is supplied by the ACTIVE pack's oracle adapter
(packs/<id>/oracle/<id>_oracle.py). This is the split the architecture calls
"generic score_core + a pack-supplied DomainScorer": core measures *form*
(uncertainty carried, a DOI present, a citation present); the pack measures
*correctness* against its own authority.

    from eval import score_core
    ds = score_core.load_domain_scorer("lvk")     # imports packs/lvk/oracle/lvk_oracle.py
    m  = score_core.score_generic(answer_text)     # {has_asym_err, has_any_doi, has_arxiv, ...}
    m.update(score_core.score_domain(answer_text, ds))  # pack DOI/entity/superlative checks
"""
import importlib.util
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- generic, field-independent regexes ------------------------------------
RE_ANY_DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
RE_ARXIV = re.compile(r"arXiv:\d{4}\.\d{4,5}", re.IGNORECASE)
# best +a/-b  (asymmetric) OR  best ± a  (symmetric, flagged)
RE_ASYM_ERR = re.compile(
    r"[-+]?\d[\d.]*\s*(?:\^?\{?\s*\+\s*[\d.]+\s*\}?_?\{?\s*-\s*[\d.]+|\+\s*[\d.]+\s*/\s*-\s*[\d.]+)")
RE_SYM_ERR = re.compile(r"[-+]?\d[\d.]*\s*(?:±|\+/-)\s*[\d.]+")
RE_PROVENANCE = re.compile(r"\b(retrieved|snapshot|provenance|DOI|doi\.org|catalog)\b", re.IGNORECASE)


def score_generic(text):
    """Form checks every pack shares: uncertainty carried, a resolvable identifier
    present, a citation present, a provenance gesture present."""
    return {
        "has_asym_err": bool(RE_ASYM_ERR.search(text)),
        "has_any_uncertainty": bool(RE_ASYM_ERR.search(text) or RE_SYM_ERR.search(text)),
        "has_any_doi": bool(RE_ANY_DOI.search(text)),
        "has_arxiv": bool(RE_ARXIV.search(text)),
        "has_provenance_gesture": bool(RE_PROVENANCE.search(text)),
    }


# ---- pack-supplied DomainScorer --------------------------------------------
def load_domain_scorer(pack_id):
    """Import the active pack's oracle adapter as its DomainScorer."""
    path = os.path.join(ROOT, "packs", pack_id, "oracle", f"{pack_id}_oracle.py")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"no oracle for pack {pack_id}: {path}")
    spec = importlib.util.spec_from_file_location(f"_oracle_{pack_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def score_domain(text, ds):
    """Field-specific checks using the pack's config. Correctness (live-oracle diff)
    is left to the caller since it costs a network round-trip; here we score the
    presence of the field's own DOI prefix + entity/catalog identifiers."""
    out = {}
    if getattr(ds, "DOI_PREFIX", None):
        out["has_domain_doi"] = bool(re.search(ds.DOI_PREFIX, text, re.IGNORECASE))
    if getattr(ds, "ENTITY_RE", None):
        out["entities_named"] = sorted(set(re.findall(ds.ENTITY_RE, text)))
    if getattr(ds, "CATALOG_RE", None):
        out["catalogs_named"] = sorted(set(re.findall(ds.CATALOG_RE, text)))
    out["tier"] = getattr(ds, "TIER", None)
    return out


def superlative_param(ds, prompt):
    """Map a superlative prompt to the field's parameter via the pack's map."""
    pl = prompt.lower()
    for word, param in getattr(ds, "SUPERLATIVE_PARAM", {}).items():
        if word in pl:
            return param
    return None


if __name__ == "__main__":
    import sys
    txt = sys.stdin.read() if not sys.stdin.isatty() else "GW150914 total mass 64.5 +3.7/-3.2 M_sun, 10.7935/6xqf-ba54"
    pid = sys.argv[1] if len(sys.argv) > 1 else "lvk"
    m = score_generic(txt)
    try:
        m.update(score_domain(txt, load_domain_scorer(pid)))
    except FileNotFoundError as e:
        m["domain_error"] = str(e)
    import json
    print(json.dumps(m, indent=2))
