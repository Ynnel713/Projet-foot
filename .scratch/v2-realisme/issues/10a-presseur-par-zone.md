# 10a: Choix du presseur selon la zone et la responsabilité

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un défenseur central ne doit pas être aspiré loin de sa ligne). **Catégorie :** décision.

**Constat vérifié :** `defense.py:316-317` : le presseur est le joueur de champ qui arrive le premier sur le porteur, quel que soit son poste ou sa zone (règle de capacité R5).

**What to build:** Restreindre les candidats au pressing à ceux dont la zone de responsabilité (ligne et couloir de leur place de référence) contient le porteur, sauf si aucun d'eux n'arrive dans une marge validée ; à égalité de zone, le premier arrivé.

**Attributs :** aucun

**Lien avec l'existant :** complète `v2-collectif/07` et `08` (livrés, non modifiés) ; à coordonner avec `v2-collectif/27` (à faire).

**Blocked by:** 02e (Place de référence sans ballon selon le rôle).

**Bloque :** 10b, 10j.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : zone définie à partir de la place de référence sans ballon.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** porteur au rond central, DC à 25 m, milieu à 12 m : le milieu presse ; porteur dans la zone du DC : le DC presse
- **Statistiques (séries de matchs) :** 50 matchs : distance moyenne du presseur à sa place de référence par poste

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Zone de responsabilité tracée avec le presseur
- [ ] Défenseurs centraux pressant hors de leur zone en baisse mesurée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
