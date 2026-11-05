# Tablas en Markdown para la documentación (calibración y resultados por escenario) a partir de los resultados exportados
import json, re
D = json.load(open('inund/datos_mod.json'))['inundacion']
CU = json.load(open('sim/calibracion_unidades.json'))
celdas = {}
for l in open('sim/calibracion.txt'):
    m = re.match(r"sim/res_presente_(\S+)\.npz .*'k2': np\.float64\(([\d.]+)\).*'criticos': (\d+)", l)
    if m: celdas[m.group(1)] = float(m.group(2))
f = lambda v, d=2: ('%.*f' % (d, v)).replace('.', ',')
print('<!--TABLA_CALIBRACION-->')
print('| Corrida | ΔCN | Cauce (m) | n de bloque | Edificaciones | Umbrales (m) | κ 4 clases | κ ponderado | κ 2 clases | Unidades en riesgo alto (sim / mapa C-04) | Puntos críticos ≥ 10 cm / ≥ 30 cm | κ celdas (C-03) |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|')
for r in CU:
    print('| `%s` | %+d | %s | %s | %s | %s | %s | %s | %s | %d / %d | %d / %d | %s |' % (
        r['corrida'], r['dCN'], f(r['prof_cauce_m'], 1), f(r['n_bloque'], 2), '+%d m' % r['edificaciones_m'] if r['edificaciones_m'] else 'no',
        ' · '.join(f(u, 2) for u in r['umbrales']), f(r['k4'], 3), f(r['kw'], 3), f(r['k2'], 3), r['n3'], r['n3t'], r['pc10'], r['pc30'],
        f(celdas[r['corrida']], 3) if r['corrida'] in celdas else '—'))
print()
CORTO = {'presente': 'Presente (1981–2020)', 'cmip5_rcp45_2031_2060': 'CMIP5 RCP 4.5 · 2031–2060', 'cmip5_rcp45_2071_2100': 'CMIP5 RCP 4.5 · 2071–2100',
         'cmip5_rcp85_2031_2060': 'CMIP5 RCP 8.5 · 2031–2060', 'cmip5_rcp85_2071_2100': 'CMIP5 RCP 8.5 · 2071–2100', 'cmip6_ssp245_2031_2060': 'CMIP6 SSP2-4.5 · 2031–2060',
         'cmip6_ssp245_2071_2100': 'CMIP6 SSP2-4.5 · 2071–2100', 'cmip6_ssp585_2031_2060': 'CMIP6 SSP5-8.5 · 2031–2060', 'cmip6_ssp585_2071_2100': 'CMIP6 SSP5-8.5 · 2071–2100'}
pct = lambda e: (' (%+.0f %%)' % e['cambio']).replace('.', ',') if e['cambio'] else ''
print('<!--TABLA_ESCENARIOS-->')
print('| Escenario | P24 en la Plaza | Tesis: ciudad en peligro alto | Unidades en riesgo alto: tesis (tabla / mapa) · simulación | κ por unidad | Puntos críticos en peligro alto: tesis · simulación | Área urbana > 10 cm | Área > 50 cm | Edificaciones con > 30 cm |')
print('|---|---|---|---|---|---|---|---|---|')
for e in D['escenarios']:
    T, S = e['tesis'], e['sim']
    print('| %s | %s mm%s | %s %% | %d / %d · **%d** | %s | %d · **%d** | %s km² | %s km² | %s |' % (
        CORTO[e['id']], f(e['P24'], 1), pct(e), f(T['pct_ciudad'], 1), T['unidades'], T['unidades_mapa'], S['unidades'], f(S['kappa_unidades'], 2),
        T['criticos'], S['criticos'], f(S['area01'], 2), f(S['area05'], 2), format(S['edif03'], ',').replace(',', ' ')))
print()
print('<!--TABLA_RESULTADOS-->')
print('| Escenario | P24 en la Plaza | Unidades en riesgo alto: tesis · simulación | Área urbana con > 10 cm | Puntos críticos en peligro alto: tesis · simulación |')
print('|---|---|---|---|---|')
for e in D['escenarios']:
    T, S = e['tesis'], e['sim']
    print('| %s | %s mm%s | %d · **%d** | %s km² | %d · **%d** |' % (CORTO[e['id']], f(e['P24'], 1), pct(e), T['unidades'], S['unidades'], f(S['area01'], 2), T['criticos'], S['criticos']))
