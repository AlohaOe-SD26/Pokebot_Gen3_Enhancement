# Inbox: strategies for the learner to try

Drop a JSON file here and the next cycle runs it as one of its strategies (at most `max_proposals_per_cycle`
per cycle, oldest first):

```json
{"name": "no-open-fence", "why": "test whether OPENFENCE causes the Norman wall",
 "genes": {"POKEBOT_R20_OPENFENCE": "0", "POKEBOT_R25_CAP": "1"}}
```

A knob you leave out stays at its baseline value (step 14's arm A). The learner checks every file against
`knowledge.GENES`. A file naming an unknown knob or value is moved to `rejected/` with a `.why.txt`. A
proposal is moved to `done/` once a cycle has scored runs for it. Claude's consult step writes here too.

A proposal that has waited longer than `consult.proposal_ttl_days` in `config.json` (3 days, by its file date),
or that names the same strategy (genome) as an older waiting one, is moved to `expired/` with a `.why.txt` when the
next cycle is planned (`learner.py plan` does it too). Nothing is deleted. To run an expired one after all, COPY it
back here: a copy gets today's date, while a moved file keeps its old one and would expire again.
