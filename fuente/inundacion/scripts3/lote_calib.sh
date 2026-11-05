#!/bin/bash
# corridas de calibración (escenario presente): cambio de CN (humedad antecedente) y profundidad del cauce excavado
cd "$(dirname "$0")/.."
for dcn in 0 6 11; do
  for prof in 0.5 1.5; do
    et="c${dcn}_p${prof}"
    [ -f sim/res_presente_${et}.npz ] || python3 -I scripts3/sim2d.py presente $et $dcn $prof 0.20 6 18 > sim/log_presente_${et}.txt 2>&1
    python3 -I scripts3/calibrar.py sim/res_presente_${et}.npz >> sim/calibracion.txt
  done
done
echo FIN >> sim/calibracion.txt
