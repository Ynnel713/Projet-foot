# 08a: Champ de vision : ce qui est dans le dos n'est pas vu

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** le porteur évalue ses options avec les positions réelles de tous les adversaires (`decision.evaluate_options`) ; seule l'élan des adversaires est déformé par l'Anticipation (`decision.anticipation_share`).

**What to build:** Chaque joueur voit les joueurs situés dans un cône autour de son cap (angle sourcé ou « non trouvé ») ; les autres ne sont pas vus à cet instant. Ce ticket calcule la visibilité et la trace ; il ne change pas encore les décisions.

**Hors de ce ticket :** mémoire (08b), décisions sur le monde perçu (08d).

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 08b, `v2-collectif/31`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : calcul en O(n²) par pas acceptable (à mesurer).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs (temps de calcul).

## Tests

- **Unitaires (scène contrôlée) :** adversaire à 2 m dans le dos : non vu ; devant : vu
- **Intégration :** temps de calcul rapporté

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Visibilité calculée et tracée
- [ ] Aucun effet sur le jeu dans ce ticket
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
