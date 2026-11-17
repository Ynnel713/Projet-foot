# 03: Work Rate offensif : soutien et repli après la perte

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** attributs.

**Constat (audit du 17/11/2026, corrigé le 17/11/2026 au lancement du ticket) :** Work Rate n'a aucun contexte du registre, mais il n'est pas lu que par le pressing : il règle aussi le replacement sans ballon et le trot en possession (`defense.replacement_intensity`, ticket `v2-realisme/12d`) et le repli après la perte (`cerveau`, rôle REPLI, à `press_intensity`, ticket `v2-collectif/10`). Le ticket `v2-realisme/12d` l'a écarté des appels (« seul Off the Ball »).

**What to build (réduit le 17/11/2026) :** le repli après la perte (rôle REPLI de `cerveau.py`, aujourd'hui à `defense.press_intensity`, Work Rate seul) devient le contexte « repli après la perte » du registre, Work Rate + Teamwork. Le soutien offensif est abandonné : il ajouterait des tirs à un écart de buts déjà fort (ticket `03m`).

**What to build (d'origine, avant réduction) :** Work Rate entre dans deux contextes nouveaux : « soutien offensif » (volume des courses pour se proposer au porteur, avec Off the Ball pour le moment et le choix de l'espace) et « repli après la perte » (intensité et délai du retour derrière le ballon, avec Teamwork). L'intensité de l'appel lui-même reste à Off the Ball (pas de double comptage avec 12d).

**Attributs :** Work Rate, Off the Ball, Teamwork (poids à proposer).

**Blocked by:** 01, 02.

**Status:** livré (17/11/2026), validé expert + QC (périmètre réduit le 17/11/2026, décision du propriétaire : « Accepter, 03 réduit », après le ticket `03m`)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 35 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible. Hypothèses : les rôles soutien et replacement du cerveau (`cerveau.py`) portent déjà une intensité. Au-dessus du seuil de 2 h : découpage à examiner (soutien, puis repli).
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après ; banc de profils de l'attribut (`scripts/measure_v2.py --profil`).

## Acceptance criteria

- [x] Contexte, poids et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (« je valide », 17/11/2026)
- [x] Contexte déclaré dans le registre et documenté dans la carte ; entrée de la liste de transition : Work Rate n'a qu'un contexte (soutien abandonné), il y reste, rattaché au ticket 08 (second contexte sans effet sur les buts, décision du 03m)
- [x] Scène reproductible : Teamwork 99 contre 11 à Work Rate égal (`tests/test_v2engine_repli_contexte.py`) ; effet continu (intensité), jamais binaire
- [x] 50 matchs avant/après sur l'indicateur visé ; profils 99 / 11 dans le plafond d'écart de la carte ; pas de double comptage (R1)
- [x] Déterminisme à graine fixée ; suite complète passée, compte comparé à l'attendu de `CLAUDE.md`
- [x] Durée réelle relevée et comparée à l'estimation

## Constat au lancement (17/11/2026, avant tout code)

Banc de profils `scripts/measure_v2.py 10 --profil "Work Rate"` (équipe à 99 contre équipe à 11) : km par joueur 12,75 contre 11,46 (+ 11 %) ; course intense 1 197 contre 676 m (+ 77 %) ; vitesse de repli à 1,5 s 2,03 contre 1,39 m/s (+ 46 %) ; appels par joueur 43,9 contre 34,3 (+ 28 %, effet indirect) ; temps de pressing 1 046 contre 963 s ; écart de tirs + 11,6 par match et de buts + 2,4 par match (4,5 contre 2,1, IC 95 % de 0,5 à 4,3), significatifs. Repère réel : à poste égal, la distance à haute intensité varie nettement d'un joueur à l'autre (FIFA, Coupe du monde 2022, https://www.fifatrainingcentre.com/en/fwc2022/physical-analysis/what-distances-did-various-positions-cover.php ; Bradley et al. 2009, https://sure.sunderland.ac.uk/id/eprint/3478/) ; lien entre volume d'effort et écart de buts : non trouvé.

Conclusion : Work Rate a déjà un rayon large (par lectures directes) et un effet fort sur le résultat. Brancher le soutien offensif et un repli plus intense augmenterait l'écart de buts. Décision du propriétaire : ne rien brancher, mesurer d'abord le plafond d'écart (ticket `03m`) ; Work Rate reste dans la liste de transition.

Durée passée sur ce ticket avant mise en attente : environ 30 min (analyse et constat). Temps machine : banc de profils de 10 matchs.

## Constantes validées (17/11/2026, « je valide »)

Contexte « repli après la perte » (`REPLI_APRES_LA_PERTE`, temps décision) : Work Rate 0,7 ; Teamwork 0,3. Effet `defense.retreat_intensity` : la courbe du presseur (`_PRESS_INTENSITY`, 11 → 55 %, 55 → 80 %, 99 → 100 % de la vitesse max) appliquée à la note du contexte. Chiffre réel : non trouvé. Le presseur garde Work Rate seul (`press_intensity`), le replacement (`replacement_intensity`, 12d) aussi : pas de double comptage.

## Réalisation (17/11/2026)

- `v2engine/contextes.py` : contexte déclaré ; `v2engine/defense.py` : `retreat_intensity` ; `v2engine/cerveau.py` : le rôle REPLI lit `retreat_intensity` au lieu de `press_intensity`.
- `docs/CARTE_ATTRIBUTS_V2.md` : ligne du contexte, cellules Work Rate et Teamwork.
- Tests : `tests/test_v2engine_repli_contexte.py` (3 tests : notes égales = courbe d'avant, profil mêlé 99 / 11 = note 72,6 ; Teamwork accélère le repli à Work Rate égal, pressing inchangé ; scène du cerveau, intensité REPLI plus haute à Teamwork 99 qu'à 11) ; `test_v2engine_contextes.py`, `test_v2engine_transition_defensive.py` adaptés ; `test_v2engine_rayon_attributs.py` : entrée Work Rate rattachée au ticket 08.

## Mesures (17/11/2026)

Série de 50 matchs (`scripts/measure_v2.py 25 --debut 0` et `--debut 25`), avant (`654f590`) puis après :

| Indicateur | Avant | Après | Écart |
|---|---|---|---|
| repli : vitesse des joueurs devant le ballon à 1,5 s (m/s) | 2,051 | 2,058 | + 0,007 |
| repli : temps pour reformer le bloc (s) | 3,10 | 3,04 | − 0,06 |
| buts par match | 4,54 | 5,06 | + 0,52 |
| tirs par équipe | 19,63 | 20,00 | + 0,37 |
| xG neutre par match | 4,62 | 4,67 | + 0,05 |
| xG après frappe par match | 4,64 | 5,14 | + 0,51 |
| pertes de balle par match | 256,6 | 258,0 | + 1,4 |
| pertes en transition par match | 40,4 | 38,7 | − 1,7 |

Lecture : en moyenne, la note du repli bouge peu (Teamwork − Work Rate dans la base : moyenne − 1,5, écart-type 9,6, soit 2,9 points de note), d'où une vitesse de repli inchangée. L'écart de buts (+ 0,52) est dans le bruit : les deux lots « avant » diffèrent eux-mêmes de 0,52 (4,80 et 4,28), environ 1,2 erreur type sur 50 matchs ; les occasions créées sont inchangées (xG neutre + 0,05), l'écart vient de l'exécution des frappes (xG après frappe), tirage indépendant du repli.

Banc de profils Teamwork (`--profil Teamwork`, 10 matchs) : vitesse de repli à 1,5 s, haut contre bas, 1,99 contre 2,38 m/s avant, 2,07 contre 2,08 après (Teamwork par ses autres effets garde des joueurs placés et moins pressés de revenir ; le contexte rattrape 0,38 m/s de l'écart) ; tirs, buts et interceptions sans écart significatif avant comme après (buts sur tir : − 0,3 avant, + 0,3 après, IC 95 % de − 1,4 à 2,0). Plafond d'écart respecté. Work Rate : son poids passe de 1 à 0,7 dans le seul repli, ce qui ne peut que réduire l'écart 99 / 11 mesuré au 03m (+ 1,73 but).

Déterminisme : deux exécutions de deux matchs de 20 min à graine fixée, empreintes complètes identiques (`11555eaad3e01c9d`, `140cad85bbe297b5`).

## Durée réelle

Environ 1 h 50 de travail effectif (30 min de constat avant la mise en attente, puis 1 h 20 : code 25 min, tests 20 min, mesures et documentation 35 min), contre 2 h 30 estimées pour le périmètre d'origine : − 27 %, sous le seuil de 30 % ; le soutien offensif abandonné explique l'écart. Temps machine non compté : séries de 50 matchs avant et après, bancs de profils Teamwork, suite complète.

## Comments

- 17/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Aucune anomalie bloquante. Amélioration facultative A1 de l'expert (documentaire) : la cellule Work Rate de la carte cite encore le repli du ticket 10 « même courbe d'intensité » avant la mention du contexte, à préciser. Réserves QC non bloquantes : écart de buts + 0,52 attribué au bruit ; fichier du ticket à indexer au commit. À surveiller (expert) : niveau de buts (environ 5 par match) au-dessus de la fourchette réelle, hors de ce ticket.
