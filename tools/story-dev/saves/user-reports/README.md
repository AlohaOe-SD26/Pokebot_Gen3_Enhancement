# user-reports — bug-capture save states from real-hardware runs

When a real (GUI) run hits a wedge/bug: create a save state at the moment of the
problem (Emulator → New Save State), copy the `.ss1` from `<profile>/states/` into
this folder with a descriptive name (e.g. `rocksmash_hang_r111.ss1`), and push (or
send it with the log). The agent then reproduces the EXACT state in the harness —
byte-for-byte — instead of reconstructing it from logs.

These are debug artifacts, not milestones: the "Load Milestone State" picker does
not list this folder.
