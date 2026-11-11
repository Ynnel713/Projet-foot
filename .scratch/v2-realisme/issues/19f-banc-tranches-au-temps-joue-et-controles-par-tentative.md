# 19f: Banc : tranches au temps joué et contrôles ratés par tentative

**Chantier :** `v2-realisme` (réserves A1 et A2 de l'expert sur le 19d, 11/11/2026, acceptées par le propriétaire). **Priorité :** P0 (avant 18a : le 18a et le 20d calent des repères sur ces chiffres). **Catégorie :** mesure.

**Constat vérifié :**
- A1 : le banc découpe les tranches sur l'horloge du moteur (`now_s / 60`, `scripts/v2_indicators.py`, `on_tick` et `_speeds`), alors que la fatigue suit le temps joué (`played_minute`, `v2engine/match.py`). Avec 2 à 3 minutes de temps additionnel en première période, « 75-90 » couvre environ les minutes jouées 72,5 à 87,5 et « 90 et plus » commence vers la 87e minute jouée.
- A2 : « contrôles ratés pour 100 passes visées » divise tout contact raté (interceptions manquées comprises, `match.py`, boucle des contacts) par les seules passes de son équipe qui visent le joueur : le niveau des défenseurs est gonflé par leurs tentatives d'interception.

**What to build:** Tranches au temps joué : `played_minute(minute, second_half_start_minute, 45)` lu sur la trace en cours (`live["trace"]` de l'observateur de `measure_v2.run`), avec une tranche « 45 et plus » pour le temps additionnel de la première période et « 90 et plus » pour celui de la seconde. Contrôles : séparer le contrôle d'une passe de son équipe (ratés sur passes visées reçues ou manquées) et le contact sur un ballon adverse ou libre (interception manquée), ou rapporter les ratés aux tentatives de contrôle. Section 23 de `docs/INDICATEURS_V2.md` remise à jour (50 matchs). Facultatif (A3) : un but contre son camp n'est pas un but personnel du dernier toucheur adverse. Facultatif, repris de l'expert sur le 19e (11/11/2026) : `scripts/v2_chain.py` coupe la remontée sur une perte ou un hors-jeu de l'équipe qui marque (but alors inclassable si la reprise n'est pas écrite) ; un test d'invariant du journal (minutes croissantes, aucune faute causée par un but) sur un match court à graine fixée ; `--but` hors limites donne une erreur claire. Lecture seule : le moteur n'est pas modifié.

**Attributs :** aucun

**Blocked by:** 19d (livré).

**Bloque :** 18a ; 20d.

**Status:** à faire

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

- [ ] Tranches au temps joué, temps additionnel de chaque période à part
- [ ] Contrôles ratés de passe et interceptions manquées séparés (ou ratés par tentative)
- [ ] Section 23 mise à jour ; jeu inchangé (aucun fichier `v2engine/` modifié)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes valeurs sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
