---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets for Simulafoot, each declaring its blocking edges, published to the local tracker (.scratch/<feature>/issues/). Simulafoot-specific variant of Matt Pocock's to-tickets — adds adaptive depth (léger/standard/approfondi), CLAUDE.md's protected-file and constante-produit rules, and proportional PRD documentation. Supersedes the global to-tickets skill only inside this project.
disable-model-invocation: true
---

# To Tickets (Simulafoot)

Break a plan, spec, or conversation into **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it. This is the Simulafoot-scoped variant, audited and optimized on 23/10/2026 (see `docs/PRD_PRODUIT.md` for the audit's conclusions) — it supersedes `~/.claude/skills/to-tickets/` only inside this project, and never changes `/to-tickets` behaviour in any other project.

Tickets publish to the local tracker: one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first), per `docs/agents/issue-tracker.md`.

## 0. Pick the depth level first

Before gathering context, decide the level — it shapes how wide steps 1-2 and how strict step 4 are. Re-check it if new information changes the picture mid-flow (a "léger" ticket that turns out to touch a protected file becomes "standard" immediately).

**Trigger criteria, in order — the first one that matches wins:**

- Touches a file on CLAUDE.md's protected list (`events.py`, `simulation.py`, `narrative.py`, `narrative_player.py`, `ball_events.py`, `types.py`, `serialize.py`, `motion.py`, `sequence_generator.py`, `ball.py`, `templates.py`, `render/canvas.html`)? → at least **standard**, and **approfondi** if it's the Poisson/narrative engine (`events.py`, `simulation.py`, `narrative.py`) rather than the animation layer.
- Introduces a concept that doesn't exist anywhere in the engine yet (a new event type, a new invariant, a new calculation rule)? → **approfondi**, even if the request sounded small. A risk of breaking an already-documented invariant (score decided in advance, determinism) forces **approfondi** regardless of apparent size.
- Extends an already-validated mechanism without changing its shape (more items in an existing fixed catalogue, more positions covered by an existing pattern)? → **standard**, or **léger** if the extension is purely mechanical (one more line in a lookup table, one more reason in an already-fixed list).
- A pure tracker/wording fix with no code implication (renumbering, a "Blocked by" correction, a wording tweak on an already-published ticket)? → **léger**.

## 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number) as an argument, fetch it and read its full body.

**Reuse, don't re-verify.** A fact already confirmed earlier in this same conversation (a project rule, a file's current shape, an already-stated decision) stays valid — re-read only if the file changed since, or enough turns passed that it might have. Don't reopen a decision the user already gave a blanket approval for in this conversation.

## 2. Explore the codebase

**Léger**: skip unless one specific fact needs confirming — no broad exploration.
**Standard**: targeted checks only — the specific mechanism(s) the tickets touch, not a module-wide audit. Batch independent checks (several `grep`/`Read` calls for unrelated facts) into one tool round when they don't depend on each other's results.
**Approfondi**: also read the invariants documented near the code you're touching (module docstrings that say "never", "invariant", "jamais recalculé"...) and confirm none of them would be broken by the proposed tickets. Check for prior art — an existing mechanism (even partial) that the new tickets should extend rather than duplicate; this caught real duplicate-work risk before (e.g. the existing "mouvement collectif" support-initiative mechanism).

Look for prefactoring opportunities regardless of level: "make the change easy, then make the easy change."

## 3. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer: vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

</vertical-slice-rules>

