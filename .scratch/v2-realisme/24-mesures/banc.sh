#!/bin/bash
# Banc du ticket v2-realisme/24 : 14 attributs, 20 matchs, 80 contre 70, 4 processus.
# usage : banc.sh <dossier_du_code> <dossier_de_sortie>   (lancer depuis une copie figée du code si on modifie le moteur)
CODE=$1; OUT=$2; mkdir -p "$OUT"; cd "$CODE"
printf '%s\n' Passing "First Touch" Technique Dribbling Tackling Finishing Decisions Composure Anticipation Positioning Pace Acceleration Agility Strength | \
  xargs -P 4 -I{} sh -c 'PYTHONHASHSEED=0 uv run python -m scripts.measure_v2 20 --profil "{}" --niveaux 80 70 --json "'"$OUT"'/{}.json" > "'"$OUT"'/{}.log" 2>&1; echo "fini {} $?"'
