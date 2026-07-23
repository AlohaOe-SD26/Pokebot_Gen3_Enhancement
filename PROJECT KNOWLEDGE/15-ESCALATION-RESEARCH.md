# 15 — Escalation: external research for stuck story sequences

> **What this is:** the LAST rung of the `/validate-docs` ladder. When a story-mode
> sequence can't be resolved from the decomp + live recon + walkthroughs + reasoning,
> the agent stops burning budget on it, PAUSES that sequence, and hands a precise
> research question to an EXTERNAL AI agent (e.g. Gemini) via two copy-paste prompts.
> The external agent's answer is a **lead, not gospel** — it is VERIFIED against the
> decomp/harness before any code is written (house rule: prove every fix).
>
> Motivating case: KI-11 (the Oceanic Museum grunt-seal was a missing story STEP — talk
> to Dock at Stern's Shipyard — invisible to static recon, obvious in a walkthrough).

## Two different research shapes (don't confuse them)
- **Escalation (this document)** — SURGICAL. One stuck sequence, asked only after the
  recon ladder below is exhausted. Keep it rare.
- **Full-game deep research** — BROAD, and deliberately NOT gated on being stuck:
  `sandbox-pokebot/profiles/GEMINI-FULLGAME-RESEARCH.md` commissions a whole-game,
  bot-grade walkthrough in one Deep Research run, to be re-run periodically so mapping
  detail lands AHEAD of the build frontier instead of being derived at build time.
  Commissioned 2026-07-23 (user directive). Same house rule: leads, not gospel.

## When to escalate (the trigger threshold — keep it RARE)
Only after ALL of these are exhausted for the sequence in question:
1. Decomp (`pret/pokeemerald`) read for the relevant maps/scripts.
2. Live ROM recon (probes: coords, collision, live objects, flags/vars).
3. Walkthrough(s) consulted for step order.
4. My own reasoning + a direct ask to the user (fastest when they know it).

If it's still ambiguous, escalate. Never use this as a shortcut around doing the recon.

## The two prompts
- **PRIMER (Prompt A)** — reusable, model-agnostic. Sets up a fresh research agent with
  the project context + the answer format I need. Paste it ONCE into a new agent chat
  (or re-paste into a fresh chat when the old one's context gets too large). Stored below
  verbatim.
- **QUESTION (Prompt B)** — generated per escalation: the exact sequence ambiguity, what
  I've already TRIED and RULED OUT (so they don't re-walk dead-ends), and the answer
  format. The `/escalate-sequence` command writes this to a scratch file for the user to
  relay.

## After the answer comes back
1. Treat every claim as a LEAD. VERIFY each flag/var/coord/trigger against the decomp
   (WebFetch) and/or the harness (a probe or a segment run) BEFORE building.
2. If verified → build the segment, update the doc section with the now-confirmed
   sequencing (tag `✓ external-research + verified`), then commit.
3. If wrong/vague → note it and either re-ask with tighter constraints or fall back to
   the user. The external agent never bypasses "prove every fix."

## Model-agnostic by design
The primer works whether pasted manually into **Gemini** (the cost-effective default —
keeps research off Claude's credits) OR fed to a spawned Claude sub-agent (a possible
future automation — see the note at the bottom). Same prompt, either route.

---

## PRIMER (Prompt A) — paste into a fresh research agent first

```
You are a research assistant helping build a faithful, automated Pokémon Emerald
story-mode bot. I will send you specific questions about Pokémon Emerald's STORY
SEQUENCING, and your job is to dig through authoritative sources and return precise,
game-internal, CITED answers.

## The project (context you need)
- The bot plays Pokémon Emerald (Generation 3, Ruby/Sapphire/Emerald engine, USA
  version) from a fresh save toward the Elite Four, unattended and FAITHFULLY — it does
  exactly what a legitimate human player does: walks to places, presses the buttons,
  fights the battles. No cheats, no teleporting past content. It runs on the
  40Cakes/pokebot-gen3 framework (Python controlling the libmgba emulator).
- It also serves as a DETERMINISTIC REFERENCE PLAYTHROUGH for a sibling "Pokémon Emerald
  AI" project, so the accuracy of the story sequence matters a great deal.
- Because it is faithful, I need to know the EXACT in-game mechanics behind each story
  beat: which flags/vars gate it, which NPC or tile trigger advances it, the precise
  ORDER of steps a player must perform, and the coordinates involved. "Roughly how the
  quest works" is not enough — I translate your answer into code and verify it against
  the game's memory, so exact identifiers and ordering are what matter.

## What I need in every answer
1. The exact ORDER of player steps to trigger/complete the beat (numbered).
2. Game-internal identifiers: FLAG_* and VAR_* names, EventScript_* / map-script
   symbols, exact map names, and tile coordinates / warp destinations where relevant.
3. The trigger for each step (talk to NPC X at tile (x,y); step on coordinate (x,y); a
   flag/var reaching a value; a prior battle won; etc.).
4. What each step SETS (which flags/vars) and how completion is detected.
5. A CITATION for every factual claim — prefer the pret/pokeemerald decompilation
   (github.com/pret/pokeemerald: data/maps/<MapName>/scripts.inc,
   data/maps/<MapName>/map.json, and src/*.c) for flags/vars/scripts/mechanics; use
   written walkthroughs (Bulbapedia's Emerald walkthrough, Serebii, GameFAQs) for step
   ORDER and prerequisites.
6. Explicitly flag anything you are UNSURE about, and note how it could be verified
   in-game.

## Sources, in priority order
- Mechanics / flags / vars / scripts / coordinates: the pokeemerald decompilation
  (pret/pokeemerald on GitHub). Authoritative for WHAT the game sets and WHERE.
- Step order / prerequisites / "you must do X before Y unlocks": written walkthroughs
  (Bulbapedia, Serebii, GameFAQs).
- If two sources disagree, tell me WHY — the discrepancy is usually the real mechanic
  (e.g. a hidden flag set by an earlier, easily-missed step).

## Ground rules
- Precision over prose. Exact names and coordinates beat readable explanation.
- Do not guess silently. If you cannot find something, say so plainly.
- If a question is ambiguous, ask me to clarify rather than assuming.

Reply "Ready" and I will send the first question.
```

---

## QUESTION (Prompt B) — template the `/escalate-sequence` command fills in

```
QUESTION — <one-line summary of the stuck sequence>

Game: Pokémon Emerald (USA), Gen 3.

What I'm trying to do (in the bot):
<the story beat the bot must perform, and where the bot currently is>

What I already know / have verified myself (don't re-derive these):
- <decomp facts confirmed: flags/vars/scripts/coords>
- <recon facts confirmed: live object positions, collision, current flag/var values>

What I've RULED OUT (dead-ends — don't send me back down these):
- <approaches tried that failed, with why>

The exact ambiguity I need resolved:
<the precise unknown — usually the TRIGGER or the ORDER of a step>

Answer format I need (per the primer): numbered player steps; the FLAG_*/VAR_*/
EventScript_* identifiers; the trigger + coords for each step; what each sets; and a
citation (decomp path or walkthrough URL) for each claim. Flag anything uncertain.
```

---

## Future automation note (NOT built — discussion record 2026-07-22)
Three possible execution routes for the research call; the primer is model-agnostic so
the SAME prompts drive all of them:
1. **Manual paste to Gemini (CURRENT DEFAULT).** Zero setup, zero Claude credits; the
   user relays prompts/answers. Proven workable.
2. **Gemini via API (user-proposed 2026-07-22 — the designated automation path).** The
   agent can call HTTP APIs from this environment, so given a Gemini API key it could
   send primer+question programmatically and parse the reply — automating
   /escalate-sequence end-to-end while still keeping research costs on Gemini.
   Requirements when built: the key lives in a GITIGNORED env file / environment variable
   (NEVER committed — git-conduct rules); calls are logged (question + answer archived
   alongside the doc correction they produced); the verify-before-build rule is unchanged.
3. **Internal Claude sub-agent** (Fable 5 / Opus 4.8 both support spawning them, with
   WebSearch/WebFetch). Fastest integration but consumes Claude credits — reserve for
   when speed outweighs cost.
Decision so far: route 1 now; route 2 when the user provides a key and asks; route 3
exceptional. First real-world PoC: the Ch9 (Route 110 → Wattson) pre-build validation.
