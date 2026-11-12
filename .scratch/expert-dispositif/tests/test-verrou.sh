#!/usr/bin/env bash
# Banc du verrou de commit (scénarios d'interruption). Usage : bash test-verrou.sh <dossier_temporaire_vide>
# Copie les VRAIS scripts (.claude/qc, cloture.py, expert.md) dans un dépôt jetable et joue le hook réel
# (verrou-commit.ps1) avec un événement « git commit ». Ne touche ni au dépôt ni au journal réels.
set -u
SRC="$(cd "$(dirname "$0")/../../.." && pwd)"
R="$1/depot"
rm -rf "$R"; mkdir -p "$R/.claude/qc" "$R/.claude/skills/valider-ticket-simulafoot" "$R/.claude/skills/valider-etape" "$R/.claude/agents" "$R/v2engine" "$R/docs"
cp "$SRC"/.claude/qc/*.ps1 "$R/.claude/qc/"
cp "$SRC/.claude/skills/valider-ticket-simulafoot/cloture.py" "$R/.claude/skills/valider-ticket-simulafoot/"
cp "$SRC/.claude/agents/expert.md" "$R/.claude/agents/"
cp "$SRC/.claude/agents/controle-qualite.md" "$R/.claude/agents/"
cp "$SRC/.claude/skills/valider-etape/SKILL.md" "$R/.claude/skills/valider-etape/"
cd "$R" || exit 1
G() { git -c user.name=t -c user.email=t@t -c core.autocrlf=false "$@"; }
G init -q; echo "v = 1" > v2engine/x.py; echo "w = 1" > v2engine/y.py; echo doc > docs/a.md
G add -A; G commit -qm base; BASE=$(git rev-parse HEAD)
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/qc/integrite.ps1 -Action MettreAJour > /dev/null
CL=".claude/skills/valider-ticket-simulafoot/cloture.py"
J=".claude/qc/journal.jsonl"
RAP="$1/rapport.md"
PASS=0; FAIL=0

lock() {  # code de sortie du hook réel pour la commande donnée
  printf '{"tool_input":{"command":"%s"}}' "${1:-git commit -m essai}" \
    | HOME="${FAUXHOME:-$HOME}" powershell -NoProfile -ExecutionPolicy Bypass -File .claude/qc/verrou-commit.ps1 > "$R.out" 2>&1
  echo $?
}
qc() { powershell -NoProfile -ExecutionPolicy Bypass -File .claude/qc/append.ps1 -Action Append -SousEtape "$1" -Verdict "$2" -Justification "$3" > /dev/null; }
rapport() {  # rapport expert au format imposé, sur l'état actuel de x.py
  local emp; emp=$(python -I "$CL" empreinte --base "$BASE" ${FICHIERS:-v2engine/x.py})
  { echo "Ticket : ${2:-t/01}"; echo "Empreinte : $emp"; echo "Verdict : $1"; echo "Résumé : essai"
    for s in "Identification" "Analyse du réalisme" "Vérifications" "Anomalies" "Recommandation finale"; do echo "## $s"; echo x; done; } > "$RAP"
}
decision() { python -I "$CL" decision --ticket t/01 --rapport "$RAP" --base "$BASE" v2engine/x.py "$@" > /dev/null; }
reset() {  # état de départ : x.py modifié et indexé, journal avec une entrée d'un autre ticket
  G reset -q --hard "$BASE"; G clean -qfd -e .claude; rm -f "$J"
  qc "autre/09" "VALIDÉ" "historique"
  echo "v = 2" > v2engine/x.py; G add v2engine/x.py
}
nominal() { reset; qc t/01 VALIDÉ ok; rapport APPROVED; decision; }
check() {  # check <nom> <code attendu> <code obtenu>
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "OK    $1 (code $3)"; else FAIL=$((FAIL+1)); echo "ÉCHEC $1 : attendu $2, obtenu $3"; sed 's/^/      /' "$R.out"; fi
}

nominal;                                                                check "S0 nominal : QC VALIDÉ + clôture complète" 0 "$(lock)"
reset; qc t/01 VALIDÉ ok;                                               check "I1 interruption après QC VALIDÉ, avant clôture" 2 "$(lock)"
reset; qc t/01 VALIDÉ ok; rapport APPROVED;                             check "I2 interruption après rapport, avant décision" 2 "$(lock)"
nominal; tail -n1 "$J" | head -c 60 > "$R.t"; sed -i '$d' "$J"; cat "$R.t" >> "$J"
                                                                        check "I3 interruption pendant l'écriture de la clôture (ligne tronquée)" 2 "$(lock)"
nominal; echo "v = 3" > v2engine/x.py; G add v2engine/x.py;             check "I4 code modifié (et indexé) après la revue" 2 "$(lock)"
nominal; echo "v = 3" > v2engine/x.py;                                  check "I5 code modifié non indexé après la revue" 2 "$(lock)"
nominal; rm "$RAP";                                                     check "I6 rapport supprimé après clôture" 2 "$(lock)"
nominal; echo "ajout" >> "$RAP";                                        check "I7 rapport modifié après clôture" 2 "$(lock)"
nominal; qc t/01 REFUSÉ "nouvelle revue";                               check "I8 QC REFUSÉ ajouté après la clôture" 2 "$(lock)"
nominal; qc t/02 VALIDÉ "autre ticket";                                 check "I9 QC VALIDÉ d'un autre ticket après la clôture" 2 "$(lock)"
reset; qc t/01 VALIDÉ ok; qc t/01/cloture VALIDÉ "ancienne forme";      check "I10 clôture VALIDÉ sans champs de liaison (append.ps1)" 2 "$(lock)"
reset; qc t/01 VALIDÉ ok; rapport REJECTED; decision;                   check "I11 expert REJECTED (clôture REFUSÉ journalisée)" 2 "$(lock)"
reset; qc t/01 VALIDÉ ok; rapport INCONCLUSIVE; decision;               check "I12 expert INCONCLUSIVE" 2 "$(lock)"
reset; qc t/01 VALIDÉ ok; rapport APPROVED_WITH_RESERVATIONS; decision; check "I13 réserves non acceptées" 2 "$(lock)"
reset; qc t/01 VALIDÉ ok; rapport APPROVED_WITH_RESERVATIONS; decision --reserves-acceptees
                                                                        check "I14 réserves acceptées par le propriétaire" 0 "$(lock)"
reset; qc t/01 REFUSÉ ko; rapport APPROVED; decision --qc VALIDÉ;       check "I15 --qc VALIDÉ annoncé mais QC journalisé REFUSÉ" 2 "$(lock)"
reset; rapport APPROVED; decision;                                      check "I16 aucun QC pour le ticket" 2 "$(lock)"
reset; qc t/01 VALIDÉ ok; rapport APPROVED t/99; decision;              check "I17 rapport d'un autre ticket" 2 "$(lock)"
nominal; python -I - "$J" <<'EOF'
import json, sys
p = sys.argv[1]; lignes = open(p, encoding="utf-8-sig").read().splitlines()
c = json.loads(lignes[-1]); c["qc_id"] = json.loads(lignes[0])["id"]; lignes[-1] = json.dumps(c, ensure_ascii=False)
open(p, "w", encoding="utf-8").write("\r\n".join(lignes) + "\r\n")
EOF
                                                                        check "I18 clôture forgée : qc_id d'une autre entrée" 2 "$(lock)"
nominal; python -I - "$J" <<'EOF'
import json, sys
p = sys.argv[1]; lignes = open(p, encoding="utf-8-sig").read().splitlines()
c = json.loads(lignes[-1]); c["empreinte"] = "0" * 64; lignes[-1] = json.dumps(c, ensure_ascii=False)
open(p, "w", encoding="utf-8").write("\r\n".join(lignes) + "\r\n")
EOF
                                                                        check "I19 clôture forgée : empreinte arbitraire" 2 "$(lock)"
nominal; rapport REJECTED; python -I - "$J" "$RAP" <<'EOF'
import hashlib, json, sys
p = sys.argv[1]; lignes = open(p, encoding="utf-8-sig").read().splitlines()
c = json.loads(lignes[-1]); c["rapport_sha256"] = hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
lignes[-1] = json.dumps(c, ensure_ascii=False); open(p, "w", encoding="utf-8").write("\r\n".join(lignes) + "\r\n")
EOF
                                                                        check "I20 clôture VALIDÉ forgée sur un rapport REJECTED" 2 "$(lock)"
nominal; tail -n1 "$J" >> "$J";                                         check "I21 identifiants dupliqués (ligne recopiée)" 2 "$(lock)"
nominal; sed -i '1s/.*/{pas du json/' "$J";                             check "I22 ligne malformée au milieu du journal" 2 "$(lock)"
nominal; : > "$J";                                                      check "I23 journal vidé" 2 "$(lock)"
nominal; rm "$J";                                                       check "I24 journal supprimé" 2 "$(lock)"
nominal; echo "w = 2" > v2engine/y.py; G add v2engine/y.py;             check "I25 fichier de code indexé non revu" 2 "$(lock)"
nominal; echo "statut livré" > docs/a.md; G add docs/a.md;              check "I26 doc indexée en plus (suivi après clôture)" 0 "$(lock)"
reset; echo "n = 1" > v2engine/n.py; qc t/01 VALIDÉ ok; FICHIERS="v2engine/x.py v2engine/n.py" rapport APPROVED
python -I "$CL" decision --ticket t/01 --rapport "$RAP" --base "$BASE" v2engine/x.py v2engine/n.py > /dev/null
[ "$(tail -n1 "$J" | grep -c '"verdict": "VALIDÉ"')" = 1 ] || echo "ÉCHEC I27 : la décision aurait dû être VALIDÉ"
                                                                        check "I27 fichier nouveau revu mais non indexé" 2 "$(lock)"
reset; printf 'v = 2\nz = 1\n' > v2engine/x.py; G add v2engine/x.py; printf 'v = 2\n' > v2engine/x.py
qc t/01 VALIDÉ ok; rapport APPROVED; decision
                                                                        check "I28 index différent de la version revue (hunk partiel)" 2 "$(lock)"
nominal; echo "# x" >> "$CL";                                           check "I29 cloture.py modifié (intégrité)" 2 "$(lock)"
nominal; sed -i 's/tools: Read, Grep, Glob/tools: Read, Grep, Glob, Bash/' .claude/agents/expert.md
                                                                        check "I30 outils de l'expert élargis (intégrité)" 2 "$(lock)"
nominal; echo "# x" >> .claude/qc/verrou-commit.ps1;                    check "I31 verrou modifié (intégrité existante)" 2 "$(lock)"
reset; qc t/01 VALIDÉ ok;                                               check "I32 commande sans git : hook muet" 0 "$(lock 'ls -la')"
nominal;                                                                check "I33 git push avec clôture valide" 0 "$(lock 'git push origin main')"
reset; qc t/01 VALIDÉ ok;                                               check "I34 git push sans clôture" 2 "$(lock 'git push origin main')"
nominal; G commit -qm "ticket"; echo "v = 4" > v2engine/x.py; G add v2engine/x.py
                                                                        check "I35 après commit, nouvelle modification sans nouvelle revue" 2 "$(lock)"

nominal; echo "# x" >> .claude/agents/controle-qualite.md;              check "I36 agent controle-qualite du dépôt modifié (intégrité)" 2 "$(lock)"
# Exemplaires globaux (~/.claude) : seulement si PowerShell lit $HOME dans la variable HOME (pwsh sous Linux/macOS).
FH="$1/fauxhome"; rm -rf "$FH"; mkdir -p "$FH/.claude/agents" "$FH/.claude/skills/valider-etape"
if [ "$(HOME="$FH" powershell -NoProfile -Command '$HOME' | tr -d '\r')" = "$FH" ]; then
  nominal; cp .claude/agents/controle-qualite.md "$FH/.claude/agents/"; cp .claude/skills/valider-etape/SKILL.md "$FH/.claude/skills/valider-etape/"
                                                                        check "I37 exemplaires globaux identiques au dépôt" 0 "$(FAUXHOME="$FH" lock)"
  echo "# diverge" >> "$FH/.claude/skills/valider-etape/SKILL.md"
  nominal;                                                              check "I38 exemplaire global divergent du dépôt" 2 "$(FAUXHOME="$FH" lock)"
else
  echo "NON EXÉCUTÉS I37-I38 : PowerShell ne lit pas \$HOME dans HOME (Windows) ; vérifier à la main avec les exemplaires réels."
fi

echo "---- $PASS réussis, $FAIL échoués"
[ "$FAIL" = 0 ]
