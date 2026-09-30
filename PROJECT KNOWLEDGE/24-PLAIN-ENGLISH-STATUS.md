# Plain-English Status — what the bot does, what we fixed, what is still stuck

> ⚠ **STALE AGAIN, found 2026-09-29 by a Tier 2 cold-start audit:** this file was last brought current on 2026-09-03. Nothing from USER RULINGS 18-27 or design v2 (the League basket bought early, the catch and training changes, the rare-species list, the catch cap, the ball top-off) is in it yet, and its "0 files differ" line is wrong (`promote.py --check` prints the live drift). For the current state read `04-HANDOFF.md`. A refresh is owed.

> **Current-state file: edit in place.** Written for a human reading it cold — in GAME terms, not
> code terms. No jargon, no statistics. Every technical claim here has a precise version
> elsewhere: `07-CHANGELOG.md` (what changed), `08-MISTAKES.md` (what went wrong),
> `03-PUNCH-LIST.md` (the queue), `04-HANDOFF.md` (resume point).
> **Last updated: 2026-09-03** (the two opening paragraphs and this line; the day-by-day narrative below is still HISTORY from 2026-08-10, deliberately). ‼ **This file was THREE DAYS AND FIVE CHAPTERS STALE** until a
> cold-start audit caught it. *(This line used to claim `00-README.md` "sends new readers HERE
> FIRST". It does not — the README lists this file under **"Read WHEN RELEVANT — not part of the
> start-of-session ritual"**, while calling it "START HERE FOR A HUMAN ANSWER". Overstating its own
> position to dramatise its staleness is the same species of error as the staleness.)* The "Where it gets to today" and "Where it
> stands now" sections are corrected below. **The day-by-day narrative in between is HISTORY from
> 2026-08-10 and is left as written.**

---

## What this thing is

A bot that plays **Pokémon Emerald by itself**, from a brand-new save, with nobody watching.
It picks a starter, walks the routes, catches Pokémon, trains them, and fights the gyms.

**Where it gets to today (brought current 2026-09-03):** it plays **23 of the game's 24 story
beats** by itself, in one unattended run from a brand-new save. It wins **all eight gym badges**, raids
the Magma Hideout and gets back out, recovers the stolen submarine at Slateport, clears the Aqua
Hideout maze (**taking the Master Ball on the way**), defends the Mossdeep Space Center alongside
Steven, earns **HM08 Dive**, plays the **Seafloor Cavern** end to end — boulder puzzles, underwater
currents, the Aqua ambush, Archie, waking Kyogre and escaping the atoll — then dives into
**Sootopolis**, escorts Steven to the Cave of Origin, climbs the **Sky Pillar**, wakes **Rayquaza**
to end the Kyogre-vs-Groudon fight, is given **HM07 Waterfall**, and finally beats **Juan** for the
eighth and last badge — which is what makes Waterfall usable out in the world.

⛔ *(Two paragraphs here said the cavern was "a test harness, not part of the real playthrough" and
that the work was PARKED. Both stopped being true on 2026-08-24, when the cavern was wired into the
real run; Sootopolis followed on 2026-09-02. This file went three weeks without catching up — see
"What we got wrong" below, which is exactly the shape of mistake it describes.)*

✅✅ **AND AS OF 2026-09-03 IT WINS THE EIGHTH AND LAST GYM BADGE TOO** — 23 of the 24 story
beats. The ice-puzzle gym below is now part of the real playthrough, not a test: the bot walks the
64-tile ice route, beats Juan, falls through the floor on purpose and walks back out.
⚠ **And it does that even when it LOSES the gym fight.** Juan is genuinely hard for this party —
across six attempts it won five and lost one — so when it loses, the bot wakes up in the Poké
Centre, walks back to the gym, re-solves the whole ice puzzle and fights him again. That happened
on the very run that proved the chapter works.

**What it was doing before that:** the **eighth and last gym — Juan, in Sootopolis.** This one is an
ice puzzle: the floor is thin ice that cracks as you walk, you must cross **every** tile exactly
once to open the stairs, and once you reach the leader the only way back out is to **deliberately
fall through the floor** into the basement. The bot can now do all of it — the 64-step ice route,
the fight, the fall, and the walk out — and **it beats Juan most of the time**.
⛔ *(This read "four wins out of four, including three runs deliberately given different luck"
for a few hours, until the very run that proved the chapter works LOST the fight. Six attempts
are now measured: five wins and one loss. It is the spelled-out numbers that survive a search
for "4/4" — which is how this one lasted as long as it did.)*

