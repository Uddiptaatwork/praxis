"""Builds the `claude` CLI command for each arm.

The two arms are IDENTICAL except for the one variable under test: praxis.
  vanilla : plain Claude Code, user config excluded (--setting-sources "")
  praxis  : same + the praxis plugin (--plugin-dir) + the scientific-integrity
            rules injected as a system prompt (those rules are NOT shipped by
            the plugin system per INSTALL.md, so we replicate them to test
            praxis as intended).

Both arms use the same model, effort, and permission mode, so any measured
difference is attributable to praxis -- not to config leakage.
"""
from common import resolve


def build_cmd(arm, model, effort, prompt, cfg):
    cmd = [
        "claude", "-p",
        "--setting-sources", "",                 # ignore user/project/local config (kills global-rule leakage)
        "--model", model,
        "--effort", effort,
        "--permission-mode", cfg.get("permission_mode", "bypassPermissions"),
        "--output-format", "json",
    ]
    if arm == "praxis":
        cmd += ["--plugin-dir", str(resolve(cfg["praxis_dir"]))]
        rules_file = cfg.get("rules_file")
        if rules_file:
            rf = resolve(rules_file)
            if rf.exists():
                cmd += ["--append-system-prompt", rf.read_text()]
    elif arm != "vanilla":
        raise ValueError(f"unknown arm: {arm}")
    cmd += [prompt]
    return cmd
