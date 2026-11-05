#!/bin/bash
# corridas finales de los 9 escenarios con los parámetros calibrados (b3_c0):
# dCN 0, cauce 1.0 m, n de bloque 0.10, edificaciones +3 m, 6 h a 18 h
cd "$(dirname "$0")/.."
for e in cmip5_rcp85_2071_2100 cmip6_ssp585_2071_2100 cmip6_ssp245_2071_2100 cmip5_rcp85_2031_2060 cmip5_rcp45_2071_2100 cmip5_rcp45_2031_2060 cmip6_ssp585_2031_2060 cmip6_ssp245_2031_2060; do
  [ -f sim/res_${e}_final.npz ] || python3 -I scripts3/sim2d.py $e final 0 1.0 0.10 6 18 3.0 > sim/log_${e}_final.txt 2>&1
  echo "$e listo $(date +%H:%M:%S)"
done
echo FIN_FINAL
