# 06a: xG après frappe : la qualité d'exécution mesurée

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (sépare l'occasion, l'exécution et le gardien). **Catégorie :** mesure.

**Constat vérifié :** le ticket `v2-collectif/28c` (à faire) crée l'xG neutre (`occasion_xg`, étape 0) ; rien ne mesure la qualité de la frappe une fois partie (point d'arrivée, vitesse).

**What to build:** Pour chaque tir non contré, calculer un xG après frappe : chance qu'un gardien moyen, placé où est le vrai gardien, n'arrête pas un ballon arrivant à ce point à cette vitesse (même modèle que 05b, gardien neutre). Tracer xG neutre, xG après frappe et issue sur chaque tir.

**Attributs :** aucun

**Lien avec l'existant :** complète `v2-collectif/28c` (étape 0) sans le modifier.

**Blocked by:** 05b (Arrêt : le gardien atteint ou non le ballon); `v2-collectif/28c`; 05h (Allumer le tir physique, découpé du 05b le 08/11/2026).

**Bloque :** 05e, 06b.

**Status:** livré (09/11/2026), validé expert + QC

## Constantes et définitions (proposées le 09/11/2026, validées par délégation du propriétaire ; décision D-V12)

- **xG neutre** (absent : le 28c ne l'a pas réalisé et renvoyait la question au 06a ; rattaché ici) : chance de but d'un tireur moyen face à un gardien moyen, à la même place et dans la même situation (adversaires, position du gardien, contre compris) : `shooting.occasion_quality` avec les notes neutres (`shooting.neutral_xg`).
- **xG après frappe** : chance qu'un gardien moyen, placé où est le vrai gardien, n'atteigne pas un ballon passant à cet écart après ce temps de vol (portée `keeper_reach_m` du 05b), avec une incertitude de portée logistique `PSXG_SPREAD_M` = 0,3 m (dispersion de la portée d'un gardien : non trouvée, ordre de grandeur) ; 0 pour un tir hors du cadre ou dévissé, 1 pour un tir cadré sans gardien ; non défini pour un tir contré et un penalty.

Délégation : « Considère que je valide automatiquement toutes tes recommandations et les conseils d'experts » (09/11/2026).

## Estimation

| Poste | Estimé | Réel |
|---|---|---|
| Analyse et compréhension du code | 25 min | 20 min |
| Développement | 45 min | 30 min |
| Tests unitaires et comportementaux | 30 min | 20 min |
| Intégration et vérifications | 20 min | 30 min |
| **Total (travail effectif)** | **2 h** | **1 h 40** (- 17 %, durée estimée, non chronométrée) |

Confiance : moyenne. Hypothèses : le modèle d'arrêt neutre de 05b est réutilisable sans tirage.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir en pleine lucarne : xG après frappe proche de 1 ; tir sur le gardien : proche de 0 ; tir non cadré : 0
- **Comportementaux (profils comparés) :** Finishing 99 contre 11, mêmes positions : xG neutre identique, xG après frappe plus élevé

## Réalisation

- `shooting.neutral_xg`, `shooting.post_shot_xg`, `PSXG_SPREAD_M` ; `ShotEvent.xg` et `ShotEvent.post_shot_xg` (`v2engine/trace.py`) : chaque tir trace xG neutre, xG après frappe et issue. Renseignés dans `match` : au départ (xG neutre ; dévissé, hors cadre ou sans gardien : xG après frappe 0 ou 1), au jugement du gardien (`_keeper_reaches`), effacé au contre (`_blocked`). Lecture seule : aucun tirage ajouté, jeu inchangé.
- Banc : xG neutre et xG après frappe par match et par tir (`scripts/v2_indicators.py`, `scripts/measure_v2.py`).
- Tests : `tests/test_v2engine_xg_apres_frappe.py` (6) : 0,5 au bord de la portée ; pleine lucarne à 8 m au-dessus de 0,9 ; tir sur le gardien sous 0,05 ; tir à côté à 0 avec xG neutre tracé ; tir contré sans xG après frappe ; Finishing 99 contre 11, mêmes positions : xG neutre identique, xG après frappe plus élevé.

## Mesures (09/11/2026, graine d'audit, `.scratch/v2-realisme/mesures/06a-*`, moyenne de 10 lots de 5 matchs)

- **Jeu inchangé** : les 10 lots sont identiques à ceux du 05d (`05d-on*`) hors indicateurs xG ; déterminisme : `06a-on0.json` contre `06a-det2.json` identiques.
- **xG neutre** : 2,97 par match, 0,062 par tir ; **xG après frappe** : 4,23 par match, 0,110 par tir non contré ; **buts** : 3,92 par match (penaltys compris, sans xG). L'xG neutre sous-estime les buts de la résolution physique : écart à corriger au 05e (évaluation du tir alignée sur la résolution), qu'il mesure désormais.

## Acceptance criteria

- [x] Trois valeurs tracées par tir
- [x] xG neutre indépendant du tireur (test)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 09/11/2026, premier passage : expert APPROVED_WITH_RESERVATIONS (empreinte e292ea63) ; anomalie facultative A2 (commentaire de `block_exit_deg` déplacé sur `post_shot_xg` dans `trace.py`) corrigée, suite relancée (2 608 passés).
- 09/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (second passage, empreinte a1ef8c91) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-realisme/06a/cloture`). Suite complète : 2 608 passés, 14 désélectionnés.
- Réserve A1 (xG après frappe non calibré sur le moteur : + 0,31 ± 0,12 but par match, environ 8 %, à gardien neutre et issue déterministe ; cause : étalement logistique de 0,3 m sur un seuil net) : acceptée ; reportée au `06b` comme préalable à toute exploitation de l'indicateur.
- Facultatifs : A3 (gardien remis aux notes neutres dans `rivals` sans effet) et A4 (nom du test « pleine lucarne », hauteur sans effet sur la portée en 2D) : non traités.
- À surveiller : écart xG neutre / buts (2,97 contre 3,92 par match), à résorber au 05e.
- Réserves acceptées par le propriétaire : « Considère que je valide automatiquement toutes tes recommandations et les conseils d'experts » (09/11/2026, lancement de la série 05h, 05c, 05d, 06a).
