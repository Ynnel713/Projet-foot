# 03b3b: Gardien : sorties inattendues (Eccentricity)

**Découpé du ticket `03b3` le 22/11/2026.** Référence : Eccentricity 40, médiane des 50 gardiens notés de Ligue 1 de la base (de 25 à 85).

**What to build:** Eccentricity (tendance : goût du risque) donne au gardien des sorties inattendues : sur un ballon libre qu'il ne devrait pas disputer d'après la course (`gardien.race`), un gardien excentrique tente parfois sa chance, une fois par action (mémoire du « coup de tête » à créer, pour ne pas tirer à chaque tick ni changer d'avis aussitôt). Imprévisible : peut sauver ou couler son équipe ; le niveau moyen ne change pas. Dribbles du gardien dans sa surface : au `10b`.

**Attributs :** Eccentricity.

**Blocked by:** `03b3a`.

**Bloque :** `10b` ; `v2-coach-et-gestion-de-match/04`.

**Status:** livré (23/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 25 min |
| Développement | 40 min |
| Tests | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible (mécanisme à créer). Temps machine, non compté : suite complète ; 50 matchs appariés.

**Constantes** (proposées au propriétaire le 22/11/2026, délégation permanente « Je valide automatiquement toutes tes recommandations et les avis d'expert ») : référence 40 (médiane des 50 gardiens notés de Ligue 1 de la base) ; à 40, en dessous et sans note : aucun tirage, comportement d'avant ; probabilité d'une sortie inattendue 0,008 par point au-dessus de 40, plafond 0,4 (0,08 à 50, 0,32 à 80, 0,36 à 85) ; fenêtre d'un ballon encore disputé : la course (`gardien.race`) refuse la sortie, mais le gardien n'arrive pas plus de 0,1 s après l'adversaire (un 50/50), et le point est à 8 m au plus au-delà de sa distance maximale de sortie (Rushing Out, `03b3a`). Un tirage par action (mémoire `BallState.keeper_whims`, vidée quand le ballon n'est plus libre à sa portée), dans un flux aléatoire à part (`flux.CAPRICE`). Repères réels (fréquence des sorties « hasardeuses » d'un gardien excentrique) : non trouvés, ordres de grandeur. Premier réglage (0,3 s de retard toléré, 0,006 par point, plafond 0,3) abandonné après mesure, voir Résultats.

**Critères chiffrés** (posés avant le code) : à 40 ou moins et sans note, aucun tirage et mêmes scores qu'avant (4 matchs forcés à 25) ; scène : fréquence d'une sortie inattendue égale à la probabilité (0,08 à 50, 0,32 à 80, ± 0,03 sur 2 000 essais), une seule fois par action ; série forcée à 80 : sorties inattendues mesurables (au moins 0,2 par gardien et par match) ; buts par match : écart apparié rapporté avec son intervalle.

## Acceptance criteria

- [x] Constantes proposées au propriétaire avant le code
- [x] Eccentricity élevée : plus de sorties inattendues (scène et matchs), sans changer le niveau moyen
- [x] Une décision par action : pas de tirage à chaque tick, pas d'aller-retour
- [x] Test de rayon et carte à jour
- [x] Durée réelle relevée ; déterminisme ; suite V2 verte ; V1 inchangée

## Résultats (22-23/11/2026)

- Code : `gardien.eccentricity` (référence 40 sans note ou sans la colonne), `whim_probability`, `whim_window`, `whim` ; mémoire `BallState.keeper_whims` (gardien -> réponse du tirage pour le ballon libre en cours), vidée par `cerveau._keeper` dès que le ballon n'est plus libre à sa portée ; nouveau flux aléatoire `flux.CAPRICE` (« caprice »). La sortie inattendue passe par l'état `sortie` existant (même geste qu'une sortie normale), sa raison porte « sortie inattendue : il tente sa chance ».
- Flux à part, décision prise en cours de ticket : avec le flux de décision partagé, chaque tirage, même refusé, décalait les autres tirages de décision et changeait tout le match (première série : buts + 0,98 [+ 0,28 ; + 1,68], y compris + 0,94 sur les 31 matchs sans aucune sortie inattendue). Avec `CAPRICE`, un tirage refusé ne change rien : 30 des 38 matchs sans sortie inattendue repérée ont un score identique à avant (les autres ont eu une sortie trop brève pour la trace à 2 images par seconde, ou un tirage gagnant aussitôt sans effet visible).
- Réglage revu après mesure (délégation du propriétaire) : premier réglage (jusqu'à 0,3 s de retard sur l'attaquant, 0,006 par point, plafond 0,3), forcé à 80 : 4 ballons gagnés sur 45 sorties inattendues, 7 buts encaissés dans les 15 s ; sonde de 8 matchs : 11 sorties sur 19 partaient en retard, à 4-18 m du but. Fenêtre ramenée à un vrai 50/50 (0,1 s de retard au plus), probabilité 0,008 par point (plafond 0,4).
- Scènes (`tests/test_v2engine_excentricite_gardien.py`, 13 cas) : à 40, à 25 et sans note, aucun tirage ; à 80, une seule fois par action, sans retour en arrière, nouveau tirage sur un nouveau ballon libre ; fenêtre (0,05 s de retard : jouable ; 0,2 s : non ; 40 m de son but : jouable ; 48 m : non) ; aucun tirage pour une sortie que la course accorde ; fréquence sur 2 000 essais 0,08 à 50 et 0,32 à 80 (± 0,02 / 0,03) ; un tirage refusé ne décale pas le flux de décision. Garde des attributs : scène « ballon disputé » (Eccentricity 11 contre 99, divergence trouvée).
- Contrôle (4 matchs, tous les gardiens forcés à 25) : 4 scores identiques à `03b3a-reel`.
- Séries (mêmes graines ; avant : `03b3a-reel`, code de `e924fb1`) :

| Série | Buts/match | Sorties/gardien/match | Inattendues/gardien/match | Ballon au gardien | Buts encaissés dans les 15 s |
|---|---|---|---|---|---|
| avant (50 matchs) | 4,12 | 6,53 | — | — | — |
| réelle (50 matchs) | 4,22 | 6,71 | 0,18 | 1 / 18 | 2 |
| forcée à 80 (30 matchs) | 4,27 | 7,10 | 0,83 | 12 / 50 | 7 |

  Écart apparié des buts : réelle + 0,10 [− 0,29 ; + 0,49] ; forcée à 80 + 0,03 [− 0,92 ; + 0,98] : niveau moyen inchangé. Série réelle par tranche : 0 sortie inattendue sous 41 (45 gardiens-matchs), 0,50 de 41 à 59 (28), 0,15 à 60 et plus (27 ; trois gardiens seulement, peu de ballons disputés : l'adversaire pèse plus que la note sur une série réelle, l'effet propre est isolé par la série forcée).
- Sonde (8 matchs forcés à 80, `03b3b-sonde.py`) : 18 sorties inattendues, avance estimée du gardien de − 0,04 à + 0,59 s ; issue : adversaire 10, gardien 2, partenaire 2, ballon mort 4 ; but encaissé dans les 15 s : 5. **Constat hors périmètre** : même estimé en avance, le gardien perd la plupart de ces ballons, parce que la course (`gardien.race`, ticket `v2-realisme/03d`) compare les deux joueurs sur le point visé par le gardien, alors que l'attaquant intercepte souvent le ballon plus tôt sur sa trajectoire. Toutes les sorties disputées en souffrent (13,8 % gagnées, `03k`). Ticket de suite proposé : `v2-realisme/03m`.
- Suite complète (après le réglage) : 3 554 passés, 0 ignoré, 14 désélectionnés (3 540 + 14 cas nouveaux : 13 dans le nouveau fichier, 1 dans la garde des attributs). Déterminisme : matchs 0 et 4 rejoués deux fois, mêmes empreintes (`061775e5…`, `5f6adecc…`).
- Durée réelle : environ 2 h 35 (analyse 30, développement 40, tests 35, intégration et vérifications 50), + 29 % ; dépassement dû au passage au flux à part et au réglage revu après mesure ; à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : trois séries de 50 matchs, deux séries forcées de 30 matchs, deux sondes de 8 matchs, contrôle de 4 matchs (environ 3 h 30 en tout), deux suites complètes.

## Comments

- 23/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Aucune anomalie bloquante. Améliorations facultatives de l'expert : A1, la mémoire du tirage est vidée dès que le ballon sort de la portée du gardien (plus le plus proche à plus de 15 m), un second tirage reste possible sur le même ballon si le plus proche alterne, rare ; à reprendre avec le `v2-realisme/03m` ; A2, libéro excentrique (Rushing Out 99) : fenêtre jusqu'à 53 m de son but, à surveiller à l'écran ; A3, date du statut alignée sur le 23/11. À surveiller : remesurer sorties inattendues et leur issue après le `03m`. Réserves du QC, non bloquantes : date, effet sportif défavorable attribué à `gardien.race` (`03m`), intervalles larges sur les buts.
- 23/11/2026, passage 2 : liste des fichiers revus corrigée (code et tests seulement ; la documentation et `.scratch/` sont du suivi documentaire, hors empreinte, comme aux clôtures précédentes : le passage du statut à « livré » avait changé l'empreinte du passage 1). Expert APPROVED, mêmes améliorations facultatives A1 et A2 ; QC VALIDÉ (inchangé, code identique) ; clôture VALIDÉ.
