# 11d: Le tacle selon l'angle d'approche et la vitesse relative

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un tacle par derrière ou à contre-courant n'a pas la même issue). **Catégorie :** exécution.

**Constat vérifié :** `duel.tackle_success_probability` (`duel.py:58`) ne lit que Tackling, Strength et Balance ; ni angle, ni vitesse.

**What to build:** La réussite et le risque de faute du tacle dépendent de l'angle entre l'approche du tacleur et le cap ou la course du porteur (de face, de côté, par derrière) et de leur vitesse relative ; par derrière : réussite plus faible et faute plus probable.

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 11e, 21b (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : facteurs par angle : valeurs proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même duel de face, de côté, par derrière : réussite décroissante, faute croissante
- **Statistiques (séries de matchs) :** 50 matchs : fautes par match (repère 21-26, indicatif)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de l'angle mesuré en scène
- [ ] Fautes rapportées
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
