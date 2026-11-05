#!/bin/bash
# calibración del cauce con el terreno corregido (cauce continuo y depresiones con salida): presente, profundidad 1.0/0.5/1.5 m
cd "$(dirname "$0")/.."
for p in 1.0 0.5 1.5; do
  et="b3pt_c0_p${p}"
  [ -f sim/res_presente_${et}.npz ] || python3 -I scripts3/sim2d.py presente $et 0 $p 0.10 6 18 3.0 1 1 > sim/log_presente_${et}.txt 2>&1
  echo "$et listo $(date +%H:%M:%S)"
done
echo FIN_TERRENO
