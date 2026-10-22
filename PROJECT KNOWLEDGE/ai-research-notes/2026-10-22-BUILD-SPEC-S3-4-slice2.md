# BUILD SPEC S3-4 slice 2: `items_gifts.json` (stage 2a) and `events.json` (stage 2b), 2026-10-22

> The coordinator's spec. It replaces the NEEDS DESIGN block of `2026-10-19-BUILD-SPECS-step-3.md` (grep "NEEDS DESIGN
> (critic), slice 2"). Inputs, all filed beside this file:
> - the census `2026-10-22-KB2-slice2-scripts-census.md` (three tables, 0 UNPARSED);
> - two recon NOTES, `2026-10-22-KB2-slice2-recon-data.md` and `-adversarial.md`;
> - W7's missing-fact lists `2026-10-22-W7-chapter-packs/w7-ch1..4.md`.
>
> The recon counts are NOTES. The builder RE-MEASURES every count it relies on, and the verifier re-derives it
> independently.

## WHY

A seasoned player (USER RULING 40) knows the following:
- where the TMs and HMs are, and who gives them;
- what each mart sells and when its stock grows;
- which gifts are once, daily or a choice;
- what a story step changes (a gate opens, a person appears).

W7 found 20 load-bearing facts the chapter packs lack: 13 are scripted events and 3 are gifts or items. Slice 1 gave
trainers, bosses, maps and the campaign.

The recon showed why a naive "parse `finditem`/`giveitem`/`pokemart`/`setflag` per map" would be FALSE:
- item balls live in a shared file and are placed by `map.json`;
- 3 of the 165 `finditem` labels are dead, and leftover RS code is marked only by comments;
- 60 ball-looking objects are not items;
- most flags are set with no `setflag` line;
- 15 gifts are runtime values, and many are daily, random, a choice, or decided by the starter, the gender or a hidden
  stat;
- inline scripts sit in `data/event_scripts.s`.

## RULES THAT SHAPE BOTH FILES (each from a measured fact)

- **R-1 ONE SOURCE PER FACT.** Field items and hidden items are ALREADY in slice 1's `maps.json` (`item_balls`,
  `hidden_items`: 162 and 112). Slice 2 does not re-derive them. Each per-map items record carries
  `field_items: "maps.json"` as a pointer.
  - The TM/HM index below DOES list the 14 TM item balls and the 1 hidden TM. Each such entry references its
    `maps.json` record (map + index) and copies no coordinates.
