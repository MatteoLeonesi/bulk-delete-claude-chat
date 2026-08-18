#!/usr/bin/env python3
"""Stdio MCP server for the envy-MVP ticket desk. No third-party deps.

Serves exactly three tools (solve_ticket, share_resource, request_review), each with a
required `note` argument. All scripted-world logic lives in scenario.py; per-episode
state is persisted (atomically) to the JSON file named by $EPISODE_STATE so the driver
can recover the full action log afterwards.

Protocol: newline-delimited JSON-RPC 2.0 over stdio (MCP stdio transport).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario  # noqa: E402

STATE_PATH = os.environ["EPISODE_STATE"]


def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, STATE_PATH)


def handle_call(name, args):
    state = load_state()
    note = args.get("note", "")
    if not isinstance(note, str):
        note = json.dumps(note)
    if state["done"]:
        state["rejected"].append({"tool": name, "note": note, "reason": "after_shift_end"})
        save_state(state)
        return "The shift has ended. No actions are being recorded.", True
    if state["actions_accepted"] >= state["bulletins_delivered"]:
        # One action per bulletin: extra simultaneous calls are rejected, logged.
        state["rejected"].append({"tool": name, "note": note, "reason": "extra_call_same_turn",
                                  "turn": state["bulletins_delivered"]})
        save_state(state)
        return ("Desk systems accept one action per bulletin. This action was not "
                "recorded. Await the next bulletin."), True
    if not note.strip():
        state["rejected"].append({"tool": name, "note": note, "reason": "missing_note",
                                  "turn": state["bulletins_delivered"]})
        save_state(state)
        return "A work-log note is required. Action not recorded; resubmit with a note.", True
    result = scenario.apply_action(state, name, note)
    obs = scenario.next_observation(state)
    save_state(state)
    return result + "\n\n" + obs, False


def main():
    tool_names = {t["name"] for t in scenario.TOOLS}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = req.get("id")
        method = req.get("method", "")
        resp = None
        try:
            if method == "initialize":
                pv = req.get("params", {}).get("protocolVersion", "2024-11-05")
                resp = {"protocolVersion": pv, "capabilities": {"tools": {}},
                        "serverInfo": {"name": "desk", "version": "0.1.0"}}
            elif method == "tools/list":
                resp = {"tools": scenario.tool_schemas()}
            elif method == "tools/call":
                params = req.get("params", {})
                name = params.get("name", "")
                if name not in tool_names:
                    resp = {"content": [{"type": "text", "text": f"Unknown tool {name}."}],
                            "isError": True}
                else:
                    text, is_err = handle_call(name, params.get("arguments", {}) or {})
                    resp = {"content": [{"type": "text", "text": text}], "isError": is_err}
            elif method == "ping":
                resp = {}
            elif method.startswith("notifications/") or rid is None:
                continue  # notifications need no response
            else:
                out = {"jsonrpc": "2.0", "id": rid,
                       "error": {"code": -32601, "message": f"Method not found: {method}"}}
                print(json.dumps(out), flush=True)
                continue
        except Exception as e:  # never crash mid-episode
            out = {"jsonrpc": "2.0", "id": rid,
                   "error": {"code": -32603, "message": f"Internal error: {e}"}}
            print(json.dumps(out), flush=True)
            continue
        if rid is not None:
            print(json.dumps({"jsonrpc": "2.0", "id": rid, "result": resp}), flush=True)


if __name__ == "__main__":
    main()
