# §Ch24 LEG 1 — SIX-ANGLE RECON + ADVERSARIAL VERIFY (2026-09-16)

> ⛔⛔ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. 24 Claude subagents (6 recon
> angles, each of whose top claims was then handed to 3 independent refuters). Every claim below
> carries a citation the agent quoted, but **a citation is a READ, not a measurement** — the
> authoritative docs win on any contradiction until a claim is verified in our own harness.
> ✅✅ **UPDATE, SAME DAY: §0'S LOAD-BEARING FACT IS NOW MEASURED, AND SO IS §6'S UNKNOWN #3.** `B` clears the post-victory msgbox (control returns in 297 frames) and a no-press CONTROL proves the box does not self-clear; and `calculate_path` DOES route to the door. See §0 and §6.3.

**Question asked:** why does a `ch24probe` drive stall after beating Sidney, and what does §Ch24
leg 1 actually need? **Angles:** (1) our code, (2) the dismiss machinery as a REUSE hunt,
(3) the decomp, (4) routing/mapping, (5) adversarial refutation, (6) blast radius.

---

## §0 — WHAT MUST BE MEASURED BEFORE ANY CODE DEPENDS ON THIS

✅✅✅ **ANSWERED 2026-09-16 (same day) — `B` CLEARS IT.** `--driver e4dismiss` from the pinned `post_sidney_door_open.ss1`: TREATMENT `controllable_after=True` in **297** frames, `prompts_cleared=2`; CONTROL (`POKEBOT_E4DISMISS_FAULT_NOPRESS=1`) `controllable_after=False` after its **full 2,600-frame budget**, printer still `(True,'WaitForButton')`. ⇒ the box does NOT self-clear. The angle-6 second-order worry below is also settled: `script_active_after=False`, so the script does not park active. Graded against predictions filed before the run (`2026-09-16-e4dismiss-PREDICTIONS.md`). —— *the question as it stood:* ⛔ **NO EVIDENCE FILE IN THIS TREE SHOWS THE SIDNEY POST-VICTORY MSGBOX EVER BEING DISMISSED BY THE
BOT.** The decomp says `waitbuttonpress` accepts `JOY_NEW(A_BUTTON | B_BUTTON)`; that is a READ.
Two independent angles (5 and 6) flagged this as the single claim the whole plan rests on, and both
declined to assert it. ⇒ **the next action is a drive that presses B at (6,6) from
`post_sidney_door_open.ss1` and asserts the avatar becomes controllable.** That fixture IS the stall
state (`probe_anchor_inventory`: `EVER_GRANDE_CITY_SIDNEYS_ROOM (6,6)`, *"‼ NOT a clean controllable
overworld"*), so the experiment costs seconds, not a 29,000-frame drive.

⚠ Second-order unknown from angle 6: if this specific script parks its global script context ACTIVE
after `release`/`end` (the KI-15 "phantom script" family), a B-rider would press for its whole budget
and hand back anyway. The same drive settles it.

---

## §1 — FOUR CORRECTIONS TO CLAIMS THIS PROJECT HAD ALREADY WRITTEN DOWN AS MEASURED

1. ⛔ **"~40 call sites" is wrong by 6.5×.** `wait_until_truly_controllable` has **262 `yield from`
   call sites** (303 grep lines = 262 calls + 36 imports + 4 comments + 1 def). **40 is the count of
   call sites lexically INSIDE a loop** — which is almost certainly where the figure came from.
   Per file: `early_game.py` 121, `victory_road.py` 60, `sootopolis.py` 33, `space_center.py` 15,
   `sootopolis_gym.py` 11, `pokemon_league.py` 8, `seafloor_cavern.py` 6, `mossdeep_gym.py` 3,
   `roster.py` 3, `counter_hunt.py` 1, `story_mode.py` 1.
2. ⛔ **"= 27174 + 1800 EXACTLY" is wrong arithmetic.** 28976 − 27174 = **1802**. The two extra
   frames are the Manual teardown (one frame for the driver to reach its trailing `yield` after
   `set_manual_mode()`, one for the harness to clear the stack). ‼ The conclusion is unaffected and
   in fact TIGHTER — but the wrong figure was copied verbatim into the punch list.
3. ⛔ **"4 drives out of 4" is AT MOST TWO TRAJECTORIES.** Three of the four are frame-identical
   (drop f26821, hang f46821, byte-identical party strings). Session-discipline rule 8: that is a
   determinism check replayed, never four replications. The honest count is **two**, both showing
   the same 1802.
4. ⭐⭐ **THE `(6,7)` vs `(6,11)` "CONFLICT" IS NOT A CONFLICT — AND OUR STANDING WARNING IS THE
   HALF THAT IS WRONG.** Both are correct readings at different instants of ONE six-step scripted
   walk. The room's entry warp is **(6,13)**; the entry script runs `Common_Movement_WalkUp6`;
   13−6 = **7**, so the auto-walk END tile really is **(6,7)**. Our probe's **(6,11)** is 13−2 =
   exactly TWO steps in. ⭐ **THE DISCRIMINATOR WAS ALREADY IN OUR OWN LOG:** the same drive recorded
   `elite4_state_in_room = 0`, and `setvar VAR_ELITE_4_STATE, 1` executes only AFTER
   `WalkInCloseDoor` returns — so at the instant (6,11) was sampled the auto-walk had **provably**
   not finished. ⇒ retire the claim *"(6,7) is WRONG"*; **keep the operational rule** (read the
   position back, never hardcode), which is right for a different reason.

---

## §2 — THE DIAGNOSIS, AND WHY THE FIX IS NOT NEW CODE

**The chain (angles 1, 3, 5 agree, and 5 was trying to refute it):** the field script `lock`s the
player, prints `MSGBOX_DEFAULT`, and only `release`s afterwards. `player_avatar_is_controllable()`
is False while "frozen" is set. ⇒ **the wait cannot merely lose a race here — it can NEVER succeed.**
It burns its full budget by construction, then returns with no success signal.

⭐ **BUT THE HEADLINE "IT FALLS TO MANUAL" IS REFUTED.** `context.set_manual_mode()` is the probe's
own **last statement**; the drop and the later `HANG CONFIRMED` are its DESIGNED handoff.
**MEASURED across the tree: 51 of 53 `HANG CONFIRMED` evidence files also carry an `ACCEPTANCE:`
line** (43 PASS + 8 FAIL), and the drop→HANG interval is exactly 20,000 frames in every sampled
case, including drivers unrelated to §Ch24. ⇒ that signature is the watchdog counting an idle
emulator. *(This is CLAUDE.md rule 2 exactly: read X to its LAST statement.)*

⇒ **The defect is best stated as: the probe called the press-NOTHING wait where a press-SOMETHING
helper was required.** Three already-shipped candidates:

| helper | gate | status |
|---|---|---|
| `early_game.py:639 _wait_until_cutscene_over` | `script_running or is_waiting_for_input()` | both conjuncts MEASURED true in the stall |
| `_ride_out_scripted_scene("B")` | same | **already inserted before the wait at `early_game.py:3290` and `story_mode.py:3683`** |
| `normalize_to_overworld()` | B-presses on a cadence until stable | documented *"safe to call unconditionally"*; the playbook already prescribes it for this shape |

⭐ `modules/tasks.py:199 is_waiting_for_input()` is **the same predicate** as the log's
`WaitForButton`, not merely similar: both read `sTextPrinters` offsets 0x1B/0x1C and accept raw
states 2/3. ⇒ the existing rider provably WOULD press here.
⭐ The edge is already supplied by the emulator: `press_button` auto-alternates (`libmgba.py:476`),
so a per-frame call is a 50% duty cycle = a real `JOY_NEW` edge every other frame.

### ⛔⛔ IT MUST PRESS **B**, NOT A
The bot stands at (6,6) facing NORTH at Sidney's object at (6,5), and his script is **re-triggerable
after defeat** into another `MSGBOX_DEFAULT`. An A-mash re-opens the box it just closed — a
livelock this project has already paid for. **KI-93's own dismiss presses B**, on one frame in 12
(`_KI93_DISMISS_PERIOD = 12`). Any helper that copies KI-93 and presses A is copying it backwards.

### ⛔ RECOMMENDATION FROM THE BLAST-RADIUS ANGLE: CHANGE NEITHER
Not the shared function (262 sites, **≥7 actively hostile to an A-press**, including
`roster.py:167` where the START MENU is deliberately still open — an A there could hit SAVE;
`victory_road.py:2977`, the League nurse, where mashing A was MEASURED to heal nothing; and
`victory_road.py:3207/:3226` inside shop menus). Not a new sibling either. **Insert the EXISTING
rider before the sequencer's wait — one line, one call site.**
⚠ Counter-evidence the angle volunteered: `_wait_until_cutscene_over` can RAISE after 8000 frames,
converting a silent hang into a loud `BotModeError`. That is an improvement, but the sequencer must
wrap it the way `roster.py` does if it needs to continue.
⚠ **The docstring's press-veto is UNSOURCED** — *"probing showed that mashing inputs at it only
prolongs the flicker"* has no probe, decision-log entry or changelog behind it; `git log -S` finds
only the commit that first wrote the sentence. Treat it as a caution, not a measurement.
⭐ **If the shared function is ever changed, the A/B target is `--driver ch23heal`** — it hits the
function 7× on a short, encounter-free, NPC-free happy path and contains the most A-hostile site in
the tree, so an A-pressing arm should FAIL it. ⛔ The obvious target `--driver traintest` is
**VACUOUS**: `train_team` reaches the function only via two table-gated helpers, and Route 116 is in
neither table.

---

## §3 — THE DECOMP: HOW MANY PRESSES, AND WHAT THE STALL DUMP ACTUALLY MEANS

* **Both `\p` (CHAR_PROMPT_CLEAR) and `\l` (CHAR_PROMPT_SCROLL) park on an edge-triggered A/B wait
  with NO timeout.** `\l` is NOT a free line-scroll — it costs a press exactly like `\p`.
  `MSGBOX_DEFAULT` = `Std_MsgboxDefault`, which ends in a THIRD such wait, `waitbuttonpress`.
* **FIELD presses between the win and `release`:** Sidney **3**, Phoebe **4**, Glacia **2**,
  Drake **6**, Wallace's post-battle speech **7**. Plus ≥2 IN-BATTLE presses every win (the
  "Player defeated …" and "got ¥… for winning!" strings both end in `\p`).
  ⇒ totals: Sidney 5, Phoebe 6, Glacia 6, Drake 8. Wallace never returns control (see §4).
