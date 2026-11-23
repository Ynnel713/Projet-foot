# 02a2: Hauteur du ballon : courbe des tirs

**Découpé du ticket `02a` le 23/11/2026** (décision du propriétaire). Référence de détail : `02a-hauteur-du-ballon-physique.md` point 4.

**What to build:** un tir a une vraie hauteur pendant son vol (`z`, `vz` du `02a1`) : `vz0` est choisi pour que le ballon passe la ligne de but à la hauteur que fixe déjà l'issue du tir (`SHOT_AIM_HEIGHT_M` + pente, `v2-collectif/28b`, `v2-realisme/05a`) : sous 2,44 m pour un tir cadré, au-dessus pour un tir « au-dessus ». L'issue du tir n'est pas changée. Cohérence à examiner entre la hauteur réelle et la hauteur lue par le gardien et le contre (pente linéaire).

**Attributs :** aucun.

**Blocked by:** `02a1`.

**Bloque :** `02b` (tirs à l'écran), `v2-attributs-restants/10b`.

**Status:** livré (23/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 12 min), suite complète (environ 15 min).

**Estimation révisée au lancement (23/11/2026) : 1 h 15** (+ 15 min : ballon remis au sol après un arrêt ou un contre, hauteur du tir tracée à la ligne, au gardien et au contre, mesure de cohérence). Temps machine révisé : deux séries de 50 matchs (environ 35 min chacune, avant et après) et suite complète (environ 17 min).

**Constantes :** celles du `02a1` (validées le 23/11/2026) ; aucune nouvelle.

**Critères chiffrés** (posés avant le code) :
- hauteur réelle à la ligne = hauteur qui fixe l'issue (visée + pente) à 1 mm près (scènes) ; ballon au-dessus du sol de la frappe à la ligne (pas de rebond, donc vitesse horizontale et issue inchangées) ; hauteur nulle ou négative : tir rasant (`z = 0` sur tous les pas) ;
- 50 matchs mêmes graines, avant / après : scores, tirs (minute, tireur, issue, origine) et piste du ballon en 2D identiques sur 50 matchs sur 50 ;
- 50 matchs : buts sous 2,44 m à la ligne, « au-dessus » à 2,44 m ou plus, 100 % ; `z ≥ 0` sur tous les pas, mode tracé « aérien » si et seulement si `z > 2,5 m` ;
- cohérence relevée, sans correction (ticket 03) : hauteur au passage au gardien et au contre ;
- mêmes empreintes complètes (hauteur et mode compris) sur deux exécutions à graine fixée ; suite complète au compte attendu.

## Acceptance criteria

- [x] Tirs de 50 matchs : 100 % des cadrés passent la ligne sous 2,44 m, 100 % des « au-dessus » au-dessus
- [x] Issue des tirs inchangée (mêmes graines)
- [x] `z ≥ 0` sur tous les pas
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [x] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu

## Résultats (23/11/2026)

- Code : `v2engine/vol.py` (`line_crossing_s` : instant de passage sur la ligne avec l'avance pas à pas du moteur, interpolé dans le pas comme le point de sortie ; `shot_launch_vz` : `vz0 = (h + g·t²/2) / t`, 0 pour une hauteur nulle ou négative ou une ligne jamais atteinte) ; `match._lift_shot` au départ d'un tir en vol (hauteur visée + pente sur la ligne, la même que celle qui fixe l'issue) ; ballon remis au sol après un arrêt (`_keeper_save`) ou un contre (`_blocked`), point 6 du `02a1` ; `ShotEvent.line_z_m`, `keeper_z_m`, `block_z_m` (hauteur réelle à la ligne, au gardien, au contre). Penalty (règle provisoire du ticket 30) et tir dévissé : au sol, inchangés. API inchangée.
- Scènes (`tests/test_v2engine_hauteur_tirs.py`, 19 cas) : instant de passage identique à l'avance pas à pas ; hauteur à la ligne exacte, pas de retour au sol avant ; rasant pour une hauteur nulle, négative ou une ligne hors d'atteinte ; tir au-dessus (3,6 m à la ligne, tracé « aérien ») ; tir cadré au but (2,3 m) ; tir rasant (`z = 0` à chaque pas) ; même issue et même trajet au sol, pas à pas, qu'un tir sans hauteur (12 combinaisons hauteur × écart latéral) ; ballon au sol après un arrêt et après un contre.
- Série (50 matchs mêmes graines, avant : `90cbbc9`), détail `docs/INDICATEURS_V2.md` § 72 : scores, tirs (minute, tireur, issue, origine) et piste 2D du ballon identiques sur 50 matchs sur 50 (258 buts). Hauteur à la ligne : 256 buts sous 2,44 m (100 %, médiane 0,22 m, max 2,43 m ; 115 rasants ; + 2 penalties au sol) ; 223 « au-dessus » à 2,44 m ou plus (100 %, médiane 3,81 m, max 13,8 m) ; à côté jusqu'à 18,2 m. Hauteur jamais négative, 0 mode incohérent. Cohérence (non corrigée, ticket 03) : 7 contres sur 348 et 2 arrêts sur 324 sur un ballon au-dessus de 2,5 m ou de la barre.
- Déterminisme : matchs 0 et 1 rejoués, mêmes empreintes complètes, hauteur et mode compris (`43b15b90…`, `3175d14c…`).
- Suite complète : 3 599 passés, 0 ignoré, 14 désélectionnés (attendu 3 580 + 19 cas ajoutés) ; V1 non touchée.
- Durée réelle : environ 1 h 25 (analyse 25, développement 20, tests 15, intégration et vérifications 25), + 13 % sur l'estimation révisée de 1 h 15 (+ 42 % sur la première, 1 h : périmètre élargi annoncé au lancement). À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : deux séries de 50 matchs (33 et 31 min), rejeu de 2 matchs (4 min), suite complète (18 min).

## Comments

- 23/11/2026, passage 1 : expert APPROVED (empreinte `0cd292cd…`), aucune action obligatoire ; facultatifs A1 (contre et gardien ignorent la hauteur réelle : 7 contres au-dessus de 2,5 m, 2 arrêts au-dessus de la barre ; ticket 03, à traiter avant ou avec le `02b`) et A2 (hauteurs extrêmes et vitesse totale jusqu'à environ 36 m/s, loi d'écart sans borne du `35b`, calibration `22c`). QC VALIDÉ (réserves non bloquantes : ordre avance / lecture de la hauteur hors du diff, cohérent sur 479 tirs ; docs § 72 et plan non relus). Clôture VALIDÉ.
