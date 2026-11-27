#!/bin/bash
# Banc de fluidité du ticket v2-ecran-match/22 : chaque état de l'interface est construit dans un worktree détaché
# (la branche de travail et ui/ ne sont pas touchés), servi par `vite preview`, puis mesuré par 22-fps.js sur les
# réponses d'API figées (02b2-fixture-fps.py ; empreinte attendue : 22-trace-figee.json). Fenêtre de mesure
# identique pour tous les états (10 à 40 s de lecture, voir 22-fps.js) : le banc du 02b2 mesurait les états d'avant le
# 21a sur une page immobile.
#
#   bash 22-banc.sh <dossier de travail hors dépôt> <dossier des réponses figées> <tours> <commit>...
#   FPS_RATE=12 bash 22-banc.sh ...   (ralenti processeur, 6 par défaut)
#
# Les commits sont mesurés en alternance (tour 1 : A B C, tour 2 : A B C...) pour que les dérives de charge de la
# machine touchent tous les états de la même façon. Une ligne JSON par passage, ajoutée à <travail>/fps.jsonl.
# Dépendances : celles de ui/ (inchangées de 41e573e à 145a292, node_modules partagé par lien symbolique).
set -u
DEPOT=$(git rev-parse --show-toplevel)
ICI=$(cd "$(dirname "$0")" && pwd)
TRAVAIL=$1; FIGEES=$2; TOURS=$3; shift 3
mkdir -p "$TRAVAIL/wt"
for c in "$@"; do
  d="$TRAVAIL/wt/$c"
  [ -d "$d" ] || git -C "$DEPOT" worktree add --detach "$d" "$c" >/dev/null
  [ -e "$d/ui/node_modules" ] || ln -s "$DEPOT/ui/node_modules" "$d/ui/node_modules"
  [ -f "$d/ui/dist/index.html" ] || (cd "$d/ui" && npx vite build >"$TRAVAIL/wt/build-$c.log" 2>&1)
done
for t in $(seq 1 "$TOURS"); do
  for c in "$@"; do
    # port déjà servi (serveur orphelin d'un autre état) : la mesure viserait le mauvais état, on s'arrête
    if curl -s -o /dev/null http://localhost:4174/; then echo "port 4174 déjà occupé, mesure de $c refusée" >&2; exit 1; fi
    # groupe de processus à part (setsid) : npx lance vite dans un processus enfant, tué avec lui à la fin
    (cd "$TRAVAIL/wt/$c/ui" && exec setsid npx vite preview --port 4174 --strictPort >"$TRAVAIL/wt/preview-$c.log" 2>&1) &
    P=$!
    for i in $(seq 1 30); do curl -s -o /dev/null http://localhost:4174/ && break; sleep 0.5; done
    node "$ICI/22-fps.js" http://localhost:4174 "$FIGEES" "x${FPS_RATE:-6}-$c" 1 | tee -a "$TRAVAIL/fps.jsonl"
    kill -- -$P 2>/dev/null; wait $P 2>/dev/null
  done
done
# Nettoyage : git worktree remove --force <travail>/wt/<commit> pour chaque état.