* ‼ **Glacia's and Wallace's in-battle lose-texts contain `\p`/`\l` (2 and 4); Sidney's, Phoebe's
  and Drake's contain none.** ⇒ **the Sidney drive never exercised the KI-93 in-battle dismiss path
  for a trainer lose-text.** Glacia and Wallace are the first rooms that will. UNTESTED, not broken.
* ⛔⛔ **`cb=`, `instr=` AND `bt=` IN THE `STUCK-OW` DUMP ARE DEAD RESIDUE, NOT LIVE STATE.**
  `BattleScript_PayDayMoneyAndPickUpItems` is the 3-byte tail of the win script and `Cmd_end2` does
  not advance `gBattlescriptCurrInstr`, so the pointer freezes on that byte forever and a
  nearest-preceding-symbol lookup prints that label. `gBattleMainFunc` and `gDisplayedStringBattle`
  are likewise never cleared on battle exit. ⇒ **only `state=`, `textprinter=`, `tasks=` and
  `scripts=` describe live state.** Every past reading of that instruction name as a clue was noise.
* `TextPrinterState.WaitForButton` in our reader can ONLY mean `\p` or `\l`. Nothing else maps to it.

---

## §4 — ROUTING: THE BACKBONE, AND FOUR TRAPS NOT RECORDED ANYWHERE IN OUR TREE

