# Plain-English Status — what the bot does, what we fixed, what is still stuck

> **Current-state file: edit in place.** Written for a human reading it cold — in GAME terms, not
> code terms. No jargon, no statistics. Every technical claim here has a precise version
> elsewhere: `07-CHANGELOG.md` (what changed), `08-MISTAKES.md` (what went wrong),
> `03-PUNCH-LIST.md` (the queue), `04-HANDOFF.md` (resume point).
> **Last updated: 2026-08-13.** ‼ **This file was THREE DAYS AND FIVE CHAPTERS STALE** until a
> cold-start audit caught it — and `00-README.md` sends new readers HERE FIRST, so it was the very
> first thing a fresh session read and the most wrong. The "Where it gets to today" and "Where it
> stands now" sections are corrected below. **The day-by-day narrative in between is HISTORY from
> 2026-08-10 and is left as written.**

---

## What this thing is

A bot that plays **Pokémon Emerald by itself**, from a brand-new save, with nobody watching.
It picks a starter, walks the routes, catches Pokémon, trains them, and fights the gyms.

**Where it gets to today (2026-08-13):** it plays **20 of the game's 24 story beats** by itself.
It wins **seven gym badges**, raids the Magma Hideout and gets back out, recovers the stolen
submarine at Slateport, clears the Aqua Hideout maze (**taking the Master Ball on the way**),
defends the Mossdeep Space Center alongside Steven, and is handed **HM08 Dive**.

**What it is doing right now:** learning the **Seafloor Cavern** — the dungeon where Team Aqua
wakes Kyogre. ‼ **UPDATED 2026-08-15:** it now plays the cavern **END TO END** — dives to the entrance, solves
every boulder room, rides the underwater currents, fights the Aqua ambush, beats Archie, wakes
Kyogre and escapes the atoll. *(This paragraph said it 'stops at the second-to-last room' for a
day after that stopped being true.)*

‼ **An honest caveat, because it matters:** that cavern run is a **test harness**, not part of the
real playthrough yet. It is driven room by room from a saved game, and the Dive move is handed to
it rather than earned. Wiring it into the actual story run is still to do.

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

* Everything is saved and backed up. ⚠ **The working copy does NOT match the shipped copy** —
  **three files differ on purpose**, holding fixes that have been proven but not yet approved for
  the shipped build. That approval is a decision for the project's owner, not something the bot
  should do on its own.
* **The next room is mapped in detail**, including the one mistake that cannot be undone: there is
  a spot where pushing a boulder the wrong way **permanently blocks the only exit**. The plan
  avoids it, and if it ever happened the fix is to walk out of the room and back in, which resets
  every boulder.
* **What is genuinely still unknown:** how the bot handles the fight with the Aqua leader at the
  end, and the escape afterwards — the game drops the player on a **sandbar surrounded by
  water**, and swimming the obvious direction leads into a **dead-end pool with no way out**. That
  has been measured and the safe direction is known; it has not been driven yet.
