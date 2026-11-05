# 03: Temps additionnel

**What to build:** Le match V2 tourne aujourd'hui d'un seul bloc de 90 minutes (`v2engine/match.py` l.402-403) : ni mi-temps, ni temps additionnel. Ajouter :

1. **Une mi-temps** : déplacée au ticket 07 (03/11/2026), non bloqué. Ce ticket part du découpage en deux périodes qu'il pose.
2. **Un temps additionnel** à chaque période, dérivé des arrêts de jeu réels du match : buts, remplacements (ticket 05), remises en jeu et coups de pied arrêtés (v2-attributs-restants/02), gestion du temps de l'équipe qui mène (ticket 02, geste Stops Play). Tirage déterministe (sha256 d'une clé stable).
3. **Fin de période réaliste** : l'arbitre ne siffle pas la fin pendant qu'un corner, un coup franc ou un penalty déjà accordé n'a pas été joué ; l'action qui en découle va à son terme.

La trace expose la minute affichée (`45+N'`, `90+N'`) pour le rendu et la narration.

**Attributs :** aucun (Stamina via la récupération à la pause).

**Blocked by:** 07 (livré le 04/11/2026, `efa65c2`) ; `v2-collectif/29` (ballon mort : touches, sorties de but, corners, engagement ; levé du 02 le 03/11/2026, décision Q14). Les coups de pied arrêtés travaillés (02) et les fautes (`v2-collectif/30`) alimentent ensuite le temps additionnel sans bloquer ce ticket. Le coup d'envoi après but est au ticket 29 ; celui-ci ne traite que le début des périodes. La perte de temps de l'équipe qui mène (Stops Play, ticket 02 de ce chantier) s'y ajoute.

**Status:** livré (05/11/2026), validé expert + QC (3 passages, aucune réserve restante)

## Constantes et critères (04/11/2026, validés par délégation du propriétaire)

**Correction du point 2, d'après la Loi 7 :** les touches, sorties de but, corners et coups francs ordinaires font partie du jeu et ne sont **pas** rattrapés (Collina, FIFA ; directive IFAB 2023 : on rattrape le temps réellement perdu en célébrations, remplacements, blessures, sanctions, VAR, penalties). Le ballon mort de ces remises s'écoule déjà dans l'horloge du moteur (`restart.DEAD_S`), comme dans la réalité. Comptent donc : buts, penalties, et un « fond » pour les causes pas encore jouées par le moteur (blessures, VAR, cartons ; remplacements en 2e période tant que le ticket 05a n'existe pas).

**Tirage :** sha256 d'une clé stable (équipes, période, événements de la période : buts, penalties, fautes, remises en jeu), donc même graine = même temps additionnel, sans consommer le flux `random` du match (les autres tests à graine fixe ne bougent pas).

| Constante | Valeur | Justification |
|---|---|---|
| Temps perdu par but | 60 s | Avant 2023 : 30 s forfaitaires par but (AP, 02/2023) ; la directive 2023 impose la durée réelle, plus longue. Durée réelle moyenne : non trouvé. |
| Temps perdu par penalty | 60 s | Même valeur que `DEAD_S[PENALTY]` (provisoire, ticket 30). |
| Fond 1re période | 60 à 150 s (uniforme) | Blessures, VAR, cartons. Ventilation réelle par cause : non trouvé. |
| Fond 2e période | 180 à 330 s (uniforme) | Idem + remplacements (5 par équipe en 3 fenêtres). Le ticket 05a en retirera la part remplacements quand ils seront joués. |
| Annonce | arrondi à la minute la plus proche | Le 4e arbitre affiche des minutes entières (minimum joué). |
| Fond pour un match court | proportionnel à la durée | Un match de test de 2 min n'a pas 4 min d'arrêts. |
| Coup de pied arrêté accordé à la fin | joué, puis l'action va jusqu'au prochain ballon mort ou changement de possession, 30 s au plus | Loi 7 (penalty) et usage des arbitres (corner, coup franc). |
| Butoir | 3 min après la fin annoncée | Garde contre une chaîne de corners sans fin. |

Attendu : 1re période ≈ 3 min, 2e ≈ 6 min, total ≈ 9 min.

**Données réelles :**
- Ligue 1 : 5,42 min par match en 2022-23 (avant la directive), plus de 8 min en 2025-26 (ligue1.com, 04/03/2026).
- Premier League 2023-24 : 11 min 35 s par match (ESPN). Premier League : durée moyenne du match 101:42 à mi-saison 2023-24 (premierleague.com).
- Ventilation par période : non trouvé de source officielle ; un tableau non sourcé donne pour la Ligue 1 3,3 min puis 7,0 min.

