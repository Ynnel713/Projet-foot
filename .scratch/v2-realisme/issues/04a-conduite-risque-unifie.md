# 04a: Conduite : même risque de perte à l'évaluation et à la résolution

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le porteur décide sur un risque qui ne se produit jamais). **Catégorie :** exécution.

**Constat vérifié :** `decision.keep_ball_probability` (`decision.py:233`) donne la chance de garder le ballon en conduisant (Dribbling 55 : 83 % au contact) et sert seulement à évaluer l'option ; en match, la conduite ne perd le ballon que par un tacle, tenté au taux de base de 0,03 par seconde de contact (`duel.py:21`) contre Strength et Balance. Dribbling n'a aucun effet sur l'issue réelle. Mesure du 28b : 52 % des tirs viennent d'une conduite.

**What to build:** Une seule fonction de risque de perte en conduite, appelée par l'évaluation (`decision`) et par la résolution (`match`) : pendant une conduite au contact (pression), une perte est tirée à chaque intervalle de décision avec la probabilité qui a servi à évaluer l'option, rapportée à la durée de l'intervalle. Le tacle existant reste, mais son effet est retiré du risque de perte de conduite pour ne pas compter deux fois.

**Hors de ce ticket :** où part le ballon perdu (04b) ; gestes du duel (04g à 04j).

**Attributs :** Dribbling (garder le ballon en conduite serrée)

**Lien avec l'existant :** fondation commune du ticket `v2-attributs-restants/07a`, qui ajoutera les gestes sur cette fonction.

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 04b, 04c, 04d, 04g, 04i.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Strength et Balance restent au tacle (`v2-attributs-restants/07a`, règle R1) : vérifier que la perte de conduite ne relit pas ces attributs.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : moyenne. Hypothèses : perte modélisée comme un événement par unité de temps au contact ; les volumes de tirs bougeront (à rapporter, pas à régler).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** conduite au contact pendant 2 s, 10 000 tirages : perte observée égale à la perte estimée à 1 point près
- **Comportementaux (profils comparés) :** Dribbling 99 contre 11 au contact : perte observée nettement plus faible
- **Statistiques (séries de matchs) :** 50 matchs : part des tirs après conduite, pertes en conduite par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Une seule fonction appelée par l'évaluation et la résolution (test de garde)
- [ ] Écart perte estimée / observée sous 1 point en scène contrôlée
- [ ] Dribbling agit sur l'issue réelle (scène A/B)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
