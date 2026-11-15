# 11g: Une seule décision par ballon : un chasseur sur le ballon libre, un presseur sur le porteur

**Chantier :** `v2-realisme` (diagnostic du 11f, 15/11/2026). **Priorité :** P0 (suite de l'évitement, priorité absolue du propriétaire). **Catégorie :** décision.

**Constat vérifié (diagnostic hors dépôt, 30 min de jeu, 85 contacts francs entre coéquipiers) :** paires de rôles en contact : ballon libre + ballon libre 13, marquage + presseur 13, presseur + replacement 11, gardien + tenir sa place 10, replacement + replacement 8, ballon libre + presseur 6, presseur + presseur 2. Code : tout joueur à moins de 15 m d'un ballon libre prend le rôle « ballon libre » (`cerveau.interpret`) ; tout joueur non affecté qui quitte le bloc (Teamwork) devient presseur et vise le porteur lui-même (`cerveau.decide`, « quitte le bloc pour aller au ballon »), en plus du presseur affecté par `defense`.

**What to build:** (1) Ballon libre : un seul joueur par équipe y va, le plus proche (`nearest_of_team`, déjà le « désigné » du 11f) ; les autres se replacent. (2) Porteur adverse : un seul presseur ; le joueur qui quitte le bloc (effet de Teamwork, conservé) ne vise plus le porteur quand un presseur est affecté : il couvre derrière lui, à 3 m du porteur sur l'axe porteur → son propre but.

**Attributs :** aucun nouveau ; Teamwork garde son effet (sortir du bloc), seule la cible de celui qui sort change.

**Constantes validées par le propriétaire le 15/11/2026 (« je valide ») :** un seul chasseur par équipe sur ballon libre ; couverture du joueur sorti du bloc à **3 m** du porteur, vers son propre but. Chiffre réel : non trouvé.

**Blocked by:** 11f (livré).

**Bloque :** 11k.

**Status:** livré (15/11/2026), validé expert (avec réserves acceptées) + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : deux points d'application dans `cerveau` (rôle du ballon libre, cible du joueur sorti du bloc) ; tests de scène existants sur le ballon libre ou le pressing peut-être à adapter.
Temps machine, non compté : suite complète (environ 12 min) ; deux mesures de 2 matchs ; diagnostic par paires de rôles.

## Tests

- **Unitaires (scène contrôlée) :** trois coéquipiers à moins de 15 m d'un ballon libre : un seul « ballon libre » (le plus proche), les autres en replacement ; presseur affecté et second joueur sorti du bloc : le second vise un point à 3 m du porteur, côté de son but, pas le porteur ; sans presseur affecté : il va au porteur comme avant.
- **Statistiques :** 2 matchs (indicatif) ; série de 50 matchs au 11k.

## Acceptance criteria

- [x] Constantes produit validées par le propriétaire avant le code
- [x] Scènes : un seul chasseur par équipe sur ballon libre ; joueur sorti du bloc en couverture à 3 m, pas sur le porteur
- [x] Teamwork garde son effet (garde des attributs et test de rayon verts)
- [x] Diagnostic par paires de rôles sur 30 min : « ballon libre + ballon libre » et « presseur + presseur » quasi nuls (rapportés)
- [x] Ballons libres récupérés et pressings rapportés sur 2 matchs (avant / après)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**15/11/2026, démarrage.** Estimation annoncée : 1 h 50 (celle du ticket). Critères chiffrés annoncés avant le code (voir Acceptance criteria).

**15/11/2026, implémentation.** `cerveau.interpret` : sur ballon libre, rôle « ballon libre » au seul `nearest_of_team`, les autres « replacement ». `cerveau.decide` : le joueur non affecté qui quitte le bloc (Teamwork) garde le rôle presseur ; si un presseur est déjà affecté au même porteur (`defense.assignments`), il vise un point de couverture à `COVER_BEHIND_PRESSER_M` = 3 m du porteur sur l'axe porteur → son but (`defense.own_goal`), action « couvrir », sinon il va au porteur comme avant. Tests : `tests/test_v2engine_une_decision.py` (2 : un seul chasseur par équipe, le chasseur change avec la distance) ; `tests/test_v2engine_defense.py` : `test_unassigned_player_holds_the_bloc_unless_he_leaves_it` adapté au comportement validé (un presseur est affecté : le joueur sorti couvre à 3 m, côté de son but ; il attendait « quitte le bloc pour aller au ballon »), et cas sans presseur affecté ajouté (comportement d'avant conservé).

**15/11/2026, mesure (2 matchs, graine d'audit ; `11g-avant-2matchs.txt`, identique à `11f-det1.txt` hors temps de calcul ; `11g-det1.txt`).** Contacts francs entre coéquipiers **241,5 → 113 par match** (− 53 % ; 356 → 113 depuis l'avant 11f) ; tous contacts francs 842 → 613 ; contacts perdus 959 → 685. Passes 1 114 → 1 139, passes réussies 0,837 → 0,855, buts 4,0 → 5,5, tirs par équipe 20,8 → 21,8, pertes de balle 224 → 218, pressings 792 → 823, pressings suivis d'une récupération en 5 s 0,193 → 0,188, temps de jeu effectif 0,719 → 0,759 (2 matchs : indicatif, série de 50 matchs au 11k ; récupération sur ballon libre à y mesurer). Coût inchangé (123,0 → 121,4 s par match). `11g-det1` et `11g-det2` identiques hors temps de calcul.