- **R-2 ATTRIBUTE BY REFERENCE, NOT BY FILE.** A script label belongs to the map(s) whose `map.json` (object, coord or
  bg `script`, honouring `shared_scripts_map`, as slice 1's `script_owner` does) or whose own script references it,
  through `call`/`goto`/conditional/`call_if_*` chains. The closure is bounded like slice 1's `MAX_LABELS`.
  - Parse all THREE homes: `data/maps/*/scripts.inc`, `data/scripts/*.inc`, `data/event_scripts.s`.
  - A label reached by nothing is DEAD. It never appears in an AI-facing record. It is listed in the file's `dead`
    section with its file:line, so the verifier can check the split.
  - A label reached only from C is listed with `reached_from: "C"` and the C file:line when known; otherwise it goes
    in `dead`, marked `"unverified: may be reached from C"`.
- **R-3 VANILLA ONLY.** Keep the `#ifndef BUGFIX/UBFIX` / `#else` side (11 blocks). Where vanilla's `copyvar X, 1`
  reads through a NULL pointer, the value is recorded as `"unknown (vanilla copyvar bug, scrcmd.c:371)"`, never `1`.
  Mystery-gift and record-mixing scripts (`data/mystery_gift.s` includes; the Eon Ticket) are excluded and counted in
  `excluded`.
- **R-4 CONDITIONS IN WORDS; FLAG AND VAR NAMES ARE DEVELOPER-ONLY (RULING 40).**
  - Every record that depends on state carries `when` in words, e.g. "after badge 3 and meeting the shop owner",
    "once a day", "one of {A, B}; taking one removes the other", "by the lead's friendship", "the doll of your
    starter".
  - The flag and var names behind it go ONLY under a key named `dev`, a dict, e.g.
    `dev: {flags: [...], vars: [...], ref: "file:line"}`.
  - **Never a key named `flag`, `flags`, `var` or `vars` at any other path.** `check_fairness.developer_keys()`
    removes a key from the refused set once any file classifies it `ai`. That would silently stop B2 refusing
    `x["flag"]` everywhere, including `milestones.json`.
  - The gate T-FAIR (below) pins this.
- **R-5 NAMES CHECKED AGAINST THE DECOMP, NOT `emerald.txt`.** Every flag or var name in `dev` must be `#define`d in
  `include/constants/flags.h` / `vars.h` at the pin, aliases resolved (`FLAG_TEMP_SKIP_GABBY_INTERVIEW` ->
  `FLAG_TEMP_1`, the special flags).
  - Do NOT filter by `sandbox-pokebot/modules/data/event_flags/emerald.txt`: it lacks 9 real names, and it misspells
    `FLAG_HIDE_FALLARBOR_POKEMON_CENTER_LANETTE` as FALLORBOR. That table is BOT data; REPORT the misspelling, do not
    edit it.
- **R-6 NO ROUTE KEYS** (slice 1's W6): no `x`, `y`, `route`, `path`, `steps` or `coords` key outside a pointer into
  `maps.json`. A record says WHO and WHERE (map, giver's local id / name), never how to walk there.
- **R-7 WITHHELD as in slice 1** (USER RULINGS 44, 45): no IVs, no AI flags, no species shares.

## STAGE 2a: `ai_player/knowledge/world/items_gifts.json`

Top level: `_generated`, `_source` (the pin), `gifts`, `marts`, `tm_hm`, `purchases`, `dead`, `excluded`.

- **`gifts[]`**: one record per REACHABLE `giveitem` / `givemon` / `giveegg` / `givedecoration` line. Fields:
  - `id` (`<label>:<n>`), `maps` (by R-2), `giver` (the object's local id and graphics name, or `coord`, or
    `map_script`), `kind` (`item`, `tm`, `hm`, `key_item`, `decoration`, `mon`, `egg`);
  - `what`: the item or species constant, OR `one_of: [...]` with `chosen_by` (`random`, `draw`, `friendship`,
    `trainer_id`, `starter`, `gender`, `choice`, `nature`) when the line takes a VAR;
  - `repeat` (`once`, `until_received` when a bag-full branch precedes the flag, `daily`, `weekly`, `repeatable`);
  - `exclusive_with` (gift ids), `when` (words), `dev`, `ref`.
  - The 15 `giveitem VAR_*` lines each resolve to a `one_of` set cited to its source (the `random` range plus the base
    index, the C table such as `src/lottery_corner.c:14-19`, or the `switch` cases). If a set cannot be resolved,
    `what: "unknown"` with the reason; never `VAR_RESULT`.
- **`marts[]`**: per `pokemart` / `pokemartdecoration*` line: `map`, `clerk`, and `lists: [{items, when, dev}]`. A mart
  whose script picks between list labels has one entry per list (Oldale, Petalburg, Rustboro and Trainer Hill: 5
  pairs, re-measure). The Petalburg condition is set in `data/event_scripts.s:678` and reached from four gyms (R-2).
- **`tm_hm[]`**: every TM and HM in vanilla solo play with every source: `gift` (gift id), `field_item` /
  `hidden_item` (the `maps.json` pointer), `mart` (mart + list), `purchase` (the Game Corner `additem`). This is the
  index a seasoned player keeps in their head. The recon counts are NOTES: 8 HMs, 34 distinct TMs from 42 `giveitem`
  lines, 14 TM item balls, 1 hidden TM, 10 mart TMs, 5 Game Corner TMs.
- **`purchases[]`**: the 13 `additem` lines (coins, vending) as purchases, not gifts.

## STAGE 2b: `ai_player/knowledge/world/events.json`

Per map, the story-state changes a seasoned player knows. The records are WORDS for the AI and `dev` for the rest.
- **`labels[]`**, each a reachable label that changes persistent state:
  - `label`, `maps` (R-2) and `trigger`: talk to <giver>; step on a coord trigger (with its `dev` var condition); a map
    script (`on_transition`, `on_frame`, `on_load`, `on_warp_into`); a battle's post-defeat script; called by
    <labels>.
  - `changes`, in order, each `{op, dev}`. `op` is one of `setflag`, `clearflag`, `setvar`, `addvar`, `subvar`,
    `settrainerflag`, `cleartrainerflag`, `warp` (scripted move: map + warp id), `special` (its name), or
    `trainerbattle` (the trainer id, joined to `trainers.json`).
  - `effect`: words, when the coordinator's word table covers the op. See below.
  - **Persistent only:** `FLAG_TEMP_*`, `VAR_TEMP_*`, the special 0x80xx vars and `VAR_RESULT` are dropped and counted
    in `excluded`.
- **`gates[]`**: the conditions that block or open a way, e.g. "Oldale's west exit stays closed until the Pokedex",
  "Petalburg Gym's doors open at 4 badges".
  - Each is derived from a `goto_if_*`, `call_if_*` or coord-trigger var test whose branch blocks the player
    (`applymovement` back, a locked door).
  - Each carries the `when` text and the `dev` test.
  - The builder lists every `gates[]` candidate it emits. The word text for one comes from a small HAND table keyed by
    label, cited, like slice 1's `campaign_skeleton.json`; a candidate without a hand entry is emitted with
    `when: null` and listed. **Words are not generated from flag names.**
- W7's 13 events.json facts (`-recon-data.md` Q7, rows 1, 4-12, 14, 15) are the acceptance list: each must be findable
  in `events.json` by map and label.

## THE INDEPENDENT VERIFIER: `ai_player/gates/verify_world.py`, extended

It shares NO function with the extractor. It re-derives from the raw decomp files by a DIFFERENT path:
- field items from `map.json` objects whose label's first command is `finditem`;
- gifts by scanning every gift command and resolving its owner by its own reference walk;
- marts by `pokemart` operand to `.2byte` lists.

Its FAULT arms (`--plant <name>`, each must report the planted fault; CONTROL: the real output reports 0):
- (e) one gift moved to another map;
- (f) one `setflag` dropped from an events label;
- (g) a DEAD label promoted into `gifts` (the Aqua Hideout Master Ball): a verifier that recounts `finditem` lines
  AGREES with the bad output, so this arm proves this verifier does not;
- (h) a condition stripped: the Lilycove berry loses `daily`, or Root/Claw loses `exclusive_with`;
- (i) a mart list item dropped;
- (j) an Electrode (ITEM_BALL graphics) reported as a gift or item;
- (k) a flag name moved out of `dev` to a bare `flag` key (R-4).

## GATES AND TESTS

- `ai_player/gates/test_kb2.py` grows W-arms for slice 2, each FAULT + CONTROL. It runs in `run_units`.
  - The R-4 key rule, scanned over the whole output.
  - R-5: every `dev` name defined in flags.h/vars.h at the pin.
  - R-6 and R-7.
  - The `dead` / `excluded` lists are non-empty and named.
  - The W7 acceptance list.
- **T-FAIR:** `check_fairness.developer_keys()` still contains `flag` after the new files exist. It is a test in
  `test_kb2.py`: if a `KNOWLEDGE_FIELDS` entry ever classifies a flag path `ai`, it goes red.
  - `dev` is not in that set until the loader's `KNOWLEDGE_FIELDS` step classifies `world/`.
  - Until then the R-4 output scan is what keeps every flag name under `dev`.
  - The loader item must add `dev` as `developer` and extend T-FAIR to assert it.
- `extract_world.py --check` (or the slice's own `--check`): regenerating at the pin is byte-identical. That is a
  determinism check, not a replication.
- Every guard gets a call-deleting mutant in scratch, and every mutant is caught or explained.
- `run_regression.py --quick` passes, and so does `cd tools/story-dev && PYTHONUTF8=1 py -3.12 run_gates.py --quick`
  (08 2026-10-22: a suite nobody runs is not a gate).

## STAGING

- Stage 2a (items_gifts) is built and verified first.
- Stage 2b (events) follows as its own build + verify round, so a 2a problem cannot hide inside a 2b diff.
- Neither file is read by AI play code until the loader and the `KNOWLEDGE_FIELDS` step exist (unchanged from slice 1).
- The chapter-pack tool may READ both after 2b, as a follow-up item.

## STOP CONDITIONS (report instead of improvising)

- A count the recon gives does not reproduce. Report both, and the reason.
- A condition cannot be put in words without a hand table entry: emit `when: null` and list it; do not invent words.
- R-4 cannot be met by some record shape.
- Anything in the decomp contradicts a USER RULING's boundary.
