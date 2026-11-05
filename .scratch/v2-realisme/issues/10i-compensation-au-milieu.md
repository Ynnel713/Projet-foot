# 10i: Compensation d'un trou au milieu

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un récupérateur aspiré laisse l'axe ouvert). **Catégorie :** décision.

**Constat vérifié :** les compensations ne concernent que les places des postes `DC, LB, RB` (`defense.py:108`).

**What to build:** Étendre la détection de trou à la place du milieu récupérateur (10d) : un trou au milieu est comblé par un relayeur ou, à défaut, un défenseur central si un autre central couvre ; même mécanique que le ticket 09 (temps d'arrivée, Teamwork, un tirage par trou).

**Attributs :** Teamwork (rayon existant : accepter de quitter sa place)

**Lien avec l'existant :** complète `v2-collectif/09` (livré, non modifié).

**Blocked by:** 10d (Protection de l'axe : le milieu récupérateur fait écran).

**Bloque :** 10j.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : cascade limitée à deux niveaux, comme au ticket 09.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** récupérateur sorti presser, attaquant qui entre dans sa zone : un relayeur comble

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Trou au milieu comblé en scène
- [ ] Part du temps avec l'axe devant la surface vide en baisse
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
