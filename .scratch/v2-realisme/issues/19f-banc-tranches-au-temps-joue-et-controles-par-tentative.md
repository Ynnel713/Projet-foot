# 19f: Banc : tranches au temps joué et contrôles ratés par tentative

**Chantier :** `v2-realisme` (réserves A1 et A2 de l'expert sur le 19d, 11/11/2026, acceptées par le propriétaire). **Priorité :** P0 (avant 18a : le 18a et le 20d calent des repères sur ces chiffres). **Catégorie :** mesure.

**Constat vérifié :**
- A1 : le banc découpe les tranches sur l'horloge du moteur (`now_s / 60`, `scripts/v2_indicators.py`, `on_tick` et `_speeds`), alors que la fatigue suit le temps joué (`played_minute`, `v2engine/match.py`). Avec 2 à 3 minutes de temps additionnel en première période, « 75-90 » couvre environ les minutes jouées 72,5 à 87,5 et « 90 et plus » commence vers la 87e minute jouée.
- A2 : « contrôles ratés pour 100 passes visées » divise tout contact raté (interceptions manquées comprises, `match.py`, boucle des contacts) par les seules passes de son équipe qui visent le joueur : le niveau des défenseurs est gonflé par leurs tentatives d'interception.

**What to build:** Tranches au temps joué : `played_minute(minute, second_half_start_minute, 45)` lu sur la trace en cours (`live["trace"]` de l'observateur de `measure_v2.run`), avec une tranche « 45 et plus » pour le temps additionnel de la première période et « 90 et plus » pour celui de la seconde. Contrôles : séparer le contrôle d'une passe de son équipe (ratés sur passes visées reçues ou manquées) et le contact sur un ballon adverse ou libre (interception manquée), ou rapporter les ratés aux tentatives de contrôle. Section 23 de `docs/INDICATEURS_V2.md` remise à jour (50 matchs). Facultatif (A3) : un but contre son camp n'est pas un but personnel du dernier toucheur adverse. Facultatif, repris de l'expert sur le 19e (11/11/2026) : `scripts/v2_chain.py` coupe la remontée sur une perte ou un hors-jeu de l'équipe qui marque (but alors inclassable si la reprise n'est pas écrite) ; un test d'invariant du journal (minutes croissantes, aucune faute causée par un but) sur un match court à graine fixée ; `--but` hors limites donne une erreur claire. Lecture seule : le moteur n'est pas modifié.

**Attributs :** aucun

**Blocked by:** 19d (livré).

**Bloque :** 18a ; 20d.

**Status:** livré (11/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : `played_minute` et `second_half_start_minute` lisibles depuis la trace en cours ; le moteur distingue déjà, au moment du contact, une passe de son équipe d'un ballon adverse.
Temps machine, non compté : série de 50 matchs (environ 60 min) ; suite complète (environ 25 min).

## Tests

- **Unitaires :** avec une deuxième période commencée à la 47e minute d'horloge, 89 minutes jouées tombent en « 75-90 » et « 90 et plus » commence après 90 minutes jouées ; un défenseur qui manque une interception n'ajoute aucun raté à ses contrôles de passes visées.
- **Statistiques (séries de matchs) :** 50 matchs : tableaux de la section 23 refaits ; écart de la baisse de fin de match entre horloge et temps joué.

## Acceptance criteria

- [x] Tranches au temps joué, temps additionnel de chaque période à part
- [x] Contrôles ratés de passe et interceptions manquées séparés (ou ratés par tentative)
- [x] Section 23 mise à jour ; jeu inchangé (aucun fichier `v2engine/` modifié)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes valeurs sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (11/11/2026)

- **Temps joué** : `scripts/v2_tranches.py`, `tranche(minute, second_half_start)` découpe au temps joué (`played_minute`), avec « 45 et plus » (temps additionnel de la 1re période) et « 90 et plus » ; `MinuteProfile.second_half_start` lu sur `live["trace"].second_half_start_minute` par l'observateur de `scripts/measure_v2.py`, remis à zéro en fin de match. La hauteur du bloc passe par `MinuteProfile.on_block` (même découpage) ; `block_height_by_tranche` et la clé « bloc par minute » de `scripts/bench_series.py` sont retirées.
- **Contrôles** (A2) : `scripts/v2_indicators.py`, `on_events` : contrôle raté seulement si la cause est une passe ou une remise de son équipe qui vise le joueur ; sinon « contacts ratés » (« autres contacts ratés pour 90 min » par groupe, « par match » tous joueurs).
- **Facultatifs** : but contre son camp exclu des buts personnels (A3, équipe du joueur lue par `MinuteProfile.team`) ; `scripts/v2_chain.py` : `_breaks` coupe la remontée sur une perte ou un hors-jeu de l'équipe qui marque ; `--but` hors limites donne une erreur claire ; test d'invariant du journal sur un match court à graine fixée.
- **Tests** : 4 ajoutés (`tests/test_v2_tranches.py` : temps joué, interception manquée et contre son camp ; `tests/test_v2_chain.py` : perte de l'équipe qui marque, invariant du journal), 3 tests du 19d adaptés (début de 2e période fixé à 45).
- **Mesure, 50 matchs** (`.scratch/v2-realisme/mesures/19f-det1.*`, section 23 ter de `docs/INDICATEURS_V2.md`) : au temps joué, sprints − 36 % et course au-dessus de 25 km/h − 37 % de 0-15 à 75-90 (− 27 % et − 28 % à l'horloge) ; rapport médian des sprints par joueur 0,65 (0,73 à l'horloge). Contrôles ratés pour 100 passes visées des DC : 4,2 en 0-15 (16,2 avec les interceptions manquées).
- **Chaîne, 20 matchs** (`19f-chaine.json`) : 108 buts, parts inchangées (récupération 81 %, erreur adverse 15 %, jeu placé 3 %, coup de pied arrêté 1 %, touche 1 %), aucun inclassable : la coupure sur une perte de l'équipe qui marque ne change aucun but de ces 20 matchs.
- **Déterminisme** : 10 premiers matchs rejoués (`19f-det2.json`) : 2 467 clés par match communes, valeurs identiques.
- **Durée** : estimée 1 h 20, réelle environ 1 h 30 (+ 13 %). Temps machine hors total : séries de 50 et 10 matchs (61 et 38 min en parallèle), chaîne de 20 matchs, suite complète.

## Comments

- 11/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Aucune anomalie bloquante, aucune réserve. Améliorations facultatives de l'expert : A1 `HALF_MIN = 45` codé en dur (faux si `--duration` ≠ 90, aucune série publiée concernée) ; A2 les autres découpages « minute » de la géométrie restent à l'horloge (hors section 23) ; A3 constat moteur, environ 2 passes visées par DC et par 15 min, loin du réel (repris au 18a). Remarque du QC : un second contrôle raté causé par le premier tombe dans les autres contacts.
