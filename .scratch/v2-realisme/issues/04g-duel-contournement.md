# 04g: Duel un contre un : le contournement

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (premier geste réel du duel, base de 07a). **Catégorie :** exécution.

**Constat vérifié :** aucun geste de duel : le porteur avance vers un point libre ou subit un tacle (`decision.dribble_options`, `duel.py`).

**What to build:** Face à un défenseur à portée, le porteur peut tenter de le contourner (passer à côté en accélérant) : réussite par Dribbling contre Tackling du défenseur, avec la vitesse relative et l'espace latéral disponible ; réussi, le défenseur est éliminé pour un temps ; raté, le ballon est perdu selon 04b.

**Attributs :** Dribbling (porteur), Tackling (défenseur)

**Lien avec l'existant :** découpe (validée le 05/11/2026) du ticket `v2-attributs-restants/07a` : contournement.

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution).

**Bloque :** 04h, 04j, 21c (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : Decisions choisit le geste par la valeur (même monnaie que le ticket 33).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur arrêté, porteur lancé, espace latéral : contournement tenté et réussi plus souvent qu'avec un défenseur lancé
- **Comportementaux (profils comparés) :** Dribbling 99 contre 11 : plus de contournements réussis à défenseur égal

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Geste tracé et affiché
- [ ] Effet de Dribbling et de Tackling mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
