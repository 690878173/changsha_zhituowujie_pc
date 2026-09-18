import json
d = json.load(open(r'/8-3到8-8/roguefitness\cs\roguefitness_resolved.json', 'r', encoding='utf-8'))

# --- promos ---
pm = d['promos']['activePromos']
print('promos type:', type(pm).__name__)
k = list(pm.keys())[0]
print('key:', k)
v = pm[k]
print('promo item:', v)

# --- lists ---
print()
l = d['lists']
print('lists type:', type(l).__name__)
if isinstance(l, list):
    print('len:', len(l))
    print('list[0]:', l[0])
    print('list[1]:', l[1])
else:
    for kk, vv in l.items():
        print(kk, type(vv).__name__, str(vv)[:80])
