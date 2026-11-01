# CH5-RECON report (static, from decomp source; no emulator)
Decomp: pret/pokeemerald@731ad5bfd6e6f265508d0efcca0ba42f9dcf5881. Data: `ai_player/knowledge/seasoned/ch5_maps.json` (extractor: stdlib Python over data/maps/*/map.json + scripts.inc + src/data/trainers.h + trainer_parties.h).

## Story order after BADGE 1 (verified in scripts)
1. **Rustboro, Devon Corp 3F** (`RustboroCity_DevonCorp_3F`): Mr. Stone gives ITEM_LETTER (for Steven), sets FLAG_RECEIVED_POKENAV / FLAG_SYS_POKENAV_GET, clears Briney-house hide flags, `VAR_BRINEY_LOCATION=1`, `VAR_DEVON_CORP_3F_STATE=1`, `VAR_RUSTBORO_CITY_STATE=6`.
2. **Goods stolen** (`RustboroCity/scripts.inc` ~l.287): sets **FLAG_DEVON_GOODS_STOLEN**, `VAR_RUSTURF_TUNNEL_STATE=2` (Team Aqua grunt flees into Rusturf Tunnel).
3. **Route116 / Rusturf Tunnel**: Route116 coord event (47,9) `VAR_ROUTE116_STATE==1` = Briney trigger. In the tunnel, state 2 gates the grunt back-up tiles (9,4),(9,5); beating TRAINER_GRUNT_RUSTURF_TUNNEL (lvl16 GEODUDE, GEODUDE, MACHOP) gives ITEM_DEVON_GOODS, clears DEVON_GOODS_STOLEN, sets **FLAG_RECOVERED_DEVON_GOODS**, `VAR_RUSTBORO_CITY_STATE=4`, `VAR_BRINEY_HOUSE_STATE=1`. Tunnel also has the HM Strength scene (FLAG_RECEIVED_HM_STRENGTH) and blockage coord events at (23,4),(25,4),(25,5).
4. **Return goods** in Devon Corp 1F: **FLAG_RETURNED_DEVON_GOODS** (set in RustboroCity/scripts.inc ~l.561; 1F stairs blocked until set); EXP Share from 3F = FLAG_RECEIVED_EXP_SHARE.
5. **Mr. Briney's house** (`Route104_MrBrineysHouse`): sailing offer checks FLAG_MR_BRINEY_SAILING_INTRO, then FLAG_DELIVERED_STEVEN_LETTER (unset => "both deliveries" trip to Dewford). Boarding sets `VAR_BOARD_BRINEY_BOAT_STATE=1`, `VAR_RUSTBORO_CITY_STATE=8`, `VAR_ROUTE104_STATE=2`, warps to MAP_ROUTE104 (13,51).
6. **Dewford Town**: landing sets `VAR_BOARD_BRINEY_BOAT_STATE=2`; FLAG_VISITED_DEWFORD_TOWN; Old Rod (FLAG_RECEIVED_OLD_ROD); boat back to Petalburg is refused until FLAG_DELIVERED_STEVEN_LETTER.
7. **Dewford Gym** (BRAWLY): win => **FLAG_DEFEATED_DEWFORD_GYM + FLAG_BADGE02_GET**, TM Bulk Up (FLAG_RECEIVED_TM_BULK_UP).
8. **Granite Cave** (1F -> Steven's room): 1F gives HM Flash (FLAG_RECEIVED_HM_FLASH) from a script; Steven's room: letter handed over => **FLAG_DELIVERED_STEVEN_LETTER**, TM Steel Wing, **FLAG_REGISTERED_STEVEN_POKENAV**.
9. **Boat onward**: Dewford script ~l.160 clears Route109 Briney/boat hide flags; lands at Route109 (then Slateport). **FLAG_DELIVERED_DEVON_GOODS** is set in SlateportCity_OceanicMuseum_2F (outside this recon's scope).

## Per-map gates (short)
- DevonCorp 1F/2F/3F: no trainers/items; 1F stairs blocked until goods returned; 2F fossil var `VAR_FOSSIL_RESURRECTION_STATE`.
- Route116 (5 warps, 10 trainers, 5 balls, 2 hidden items): optional; Briney trigger var `VAR_ROUTE116_STATE`. Flash is not needed.
- RusturfTunnel (1 trainer: the grunt; 2 balls; 5 coord events): gate = VAR_RUSTURF_TUNNEL_STATE (2 -> 3 -> 4/5 clear).
- Route104_MrBrineysHouse: gated by the three DELIVERED flags above.
- DewfordTown / Gym / GraniteCave_1F / StevensRoom: see steps 6-8. Gym is a dark room (flash level tracks trainers beaten).
- Route106 (4 trainers), Route107 (7), Route109 (14): sea routes (Surf not needed for the boat ride; trainers on them are swimmers).

## Dewford Gym (MAP_DEWFORD_TOWN_GYM)
Trainers (name, lvl/species): TAKAO (13 MACHOP) at (2,18); JOCELYN (13 MEDITITE) at (15,3); LAURA, CRISTIAN, LILITH, BRENDEN (see json `trainers[].party`). **BRAWLY** (`gym_leader`, local id 1 at (4,3), TRAINER_BRAWLY_1): MACHOP 16, MEDITITE 16, MAKUHITA 19 (Sitrus Berry); items 2x Super Potion.

## Counts (warps / trainers / item balls / coord events / hidden items)
- RustboroCity_DevonCorp_1F: 3 / 0 / 0 / 0 / 0
- RustboroCity_DevonCorp_2F: 2 / 0 / 0 / 0 / 0
- RustboroCity_DevonCorp_3F: 1 / 0 / 0 / 0 / 0
- Route116: 5 / 10 / 5 / 1 / 2
- RusturfTunnel: 3 / 1 / 2 / 5 / 0
- Route104_MrBrineysHouse: 2 / 0 / 0 / 0 / 0
- DewfordTown: 5 / 0 / 0 / 0 / 0
- DewfordTown_Gym: 2 / 6 / 0 / 0 / 0
- GraniteCave_1F: 4 / 0 / 1 / 0 / 0
- GraniteCave_StevensRoom: 1 / 0 / 0 / 0 / 0
- Route106: 1 / 4 / 1 / 0 / 3
- Route107: 0 / 7 / 0 / 0 / 0
- Route109: 1 / 14 / 2 / 0 / 6

## Could not extract / caveats
- Party species/levels come from the trainer tables; held items and moves not captured except as above.
- DewfordTown_Gym leader is a non-trainer-typed object (script-triggered) so he is stored under `gym_leader`.
- Rustboro scene scripts live in RustboroCity (not in the requested map list); only the key flag lines were quoted. Route104 and Slateport were not extracted.
- RusturfTunnel coord events show `var: TRIGGER_RUN_IMMEDIATELY` literally as map.json states it.
- Nothing here is verified live: this is a NOTE from source, to be checked before code depends on it.

Wall time: ~98s of tool time before this report (about 10-12 min session-wide).
