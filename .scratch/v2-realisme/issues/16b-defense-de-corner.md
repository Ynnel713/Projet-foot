# 16b: Corner : défense en zone, individuelle ou mixte

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (l'organisation défensive décide de la plupart des corners). **Catégorie :** placement.

**Constat vérifié :** voir 16a.

**What to build:** Sur un corner contre lui, l'équipe défend en zone (zones du 10f étendues au petit rectangle), en individuelle (marquage du plus apte) ou en mixte, selon une consigne d'équipe (13a, neutre : mixte).

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/02b` : défense.

**Blocked by:** 16a (Corner : placement offensif); 10f (Défense de la surface : premier poteau, second poteau, point de penalty, retrait); 13a (Consignes d'équipe : lecture des styles et structure neutre).

**Bloque :** 16c, 16g, 16i (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : consigne lue dans 13a.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** corner : en zone, chaque zone tenue ; en individuelle, chaque attaquant dangereux marqué

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Trois organisations tracées
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
