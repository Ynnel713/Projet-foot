# 10b: Le défenseur central ne quitte sa ligne que couvert

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un central qui sort sans couverture ouvre la profondeur). **Catégorie :** décision.

**Constat vérifié :** la couverture n'existe que si le porteur est dans la moitié défendue (`defense.py:332`) ; rien n'empêche un central marqueur ou presseur de quitter sa ligne sans couverture.

**What to build:** Un défenseur central ne sort de sa ligne (presser, suivre un décrochage) que si un partenaire couvre sa place (compensation existante ou couverture) ; sinon il garde sa ligne et cède le rôle au suivant.

**Attributs :** aucun

**Blocked by:** 10a (Choix du presseur selon la zone et la responsabilité).

**Bloque :** 10c, 10j.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : réutilise `_compensate`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** attaquant qui décroche, aucun couvreur : le central reste ; couvreur présent : il suit

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Sorties non couvertes des centraux en baisse mesurée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
