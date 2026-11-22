# 05a: Gestes préférés, lignes branchées avant la calibration

**Découpé du ticket 05 le 22/11/2026** (décision du propriétaire : tout ce qui change le jeu passe avant la calibration ; levée de l'incohérence avec `v2-realisme/04n`). Catalogue, règles et paires contradictoires : `05-catalogue-gestes-preferes.md`, qui reste la référence de détail.

**What to build:** brancher comme **biais de probabilité** (jamais un ordre) les gestes préférés dont le mécanisme porteur est livré ou passe avant la calibration, chacun dans le ticket qui porte son choix :

| Mécanisme | Gestes | Ticket porteur |
|---|---|---|
| Conduite et dribble | Runs With Ball Often / Rarely / Down Left / Down Right / Through The Centre, Likes To Beat Opponent Repeatedly, Knocks Ball Past Opponent, Tries Tricks, Bring Ball Out of Defence, Dwells On Ball, Tries To Play Way Out Of Trouble, Cuts Inside From Left Wing / Right Wing / Both Wings | `v2-collectif/19` (gestes de `v2-realisme/04g` à `04m`, livrés ou avant le 05a) ; le choix du geste (`v2-realisme/04n`) lit ces penchants, il ne les porte pas |
| Passe | Plays Short Simple Passes, Plays No Through Balls, Tries Killer Balls Often, Tries Long Range Passes, Likes To Switch Ball To Wide Areas, Plays One-Twos, Dictates Tempo, Stops Play, Looks For Pass Rather Than Attempting To Score, Uses Outside Of Foot (partie passe), Likes Ball Played Into Feet (côté passeur) | `v2-collectif/19`, 13, 14 (livrés) |
| Appels sans ballon | Gets Forward Whenever Possible, Gets Into Opposition Area, Arrives Late In Opposition Area, Moves Into Channels, Comes Deep To Get Ball, Likes Ball Played Into Feet (côté receveur), Plays With Back To Goal, Likes To Try To Break Offside Trap, Stays Back At All Times, Penalty Box Player, Hugs Line | `v2-collectif/16`, 23 (livrés) ; 19 pour la conduite |
| Tir (choix de tirer) | Shoots From Distance, Refrains From Taking Long Shots | `v2-collectif/28a` (livré) |
| Jeu aérien et centres | Crosses Early, Attempts Overhead Kicks, Curls Ball (centres enroulés) | 01, 11 |
| Coups de pied arrêtés | Hits Free Kicks With Power, Tries Long Range Free Kicks, Demands to Take Penalties, Possesses Long Flat Throw, Curls Ball (coups francs) | 02a ; `v2-realisme/16d`, `16e`, `16f`, `16j` (découpage du 02b) |
| Gardien | Uses Long Throw To Start Counter Attacks | 03c |

**Attributs :** Preferred moves.

**Blocked by:** `v2-collectif/19` pour le principe ; chaque ligne est branchée quand son ticket porteur est livré (ouverts : `v2-collectif/19`, 01, 02a, 03c, 11 ; `v2-realisme/16d`, `16e`, `16f`, `16j`).

**Bloque :** `v2-realisme/04n` (penchants de fréquence du geste de dribble : le 04n les lit dès que la ligne « Conduite et dribble » est branchée) ; `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 60 min |
| Tests unitaires et comportementaux | 45 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 45** |

Confiance : faible. Hypothèses : chaque ticket porteur expose son choix dans la monnaie de la décision (`decision.py`), le geste n'ajoute qu'un biais de fréquence. Au-dessus du seuil de 2 h : découpage par mécanisme à examiner avant le code (une ligne du tableau par lot). Les lignes dont le porteur n'est pas encore livré sont branchées au fil des livraisons.
Temps machine, non compté : banc de profils par geste (`scripts/measure_v2.py --profil`), suite complète.

## Acceptance criteria

- [ ] Pour chaque geste branché : fréquence du choix concerné mesurablement plus haute (ou plus basse) qu'un joueur aux mêmes attributs sans ce geste ; jamais systématique
- [ ] Réussite du geste inchangée à attributs égaux (règle anti double comptage)
- [ ] Paires contradictoires signalées, jamais additionnées (règle du ticket 05)
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
