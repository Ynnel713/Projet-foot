# 18i: Passe précise coupée trop souvent, même courte

**Chantier :** `v2-realisme`. **Catégorie :** exécution, défense.

**Origine :** ticket 18h (12/11/2026, 12 matchs, moteur après 18g). Une passe PRÉCISE (tirage de `possession.pass_aim` réussi) n'est reçue par un coéquipier que dans environ 85 % des cas, quelle que soit sa longueur : courte 85,4 %, moyenne 85,3 %, longue 86,0 %. Les échecs viennent des coupes (adversaire qui touche le ballon le premier : table du 18g, plus environ 5 % de coupes imprévues). Réel indicatif (toutes passes, précises ou non) : courte 89,4 %, moyenne 87,1 %, longue 51,7 % (Premier League 2024-25, Total Football Analysis d'après FBref). Une passe courte précise est presque jamais coupée dans le réel.

**What to build :** Trouver pourquoi une passe courte précise est coupée aussi souvent qu'une longue (placement et course des défenseurs pendant la passe, `anticipation.pass_readers`, contacts du ballon avec un joueur proche du passeur, choix de passes dans le trafic) et corriger le mécanisme. Remesurer ensuite la table de coupe du 18g et l'indicateur de calibration de la passe.

**Hors de ce ticket :** conséquence de la passe ratée (18h) ; calibration finale des passes (`v2-collectif/22a`).

**Attributs :** Anticipation, Positioning, Passing (aucun rôle nouveau).

**Blocked by :** 18h.

**Bloque :** `v2-collectif/22a`.

**Status :** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 1 h |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible (cause à trouver). À examiner pour découpage après le diagnostic. Temps machine, hors total : diagnostics et séries de 50 matchs, suite complète.

## Acceptance criteria

