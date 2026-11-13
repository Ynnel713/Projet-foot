# 31b: Contrôle orienté

**Découpé du ticket 31 le 13/11/2026** (validé par le propriétaire). Détail : `31-premiere-touche.md`, point 2.

**What to build:** Le premier contact oriente le ballon vers l'espace libre ou vers la passe suivante, ce qui raccourcit le temps avant l'action suivante ; sans orientation, le contrôle reste comme aujourd'hui. S'appuie sur le type de réception (`v2-realisme/07c`) et le cap du corps (`07a`, `07e`).

**Hors de ce ticket :** jeu à une touche (31a), durée de réception selon les notes (31c), effet de l'orientation sur le temps de contrôle (`v2-realisme/07d`).

**Attributs :** First Touch (qualité du contact), Anticipation, Vision (choisir où orienter). Rayons à fixer dans la carte, sans double comptage.

**Blocked by:** 31a.

**Bloque :** 31c, `v2-realisme/07d`.

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Temps machine, non compté : suite complète ; 50 matchs avant/après.

## Acceptance criteria

- [x] Constantes et chiffres réels validés par le propriétaire avant le code : temps de base 2,3 s ; orienté x 0,6 (1,38 s) et corps tourné vers le jeu, côté but, ballon reçu devant lui (règle du 07c) ; non orienté x 1,4 (3,22 s) ; chance d'orienter selon First Touch 25 / 50 / 75 % (11 / 55 / 99) ; moyenne attendue 2,76 / 2,3 / 1,84 s (avant : 2,9 / 2,3 / 1,7 s) ; part réelle des contrôles orientés et durées : non trouvées ; validées le 13/11/2026 (« je valide »)
- [x] Scène contrôlée : le contrôle orienté raccourcit le temps avant l'action suivante de 1,84 s (1,38 contre 3,22 s, `tests/test_v2engine_oriented_control.py`), et tourne le corps (dos au but → de profil, 90°, ballon reçu devant lui)
- [x] En match (50 matchs, graines du banc, avant = 31a) : part des contrôles orientés, temps par possession de joueur, avant et après (`31b-50-synthese.txt`)
- [x] Rayon des attributs conforme à la carte : First Touch reste dans `possession` (déplacé du temps vers la chance d'orienter, pas ajouté) ; `tests/test_v2engine_rayon_attributs.py` inchangé et vert
- [x] Durée réelle relevée (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée (`31b-det1`, `31b-det2` identiques hors temps de calcul) ; suite V2 verte ; V1 inchangée (voir Comments)

## Comments

**13/11/2026, analyse et constantes.** Estimation annoncée : 2 h 15. Deux constats : la rotation résiduelle avant une passe n'est que de 0,11 s en moyenne (le porteur tourne pendant son attente), le gain du contrôle orienté doit donc porter sur l'attente elle-même ; et cette attente dépendait déjà de First Touch (commentaire : « contrôle orienté qui fait gagner du temps »), d'où un risque de double comptage. Proposition : déplacer l'effet de First Touch vers la chance d'orienter, temps de base commun, x 0,6 orienté, x 1,4 non orienté ; Vision et Anticipation hors de ce ticket. Réponse : « je valide ».

**13/11/2026, implémentation.** `possession.oriented_control_probability`, `orients_control` (flux passe), `reception_delay_s(..., oriented=)` : `None` (ballon gagné au tacle, remise en jeu, gardien) donne la moyenne attendue sans tirage ; constantes `RECEPTION_CALM_S`, `ORIENTED_FACTOR`, `UNORIENTED_FACTOR`, `_ORIENTED_POINTS` (remplacent `_RECEPTION_S`). `match` : tirage à toute réception contrôlée ; s'il pense à jouer de première (31a), le tirage est gardé dans `BallState.one_touch` et appliqué s'il contrôle finalement ; `_orient` tourne le cap aussitôt (`reception.open_facing`, ballon reçu devant lui). Trace : `ReceptionEvent.oriented`, `.first_time`. Banc : `contrôles orientés (part des contrôles)`, hors receveurs qui pensent à jouer de première. Le type de réception (07c) reste tracé au contact, avant le contrôle orienté : sa répartition ne montre donc pas l'effet du cap (vérifié en scène). Tests : 5 ajoutés (`tests/test_v2engine_oriented_control.py`) ; adaptés : `tests/test_v2engine_rythme.py` (repères 1,7 / 2,3 / 2,9 s remplacés par les valeurs validées ; orientation fixée dans les deux scènes de réception).

**13/11/2026, mesures (50 matchs, graines du 08f, avant = 31a, `31b-50-synthese.txt`).** Contrôles orientés 58,7 % ; temps par possession de joueur 2,42 → 2,34 s (courbe linéaire contre l'ancienne courbe logistique : moyenne un peu plus courte au-dessus de 55) ; une-deux 1,58 → 2,48 par équipe et par match (le receveur orienté rejoue plus vite) ; troisième homme 37,5 → 40,3 ; retours au passeur 3,4 → 5,9 % ; passes par match 1 115 → 1 135 (repère 890 à 940, à la 22a) ; passes par minute de jeu effectif 14,9 → 15,2 (15 à 17 visés) ; réussite 80,3 → 80,9 % ; pertes de balle 285 → 278 ; tirs par équipe 17,7 → 17,6 ; buts 3,02 → 3,10 ; face-à-face 16,0 → 15,0 ; temps de calcul 118 → 114 s par match. Déterminisme : `31b-det1` et `31b-det2` identiques hors temps de calcul.

**13/11/2026, suite.** 2 913 passés, 0 ignoré, 14 désélectionnés (2 908 + 5 ; `.scratch/v2-collectif/mesures/31b-suite.txt`) ; `CLAUDE.md` mis à jour. V1 inchangée (aucun fichier V1 touché).

**13/11/2026, passage 1.** Expert : APPROVED (facultatifs : A1, cap imposé en un tick sans passer par la vitesse de rotation, à vérifier à l'écran ; A2, indicateur qui exclut les receveurs ayant pensé à jouer de première puis contrôlé, biais faible). QC : REFUSÉ : critère « durée réelle relevée » coché sans durée dans le ticket ni ligne au registre (refus n° 1). Correction : durée ci-dessous et ligne ajoutée à `docs/agents/suivi-estimations.md` ; aucun fichier de code modifié.

**À vérifier à l'écran (propriétaire).** Pivot du corps au contrôle orienté (instantané, jusqu'à 90°) : pas de « claquement » visible du trait d'orientation.

**Durée.** Estimée 2 h 15 (135 min). Réelle environ 45 min, non chronométrée (analyse 10 min, développement 12 min, tests 8 min, intégration et vérifications 15 min), relevée à l'horloge de la session (19:11 → 20:00) moins les attentes machine (série de 50 matchs, déterminisme, suite) et la réponse du propriétaire : − 67 %. Cause : le chemin de réception, le tirage de première et le banc venaient d'être posés au 31a ; le changement se réduit à une loi (chance d'orienter, deux facteurs) et à un pivot du cap ; ticket et tests écrits pendant la série. Temps machine hors total : 50 matchs (environ 29 min), déterminisme 2 x 2 matchs, suite complète (10 min).

**13/11/2026, passage 2 (QC).** QC : VALIDÉ (refus n° 1 corrigé, documentation seule). Expert : APPROVED (passage 1, code inchangé depuis). Clôture : VALIDÉ. Facultatifs A1 et A2 non faits : à vérifier à l'écran (A1).
