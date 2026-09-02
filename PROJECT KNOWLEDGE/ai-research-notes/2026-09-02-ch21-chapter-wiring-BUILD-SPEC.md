# §Ch21 — WIRING THE CHAPTER INTO `_play()`: BUILD SPEC (recon done, build NOT started)

> ‼ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`) — with one difference from most notes in
> this directory: **the load-bearing claims below carry a ✅ because I opened the file and read the
> line myself**, not because an agent said so. Anything without a ✅ is still a NOTE.
> Produced 2026-09-02 by a 7-agent workflow (5 recon angles → 1 adversarial refuter → 1 synthesis),
> run `wf_6355d22e-da6`. ⛔ The refuter found **six WRONG claims** in the recon reports; every one is
> listed in §0 so nobody re-derives them.

---

## §0. WHAT THE REFUTER KILLED — read this before trusting any older note on the subject

| # | The claim | Reality |
|---|---|---|
| W1 | "whiteout recoveries are capped at 5" | ✅ **40** — `story_mode.py:2624` `if recoveries > 40:`. The derail cap IS 4 (`:2563`). An 8× understatement of how long a mis-owned state burns before Manual. |
| W2 | "leg 5's error text names a tile `(5,1)` that is not leg 4's end tile — the message misinforms" | ✅ **INVENTED DEFECT.** `(5,1)` is this module's VAR-PAIR notation (`sootopolis.py:2172-2173`), matching leg 5's own gate at `:2969`. No defect. |
| W3 | "L3→L4 needs a step-off the warp first" | ✅ **DO NOT ACT ON THIS.** Leg 4's first act is `navigate_to(SKY_PILLAR_ENTRANCE, SEAM_APPROACH)` with `SEAM_APPROACH = (14,3)`, MEASURED `is_warp=False` (`sootopolis.py:1874-1875`, `:2275`), and leg 3 GRADES itself on a path to that tile. ⛔ Inserting a step-off — or any D-pad-jolting helper — risks CREATING the south-warp bug the module is built to avoid (`FIXTURES.md5` post_skypillar_door row). |
| W4 | "leg 1 re-runs safely ✅" | ✅ **FALSE, AND IT IS THE #1 BUILD HAZARD.** `enter_sootopolis()` has NO resume guard: after `assert_ch21_preflight()` it runs `_navigate_riding_out(MapRSE.ROUTE126, DIVE_TILE)` unconditionally (`sootopolis.py:194`), and Sootopolis has ZERO map connections (`:40-49`). ⇒ on ANY post-whiteout resume, **leg 1 is the first thing that dies**, before reaching the leg that owns the state. |
| W5 | "segments run 1→20 with suffixes 5a/5b/5c, 19b" | The suffix set is much larger (7a/7b, 8a/8b, 9a/9b/9c, 10a-c, 11a-d, 12a-c, 13a, 19b). Cosmetic, but do not quote the short list. |
| W6 | "the escort's end state is *asserted* at `:310-316`" | That is the ride loop's `return True` condition, not an assertion. `steven_escort()` asserts nothing at its end; the postcondition is enforced indirectly by `break` / `for…else` (`:443`, `:457-462`). |

⛔ **AND A SEVENTH, WHICH WAS MINE, NOT THE AGENTS':** I had written into four documents that
"`chapters.py` does not yet consume `RECEIVED_HM_WATERFALL`". ✅ **FALSE** — `chapters.py:249-250` is
`Chapter("21", 26, …, flag("RECEIVED_HM_WATERFALL"), …)` with a ten-line rationale at `:240-248`, and
`progress.py:40` maps it. ⇒ **the wiring needs NO `chapters.py` edit.** See `08-MISTAKES.md`
2026-09-02 (later).

---

## §1. WHAT TO EDIT (✅ = insertion point read and confirmed)

| # | File | Where | Edit |
|---|---|---|---|
| E1 | `modules/story/sootopolis.py` | end of file | NEW zero-arg `do_sootopolis_chapter() -> Generator` (§2). ✅ Zero-arg matches `do_seafloor_cavern_chapter()` at `seafloor_cavern.py:931`. |
| E2 | `modules/story/sootopolis.py` | near `ch21_done()` `:104` | NEW `ch21_chapter_done()` = flag **and** `SOOTOPOLIS_WALLACE_STATE != 0` (§2 rationale). |
| E3 | `plugins/custom_modes/story_mode.py` | ✅ after `:3741` (`_guard("Seafloor Cavern / Kyogre (Ch20)", …)`) and BEFORE `:3743` | The Segment 21 block, mirroring `:3735-3741` exactly. |
| E4 | `plugins/custom_modes/story_mode.py` | ✅ `:3743` onward | The comment block opens `# END OF BUILT CONTENT. Next build: SOOTOPOLIS / RAYQUAZA — **Chapter 21**.` — false once E3 lands. Retarget to Chapter 22 (Juan). |
| E5 | `plugins/custom_modes/story_mode.py` | ✅ `:3765-3769` | `context.message` says *"End of built content. NEXT (WIP): Ch21, Sootopolis and Rayquaza."* — a BANNER, and it needs the same pair check as a doc heading. |
| E6/E7 | `tools/story-dev/story_harness.py` | `:37` choices + a new class | `--driver ch21chapter` → `Ch21ChapterMode`, modelled on `Ch20ChapterMode`, driving the PRODUCTION entry point. ✅ `"ch21chapter"` is absent from the choices list today. |
| — | `modules/story/chapters.py` | — | ✅ **NO EDIT.** |