**BACKBONE** (every hop re-fetched from `map.json`): `EVER_GRANDE_CITY (18,6)` walk N into (18,5)
→ `LEAGUE_1F (9,11)`; `(9,1)/(10,1)` → `HALL5 (5,12)`; walk to `(5,2)` → `SIDNEYS_ROOM (6,13)`
→ auto-walk to `(6,7)`; `(6,2)` → `HALL1 (5,12)`; … repeating through Phoebe/Glacia/Drake;
`DRAKES_ROOM (6,2)` → `HALL4 (5,33)` (11×34, the long corridor) → `CHAMPIONS_ROOM (6,12)`
→ auto-walk `(6,6)`; then **a scripted warp**, not a tile.

1. ⛔⛔ **THE LAST HOP IS NOT A WARP TILE.** The post-Wallace sequence is one locked cutscene that
   script-walks the player, makes them invisible, and hard-warps BY COORDINATE to
   `HALL_OF_FAME (7,16)` — not to warp#0's tile. **A sequencer that navigates to (6,2) in the
   Champion's room is building for a hop that does not exist.**
2. ⛔⛔ **THE ENTRY AUTO-WALK IS CONDITIONAL, ON A VAR THE BOT DOES NOT CONTROL.** Each room's
   `OnFrame` gates on `VAR_ELITE_4_STATE == k-1` (Sidney 0, Phoebe 1, Glacia 2, Drake 3) and then
   sets it to k. Enter room k with any other value and `WalkInCloseDoor` does **not** run — **no
   auto-walk AND no entry seal.** A leg that waits for the auto-walk would hang; a leg that assumes
   it happened would act from the wrong tile.
