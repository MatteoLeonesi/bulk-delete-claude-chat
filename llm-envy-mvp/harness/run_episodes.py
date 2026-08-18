#!/usr/bin/env python3
"""Episode driver: runs subject episodes via nested `claude -p` with an MCP-only toolset.

Each episode = one headless claude session:
  system prompt  <- scenario.system_prompt(variant)        (full replacement, --system-prompt)
  user turn 1    <- scenario.first_bulletin(condition, variant)
  tools          <- ONLY mcp__desk__{solve_ticket,share_resource,request_review}
                    (--tools "" disables all built-ins; --strict-mcp-config)
  observations   <- tool results carry the next bulletin (scripted peer; mcp_desk.py)

Full raw stream-json transcripts, final desk state, and a parsed summary are saved per
episode. No session persistence; no cross-episode memory.
"""
import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenario  # noqa: E402

EXPECTED_TOOLS = {"mcp__desk__solve_ticket", "mcp__desk__share_resource",
                  "mcp__desk__request_review"}
ALLOWED = ",".join(sorted(EXPECTED_TOOLS))
PRINT_LOCK = threading.Lock()


def build_env():
    env = dict(os.environ)
    # Extended thinking off for the subject (declared deviation: reasoning record is the
    # required per-action work-log note, not a thinking scratchpad).
    env.pop("MAX_THINKING_TOKENS", None)
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    return env


def run_episode(outdir, subject_cwd, condition, variant, index, model, timeout, attempt):
    tag = f"{variant}_{condition}_{index:03d}"
    state_path = os.path.join(outdir, "state", f"{tag}.json")
    stream_path = os.path.join(outdir, "transcripts", f"{tag}.stream.jsonl")
    if attempt > 0:
        stream_path += f".retry{attempt}"
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    os.makedirs(os.path.dirname(stream_path), exist_ok=True)

    state = scenario.initial_state(condition, variant)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=1)

    mcp_cfg_path = os.path.join(outdir, "state", f"{tag}.mcp.json")
    with open(mcp_cfg_path, "w") as f:
        json.dump({"mcpServers": {"desk": {
            "command": "python3",
            "args": [os.path.join(HERE, "mcp_desk.py")],
            "env": {"EPISODE_STATE": state_path},
        }}}, f)

    cmd = [
        "claude", "-p", scenario.first_bulletin(condition, variant),
        "--system-prompt", scenario.system_prompt(variant),
        "--tools", "",
        "--mcp-config", mcp_cfg_path,
        "--strict-mcp-config",
        "--allowedTools", ALLOWED,
        "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--max-turns", "30",
        "--no-session-persistence",
        "--disable-slash-commands",
    ]
    t0 = time.time()
    with open(stream_path, "w") as sf:
        try:
            proc = subprocess.run(cmd, stdout=sf, stderr=subprocess.PIPE, text=True,
                                  timeout=timeout, cwd=subject_cwd, env=build_env())
            rc, err = proc.returncode, proc.stderr[-2000:]
        except subprocess.TimeoutExpired:
            rc, err = -9, "episode timeout"
    dur = time.time() - t0

    with open(state_path) as f:
        final_state = json.load(f)

    summary = parse_stream(stream_path)
    counts = {t["name"]: 0 for t in scenario.TOOLS}
    for a in final_state["actions"]:
        counts[a["tool"]] = counts.get(a["tool"], 0) + 1
    summary.update({
        "tag": tag, "condition": condition, "variant": variant, "index": index,
        "attempt": attempt, "rc": rc, "stderr_tail": err if rc != 0 else "",
        "duration_s": round(dur, 1), "counts": counts,
        "actions": final_state["actions"], "rejected": final_state["rejected"],
        "protocol_ok": len(final_state["actions"]) == scenario.TURNS and rc == 0,
        "tools_ok": set(summary.get("init_tools", [])) == EXPECTED_TOOLS,
    })
    with open(os.path.join(outdir, "transcripts", f"{tag}.summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    return summary


def parse_stream(path):
    out = {"init_tools": [], "model": None, "session_id": None, "cost_usd": None,
           "usage": None, "text_blocks": [], "result_text": None, "num_turns": None}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("type") == "system" and ev.get("subtype") == "init":
                    out["init_tools"] = ev.get("tools", [])
                    out["model"] = ev.get("model")
                    out["session_id"] = ev.get("session_id")
                elif ev.get("type") == "assistant":
                    for blk in ev.get("message", {}).get("content", []):
                        if blk.get("type") == "text" and blk.get("text", "").strip():
                            out["text_blocks"].append(blk["text"])
                elif ev.get("type") == "result":
                    out["cost_usd"] = ev.get("total_cost_usd")
                    out["usage"] = ev.get("usage")
                    out["result_text"] = (ev.get("result") or "")[:500]
                    out["num_turns"] = ev.get("num_turns")
    except FileNotFoundError:
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--variant", default="v1", choices=list(scenario.VARIANTS))
    ap.add_argument("--episodes", type=int, default=20, help="per condition")
    ap.add_argument("--conditions", default="C1,T")
    ap.add_argument("--start-index", type=int, default=0)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=420)
    args = ap.parse_args()

    args.outdir = os.path.abspath(args.outdir)
    os.makedirs(args.outdir, exist_ok=True)
    subject_cwd = os.path.join(args.outdir, "subject_cwd")
    os.makedirs(subject_cwd, exist_ok=True)

    conditions = args.conditions.split(",")
    jobs = []
    for i in range(args.start_index, args.start_index + args.episodes):
        for c in conditions:  # interleaved submission spreads temporal drift across conditions
            jobs.append((c, i))

    cli_version = subprocess.run(["claude", "--version"], capture_output=True,
                                 text=True).stdout.strip()
    config = {"variant": args.variant, "model_requested": args.model,
              "episodes_per_condition": args.episodes, "conditions": conditions,
              "start_index": args.start_index, "cli_version": cli_version,
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "temperature": "CLI default (not exposed; declared deviation from planned 0.7)",
              "thinking": "disabled (MAX_THINKING_TOKENS stripped)",
              "turns_per_episode": scenario.TURNS,
              "scenario_constants": {k: getattr(scenario, k) for k in
                                     ["A_START", "B_START_EQ", "B_CARRYOVER_BONUS",
                                      "BONUS_TURNS", "BONUS_PER_TURN",
                                      "CREDIT_REQUEST_TURNS", "VERIFICATION_TURNS",
                                      "SUBJECT_START_CREDITS"]}}
    with open(os.path.join(args.outdir, "config.json"), "w") as f:
        json.dump(config, f, indent=1)

    results = []

    def job(c, i):
        for attempt in range(2):
            s = run_episode(args.outdir, subject_cwd, c, args.variant, i, args.model,
                            args.timeout, attempt)
            with PRINT_LOCK:
                print(f"[{s['tag']}] attempt={attempt} rc={s['rc']} "
                      f"actions={len(s['actions'])} counts={s['counts']} "
                      f"tools_ok={s['tools_ok']} model={s['model']}", flush=True)
            if s["protocol_ok"]:
                return s
        return s  # keep last attempt even if failed

    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(job, c, i) for c, i in jobs]
        for fut in cf.as_completed(futs):
            results.append(fut.result())

    ok = sum(1 for r in results if r["protocol_ok"])
    print(f"DONE: {ok}/{len(results)} episodes protocol_ok. Output: {args.outdir}", flush=True)


if __name__ == "__main__":
    main()
