# 15a2: Maintien du premier désigné sur un ballon aérien

**Chantier :** `v2-realisme` (réserve A1 de l'expert au ticket `15a`, 23/11/2026, acceptée par le propriétaire : « Accepter, corriger en ticket »). **Priorité :** P2. **Catégorie :** décision.

**Constat vérifié (15a) :** dans `jeu_aerien.select_attackers`, la clé de tri est `(non receveur, pas à temps, instant du contact arrondi, arrivée − maintien, nom)` : le maintien de 0,3 s (`ATTACKER_HOLD_S`) ne départage que deux joueurs qui touchent le ballon au même pas de 0,1 s. Un coéquipier qui touche un pas plus tôt passe devant le désigné, même avec 0,04 s d'avance à l'arrivée. Mesure (50 matchs, `docs/INDICATEURS_V2.md` § 76) : le premier désigné change en moins de 1 s dans 12 % des désignations.

**What to build:** appliquer le maintien aussi à l'instant du contact du joueur déjà désigné (correctif proposé par l'expert : `round(contact_s − hold, 6)` dans la clé), sans changer le classement par portée hors maintien.

**Attributs :** aucun. **Constantes :** aucune nouvelle (`ATTACKER_HOLD_S` validée au 15a).

**Blocked by:** `15a` (livré). **À faire avant ou avec :** `15b`.

**Status:** livré (24/11/2026), validé expert + QC (réserve A1 acceptée par le propriétaire ; correction : `15a3`)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 5 min |
| Développement | 10 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **50 min** |

Confiance : élevée. Temps machine, non compté : série de 50 matchs appariée (environ 37 min), suite complète (environ 17 min).

**Estimation révisée en cours de route (24/11/2026)** : 1 h 05 (développement + 10 min, tests + 5 min). Le correctif de l'expert seul faisait échouer la scène validée du `15a` (à contact au même instant, un coéquipier qui arrive 0,4 s plus tôt ne remplaçait plus le désigné). **Décision du propriétaire du 24/11/2026 : « Règle double »** : le désigné garde sa place sauf si un coéquipier touche le ballon plus de 0,3 s avant lui, ou le touche au plus tard au même instant et arrive plus de 0,3 s avant lui. Temps machine : deux séries de 50 matchs (avant : `eb16120`), suite complète, rejeu de 2 matchs.

