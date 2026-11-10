# 20e: Le bloc et le pressing suivent ce que les joueurs peuvent encore donner

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (une équipe épuisée recule et presse moins, sans règle « à la 70e »). **Catégorie :** décision.

**Constat vérifié :** hauteur du bloc et déclenchement du pressing (`bloc.py`, `defense.py`) ne lisent pas l'état physique : une équipe fatiguée garde la même hauteur de ligne et presse de la même façon.

**What to build:** Aucun seuil : la ligne et le presseur lisent la capacité restante (vitesse atteignable, réserve) dans les calculs qu'ils font déjà (temps d'arrivée du presseur, couverture de la profondeur). Le bloc recule et le pressing se raréfie quand les joueurs n'arrivent plus à temps. Le style Pressing (13b) peut demander de maintenir l'intensité : l'équipe s'use plus vite (12e) et ouvre des espaces en fin de match.

**Attributs :** aucun nouveau (Work Rate garde son rayon : l'effort de base).

**Blocked by:** 12e, 10a, 10c, 13b.

**Bloque :** `v2-collectif/22b`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : les temps d'arrivée du pressing lisent déjà la vitesse ; il suffit qu'elle soit la vitesse atteignable.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Comportementaux (profils comparés) :** même équipe, réserve pleine puis basse : hauteur de ligne et part des pressings déclenchés
- **Statistiques (séries de matchs) :** 50 matchs : hauteur du bloc par tranche de 15 minutes ; espaces entre les lignes après la 75e

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Recul du bloc et baisse du pressing qui émergent de la capacité restante, sans seuil codé
- [ ] Une équipe qui presse fort tout le match finit plus fatiguée et concède plus d'occasions après la 75e (sens mesuré)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