3. ⛔ **THE CHAMPION'S ROOM HAS NO PRE-BATTLE WINDOW.** Entering auto-walks and `goto`s straight
   into Wallace's intro + battle — no controllable frame, no NPC, no chance to heal.
   ⇒ **healing must happen before the Hall4 → ChampionsRoom warp.**
4. ⭐ **`get_map_objects()` INCLUDES THE PLAYER, as local_id 255.** The BFS spec in the earlier note
   says "object positions come from `get_map_objects()`" without that caveat — a BFS treating every
   returned object as an obstacle would wall off its own starting tile.

**ONE-WAY — now settled by TWO independent mechanisms, and it applies at the FIRST hop too.**
Besides the entry seal, the halls' three southern "backward warps" at (4,12)/(5,12)/(6,12) sit on
metatile 738 = **`MB_NORMAL`**, and `TryStartWarpEventScript` fires only if
`IsWarpMetatileBehavior()` is true, which `MB_NORMAL` is not. ⇒ those entries exist only as arrival
destinations and can never be triggered by stepping on them. Hall5 shares that layout, so **the
lobby is unreachable on foot from the moment the bot steps through (9,1)** ⇒ bag healing between
rooms is a HARD requirement, and the pre-gauntlet stock-up is a single-shot opportunity.
⭐ This also REFUTES the BUILD-SPEC's *"a lateral nudge silently undoes a cleared room"*.

**GEOMETRY.** The four E4 rooms are 13×14 with **byte-identical collision AND elevation grids** ⇒
one routine genuinely serves rooms 1–4. Floor plan: rows 0–2 blocked; **row 3 fully walkable
x=0..12**; rows 4–8 walkable only x=2..10; rows 9–11 fully walkable; rows 12–13 only x=5,6,7.
⇒ routing around the trainer at (6,5) costs **exactly one lateral tile**:
`(6,6) → (5,6) → (5,5) → (5,4) → (5,3) → (6,3) → (6,2)` = **six steps**. Only the final tile is
KI-74-affected.

* ⭐⭐ **THE EXIT DOOR WILL WARP WHEN STEPPED ON — with a positive control.** The victory script
  writes `METATILE_EliteFour_OpenDoor_Opening = 0x345`; our drive read exactly `0x345` there live;
  metatile 0x345's attribute byte is `0x60` = **`MB_NON_ANIMATED_DOOR`**, which IS accepted and is
  step-on. **The halls' working north door (5,2) is the same metatile.** ⚠ Still NOT verified live:
  no run has stepped on it.
* ⛔ **THE DOOR-OPENER ALSO SEALS TEN TILES.** It makes (6,1)/(6,2) passable **and (0..4,2) and
  (8..12,2) IMPASSABLE**. A live-grid reader must pick up both halves.
* ‼ **THE ENTRY SEAL IS SIX TILES, NOT THREE.** Our probe read only (5,13)/(6,13)/(7,13); the script
  also seals the whole row y=12. *(A sealed tile reads collision **3**, not 1 — `MAPGRID_IMPASSABLE`
  sets both bits. Our measured LIVE=3 corroborates the script byte-for-byte.)*
