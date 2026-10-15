# KB1 status (seasoned-player knowledge base, USER RULING 40)

Branch: `claude/kb1-seasoned-knowledge-cr1f5t`. Decomp: pret/pokeemerald@731ad5bfd6e6f265508d0efcca0ba42f9dcf5881
Resume: `git clone --depth 1 https://github.com/pret/pokeemerald /tmp/pokeemerald` then `python3 ai_player/gates/extract_seasoned.py --decomp /tmp/pokeemerald`.

| Step | State |
|---|---|
| 1 species.json | DONE (411 entries, 386 real + 25 OLD_UNOWN placeholders) |
| 2 learnsets.json + moves.json | DONE (354 moves, 386 species learnsets, 58 TM/HM, 30 tutor moves, 165 egg-move species) |
| 3 encounters.json | DONE (135 map entries: 124 maps + 7 pyramid + 4 pike; slot tables identical to expected Gen-3; Feebas algorithm noted, tiles not static) |
| 4 verify_seasoned.py | next |
| 5 KB1-REPORT.md | not started |
