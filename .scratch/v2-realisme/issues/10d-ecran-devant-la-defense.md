# 10d: Protection de l'axe : le milieu récupérateur fait écran

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (l'axe devant la surface doit rester fermé quand le ballon est sur un côté). **Catégorie :** placement.

**Constat vérifié :** aucun rôle d'écran : la couverture ferme l'axe seulement derrière le porteur ; les compensations ne visent que les places des DC, LB et RB (`defense.py:108`).

**What to build:** Sans ballon, le rôle « milieu récupérateur » (02c) se place entre le ballon et le centre de son but, devant la ligne défensive, quand le ballon est sur un côté ; il quitte cette place seulement pour un rôle attribué (presseur, marqueur).

**Attributs :** aucun

**Blocked by:** 02e (Place de référence sans ballon selon le rôle).

**Bloque :** 10i, 10j.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : priorité des rôles inchangée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ballon dans le couloir droit : le récupérateur est entre ballon et axe du but, devant la ligne

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Passes adverses reçues dans l'axe devant la surface en baisse mesurée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
