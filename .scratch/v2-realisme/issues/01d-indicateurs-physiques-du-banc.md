# 01d: Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les volumes de course sont le premier symptôme de C5). **Catégorie :** mesure.

**Constat vérifié :** la dernière mesure de distance publiée (ticket 07, 30/10/2026) donne 20,7 km par joueur de champ ; « appels par joueur » 156 à 507 (référence du 26/10/2026) contre 5,5 à 19,2 au réel, avec une définition à confirmer (01c).

**What to build:** Aligner les indicateurs physiques du banc (`scripts/v2_indicators.py`) sur les définitions retenues au 01c : km par joueur de champ et par poste, part du temps et de la distance au-dessus de 19,8 et de 25 km/h, nombre de sprints, appels par joueur selon la définition sourcée. Mesure de référence sur 50 matchs, graine d'audit.

**Attributs :** aucun

**Blocked by:** 01c (Repères de calibration : sources, définitions, compatibilité avec le banc).

**Bloque :** 02h, 03g, 04c, 05g, 07g, 08f, 09a, 12g.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : élevée. Hypothèses : les observateurs du banc exposent déjà positions et vitesses à chaque pas.
Temps machine, non compté : suite complète (environ 40 min) ; mesure de référence sur 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** trajectoires synthétiques (joueur à 20 km/h pendant 10 s, puis à 10 km/h) : distances et temps au-dessus des seuils exacts
- **Statistiques (séries de matchs) :** référence 50 matchs publiée dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [ ] Indicateurs définis par écrit (formule, unité) avant le code
- [ ] Tests sur trajectoires synthétiques
- [ ] Référence 50 matchs publiée, par poste
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
