# 05a: Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (aujourd'hui l'issue précède la trajectoire). **Catégorie :** exécution.

**Constat vérifié :** `match.py:479` tire le but au départ du tir (`attempt_shot`) ; un tir « but » file ensuite vers le centre du but sans pouvoir être touché (`match.py:557`, `ball.shot_for`) ; un tir « à côté » est choisi par une part fixe (`SHOT_WIDE_SHARE = 0.64`, `match.py:54` et `492`). La vitesse est la même pour tous (`SHOT_SPEED_MPS`, `match.py:49`).

**What to build:** Le tir part vers le point d'arrivée réel donné par le cadrage du ticket `v2-collectif/35b` (point visé plus écart d'exécution), à la vitesse du ticket `v2-collectif/35a` (30 m/s tant que 35a n'est pas livré). Le ballon est simulé pas à pas comme une passe ; il devient but s'il franchit la ligne entre les poteaux, sortie de but ou corner sinon. Dans ce ticket, le gardien et les défenseurs ne le touchent pas encore (05b, 05c) : seule la décision du but au départ disparaît.

**Hors de ce ticket :** arrêt (05b), contre (05c), hauteur (05f).

**Attributs :** aucun

**Lien avec l'existant :** s'appuie sur `v2-collectif/35b` (à faire) sans le modifier ; remplace la branche de tirage du but livrée au ticket 28a et la part fixe du ticket 29 (tickets livrés non modifiés, nouveau comportement ici).

**Blocked by:** `v2-collectif/35b`.

**Bloque :** 05b, 05c, 05g, 15c.

**Status:** livré (08/11/2026), validé expert + QC

## Constantes (proposées le 08/11/2026, validées par délégation du propriétaire)

| Constante | Valeur | Source |
|---|---|---|
| `SHOT_FLIGHT_RESOLUTION` (interrupteur) | coupé (`False`) | point de vigilance du ticket : sans l'arrêt du gardien (05b), tout tir cadré entre. Le 05b l'allume, mesure à l'appui |
| Vitesse du tir | 30 m/s (`SHOT_SPEED_MPS`, inchangée) | en attendant le 35a ; réel : 25 à 35 m/s pour une frappe appuyée (ordre de grandeur, non sourcé) |
| Écart d'exécution | lois du 35b (0,18 rad, visée à 1 m, pression, note), tirées au départ en largeur et en hauteur | aucune nouvelle constante |
| Dévissé | `SHANK_SHARE` x (écart relatif)² x P(hors du cadre) | même part des tirs ratés qu'au 35b |

Pas de chiffre réel nouveau : le ticket remplace un tirage par une trajectoire, sans nouvelle grandeur à caler.

## Réalisation

- `shooting.draw_shot_error` : écarts d'angle (largeur, hauteur) tirés au départ, ou `None` pour un dévissé.
- `match._step_ball`, interrupteur allumé : ni `attempt_shot` ni `classify_unscored` ; le ballon part vers l'axe du but tourné de l'écart, à 30 m/s, freiné comme une passe ; personne ne le touche (`BallState.shot_flight`). Sur la ligne : but entre les poteaux et sous la barre (hauteur = visée + distance x pente), sinon sortie de but (ou touche). Trace : issue « en vol » au départ, remplacée sur la ligne (but, à côté, au-dessus).
- Interrupteur coupé : jeu inchangé (dévissé regroupé dans `match._shank`, sans changement de comportement).
- Tests : `tests/test_v2engine_tir_en_vol.py` (6). Suite complète : 2 582 passés, 14 désélectionnés (2 576 après le 28c, + 6).

## Mesures (08/11/2026, graine d'audit, `.scratch/v2-realisme/mesures/05a-*`)

- **Interrupteur coupé** : 2 matchs, moteur du commit `db5e497` (`05a-avant.json`) contre moteur du ticket (`05a-det1.json`, `05a-det2.json`) : tous les indicateurs identiques, seul le temps de calcul diffère. Jeu inchangé, déterminisme vérifié.
- **Interrupteur allumé** (20 matchs, 4 lots de 5, `05a-on*.json`) : 12,0 à 13,8 buts par match ; conversion 25 à 32 %, égale à la part de tirs cadrés, puisque personne n'arrête le ballon. C'est le risque du point de vigilance, mesuré : l'interrupteur reste coupé jusqu'au 05b.
- **Limite du banc, pour le 05b** : `measure_v2` compte les tirs par `attempt_shot` ; interrupteur allumé, « tirs par équipe » et « face-à-face : tirs » tombent à 0. À recâbler sur la trace des tirs quand le 05b allumera l'interrupteur.

**Point de vigilance :** tant que 05b n'est pas livré, le taux de buts monte : livrer 05a et 05b ensemble ou derrière un interrupteur de configuration, mesure à l'appui.

## Estimation

| Poste | Estimé | Réel |
|---|---|---|
| Analyse et compréhension du code | 30 min | 35 min |
| Développement | 50 min | 35 min |
| Tests unitaires et comportementaux | 30 min | 15 min |
| Intégration et vérifications | 25 min | 30 min |
| **Total (travail effectif)** | **2 h 15** | **1 h 55** (− 15 %, durée estimée, non chronométrée) |

Confiance : moyenne. Hypothèses : le point d'arrivée de 35b existe ; la branche `shot_for` est supprimée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir visant l'intérieur du poteau : but ; visant 1 m à l'extérieur : sortie de but ; aucune décision de but avant l'arrivée sur la ligne
- **Intégration :** trace : la trajectoire du ballon va du tireur au point d'arrivée

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Plus aucun tirage du but au départ (test de garde sur `attempt_shot` dans la résolution)
- [x] Issue déterminée par le point de franchissement de la ligne
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 08/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (un passage, empreinte 7b6beca0) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-realisme/05a/cloture`).
- Réserve A1 (registre des estimations non tenu) : acceptée et traitée (ligne ajoutée à `docs/agents/suivi-estimations.md`).
- Réserve A2 (le but reste tiré au départ en jeu réel, l'interrupteur étant coupé) : acceptée ; reportée au 05b (allumer l'interrupteur, retirer l'ancienne branche, test de garde sans monkeypatch).
- Réserve A3 (trace des occasions et `measure_v2` lisent l'issue provisoire « en vol », interrupteur allumé) : acceptée ; reportée au 05b.
- Facultatif A4 (tir mort avant la ligne ou coupé par la mi-temps reste « en vol », hauteur linéaire sans gravité, cases non cochées) : cases cochées ; le reste au 05b et au 05f.
- Réserves acceptées par le propriétaire : délégation permanente du 05/11/2026 (« Considère que je valide automatiquement toutes tes recommandations et celles des expert ») et lancement de la clôture du 08/11/2026 (« Oui »).
