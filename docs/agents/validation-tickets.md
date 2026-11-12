# Validation des tickets : expert + contrôle qualité

Règle : `CLAUDE.md`, section « Clôture des tickets ». Procédure : skill `/valider-ticket-simulafoot`.

## Cycle

`/to-tickets` → annonce de l'estimation → `/implement` (tdd, code-review) → suite de tests → statut `implémenté` → `/valider-ticket-simulafoot` → statut `livré, validé expert + QC` → durée réelle comparée à l'estimation, ligne ajoutée à `suivi-estimations.md` → commit.

Estimation : règle dans `CLAUDE.md` (« Estimer la durée d'un ticket ») ; registre et format dans [suivi-estimations.md](suivi-estimations.md). Ce suivi n'entre pas dans la table de clôture : il ne bloque ni le verdict ni le commit.

`/implement` se termine par un commit : le verrou de commit le bloque tant que la dernière entrée du journal n'est pas une clôture `<id>/cloture` VALIDÉ écrite par `cloture.py decision` et encore vraie (voir « Verrou de commit »). Une entrée QC `VALIDÉ` seule ne suffit pas.

## Verrou de commit (depuis le 29/10/2026)

`.claude/qc/verrou-commit.ps1` garde ses contrôles (journal valide via `append.ps1 -Action Validate`, intégrité via `integrite.ps1`) et appelle ensuite `cloture.py verrou`, qui refuse si :
- la dernière entrée n'est pas une clôture VALIDÉ, ou qu'il lui manque un champ de liaison (`ticket`, `base`, `fichiers`, `empreinte`, `rapport`, `rapport_sha256`, `qc_id`, `expert`, `reserves_acceptees`) ;
- elle ne cite pas la dernière entrée QC du ticket, ou celle-ci n'est pas VALIDÉ ; un identifiant est dupliqué ;
- l'empreinte recalculée diffère (code modifié depuis la revue) ;
- le rapport est absent ou modifié (sha256), ou, relu, ne donne plus VALIDÉ avec la table de décision ;
- un fichier indexé n'est ni revu ni du suivi documentaire (`docs/`, `.scratch/`, `Plan architecte Simulafoot.md`, `PROJET_SIMULAFOOT.md`, journal), ou un fichier revu diffère entre index et arbre de travail.

`integrite.ps1` surveille aussi `cloture.py`, `expert.md`, `controle-qualite.md` et `valider-etape/SKILL.md`, repérés par leur chemin relatif à la racine du dépôt (mêmes clés sous Windows et Linux) ; les exemplaires globaux `~/.claude/...` de ces deux derniers, s'ils existent, doivent être identiques à ceux du dépôt (anomalie DIVERGENT). Banc : `bash .scratch/expert-dispositif/tests/test-verrou.sh <dossier temporaire vide>` (39 scénarios, dépôt jetable, scripts réels ; I37-I38 non exécutés sous Windows). Session cloud Linux : environnement `projet-foot` (PowerShell 7, liens `powershell` et `powershell.exe` vers `pwsh`).

Conséquence : un commit sans ticket clôturé est désormais refusé (avant, un QC `VALIDÉ` suffisait).

## Pièces

| Fichier | Portée | Rôle |
|---|---|---|
| `.claude/agents/expert.md` | projet | Sous-agent expert, outils Read/Grep/Glob seulement (pas d'écriture, pas de shell, pas de MCP) |
| `.claude/skills/valider-ticket-simulafoot/SKILL.md` | projet | Orchestration : dossier, expert, vérifications, QC, décision, traçabilité |
| `.claude/skills/valider-ticket-simulafoot/cloture.py` | projet | Empreinte du changement + table de décision déterministe (`--selftest`) |
| `controle-qualite`, `/valider-etape`, `.claude/qc/*` | global + projet, **inchangés** | Contrôle qualité existant, journal, verrou de commit |

## Commandes

```bash
python -I .claude/skills/valider-ticket-simulafoot/cloture.py --selftest
python -I .claude/skills/valider-ticket-simulafoot/cloture.py empreinte --base <REV> <fichiers du ticket>
python -I .claude/skills/valider-ticket-simulafoot/cloture.py decision --ticket <id> --rapport <rapport.md> --qc <VALIDÉ|REFUSÉ|BLOQUÉ> --base <REV> <fichiers> [--reserves-acceptees]
```

## Table de clôture (journalisée sous `<id>/cloture`)

| Expert | QC | Clôture |
|---|---|---|
| APPROVED | VALIDÉ | VALIDÉ |
| APPROVED_WITH_RESERVATIONS + réserves acceptées par le propriétaire | VALIDÉ | VALIDÉ |
| REJECTED | quelconque | REFUSÉ |
| quelconque | REFUSÉ | REFUSÉ |
| INCONCLUSIVE, réserves non acceptées, rapport absent/incomplet/autre ticket/code modifié depuis | VALIDÉ ou BLOQUÉ | BLOQUÉ |
| quelconque | BLOQUÉ ou absent | BLOQUÉ (sauf REFUSÉ ci-dessus) |

## Calculs de l'expert

Aucun MCP d'exécution Python n'est installé (vérifié le 29/10/2026). L'expert n'exécute donc rien : il rend une `DEMANDE DE VÉRIFICATIONS` (hypothèse, formulation, commande d'un script existant ou spécification d'un script, résultat attendu) ; le skill l'exécute, avec une empreinte de tout le dépôt avant et après pour prouver que rien n'a été modifié, et lui renvoie sortie et empreintes. Un script nouveau est écrit par le développeur hors du dépôt. C'est une détection a posteriori, pas un bac à sable : une commande qui écrit dans le dépôt est repérée, pas empêchée.

## Limites

- Le statut écrit dans le fichier ticket n'est protégé par aucun mécanisme : seul le commit l'est (verrou).
- Corrigé le 29/10/2026 : une interruption entre l'entrée QC `VALIDÉ` et la clôture laissait passer un commit ; le verrou exige maintenant la clôture liée (banc, scénarios I1 à I3).
- `FICHIERS` est déclaré par le développeur : un fichier de code omis mais indexé est refusé ; un fichier omis et non indexé échappe toujours à la revue.
- `git commit -a` ou `git commit <chemin>` commitent l'arbre de travail : les fichiers revus restent couverts par l'empreinte, mais d'autres fichiers modifiés peuvent partir dans le commit sans contrôle. Indexer explicitement puis `git commit -m`.
- Un commit lancé depuis un script (`bash x.sh`) n'est pas détecté (limite de `detection-git.ps1`).
- Le champ `reserves_acceptees` et le journal restent modifiables par la même main : une clôture forgée de façon cohérente (rapport, empreinte, QC) passerait. Le verrou détecte l'oubli et l'incohérence, pas la falsification délibérée.
- Le rapport est lu à son chemin dans le scratchpad : si la session change, le rapport n'est plus trouvé et il faut refaire la clôture (refus par défaut).

## Tests d'acceptation du dispositif

Cas synthétiques dans `.scratch/expert-dispositif/tests/` (patchs non appliqués, régénérés contre l'état du 31/10/2026 ; à régénérer si `git apply --check` échoue). Exécutés le 31/10/2026 :

| Cas | Ticket | Patch | Attendu | Obtenu |
|---|---|---|---|---|
| T2 physique | `t2-ticket.md` | `exp(-1/τ)` au lieu de `exp(-dt/τ)` dans `movement.py` | REJECTED | REJECTED (dépendance au pas, ~49 m/s² à 10 Hz, 2 tests cassés, τ validé contourné) |
| T3 tactique | `t3-ticket.md` | recherche d'espace inversée dans `off_ball.py` | REJECTED | REJECTED (appels vers son propre but, critères 1 et 2 violés) |
| T4 esthétique | `t4-ticket.md` | libellé en capitales dans `V2Match.jsx` | APPROVED | APPROVED (une remarque facultative, aucun blocage) |
| T5 | `t5-ticket.md` | tolérance 0,3 → 0,5 m | — | REJECTED à juste titre : tolérance = marge du passeur, 2 tests cassés (cas mal construit pour T5) |
| T5b vérification impossible | `t5b-ticket.md` | tolérance 0,3 → 0,25 m sans mesure | INCONCLUSIVE | INCONCLUSIVE (mesure 20 matchs indispensable) |
| T9 isolation | — | — | aucun outil d'écriture | outils Read, Grep, Glob seulement ; aucun fichier créé |

Les agents ne sont chargés qu'au démarrage d'une session. Dossier minimal : ticket, BASE `HEAD`, fichier, patch, empreinte = sha256 du patch, fichier tests. Ne pas lancer `cloture.py decision` sur ces cas : il journalise.
