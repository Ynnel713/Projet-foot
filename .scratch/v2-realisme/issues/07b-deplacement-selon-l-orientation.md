# 07b: Se déplacer de face, de côté ou à reculons

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un défenseur qui recule est plus lent qu'un attaquant qui court face au jeu). **Catégorie :** physique.

**Constat vérifié :** `movement.step` donne la même vitesse maximale quelle que soit la direction par rapport au corps (aucun corps, voir 07a).

**What to build:** La vitesse maximale dépend de l'angle entre la direction de course et le cap : pleine vitesse vers l'avant, réduite en pas chassés, plus réduite à reculons (parts validées). Le joueur choisit de se retourner ou de reculer selon la distance à parcourir.

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 07g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : choix « se retourner ou reculer » : règle simple par distance.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur face au jeu qui doit reculer de 3 m : recule ; de 20 m : se retourne et court
- **Statistiques (séries de matchs) :** 20 matchs : km par poste avant / après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Vitesses par direction documentées
- [ ] Choix tracé
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**12/11/2026, reprise du 07a (réserve facultative A1 de l'expert).** Le cap vise le sens de course au-dessus de `movement.FACING_RUN_SPEED_MPS` (19,8 km/h) et le ballon en dessous, sans hystérésis : quand ce ticket fera lire le cap au jeu, prévoir une bande de quelques dixièmes de m/s ou une pondération continue entre les deux directions (test : vitesse oscillant de ± 0,1 m/s autour du seuil, variation de cap bornée).
