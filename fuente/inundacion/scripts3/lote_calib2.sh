#!/bin/bash
# corridas de calibración con edificaciones como obstáculos (+3 m) y n de bloque reducido
cd "$(dirname "$0")/.."
while pgrep -f lote_calib.sh > /dev/null; do sleep 5; done
for dcn in 0 6; do
  et="b3_c${dcn}"
  [ -f sim/res_presente_${et}.npz ] || python3 -I scripts3/sim2d.py presente $et $dcn 1.0 0.10 6 18 3.0 > sim/log_presente_${et}.txt 2>&1
  python3 -I scripts3/calibrar.py sim/res_presente_${et}.npz >> sim/calibracion.txt
done
echo FIN2 >> sim/calibracion.txt
