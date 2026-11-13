# 31c: Durée de réception selon First Touch, Technique, pression et vitesse du ballon

**Découpé du ticket 31 le 13/11/2026** (validé par le propriétaire). Détail : `31-premiere-touche.md`, point 3.

**What to build:** La durée de réception (`possession.reception_delay_s`) dépend déjà de First Touch et de la pression ; elle dépendra aussi de Technique et de la vitesse du ballon reçu, au lieu d'une plage commune.

**Hors de ce ticket :** effet de l'orientation du corps sur le temps de contrôle (`v2-realisme/07d`, qui s'y ajoute sans double comptage).

**Attributs :** First Touch, Technique. Rayons à fixer dans la carte, sans double comptage.

**Blocked by:** 31b.

**Bloque :** `v2-realisme/07d`.

**Status:** livré (13/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Temps machine, non compté : suite complète ; 50 matchs avant/après.

## Acceptance criteria

- [x] Constantes et chiffres réels validés par le propriétaire avant le code : la vitesse du ballon et Technique agissent par la chance d'orienter le contrôle (31b) ; dureté (vitesse − 6) / (30 − 6) bornée à [0, 1] (constantes existantes) ; Technique compense 0,2 / 0,5 / 0,8 de la gêne (11 / 55 / 99, non trouvée) ; validées le 13/11/2026 (« Oui »)
- [x] Scène contrôlée : ballon plus rapide, réception plus longue (temps moyen croissant de 6 à 30 m/s) ; Technique élevée, réception plus courte (à 24 m/s : 99 < 55 < 11) ; exemple validé à 18 m/s (`tests/test_v2engine_hard_ball.py`)
- [x] En match (50 matchs, avant = 31b) : temps par possession de joueur et rythme (passes par minute de jeu effectif) avant et après (`31c-50-synthese.txt`)
- [x] Rayon des attributs conforme à la carte : First Touch et Technique dans `possession` (déjà permis) ; cumul déclaré (A17) ; `tests/test_v2engine_rayon_attributs.py` vert
- [x] Durée réelle relevée (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée (voir Comments)

## Comments

**13/11/2026, lancement et constantes.** Estimation annoncée : 1 h 30, confiance moyenne. Constat : la vitesse du ballon ne jouait que sur la réussite du contrôle, et depuis le 31b le temps ne dépend que de l'orientation ; proposition : passer par la chance d'orienter (ballon dur moins souvent orienté, Technique en compense une part), effet attendu faible en match (passes dosées vers 6 m/s). Réponse : « Oui ». Erreur d'arrondi dans la proposition : temps moyens à 18 m/s annoncés 2,65 / 2,53 / 2,38 s pour 2,668 / 2,53 / 2,392 s exacts (même loi), corrigée dans le test.

**13/11/2026, implémentation.** `possession.hard_ball_share`, `hard_ball_technique_share`, `oriented_control_probability(player, ball_velocity)`, `orients_control(player, ball_velocity)` ; `match` : tirage avec la vitesse du ballon reçu ; ballon gagné hors passe (`reception_delay_s(..., None)`) : moyenne sans vitesse de ballon. Trace : `ReceptionEvent.ball_speed_mps`. Banc : contrôles de ballon dur (plus de 12 m/s, seuil de mesure seule) et leur part orientée. Tests : 4 ajoutés (`tests/test_v2engine_hard_ball.py`) ; adaptés : substituts de `orients_control` à deux arguments (`tests/test_v2engine_rythme.py`, `tests/test_v2engine_oriented_control.py`).

**13/11/2026, mesures (50 matchs, graines du 08f, avant = 31b, `31c-50-synthese.txt`).** Contrôles de ballon dur 11,4 % des contrôles, orientés à 49,3 % ; contrôles orientés 58,7 → 55,9 % ; temps par possession de joueur 2,34 → 2,37 s ; passes par match 1 135 → 1 112 ; passes par minute de jeu effectif 15,2 → 15,0 ; une-deux 2,48 → 2,28 ; troisième homme 40,3 → 39,2 ; tirs par équipe 17,6 → 18,3 ; buts 3,10 → 3,48 (environ un écart-type de la différence, à surveiller) ; xG neutre 3,43 → 3,63 ; face-à-face 15,0 → 15,5 ; temps de calcul 114 → 102 s par match (bruit de machine).

**13/11/2026, suite et déterminisme.** 2 917 passés, 0 ignoré, 14 désélectionnés (2 913 + 4 ; `.scratch/v2-collectif/mesures/31c-suite.txt`) ; `CLAUDE.md` mis à jour. `31c-det1` et `31c-det2` identiques hors temps de calcul. V1 inchangée (aucun fichier V1 touché).

**Durée.** Estimée 1 h 30 (90 min). Réelle environ 45 min, non chronométrée (analyse 10 min, développement 12 min, tests 10 min, intégration et vérifications 13 min), relevée à l'horloge de la session (20:12 → 21:05) moins les attentes machine (série de 50 matchs, déterminisme, suite) et la réponse du propriétaire : − 50 %. Cause : même cause qu'au 31b, la réception et le banc venaient d'être posés au 31a et au 31b ; la loi passe par la chance d'orienter existante. Temps machine hors total : 50 matchs (environ 29 min), déterminisme 2 x 2 matchs, suite complète (9 min).

**13/11/2026, passage 1.** Expert : APPROVED, aucune anomalie (à surveiller : buts 3,48 par match, environ 0,9 erreur type, à recontrôler à la prochaine série ; au 07d, combiner l'orientation du corps sans repasser par Technique ni la vitesse du ballon). QC : VALIDÉ. Clôture : VALIDÉ. Ticket chapeau 31 entièrement livré (31a, 31b, 31c).