‼ **An honest caveat, because it matters:** one thing can still stop it, and it is not the gym.
A long-standing bug in the shared *battle* code (KI-47) can freeze the bot mid-fight; a safety net
catches it and stops cleanly rather than hanging, but the run ends there. It happened once in three
attempts at this gym. The good news is that this is the first time we have been able to reproduce
that bug **on demand** — before, it only ever turned up by chance in long overnight runs.

## ⛔ BUT THAT IS NOT WHAT WE ARE WORKING ON (changed 2026-08-14 — read this before the day-by-day below)

**The cavern work is PARKED — finished and set aside, not cancelled.** On 2026-08-14 you watched a
real run do something worse than crash, and we changed priorities to it. What happened, in game
terms:

The bot was losing to **Winona**, the Fortree gym leader. It correctly worked out *why* — nothing on
its team hurt her Altaria — and went off and **caught a Slugma** to fix it. Good so far. Then it
went to the Pokémon Center to heal, **the Slugma got left in the PC box**, the run dropped to manual
control, and when it picked up again **it walked back into the gym without the counter it had just
gone and caught.** All that work, thrown away silently. Nothing errored. Nothing said a word.

**So the live job is: make the bot use the Pokémon PC robustly.** Where that stands:

* ✅ **The Slugma bug is found, fixed, and reproducible on demand** — we can make the bot fail that
  exact way and then show the fix stops it. Fixed in both copies of the code.
  ⚠ **Honest limit:** the test hands the bot the Slugma rather than making it go and catch one, so
  the *catching* half of your original run is still not covered end to end. The part that went
  wrong — losing the Pokémon at the Center — is.
* ✅ **The bot no longer LIES about the PC.** It used to announce "Slugma is in the party" after
  merely counting how many Pokémon it had. Now it checks *that specific Pokémon by identity*, and
  says so loudly when the withdrawal did not happen.
  ⚠ **But it still only SAYS it.** Nothing yet reacts to that message — the bot reports the failure
  and then carries on regardless. Making it act on its own warning is still open work.
* ✅ **A second, unrelated trap was found and reproduced (2026-08-15).** If you ever give a gym
  leader a designated **training patch of grass**, the bot **silently loses its ability to work out
  that a fight is hopeless and go catch a counter** — the exact machinery above. It keeps printing a
  cheerful "training harder before re-attempting" and grinding levels that cannot help. We proved
  this by running the real code three ways and watching which path it took.
  ⛔ *That warning has been LIFTED (2026-08-16).* Giving a boss a training area is safe now.
  ⚠ One knock-on worth knowing: at a few of the early gyms the bot will now stop and say a fight is
  hopeless rather than grinding away at it — that is deliberate, and it stops honestly.
* ✅ **Done.** A boss can now be given a training area *and* still go and catch a counter — the two
  ideas are untangled, in both copies of the program. The obvious one-line version of that fix was
  caught red-handed breaking the opposite case before it ever shipped.

---

## The last three days, in order

### Day 1 — teaching it to fetch the right Pokémon

When the bot loses to a gym leader over and over, it is smart enough to work out *why*:
*"I keep losing to Norman because nothing on my team beats Normal-types — I need a Fighting-type."*
It then goes off to catch one.

Two things were wrong with that:

* **It picked Pokémon it could not actually reach.** It would set off toward a patch of grass on
  the far side of the map, or one locked behind a move it had not learned yet, and waste the trip.
  We changed the rule to: *only hunt somewhere the bot has genuinely walked to and back from.*
  Successful catches went from roughly **1 in 7 attempts to about half**.
* **It was lying to itself about catches.** It counted Pokémon that were *already in its party* as
  new catches. Of 13 reported catches in one overnight test, only **3 were real**.

### Day 2 — confirming the fix, and one gym leader that cannot be helped

We ran 8 copies of the bot overnight and confirmed the fix stuck. For Machop in particular it went
from **0 catches out of 7 tries to 6 out of 7**.

