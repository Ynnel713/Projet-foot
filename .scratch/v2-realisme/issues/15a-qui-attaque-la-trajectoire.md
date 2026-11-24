# 15a: Qui attaque la trajectoire aérienne

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (seuls les joueurs capables d'arriver au point de chute disputent le ballon). **Catégorie :** décision.

**Constat vérifié :** un ballon aérien ne peut être touché qu'à son point de chute (`ball.aerial_left_m`, ticket 29) ; aucune sélection des joueurs qui l'attaquent.

**What to build:** Pour un ballon aérien, chaque équipe désigne au plus deux joueurs qui vont au point de contact (temps d'arrivée et hauteur atteignable, `v2-hauteur-ballon/03`) ; les autres se placent pour le second ballon.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/01` : sélection.

**Blocked by:** `v2-hauteur-ballon/03`.

**Bloque :** 15b, 15e, 16a, 16f.

**Status:** livré (23/11/2026), validé expert + QC (réserves A1 et A2 acceptées par le propriétaire ; correction de A1 : `15a2`)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : hauteur du ballon disponible.
Temps machine, non compté : suite complète (environ 40 min).

**Estimation révisée avant le code (23/11/2026)** : 2 h 25 (analyse 30, développement 50, tests 35, intégration 30), à cause des indicateurs repris du `v2-attributs-restants/01` ; découpage examiné, décision du propriétaire : un seul ticket. Temps machine : deux séries de 50 matchs, suite complète, rejeu de 2 matchs.

**Constantes** (validées par le propriétaire le 23/11/2026, « Validées telles quelles », chiffres réels non trouvés) : au plus 2 joueurs par équipe ; le second n'y va que s'il arrive au plus 1,0 s après le premier de son équipe ; maintien de 0,3 s pour un désigné ; recherche du point de contact au pas de 0,1 s sur 3 s (valeurs de `occasion.py`). **Écarts en cours de route, confirmés par le propriétaire le 23/11/2026 (« Confirmés, réserve acceptée »)** : (1) horizon prolongé jusqu'au pas qui suit la retombée du ballon, au plus 4 s (`vol.MAX_FLIGHT_S`, déjà validée) : un long ballon vole plus de 3 s, personne n'attendait sous sa chute ; (2) le maintien de 0,3 s s'applique aussi à l'écart du second déjà en route (1,3 s), contre l'instabilité mesurée du second.

**Critères chiffrés** (posés avant le code) : scène du dégagement long (les deux plus aptes de chaque équipe vont au point de contact, les autres non ; un ballon trop haut n'est pas visé là) ; sélection tracée ; 50 matchs appariés avant/après (passes longues réussies, contrôles de la tête, sorties du gardien, possession, tirs, buts ; chaque écart significatif expliqué) ; réserves du `01` (partie du corps au premier contrôle après un centre, part des contrôles de la tête, rapport centres / tirs et buts) ; déterminisme à graine fixée ; suite complète au compte attendu, V1 inchangée.

## Tests

- **Unitaires (scène contrôlée) :** dégagement long : les deux plus aptes de chaque équipe attaquent le ballon, les autres non

**Repris du ticket `v2-attributs-restants/01` (23/11/2026, décisions du propriétaire sur les réserves de l'expert)** : indicateur « partie du corps au premier contact après un centre » (pied, corps, tête) et part des contrôles de la tête avant/après (réserve A1) ; rapport entre le nombre de centres et la variation des tirs et des buts, série de contrôle si l'écart persiste (A2) ; cibles du centre hors du filtre de Vision, actées (« un centreur voit toujours la surface ») et à revoir ici si besoin (A3).

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Sélection tracée
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Résultats (23/11/2026)

- Code : `v2engine/jeu_aerien.py` (constantes ; `is_aerial_ball` : ballon libre en l'air, ni mort ni tir en vol ; `ball_path` : trajectoire freinée avec la hauteur ; `contact_point` : premier point à sa portée, `atteinte.reach_m`, où il arrive à temps, sinon le moins en retard ; `select_attackers` : par équipe, joueurs de champ hors passeur et hors signalés hors-jeu, classés à temps d'abord, puis instant du contact, puis arrivée ; receveur visé toujours retenu ; second dans l'écart) ; `BallState.aerial_attackers` posé à chaque pas par `match.simulate_match` ; `cerveau.interpret` : rôle `BALLON_AERIEN` (« attaquer le ballon », au point de contact), receveur visé au point de contact, plus de chasseur du ballon libre (11g) sur un ballon en l'air ; priorité d'évitement au premier désigné ; trace `AerialRecord` (`MatchTrace.aerial`, à chaque changement). Banc : désignations, part à deux, part du premier à temps, changements en moins de 1 s (dont le premier) ; partie du corps des contrôles et du premier contrôle après un centre (`measure_v2`, `v2_indicators`).
- Scènes (`tests/test_v2engine_jeu_aerien.py`, 12 cas ; `tests/test_v2_indicators_jeu_aerien.py`, 2 cas) : constantes ; dégagement long (h1, h2, a1, a2 désignés, rôles et cibles ; les autres ni désignés ni chasseurs) ; point de contact là où le ballon redescend à sa portée ; second trop tard écarté ; maintien du premier (0,2 s gardé, 0,4 s perdu) ; second déjà en route gardé dans la marge ; receveur toujours retenu, au point de contact ; hors-jeu écarté ; passeur écarté ; ballon au sol, tenu ou tir : rien ; grand sauteur préféré sur un ballon tendu ; trace ; indicateurs.
- Défauts trouvés par la mesure et corrigés avant la série retenue : le passeur était désigné second au départ du ballon (contact à 0 s), puis retiré au pas suivant ; changements rapides 38 % → 25 % des désignations (premier : 12 %). Première série « après » écartée (code modifié depuis).
- Série (50 matchs appariés, `bench_series`, avant : `994d996`), détail `docs/INDICATEURS_V2.md` § 76 : 34,9 désignations par équipe et par match, 69 % à deux, premier à temps 92 % ; contrôles de la tête 0,47 → 1,11 % des contrôles ; premier contrôle après un centre (agrégé) : tête 30 → 52 % (écart apparié + 10,5 points [− 3,0 ; + 24,1], non significatif : 1,3 à 1,5 centre par équipe), pied 62 → 44 % (− 17,0 points, significatif) ; centres réussis 46,8 → 34,4 % (significatif : les défenseurs attaquent les centres), centres par équipe 1,54 → 1,31 (bruit) ; passes longues réussies 69,4 → 67,6 % (bruit) ; ballon libre : épisodes disputés − 16,5 par match et pris par l'adversaire 16,2 → 14,5 % (un ballon en l'air n'a plus de chasseur 11g) ; contacts francs + 19 par match ; buts 4,32 → 4,66, tirs 14,6 → 14,6, possession, passes réussies, sorties du gardien : bruit. 165 indicateurs significatifs sur 2 834 (environ 142 attendus).
- Réserves du `01` : A1 mesurée ci-dessus ; A2 : centres − 0,23 par équipe, tirs − 0,02, part des tirs nés d'un centre 2,05 → 2,19 %, buts + 0,34 : aucun lien mesurable entre la baisse des centres et les tirs ou buts, pas de série de contrôle ; A3 : cibles du centre hors du filtre de Vision gardées (sans objet ici).
- Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes (`5b44fb70…`, `3c206c3d…`).
- Suite complète : 3 642 passés, 0 ignoré, 14 désélectionnés (3 628 + 14 cas) ; V1 non touchée.
- Durée réelle : environ 2 h 40 (analyse 35, développement 45, tests 35, intégration et vérifications 45), + 10 % sur l'estimation révisée de 2 h 25 (+ 33 % sur les 2 h d'origine, écart annoncé avant le code : indicateurs repris du `01`) ; instabilité du second et passeur désigné, trouvés par la mesure, corrigés avec une série refaite. À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : trois séries de 50 matchs (37, 36 et 35 min, la deuxième écartée), deux relevés d'un match, rejeu de 2 matchs, suite complète (16 min).

## Comments

- 23/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte `ce75cb83…`, périmètre incluant à tort le ticket et la carte des attributs, documents hors revue) ; réédité sur le seul code et les tests (empreinte `2d9c524b…`), même verdict. QC VALIDÉ (remarques non bloquantes : pas de scène d'un ballon hors d'atteinte sur tout l'horizon, couvert indirectement ; écarts de constantes à confirmer). Clôture VALIDÉ.
- Réserve A1 (le maintien de 0,3 s ne départage que des joueurs qui touchent au même pas de 0,1 s ; 12 % de changements rapides du premier) : acceptée par le propriétaire, « Accepter, corriger en ticket » ; correction au ticket `15a2`, avant ou avec le `15b`.
- Réserve A2 (horizon jusqu'à la retombée, au plus 4 s ; maintien ajouté à l'écart du second, 1,3 s) : acceptée par le propriétaire, « Confirmés, réserve acceptée » ; documents de suivi commités comme suivi documentaire.
- Facultatifs : A3 (`ball_path` suit la loi continue et ignore la perte au rebond, erreur de l'ordre du mètre, recalculée à chaque pas) ; A4 (lecture parfaite de la trajectoire, désignation immédiate devant la lecture de passe et le marquage : à mesurer au `15f`).

