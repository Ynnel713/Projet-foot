# 17a: Carte des attributs : état réel de branchement

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (la carte annonce branchés des attributs que le moteur ne lit pas). **Catégorie :** documentation.

**Constat vérifié :** `docs/CARTE_ATTRIBUTS_V2.md` donne Technique « branché ; à revoir », alors qu'aucun appel `player_attribute(..., "Technique")` n'existe dans `v2engine/` (seule mention : une docstring de `match.py`).

**What to build:** Relire la colonne « État » de la carte contre le code (recherche de chaque nom d'attribut) et la corriger : branché (avec le fichier), lu sans effet sur l'issue (cas de Dribbling avant 04a), à créer (avec le ticket qui le branche, dont ceux de ce chantier). Aucun code.

**Attributs :** aucun

**Blocked by:** None.

**Bloque :** 17d, 18a.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 0 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 15** |

Confiance : élevée. Hypothèses : documentation seulement.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Intégration :** liste des attributs lus par le code jointe au rapport

## Acceptance criteria

- [x] Chaque ligne de la carte cohérente avec le code ou renvoyée à un ticket
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Rapport d'implémentation (06/11/2026)

Méthode : analyse de l'arbre syntaxique de `v2engine/*.py`, chaîne littérale égale à un nom d'attribut hors docstring ; plus les champs de capacité `.pace`, `.acceleration`, `.stamina` de `PlayerState`. Chaque ligne de la colonne « État » de `docs/CARTE_ATTRIBUTS_V2.md` porte désormais le fichier qui lit l'attribut, ou le ticket qui le branchera.

### Attributs lus par le code (preuve d'intégration)

| Attribut | Lu dans |
|---|---|
| Pace, Acceleration, Stamina | `match.py` (construction des joueurs) ; champs lus dans `movement.py`, `anticipation.py`, `bloc.py`, `decision.py`, `defense.py` |
| Balance, Strength | `duel.py` (résistance au tacle, dérogation A3) |
| Work Rate | `defense.py` |
| Off the Ball | `off_ball.py`, `offside.py` |
| Teamwork | `bloc.py`, `decision.py`, `defense.py` |
| Decisions | `decision.py`, `restart.py` |
| Vision | `decision.py`, `off_ball.py` |
| Anticipation | `anticipation.py`, `decision.py`, `defense.py`, `match.py` |
| Positioning | `bloc.py` |
| Composure | `decision.py`, `possession.py`, `shooting.py` |
| Aggression | `defense.py`, `duel.py`, `match.py` |
| First Touch | `possession.py` |
| Passing | `off_ball.py`, `possession.py` |
| Dribbling | `decision.py` (évaluation seulement : sans effet sur l'issue, `04a`) |
| Finishing, Long Shots | `shooting.py` |
| Tackling | `duel.py` |
| Marking | `defense.py` |
| Reflexes, One on Ones, Handling | `shooting.py` (note mélangée, dérogation A8) |

Lus : 24 attributs sur 47. Non lus (23 attributs, plus 5 colonnes) : Agility, Jumping Reach, Natural Fitness, Concentration, Flair, Determination, Bravery, Leadership, **Technique**, Crossing, Heading, Corners, Free Kick Taking, Long Throws, Penalty Taking, Aerial Reach, Command of Area, Communication, Kicking, Throwing, Rushing Out, Punching, Eccentricity ; colonnes Weak foot, Pieds, Taille, Preferred moves, Postes naturels.

### Corrections de la carte

- **Technique** : « branché ; à revoir » devient « à créer » (aucun appel ; seule mention : docstring de `match.py`), avec ses tickets (`v2-collectif/31`, `34a`, `34b`, `34d`, `36a`, `36b`, `32b`, `v2-attributs-restants/10a`).
- **Dribbling** : « branché dans la valeur factuelle » devient « lu sans effet sur l'issue » (`04a`).
- **Balance** : « branché » devient « lu hors de son rayon » (tacle, A3 ; rayon propre au `12c`).
- **Reflexes, One on Ones, Handling** : branchés hors de leur rayon (note mélangée A8) ; Handling ne règle pas « captée ou repoussée ».
- **Decisions** : lecture non documentée ajoutée (`restart.py`, choix du receveur d'une remise en jeu).
- **Natural Fitness** : « non branché à raison » (D-V10, exception assumée de `v2-attributs-restants/08`).
- Renvois périmés (« phase 6 à 10 », « étape duels », `v2-cerveau-joueurs/05`, « ticket 12 », `v2-attributs-restants/10`) remplacés par les tickets actuels.
- Tableau des interactions : « Acceleration non utilisée » (faux : `defense.py`, temps d'arrivée) et la ligne Dribbling + Flair + Decisions corrigés.

Hors périmètre, non modifié : les colonnes « Rayon propre », « Ne pilote pas », « Où on le voit », « Liens », et le tableau d'audit A1 à A14.

## Comments

- **06/11/2026, passage 1** : expert APPROVED, QC VALIDÉ, clôture VALIDÉ. Aucune anomalie bloquante. Réserves : aucune. Facultatifs (expert A1) : deux cellules du tableau des interactions encore périmées (« Acc à recaler », renvois « Tickets 12, 16 » sans le découpage 12d à 12f), à traiter avec 17d ou 18a. QC : suite non exécutée par le contrôleur, passée par la session (2 399 passés, 14 désélectionnés, 18 min 53 s machine).
- **Durée** : estimée 75 min ; réelle environ 60 min (estimation de la session, non chronométrée), soit − 20 %, sous le seuil de 30 %. Analyse et correction de la carte plus rapides que prévu (scan par arbre syntaxique).
