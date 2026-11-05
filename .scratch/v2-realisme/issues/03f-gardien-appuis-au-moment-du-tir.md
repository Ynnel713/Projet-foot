# 03f: Gardien : en mouvement ou sur ses appuis au moment du tir

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un gardien pris à contre-pied doit encaisser plus). **Catégorie :** exécution.

**Constat vérifié :** la chance du tir ne tient compte que de la position du gardien, pas de sa vitesse au moment de la frappe (`shooting.keeper_position_factor`).

**What to build:** Avec l'arrêt par portée du 05b, la portée latérale disponible du gardien dépend de sa vitesse au moment du tir : déjà lancé du bon côté, il gagne ; à contre-pied, il perd (portée réduite d'une part proportionnelle à sa vitesse dans le mauvais sens).

**Attributs :** aucun

**Blocked by:** 03b (Gardien : placement sur la bissectrice ballon-poteaux); 05b (Arrêt : le gardien atteint ou non le ballon).

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : portée de base du 05b.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même tir, gardien immobile, lancé du bon côté, à contre-pied : chance d'arrêt décroissante dans cet ordre

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de la vitesse du gardien sur l'arrêt mesuré en scène contrôlée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
