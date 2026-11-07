# 03d: Gardien : sortie sur un ballon dans la profondeur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (une passe en profondeur doit pouvoir être coupée par le gardien). **Catégorie :** décision.

**Constat vérifié :** le gardien ne court au ballon libre que s'il est le plus proche de son équipe ou à moins de 15 m (règle générale `BALLON_LIBRE`) ; aucune comparaison avec l'attaquant ni limite de surface.

**What to build:** Sur une passe adverse ou un ballon libre vers son but, le gardien compare son temps d'arrivée à celui de l'attaquant le plus rapide (même calcul que `defense.arrival_time_s`) ; s'il arrive avant avec une marge validée, il sort (état « sortie ») ; sinon il reste en placement. Hors de sa surface, il dégage ou joue au pied, jamais à la main.

**Hors de ce ticket :** le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 03c (Gardien : hauteur selon le ballon et la ligne défensive (couverture de la profondeur)).

**Bloque :** 03g.

**Status:** livré (07/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : le jeu à la main hors surface n'existe pas aujourd'hui ; le dégagement réutilise la passe existante.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** passe en profondeur, gardien à 20 m du point de chute, attaquant à 30 m : il sort ; attaquant à 10 m : il reste
- **Statistiques (séries de matchs) :** 50 matchs : sorties par match et part réussie

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (proposées par Claude, validées par délégation, voir Comments ; chiffres réels non trouvés)
- [x] Décision de sortir fondée sur les temps d'arrivée, tracée (`gardien.race` ; raison de l'intention avec les deux temps ; tests)
- [x] Aucune prise à la main hors de la surface (test : tir « capté » tiré hors de sa surface devient « repoussé »)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`bb720caeead76988`, 15 minutes, graine d'audit, rapport sans la ligne du temps de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 500 passés, 14 désélectionnés (07/11/2026, 13 min 45 s, état final) ; attendu 2 493 + 7 nouveaux

## Comments