✅ Every flag/var name the design uses resolves in `modules/data/event_{flags,vars}/emerald.txt`:
`RECEIVED_HM_WATERFALL` (312), `SOOTOPOLIS_CITY_STATE` (94), `SKY_PILLAR_STATE` (202),
`SOOTOPOLIS_WALLACE_STATE` (216) — so neither `_done` nor `_done_var` will raise on a phantom name.

**E3 shape (mirrors the ✅-read Ch20 block at `story_mode.py:3735-3741`):**
```python
        from modules.story.sootopolis import do_sootopolis_chapter, ch21_chapter_done

        if not ch21_chapter_done():
            yield from do_sootopolis_chapter()
        else:
            console.print("[dim]Story: Sootopolis / Rayquaza already done — skipping.[/]")
        _guard("Sootopolis / Rayquaza / HM07 (Ch21)", ch21_chapter_done)
```

## §2. THE ORCHESTRATOR — mirror §Ch20's PROVEN shape, which I read at `seafloor_cavern.py:954-1000`

✅ The proven shape is: `if done: return` → resume branches → preflight → `for attempt in range(1, 4)`
with **`_check_abort()` as the first statement of the loop body, OUTSIDE the try** → the resume
conditions **re-checked INSIDE the loop** → `except StoryAbort: raise` → `except BotModeError` whose
first statement is `reraise_if_aborting(error)`.

⛔⛔ **KI-67, QUOTED FROM `seafloor_cavern.py:934-939` — DO NOT "IMPROVE" THIS:** *"THE RETRY IS THE
`StoryMode.run` LOOP, NOT A LOOP IN HERE. `except StoryAbort: raise` is deliberate: the abort latch is
cleared ONLY by `StoryMode.run`, so catching a whiteout and looping would run straight into the next
`_check_abort()` and die instantly — one whiteout would burn all three attempts in a handful of
frames and report three failures, two of them invented."* The `for attempt` loop exists for
`BotModeError`, NOT for whiteouts.

**Per-leg gates — POSITION *and* STATE together, never vars alone** (the rule leg 4 and leg 5 both
carry, and the reason a vars-only selector once sent leg 4's own output fixture on a doomed walk):

| Leg | Gate | Why |
|---|---|---|
| 1 `enter_sootopolis()` | `state < 2` | ⛔ **MUST be gated — W4.** It has no guard of its own. `sootopolis_reached()` (`:99`) looks like the predicate but is ✅ **DEAD CODE — defined, never called anywhere in the tree**; verify it live before adopting it, do not adopt it because the name fits. |
| 2a `steven_escort()` | call unconditionally | ✅ self-skips on its flag at `:381-383`, checked BEFORE the `state != 2` raise. |
| 2b `cave_of_origin()` | `state == 2` **and** on `CAVE_OF_ORIGIN_ENTRANCE` | ⛔ **THE UN-OWNED STRAND:** state 2 + escort flag set + standing in Sootopolis. The escort is the only way into the cave and NO leg walks that corridor. Raise NAMED rather than sending leg 2b into its own error. |
| 3 `approach_sky_pillar(report)` | `state == 3 and pillar == 0 and not at_sky_pillar_door()` | |
| 4 `climb_sky_pillar(report)` | (3,0)+ENTRANCE, or (4,0)+OUTSIDE, or (5,1)+TOP | ⛔ (5,1) on **ENTRANCE** is leg 4's OWN OUTPUT and leg 4 RAISES on it — position is what separates it from leg 5. |
| 5 `return_and_get_waterfall(report)` | mirror leg 5's own three phases (`:2969-2976`) | so the orchestrator never calls it into its "no phase" raise. |

**Completion predicate: the flag AND `SOOTOPOLIS_WALLACE_STATE != 0`.** Leg 5 already raises on
`wallace_state == 0`, so this conjunct only bites when a run dies *between* the `giveitem` and the
facing tail — exactly the window a whiteout can land in, and exactly the state in which §Ch22's gym
door is sealed. ⇒ flag-only would grade a stranded run as complete.

## §3. ACCEPTANCE for `--driver ch21chapter`
`done ∧ hm07 ≥ 1 ∧ wallace_state != 0 ∧ at == (31,34) ∧ gym_path ∧ continue_path`, where **`gym_path`
is a real `calculate_path` to `L5_GYM_DOOR = (31,32)`** — §Ch22's entrance warp, and the one check
that fails when Wallace never stepped off the door. Compute both paths INLINE in the driver.

## §4. ⛔ WHAT IS **NOT** KNOWN — measure before or during the build

1. **No drive of legs 1→5 in sequence has ever happened.** Every fixture is a per-leg pin; the
   chapter driver is the first such run. **Total frame budget is UNMEASURED** (leg 5 alone is 20,705
   and leg 3 is 34,122, so the floor is well over 60,000).
2. **No fixture exists for a post-whiteout resume** at states 2 (flag set), 3 (not at the reload
   tile), 4, or (5, pillar 1). Whether "raise NAMED and let `StoryMode.run` retry" is acceptable for
   those is arguably a USER decision, not something to invent.
3. **UNVERIFIED:** whether `SootopolisCity_OnFrame` self-fires the Rayquaza arrival scene. It decides
   whether a whiteout during leg 5's swim can ever reach leg 5's `post-arrival` phase. ⛔ Nobody has
   opened the decomp for this; do not assume either way.
4. **UNMEASURED:** party HP/PP surviving legs 1→5 end-to-end. `post_ch20` starts with one FAINTED
   member at 80%, there is no Poké Center after leg 3's heal, and legs 4+5 are pinned at 91%.
   The chapter drive is what measures this.
5. Cosmetic, out of scope: `modules/web/static/stream-overlay/index.html:236` labels HM07 "HM08".