We also settled a question that had been nagging for a while: **Wattson**, the Electric gym leader.
The bot kept announcing *"I need a Ground-type"* and then failing to get one.

It turns out **every Ground-type it could theoretically get is behind Wattson himself** — you need
his badge to use Rock Smash to reach them. The single exception is on Route 116, and we proved the
bot cannot walk to that grass from where it is standing when it needs to.

So the honest answer is: **Wattson has to be beaten with levels and good matchups, not with a
counter.** The bot giving up on the hunt there is *correct behaviour*, not a bug. Nobody should
"fix" it later.

### Day 3 — using items (your request)

You asked for the bot to use items intelligently. Watching thousands of battles told us exactly
why that mattered:

> **Norman heals his Slaking 27 separate times**, usually about **81 HP** at a go — while the bot
> was chipping away 6–8 damage a turn and never once opening its own bag.

It was fighting a boss who drinks potions, with one hand tied behind its back.

The bot now uses healing items in trainer battles, and it is deliberately picky:

* **only when badly hurt** — not for a scratch;
* **the smallest potion that does the job** — it will not burn a Full Restore on minor damage;
* **it will not heal if it is going to die anyway** — if the opponent hits harder than the potion
  heals, healing just wastes a turn, so it attacks instead;
* **capped per battle** — because the boss heals too, and two healers with no limit is a fight
  that never ends.

While building it we found a real bug underneath: **using an item was aiming at the wrong Pokémon
in the menu**, so potions often did nothing at all. Before the fix, 1 potion in 5 actually worked.
After it, all of them did.

---

## What has been stuck a long time

### 1. The "teaching Surf" freeze — nine attempts
When the bot catches a Pokémon specifically to learn **Surf**, the teaching menu sometimes freezes
and Surf is never learned. This has been chased across **nine different test setups** over several
days.

Today it finally **fails on demand — at the exact same moment, every single time.** That is the
hard part of any bug. Three separate theories about the cause have now been positively ruled out.

**Still unfixed, but no longer mysterious.** And it is not urgent: 38 teaches worked, 4 froze, and
**not one of them ended a run.** It wastes time, it does not break anything.

### 2. The Magma Hideout — written off for three weeks, for the wrong reason
This is the next chunk of story the bot cannot play. It was set aside ages ago as *"the door is
unreachable — Jagged Pass only lets you jump **down** ledges, never climb back up."*

That was wrong. **A Team Magma grunt is standing on the doorstep.** He is removed once you have
done Mt. Pyre. At the right point in the story the door is **two steps away** from a spot the bot
already walks past.

Three weeks of "impossible" was one NPC standing in a doorway.

### 3. The number that has not moved — how often it finishes
Despite everything above, the share of runs that make it all the way through **has not measurably
improved in a week**: 25%, then 33%, then 16%, then 29%.

Those swings are noise, not progress or regress. We worked out why we could not tell the
difference: each overnight test only produces about **30 attempts**, and you would need roughly
**300 of them — about 30 hours of running — to prove a change of that size.**

So we have **stopped using it as the scorecard.** The next chapter gets judged the simple way:
*did the bot get through the Magma Hideout, yes or no?* One run answers it.

---

## What we got wrong, and why that is worth knowing

Being honest about this is the point of the file. Several confident conclusions this week were
wrong and had to be withdrawn:

* We tested whether a caught counter could beat Norman using an **injected Pokémon that could not
  attack at all** — six experiments measuring nothing.
* We reported that the bot walks into boss fights with its best Pokémon already fainted. Measured
  properly, that happens **6% of the time, not the 99% a faulty reading suggested.**
* We said bosses heal in **62%** of long fights. Once we separated real potion use from tiny
  unexplained blips, it is **17%**.
* We concluded the Magma Hideout was genuinely blocked and needed special hand-written movement —
  an hour before finding the grunt.

The common thread every time: **measuring the wrong thing, or measuring from the wrong point in
the game.** Not carelessness so much as trusting an instrument without checking it could see what
it was pointed at.

That is why the project now insists on *positive controls* — before believing a "nothing found"
result, prove the tool can find something you already know is there.

---

## Where it stands now

*(‼ corrected 2026-08-13 — every bullet here was about the Magma Hideout, which shipped on
2026-08-10, the day this section was written.)*