- 07/11/2026 : **Constantes proposées avant le code** (par Claude, validées par délégation du propriétaire, consigne permanente ; chiffres réels non trouvés, ordres de grandeur) : **marge de 0,5 s** (le gardien sort s'il arrive au moins 0,5 s avant l'adversaire de champ le plus rapide, temps de `defense.arrival_time_s`) ; **plafond de 35 m** entre le point visé et le centre de son but (au-delà, il reste en placement) ; hors de sa surface, un tir arrêté tiré « capté » devient « repoussé » (jamais à la main). **Critères chiffrés** : (1) scène du ticket : ballon à 20 m du gardien, attaquant à 30 m : il sort ; à 10 m : il reste ; (2) la marge sépare un attaquant 0,3 s derrière (il reste) d'un attaquant 0,7 s derrière (il sort) ; (3) aucune sortie au-delà de 35 m, même sans attaquant ; (4) 50 matchs : sorties par match, part réussie, part hors de sa surface, distance maximale du gardien à son but (réserve A1 du 03a : 54 m au 03b) ; (5) deux exécutions, même empreinte.
- 07/11/2026 : **Réalisé** (`v2engine/gardien.py` : `RUSH_MARGIN_S`, `RUSH_MAX_FROM_GOAL_M`, `Race`, `race(player, ball, players)` ; `cerveau._keeper` : la course n'est calculée que sur un ballon libre à sa portée, le gardien passe en `sortie` si `rush`, sinon reste en `placement` avec la raison « l'adversaire arrive avant lui » ou « le ballon est trop loin de son but » ; `match.py` : tir capté hors de sa surface repoussé ; banc : `Collector.on_keeper`, `measure_v2` : sorties, sorties réussies, hors de sa surface, ballons libres laissés). Point visé = celui que le gardien courrait déjà (`loose_ball_target`) ; les adversaires de champ sont tous comptés, le gardien adverse non.
- 07/11/2026 : **Découverte en cours de route, corrigée dans le ticket** : sur HEAD, le gardien « sortait » 215 fois par match (43 % hors de sa surface, distance maximale 49 m), parce que la passe d'un coéquipier en vol lui paraissait un ballon libre dès qu'il était le plus proche de son équipe (il courait vers les passes de son propre camp). La passe de son équipe en vol n'est plus un ballon libre pour lui (`cerveau._keeper`, `own_pass`) ; son receveur la prend, et si la passe est ratée le ballon redevient libre. Hors du texte du ticket mais dans son esprit (« sur une passe adverse ou un ballon libre ») ; sans cela la comparaison avec l'attaquant portait sur des cas qui n'existent pas.
- 07/11/2026 : **Mesure (50 matchs, graine d'audit, trois séries)** : **A** = HEAD `156d85d` + indicateurs ; **B** = A + passes de son équipe exclues, course neutralisée (`RUSH_MARGIN_S = -1e9`, `RUSH_MAX_FROM_GOAL_M = 1e9`) ; **C** = final. Sorties par match **215 → 70,6 → 34,9** ; part hors de sa surface **43,2 % → 21,9 % → 0,17 %** ; distance maximale du gardien à son but **49,3 → 36,2 → 29,2 m** (réserve A1 du 03a : 54,1 m au 03b) ; point visé moyen 19,5 → 13,5 → 7,5 m ; ballons libres à sa portée laissés (le gardien reste en placement) 0 → 0 → 40,6 par match ; part de sorties réussies (de la sortie à la relance : il a le ballon) 3,4 → 5,8 → 4,6 %. Effets de jeu : buts 3,00 → 3,08 → 2,90 par match, chance moyenne des tirs 0,0691 → 0,0641 → 0,0628, tirs par équipe 22,8 → 23,1 → 22,7, arrêts 15,3 → 16,1 → 14,9, corners 13,6 → 12,7 → 12,6, distance moyenne du gardien à son but 11,65 → 11,43 → 11,34 m, tirs à moins de 2 m de la bissectrice 98,0 → 98,5 → 98,9 %. Aucun écart de jeu au-delà du bruit.
- 07/11/2026 : **Limites et points à surveiller.** (1) En match, le gardien sort presque toujours dans sa surface (0,17 % des sorties au-dehors, soit environ 0,06 par match) : hors de sa surface, un défenseur est le plus souvent plus proche du ballon, ou un attaquant arrive avant lui ; le mécanisme est démontré en scène, il reste rare en match, et le ticket n'avait aucun repère réel à atteindre (non trouvé). À regarder avec le 03g et la réserve A2 du 03c (la ligne de référence du bloc). (2) La « part réussie » (4,6 %) est faible parce que l'indicateur compte tout épisode de course, y compris les remises en jeu où le ballon attend un instant et les rebonds après un arrêt ; il ne mesure pas les interceptions de passes en profondeur seules. Un indicateur « sorties disputées » (un attaquant dans la course) est à créer au 03g. (3) Dégagement hors de sa surface : il passe par la règle générale du porteur, sans ordre de dégagement ni jeu à la main distinct : le moteur n'a pas de jeu à la main hors des arrêts de tir, d'où la seule règle « capté devient repoussé » ; le tir arrêté capté hors de sa surface est rare (le gardien reste dans sa surface). (4) Le tirage « capté / repoussé / claqué » est inchangé : seul le résultat est requalifié, le flux aléatoire n'est pas modifié. (5) Le ballon libre devant un défenseur plus proche que le gardien reste au défenseur : pas de règle « c'est à moi » (appel du gardien).
- Tests : 7 nouveaux (`tests/test_v2engine_gardien.py`, 5 : scène du ticket et trace, marge, plafond de 35 m, gardien adverse ignoré et miroir de l'équipe visiteuse, passe de son équipe en vol ; `tests/test_v2engine_issues_tir.py`, 1 : capté hors de sa surface repoussé ; `tests/test_v2_indicators.py`, 1 : épisodes de sortie).
- Durée : estimée 2 h 05 (125 min ; 20/50/35/20), réelle environ 2 h 15 (135 min ; 25/55/40/35, non chronométrée), écart environ + 8 % : l'analyse des 215 sorties par match a ajouté une correction et deux séries de mesure de plus. Temps machine, hors total : trois séries de 50 matchs d'environ 25 min, suite complète 13 min 45 s (`03d-suite.txt`).
- 07/11/2026 : **Clôture.** Expert `APPROVED_WITH_RESERVATIONS` (empreinte `9deb6bd9`), QC `VALIDÉ` (un seul passage), clôture `VALIDÉ` (journal). Réserves acceptées d'office par le propriétaire, selon sa consigne permanente (« Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026) : **A1** preuve en match du cas P0 (passe en profondeur coupée) insuffisante, seulement démontrée en scène : créer l'indicateur « sorties disputées » (un attaquant dans la course) au 03g, vérifier que le filtre `reach` (ballon à moins de 15 m, ou gardien le plus proche) ne masque pas de courses gagnantes pour le gardien, et ajouter la scène « ballon à 18 m du gardien, défenseur à 15 m du ballon, attaquant à 30 m » ; **A2** pas d'ordre de dégagement ni de jeu au pied hors surface (seul « jamais à la main » est garanti, pour les arrêts de tir) : à revoir si un jeu à la main ou une passe en retrait au gardien est ajouté. Facultatifs : A3 pas d'hystérésis sur la décision de sortie (diagnostic sur 2 matchs de 30 minutes : la plupart des épisodes durent plus de 0,5 s, aucun basculement massif ; à surveiller), A4 cas de bord d'un gardien à environ 16,5 m. Réserve du QC, non bloquante : l'état du gardien est lu dans la chaîne de la raison (fragile mais testée).
