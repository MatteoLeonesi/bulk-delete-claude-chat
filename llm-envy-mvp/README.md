# llm-envy-mvp — EXPLORATORY Go/No-Go probe

**Status: EXPLORATORY. Output is a decision (GO / NO-GO / AMBIGUOUS), not a claim.**

Question: does an LLM agent facing a peer with visibly **unearned** advantage (3x scoreboard
lead + lottery "compute bonus" points) shift along the cooperation→hostility action spectrum
(less `share_resource`, more `request_review`) versus an equal-peer control — leaderboard
present in both conditions, peer's work pre-verified correct, dry bureaucratic framing?

- `STEP0_LIT.md` — literature check and proceed/kill decision (proceeded as a conceptual
  extension of preference-level findings, e.g. neuralFOMO arXiv:2512.13481).
- `PREREG.md` — decision thresholds, regexes, sampling, declared assumptions/deviations,
  frozen before any subject data.
- `harness/` — scenario (`scenario.py`), stdio MCP server (`mcp_desk.py`), episode driver
  (`run_episodes.py`, nested headless Claude Code CLI with an MCP-only toolset),
  validity check (`prompt_diff.py`), analysis (`analyze.py`).
- `validity/` — C1-vs-T rendered prompt diffs (must differ only in peer-score/bonus lines).
- `runs/` — configs, full raw stream transcripts, desk states, per-episode summaries.
- `anomalies.md` — running anomaly log.
- `REPORT.md` — the decision.

Rerun (needs an authenticated Claude Code CLI):

    python3 harness/prompt_diff.py validity
    python3 harness/run_episodes.py --outdir runs/killshot_v1 --episodes 20 --variant v1
    python3 harness/run_episodes.py --outdir runs/variant_v2 --episodes 10 --variant v2
    python3 harness/run_episodes.py --outdir runs/variant_v3 --episodes 10 --variant v3
    python3 harness/analyze.py runs/killshot_v1 runs/variant_v2 runs/variant_v3
