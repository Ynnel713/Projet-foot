# 05d: Déviation du ballon au contact d'un corps

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (contres, parades et ballons repoussés doivent partir de façon plausible). **Catégorie :** physique.

**Constat vérifié :** après un contre, le ballon repart avec une déviation tirée entre -60 et +60° à la moitié de la vitesse (`match.SHOT_DEFLECTION_DEG`) ; après une parade, selon des angles tirés (`shooting.parry_velocity`) ; après un contrôle raté, ±20 à 60° (`possession.missed_control_velocity`).

**What to build:** Une fonction commune de déviation au contact : la direction de sortie dépend du point d'impact sur le corps (décalage latéral par rapport à l'axe du ballon) et d'un coefficient de restitution ; une part aléatoire bornée reste. Utilisée par le contre (05c) ; la parade et le contrôle raté peuvent l'adopter plus tard sans changer leurs tickets.

**Attributs :** aucun

**Blocked by:** 05c (Contre : le défenseur touche réellement le tir).

**Bloque :** 05g, 15e.

**Status:** livré (09/11/2026), validé expert + QC

## Constantes (proposées le 09/11/2026, validées par délégation du propriétaire)

| Constante | Valeur | Source |
|---|---|---|
| `DEFLECTION_RESTITUTION` | 0,4 | coefficient de restitution ballon contre corps humain : non trouvé ; ordre de grandeur 0,3 à 0,5 (corps mou, jambe qui amortit) |
| `DEFLECTION_NOISE_DEG` | ± 15° | surface du corps irrégulière, pas de rotation du ballon avant le 14c ; ordre de grandeur |

Le corps (ou la jambe tendue) est un cylindre vertical de la portée du défenseur : la composante normale de la vitesse au point d'impact est renvoyée avec la restitution, la tangentielle est gardée. Remplace la déviation tirée entre - 60 et + 60° à la moitié de la vitesse (`match.SHOT_DEFLECTION_DEG`, retirée). Délégation : « Considère que je valide automatiquement toutes tes recommandations et les conseils d'experts » (09/11/2026).

## Estimation

| Poste | Estimé | Réel |
|---|---|---|
| Analyse et compréhension du code | 20 min | 10 min |
| Développement | 45 min | 35 min |
| Tests unitaires et comportementaux | 30 min | 25 min |
| Intégration et vérifications | 20 min | 30 min |
| **Total (travail effectif)** | **1 h 55** | **1 h 40** (- 13 %, durée estimée, non chronométrée) |

Confiance : moyenne. Hypothèses : restitution et dispersion proposées ; pas de rotation du ballon (14c).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** contact dans l'axe : ballon renvoyé vers le tireur ; contact excentré : déviation du côté de l'impact

## Réalisation

- `possession.deflect(velocity, ball_at, body_at, radius_m, rng)` : fonction commune de déviation au contact d'un corps (décalage latéral du ballon par rapport au centre du corps, restitution, écart borné tiré dans le flux du geste). La parade et le contrôle raté pourront l'adopter sans changer leurs tickets.
- `match._blocked` : un tir contré repart de ce point avec `deflect` (flux `TIR`) ; le point de contact est celui où le ballon entre dans la portée du défenseur (réserve facultative A1 de l'expert du 05c : il était pris à l'entrée du cercle de 1 m même quand seul le corps comptait) ; angle de sortie tracé (`ShotEvent.block_exit_deg`) et réparti par le banc (`scripts/v2_indicators.py`, `scripts/measure_v2.py`).
- Tests : `tests/test_v2engine_deviation.py` (5) : contact dans l'axe, ballon renvoyé vers le tireur à 0,4 de sa vitesse ; contact excentré, dévié du côté de l'impact ; ballon effleuré presque inchangé ; plus l'impact est central, plus le ballon revient ; contre en match à 2 m dans l'axe tracé à 1,59 m du tireur et renvoyé.

## Mesures (09/11/2026, graine d'audit, `.scratch/v2-realisme/mesures/05d-*`, moyenne de 10 lots de 5 matchs)

- **Sortie des tirs contrés** (angle avec la direction du tir) : 0-45° (effleuré, il continue) 13,6 %, 45-90° 32,4 %, 90-135° 31,9 %, 135-180° (renvoyé vers le tireur) 22,1 %.
- Contrés 18,8 % (19,6 % au 05c), conversion 8,3 %, 3,9 buts par match ; corners 8,6 → 6,6 par match (moins de contres filent derrière la ligne), à surveiller (repère réel environ 10 par match).
- **Déterminisme** : lot 0 joué deux fois (`05d-on0.json`, `05d-det2.json`) : identiques.

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Fonction unique, testée en scène
- [x] Contres : répartition des directions de sortie rapportée
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 09/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (un passage, empreinte 0e13b2e8) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-realisme/05d/cloture`). Suite complète : 2 602 passés, 14 désélectionnés.
- Réserve A1 (géométrie du contact prise sur la position du défenseur en fin de pas, alors que la détection suit son mouvement : côté de la déviation incertain pour un défenseur qui se jette dans l'axe) : acceptée ; correctif (position du joueur à l'instant du contact) à faire avant que la parade ou le contrôle raté n'adoptent `deflect`, noté au `05g`.
- Réserve A2 (corners 8,6 → 6,6 par match, repère réel environ 10) : acceptée ; suivi rattaché au `05g` (validation des tirs), sans compenser ailleurs avant d'en traiter la cause (modèle 2D, pas de déviation verticale).
- Facultatif A3 (placement de `deflect` dans `possession.py`) : laissé, réutilisation prévue par le contrôle raté.
- Réserves acceptées par le propriétaire : « Considère que je valide automatiquement toutes tes recommandations et les conseils d'experts » (09/11/2026, lancement de la série 05h, 05c, 05d, 06a).
