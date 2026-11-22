# 03b3a: Gardien : hauteur de placement et sorties (Rushing Out)

**Découpé du ticket `03b3` le 22/11/2026.** Gardien de référence : Rushing Out 55, médiane des 50 gardiens notés de Ligue 1 de la base (de 25 à 90) ; un gardien sans note (ou sans cette colonne) vaut la référence et garde le comportement d'avant.

**What to build:** Rushing Out (tendance : style, jamais niveau) règle la hauteur du gardien quand le ballon est loin (`gardien.depth_for_ball` : la part au-delà de `DEPTH_M[0]`, sans changer le placement près du ballon), la marge de sortie sur ballon libre (`gardien.RUSH_MARGIN_S`) et la distance maximale de sortie (`gardien.RUSH_MAX_FROM_GOAL_M`). Le haut balaie derrière sa défense ; le risque d'être lobé est mesuré au `10b`.

**Attributs :** Rushing Out (colonne `Rushing Out (Tendency)` de la base).

**Blocked by:** `03b1`.

**Bloque :** `03b3b` ; `10b` (lob et dribble du gardien) ; `v2-coach-et-gestion-de-match/04` ; `v2-collectif/22a`.

**Status:** livré (22/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 25 min |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Temps machine, non compté : série réelle de 50 matchs, deux séries forcées de 30 matchs (tous les gardiens à 90, puis à 25), environ 1 h 05 ; suite complète (environ 16 min).

**Constantes** (proposées au propriétaire le 22/11/2026, délégation permanente « Je valide automatiquement toutes tes recommandations et les conseils d'expert ») : référence 55 ; hauteur au-delà de `DEPTH_M[0]` multipliée par 1 + 0,01 par point autour de 55, bornée à 0,6-1,4 (ballon loin, sans ligne : 6,1 m à 25, 8,0 m à 55, 10,3 m à 90 ; toujours dans la surface) ; marge de sortie 0,50 s − 0,01 s par point, bornée à 0,15-0,85 s (0,80 s à 25, 0,15 s à 90) ; distance maximale de sortie 35 m + 0,3 m par point, bornée à 25-45 m (26 m à 25, 45 m à 90). Repères réels (hauteur moyenne et sorties d'un gardien selon son style) : non trouvés, ordres de grandeur.

## Acceptance criteria

- [x] Constantes proposées au propriétaire avant le code
- [x] Gardien sans note ou à 55 : placement et course identiques à avant (scènes) ; matchs sans notes : mêmes empreintes avant / après
- [x] Rushing Out élevé : position moyenne plus haute quand le ballon est loin et plus de sorties sur ballon libre (scènes, puis 30 matchs forcés à 90 contre 30 matchs forcés à 25) ; près du ballon, placement inchangé
- [x] Série réelle de 50 matchs appariés : buts par match avec intervalle (repère du `03b2` : 4,48)
- [x] Test de rayon et carte à jour ; Rushing Out sort des exceptions de couverture et rejoint la liste de transition (un contexte)
- [x] Durée réelle relevée ; déterminisme ; suite V2 verte ; V1 inchangée

## Résultats (22/11/2026)

- Code : `gardien.rushing_out` (référence 55 si pas de notes ou pas cette colonne, et non le défaut générique 60), `depth_factor`, `rush_margin_s`, `rush_max_from_goal_m` ; `race` et `bisector_point` les lisent ; `cerveau._keeper` lit la distance maximale propre au gardien. `condition.FAMILIES` : « Rushing Out » renommé « Rushing Out (Tendency) », nom de la carte et de la base.
- Scènes (`tests/test_v2engine_style_gardien.py`, 8 tests) : à 55 ou sans note, mêmes points qu'avant ; ballon loin sans ligne, 6,05 m à 25 contre 10,275 m à 90 ; ballon à 12 m ou moins de son but : même place pour tous ; marge de sortie 0,80 s à 25, 0,15 s à 90 ; distance maximale 26 m à 25, 45 m à 90 ; symétrie pour l'extérieur.
- Contrôle (30 matchs, tous les gardiens forcés à 55) : 30 scores identiques à la série `03b2-apres` (code d'avant).
- Séries forcées (30 matchs chacune, mêmes graines) :

| Rushing Out forcé | Buts/match | Hauteur, ballon à plus de 40 m (m) | Sorties/gardien/match | Prises hors surface/gardien/match |
|---|---|---|---|---|
| 25 | 4,73 | 10,22 | 5,38 | 5,20 |
| 55 | 4,30 | 13,95 | 5,78 | 7,05 |
| 90 | 4,30 | 15,81 | 7,85 | 10,33 |

  Écart apparié des buts 90 contre 25 : − 0,43 [− 1,39 ; + 0,53], dans le bruit.
- Série réelle (50 matchs appariés contre `03b2-apres`) : buts 4,48 → 4,12, écart − 0,36 [− 1,03 ; + 0,31], dans le bruit. Par tranche de note réelle : hauteur 11,97 m sous 50 (16 gardiens-matchs), 14,22 m de 50 à 64 (34), 15,16 m à 65 et plus (50), croissante ; sorties 7,44 / 5,74 / 6,78, non monotones en série réelle (l'adversaire et le jeu de l'équipe pèsent plus que la note ; l'effet propre est isolé par les séries forcées).
- Suite complète, premier passage : 2 échecs révélés et corrigés (nom de famille dans `condition.FAMILIES` ; gardien noté sans la colonne qui valait 60 au lieu de 55, cassant `test_scenes`). Aucun titulaire de la série réelle ne manque de la note : mesures inchangées par la correction.
- Suite complète après correction : 3 540 passés, 0 ignoré, 14 désélectionnés (3 531 + 9, dont les 8 cas du nouveau fichier ; base relevée à la clôture du `03b2`). Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes (`51f3b07e…`, `d9b18549…`).
- Durée réelle : environ 2 h 20 (analyse 30, développement 35, tests 40, intégration et vérifications 35), + 22 % ; à l'horloge de la session hors attentes machine, non chronométrée.

## Comments

- 22/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Aucune anomalie bloquante. Améliorations facultatives de l'expert : A1, en face-à-face avec une ligne, la règle du `03g` reprend la profondeur étirée par Rushing Out (10,6 m contre 8,2 m à 25 m du but), plausible, scène à ajouter au plus tard au `10b` ; A2, marge de 0,15 s sans hystérésis, compter au `10b` ou au `03b3b` les sorties d'au moins 0,5 s pour écarter les oscillations ; A3, compte de la suite (8 cas nouveaux sur + 9) précisé. Réserves du QC, non bloquantes : durée non chronométrée ; sorties non monotones en série réelle (expliqué).
