---
name: unlazy
description: Run before declaring ANY work item done, and whenever tempted to stop at the first green result. Forces the steps this project has historically skipped — the second half of the Definition of Done, the vacuity gate, fault-testing, and verifying claims about code you did not open. Use when finishing a feature/fix, before a commit, or when a check passes and you are about to move on.
---

# unlazy — the steps this project actually skips

⛔ **This exists because every rule below was violated by someone who had already written it down,
often the same day.** Read the checklist and answer each line OUT LOUD with evidence, not intent.
"I would have" is not an answer. A line you cannot evidence is a line that is NOT done.

## 1. THE CLAIM CHECK — before you write a sentence about code

- [ ] Does any sentence I am writing assert something about a file I have **not opened this
      session**? Especially a NEGATIVE ("X does not handle Y", "nothing consumes Z", "there is no
      caller"). ⇒ **open it, or grep it, and cite FILE:LINE.**
      *Cost of skipping: a false "chapters.py does not consume this flag" shipped to FOUR documents
      in one commit. No pair check could catch it — they compare documents to each other, and all
      four agreed.*
- [ ] Am I about to repeat a number (a count, a budget, a line total, a frame estimate)? ⇒ **measure
      it now**; a repeated number is a decaying number. Prefer naming the command that prints it.

## 2. THE MEASUREMENT CHECK — before you believe a result

- [ ] Did the thing actually RUN, or did a guard skip it? Print the value the code ACTS on, not the
      candidate list, the eligible set, or the flag. ⛔ **A CANDIDATE IS NOT AN ATTEMPT.**
- [ ] Could this result be VACUOUS? Point the test at its own OUTPUT fixture / already-satisfied
      state. **If it still passes, it is measuring nothing.** Add a premise conjunct to the grade —
      not a warning, a conjunct.
- [ ] Two runs producing identical output is a DETERMINISM check, **never** a replication. Say
      "one trajectory, replayed".
- [ ] Is this an A/B? Then the arms must actually DIFFER on the discriminator. Compute it and show
      the difference before trusting the verdict.

## 3. THE GATE CHECK — for anything you added that is supposed to catch something

- [ ] **FAULT-TEST IT.** Prove it FAILS when the thing it guards is broken, and prove it does NOT
      fire on mere mentions in comments or docs. An untested gate is decoration; a false-positive
      gate teaches people to bypass it, which is worse than no gate.
- [ ] Does the grade include **"and the work can CONTINUE"** — a real reachability/usability check
      off the END state? ⛔ And is it aimed at **what the NEXT item actually needs**, not merely
      "somewhere"? *Three chapters PASSED their own tests while stranded; a fourth passed while
      sealing the next chapter's entrance, because the check pointed somewhere reachable either way.*

## 4. THE ERROR-PATH CHECK — the half nobody drives

- [ ] Did I copy a class/function from another one? ⇒ **diff the ERROR PATHS, not just the happy
      path.** Copying a comment does not copy the `try/except` that makes it true.
- [ ] Every loop bounded? Every loop head starts with the abort check, OUTSIDE any `try`?
- [ ] Does any new `except` swallow an abort? First statement of the handler re-raises if aborting.
- [ ] If it raises, does a VERDICT still print? Run the failure path once and confirm.

## 5. THE DOC CHECK — Definition of Done steps 2–4, which are where items die

- [ ] Current-state docs updated (01/02/03/04/05 as applicable).
- [ ] `07-CHANGELOG` appended. `06-DECISIONS-LOG` appended if a real choice was made.
      `08-MISTAKES` appended if a bug was fixed or an approach abandoned — with a
      one-line prevention rule.
- [ ] **Run the `staleness-sweep` skill.** A status change falsifies sentences you did not write and
      cannot recall. *One status change once left EIGHT stale claims across THREE files.*
- [ ] Tier 0 green (`lint_docs.py`, `audit_doc_consistency.py`, `audit_handoff_invariants.py`).
- [ ] Tier 1: ONE fresh independent reviewer (not a fork) with the diff + a claim paragraph +
      pairs P1–P5. Fix findings, re-run Tier 0, **then** commit.

## 6. THE COMMIT CHECK

- [ ] Staged EXPLICIT paths — never `git add -A` / `git add .`.
- [ ] Every added file NAMED in the message. If you cannot say what a staged file is, it does not
      belong in the commit.
- [ ] Is the EVIDENCE you cite actually committed? ⇒ **grep the committed evidence file for the
      line your claim rests on.** *A fault arm's proof once existed only in uncommitted scratch
      output, so the repo did not contain the thing the commit message asserted.*
- [ ] Pushed, and `git status -sb` confirms no divergence.

## 7. THE STOPPING CHECK

- [ ] Am I stopping because it is DONE, or because the first thing went green? Name the remaining
      work explicitly, or say plainly that there is none.
- [ ] Anything I decided that was the USER's to decide? (promotion, scope, a policy branch) ⇒ hand
      it back, and ⛔ **first `grep -i 06-DECISIONS-LOG.md`** — a question may already be ruled.
