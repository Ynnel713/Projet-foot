# 05c: Contre : le défenseur touche réellement le tir

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le contre doit naître de la trajectoire, pas d'un tirage préalable). **Catégorie :** exécution.

**Constat vérifié :** `match.py:461` tire le contreur avant le départ du tir (`draw_blocker`, cône et chance de 0,6 par part couverte, `shooting.py`) ; le ballon repart ensuite d'un angle tiré au hasard.

**What to build:** Le tir simulé pas à pas (05a) touche un joueur de champ qu'il frôle (détection de contact existante) ; un défenseur sur la trajectoire tente de contrer avec une chance qui dépend de sa distance au tireur (temps de réaction) ; la valeur `BLOCK_CHANCE` devient cette chance au contact. Le contre est tracé avec l'endroit du contact.

**Hors de ce ticket :** déviation après contact (05d) ; Bravery (17b).

**Attributs :** aucun

**Lien avec l'existant :** remplace le tirage préalable du ticket 33 / 28a (livrés, non modifiés).

**Blocked by:** 05a (Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ).

**Bloque :** 05d, 05e, 05g, 17b.

**Status:** livré (09/11/2026), validé expert + QC

## Constantes (proposées le 09/11/2026, validées par délégation du propriétaire)

| Constante | Valeur | Source |
|---|---|---|
| `BLOCK_BODY_M` | 0,41 m | portée du corps seul : celle du contact ballon-joueur (`match.CONTROL_RADIUS_M`) |
| `BLOCK_WIDTH_M` | 1,0 m (existante) | jambe tendue plus ballon (ticket 33) |
| `BLOCK_REACTION_S` | 0,10 s | temps de réaction d'un défenseur sur un tir : non trouvé ; 0,25 s (ordre du gardien) donnait 12,5 % de tirs contrés sur 50 matchs ; 0,10 s recalé hors ligne sur 1 074 tirs de 24 matchs vers le repère réel |
| `BLOCK_CHANCE` | 0,6 (existante) | devient la chance de contrer au contact |

Repère réel : 20 à 28 % des tirs contrés, 22,5 % en Bundesliga 2015-16 (ticket 28). Délégation : « Considère que je valide automatiquement toutes tes recommandations et les conseils d'experts » (09/11/2026).

## Estimation

| Poste | Estimé | Réel |
|---|---|---|
| Analyse et compréhension du code | 25 min | 20 min |
| Développement | 45 min | 40 min |
| Tests unitaires et comportementaux | 35 min | 35 min |
| Intégration et vérifications | 25 min | 50 min |
| **Total (travail effectif)** | **2 h 10** | **2 h 25** (+ 12 %, durée estimée, non chronométrée) |

Confiance : moyenne. Hypothèses : la décision du porteur garde son estimation du contre (`block_probability`) jusqu'au 05e.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur à 1 m sur l'axe : contre fréquent ; à 8 m : moins fréquent (temps de réaction) ; hors axe : jamais
- **Statistiques (séries de matchs) :** 50 matchs : part des tirs contrés (repère 20-28 %, indicatif)

## Réalisation

- `match._blocked` : à chaque pas du tir en vol, le premier défenseur de champ adverse que le ballon frôle à sa portée (`shooting.block_reach_m` : corps avant `BLOCK_REACTION_S` après la frappe, jambe tendue ensuite) tente de contrer, une fois par tir (`ShotFlight.tried`), avec la chance `BLOCK_CHANCE`. Contré : issue « contré » et point de contact tracés (`ShotEvent.block_x`, `block_y`) ; le ballon rebondit de ce point, dévié comme au ticket 33 (déviation physique au 05d), à la moitié de sa vitesse au contact. `_contacts` reçoit un rayon.
- `shooting.draw_blocker` retiré (plus de tirage du contreur au départ) ; `block_probability` reste l'estimateur de la décision jusqu'au 05e.
- Reprises facultatives de l'expert du 05h : A4, vitesse du ballon au gardien tracée (`ShotEvent.keeper_speed_mps`, lue par le banc) ; A5, `shot_wide` remis à faux pour un tir mort avant la ligne ; réserve A2, effectif de chaque tranche du taux d'arrêt dans le rapport du banc.
- Tests : `tests/test_v2engine_contre.py` (5) : portée corps puis jambe ; défenseur à 1 m dans l'axe contre plus souvent qu'à 8 m, jamais hors de l'axe ; contre tracé au point de contact ; le corps seul ne touche pas un ballon qui passe à 0,6 m tout de suite ; garde : au départ, le tir est en vol. Adaptés : six fichiers où le contre était neutralisé par `draw_blocker` (désormais `BLOCK_CHANCE` à 0), le rebond sur le défenseur (`test_v2engine_meilleur_choix`) joué physiquement ; la garde en match du 05h passe à son propre test sur 30 minutes (10 minutes ne donnaient plus de tir cadré à graine fixée).

## Mesures (09/11/2026, graine d'audit, `.scratch/v2-realisme/mesures/05c-*` et `05c2-*`, moyenne de 10 lots de 5 matchs)

- **Réaction 0,25 s** (`05c-on*`) : 12,5 % de tirs contrés, conversion 10,1 %, 4,7 buts par match.
- **Réaction 0,10 s** (`05c2-on*`) : **19,6 % de tirs contrés** (lots 16,3 à 24,9 %), cadrés 29,0 %, conversion 8,2 %, 3,9 buts par match, tirs 23,3 par équipe (les tirs contrés sont désormais comptés au départ, comme les autres).
- **Déterminisme** : lot 0 joué deux fois (`05c2-on0.json`, `05c2-det2.json`) : identiques.

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Plus de tirage préalable du contreur
- [x] Part contrée rapportée (50 matchs)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 09/11/2026, clôture : expert APPROVED (un passage, empreinte 6f81b88c) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-realisme/05c/cloture`). Suite complète : 2 597 passés, 14 désélectionnés.
- Facultatifs de l'expert, non traités : A1 (point de contact tracé jusqu'à 0,59 m trop tôt quand seul le corps compte, à reprendre au 05d) ; A2 (dépendance au pas si `tick_seconds` change de 0,1 s) ; A3 (hauteur du ballon ignorée au contact, avec 05f ou 17b).
- À surveiller (expert) : grosses occasions 6,5 → 8,1 par match ; « tirs par équipe » compte désormais les tirs contrés ; alignement de `block_probability` au 05e ; volume de tirs (22c).
- QC : non bloquant, 19,6 % de contrés légèrement sous le repère indicatif de 20-28 %.
