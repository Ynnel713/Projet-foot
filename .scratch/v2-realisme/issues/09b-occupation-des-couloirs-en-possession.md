# 09b: Occuper la largeur en possession

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (une équipe sans joueur sur un côté ne peut pas écarter le bloc adverse). **Catégorie :** placement.

**Constat vérifié :** les appels choisissent un espace libre autour de la place (`off_ball.choose_space`), sans contrainte de couloir.

**What to build:** En possession installée, chaque couloir extérieur a au moins un joueur et aucun couloir n'en a plus que la limite validée ; la règle s'applique au choix de l'espace et à la place de référence (02d).

**Attributs :** aucun

**Blocked by:** 02d (Place de référence avec ballon selon le rôle); 09a (Couloirs et demi-espaces : définition et mesure).

**Bloque :** 09c, 09h, 13g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : contrainte souple (pénalité sur l'espace choisi).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** possession au centre : au moins un joueur par couloir extérieur
- **Statistiques (séries de matchs) :** 50 matchs : part du temps avec les deux couloirs extérieurs occupés

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Occupation mesurée en hausse dans le sens attendu (50 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
