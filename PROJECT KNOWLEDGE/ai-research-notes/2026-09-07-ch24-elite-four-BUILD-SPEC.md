# §Ch24 (THE ELITE FOUR) — build spec from a 7-agent recon. ⚠ A NOTE, NOT TRUTH.

**Produced 2026-09-07** by a 5-angle recon (maps, opposition, our code, healing, hazards) + an
adversarial verifier + a synthesis pass. ⛔ Per `ai-research-notes/00-READ-THIS-FIRST.md` this is a
**NOTE**: the authoritative docs win on any contradiction until a claim is verified here.

⭐ **THE ADVERSARY FOUND NINE ERRORS IN THE RECON AND THE SPEC TOOK THE ADVERSARY IN ALL NINE.** That
is the reason to trust the shape of this document and still probe its numbers. **One of those nine was
a defect in OUR OWN COMMITTED DOCS** — see "already actioned" below.

---

## ✅ ALREADY ACTIONED FROM THIS RECON (not pending)

* **`KI-96`'s line citation was WRONG in our docs.** We cited
  `battle_action_selection.py:590-592`; the loop is at **672** (verified in BOTH forks). The `KI-93`
  fix and the `KI-96` census grew the file after `KI-96` was filed. Corrected in `04-HANDOFF.md` (3
  sites) and `05-KNOWN-ISSUES.md` (1).
  ⭐ **Why no gate caught it:** `audit_doc_citations.py` resolves `symbol` + `file.py:LINE` PAIRS; a
  **bare line number has no symbol to resolve against**. ⇒ **cite the SYMBOL.**

---

## THE SHAPE OF THE CHAPTER (high confidence)

Dispatch **on where the bot is**, never down a fixed list — the §Ch23 pattern. Every leg self-skips on
position, so a resume mid-gauntlet works.

| leg | action | acceptance check |
|---|---|---|
| 1 | heal + confirm the league basket | `party_is_gauntlet_ready()` |
| 2 | lobby: face N at (18,6), hold Up (animated door) | map == `..._POKEMON_LEAGUE_1F` |
| 3 | guards: approach **from x ∈ {9,10} only**, talk N | `FLAG_ENTERED_ELITE_FOUR` set |
| 4 | door → **HALL5** (Hall5 is FIRST, then 1→2→3) | map == `HALL5` |
| 5-8 | per room: locate trainer live, step adjacent, press A | `VAR_ELITE_4_STATE == k` |
| 5b-8b | **heal between fights** — raise if not ready | `party_is_gauntlet_ready()` |
| 9 | `HALL4` is **31 tiles** (5,33)→(5,2) — budget for it | map == `CHAMPIONS_ROOM` |
| 10 | **Wallace: do NOT press A** — an `OnFrame` script on `VAR_TEMP_1==0` starts it | battle entered |
| 11 | scripted warp to `HALL_OF_FAME` | map == `HALL_OF_FAME` |
| 12 | done | `FLAG_SYS_GAME_CLEAR` |

**Verified structural facts:** all 15 `MapRSE` names exist in our `map_data.py`; rooms are 13×14 with
entry warp (6,13) and forward warp (6,2); trainer tile is (6,5) in all five rooms; the door-opening
script sets `impassable=FALSE` on (6,1)/(6,2) and **seals (5..7,12..13) behind you**.

---

## ⛔ THE THREE THINGS THAT WOULD BREAK A NAIVE BUILD

1. **⛔⛔ DO NOT GRADE ON THE `DEFEATED_ELITE_4_*` FLAGS.** `ResetEliteFour` clears all four flags **and**
   `VAR_ELITE_4_STATE`, and it is called from **both** `EventScript_WhiteOut` **and** the win path
   (`hall_of_fame.inc`). ⇒ a done-check built on them reads False *after victory* and re-enters §Ch23
   with a spent basket. **This is exactly the "a position can be reached by succeeding OR by failing"
   reversal this project already paid for in `victory_road.py`.**
