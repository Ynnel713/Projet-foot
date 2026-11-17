# 04a: Decisions en défense : presser ou temporiser, tacler ou attendre

**Chantier :** `v2-attributs-contextes` (ADR 0002). **Priorité :** P2. **Catégorie :** attributs.

**Constat (audit du 17/11/2026) :** Decisions est lu par le choix du porteur (`decision.py`), des remises (`restart.py`) et, depuis le ticket `v2-realisme/11h` (livré le 16/11/2026, fusionné le 17/11/2026), par le renoncement au tacle hors urgence selon l'angle d'approche (`duel.tackle_attempt_factor`). Le choix du presseur (engager ou attendre le soutien) et le tacle de face (tacler ou temporiser) n'en dépendent pas.

**What to build:** contexte « choix défensif » : le défenseur au contact choisit entre tacler et temporiser, et le presseur entre engager et attendre le soutien, selon Decisions (bon choix plus probable), avec Aggression qui garde la fréquence de base des tentatives (pas de double comptage). Le facteur du 11h (tacle par derrière ou de côté hors urgence) reste tel quel ; ce ticket l'étend au tacle de face et au presseur dans le même contexte « choix défensif », sans compter deux fois le renoncement du 11h. À articuler avec `21c` (faute tactique, découpé en 21c1 à 21c7).

**Attributs :** Decisions, Aggression (fréquence, inchangée), Anticipation (poids à proposer).

**Blocked by:** 01, 02.

**What to build (réduit le 17/11/2026, décision du propriétaire « Réduit : choix défensif », après le constat ci-dessous) :** contexte « choix défensif » (Decisions 0,7, Anticipation 0,3) dans `duel.tackle_attempt_factor` : le discernement du 11h y migre (identique à notes égales) et s'étend au tacle plongé, lancé à plus de 2 m/s hors urgence (11 → 1,3, 55 → 1,0, 99 → 0,5). Le presseur qui attend le soutien est abandonné. Decisions et Anticipation sortent de la liste de transition. Le propriétaire a d'abord demandé un seul ticket (« Lance le en un seul ticket », découpage en 04a-m, 04a1, 04a2 refusé) : estimation annoncée 3 h 30, ramenée à 2 h 15 avec la réduction.

