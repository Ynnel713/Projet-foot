# 03c1: Gardien : relance au pied (Kicking)

**Découpé du ticket `03c` le 22/11/2026** (recommandation de Claude sous la délégation du propriétaire : l'ensemble, estimé à 2 h 40 en confiance faible, dépassait le seuil de 2 h ; la relance à la main demande un état « ballon en main » qui n'existe pas). Gardien de référence : Kicking 60, médiane des 50 gardiens notés de Ligue 1 de la base (de 35 à 80) ; un gardien sans note ou sans cette colonne vaut la référence.

**What to build:** Kicking (exécution, ADR 0002 : le choix reste à la décision, Vision et Decisions) règle la qualité des longs ballons du gardien au pied : relance longue en l'air en jeu (`v2-collectif/15a`) et sortie de but jouée long (au-delà de `restart.LONG_RESTART_M`). Précision : Kicking remplace Passing dans la difficulté d'une passe en l'air ; une sortie de but jouée long devient une passe en l'air (aujourd'hui sa précision suit la difficulté d'une passe au sol, 1,8 point par mètre, alors qu'elle vole). Distance : la vitesse de frappe plafond du gardien dépend de Kicking, et la portée envisagée par la décision la suit. Passes courtes au sol : Passing, inchangé.

**Attributs :** Kicking.

**Blocked by:** `v2-collectif/15a`, `v2-realisme/25b` (livrés).

**Bloque :** `03c2` ; `v2-collectif/22a`.

**Status:** livré (23/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 20 min |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Temps machine, non compté : série réelle de 50 matchs, série « avant » de 30 matchs, deux séries forcées de 30 matchs (Kicking 40 et 80), environ 2 h 20 ; suite complète (16 min).

**Constantes** (proposées au propriétaire le 23/11/2026, délégation permanente « Je valide automatiquement toutes tes recommandations et les avis d'expert ») : référence 60 ; précision d'un long ballon du gardien en l'air : Kicking à la place de Passing, contre la difficulté d'une passe en l'air (`possession.LONG_BALL_DIFFICULTY_PER_M`, 0,8 point par mètre, inchangé) ; vitesse de frappe plafond 30 m/s à 60 (`MAX_PASS_MPS`, inchangé à la référence) + 0,1 m/s par point, bornée à 26,5-34 m/s : portée 52,9 m à 35, 57,8 m à 60, 61,7 m à 80, 65,4 m à 99 ; la relance longue envisagée par la décision va jusqu'à cette portée ; une sortie de but (ou une remise du gardien) jouée long est une passe en l'air à l'exécution (précision Kicking, vol aérien, portée). Le choix du receveur d'une remise (`restart.restart_target`) reste celui d'avant (ADR 0002 : Kicking ne règle que la qualité du geste). Essais abandonnés en cours de ticket : le juger comme une passe en l'air sans la retombée disputée donnait 81 % de sorties de but longues (environ 62 % avant) ; avec la retombée comptée comme en jeu (`decision.LONG_BALL_WON`, 0,5), 30 % et des buts + 1,04 [+ 0,28 ; + 1,80] par match sur 50 matchs, parce que le moteur, sans duel aérien, garde 85 % de ses longs ballons : le choix court ou long des remises du gardien est renvoyé au ticket de suite `v2-collectif/15e`, après le duel aérien (`v2-realisme/15b`). Repères réels : dégagement et sortie de but d'un gardien de haut niveau, 50 à 65 m (ordre de grandeur, relation note-distance non trouvée).

**Critères chiffrés** (posés avant le code) : gardien sans note : précision et portée identiques à un gardien à 60 (scènes) ; scène : précision d'un long ballon croissante de Kicking 40 à 80, Passing sans effet sur elle, passes au sol et joueurs de champ inchangés ; portée : partenaire à 61 m envisagé à 80, pas à 60 ; séries forcées (30 matchs, mêmes graines) : longueur moyenne des longs ballons du gardien plus grande et part gardée par son équipe plus haute à 80 qu'à 40 ; série réelle : buts par match avec intervalle ; part longue des sorties de but inchangée au bruit près (choix non modifié).

## Acceptance criteria

- [x] Constantes produit et critères chiffrés validés par le propriétaire avant le code (délégation)
- [x] Gardien sans note : précision et portée identiques à un gardien à 60 (scènes)
- [x] Kicking : distance des longs ballons mesurablement liée à l'attribut (scène et séries forcées)
- [~] Kicking : précision liée à l'attribut — prouvée en scène ; en match, la part gardée par son équipe n'en dépend pas (85,3 % à 40, 84,5 % à 80) : sans duel aérien, le moteur garde 85 % des longs ballons quelle que soit leur précision (`v2-realisme/15b`)
- [x] Passes au sol du gardien et longs ballons des joueurs de champ inchangés (Passing)
- [x] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Résultats (23/11/2026)

- Code : `possession.kicking` (référence 60 sans note ou sans la colonne), `keeper_kick`, `kick_speed_cap_mps`, `keeper_kick_reach_m` ; `pass_accuracy_probability` lit Kicking pour un long ballon du gardien en l'air ; `_launch_speed` et `max_pass_reach_m` prennent un plafond ; `pass_aim` et `pass_velocity` l'appliquent ; `decision.evaluate_options` envisage la relance longue du gardien jusqu'à sa portée ; `match._play_restart` joue une remise longue du gardien en passe en l'air (précision Kicking, vol aérien, portée) ; choix du receveur inchangé.
- Scènes (`tests/test_v2engine_relance_au_pied.py`, 4 cas) : référence et constantes (plafond 30 m/s à 60, 32 à 80, 27,5 à 35 ; portée 52,9 / 57,8 / 61,7 / 65,4 m à 35 / 60 / 80 / 99) ; précision croissante de 40 à 80, Passing sans effet sur un long ballon du gardien, passe au sol et joueur de champ inchangés ; partenaire à 61 m envisagé à 80, pas à 60, frappe au-delà de 30 m/s ; sortie de but longue jouée en l'air, même receveur. Garde des attributs : scène « relance longue » (Kicking 11 contre 99, divergence trouvée).
- Séries (mêmes graines ; avant : code de `b90ea8c`) :

| Série | Buts/match | Longs ballons/gardien/match | Longueur moyenne (90e centile) | Gardés par son équipe | Sorties de but jouées long |
|---|---|---|---|---|---|
| avant (30 matchs) | 4,33 | 4,20 | 40,5 m (54,0) | 84,0 % | 62,3 % |
| réelle (50 matchs) | 4,42 | 4,36 | 41,4 m (53,9) | 85,8 % | 57,7 % |
| Kicking forcé à 40 (30 matchs) | 4,67 | 4,03 | 40,4 m (51,6) | 85,3 % | 60,8 % |
| Kicking forcé à 80 (30 matchs) | 3,63 | 4,27 | 42,0 m (57,3) | 84,5 % | 53,2 % |

  Écart apparié des buts : réelle contre avant (50 matchs, avant = `03b3b-reel`, même code) + 0,20 [− 0,47 ; + 0,87], dans le bruit ; 80 contre 40 : − 1,03 [− 1,71 ; − 0,35] (moins de longs ballons perdus en route, cause non décomposée).
- Essais abandonnés (choix du receveur d'une remise jugé en l'air) : sans la retombée disputée, 81 % de sorties de but longues ; avec elle (0,5), 30 % et buts + 1,04 [+ 0,28 ; + 1,80] sur 50 matchs. Choix restauré (ADR 0002), suite au ticket `v2-collectif/15e`, après le duel aérien.
- Suite complète : 3 559 passés, 0 ignoré, 14 désélectionnés (3 554 + 5 : 4 cas nouveaux, 1 dans la garde des attributs). Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes (`d01f4ae7…`, `7ca5dd39…`).
- Durée réelle : environ 2 h 10 (analyse 20, développement 35, tests 30, intégration et vérifications 45), + 18 % ; deux essais du choix des remises abandonnés après mesure ; à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : séries (50 + 30 + 30 + 30 matchs, et 50 matchs de chaque essai abandonné, environ 3 h 30), suite complète (20 min).

## Comments

- 23/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ (réserves acceptées). Réserves de l'expert, acceptées par le propriétaire (« Considéré que je valide automatiquement toutes tes recommandations et les avis d'expert », 22/11/2026, consigne de la session) : A1, part gardée des longs ballons non plus haute à 80 qu'à 40 (84,5 % contre 85,3 %), limite du moteur sans duel aérien : mesure 40/80 à refaire au `v2-realisme/15b` ; A2, buts − 1,03 [− 1,71 ; − 0,35] entre Kicking 40 et 80, cause non décomposée : décomposer (ballons perdus selon la zone, buts après une remise du gardien) et mesurer le profil Kicking avant ou dans `v2-collectif/15e`. Facultatif : A3, commentaire de portée de `possession.py` (51 m à 35 au lieu de 52,9 m, date) à corriger au `03c2` ; A4, choix des remises jugé au sol et sans portée, renvoyé au `15e`. Réserves du QC, non bloquantes : les mêmes (A1, A2, commentaire).