Give each ticket its **blocking edges**: the other tickets that must complete before it can start, or "None". Distinguish a genuine technical dependency from a pure **priority/sequencing preference** (e.g. two tickets touch the same protected file and risk a merge conflict, but neither logically needs the other's output first) — state the latter as "ordre recommandé" in prose, never as a fake "Blocked by" edge; a reader should never have to guess which kind it is.

**Wide refactors are the exception to vertical slicing** — see the global skill's definition (unchanged here): sequence as expand → migrate batches → contract instead of forcing a tracer bullet.

**Before finalizing the draft, check for hidden sub-categories.** If a ticket's scope silently bundles several distinct real-world entities that could reasonably get their own ticket (positions, reasons, incident types, postes...), don't assume the bundled grain is right — flag it explicitly as a question in step 4 rather than discovering it later as a rework. (This is the one concrete lesson from the 23/10/2026 audit: a 3→9 ticket restructuring happened because this wasn't asked explicitly the first time.)

## 4. Quiz the user

Present the proposed breakdown as a numbered list — title, blocked by, what it delivers — proportional to the level:

**Léger**: one grouped confirmation is enough if several small adjustments are proposed together; don't ask once per ticket.
**Standard/Approfondi**: ask explicitly:
- Does the granularity feel right — in particular, **does any ticket secretly bundle distinct real-world entities (postes, reasons, types) that should split**?
- Are the blocking edges correct — technical dependency vs. priority-only, each genuinely gating?
- **Approfondi only**: confirm each sensitive point (a constant, an invariant interpretation, a scope boundary) individually — never bundle them into one yes/no when the stakes differ.

Don't re-ask a question the user already answered for this exact scope — a blanket approval ("formalise tout ce que tu proposes") covers every item it was given for, not just the first one.

Iterate until the user approves the breakdown.

## 5. Document proportionally (PRD)

Not part of the generic skill — a Simulafoot convention, scaled by level:

**Léger**: skip a PRD entry if the subject is already documented there.
**Standard/Approfondi**: add the user story and the decisions that would otherwise live nowhere else (reuse the exact wording pattern already in `docs/PRD_PRODUIT.md` — numbered user story + a "décisions de l'interview/constat du <date>" bullet). Batch multiple Edit calls to the same file in one pass (read once, edit several times in sequence) rather than re-reading between each.

## 6. Publish the tickets

Write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order. Use the template below.

**Reusable clauses — copy verbatim, don't recompose prose each time:**

- Protected file touched: `**Note :** <fichiers> sont sous exception (`CLAUDE.md`) — exception à demander/redemander explicitement au propriétaire avant de coder.`
- A value needs sign-off: `Propriétaire valide <quoi> AVANT implémentation (constante produit, règle `CLAUDE.md`).` as an acceptance-criterion checkbox.
- Shared mechanism dependency: `Le mécanisme consomme le facteur/table partagé(e) de `<ticket>`, ne recalcule pas son propre plafond/plancher.` as a checkbox, when a ticket builds on a shared-infrastructure ticket.

<local-ticket-template>

# \<NN\>: \<Ticket title\>

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective, not a layer-by-layer implementation list.

**Blocked by:** the numbers/titles of the tickets that genuinely gate this one, or "None (can start immediately)". A priority-only ordering goes in a separate "Ordre recommandé" sentence, never disguised as a blocker.

**Status:** ready-for-agent (or `decision-needed` for a ticket whose job is a decision, not a build)

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

Avoid specific file paths or code snippets in the ticket body: they go stale fast. Exception: a prototype snippet that encodes a decision precisely (state machine, schema), trimmed to the decision-rich part.

## 7. Transmit (multi-session only)

If the implementation happens in a different session than this one (this project's usual pattern — a worker session, `.claude/skills` scoped per project), send it a summary: what was created, why, which files, which exceptions/decisions still need the owner.

**Before `SendMessage`**: call `ListAgents` first whenever the target session's reference might be stale (anything beyond the immediately preceding turn) — a wrong/expired ref wastes a round trip for nothing, and this cost was observed directly in the 23/10/2026 audit.

## 8. Lightweight diagnostic (close every execution with this, 2-4 lines)

Not a persistent log file — just state it in the response that publishes the tickets:

- Depth level used, and which trigger fired it.
- Ticket count produced, and how many were "léger" adjustments vs new files.
- Any repeated/wasted operation noticed this pass (a re-read that didn't need to happen, a retry) — name it, don't hide it.

No fabricated token/time numbers — if precise measurement isn't available, say so rather than inventing one; the tool-call counts above are a reliable, honest proxy.