**Status:** livré (17/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible. Hypothèses : le déclenchement du tacle (`match.should_attempt_tackle`) et le presseur (`defense.py`) acceptent une probabilité de plus sans refonte. Au-dessus du seuil de 2 h de peu : découpage examiné avant le code.
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après ; banc de profils de l'attribut (`scripts/measure_v2.py --profil`).

## Acceptance criteria

- [x] Contexte, poids et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (choix « Réduit : choix défensif », 17/11/2026, chiffres réels non trouvés)
- [x] Contexte déclaré dans le registre et documenté dans la carte ; Decisions et Anticipation retirés de la liste de transition du test de rayon
- [x] Scène reproductible : 99 contre 11 sur l'attribut, effet probabiliste, jamais binaire (`tests/test_v2engine_choix_defensif.py` : 98 tentatives de plongé à 99 contre 248 à 11 sur la même exposition)
- [x] 50 matchs avant/après sur l'indicateur visé ; profils 99 / 11 dans le plafond d'écart de la carte ; pas de double comptage (R1) (voir Mesures)
- [x] Déterminisme à graine fixée ; suite complète passée, compte comparé à l'attendu de `CLAUDE.md` (voir Mesures)
- [x] Durée réelle relevée et comparée à l'estimation (voir Durée réelle)

## Constat (17/11/2026, avant tout code moteur)

Script de constat hors dépôt (4 matchs de 90 min, graines 20261118 à 20261121), tacles relevés par angle d'approche, urgence, vitesse de rapprochement et soutien du tacleur ; tir de l'équipe du porteur dans les 10 s (puis 15 s) après le tacle. Par match :

| Classe | Exposition (s) | Tentatives | Gagnés | Fautes | Ratés | Tir après un raté |
|---|---|---|---|---|---|---|
| de face, hors urgence | 469 | 18,8 | 29 % | 32 % | 39 % | 0 % (10 s), 7 % (15 s) |
| de côté, hors urgence | 637 | 19,5 | 17 % | 51 % | 32 % | 12 % (10 s) |
| par derrière, hors urgence | 196 | 3,2 | 15 % | 69 % | 15 % | 0 % |
| en urgence (tous angles) | 39 | 1,3 | — | — | — | — |
| rapprochement ≤ 2 m/s | 1 156 | 35,0 | 23 % | 42 % | 35 % | 10 % |
| rapprochement 2 à 4 m/s | 115 | 4,2 | 24 % | 47 % | 29 % | 20 % |
| rapprochement > 4 m/s | 31 | 2,2 | 11 % | 67 % | 22 % | 0 % |

Lecture : un tacle raté n'est presque jamais suivi d'un tir ; le soutien du tacleur (coéquipier à moins de 5 m, couverture entre le porteur et le but) ne change pas l'issue. Le choix « presser ou attendre le soutien » n'a donc pas d'enjeu mesurable aujourd'hui : abandonné. Le seul levier est le tacle plongé (rapprochement au-delà de 2 m/s, environ 6 par match, 2 sur 3 en faute, la faute coûtant un coup franc). Les fautes sont à 16,7 par match (ticket `v2-realisme/11s`), sous le repère de 21 à 26 du `21c` : la courbe est neutre à 55 pour ne pas les faire baisser en moyenne.

## Constantes validées (17/11/2026, choix « Réduit : choix défensif »)

- Contexte « choix défensif » (`CHOIX_DEFENSIF`, temps décision) : Decisions 0,7 ; Anticipation 0,3. Effet : `duel.tackle_attempt_factor`.
- Renoncement par derrière et de côté (11h) : courbes inchangées (11 → 0,40, 55 → 0,15, 99 → 0,05), lues sur la note du contexte.
- Tacle plongé (`TACKLE_DIVE_FACTOR_BY_CHOICE`), rapprochement au-delà de `TACKLE_CLOSING_FREE_MPS` (2 m/s, ticket 11d), hors urgence : 11 → 1,3, 55 → 1,0, 99 → 0,5, interpolé.
- Inchangés : la prudence de surface (`box_prudence`, Decisions seul, commune à toutes les fautes, 21c1) ; Aggression, seule fréquence de base (R1).
- Chiffres réels : non trouvés.

## Réalisation (17/11/2026)

- `v2engine/contextes.py` : contexte déclaré. `v2engine/duel.py` : `tackle_attempt_factor` lit le contexte ; facteur du plongé.
- `docs/CARTE_ATTRIBUTS_V2.md` : ligne du contexte ; cellules Decisions et Anticipation ; cellule Work Rate précisée (amélioration facultative A1 de l'expert au ticket 03).
- Tests : `tests/test_v2engine_choix_defensif.py` (4 tests) ; `test_v2engine_contextes.py` (registre) ; `test_v2engine_rayon_attributs.py` (Decisions et Anticipation sortis de la transition) ; `test_v2engine_tacle_dernier_recours.py` et `test_v2engine_prudence_surface.py` : Anticipation alignée sur Decisions dans les joueurs de test (sans cela, Anticipation par défaut à 60 décalait la note du contexte), valeurs attendues inchangées.
- Ticket 08 : Anticipation retirée de son périmètre (16 attributs).

## Mesures (17/11/2026)

50 matchs avant (`ebec5ba`, série « après » du ticket 03 sur un moteur identique) et après (graines 0 à 49, `scripts/measure_v2.py 25 --debut 0` et `--debut 25`), par match :

| Indicateur | Avant | Après | Écart |
|---|---|---|---|
| tacles | 41,52 | 40,96 | −0,56 |
| fautes | 20,52 | 19,90 | −0,62 |
| coups francs | 15,40 | 15,08 | −0,32 |
| penaltys | 0,04 | 0,04 | 0 |
| fautes inconsidérées (part) | 0,101 | 0,104 | +0,003 |
| buts | 5,06 | 5,16 | +0,10 |
| tirs par équipe | 20,00 | 20,18 | +0,18 |
| conversion des tirs | 0,126 | 0,128 | +0,001 |

Lecture : effet moyen faible, comme attendu d'une courbe neutre à 55 sur environ 6 plongés par match ; les écarts restent dans le bruit d'une série de 50 matchs. Le repère de fautes du `21c` (21 à 26) n'est pas visé ici.

Banc de profils Decisions (`--profil Decisions`, 10 matchs avant et après ; le banc ne force que Decisions, Anticipation garde la note de la fiche, la note du contexte ne bouge donc que de 0,7 de l'écart) : fautes haut − bas −6,1 [−9,9 ; −2,3] avant, −2,8 [−7,3 ; +1,7] après ; tacles gagnés −2,2 avant, −2,3 après ; écart au meilleur choix −0,46 avant et après. Le sens reste le même (le profil haut fait moins de fautes) ; l'écart se resserre parce que le renoncement par derrière et de côté du 11h ne suit plus que 0,7 de l'écart de Decisions, ce que le plongé ne compense pas sur 10 matchs. Pas de double comptage : Aggression reste la seule fréquence de base, la prudence de surface lit toujours Decisions seul (effet distinct, commun à toutes les fautes).

Déterminisme : deux exécutions de traces de 20 min à graine fixée (20260923 et 20261107), empreintes identiques (`11555eaad3e01c9d`, `140cad85bbe297b5`) ; ce sont aussi celles du ticket 03 : sur ces deux traces courtes, aucun tirage du flux DUEL ne change d'issue (l'effet n'apparaît qu'en série, voir ci-dessus).

## Durée réelle

| Poste | Estimé | Réel |
|---|---|---|
| Analyse (constat compris) | 30 min | 15 min |
| Développement | 45 min | 15 min |
| Tests | 35 min | 10 min |
| Intégration et vérifications | 25 min | 10 min |
| **Total** | **2 h 15** | **50 min** |

Écart : − 63 %. Cause : estimation faite sur le périmètre réduit mais avec la confiance faible du ticket d'origine ; le changement tient dans une fonction (`tackle_attempt_factor`) et un contexte, le constat réutilise le script du 03, et la série « avant » de 50 matchs est celle du 03 (moteur identique) ; expert et QC au premier passage. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée. Temps machine hors total : constat de 4 matchs, deux lots de 25 matchs, deux bancs de profils Decisions de 10 matchs, deux paires d'empreintes, suite complète (13 min 05).

## Comments

- 17/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture journalisée VALIDÉ. Aucune anomalie bloquante. Améliorations facultatives de l'expert : A1 commentaire « neutre à 55 » exact seulement si la note moyenne du contexte vaut 55 (baisse de 0,6 faute par match cohérente avec une moyenne vers 63), à reprendre au réglage du `21c` ; A2 marche d'escalier du facteur au seuil de 2 m/s, rampe seulement si un effet visible est mesuré ; A3 le geste préféré « Dives Into Tackles » (`v2-attributs-restants/09a`) devra moduler `TACKLE_DIVE_FACTOR_BY_CHOICE` et non ajouter un facteur (R1) ; A4 banc forçant Decisions et Anticipation ensemble, et écart 16,7 (11s) contre 20,52 fautes par match à préciser (périmètre de comptage probable). Réserves non bloquantes du QC : le test de plus (3 390 contre 3 389) est l'instance paramétrée du registre (`test_v2engine_contextes.py`), expliquée par l'expert ; grosses occasions 118,4 → 124,7 par match non visées, dans le bruit d'un indicateur à forte variance.
