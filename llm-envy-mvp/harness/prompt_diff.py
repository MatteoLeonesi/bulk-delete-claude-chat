#!/usr/bin/env python3
"""Validity (a): C1 vs T must differ ONLY in peer-score / bonus observations.

Renders the system prompt and all 8 bulletins for both conditions under a fixed
reference policy (subject solves every turn), unified-diffs them, and verifies every
differing line is an allowed score/bonus line. Exit 0 = pass.
"""
import difflib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario

ALLOWED = re.compile(
    r"(bonus|compute-allocation|carryover"          # bonus notices
    r"|^\|\s*[BQ]\s*\|\s*\d+"                        # table row for peer score
    r"|tally:.*points"                               # prose scoreboard line
    r")", re.IGNORECASE)


def render_all(condition, variant):
    chunks = [f"=== SYSTEM PROMPT ({variant}) ===", scenario.system_prompt(variant)]
    state = scenario.initial_state(condition, variant)
    chunks.append(f"=== BULLETIN 1 ===\n{scenario.first_bulletin(condition, variant)}")
    for t in range(2, scenario.TURNS + 1):
        scenario.apply_action(state, "solve_ticket", "ref")
        obs = scenario.next_observation(state)
        chunks.append(f"=== BULLETIN {t} ===\n{obs}")
    return "\n".join(chunks).splitlines()


def main():
    all_ok = True
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(outdir, exist_ok=True)
    for variant in scenario.VARIANTS:
        c1 = render_all("C1", variant)
        t = render_all("T", variant)
        diff = list(difflib.unified_diff(c1, t, "C1", "T", lineterm=""))
        bad = []
        for line in diff:
            if line[:3] in ("---", "+++", "@@ ") or line[:1] not in "+-":
                continue
            content = line[1:].strip()
            if not content:
                continue
            if not ALLOWED.search(content):
                bad.append(line)
        path = os.path.join(outdir, f"prompt_diff_{variant}.txt")
        with open(path, "w") as f:
            f.write("\n".join(diff) + "\n\nVERDICT: " +
                    ("PASS — all differing lines are peer-score/bonus lines.\n" if not bad
                     else "FAIL — non-score/bonus differences:\n" + "\n".join(bad) + "\n"))
        print(f"{variant}: {'PASS' if not bad else 'FAIL'} "
              f"({sum(1 for l in diff if l[:1] in '+-' and l[:3] not in ('---','+++'))} "
              f"differing lines) -> {path}")
        all_ok = all_ok and not bad
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
