import json, re
from fractions import Fraction as F
# species constants
sp = {}
for m in re.finditer(r'^#define (SPECIES_\w+) (\d+)\s*$', open('species.h').read(), re.M):
    sp[m.group(1)] = int(m.group(2))
# national dex enum
txt = open('pokedex.h').read()
enum1 = txt[txt.index('enum {'):txt.index('};')]
nat = {}
i = 0
for m in re.finditer(r'^\s*(NATIONAL_DEX_\w+),', enum1, re.M):
    nat[m.group(1)] = i; i += 1
assert nat['NATIONAL_DEX_DEOXYS'] == 386 and nat['NATIONAL_DEX_TREECKO'] == 252
def natdex(s):  # 'SPECIES_X' -> national
    return nat['NATIONAL_DEX_' + s[len('SPECIES_'):]]
# gender ratios
si = open('species_info.h').read()
body = si[si.index('gSpeciesInfo[] ='):]
gr = {}
blocks = re.split(r'\n    \[(SPECIES_\w+)\]\s*=', body)
for k in range(1, len(blocks), 2):
    name, b = blocks[k], blocks[k+1]
    m = re.search(r'\.genderRatio\s*=\s*([^,\n]+),', b)
    if not m:
        gr[name] = None; continue
    v = m.group(1).strip()
    if v == 'MON_MALE': r = 0
    elif v == 'MON_FEMALE': r = 254
    elif v == 'MON_GENDERLESS': r = 255
    else:
        p = re.match(r'PERCENT_FEMALE\(([\d.]+)\)', v).group(1)
        r = min(254, int(F(p) * 255 / 100))  # C truncation toward zero (positive)
    gr[name] = r
# wild
d = json.load(open('wild_encounters.json'))
g = [g for g in d['wild_encounter_groups'] if g['label'] == 'gWildMonHeaders'][0]
rates = {f['type']: f for f in g['fields']}
LAND = rates['land_mons']['encounter_rates']; WATER = rates['water_mons']['encounter_rates']
RS = rates['rock_smash_mons']['encounter_rates']; FISH = rates['fishing_mons']['encounter_rates']
FG = rates['fishing_mons']['groups']
assert LAND == [20,20,10,10,10,10,5,5,4,4,1,1] and WATER == [60,30,5,4,1] and RS == WATER
assert FISH == [70,30,60,20,20,40,40,15,4,1] and FG == {'old_rod':[0,1],'good_rod':[2,3,4],'super_rod':[5,6,7,8,9]}
EXCL = {'MAP_CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP1','MAP_CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP2','MAP_CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP3'}
id2folder = json.load(open('id2folder.json'))
rms = [s['id'] for s in json.load(open('region_map_sections.json'))['map_sections']]
mapsec_id = {n: i for i, n in enumerate(rms)}
mapsec = {}
for mid, f in id2folder.items():
    mj = json.load(open(f'maps/{f}.json'))
    assert mj['id'] == mid, (mid, mj['id'])
    mapsec[mid] = mj['region_map_section']
MAPG = {
 'MAP_METEOR_FALLS_1F_2R': {'surf','waterfall'}, 'MAP_METEOR_FALLS_B1F_1R': {'surf','waterfall'}, 'MAP_METEOR_FALLS_B1F_2R': {'surf','waterfall'},
 'MAP_SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM': {'surf'}, 'MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM': {'surf'},
 'MAP_SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM': {'surf'}, 'MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM': {'surf'},
 'MAP_SHOAL_CAVE_LOW_TIDE_ICE_ROOM': {'strength','surf'},
}
for k in MAPG: assert k in mapsec, k
tables = []  # (map, method, {species: rate})
seen_alter = False
for e in g['encounters']:
    mid = e['map']
    if mid in EXCL: continue
    if mid == 'MAP_ALTERING_CAVE':
        if seen_alter: continue
        seen_alter = True
    for typ, sr in (('land_mons', LAND), ('water_mons', WATER), ('rock_smash_mons', RS)):
        if typ not in e: continue
        if typ == 'land_mons' and mid == 'MAP_ROUTE130': continue
        mons = e[typ]['mons']; assert len(mons) == len(sr), (mid, typ)
        acc = {}
        for mon, r in zip(mons, sr): acc[mon['species']] = acc.get(mon['species'], 0) + r
        tables.append((mid, typ.split('_mons')[0], acc))
    if 'fishing_mons' in e:
        mons = e['fishing_mons']['mons']; assert len(mons) == 10
        for rod, idxs in FG.items():
            acc = {}
            for ix in idxs: acc[mons[ix]['species']] = acc.get(mons[ix]['species'], 0) + FISH[ix]
            tables.append((mid, rod, acc))