* **The front door differs in CLASS from every other hop:** `EVER_GRANDE_CITY (18,5)` is
  `MB_ANIMATED_DOOR` with collision 1 — it cannot be stood on, and fires via walk-into from (18,6).
  Every interior hop is `MB_NON_ANIMATED_DOOR` (step-on). **A sequencer that treats all six doors
  alike gets the first one wrong.**
* **Halls contain nothing to handle** — no objects, no triggers; every hall leg is a straight
  northward walk with no branching.
* **Lobby:** nurse object (3,2) behind an `MB_COUNTER` at (3,3) ⇒ stand **(3,4)** facing North;
  clerk (16,2) ⇒ stand **(16,4)**. The guards sit at (9,2)/(10,2) only while `FLAG_ENTERED_ELITE_FOUR`
  is unset.
* **`KI-74` does not blind the WARP TABLE**, only the collision/metatile grid — `warps_to` comes
  from the static warp-event list. That is why `map_path.py:841`'s destination exemption may apply.

---

## §5 — METHOD NOTES WORTH KEEPING

* ⛔ **`gh api` CORRUPTS BINARY PAYLOADS ON THIS WINDOWS BOX** — it applies LF→CRLF to stdout, so
  decomp `.bin` files come back inflated and sometimes an ODD number of bytes (impossible for a u16
  array). Hall4's 748-byte `map.bin` arrived as 1085. Use `urllib.request` against
  `raw.githubusercontent.com`. **The contents API's own `size` field is the detector.**
* ⚠ `battle_action_selection.py:349-352` asserts "a HELD button is invisible" and that the loop above
  "mashes B every frame", implying a hold. `libmgba.py:476` auto-alternates, so a per-frame press is
  a 50% duty cycle, not a hold. Both can be true, but a future agent relying on that comment to argue
  a field rider cannot dismiss a park would be **wrong**.

## §6 — REMAINING UNKNOWNS (carried, not hidden)

1. **The §0 drive** — does a B press at (6,6) clear the box and return control? Unmeasured.
2. Whether `(6,2)` actually warps when stepped on. Everything needed is established; no run has done it.
3. ~~Whether `calculate_path` returns a route to `(6,2)`.~~ ✅✅ **ANSWERED 2026-09-16 — IT DOES, AND
   THE BFS §G' SPECS SHOULD NOT BE BUILT.** `--driver e4dismiss` makes the call from the real
   post-dismiss state: **6 waypoints**, `SIDNEYS_ROOM (5,6)→(5,5)→(5,4)→(5,3)→(6,3)` then
   **`HALL1 (5,12)`** — around the standing trainer at (6,5) and out through the warp, onto exactly
   the tile §4's backbone predicts. Controls: `(5,6)` OK (planner works), `(0,0)` REFUSED (not saying
   yes to everything), and the discriminator **`(6,1)` REFUSED** — adjacent to (6,2), identical in
   both grids, differing only in `warps_to` ⇒ `map_path.py:841`'s destination-warp exemption is
   demonstrably the mechanism. **No earlier guard rejects the tile.** `KI-74` blinds the COLLISION
   GRID; `warps_to` comes from the static warp-event table it never touches. ⚠ Necessary, not
   sufficient: a `calculate_path` OK is not proof the DRIVEN navigator can walk it (`KI-48`).
4. Phoebe/Glacia/Drake post-victory LIVE grids — inferred from byte-identical ROM layouts + a shared
   helper, **not measured**.
5. Whether our KI-93 in-battle dismiss fires for a trainer lose-text (first exercised at Glacia).
6. ROM collision of (5,2) and (7,2) — the only two tiles in row y=2 the opener does not rewrite.
7. Hall of Fame metatile BEHAVIORS — the agent's own method returned an implausible result and it
   said so; do not quote them. Does not affect the route.
8. `2026-09-02-ch21return-DRIVE2-MSGBOX-HANG.stdout.txt` was never opened — its name suggests a
   possibly genuine msgbox-hang precedent worth a dedicated read.