* Everything is saved and backed up, and ✅ **the working copy MATCHES the shipped copy — 0 files
  differ** (measured 2026-08-16). The fix for the training-area trap described above was approved by
  the owner and copied across, and it was checked by running the SAME command on both copies and
  watching the answer flip — not by comparing files, which would only prove the copy happened. *(This line said "three files" for days; the count was
  spelled as a WORD, which is invisible to the automatic check that polices that number.)*
* **Every room is mapped and has been played through**, including the one mistake that cannot be
  undone: there is a spot where pushing a boulder the wrong way **permanently blocks the only
  exit**. The plan avoids it, and we deliberately jammed a room to prove the escape — walk out and
  back in, and every boulder resets.
* ⛔ **SUPERSEDED — this bullet said the Aqua-leader fight and the escape "have not been driven
  yet". They were driven on 2026-08-14** (and the top of this file has said so since). Both now
  work: the bot beats the leader, wakes the legendary, and takes the escape route. ⚠ **One honest
  caveat that is NOT superseded:** the leader fight was won **2 times out of 3** — it is the one
  genuinely unreliable step, because the team arrives worn down and there is nowhere to heal
  inside. The sandbar hazard is real and handled: swimming the obvious direction leads to a
  **dead-end pool**, so the bot steps south first.

---

## What changed since (brought current 2026-08-22)

*A week of work in plain English. ⛔ Deliberately number-free — that is why this file has never gone
stale the way the others do.*

* ✅ **The bot no longer plays on after it blacks out.** If the whole team fainted mid-errand — during
  a heal, on its way out of a gym door, in the middle of a PC trip — it used to keep pressing buttons
  on a fainted team and then blame something that never happened, like *"won the badge but could not
  get out of the gym"*, while the player was standing in a Pokémon Center. It now stops and gives the
  true reason.
* ✅ **A second sweep found that same trap in more places** — counter training (the most blackout-prone
  thing it does), the Mt. Chimney meteorite, the Rusturf tunnel wall, the Strength lesson, and the
  heal stops along the way. In several of them the healing code's own new guard was being undone a
  moment after it fired.
* ✅ **A Pokémon can no longer be talked out of a move it could have learned.** On levelling up the bot
  could announce that nothing could be given up and decline the new move, while several ordinary
  moves sat there perfectly forgettable — and in the same moment the rule that stops it erasing an HM
  was quietly failing open. Both hold now, and when it does decline it says honestly why.
* ✅ **When one of its Pokémon faints in a fight alongside a partner, it picks the replacement properly
  again.** It had been reading the bench against the wrong ordering, so it believed a healthy Pokémon
  was already out on the field, left it sitting there, and spent an age scrolling the party menu
  before sending anyone at all.
* ‼ **And the thing we had blamed it for never happened.** We were sure it tried to send out the
  *partner's* Pokémon; watching a real fight showed it never once asked for one. Our own headline was
  wrong, and the real fault was the ordering above.
* ‼ **Update to the PC warning:** the failure notice now travels back to the part of the bot that could
  act on it, and it tells *"the withdrawal was tried and did not work"* apart from *"there was nothing
  to fetch"* — telling those two apart is the whole difficulty. ⚠ Still nothing acts on it. You have
  already said what it should do — read what the PC puts on screen, work out why, then try again
  knowingly — but that needs a piece of the game's memory we have not located yet, and guessing there
  would make it retry blindly.
* ⚠ **New to the stuck pile: the bot's map does not know what the water currents do to it.** Ride one
  to the end and the game can set it down on foot, off its surfing — or sweep it through a doorway
  into a different room entirely — while its route plan still believes it is floating where the
  current stopped. In the cavern we have now watched that happen instead of only arguing about it;
  out on the open-water routes it is measured but not yet seen. Nothing is fixed.
* 🔧 **Behind the scenes**, a long check of our own safety nets found several that could not actually
  fail — they printed warnings and reported success anyway. Those are fixed, and the checks that
  guard the guards are now part of the standing set. None of it changes how the bot plays.
* ✅ **Nothing is waiting on you.** The game file is kept inside the project's history on purpose —
  that is what makes every saved restore point instantly playable on any machine — and you had
  already decided that once before. You confirmed it again; nothing was changed. The one thing that
  would make us revisit it is the project ever being made public.
