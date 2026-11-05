# 04d: Vitesse de conduite selon Dribbling et la pression

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un bon dribbleur va plus vite balle au pied). **Catégorie :** physique.

**Constat vérifié :** `DRIBBLE_SPEED_FACTOR = 0.85` (`decision.py:28`) : même part de la vitesse maximale balle au pied pour tous, avec ou sans adversaire.

**What to build:** La part de vitesse maximale balle au pied dépend de Dribbling (conduite serrée) et baisse au contact d'un adversaire. La valeur de l'option de conduite (espace atteint) utilise la même vitesse.

**Attributs :** Dribbling (vitesse balle au pied ; Pace reste la vitesse maximale)

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution).

**Bloque :** 04e.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : courbe partagée de `attributes`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** au contact : vitesse plus faible que sans adversaire
- **Comportementaux (profils comparés) :** Dribbling 99 contre 11, même Pace : vitesse moyenne balle au pied plus élevée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Même vitesse utilisée à l'évaluation et en mouvement (test)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
