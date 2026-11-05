# 16d: Corner : exécution (Corners)

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (la qualité du tireur fait le danger du corner). **Catégorie :** exécution.

**Constat vérifié :** Corners n'est lu nulle part ; les centres variés (`v2-attributs-restants/11`, à faire) donnent les types de ballon.

**What to build:** Le tireur (meilleur Corners de l'équipe) choisit la zone visée et le type de ballon (rentrant, sortant, court) ; Corners règle la précision ; trajectoire avec hauteur (`v2-hauteur-ballon/02a`) et effet (14b).

**Attributs :** Corners

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/02b` : exécution.

**Blocked by:** 16a (Corner : placement offensif); 14b (Effet latéral du ballon (enroulé)); `v2-attributs-restants/11`.

**Bloque :** 16g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : types de centres du ticket 11.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Corners 99 contre 11 : ballons arrivant dans la zone visée plus souvent

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de Corners mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
