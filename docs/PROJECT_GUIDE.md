# PROJECT GUIDE — Agent Society / Matchmaker

This is the operating manual for working on this project across multiple Manus
chat sessions **without context rot**. Read this first in any new session.

> Core rule: **durable knowledge lives in the repo (files + git); transient
> reasoning lives in a chat.** A chat is a worker; this repo is the memory.
> Never end a session with important knowledge living *only* in the chat —
> write it to a file and commit it ("land it before you leave it").

## The repo is the source of truth

GitHub (private): `matchmaker-council`  ·  baseline tag: `v0-checkpoint`

Always start a session by cloning and reading the durable context:

```bash
gh repo clone <owner>/matchmaker-council && cd matchmaker-council
```

Then read, in order: `README.md` → `docs/post_final.md` → this file →
the track file you're working on. That inherits the durable context WITHOUT
inheriting any old chat's clutter.

## The three tracks (each gets its OWN chat session)

| Track | Chat scope | Reads first | Writes back |
|---|---|---|---|
| **A. Product development** | Build the spine toward a real product. Long-lived, iterative, code-heavy. | `README.md`, `ROADMAP.md`, code | Commits code; updates `ROADMAP.md` + `SESSION_LOG.md` |
| **B. Concept learning** | Learn loop engineering, evals, self-* concepts, etc. Exploratory, lots of throwaway Q&A. | `docs/post_final.md` | `docs/learning-notes/*.md` |
| **C. Deep research** | Expert-grounded research on dating, attraction, compatibility, marriage. Bounded deliverable. | `docs/research/RESEARCH_BRIEF.md` | `docs/research/*` report + sources |

Keep tracks in separate chats. They coordinate through repo files, not through
the model remembering anything.

## When to start a NEW session
- Switching tracks (product → research → learning). Always.
- A session has been compacted more than once and the model starts re-asking
  things or losing threads — that's the rot signal. Checkpoint to a file, start fresh.
- A task hits a clean deliverable boundary (e.g., "research report done").

## When to run PARALLEL sessions
- Independent tracks you want progressing at once (research while you build).
- A single track with many homogeneous sub-jobs (e.g., "profile 20 experts") —
  ask for that as one parallelized batch job, not 20 chats.

## When to STAY in the current chat
- Only tight follow-ups to the work already in that chat (tweak a file, re-run,
  fix a bug). Anything opening a new big track should leave.

## End-of-session checklist (do this EVERY time)
1. Did I write durable outputs to files (not just discuss them in chat)?
2. Did I commit + push? (`git add -A && git commit && git push`)
3. Did I append a dated entry to `SESSION_LOG.md` (what changed, where it lives,
   what the next session should pick up)?
4. Is there a clear "NEXT" line so a fresh session can resume without re-reading the chat?

---

## Paste-ready kickoff prompts

Copy the relevant block into a brand-new chat in this project.

### Track A — Product development
```
This is the Product Development track for the matchmaker-council project.
1. Clone the private repo `matchmaker-council` and read README.md, docs/PROJECT_GUIDE.md,
   docs/post_final.md, and ROADMAP.md.
2. Confirm you can run `PYTHONPATH=. python3 run.py` and `eval/experiment.py`.
3. Then work the top unchecked item in ROADMAP.md. Before we end, commit your
   changes, update ROADMAP.md, and append a SESSION_LOG.md entry with a NEXT line.
Do NOT do deep research or open-ended concept tutoring here — those are other tracks.
```

### Track B — Concept learning
```
This is the Concept Learning track for the matchmaker-council project.
1. Clone `matchmaker-council`, read docs/post_final.md and docs/learning-notes/INDEX.md.
2. I want to learn <CONCEPT> (e.g., loop engineering / LLM-as-judge evals /
   self-healing patterns / hill-climbing). Teach me Socratically using OUR codebase
   as the running example, and where useful point me to the exact files/lines.
3. Capture what we cover as a new note in docs/learning-notes/ and commit it.
Keep this exploratory and separate from product code changes.
```

### Track C — Deep research
```
This is the Deep Research track for the matchmaker-council project.
1. Clone `matchmaker-council` and read docs/research/RESEARCH_BRIEF.md.
2. Execute that brief: deep, expert-grounded research on dating, attraction,
   compatibility, and lasting marriage, with credible citations.
3. Deliver a structured report into docs/research/ and commit it, plus a
   short "implications for the matchmaker design" section linking findings back
   to our agents/labels. Append a SESSION_LOG.md entry.
You do not need the application code for this track.
```
