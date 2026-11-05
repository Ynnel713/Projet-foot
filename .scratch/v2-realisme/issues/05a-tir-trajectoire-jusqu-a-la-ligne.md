# 05a: Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (aujourd'hui l'issue précède la trajectoire). **Catégorie :** exécution.

**Constat vérifié :** `match.py:479` tire le but au départ du tir (`attempt_shot`) ; un tir « but » file ensuite vers le centre du but sans pouvoir être touché (`match.py:557`, `ball.shot_for`) ; un tir « à côté » est choisi par une part fixe (`SHOT_WIDE_SHARE = 0.64`, `match.py:54` et `492`). La vitesse est la même pour tous (`SHOT_SPEED_MPS`, `match.py:49`).

**What to build:** Le tir part vers le point d'arrivée réel donné par le cadrage du ticket `v2-collectif/35b` (point visé plus écart d'exécution), à la vitesse du ticket `v2-collectif/35a` (30 m/s tant que 35a n'est pas livré). Le ballon est simulé pas à pas comme une passe ; il devient but s'il franchit la ligne entre les poteaux, sortie de but ou corner sinon. Dans ce ticket, le gardien et les défenseurs ne le touchent pas encore (05b, 05c) : seule la décision du but au départ disparaît.

**Hors de ce ticket :** arrêt (05b), contre (05c), hauteur (05f).

**Attributs :** aucun

**Lien avec l'existant :** s'appuie sur `v2-collectif/35b` (à faire) sans le modifier ; remplace la branche de tirage du but livrée au ticket 28a et la part fixe du ticket 29 (tickets livrés non modifiés, nouveau comportement ici).

**Blocked by:** `v2-collectif/35b`.

**Bloque :** 05b, 05c, 05g, 15c.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** tant que 05b n'est pas livré, le taux de buts monte : livrer 05a et 05b ensemble ou derrière un interrupteur de configuration, mesure à l'appui.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Hypothèses : le point d'arrivée de 35b existe ; la branche `shot_for` est supprimée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir visant l'intérieur du poteau : but ; visant 1 m à l'extérieur : sortie de but ; aucune décision de but avant l'arrivée sur la ligne
- **Intégration :** trace : la trajectoire du ballon va du tireur au point d'arrivée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Plus aucun tirage du but au départ (test de garde sur `attempt_shot` dans la résolution)
- [ ] Issue déterminée par le point de franchissement de la ligne
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
