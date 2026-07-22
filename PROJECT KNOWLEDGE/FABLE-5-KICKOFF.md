# FABLE 5 — KICKOFF PROMPT & BRIEFING

> This file is written to be pasted to (or read first by) the **Fable 5** agent taking over
> the Story-bot build. It is your running start. It gives you the mission, the rules, where
> we are, and the immediate next move — then gets out of your way. **You decide how to
> proceed.** Written 2026-07-21 by the previous agent (Opus 4.8).

---

## Your mission

Power through the **Pokémon Emerald Story-mode bot** (a fork of 40Cakes/pokebot-gen3) so it
plays, unattended and **faithfully**, from a fresh save toward the Elite Four — building and
validating one chapter at a time. The Story bot is a **deterministic reference playthrough**
for a sibling project ("Pokémon Emerald AI"); keeping its behaviour natural and its notes
good directly serves that project too.

You are more capable at building than the previous agents — so **build more, validate as you
go, and document with even more detail and intent than we did**, without inventing unverified
"facts."

## Read these first (in order), then act

1. **`04-HANDOFF.md`** — exactly where we are, what just changed, what's next, open blockers.
2. **`14-AGENT-PLAYBOOK.md`** — THE craft: the faithful test harness, the debugging method
   (reproduce → fault-inject A/B → fix → prove), static ROM recon → Area Atlas → build →
   validate, the renderer-gated faithful-vs-fallback pattern, and the recurring
   bug-patterns → prevention table. **Follow it. Keep it current.**
3. **`12-STORYMODE-DESIGN.md`** — the Story chapters + the Area Atlases (reconned coords) +
   per-chapter build/validate notes. The immediate next chapter's atlas is §Ch6.
4. Skim **`08-MISTAKES.md`** (don't repeat solved bugs), **`03-PUNCH-LIST.md`** (the queue),
   **`05-KNOWN-ISSUES.md`**, **`06-DECISIONS-LOG.md`** (why things are the way they are).
5. Root **`CLAUDE.md`** = the standing directives (session-start ritual, definition of done,
   two-folder layout, promotion discipline, upstream check).

## The non-negotiable rules (from the playbook — internalize)

- **Prove every fix.** Reproduce the bug first; prefer a fault-injected A/B (old fails / new
  passes on the same input). No guessing. This is the #1 house rule.
- **Faithful to natural gameplay.** Do what a player does. A state-write (setting a var/flag)
  is a *last-resort fallback*, only when the faithful path is impossible/un-provable, and it
  must reproduce the EXACT vanilla end-state. Ask the user on genuine faithfulness tradeoffs.
- **Never hang / never silently derail.** Bound every loop. Un-fleeable battles
  (trainer/gym/E4) must fight through to win-or-whiteout. Guard every "did it work?".
- **Document with intent + WHY**, per completed item (changelog + decision + mistake+prevention
  + handoff), then commit + push. Leave the docs better than you found them; add new tricks to
  the playbook. This is cost control, not bookkeeping.
- **Sandbox first.** Build/test in `sandbox-pokebot/`; promote to `custom-pokebot/` only on the
  user's explicit OK, with DIVERGENCE-LOG entries for any upstream-file edits.
- **Keep the sibling-AI notes current** (`Pokemon_Emerald_AI_Notes.md`) — reference-behaviour
  learnings that help the Pokémon Emerald AI project.

## Where we are (frontier)

The bot plays a fresh save through: intro → starter → Route 103 rival → Pokédex → Petalburg →
Wally → Petalburg Woods → **Rustboro Gym (Roxanne)** → Devon Goods → **PokéNav + faithfully
completing the Match-Call tutorial** → **Rustboro rival** (type-aware lead + level-floor + heal
+ attempt-cap). A full fresh run **beat the rival** and produced `post_rival.ss1` (player
controllable at **Rustboro (16,53)**, `RUSTBORO_CITY_STATE=8`, `DEFEATED_RIVAL_RUSTBORO=True`).

**Immediate next build:** the **sail leg** — from Rustboro (16,53), walk **south** across the
map connection onto **Route 104**, go to **Mr. Briney's cottage**, talk to Briney (5,3) →
pick **Dewford (multichoice index 0)** → sail to **Dewford Town**. Then **Granite Cave**
(deliver Steven's Letter to Steven, Steven's Room (7,8)) and **Gym 2 — Brawly** (Knuckle
Badge). All of this is mapped in **§Ch6** (verify each warp/coord live — a couple resolved
oddly in static recon).

## How to get a post-rival save (you'll need one to build the sail leg)

`post_rival.ss1` was generated in the previous session's (now-gone) scratchpad. Regenerate it:
run a fresh game to the rival and win, OR resume from a rival-prep checkpoint. The reliable
recipe is in the playbook §2 (fresh run → extract the raw state from the PNG-wrapped
`current_state.ss1` `gbAs` chunk → resume the story past the rival with the save-on-defeat
hook). If the previous session left a build-validated sail leg, `_play` will already carry you
past it — check the changelog/handoff for the latest.

## Open issues worth knowing

- **Framework mid-battle rotation stall** (`battle_action_selection.py` `RotateLead` →
  `scroll_to_party_menu_index` → `while PARTY_MENU: press A`): a rotation into a mis-mapped or
  un-sendable slot can spin. The Story bot sidesteps it (attack-only in trainer battles), but
  any *rotating* strategy is exposed. A good deep-dive: reproduce a live rotation and pin
  `map_battle_party_index` / the party-menu submenu handling.
- **Event-flag 1-frame read flicker** — require a flag stable for many consecutive frames.
- **Cross-map navigation** often needs leg-by-leg (stage tile → step across the connection →
  navigate next map). The global navigator can't always one-shot it.

## Your freedom

Decide the order, the depth, and the method — as long as you respect the mission, the rules,
and the sibling-AI documentation duty. Reasonable defaults: continue the story from the frontier
(sail leg → Dewford → Granite Cave → Brawly → onward), deep-mapping each area first (ROM recon
→ atlas), building the segment, validating in the harness, and documenting with intent. When a
faithfulness or scope call is genuinely the user's, ask. Otherwise, power through — and leave
`14-AGENT-PLAYBOOK.md` and the atlases richer for whoever comes after you.
