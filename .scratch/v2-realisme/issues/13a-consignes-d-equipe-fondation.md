# 13a: Consignes d'équipe : lecture des styles et structure neutre

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (toutes les équipes jouent aujourd'hui de la même façon). **Catégorie :** données.

**Constat vérifié :** aucune consigne ni aucun style dans `v2engine/` (recherche « style », « consigne », « mentalit » : rien) ; le ticket `v2-coach-et-gestion-de-match/01` (à faire) traduit 5 styles en décalages de mécanismes existants.

**What to build:** Lire les styles du coach (`coaches.coach_styles`, lecture seule, D-V02) et produire une structure de consignes d'équipe (hauteur de bloc, intensité de pressing, largeur, tempo, part de jeu direct, joueurs projetés) avec des valeurs neutres par défaut et le plafond de cumul de la V1 (`_STYLE_MODIFIER_BOUNDS`). Aucun effet dans ce ticket : les consignes sont tracées.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-coach-et-gestion-de-match/01` : fondation.

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 13j, 13b, 13c, 13d, 13e, 13f, 13g, 13h, 16b ; 10m1 (ordre décidé par le propriétaire le 26/11/2026).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : élevée. Hypothèses : lecture des styles déjà disponible côté V1.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** coach à 2 styles : consignes cumulées et plafonnées ; sans coach : neutres ; note du coach lue et tracée, absente sans coach
- **Intégration :** mesures identiques à graine fixée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Consignes tracées par équipe
- [ ] Note du coach tracée par équipe (absente sans coach ou note inconnue), sans effet
- [ ] Aucun effet sur le jeu dans ce ticket
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit des styles du coach (26/11/2026)

Source : audit des styles demandé par le propriétaire (26/11/2026). Le plafond global repris de la V1 ne suffit pas : la répartition par phase de jeu, la normalisation par le nombre de styles (budget tactique) et l'arbitrage des couples contradictoires sont confiés au ticket 13j, qui lit la structure produite ici. Ce ticket garde la lecture des styles et la structure neutre ; il lit aussi la note du coach (`coaches.coach_note`) et la trace, sans effet (utilisée par 13k).
