#!/usr/bin/env python3
"""Convention-driven active-domain resolver for Praxis (stdlib, no LLM tokens, no network).

A Praxis install is `praxis` (core) + N `packs/<id>/` domain packs. Everything
downstream -- the quick command, the data skill, the deep loop -- needs to know
which pack is *active*. This resolves it cheaply, from files, in a fixed order:

  1. PRAXIS_DOMAIN env var                -- wins; supports A/B + multi-domain.
  2. .praxis/active (cwd or repo root)    -- one line `<id>`, written by /praxis-use or /init.
  3. Sole-pack auto-detect                -- exactly one packs/<id>/ installed -> use it.
  4. Ambiguous (>=2 packs, no selector)   -- returns None; caller must ask.

Resolution is a file read, never a token spend. The same `<id>` token names the
pack dir, the pack.json `domain.id`, the `domain-expert-<id>` agent, the
`<id>-data` skill, and the PRAXIS_DOMAIN value -- that identity is the whole
convention.

CLI:
    python lib/pack_resolver.py active          # print active id (or empty)
    python lib/pack_resolver.py list            # list installed pack ids
    python lib/pack_resolver.py path [<id>]     # pack dir
    python lib/pack_resolver.py cache [<id>]    # cache json path
    python lib/pack_resolver.py json [<id>]     # resolved fields as JSON
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORE_ROOT = os.path.dirname(HERE)  # repo root == the `praxis` core plugin


def _repo_root(start=None):
    """Walk up from start (or cwd) to the first dir containing packs/ or .git."""
    d = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isdir(os.path.join(d, "packs")) or os.path.isdir(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return CORE_ROOT
        d = parent


def packs_dir(root=None):
    return os.path.join(root or CORE_ROOT, "packs")


def list_packs(root=None):
    """Every packs/<id>/ that carries a pack.json, sorted."""
    pd = packs_dir(root)
    out = []
    if os.path.isdir(pd):
        for name in sorted(os.listdir(pd)):
            if os.path.isfile(os.path.join(pd, name, "pack.json")):
                out.append(name)
    return out


def _active_file(root):
    for base in (os.getcwd(), root):
        f = os.path.join(base, ".praxis", "active")
        if os.path.isfile(f):
            try:
                v = open(f).read().strip()
                if v:
                    return v
            except OSError:
                pass
    return None


def active_domain(root=None, packs=None):
    root = root or CORE_ROOT
    packs = packs if packs is not None else list_packs(root)
    env = os.environ.get("PRAXIS_DOMAIN")
    if env and env in packs:
        return env
    if env and not packs:
        return env  # env override even before a pack lands on disk
    fromfile = _active_file(root)
    if fromfile and (fromfile in packs or not packs):
        return fromfile
    if len(packs) == 1:
        return packs[0]
    return None  # 0 packs, or >=2 with no selector -> caller decides


def pack_dir(pid, root=None):
    return os.path.join(packs_dir(root), pid)


def _pack_json(pid, root=None):
    p = os.path.join(pack_dir(pid, root), "pack.json")
    if os.path.isfile(p):
        with open(p) as f:
            return json.load(f)
    return {}


def cache_path(pid, root=None):
    pj = _pack_json(pid, root)
    rel = (pj.get("cache") or {}).get("path") or f"cache/{pid}_snapshot.json"
    return os.path.join(pack_dir(pid, root), rel)


def data_skill_name(pid):
    return f"{pid}-data"


def expert_agent_name(pid):
    return f"domain-expert-{pid}"


def oracle_module(pid, root=None):
    pj = _pack_json(pid, root)
    rel = (pj.get("oracle") or {}).get("adapter") or f"oracle/{pid}_oracle.py"
    return os.path.join(pack_dir(pid, root), rel)


def resolved(pid=None, root=None):
    root = root or _repo_root()
    pid = pid or active_domain(root)
    if not pid:
        return {"active": None, "packs": list_packs(root),
                "note": "no active pack -- core-only generalist mode (retrieve live with provenance)"}
    pj = _pack_json(pid, root)
    return {
        "active": pid,
        "title": (pj.get("domain") or {}).get("title", pid),
        "tier": (pj.get("oracle") or {}).get("tier"),
        "pack_dir": pack_dir(pid, root),
        "cache_path": cache_path(pid, root),
        "data_skill": data_skill_name(pid),
        "expert_agent": expert_agent_name(pid),
        "oracle_module": oracle_module(pid, root),
        "cumulative_scope": (pj.get("cache") or {}).get("cumulative_scope"),
        "packs": list_packs(root),
    }


def main():
    root = _repo_root()
    args = sys.argv[1:]
    cmd = args[0] if args else "active"
    pid = args[1] if len(args) > 1 else None
    if cmd == "active":
        print(active_domain(root) or "")
    elif cmd == "list":
        print("\n".join(list_packs(root)))
    elif cmd == "path":
        print(pack_dir(pid or active_domain(root) or "", root))
    elif cmd == "cache":
        p = pid or active_domain(root)
        print(cache_path(p, root) if p else "")
    elif cmd == "json":
        print(json.dumps(resolved(pid, root), indent=2))
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
