# 15b2: Fautes du duel aérien : bascule, charge sans jouer le ballon, appui par derrière

**Chantier :** `v2-realisme` (découpe du `15b`, validée par le propriétaire le 24/11/2026). **Priorité :** P2. **Catégorie :** exécution.

**Constat vérifié :** aucune faute dans un duel aérien (seules fautes : tacle, charge du duel d'épaule à la course `11c`).

**What to build:** dans un duel aérien (`15b1`), le fautif possible est tiré selon la situation, sa probabilité = facteur × probabilité de faute d'un tacle (Aggression, `duel.foul_probability`), × prudence de surface dans la sienne (`21c1`) :
- épaule contre épaule, de côté, les deux sautent (jeu à l'épaule) : 0,10 (3 % à Aggression moyenne) ;
- contact par derrière en sautant (appui sur l'adversaire, poussée dans le dos) : 0,50 (15 %) ;
- ne saute pas ou ne peut pas atteindre le ballon et reste sous le sauteur (bascule), ou charge sans jouer le ballon : 0,80 (24 %).
Gravité propre au duel aérien : 20 % d'inconsidérées (jaune), 1 % d'excès d'engagement (coude). Coup franc sifflé tout de suite (ballon libre : pas d'avantage, comme le `11c`). Sans faute, celui qui ne saute pas perd le duel.

**Attributs :** Aggression (risque de faute, son seul rôle ici), Decisions (prudence de surface, existante).

**Constantes :** validées par le propriétaire le 24/11/2026 (ci-dessus). Chiffres réels : part des fautes nées des duels aériens non trouvée ; Stats Perform : 19,9 % des duels sont des fautes, tous duels confondus.

**Blocked by:** `15b1`. **Bloque :** `15f`.

**Status:** livré (24/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 48 min), suite complète (environ 22 min).

**Choix du propriétaire avant le code** (24/11/2026) : contact « par derrière » quand le fautif est à plus de 120° du cap de la victime (à moins de 60° de son dos, seuil « de côté » du 11c) ; dans un contact de côté (ou de face), fautif possible : le gagnant de la part du contact (Strength, comme la charge du 11c ; égalité : tiré à 50/50).

**Critères chiffrés** (posés avant le code, 24/11/2026) : chance de faute = facteur × `duel.foul_probability(Aggression)` à 1e-9 près pour les trois situations, × `box_prudence` dans la surface du fautif seulement ; Strength, Jumping Reach, Decisions (hors surface) sans effet sur la chance ; scènes de 400 contacts : part sifflée = chance ± 4 à 6 points ; gravité sur 20 000 tirages : 20 % ± 1, 1 % ± 0,3 ; faute sifflée : coup franc (penalty dans la surface), pas de duel joué ; bascule sans faute : le sauteur joue ; série de 50 matchs : fautes aériennes par match et gravité rapportées (non réglées), buts et tirs dans le bruit ; déterminisme à graine fixée ; suite complète à 3 653 passés + nouveaux cas, 0 ignoré, 14 désélectionnés.

## Acceptance criteria

- [x] Facteurs par situation tenus en scène ; Aggression seule règle le risque
- [x] Fautes aériennes par match mesurées (rapportées, non réglées) ; cartons par gravité
- [x] Déterminisme à graine fixée ; suite complète au compte attendu
- [x] Durée réelle relevée, comparée à l'estimation

## Résultats (24/11/2026)

- Code : `v2engine/duel_aerien.py` : `FOUL_FACTOR` (`SIDE` 0,10, `BEHIND` 0,50, `BASCULE` 0,80), `BEHIND_ANGLE_DEG` 120, `RECKLESS_SHARE` 0,20, `EXCESSIVE_SHARE` 0,01 ; `from_behind` (angle d'approche du tacle, `duel.tackle_approach_angle_deg`), `challenge` (situation et fautif possible d'un duel loyal), `under` (adversaire collé au sauteur qui n'atteint pas le ballon), `foul_chance` (facteur × faute d'un tacle, Aggression, × prudence de surface). `v2engine/duel.py` : `foul_severity` prend les parts en paramètre (défaut inchangé). `v2engine/match.py` : dans la boucle des contacts, avant le duel, le contact est jugé (`_aerial_foul`) ; faute : coup franc ou penalty sifflé tout de suite au lieu de la victime (avantage en cours acquis), pas de duel joué. Trace : `AerialChallengeRecord`, liste `MatchTrace.aerial_challenges`. Banc : fautes aériennes par match, contacts et part sifflée par situation, gravité.
- Tests (`tests/test_v2engine_fautes_aeriennes.py`, 10 cas) : constantes ; chance = facteur × faute d'un tacle (Aggression 1, 50, 99), autres attributs sans effet ; prudence de surface dans la surface du fautif seulement ; situation et fautif (derrière, côté, seuil 120°, dos à dos, égalité tirée) ; bascule (`under` : 1,05 m, exclu, gardien, coéquipier, ballon sous la taille) ; gravité ; scènes de 400 contacts par situation ; bascule sans faute : le sauteur joue ; penalty dans la surface ; déterminisme. `tests/test_v2engine_duel_aerien.py` : fautes neutralisées par une fixture (le duel loyal du 15b1 reste mesuré seul).
- Série (50 matchs appariés, avant : série « après » du `15b1`, code identique à `eb4e7ab`), `docs/INDICATEURS_V2.md` § 80 : 0,78 faute aérienne par match ; contacts jugés par match : côté 5,52, derrière 2,04, bascule 1,02 ; part sifflée 2,5 / 20,6 / 21,6 % (effectifs faibles pour les deux derniers : 102 et 51 contacts) ; gravité 79,5 / 17,9 / 2,6 % (1 excès d'engagement sur 39) ; fautes 21,02 → 21,06, buts 5,08 → 5,26, tirs par équipe 15,31 → 15,14 : dans le bruit ; 165 indicateurs significatifs sur 2 844 (142 attendus par hasard).
- Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes de la trace complète (`b018cd93b08b22a9`, `8cf7998cd56d6cbf` ; 7 et 10 contacts jugés, 0 et 1 faute).
- Suite complète : 3 663 passés, 0 ignoré, 14 désélectionnés (3 653 + 10 cas) ; V1 non touchée.
- Durée réelle : environ 1 h 50 (analyse 25, développement 30, tests 25, intégration et vérifications 30), − 8 % sur l'estimation de 2 h. À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : série de 50 matchs (45,5 min), rejeu de 2 matchs (environ 12 min, 5 annoncées : empreinte sur la trace complète), suite complète (23 min), un match d'essai.

## Comments
- 24/11/2026, passage 1 : expert APPROVED (empreinte `364beab5…`, code et tests ; formule, bornes et tolérances des scènes recalculées à la main) ; QC VALIDÉ. Clôture VALIDÉ.
- Facultatif (expert A1, QC) : tests de la chance de faute en `pytest.approx` relatif 1e-6, le critère disait 1e-9 (formule exacte dans le code).
- Facultatif (expert A2) : documentation (`docs/`) hors du périmètre revu.
- À surveiller (expert, QC) : parts sifflées en série sur de petits effectifs (102 et 51 contacts) ; fautes aériennes liées au faible volume de duels aériens (constat du `15b1`) ; « contacts francs par match » très dispersé d'une série à l'autre.
