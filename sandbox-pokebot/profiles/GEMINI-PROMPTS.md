# Gemini Relay Prompts — accumulated overnight (2026-07-22 →)
> Append-only. Each entry: what we need, why, what's already verified, and the
> exact prompt to paste after the standing primer (PROJECT KNOWLEDGE/15-ESCALATION-RESEARCH.md).
> The bot builds on with decomp-verified best answers + marked assumptions; these
> relays CONFIRM or CORRECT them when the user has time.

(no open prompts yet — appended as the overnight run surfaces them)

## Q1 (2026-07-22 overnight) — Lavaridge Gym trapdoor solve (Emerald)
**Need:** the canonical hole/vent sequence from the Lavaridge Gym entrance to Flannery
in EMERALD, as tile coordinates or precise directions.
**Already verified (decomp):** 1F has 20 hole tiles (metatile 104, fall to B1F) + landing
spots; B1F has 15 geyser-vent tiles (metatile 41, pop up to 1F); every warp pair in the
map.json is same-coordinate; Flannery stands at 1F (13,9); her platform (x=11-15,y=9-12)
is only entered via the B1F vent at (12,12) — but B1F's vent room (10-12,11-14) shows no
walk-in entry and the 1F hole above it is ON the platform (mutually recursive under a
literal warp-table model). So the REAL fall-landing mechanics must differ (e.g., falling
lands you OFFSET from the paired warp tile, or specific holes drop to non-warp tiles).
**Prompt to paste after the standing primer:**
"In Pokémon Emerald's Lavaridge Gym, describe the exact route from the entrance to
Flannery: every hole you fall through (1F tile coordinates if possible), every geyser
vent you ride up (B1F coordinates), in order. Also: when you fall through a 1F hole,
where exactly do you land on B1F relative to the hole's coordinates? Cite a walkthrough
or the decomp."

**Q1 addendum — live fall experiment results (use to sharpen the answer):** falling
through 1F hole (10,18) lands at B1F (10,18) — SAME coordinates, and the landing does
NOT auto-trigger anything (landings are safe; only fresh walk-ons trigger). B1F is
COMPARTMENTALIZED rooms: from the (10,18) landing the player could walk only a small
area ((10-12,16-18)-ish); the vents (5,9)/(3,14)/(3,10) were all unreachable from it,
and steps toward (13,17) were blocked. So the maze is a hole→room→vent chain; we still
need which vent lives in which room and the canonical chain to Flannery's platform.

## 2026-07-24 — KI-17: after-faint party-menu reshow freeze (decomp question)
CONTEXT: pokemon Emerald (pokeemerald decomp). Our bot fights a wild battle; a party mon
faints; the "choose next mon" party menu opens (BattleScript_FaintedMonTryChoose); a
living replacement is selected. The game then freezes forever in the transition back to
the battle screen with this exact memory profile: gMain.callback2 =
CB2_SetUpReshowBattleScreenAfterMenu, game state = party menu, active tasks =
[Task_ReturnToChooseMonAfterText, Task_PrintAndWaitForText] (never advancing — that CB2
does not run tasks), party-menu cursor on a living slot, action=1, menu_type_and_layout=17.
Input has no effect (A/B/Down for 400+ frames), with or without the renderer.
QUESTION: walk through CB2_SetUpReshowBattleScreenAfterMenu and ReshowBattleScreenAfterMenu
(gReshowState machine) in pokeemerald: (1) enumerate every step and what condition advances
each; (2) which steps can WAIT indefinitely, and on what (palette fade? sprite load? link?);
(3) under what circumstances would the party menu leave Task_PrintAndWaitForText +
Task_ReturnToChooseMonAfterText alive while callback2 has already switched to the reshow —
is that a known race (e.g. selecting a mon during an unfinished text print)? (4) what
button-timing pattern in the party menu could produce it, and what is the safest way for an
automated player to avoid it (e.g. never press A while the faint message printer is active)?
Cite file/function names from pokeemerald master.
