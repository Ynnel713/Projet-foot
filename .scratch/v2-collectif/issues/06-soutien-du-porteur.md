# 06: Soutien du porteur et lignes de passe

**What to build:** Les coéquipiers du porteur se placent pour **créer des solutions** : triangles, lignes de passe ouvertes, distances de soutien cohérentes, occupation des couloirs, joueurs entre les lignes. Une équipe ne monte pas toute au-dessus du ballon : il reste un **équilibre derrière le ballon**. Fin des joueurs qui se superposent ou qui rejoignent tous un point prédéfini.

**Attributs :** Off the Ball (qualité du démarquage), Teamwork (équilibre), Vision du porteur (exploitation).

**Blocked by:** 04, 25 (socle cinématique et contact).

**Status:** livré (31/10/2026), validé expert + QC

**Point de vigilance :** Off the Ball (ticket cerveau 03) choisit déjà un espace libre : l'intégrer au placement collectif. Les appels au trot, sauf vers l'avant, ont été validés le 26/10 mais sont sauvegardés dans `.scratch/v2-collectif/wip-socle-02-intensite.patch`.

- [x] Nombre moyen de solutions de passe ouvertes pour le porteur dans une fourchette crédible (indicateur du ticket 01, valeur à sourcer)
- [x] Aucun regroupement : distance minimale entre coéquipiers respectée hors duel
- [x] Toujours au moins un joueur en sécurité derrière le ballon en possession installée
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée (suite complète : 2 123 passés, 13 désélectionnés, 31/10/2026)

## Implémentation (31/10/2026)

**Constantes validées (30/10/2026) :** espace trouvable si la passe du porteur réussit à 0,7 au moins (`OPEN_LANE_PROBABILITY`, d'abord 0,5) ; 8 m au moins entre coéquipiers ou espaces visés (`SPACING_MIN_M`) ; espace gardé jusqu'à l'atteindre (2 m), au moins 1 s, au plus 3 s ; 2 joueurs de champ gardés derrière le ballon en possession installée (`REST_DEFENDERS`), avec la courbe Teamwork du ticket 07 (99 → 0 %, 55 → 15 %, 11 → 35 % de chance de monter quand même).

**Code :** `v2engine/off_ball.py` (`choose_space` : espacement, espace trouvable d'abord) ; `v2engine/cerveau.py` (espace gardé, équilibre derrière le ballon) ; indicateurs `scripts/v2_indicators.py` (regroupement par phase, porteur exclu ; joueurs derrière le ballon ; équilibre) et `scripts/measure_v2.py`.

**Critères ajustés par le propriétaire (31/10/2026, après diagnostic) :** le regroupement exclut le porteur (se montrer près de lui est du soutien) ; Teamwork est jugé par les tests unitaires, la règle d'équilibre ne se déclenchant presque jamais en match (environ 7 joueurs déjà derrière le ballon).

**Mesure (20 matchs, avant `8043889` → après) :** voir `docs/INDICATEURS_V2.md`. Solutions de passe 1,86 → 1,96 ; regroupement avec ballon porteur exclu ≈ 3,3 % (4 matchs) ; au moins un joueur derrière 100 % ; buts 1,95 → 2,75 (à surveiller, ticket 22).

## Comments

- 31/10/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ.
  - A1 (réserve) : regroupement inchangé en match (6,8 → 7,0 % porteur inclus) ; la valeur porteur exclu (≈ 3,3 %) repose sur 4 matchs, pas 20.
  - A2 (réserve) : effet d'Off the Ball sur les solutions de passe indiscernable du bruit (1,92 contre 1,96) ; à reprendre au ticket 22 ou au socle 02.
  - A3, A4 (facultatif) : accessibilité jugée sur la passe du porteur et non sa Vision ; joueur d'équilibre à la hauteur exacte du ballon.
  - Réserves A1 et A2 acceptées par le propriétaire : « Ok tour est bon », « Tout est bon ».
  - À surveiller au ticket 22 : buts (2,75), regroupement hors porteur (paires DC), différenciation Off the Ball, appels des DC et latéraux.
- 31/10/2026, complément (correction C5, incluse dans le diff relu et dans `b8461d9`) : pendant une passe de son équipe, les coéquipiers autres que le receveur gardent leur appel au lieu de courir au ballon (`cerveau.interpret`, test `test_teammates_keep_their_run_while_their_pass_is_in_flight`) ; une passe adverse ou un ballon perdu restent disputés comme avant.
  - Mesure (4 matchs, porteur inclus) : regroupement avec ballon 6,8 → 4,9 %. Le reste est fait à 93 % de croisements passagers (cibles écartées), à 89 % en transition offensive : hors périmètre, à reprendre au ticket 22. Mesure de 20 matchs non refaite (ticket clos).
- 31/10/2026, passage 2 (complément C5, code inchangé, empreinte a3c4de37) : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ.
  - A1, A2 (réserves) : inchangées depuis le passage 1 ; acceptées par le propriétaire : « J'accepte A1 et A2 ».
  - A5 (facultatif) : `docs/INDICATEURS_V2.md` présente encore 7,0 % (mesure d'avant C5) comme état après le ticket ; y ajouter le diagnostic C5 (4,9 %, 4 matchs).
  - QC (non bloquant) : le critère 7 cite 2 123 passés ; suite au 31/10/2026 sur 25514b5 : 2 125 passés, 13 désélectionnés.
  - À surveiller au ticket 22 : appels des DC et latéraux pendant une passe en l'air (C5 met tout joueur de champ non visé en appel).
