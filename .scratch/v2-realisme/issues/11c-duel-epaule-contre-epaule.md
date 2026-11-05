# 11c: Duel épaule contre épaule à la course

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (deux joueurs qui courent vers le même ballon se disputent la position). **Catégorie :** exécution.

**Constat vérifié :** deux joueurs qui courent côte à côte ne font que se repousser géométriquement ; le premier arrivé au ballon le joue.

**What to build:** Deux joueurs au contact, de côté, courant vers le même point : un duel d'épaule (Strength, et Balance pour rester sur sa course, à répartir sans double comptage avec 12c) décale le perdant de sa trajectoire et lui fait perdre de la vitesse ; faute possible (Aggression, déjà branchée).

**Attributs :** Strength (gagner le contact) ; Balance seulement via 12c

**Blocked by:** 11b (Collision asymétrique : Strength).

**Bloque :** 11e.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : déclencheur : contact latéral et cible commune.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** deux joueurs côte à côte vers un ballon libre : duel tracé
- **Comportementaux (profils comparés) :** Strength 90 contre 40 : le plus fort atteint le ballon plus souvent

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Duel tracé et affiché
- [ ] Effet de Strength mesuré
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
