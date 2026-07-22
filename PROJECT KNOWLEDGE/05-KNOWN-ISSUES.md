# Known Issues — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. Open problems only — when an issue is
> fixed, remove it here and record the fix in 07-CHANGELOG.md.
> Entry format below; KI numbers never get reused.

<!--
## KI-1 — <short title>   (opened YYYY-MM-DD, severity: high/med/low)
- **Symptom:** what goes wrong
- **Repro:** how to trigger it
- **Suspected cause:** best current theory
- **Workaround:** if any
-->

These are UPSTREAM bugs in pokebot-gen3 (found during the 2026-07-17 doc
verification pass). They exist identically in `40cakes repo/pokebot-gen3/`
(pristine — do not fix there) and `custom-pokebot/` (fix candidates; any
fix goes in DIVERGENCE-LOG).

## KI-1 — Upstream pokebot.spec (PyInstaller) is stale/broken   (opened 2026-07-17, severity: low)
- **Symptom:** `pokebot.spec` references `import.py` (file doesn't exist in
  the repo) and a repo-root `sprites/` dir (sprites actually live at
  `modules/web/static/sprites/`); a PyInstaller build would fail as-is.
- **Repro:** `pyinstaller pokebot.spec`.
- **Suspected cause:** spec never updated after upstream restructures;
  upstream releases are source ZIPs, so the spec is unexercised.
- **Workaround:** run from source (our normal path). Relevant to punch-list
  #4 only if we ever want packaged builds.

## KI-2 — Upstream `BattleStateSide.modified_stats()` raises TypeError   (opened 2026-07-17, severity: low)
- **Symptom:** `modules/battle_state.py:590` builds its stage-multiplier
  table from set literals (`{10, 40}`), which can't be indexed — calling
  `modified_stats()` raises `TypeError`. Zero callers in the repo (dead
  code), so nothing breaks today.
- **Workaround:** use `stats_modifiers` (battle_state.py:587) and apply
  multipliers yourself. Must be fixed in custom-pokebot before any custom
  battle brain relies on it.

## KI-3 — Upstream stale docstring names nonexistent battle opt-out   (opened 2026-07-17, severity: low)
- **Symptom:** `modules/modes/_interface.py:62` docstring tells mode
  authors to call `self.disable_default_battle_handler()` — that method
  doesn't exist anywhere. The real mechanism is returning
  `BattleAction.CustomAction` from `on_battle_started()`.
- **Workaround:** documented in `40cakes repo/DOCUMENTATION/03`; keep in
  mind when writing custom modes.

## KI-4 — Cloud-sync requires backups enabled (opened 2026-07-19, severity: low)
- **Symptom:** If `backups enabled: false` but `sync.enabled: true`, every
  clean exit logs "sync FAILED (backup could not be created)" — cloud-sync
  is built on the backup system. Honest failure, NOT data corruption.
- **Workaround:** enable backups when using cloud-sync. Fix candidate: a
  config-validation warning at load.

## KI-5 — Background git calls could wait on a credential prompt (opened 2026-07-19, severity: low)
- **Symptom:** cloud-sync/update-check git fetch/push could block up to its
  timeout if a remote interactively prompts for credentials.
- **Mitigation in place:** all such calls are timeout-bounded on daemon
  threads, so startup is never blocked. Fix candidate: set
  `GIT_TERMINAL_PROMPT=0` in the subprocess env.