**Critères chiffrés :**
1. Sur 30 matchs : temps additionnel total moyen entre 7 et 10 min ; 1re période entre 2 et 4 min en moyenne ; 2e période entre 4 et 7 min ; 2e plus longue que la 1re dans au moins 80 % des matchs.
2. Chaque but ou penalty de la période ajoute du temps (test unitaire : temps additionnel croissant avec le nombre de buts).
3. Aucune fin de période avec un corner, coup franc ou penalty accordé et non joué (0 sur 30 matchs).
4. Même graine : même temps additionnel et même empreinte de trace.
5. Minute affichée `45+N'` / `90+N'` dans la trace (`display_minute`) et l'écran V2.
6. Suite complète : 2 281 passés au moins (plus les nouveaux tests), 13 désélectionnés, 0 échec ; lint UI 0 erreur.

**Mesures (04/11/2026, 30 matchs complets, graines 20261104 à 20261133, script de diagnostic hors dépôt) :**
- 1re période : 2,73 min en moyenne (critère 2 à 4) ; 2e : 5,40 min (critère 4 à 7) ; total : 8,13 min (critère 7 à 10), de 4 à 13 min ;
- 2e plus longue que la 1re dans 27 matchs sur 30 (90 %, critère 80 %) ;
- 0 fin de période avec un corner, un coup franc ou un penalty en attente ;
- 2,63 buts par match sur l'échantillon (mesure finale, après les corrections des passages 1 et 2 de l'expert ; mesures intermédiaires : 2,90 / 5,50 / 8,40 min puis 2,73 / 5,80 / 8,53 min). Durée de calcul d'un match : environ 70 s seul.

**Implémentation :** `v2engine/added_time.py` (`added_minutes`, `display_minute`, `played_minute` : la fatigue suit le temps de jeu et non l'horloge du moteur, constantes) ; `v2engine/match.py` (boucle par période, `LateSetPiece`) ; `MatchTrace.added_minutes` et `MatchTrace.display_minute` ; API `added_minutes` ; écran V2 : minute `45+N'` avec l'annonce `(+N)`, frise du momentum allongée au-delà de 90 min. Tests : `tests/test_v2engine_temps_additionnel.py` (9).

**Effet attendu ailleurs :** environ 9 min de jeu en plus par match, soit environ 10 % d'actions, de tirs et de buts en plus. Repris à la calibration (22a, 22c), pas corrigé ici.

**Point de vigilance :** ordre de grandeur réel à sourcer (environ 2-4 min en première période, 5-8 min en seconde depuis 2023, à confirmer). Avec seulement buts et remplacements, on n'atteindrait que 3-5 min par match. Les remises en jeu réduiront aussi le temps de jeu effectif (aujourd'hui 90 min de jeu continu contre environ 55-60 réelles) : à recalibrer dans v2-collectif/22. Prérequis du ticket 04.

- [x] Temps additionnel croissant avec le nombre d'arrêts de jeu ; distribution par période comparée à des données réelles sourcées (ou « non trouvé »), validée par le propriétaire
- [x] Aucune période ne se termine avant l'exécution d'un coup de pied arrêté déjà accordé
- [x] Même graine : même temps additionnel ; deux exécutions donnent la même empreinte de trace
- [x] Minute affichée au format `45+N'` / `90+N'` dans la trace et l'UI V2
- [x] Suite V2 verte ; V1 inchangée

## Comments

- **05/11/2026, clôture** : 3 passages. Passage 1 : expert APPROVED_WITH_RESERVATIONS (A1 : fond identique à chaque rejeu d'une même affiche, clé enrichie des fautes et remises en jeu de la période ; A2 : minute brute dans le panneau « Dernière décision », passée par `clock()`), QC VALIDÉ. Passage 2 : expert APPROVED_WITH_RESERVATIONS (A1 : fatigue lue sur l'horloge brute du moteur, corrigée par `played_minute`), QC VALIDÉ. Passage 3 : expert APPROVED, QC VALIDÉ, clôture VALIDÉ. Réserves corrigées, aucune à accepter.
- Reste à vérifier à l'écran par le propriétaire : `45+N'` / `90+N'` en fin de période, annonce `(+N)`, mi-temps après le temps additionnel de la 1re période, frise du momentum allongée.
- Suivi : ticket 05a (retirer la part remplacements du fond de `BACKGROUND_S`), calibration 22 (environ 10 % de jeu en plus par match).
