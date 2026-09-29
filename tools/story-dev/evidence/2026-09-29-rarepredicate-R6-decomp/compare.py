import json
from fractions import Fraction as F
ours = json.load(open(r'C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot/modules/data/emerald_rarity.json', encoding='utf-8'))
sp = ours['species']
mine = json.load(open('derived.json'))
rms = [s['id'] for s in json.load(open('region_map_sections.json'))['map_sections']]
LEG = {144,145,146,150,151,243,244,245,249,250,251} | set(range(377,387))

wild_rows = {k for k, v in sp.items() if v['best_rate'] is not None}
print('committed rows', len(sp), 'wild rows', len(wild_rows), 'mine wild', len(mine))
print('in committed-wild not mine:', sorted(wild_rows - set(mine), key=int))
print('in mine not committed-wild:', sorted(set(mine) - wild_rows, key=int))
nonwild = sorted(set(sp) - wild_rows, key=int)
print('committed non-wild rows:', [(k, sp[k]['name'], sp[k]['reasons']) for k in nonwild])
# key consistency
for k, v in sp.items():
    if str(v['national']) != k: print('KEY MISMATCH', k, v['national'])
diffs = []
for k in sorted(set(mine) & wild_rows, key=int):
    m, o = mine[k], sp[k]
    if m['best'] != o['best_rate']: diffs.append((k, o['name'], 'best_rate', m['best'], o['best_rate']))
    if m['ratio'] != o['gender_ratio']: diffs.append((k, o['name'], 'gender_ratio', m['ratio'], o['gender_ratio']))
    if sorted(m['secids']) != sorted(o['mapsecs']): diffs.append((k, o['name'], 'mapsecs', m['secids'], sorted(o['mapsecs'])))
    mymaps = sorted({t[0][4:] for t in m['tables']})
    if mymaps != sorted(o['maps']): diffs.append((k, o['name'], 'maps', mymaps, sorted(o['maps'])))
    # reasons
    mr = set(m['reasons']); orr = set(o['reasons'])
    if mr != orr: diffs.append((k, o['name'], 'reasons', sorted(mr), sorted(orr)))
    # variant
    if m['var']:
        mg, mv = m['var'][0], F(m['var'][1])
        if o['variant_gender'] != mg or o['variant_pct'] is None or F(o['variant_pct']) != mv:
            diffs.append((k, o['name'], 'variant', (mg, float(mv)), (o['variant_gender'], o['variant_pct'])))
    else:
        if o['variant_gender'] is not None:
            diffs.append((k, o['name'], 'variant(gender set but mine none)', None, (o['variant_gender'], o['variant_pct'])))
        # check pct for 31/63/191 above threshold
        if m['ratio'] in (31, 63, 191):
            p = F(m['ratio'], 256) if m['ratio'] in (31, 63) else F(256 - m['ratio'], 256)
            v = m['best'] * p
            if o['variant_pct'] is None or F(o['variant_pct']) != v:
                diffs.append((k, o['name'], 'variant_pct(>4 info)', float(v), o['variant_pct']))
        elif o['variant_pct'] is not None:
            diffs.append((k, o['name'], 'variant_pct set for non-31/63/191', None, o['variant_pct']))
    # gates for single-MAPSEC
    if len(m['secs']) == 1:
        easiest = [list(x) for x in m['easiest']]
        if len(easiest) != 1 or sorted(o['gates']) != easiest[0]:
            diffs.append((k, o['name'], 'gates(single-mapsec)', easiest, o['gates']))
    else:
        if o['gates']:
            diffs.append((k, o['name'], 'gates(multi-mapsec, info)', [list(x) for x in m['easiest']], o['gates']))
print('\nDIFFS:')
for d in diffs: print(' ', d)
# reasons excluding 'variant' in both
print('\nReason diffs ignoring variant token:')
for k in sorted(set(mine) & wild_rows, key=int):
    a = set(mine[k]['reasons']) - {'variant'}; b = set(sp[k]['reasons']) - {'variant'}
    if a != b: print(' ', k, sp[k]['name'], sorted(a), sorted(b))
print('\nany committed row carrying reason variant:', [k for k, v in sp.items() if 'variant' in v['reasons']])
print('committed rows with variant_gender set:', [(k, v['name'], v['variant_gender'], v['variant_pct']) for k, v in sp.items() if v['variant_gender']])
print('committed legendary/special reasons:', sorted([(int(k), v['reasons']) for k, v in sp.items() if set(v['reasons']) & {'legendary', 'special'}]))
leg_rows = {int(k) for k, v in sp.items() if 'legendary' in v['reasons']}
print('legendary set ok:', leg_rows == LEG, sorted(LEG - leg_rows), sorted(leg_rows - LEG))
print('special:', [k for k, v in sp.items() if 'special' in v['reasons']])
print('mapsec sample check (id -> decomp name):')
used = sorted({x for v in sp.values() for x in v['mapsecs']})
for x in used: print('  ', x, rms[x])
print('gates_unmeasured present:', sorted({g for v in sp.values() for g in v.get('gates_unmeasured', [])}))