def gates(mid, method):
    s = set()
    if method == 'water': s |= {'surf'}
    elif method == 'rock_smash': s |= {'rock_smash'}
    elif method.endswith('_rod'): s |= {'rod'}
    if mid.startswith('MAP_UNDERWATER_'): s |= {'surf','dive'}
    s |= MAPG.get(mid, set())
    return frozenset(s)
spec = {}
for mid, meth, acc in tables:
    for s, r in acc.items():
        spec.setdefault(s, []).append((mid, meth, r))
LEG = {144,145,146,150,151,243,244,245,249,250,251} | set(range(377,387))
out = {}
for s, lst in spec.items():
    n = natdex(s)
    best = max(r for _, _, r in lst)
    secs = sorted({mapsec[m] for m, _, _ in lst})
    gsets = [gates(m, meth) for m, meth, _ in lst]
    mn = min(len(x) for x in gsets)
    easiest = sorted({tuple(sorted(x)) for x in gsets if len(x) == mn})
    reasons = []
    if best <= 4: reasons.append('rate')
    ratio = gr[s]
    var = None
    if ratio in (31, 63, 191):
        if ratio in (31, 63): mg, p = 'female', F(ratio, 256)
        else: mg, p = 'male', F(256 - ratio, 256)
        v = best * p
        if v <= 4: reasons.append('variant'); var = (mg, v)
    if len(secs) == 1 and mn >= 2: reasons.append('pseudo')
    if n in LEG: reasons.append('legendary')
    if n == 349: reasons.append('special')
    out[n] = dict(name=s, best=best, secs=secs, secids=[mapsec_id[x] for x in secs], mingates=mn, easiest=easiest, ratio=ratio, reasons=reasons, var=var, tables=lst)
json.dump({str(k): {**v, 'var': (v['var'][0], str(v['var'][1])) if v['var'] else None} for k, v in out.items()}, open('derived.json', 'w'), indent=1)
print('tables', len(tables), 'live wild species', len(out))
print('\nRATE list (nat, name, best_rate):')
for n in sorted(out):
    if 'rate' in out[n]['reasons']: print(' ', n, out[n]['name'], out[n]['best'])
print('\nVARIANT list (nat, name, ratio, best, minority, exact, float):')
for n in sorted(out):
    if out[n]['var']: print(' ', n, out[n]['name'], out[n]['ratio'], out[n]['best'], out[n]['var'][0], out[n]['var'][1], float(out[n]['var'][1]))
print('\nPSEUDO list (nat, name, mapsec, easiest gates):')
for n in sorted(out):
    if 'pseudo' in out[n]['reasons']: print(' ', n, out[n]['name'], out[n]['secs'], out[n]['secids'], out[n]['easiest'])
print('\nSingle-MAPSEC species (all, incl. non-pseudo):')
for n in sorted(out):
    if len(out[n]['secs']) == 1: print(' ', n, out[n]['name'], out[n]['secs'][0], out[n]['secids'][0], 'min', out[n]['mingates'], out[n]['easiest'])
print('\nLegendary/special wild:')
for n in sorted(out):
    if set(out[n]['reasons']) & {'legendary','special'}: print(' ', n, out[n]['name'], out[n]['reasons'], out[n]['best'])
print('\nAll reasons per wild species with any reason:')
for n in sorted(out):
    if out[n]['reasons']: print(' ', n, out[n]['name'], out[n]['reasons'])