## KI-6 — Tab bar overcrowds with 6 tabs — RESOLVED 2026-07-19 (sandbox)
- **Symptom:** Adding the Hunt tab (#9) made 6 tabs overflow the ~360px
  tool-column width — labels overlapped/truncated.
- **Fix (done):** tab bar wraps to two balanced rows when there are >4 tabs
  (3+3 for six), legible in both desktop and the handheld drawer
  (screenshots ki6_1/ki6_2). Gamepad focus-nav + tab persist unaffected.

## KI-7 — fly_to() checks the wrong badge for Emerald (opened 2026-07-19, severity: low)
- **Symptom:** `modules/modes/util/higher_level_actions.py` fly_to() gates on
  BADGE03_GET (Dynamo) — correct for FR/LG but WRONG for Emerald, where Fly
  needs the Feather Badge (BADGE06). Inherited from upstream. Story-mode #24
  must not rely on fly_to as-is; fix when wiring Fly into story navigation.

## KI-8 — Mid-battle rotation execution can stall the party-menu switch (opened 2026-07-21, severity: med)
- **Symptom:** a mid-battle switch (`TurnAction.RotateLead`) into a weak/underlevelled bench
  hung the in-battle PARTY_MENU (Roxanne with Torchic vs Rock + an L6-7 bench → stuck, then
  Manual). `state=3` = PARTY_MENU.
- **Where:** `modules/battle_action_selection.py` `case TurnAction.RotateLead` →
  `scroll_to_party_menu_index(map_battle_party_index(index))` → `while get_game_state() ==
  PARTY_MENU: press A`. If the target is mis-mapped or the party-menu submenu default isn't
  "SHIFT", the scroll loop (`menuing.py`) or the A-press loop spins.
- **Mitigation (done):** the Story bot's trainer-battle strategy now ATTACKS through and never
  proactively rotates in a trainer/gym/E4 battle (`LevelUpTravelBattleStrategy.decide_turn`) —
  so it sidesteps this path. Faints are handled reactively by the after-faint chooser (which
  correctly excludes fainted/active/double-partner mons).
- **Still open (for Fable):** any strategy that DOES rotate (e.g. SwapTrain in an unexpected
  double/trainer case) is exposed. Reproduce a live rotation into a specific slot and pin
  `map_battle_party_index` / the party-menu submenu handling. Good first target: the Slateport
  **Gabby & Ty DOUBLE battle** (§Ch8) — it also validates the after-faint double-battle fix.

## KI-9 — Training spin could silently stall (no encounters) — MITIGATED 2026-07-21
- **Symptom:** during pre-gym / pre-rival training, the grind `spin()` could end up where it
  can't trigger wild encounters (walked out of grass, trainer line-of-sight, bad respawn spot)
  and walk in place FOREVER — the level never reaches target, the stop-condition never fires, no
  whiteout, no derail → hard stall (harness-repro'd from `route116team.ss1`: stuck at Marshtomp
  L16 with no EXP for 20k+ frames). Position/RNG-dependent (a clean fresh run trains fine).
- **Mitigation (done):** `_story_spin` now has a **no-progress watchdog** — if the party gains
  no EXP for `_STORY_SPIN_NO_PROGRESS_FRAMES` (2400) consecutive OVERWORLD frames, it bails so
  the caller (`train_team`'s loop) **re-navigates to the grass and retries**, which un-sticks it.
  Overworld-only counting means a long single battle can't false-trigger it. VALIDATED: the same
  `route116team` run that hung before now trains past L16, beats Roxanne, and reaches the rival
  prep with all fixes. Bounded by `train_team`'s outer guard (500) → derail recovery if truly stuck.

## KI-10 — Post-sail whiteout can respawn the run on the MAINLAND (Dewford arc) — MITIGATED 2026-07-22
- **Scenario:** the Emerald whiteout respawn point is the last Poké Center USED. After the first
  Briney sail (Ch6), Mr. Briney leaves his cottage (FLAG_HIDE_BRINEYS_HOUSE_MR_BRINEY) and waits
  at his BOAT: vanilla re-sails happen by talking to him on the Route 104 beach (his Route104
  object is un-hidden by the sail script) or at the Dewford dock (12,9). If the bot whites out on
  the Dewford side BEFORE ever healing at the Dewford PC, it respawns at Rustboro's PC — and
  `sail_to_dewford`'s cottage leg (Leg 3-4) would knock on an EMPTY house.
- **Mitigation (done):** `deliver_stevens_letter` heals at the Dewford PC FIRST when starting
  from town, so from the moment the Dewford arc begins, whiteouts respawn IN Dewford (the
  Segment-6 whitelist also stops any Dewford-side resume from re-running the sail). Remaining
  edge: a whiteout in the sail leg itself (route trainers) before the first Dewford heal — rare
  (the leg heals before the rival and fights little), but if hit, the run derails to Manual at
  the cottage instead of re-sailing.
- **Proper fix (when Ch8 needs re-sailing anyway):** teach the sail leg to talk to BOAT-Briney —
  if `HIDE_BRINEYS_HOUSE_MR_BRINEY` is set, engage his Route 104 beach object (live local_id via
  `_talk_to_wandering_npc`-style lookup) instead of entering the house.

## KI-11 — Oceanic Museum entrance grunt-sealed at Devon-goods time — ✅ RESOLVED 2026-07-22
**RESOLUTION:** NOT a state bug — a missing STORY STEP. The museum grunts clear when you talk
to **Dock at Stern's Shipyard** (`SlateportCity_SternsShipyard_1F_EventScript_Dock` runs
`setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA`). User-supplied + decomp-confirmed; built into
`deliver_devon_goods_to_stern` (Shipyard→Dock→museum). The doc was wrong (had the museum
freely enterable) — corrected in §Ch8b. This is the motivating case for the /validate-docs
process. Original write-up kept below for reference.

- **Symptom:** `deliver_devon_goods_to_stern` cannot reach the museum. The doors are city
  warps (30,26)/(31,26); the ONLY tiles below them, (30,27)/(31,27), are occupied by two
  Team Aqua grunts (obj id 18/5, `SlateportCity_EventScript_AquaGrunt2/1`). The whole
  y=27 row from x=22-31 is a grunt wall (gap at x=27, but (27,26) above it is collision).
  So the museum is physically SEALED — navigate_to (interior or door tile) plan-fails, and
  a walk-into-door bumps the grunt forever.
- **What's verified (probes 2026-07-22):** all 11 outside grunts share hide-flag
  `FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` (882). It is UNSET by default (confirmed on an
  INDEPENDENT fresh game at Rustboro AND on slateport.ss1), `VAR_SLATEPORT_CITY_STATE=0`,
  and the SlateportCity map.json has NO coord-trigger near the museum to reposition them
  (its only coord_event is the Battle Tent Scott scene at (10,13)). The 2F Stern-fight
  grunts are SEPARATE 2F objects (id 2-4 spawned at the stairs), not this outside crowd.
- **The contradiction:** vanilla canon = the museum IS enterable on the first (Devon-goods)
  visit, yet structurally it's sealed with flag 882 unset. Something clears/repositions the
  crowd that our static read isn't capturing (a map ON_TRANSITION/ON_FRAME script setting a
  var, an event on the Slateport dock arrival, or the flag being set earlier than found).
- **DO NOT guess a state-write** (setting flag 882 hides the crowd, but proving that matches
  vanilla's exact state at this point needs the mechanism first — house rule).
- **Fastest ground truth = the USER:** on a real first Slateport visit, are Aqua grunts
  blocking the Oceanic Museum doors, or is the entrance clear? Then either build the faithful
  trigger or document the state-write. `deliver_devon_goods_to_stern` (interior logic sound)
  stays defined but UNWIRED; frontier honestly = Slateport arrival.
