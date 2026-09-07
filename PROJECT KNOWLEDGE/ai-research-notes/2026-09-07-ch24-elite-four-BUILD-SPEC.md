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
   E4 members have **no sight line** (approach + A), while **Wallace has no A-press trigger**.

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
