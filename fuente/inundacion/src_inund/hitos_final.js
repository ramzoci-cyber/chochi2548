// ---------------------------------------------------------------- mallas de los hitos (Plaza de Armas, Catedral, Estadio)
{
  const SIN_SOMBRA = new Set(['pintura', 'cesped', 'adoquin', 'tartan']);
  for (const [k, geo] of Object.entries(H_)) if (!geo.vacio()) grupoHitos.add(geo.malla(MAT[k], !SIN_SOMBRA.has(k), true));
  console.info('Hitos generados en', Math.round(performance.now() - T0_DETALLE), 'ms');
}