2. **DO NOT HARDCODE THE LANDING TILE.** The auto-walk end-state is (6,7), but a **re-entry has no
   auto-walk at all** — the player stands at (6,13). Locate live, every time.
3. **The five fights are not alike.** Hall5 is the entrance (not Hall1); Hall4 is 31 tiles; the four
   E4 members have **no sight line** (approach + A).
   ⛔⛔ **CORRECTED 2026-09-10 — THIS READ "while **Wallace has no A-press trigger**" AND IT IS FALSE.
   A BOT BUILT ON IT HANGS FOREVER AT THE LAST FIGHT OF THE GAME.** Read from the decomp, twice, by
   two independent readers:
   ```
   EverGrandeCity_ChampionsRoom_EventScript_Wallace::
       playbgm MUS_ENCOUNTER_CHAMPION, FALSE
       msgbox EverGrandeCity_ChampionsRoom_Text_IntroSpeech, MSGBOX_DEFAULT   ← A PRESS REQUIRED
       trainerbattle_no_intro TRAINER_WALLACE, ..._Text_Defeat
   ```
   and `data/scripts/std_msgbox.inc:18-22` — `Std_MsgboxDefault: message NULL / waitmessage /
   **waitbuttonpress** / return`. ⇒ Wallace's intro speech parks on an **EDGE-TRIGGERED** press with
   **no timeout**. `trainerbattle_no_intro` means "no trainer-INTRO text", **not** "no dialogue".
   ‼ **AND THE WIN NEEDS ANOTHER ONE**: `..._EventScript_Defeated` opens the door then runs
   `msgbox ..._Text_PostBattleSpeech, MSGBOX_DEFAULT` — a second `waitbuttonpress` between beating
   Wallace and reaching the Hall of Fame.
   ⭐ **THIS IS `KI-93` VERBATIM, AND THE FIX ALREADY EXISTS** — *"a message ending in `\p` parks the
   text printer awaiting an EDGE-TRIGGERED press with no timeout, and the wait branch pressed
   nothing"*. ⛔ Dismiss on `get_text_printer(0).state == WaitForButton`, **never** on a frame count,
   and ⛔ never by mashing A (a held button is not an edge — the same trap `story-drive` §5 names).

---

## BLOCKERS, IN ORDER (each cites its evidence)

* **A — `KI-96`.** The unbounded `while … PARTY_MENU: press A`. The recon adds *why it is unavoidable
  here*: an E4 mon dropping our active below `hp_threshold` with a healthy bench routes flee →
  `rotate_lead` (trainer battles are unfleeable), and "no damaging moves" does the same. **Bound it
  first.**
* **B — the §Ch23 re-entry trap.** `story_mode.py`'s dispatch **and** its `_guard(...)` must be relaxed
  in ONE commit. `SYS_GAME_CLEAR` cannot gate it (set only at the Hall of Fame) and `ELITE_4_STATE` is
  wiped on both endings ⇒ **the only usable first conjunct is `FLAG_ENTERED_ELITE_FOUR`**, which means
  "committed", not "progressed".
* **C — `KI-74`.** Every E4 door is a `setmetatile`, and our planner reads the ROM grid, not
  `gBackupMapLayout`. The rooms need a live grid or the planner will route into a sealed door.
* **D — healing is written but NOT WIRED.** `grep` finds **zero callers** of `heal_party_from_bag`
  inside `modules/`. Five fights, no nurse, and the policy that is supposed to carry us is unreachable.
* **E — `KI-89`** (`scroll_to_item_in_bag` can silently land on the wrong item) — the whole survival
  plan runs through it.
* **F — the fixture (`KI-94`) and the level gap** (~L60 now vs ~L75 for the full gauntlet).

---

## ⚠ UNVERIFIED — PROBE BEFORE USING (the note's own list)

1. The true landing tile on **first entry vs re-entry**.
2. Whether (6,2)/(5,12) are `MB_NORMAL`.
3. Whether the Wallace cutscene advances on button presses.
4. **Roar's forced switch** (Sidney's roster) — no handling found anywhere in our code.

