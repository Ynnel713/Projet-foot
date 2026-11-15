# 11j: Cibles de placement écartées entre coéquipiers

**Chantier :** `v2-realisme` (diagnostic du 11f, 15/11/2026). **Priorité :** P0. **Catégorie :** décision.

**Constat vérifié :** voir 11g (marquage + presseur 13, presseur + replacement 11, gardien + tenir sa place 10, replacement + replacement 8 contacts sur 30 min) : deux coéquipiers visent des points presque confondus (cibles à moins de 1 m : 16 contacts sur 85).

**What to build:** Si deux coéquipiers visent des points à moins de 0,9 m l'un de l'autre, le moins prioritaire décale sa cible pour être à 0,9 m. Ordre de priorité : porteur et joueurs prioritaires du 11f (receveur, désigné sur ballon libre, gardien qui va au ballon), puis presseur, marquage, couverture, puis les autres.

**Attributs :** aucun.

**Constantes validées par le propriétaire le 15/11/2026 (« je valide ») :** écart minimal **0,9 m** (largeur du couloir d'évitement du 11f) ; ordre de priorité ci-dessus. Chiffre réel : non trouvé.

**Blocked by:** 11g.

**Bloque :** 11k.

**Status:** sans objet (15/11/2026), abandonné sur décision du propriétaire, code retiré (diagnostic : le 11g a déjà supprimé les cibles confondues ; voir Comments). Pressings du 11g reportés dans `docs/INDICATEURS_V2.md` section 46 (réserve A2 du 11g).

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : cibles des coéquipiers lues dans les intentions du pas (ou du précédent) dans `match._step_player` ; départage à priorité égale par le nom (déterministe).
Temps machine, non compté : suite complète ; deux mesures de 2 matchs.

## Acceptance criteria

- [ ] (sans objet) Scène : deux coéquipiers à cibles confondues : cibles finales à 0,9 m au moins, le prioritaire inchangé
- [ ] (sans objet) Cible seule ou déjà écartée : inchangée
- [x] Diagnostic par paires de rôles : « cibles à moins de 1 m » quasi nul (rapporté)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] (sans objet) Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] (sans objet, aucun code livré) Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**15/11/2026, démarrage.** Estimation annoncée : 1 h 30 (celle du ticket). Critères chiffrés annoncés avant le code : cibles finales à 0,9 m au moins et prioritaire inchangé ; cible seule ou écartée inchangée ; contacts francs entre coéquipiers à cibles à moins de 1 m au plus 2 sur 30 min de jeu.

**15/11/2026, implémentation (retirée ensuite).** `evitement.spread_target` (poussée le long de l'axe des deux cibles, au manque d'écart ; poussées qui s'annulent : vers le joueur) ; `match._placement_rank` (porteur, puis prioritaires du 11f, presseur, marquage, couverture, autres ; à égalité par le nom ; le porteur avant le receveur : il ne cède jamais sa place, écart découvert par un test) ; cibles écartées gardées d'un joueur à l'autre dans `simulate_match`. 16 tests, verts avec ceux du 11f.

**15/11/2026, diagnostic (`11j-diag-roles.py`, refait d'après celui du 11g, perdu avec le conteneur ; 30 min de jeu, graine 20260923 ; sorties ci-dessous).** Sur le moteur du 11g (arbre séparé à `6f40dd8`) : 39 contacts francs entre coéquipiers, même répartition par paires de rôles que `11g-diag-roles.txt` (l'outil est fidèle) ; **aucun n'a des cibles d'intention à moins de 1 m**. Écart des deux cibles : 1 à 2 m 7, 2 à 3 m 1, 3 à 5 m 9, 5 à 10 m 10, au-delà 12 ; l'un des deux à moins de 2 m de sa propre cible 23 ; au moins une cible mobile (pressing) 19. Le « 16 sur 85 » du constat datait d'avant le 11g, qui a supprimé les cibles confondues (deux chasseurs du même ballon libre, deux presseurs du même porteur). Avec le 11j : 44 contacts sur 30 min, dont 1 à cibles à moins de 1 m ; 2 matchs (`11j-det1.txt`) : contacts francs entre coéquipiers 100 → 110,5 par match (aucun gain, dans le bruit), passes 1 087 → 1 203, buts 2,5 → 4,5 (trajectoires divergentes, 2 matchs non interprétables).

**15/11/2026, décision du propriétaire : « Abandonner 11j (Recommandé) ».** Code et tests retirés ; ticket sans objet ; le 11k (50 matchs) dira si les contacts restants (cibles de 1 à 2 m, cibles mobiles, joueur arrivé à sa cible) demandent un ticket. Options écartées : garder le code (sans effet mesurable), élargir l'écart à 2 m (nouvelle constante).

**15/11/2026, durée.** Estimation 1 h 30 ; durée réelle environ 50 min (analyse 15, développement 15, tests 10, diagnostic et documentation 10), − 44 % : ticket abandonné après le diagnostic, sans suite complète ni validation. Leçon : refaire le diagnostic sur le moteur courant avant de coder un ticket issu d'un constat antérieur à son prédécesseur. Temps machine hors total : trois diagnostics de 30 min de jeu, une mesure de 2 matchs.

**15/11/2026, passage 1 de l'expert : APPROVED ; QC VALIDÉ ; clôture VALIDÉ** (journal, `v2-realisme/11j/cloture` ; commit `a89be07`). Remarques facultatives, non traitées : A1 le script de diagnostic lit encore `placed` (code retiré) et la sortie « après » ne se reproduit plus telle quelle ; A2 avertissement `uv` en tête de `11j-det1.txt`. Trace reportée ici au commit du 11k (le ticket faisait partie des fichiers revus).