**Périmètre élargi en cours de route (24/11/2026), annoncé avant de continuer : 1 h 30** (+ 25 min). Première série « après » (règle double seule, 50 matchs) : changements rapides du premier 11,9 → 10,7 % (écart apparié − 1,4 point [− 2,75 ; + 0,01], non significatif). Relevé de 2 matchs : 9 des 15 changements rapides du premier sont des échanges entre le premier et le second déjà désignés (7 au même instant de contact : le maintien de chacun s'annulait) ; les autres sont des remplacements légitimes (coéquipier 0,8 à 2,1 s plus tôt) ou un premier qui n'est plus à temps. Règle double étendue au premier face au second (même règle, aucune constante nouvelle). Temps machine : une série « après » de plus.

**Critères chiffrés** (posés avant le code) : scène à pas différents (touche 0,1 s plus tôt et arrive 0,05 s avant : désigné gardé ; touche 0,4 s plus tôt et arrive 0,4 s avant : remplacé) ; scène du `15a` inchangée (contact au même instant : 0,2 s gardé, 0,4 s perdu) ; « ballon aérien : changements du premier en moins de 1 s (part) » nettement sous 12 % sur 50 matchs appariés, autres indicateurs du jeu aérien sans dégradation expliquée ; déterminisme à graine fixée ; suite complète à 3 643 passés, 0 ignoré, 14 désélectionnés (3 644 après l'élargissement : 2 cas ajoutés).

## Tests

- Scène : un coéquipier qui arrive 0,05 s plus tôt mais touche un pas avant ; le désigné reste premier. Un coéquipier qui arrive 0,4 s plus tôt le remplace.
- Série : « ballon aérien : changements du premier en moins de 1 s (part) » nettement sous 12 %.

## Acceptance criteria

- [x] Scène du maintien à pas différents (et scène de l'échange premier / second)
- [x] Changements rapides du premier nettement sous 12 % (50 matchs appariés) : 7,4 %
- [x] Déterminisme à graine fixée ; suite complète au compte attendu
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %

## Résultats (24/11/2026)

- Code : `v2engine/jeu_aerien.py` : classement par comparaison deux à deux (`_compare`) au lieu d'une clé de tri ; receveur visé d'abord, puis à temps ; à seniorité égale, instant du contact, arrivée, nom (inchangé) ; entre un plus ancien (premier désigné, puis second déjà désigné) et un plus récent, règle double du maintien : le plus récent ne passe devant que s'il touche le ballon plus de 0,3 s avant, ou au plus tard au même instant en arrivant plus de 0,3 s avant. Écart du second et sa marge de maintien (1,3 s) inchangés.
- Scènes (`tests/test_v2engine_jeu_aerien.py`, 2 cas ajoutés, 16 au total) : centre tendu, un coéquipier qui touche un pas de 0,1 s plus tôt et arrive 0,05 s avant reste derrière le désigné, un grand sauteur qui touche 0,4 s plus tôt et arrive 0,4 s avant le remplace (sans maintien, chacun passerait devant) ; premier et second qui touchent au même instant : le second arrivé 0,2 s avant reste second, 0,4 s avant il passe premier. Scène du `15a` inchangée (0,2 s gardé, 0,4 s perdu).
- Série (50 matchs appariés, `bench_series`, avant : `eb16120`), détail `docs/INDICATEURS_V2.md` § 77 : changements rapides du premier 11,9 → 7,4 % (− 4,8 points [− 6,6 ; − 3,0]) ; tous changements rapides 24,9 → 20,8 % ; désignations par équipe 34,9 → 31,6, part à deux 68,7 → 64,5 %, premier à temps 92,5 → 91,1 % (comptés à chaque changement : les échanges supprimés étaient des relevés à deux, à temps) ; têtes, centres, longs ballons, ballon libre, buts (4,66 → 5,18), tirs, possession : bruit ; premier contrôle du corps après un centre + 4 points, à la limite, isolé. 158 indicateurs significatifs sur 2 834 (environ 142 attendus).
- Première série « après » écartée (règle double sans priorité du premier sur le second : 10,7 %, non significatif) ; cause relevée sur 2 matchs (échanges premier / second), périmètre élargi et annoncé.
- Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes de la trace complète (`5b3136f9…`, `7646a6a6…`).
- Suite complète : 3 644 passés, 0 ignoré, 14 désélectionnés (3 642 + 2 cas) ; V1 non touchée.
- Durée réelle : environ 1 h 35 (analyse 15, développement 30, tests 25, intégration et vérifications 25), + 6 % sur l'estimation révisée de 1 h 30 (+ 90 % sur les 50 min d'origine : effet de bord du correctif sur la scène du `15a`, décision du propriétaire, puis cause principale trouvée par la mesure, périmètre élargi et annoncé avant de continuer). À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : trois séries de 50 matchs (46, 46 et 48 min, une écartée), deux relevés de 2 matchs, suite complète (22 min), rejeu de 2 matchs.

## Comments

- 24/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte `37850437…`, code et tests seuls) ; QC VALIDÉ (remarques non bloquantes : attendu de la suite à aligner, 3 642 + 2 ; même risque de transitivité que A1). Clôture VALIDÉ.
- Réserve A1 (`_compare` non transitif quand un désigné et deux nouveaux se disputent la place : cycle possible, choix dépendant de l'ordre de la liste des joueurs, déterministe, effet non visible dans la mesure) : acceptée par le propriétaire, « Accepter, corriger en ticket » ; correction au ticket `15a3` (sélection en deux temps, scène à trois joueurs sur les 6 ordres), avant ou avec le `15b`.
- À surveiller (expert) : premier contrôle du corps après un centre (+ 4 points, à la limite) à la série suivante.