**The cheapest first probe:** extend `Ch24ProbeMode` into an **observe-only** walk (no fighting) that,
per room and hall, logs map+local coords every frame for 120 frames post-warp, `VAR_ELITE_4_STATE`,
the live metatile behaviour of (6,1)/(6,2)/(5,12) **before and after** a fight, and `calculate_path` to
(6,2) both before and after the door opens. That single drive settles items 1-2 and KI-74's direction.


---

## ⭐ ADDENDUM 2026-09-13 — two NEW constraints for `#24-e4healing` step 2, one ROM-VERIFIED by me

⚠ A 9-agent workflow was commissioned for exactly this item **without first reading this file**, and
its adversarial layer caught it re-deriving this spec and the 2026-09-08 recon. ⛔ **Most of what it
produced was already here.** Recorded in `08-MISTAKES.md` 2026-09-13. Only these survived as new:

### 1. ⛔⛔ HALLS 1/2/3/5 ARE UNSAFE TO STAND IN — **VERIFIED AGAINST OUR OWN ROM, NOT A NOTE**
Read live via `get_map_data(...).warps` on the repro profile:
```
EVER_GRANDE_CITY_HALL1   warps = [(5,12), (5,2), (4,12), (6,12)]
EVER_GRANDE_CITY_HALL2   warps = [(5,12), (5,2), (4,12), (6,12)]
EVER_GRANDE_CITY_HALL3   warps = [(5,12), (5,2), (4,12), (6,12)]
EVER_GRANDE_CITY_HALL4   warps = [(5,33), (5,2)]          <-- SINGLE tiles, both ends
EVER_GRANDE_CITY_HALL5   warps = [(5,12), (5,2), (4,12), (6,12)]
```
The bot arrives at **(5,12)** and **BOTH neighbours — (4,12) and (6,12) — are also warps back to the
previous room.** ⇒ **one sidestep while healing is a backward warp**, and a heal routine that moves
at all (or that a nudge/anti-stuck shim moves) can silently undo a cleared room.
⇒ **HALL4 IS THE ONLY HALL SAFE TO STAND IN**, and that is exactly where the Wallace heal must go.
⇒ **Step 2 rule: heal INSIDE the arena rooms for bosses 1-4; use HALL4 for the Wallace heal.**
‼ Do NOT heal on a hall's south tile. This is a *stronger* constraint than "heal between rooms".

### 2. Wallace cannot be reached by talking — so "heal on room entry" MISSES him
The four E4 bosses are `TRAINER_TYPE_NONE` with sight 0, so the heal window inside each arena is
unlimited. **Champion's Room is different: Wallace's object script is literally `0x0`** and the fight
starts from an `OnFrame` script. ⇒ there is **no window at all** once you are in the room, which is
the same fact this spec already states as *"leg 10 — Wallace: do NOT press A"*, arriving from the
other direction. Combined with (1): **the last heal opportunity is HALL4, before the door.**

### 3. The measurement that makes step 2 worth building — and it was already in our docs
`04-HANDOFF.md:19-26` / `KI-93`: `--driver ch24probe` **BEAT SIDNEY** (`outcome=BattleOutcome.Won`) —
and the post-fight party was `Sceptile 0/147, Zigzagoon 0/48, Swellow 0/139, Mightyena 0/144,
Castform 0/103`, **only `Wailord L47 226/226` still standing**, after **20 faint-chooser events**.
⇒ the bot can win room 1 and then walks into room 2 with **one Pokémon**. That is precisely the gap
step 2 exists to close, and it is measured, not assumed.
‼ The workflow listed this as an "unknown". It is in the first 30 lines of the handoff.

### Corrections to this spec's own details, from the same round (low cost, worth fixing)
* Champion's Room is entered at **(6,12)**, not (6,13).
* League 1F has a **fifth warp at (1,7)** to `POKEMON_LEAGUE_2F` (Union Room / Trade Center) that the
  leg-2/3 chain omits — harmless if never taken, but the chain is not universally quantified.
* Wallace's **entire six-mon party is `.iv=255`**, not "250 except the last".
