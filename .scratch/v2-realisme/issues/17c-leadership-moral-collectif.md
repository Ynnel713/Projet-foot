# 17c: Leadership : amortir la baisse collective après un but encaissé

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (seul attribut mental sans ticket dédié). **Catégorie :** décision.

**Constat vérifié :** Leadership n'est lu nulle part et n'a pas de ticket dédié (mentionné dans `v2-collectif/21`, `v2-coach-et-gestion-de-match/02` et la carte, phase 10).

**What to build:** Après un but encaissé, une baisse temporaire de concentration collective (ticket 21, Concentration) est amortie selon le meilleur Leadership présent sur le terrain ; aucun effet sur l'exécution.

**Attributs :** Leadership

**Blocked by:** `v2-collectif/21`.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : faible. Hypothèses : la baisse après un but existe au ticket 21.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** même équipe, capitaine Leadership 99 contre 11 : baisse après un but plus courte

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de Leadership mesuré en scène A/B, sur l'équipe et pas sur le joueur seul
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