**15/11/2026, diagnostic par paires de rôles (30 min de jeu, `11g-diag-roles.txt`).** Contacts francs entre coéquipiers 85 → **43** ; ballon libre + ballon libre 13 → **0** ; ballon libre + presseur 6 → 0 ; presseur + presseur 2 → 3 ; restent surtout des cibles de placement voisines (replacement + replacement 6, marquage + presseur 6, marquage + replacement 5, gardien + tenir sa place 5) : objet du 11j.

**15/11/2026, suite complète.** 3 170 passés, 0 ignoré, 14 désélectionnés (3 167 + 3 ; `11g-suite.txt`) ; `CLAUDE.md` mis à jour. V1 inchangée.

**15/11/2026, durée.** Estimation 1 h 50 ; durée réelle environ 1 h 35 (analyse 25, développement 20, tests 25, intégration 25), − 14 % : deux points d'application dans `cerveau` ; le diagnostic par paires de rôles (fait pendant le cadrage) a désigné les deux décisions fautives. Durée estimée à l'horloge de la session hors attentes machine et échanges, non chronométrée. Temps machine hors total : suite complète (12 min), trois mesures de 2 matchs, deux diagnostics de 30 min de jeu.

**15/11/2026, passage 1 de l'expert : REJECTED.** A1 [bloquant] : `nearest_of_team` comptait le gardien ; un gardien plus proche qui ne sort pas (l'attaquant arrive avant lui, `gardien.race`) privait la défense de tout chasseur de champ (mesure : ballons libres à portée laissés par le gardien 23 → 39,5 par match, tirs de près 4,5 → 7,5 par équipe, que j'avais classés « dans le bruit »). A2 [réserve] : désignation sans hystérésis (à surveiller au 11k). A3 [réserve] : point de couverture non borné au but ni au terrain. A4 [réserve] : compte rendu des mesures incomplet. **Réestimation annoncée** : + 35 min (environ 2 h 10). **Corrections** : `cerveau.nearest_field_player` (joueur de champ le plus proche, gardien exclu) pour le rôle « ballon libre » et pour la priorité d'évitement de `match._step_player` (cohérence avec le 11f) ; la portée de sortie du gardien garde `nearest_of_team` ; point de couverture borné (`min(3 m, distance au but)`, `clamp_to_pitch`) ; deux scènes avec gardien (gardien qui ne sort pas : le défenseur reste chasseur ; gardien qui sort : un seul chasseur de champ) ; mesures et diagnostic refaits, indicateurs du gardien et tirs de près rapportés.

**15/11/2026, mesure et suite après correction.** 2 matchs : contacts francs entre coéquipiers 241,5 → **100 par match** ; ballons libres laissés par le gardien 23 → 24,5 ; tirs de près 4,5 → 5,5 ; buts 4,0 → 2,5 ; passes 1 114 → 1 087 ; coût inchangé (123,0 → 123,1 s) ; `11g-det1` et `11g-det2` identiques hors temps de calcul. Diagnostic par paires de rôles (`11g-diag-roles.txt`) : 85 → 39 contacts ; ballon libre + ballon libre 0. Suite complète : 3 172 passés, 0 ignoré, 14 désélectionnés (3 167 + 5) ; `CLAUDE.md` mis à jour.

**15/11/2026, durée révisée.** Environ 2 h 05 (analyse 25, développement 30, tests 35, intégration 35), − 4 % sur la dernière annonce (2 h 10), + 14 % sur l'estimation du ticket : correction du rejet comprise (le gardien n'avait pas été pris en compte dans la désignation, et aucune scène ne le contenait).

**15/11/2026, passage 2 de l'expert : APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ** (journal, `v2-realisme/11g/cloture`, réserves acceptées). A1 [réserve] : chasseur désigné sans hystérésis (recalculé à chaque pas) ; **accepté par le propriétaire** : « Accepter, mesurer au 11k (Recommandé) » (mesurer au 11k les changements de chasseur en moins de 1 s ; si notable, désigner par le temps d'arrivée au point du ballon avec une marge de maintien). A2 [réserve] : pressings non rapportés après correction ; **accepté par le propriétaire** : « Fiche maintenant, indicateurs au 11j (Recommandé) » : pressings 791,5 → 783,5 par match, pressings suivis d'une récupération en 5 s 0,193 → 0,175 (≈ 1,3 σ, dans le bruit), à reporter dans `docs/INDICATEURS_V2.md` section 46 au commit du 11j. A3 [facultatif] : `nearest_field_player` sans garde sur une liste vide (inatteignable en match), non traité.

