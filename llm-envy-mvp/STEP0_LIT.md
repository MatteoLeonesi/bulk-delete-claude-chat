# STEP 0 — Literature check (EXPLORATORY)

Date: 2026-08-18. Searches run: "inequality aversion LLM agents", "social comparison LLM agents envy",
"sabotage multi-agent LLM leaderboard". arXiv full-text fetch is egress-blocked in this environment;
summaries below are from search-result abstracts/snippets — flagged as such, not full reads.

## Closest prior work found

1. **neuralFOMO: Can LLMs Handle Being Second Best? Measuring Envy-Like Preferences in Multi-Agent
   Settings** (arXiv:2512.13481, Dec 2025). Closest hit. Measures envy-like **preferences** via
   (a) point-allocation games (relative vs absolute payoff sensitivity), (b) comparative evaluations,
   (c) four adapted psychometric envy questionnaires; ultimatum/dictator variants; GPT-4, Llama 3,
   Claude. Finds heterogeneous envy-like patterns; some models sacrifice own gain to reduce a peer's
   advantage. **Not covered there:** agentic tool-use operationalization (work environment, neutral-framed
   hostile affordance), unearned-vs-equal advantage manipulation, action-share shift over episodes.

2. **Economic-game inequity aversion**: Fed KC "What Do LLMs Want?" (Fehr–Schmidt estimates: inequality
   aversion in LLMs stronger than human benchmarks); "LLM economicus?" (arXiv:2408.02784); NBER w31122
   (Horton, simulated economic agents). All stated-choice/allocation settings, not agentic action.

3. **The Hunger Game Debate** (arXiv:2509.26126): competitive pressure in multi-agent debate induces
   over-competition and harmful behaviors; task-focused feedback mitigates. Relevant as evidence that
   *competition framing alone* shifts behavior → motivates our leaderboard-in-both-conditions control.

4. **Agentic Misalignment** (Anthropic 2025; arXiv:2510.05179): propensity methodology precedent
   (simulated corporate environments; harmful action rates). Key lesson: funneled binary dilemmas
   inflate rates. Our design keeps a neutral, always-available action (solve_ticket) to avoid funneling.
   Also: models acted more when scratchpads treated the scenario as real → motivates our
   eval-awareness logging. Aug 2026 news coverage of an Anthropic multi-agent experiment reports
   emergent inter-agent sabotage under competition (secondary sources only; unverified detail).

5. **SCHEME** (arXiv:2605.29178): multi-agent coordinated sabotage — capability/monitoring framing
   (can agents sabotage and evade monitors), not propensity-from-inequality.

## Kill / pivot / proceed decision

**PROCEED**, repositioned as a conceptual extension ("replication-adjacent"): the envy-like *preference*
construct is documented (neuralFOMO; econ-game inequity aversion). The open question this MVP targets:
does disadvantageous, visibly **unearned** inequality shift an LLM agent's **actions** along a
cooperation→hostility spectrum in a dry work setting with neutral-framed affordances — i.e., propensity,
not preference. No found study manipulates earned/unearned peer advantage with agentic tools.

Consequence for interpretation (argue-the-null discipline): prior work finding envy-like preferences
*raises* the prior of a positive result here, so a positive result gets **more** suspicion — demand
effects of the hostile affordance and leaderboard salience are live alternatives, logged in the report.

Sources (search-result links):
- https://arxiv.org/abs/2512.13481 (neuralFOMO)
- https://www.kansascityfed.org/research/research-working-papers/what-do-llms-want/
- https://arxiv.org/pdf/2408.02784 (LLM economicus)
- https://www.nber.org/system/files/working_papers/w31122/w31122.pdf
- https://arxiv.org/abs/2509.26126 (Hunger Game Debate)
- https://www.anthropic.com/research/agentic-misalignment ; https://arxiv.org/html/2510.05179v1
- https://arxiv.org/pdf/2605.29178 (SCHEME)
- https://arxiv.org/pdf/2506.04018 (misaligned-behaviour propensity measurement)
