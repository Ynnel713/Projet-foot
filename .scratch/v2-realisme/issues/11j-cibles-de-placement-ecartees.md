# 11j: Cibles de placement écartées entre coéquipiers

**Chantier :** `v2-realisme` (diagnostic du 11f, 15/11/2026). **Priorité :** P0. **Catégorie :** décision.

**Constat vérifié :** voir 11g (marquage + presseur 13, presseur + replacement 11, gardien + tenir sa place 10, replacement + replacement 8 contacts sur 30 min) : deux coéquipiers visent des points presque confondus (cibles à moins de 1 m : 16 contacts sur 85).

**What to build:** Si deux coéquipiers visent des points à moins de 0,9 m l'un de l'autre, le moins prioritaire décale sa cible pour être à 0,9 m. Ordre de priorité : porteur et joueurs prioritaires du 11f (receveur, désigné sur ballon libre, gardien qui va au ballon), puis presseur, marquage, couverture, puis les autres.

**Attributs :** aucun.

**Constantes validées par le propriétaire le 15/11/2026 (« je valide ») :** écart minimal **0,9 m** (largeur du couloir d'évitement du 11f) ; ordre de priorité ci-dessus. Chiffre réel : non trouvé.

**Blocked by:** 11g.

**Bloque :** 11k.

**Status:** à faire (au commit : reporter dans `docs/INDICATEURS_V2.md` section 46 les pressings du 11g après correction, 791,5 → 783,5 par match et récupération en 5 s 0,193 → 0,175 : réserve A2 acceptée par le propriétaire)

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

- [ ] Scène : deux coéquipiers à cibles confondues : cibles finales à 0,9 m au moins, le prioritaire inchangé
- [ ] Cible seule ou déjà écartée : inchangée
- [ ] Diagnostic par paires de rôles : « cibles à moins de 1 m » quasi nul (rapporté)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
