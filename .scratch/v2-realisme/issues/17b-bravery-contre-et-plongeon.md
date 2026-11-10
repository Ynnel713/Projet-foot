# 17b: Bravery : se jeter pour contrer, plonger dans les pieds

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (accepter le contact risqué change le nombre de contres). **Catégorie :** décision.

**Constat vérifié :** Bravery n'est lue nulle part ; le contre de tir dépend seulement de la géométrie (`shooting.BLOCK_CHANCE`).

**What to build:** Bravery règle la tendance à se jeter devant un tir (portée de contre allongée dans 05c) et, pour le gardien, à plonger dans les pieds en face-à-face (03e) ; contrepartie : risque de blessure (`v2-attributs-restants/09b`).

**Attributs :** Bravery

**Blocked by:** 05c (Contre : le défenseur touche réellement le tir); 03e (Gardien : fermer l'angle dans un face-à-face).

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : moyenne. Hypothèses : pas de lien avec la réussite du contre une fois au contact.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Bravery 99 contre 11 : plus de tirs contrés, à positions égales

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de Bravery mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Renvoi de la garde probabiliste (10/11/2026, ticket `v2-realisme/19c`)

Le contre ne lit aucune note du défenseur (`shooting.BLOCK_CHANCE`). Test d'écart connu : `test_known_gap_the_block_reads_no_defender_rating` (`tests/test_v2engine_garde_probabiliste.py`). Quand Bravery agira sur le contre, retirer ce test et ajouter le contre aux résolutions gardées.