- [x] Cause des coupes de passes courtes précises identifiée et chiffrée (diagnostic) : ballon passé à côté du receveur visé (contact à 0,41 m), 8,6 % des passes courtes précises
- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (portée 1,0 m, reprise de `BLOCK_WIDTH_M`, réel non trouvé ; coupe imprévue 0,01 ; passe imprécise non perdue 0,85 / 0,68)
- [x] Réussite par longueur (courte, moyenne, longue) mesurée avant/après sur 50 matchs, comparée au réel : 82,9 / 76,3 / 71,2 → 92,0 / 85,3 / 76,6 % (réel 89,4 / 87,1 / 51,7)
- [~] Table de coupe du 18g remesurée ; indicateur de calibration de la passe sous 5 points par tranche : tenu sur les tranches de 0,6 à 1 (97,8 % des passes) ; [0,4 ; 0,5[ − 6,9 et [0,5 ; 0,6[ − 5,9 points, écart accepté par le propriétaire (« ok option 1 », 12/11/2026), à reprendre au `v2-collectif/22a`
- [x] Suite complète comparée à l'attendu de `CLAUDE.md` : 2 768 passés, 14 désélectionnés (2 759 + 9 ajoutés ; `.scratch/v2-realisme/mesures/18i-suite.txt`)

## Comments

**12/11/2026, reprise du 18h.** Corriger aussi la docstring de `possession.pass_aim` (« déviée de 10 à 25 % » : 25 à 50 % depuis le 18h, réserve facultative A2 de l'expert).

**12/11/2026, lancement.** Estimation annoncée : 2 h 30, confiance faible. Découpage écarté par le propriétaire (« pas de découpage »).

**12/11/2026, diagnostic (12 matchs, graines d'audit 20260923 + 0 à 11, moteur après 18h ; script `.scratch/v2-realisme/mesures/18i-diag-script.py`, enveloppes de lecture seule ; 10 986 passes de jeu, 8 591 précises).**
- Passe précise courte : reçue par un coéquipier 85,6 %, coupée 11,5 %, morte ou sortie 3,0 %. Moyenne 85,2 / 10,8 ; longue 85,2 / 11,7.
- Où la passe courte précise est coupée : 57 % des coupes dans les 3 derniers mètres, dont 82 % **au-delà du point visé**, ballon à 2,6 m/s (médiane), receveur à 2,2 m du coupeur. 27 % près du passeur (moins de 3 m), 16 % sur le trajet.
- Cause principale : **le ballon passe à côté du receveur sans le toucher**. Contact au ballon = `match.CONTROL_RADIUS_M` (0,41 m : rayon du ballon plus rayon du corps), pour tout le monde, receveur compris. Le receveur vient au ballon (`anticipation.meeting_point`) mais le ballon passe à 0,5 à 0,85 m de lui (quartiles, échantillon au pas de 0,1 s) : 8,6 % des passes courtes précises passent à moins de 1,2 m du receveur sans contact ; elles finissent chez l'adversaire (5,6 points sur les 11,5 de coupe) ou mortes / sorties (2,8 points). Le receveur ne tend pas la jambe ; le contre d'un tir (05c) l'a déjà, `shooting.BLOCK_WIDTH_M` = 1,0 m « jambe tendue plus ballon ».
- Causes secondaires, non traitées ici : un défenseur sans rôle à moins de 15 m (ou le plus proche de son équipe) traite la passe adverse en vol comme un ballon libre (`cerveau.interpret`, `BALLON_LIBRE`) et court à son point d'arrêt : c'est lui qui ramasse 31 % des passes courtes coupées, presque toujours après le raté du receveur ; le presseur du receveur vise son point de rencontre (`defense.DefensiveRoles.update`, passe en vol).
- Essai hors moteur (enveloppe du script, rien de commité), portée du seul receveur visé, 12 matchs, mêmes graines ; réussie = coéquipier au premier contact :

| Portée du receveur visé | Passes/match | Précise courte / moyenne / longue | Toutes courte / moyenne / longue |
|---|---|---|---|
| 0,41 m (actuel) | 916 | 85,6 / 85,2 / 85,2 % | 84,2 / 75,2 / 68,0 % |
| 0,7 m | 953 | 92,5 / 92,2 / 91,4 % | 91,0 / 82,5 / 73,4 % |
| 1,0 m | 963 | 93,9 / 93,3 / 90,3 % | 92,7 / 84,8 / 76,0 % |
| Réel indicatif (18h) | 890 à 940 | — | 89,4 / 87,1 / 51,7 % |

**12/11/2026, décision du propriétaire (« ok 1,0 m »).** Portée du receveur visé `match.RECEIVER_REACH_M` = `shooting.BLOCK_WIDTH_M` (1,0 m) ; les autres joueurs gardent `CONTROL_RADIUS_M`. Codé (`match._ball_contacts`), tests `tests/test_v2engine_portee_receveur.py` (8). Docstring de `possession.pass_aim` corrigée (réserve A2 du 18h).

**12/11/2026, mesure après sur 50 matchs (mêmes graines que le 18h ; `.scratch/v2-realisme/mesures/18i-50-*`, synthèse `18i-synthese.py`).**
- 18h → 18i : passes par match 933 → 1 001 (repère 890 à 940) ; passes réussies 79,7 → 86,1 % ; chez l'adversaire 16,6 → 11,7 % ; receveur visé 77,6 → 84,4 % ; passes par possession 3,84 → 4,67 ; possession d'équipe 23,8 → 27,0 s (repère 11 à 16) ; buts 2,08 → 2,26 ; pertes en conduite 56 → 66 ; passes longues réussies 49,4 → 56,8 %.
- Réussite par longueur (diagnostic de 50 matchs, 48 520 passes ; coéquipier au premier contact) : toutes 82,9 / 76,3 / 71,2 % → 92,0 / 85,3 / 76,6 % (réel indicatif 89,4 / 87,1 / 51,7 %) ; précises 93,2 / 93,5 / 90,0 %.
- Calibration de la passe avec la table actuelle : évaluée trop basse de 4,9 à 6,6 points sur les tranches de 0,5 à 1 (critère : sous 5 points) → table à remesurer.

**12/11/2026, table remesurée (`18i-ajustement.py`, sortie `18i-ajustement.txt` ; ajustement lots 0 et 2, contrôle lots 1 et 3).** Coupe par adversaire du 18g : inchangée dans le bruit (près du passeur 0,81 / 0,12 / 0,008 contre 0,75 / 0,14 / 0,01 ; trajet 0,30 / 0,15 / 0,07 / 0,04 / 0,02 / 0,01, identique). Coupe imprévue d'une passe précise : 0,007 (contrôle 0,009) contre 0,05 : ce terme comptait surtout le ballon passé à côté du receveur. Passe imprécise non perdue hors coupe : 0,835 sous 10 m (contrôle 0,896, peu de passes), 0,682 au-delà (0,673). **Proposition** : tables de coupe du 18g gardées, `UNFORESEEN_CUT` 0,05 → 0,01, `_MISS_NOT_LOST` 0,78 / 0,64 → 0,85 / 0,68. Contrôle hors ligne (lots 1 et 3) : écart prévu / non perdue de − 1,9 à + 1,1 point sur les tranches d'au moins 200 passes, − 0,2 point au total.

**12/11/2026, décision du propriétaire (« ok 0,01 et 0,85 / 0,68 »).** Codé (`possession.UNFORESEEN_CUT`, `possession._MISS_NOT_LOST`) ; tables de coupe du 18g inchangées.

**12/11/2026, mesures après (section 32 de `docs/INDICATEURS_V2.md` ; `.scratch/v2-realisme/mesures/18i-*`).**
- Calibration de la passe (50 matchs) : − 1,1 à − 4,2 points sur les tranches de 0,6 à 1 ; − 5,9 ([0,5 ; 0,6[) et − 6,9 ([0,4 ; 0,5[), 2,2 % des passes. Le contrôle hors ligne de la table (précision tirée et non chance évaluée) prévoyait moins de 2 points : il ne mesurait pas ce que mesure le banc.
- **12/11/2026, décision du propriétaire (« ok option 1 »)** : écart des deux tranches basses accepté, à reprendre au `v2-collectif/22a`.
- Effets 18h → 18i : passes par match 933 → 1 043 (repère 890 à 940) ; possession d'équipe 23,8 → 28,3 s (11 à 16) ; passes réussies 79,7 → 86,2 % ; chez l'adversaire 16,6 → 11,6 % ; buts 2,08 → 2,64.
- Scènes A/B (`18i-ab.txt`) : aucun effet inversé ni annulé (Passing + 0,139 meilleure passe, + 0,227 part de passes choisies).
- Déterminisme : deux exécutions de `measure_v2 2` identiques hors temps de calcul (`18i-det1`, `18i-det2`).
- Tests : 9 ajoutés (`tests/test_v2engine_portee_receveur.py`) ; 1 mis à jour pour les nouvelles valeurs (`test_v2engine_difficulte.py`) ; 2 scènes déplacées dont la prémisse ne tenait plus (`test_v2engine_cerveau.py` : passe et conduite devenues quasi égales, coéquipier de y = 40 à 48 ; `test_v2_tranches.py` : A passait avant 2 s, B de (30 ; 14) à (30 ; 8)). Suite : 2 768 passés, 14 désélectionnés.
- Points à surveiller : passe longue trop réussie (76,6 % contre 51,7 %) ; défenseurs sans rôle qui traitent une passe adverse en vol comme un ballon libre (`cerveau.interpret`) ; presseur qui vise le point de rencontre du receveur.

**Durée.** Estimée 2 h 30, dépassement d'environ 30 min annoncé en cours de route. Réelle environ 3 h, non chronométrée (analyse 1 h 15, développement 20 min, tests 35 min, intégration et vérifications 50 min) : + 20 %. Temps machine hors total : diagnostics de 12 matchs (3 fois) et de 50 matchs, 2 séries de 50 matchs avec l'indicateur, scènes A/B, déterminisme, suite complète (2 fois, 8 min).

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. QC : VALIDÉ. Clôture : VALIDÉ. Réserves acceptées par le propriétaire (« ok A1 A2 A3, crée le 18j ») :
- A1 [réserve] : passes par match 1 043, passes chez l'adversaire 11,6 %, passes par possession 5,11, possession d'équipe 28,3 s, hors repère ou plus loin ; inscrit au `v2-collectif/22a`.
- A2 [réserve] : passe longue trop réussie (76,6 % contre 51,7 %), écart aggravé ; inscrit au `v2-collectif/22a`.
- A3 [réserve] : portée asymétrique, le défenseur qui lit la passe touche à 0,41 m contre 1,0 m pour le receveur ; ticket `v2-realisme/18j` créé.
- A4 [facultatif] : un contrôle jambe tendue (1 m du corps) a la même difficulté qu'un contrôle dans le corps ; à examiner au `v2-collectif/22a`.

