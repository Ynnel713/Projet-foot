# 05b: Arrêt : le gardien atteint ou non le ballon

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (un arrêt doit dépendre de la position, du temps de réaction et de la portée). **Catégorie :** exécution.

**Constat vérifié :** aujourd'hui un tir non converti et cadré est toujours remis au gardien (`match.py`, `save_outcome`), sans que le gardien ait à atteindre le ballon ; sa position compte seulement comme une part d'angle (`keeper_position_factor`).

**What to build:** Sur le trajet du tir, le gardien intercepte le ballon s'il peut atteindre le point de passage à temps : temps de réaction, puis déplacement latéral et plongeon jusqu'à une portée maximale (valeurs neutres, validées). Atteint : arrêt, avec l'issue du ticket 28b (capté, repoussé, claqué). Non atteint : le ballon continue.

**Hors de ce ticket :** notes du gardien (Reflexes, One on Ones, Handling) : `v2-attributs-restants/03b`.

**Attributs :** aucun

**Lien avec l'existant :** complète `v2-collectif/28b` (issues de l'arrêt, implémenté) sans le modifier.

**Blocked by:** 05a (Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ); 03b (Gardien : placement sur la bissectrice ballon-poteaux).

**Bloque :** 03f, 05e, 05f, 05g, 06a, 16e.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : moyenne. Hypothèses : trajectoire à plat ; la hauteur viendra au 05f.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir à 20 m au centre : arrêté ; tir à 8 m en pleine lucarne latérale : non atteint ; gardien mal placé (03b désactivé) : plus de buts
- **Statistiques (séries de matchs) :** 50 matchs : taux d'arrêt par distance, rapporté sans réglage

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Arrêt décidé par l'atteinte du ballon, tracé avec le temps disponible
- [ ] Taux d'arrêt décroissant avec la proximité et la vitesse du tir (scènes)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Reprises du 05a (réserves de l'expert, 08/11/2026)

- **A2** : allumer `SHOT_FLIGHT_RESOLUTION` et retirer du jeu ouvert la branche `attempt_shot` / `shot_for` / `classify_unscored` ; test de garde sans monkeypatch de l'interrupteur.
- **A3** : `OccasionTracker.update` ferme l'occasion sur l'issue provisoire « en vol » : la fermer quand l'issue se décide sur la ligne (ou relire l'issue définitive) ; `measure_v2` doit compter les tirs depuis la trace, plus par `attempt_shot`. Test : un tir en vol qui marque donne une occasion d'issue « tir : but ».
- **À surveiller** : le tir est freiné comme une passe (environ 15 m/s à l'arrivée d'un tir de 30 m), ce qui donne au gardien plus de temps qu'en réalité tant que le 35a n'est pas livré.
