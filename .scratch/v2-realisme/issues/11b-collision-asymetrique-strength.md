# 11b: Collision asymétrique : Strength

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (le plus fort pousse le plus faible). **Catégorie :** physique.

**Constat vérifié :** la poussée est partagée à moitié quel que soit le joueur (`match.py:130-132`) ; Strength n'est lue que dans le tacle.

**What to build:** Répartir la correction de position et de vitesse selon un poids de contact qui dépend de Strength (courbe partagée) ; le joueur le plus faible est plus déplacé.

**Attributs :** Strength (duel de contact)

**Blocked by:** 11a (Collision : la vitesse change aussi, pas seulement la position).

**Bloque :** 04i, 11c, 12c, 15b, 16c.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : pas de masse corporelle dans la base : Strength seule.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Strength 90 contre 40 : déplacement subi au moins deux fois plus faible pour le plus fort (valeur validée)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de Strength mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
