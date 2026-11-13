# 07d: Temps de contrôle et enchaînement selon l'orientation

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (dos au jeu, il faut se retourner avant d'attaquer). **Catégorie :** exécution.

**Constat vérifié :** `possession.reception_delay_s` (`possession.py:170`) ne dépend que de First Touch et de la pression.

**What to build:** Le temps avant la première décision augmente pour une réception dos au jeu (rotation nécessaire) et baisse de profil ; dos au jeu, les options vers l'avant ne sont accessibles qu'après la rotation (le porteur peut jouer en remise avant).

**Attributs :** aucun

**Lien avec l'existant :** à coordonner avec `v2-collectif/31` (contrôle orienté, à faire) : 31 règle la durée par First Touch et Technique, ce ticket ajoute l'orientation, sans toucher à 31.

**Blocked by:** 07c (Réception de face, de profil ou dos au jeu); `v2-collectif/31`.

**Bloque :** 07g.

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : 31 livré avant ; sinon dépendance à rediscuter.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même joueur, même ballon : dos au jeu plus lent que de profil
- **Statistiques (séries de matchs) :** 50 matchs : temps de possession individuelle par type de réception

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : contrôle non orienté x 0,85 de profil, x 0,95 de face, x 1,35 dos au jeu (type au contact, 07c) ; contrôle orienté (31b) inchangé ; facteur moyen pondéré 1,01 sur la répartition mesurée ; chiffres réels non trouvés ; validées le 13/11/2026 (« Ok »)
- [x] Effet de l'orientation mesuré en scène : même joueur, même ballon, dos au jeu plus lent que de profil (4,35 contre 2,74 s, non orienté) ; ballon dans le dos d'un joueur arrêté compté dos au jeu, joueur lancé épargné (condition A1 du 07c) (`tests/test_v2engine_reception_orientation.py`)
- [x] Temps de possession individuelle rapporté (repère 2-3 s) : 2,43 s après correction, et par type de réception, contrôle à l'aveugle compris (`07d-50b-synthese.txt`, indicateur n° 27)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`07d-det1`, `07d-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (voir Comments)

## Comments

**12/11/2026, repris du 07c (réserves acceptées par délégation du propriétaire).**
- A1 (condition) : avant de lire le type de réception, le combiner avec la direction d'arrivée du ballon (`ReceptionEvent.ball_facing_deg`, `match._ball_facing_deg`) : un ballon qui arrive à plus de 90° du cap est un contrôle à l'aveugle ou dos au jeu, pas « de face ». Test : cap vers le but, ballon de derrière, joueur non visé, type ou pénalité attendus explicitement.
- A2 : angle d'arrivée d'un ballon arrêté (0° aujourd'hui) : prendre l'angle entre le cap et la position du ballon.
- A3 : hystérésis autour de `movement.FACING_RUN_SPEED_MPS` (réserve A1 du 07a), à faire dès que le cap agit sur le jeu.
- Mesure : la part de dos au jeu de l'avant-centre (0,4 % au 07c) reste irréaliste tant que le marqueur collé n'empêche pas de se tourner (04i, 08c).


**13/11/2026, repris du `v2-collectif/31` (31a à 31c livrés).** Le temps de réception vaut désormais 2,3 s x 0,6 (contrôle orienté) ou x 1,4 (non orienté), la chance d'orienter dépendant de First Touch, de la vitesse du ballon et de Technique (`possession.oriented_control_probability`, `reception_delay_s(..., oriented=)`) ; le contrôle orienté tourne aussitôt le corps vers le jeu (`match._orient`). Ici : ajouter l'effet de l'orientation du corps au moment du contrôle sans repasser par Technique ni par la vitesse du ballon (remarque de l'expert au 31c), et recontrôler les buts par match (3,48 après le 31c, environ 0,9 erreur type au-dessus du 31b).

**13/11/2026, lancement et constantes.** Répartition des contrôles mesurée sur 4 matchs (2 504, jeu de première exclu, type au contact) : non orientés 60,4 % de face, 19,0 % de profil, 20,6 % dos au jeu. Déjà couvert : options vers l'avant après la rotation (07e), remise avant (31a). Pour éviter le double comptage signalé au 31c, l'orientation ne joue que sur les contrôles non orientés. Proposition : de profil x 0,85, de face x 0,95, dos au jeu x 1,35 (moyenne pondérée 1,01). Estimation revue : 1 h 15 (1 h 55 d'origine ; chemin de réception posé aux 31a à 31c). Réponse : « Ok ».

**13/11/2026, implémentation.** `possession.RECEPTION_KIND_FACTORS`, `reception_delay_s(..., oriented, kind)` (facteur appliqué au seul contrôle non orienté ; `None` inchangé) ; `match` : type de réception relevé au contact, avant le contrôle orienté, passé au délai et gardé dans `BallState.one_touch` (5e élément) pour le receveur qui pensait jouer de première. Banc : temps de possession individuelle par type de réception, orienté ou non (`Collector.holds`, apparié à la réception par joueur et instant ; indicateur n° 27). Tests : 6 ajoutés (`tests/test_v2engine_reception_orientation.py`) ; adaptés : `tests/test_v2engine_rythme.py` (reçu de face, x 0,95), `tests/test_v2engine_oriented_control.py` (dos au jeu non orienté, x 1,35).

**13/11/2026, mesures (50 matchs, graines du 08f, avant = 31c, `07d-50-synthese.txt`).** Temps par possession de joueur 2,37 → 2,34 s ; par type (après seulement, indicateur nouveau) : de face 2,66 s (non orienté 3,50, orienté 2,01), de profil 2,21 s (2,82 / 1,75), dos au jeu 2,48 s (3,64 / 1,51) ; répartition 61,6 / 19,5 / 18,9 %. Passes par match 1 112 → 1 122 ; passes par minute de jeu effectif 15,0 → 15,1 ; une-deux 2,28 → 2,21 ; **buts 3,48 → 3,86** (tirs par équipe 18,3 → 18,8, face-à-face 15,5 → 16,6, xG neutre 3,63 → 3,81) : environ une erreur type, mais dérive continue depuis le 31b (3,10 → 3,48 → 3,86), au-dessus du repère 2 à 3,5 ; cause non isolée.

**13/11/2026, suite et déterminisme.** 2 923 passés, 0 ignoré, 14 désélectionnés (2 917 + 6 ; `.scratch/v2-realisme/mesures/07d-suite.txt`) ; `CLAUDE.md` mis à jour. `07d-det1` et `07d-det2` identiques hors temps de calcul. V1 inchangée (aucun fichier V1 touché).

**Durée (premier passage, remplacée ci-dessous).** Estimée 1 h 55, revue à 1 h 15 (75 min) au lancement. Réelle environ 55 min, non chronométrée (analyse 15 min dont la mesure de la répartition des réceptions, développement 10 min, tests 10 min, intégration et vérifications 20 min dont l'indicateur par type de réception ajouté en cours de série), relevée à l'horloge de la session (21:08 → 22:05) moins les attentes machine et la réponse du propriétaire : − 27 % sur 75 min (− 52 % sur l'estimation d'origine). Temps machine hors total : 4 matchs (répartition), 50 matchs (relancés une fois pour l'indicateur), déterminisme 2 x 2 matchs, suite complète (9 min).

**13/11/2026, passage 1.** Expert : REJECTED. A1 [bloquant] : la condition A1 du 07c, inscrite à ce ticket (combiner le type de réception avec la direction d'arrivée du ballon), n'était ni implémentée ni rediscutée, et le nouveau test figeait le cas visé (de face, ballon dans le dos, x 0,95). A2 [réserve] : dérive des buts non analysée (3,10 → 3,48 → 3,86 depuis le 31b). A3 [facultatif] : ballon arrêté à 0° (A2 du 07c). A4 [facultatif] : appariement de l'indicateur non publié ; commentaire mal indenté. QC non lancé.

**13/11/2026, mesure demandée (4 matchs, 2 024 contrôles non orientés, `blind.py` hors dépôt).** « De face » avec le ballon à plus de 90° du cap, joueur non lancé : 15,7 % des contrôles non orientés ; même cas lancé : 0,8 % ; « de profil » ballon dans le dos, non lancé : 7,1 % ; ballon arrêté au contrôle : 0 (A3 sans objet).

**13/11/2026, correction (validée par le propriétaire : « Ok avc ta recommandation », option A sans renormaliser).** Ballon reçu à plus de 90° du cap d'un joueur non lancé (sous 19,8 km/h ; classement ponctuel au contact, pas de bande d'hystérésis utile) : contrôle à l'aveugle, compté dos au jeu (x 1,35) quel que soit le type de réception ; aucune constante nouvelle (`reception.BLIND_MIN_DEG` = 90°, seuil existant du 07c). `reception.blind_reception` ; `match` : type qui règle la durée (`timed_kind`), gardé dans `BallState.one_touch` ; trace `ReceptionEvent.blind`, le type tracé reste celui du 07c. Banc : contrôles à l'aveugle (part des non orientés), groupe « à l'aveugle » de l'indicateur n° 27, taux d'appariement (A4), commentaire réindenté. Tests : `test_the_match_applies_the_kind_seen_at_the_touch` ramené aux ballons reçus devant ; ajoutés : ballon dans le dos d'un joueur arrêté, de face et de profil (x 1,35), receveur lancé (x 0,95 gardé), règle `blind_reception` (dos, lancé, devant, 90° pile, ballon arrêté) ; test de la moyenne renommé (moyenne 1,01 sur la répartition géométrique, relevée par le contrôle à l'aveugle).

**13/11/2026, mesures après correction (50 matchs, avant = 31c, `07d-50b-synthese.txt`).** Contrôles à l'aveugle 22,6 % des non orientés ; temps par possession de joueur 2,37 → 2,43 s (réel 2,49 s) ; par type : à l'aveugle 2,97 s (non orienté 4,36, orienté 1,96), de face 2,76 s, de profil 2,39 s, dos au jeu 2,45 s ; appariement 100 % ; passes par match 1 112 → 1 091 ; passes par minute de jeu effectif 15,0 → 14,7 ; une-deux 2,28 → 1,96 ; **buts 3,48 → 3,62** (3,86 avant la correction : elle les fait baisser, comme attendu ; environ 0,4 erreur type au-dessus du 31c) ; tirs par équipe 18,3 → 18,6 ; face-à-face 15,5 → 16,0. A2 (dérive des buts) rattachée au 07g.

**13/11/2026, suite et déterminisme après correction.** 2 927 passés, 0 ignoré, 14 désélectionnés (2 917 + 10 ; `.scratch/v2-realisme/mesures/07d-suite.txt`) ; `CLAUDE.md` mis à jour. `07d-det1` et `07d-det2` identiques hors temps de calcul.

**Durée.** Estimée 1 h 55, revue à 1 h 15 au lancement, puis à 1 h 20 annoncées pour la correction (total 1 h 40, 100 min). Réelle environ 1 h 45 (105 min), non chronométrée : premier passage 55 min (analyse 15, développement 10, tests 10, intégration 20), correction 50 min (mesure du cas à l'aveugle 15, développement 10, tests 10, intégration et vérifications 15), relevée à l'horloge de la session (21:08 → 22:05, puis 22:15 → 23:10) moins les attentes machine et les réponses du propriétaire : + 5 % sur 100 min (+ 40 % sur les 75 min du lancement). Cause : condition A1 du 07c inscrite au ticket et ratée à l'analyse, d'où rejet de l'expert, mesure, correction et nouvelle série. Temps machine hors total : 4 + 4 matchs (répartitions), 3 séries de 50 matchs (dont une relancée pour l'indicateur), déterminisme 2 x 2 matchs (deux fois), deux suites complètes.

**13/11/2026, passage 2.** Expert : APPROVED (condition A1 du 07c levée ; facultatifs : A1, critère « lancé » par la seule vitesse et non par `facing_run`, à mesurer au 07g ; A2, assertion inutile dans un test et recoupement du groupe « à l'aveugle » dans l'indicateur n° 27). QC : VALIDÉ (réserve : cases du ticket avec des chiffres d'avant la correction, harmonisées ici : 2,43 s, condition A1). Clôture : VALIDÉ.
