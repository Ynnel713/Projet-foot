# 13a: Consignes d'équipe : lecture des styles et structure neutre

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (toutes les équipes jouent aujourd'hui de la même façon). **Catégorie :** données.

**Constat vérifié :** aucune consigne ni aucun style dans `v2engine/` (recherche « style », « consigne », « mentalit » : rien) ; le ticket `v2-coach-et-gestion-de-match/01` (à faire) traduit 5 styles en décalages de mécanismes existants.

**What to build:** Lire les styles du coach (`coaches.coach_styles`, lecture seule, D-V02) et produire une structure de consignes d'équipe (hauteur de bloc, intensité de pressing, largeur, tempo, part de jeu direct, joueurs projetés) avec des valeurs neutres par défaut et le plafond de cumul de la V1 (`_STYLE_MODIFIER_BOUNDS`). Aucun effet dans ce ticket : les consignes sont tracées.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : fondation.

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 13b, 13c, 13d, 13e, 13f, 13g, 13h, 16b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : lecture des styles déjà disponible côté V1.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** coach à 2 styles : consignes cumulées et plafonnées ; sans coach : neutres
- **Intégration :** mesures identiques à graine fixée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Consignes tracées par équipe
- [ ] Aucun effet sur le jeu dans ce ticket
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
