import pickle, sys, numpy as np, collections, re
n = sys.argv[1]
E = pickle.load(open(f'planos/{n}.pkl', 'rb'))
def bbox(lst):
    xs, ys = [], []
    for d in lst:
        for p in d.get('pts') or ([d['p'][:2]] if 'p' in d else []):
            xs.append(p[0]); ys.append(p[1])
    if not xs: return None
    xs, ys = np.array(xs), np.array(ys)
    return [round(np.percentile(xs, 1)), round(np.percentile(ys, 1)), round(np.percentile(xs, 99)), round(np.percentile(ys, 99))]
por = collections.defaultdict(list)
for d in E: por[d['capa']].append(d)
for capa in ['manzana ok', 'CONT-MNR', 'CONT-MJR', 'SECCION VIAL', 'SECCIONES', 'Calles', 'NOMBRE_DE_CALLES', 'Eje', 'propuestita', 'gradas', 'canales', 'quebradas', 'Cotas', 'COTAS PROPIEDADES', 'BM', 'GRID_NE_TXT', 'retiro vial', 'VIA PRINCIPAL', 'VIA SECUNDARIA', 'CARRETERA', 'Secciones Viales Nuevas', '0', 'curvas nivel', 'nuevo rio', 'LOSA', 'puentes', 'CASCO URBANO 2017']:
    if capa not in por: continue
    L = por[capa]
    print(f'--- {capa}: {len(L)} bbox(p1-p99) {bbox(L)}')
    zs = [d.get('z') for d in L if d.get('z') not in (None, 0.0)]
    if zs: print('    elevaciones LWPOLYLINE: n', len(zs), 'min', min(zs), 'max', max(zs), 'valores', sorted(collections.Counter(round(z, 2) for z in zs).items())[:12])
    txts = [d.get('txt') for d in L if d.get('txt')]
    if txts: print('    textos:', [t.replace('\n', ' / ')[:60] for t in txts[:14]])
    meds = [round(d['med'], 2) for d in L if d.get('med')]
    if meds: print('    cotas (medidas):', meds[:30])
