# 30: Fautes sifflées, avantage et coups francs simples

**What to build:** Une faute est tirée au sort sur un tacle raté (`duel.py:26,36-40,68`, selon Aggression) mais n'a aucune conséquence : le porteur garde le ballon (`match.py:195-198`). Le seul coup franc est celui du hors-jeu, donné directement au défenseur le plus proche. Ce ticket siffle les fautes :

1. **Faute sifflée** : le jeu s'arrête, la faute est tracée (minute, fautif, victime, lieu).
2. **Avantage** : l'arbitre laisse jouer si l'équipe victime garde le ballon dans une position favorable (fenêtre courte, constante proposée) ; sinon il rappelle la faute. L'avantage dépend de la situation (danger de l'équipe victime, zone), pas d'un tirage libre.
3. **Coup franc simple** : ballon posé au lieu de la faute, preneur choisi par proximité et rôle, joué court ou tenté au but selon la distance et la situation. Pas de mur ni de coup franc travaillé (ticket `v2-attributs-restants/02`).
4. **Gravité de la faute** : enregistrée pour le ticket 09 (cartons). Aucun carton ici.

**Attributs :** Aggression (fréquence des fautes, déjà branchée), Tackling (réussite du tacle) ; arbitre sans attribut.

**Blocked by:** 29 (ballon mort et remises en jeu).

**Status:** livré (04/11/2026), validé expert + QC (réserve A1 corrigée ; réserves A2 et A3 acceptées par le propriétaire)

**Origine (03/11/2026) :** revue de réalisme avec le propriétaire (décisions Q8, Q15 : l'avantage entre ici, la perte de temps va au coach, le vent et la pelouse sont laissés de côté).

**Tranché par l'audit du 04/11/2026 :** le penalty est le ticket `v2-attributs-restants/02a`, bloqué par celui-ci et à faire juste après ; reste à choisir, avec les constantes, ce que donne une faute dans la surface entre les deux livraisons.

**Point à trancher avant le code (texte d'origine) :** une faute dans la surface donne un penalty. Le penalty (Penalty Taking, gardien) appartient au ticket `v2-attributs-restants/02`. Soit un penalty simple à conversion neutre (constante proposée) est livré ici pour ne pas laisser de faute en surface sans suite, soit il attend le 02.

**Chiffres réels :** fautes par équipe et par match, part d'avantages joués, part de coups francs tentés au but : **non trouvés, à sourcer**.

## Acceptance criteria

- [x] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code, y compris le point sur le penalty
- [x] Une faute sifflée arrête le jeu et donne un coup franc à l'équipe victime au lieu de la faute ; la faute est tracée
- [x] Scène contrôlée : l'avantage est joué quand l'équipe victime garde le ballon en position favorable, rappelé sinon
- [x] Aggression élevée : plus de fautes, à Tackling égal (mesuré)
- [x] Le coup franc est joué court ou tenté au but selon la distance et la situation (test de cohérence)
- [x] Fautes par match comparées aux chiffres réels sourcés ; temps de jeu effectif remesuré (écart sur le nombre de fautes renvoyé au 22a, voir réserves)
- [x] Indicateurs ajoutés au banc et définis dans `docs/INDICATEURS_V2.md`
- [x] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Décisions du propriétaire (04/11/2026)

Constantes validées avant le code (chiffres réels : `docs/INDICATEURS_V2.md`) :

| Constante | Valeur | Source ou justification |
|---|---|---|
| Faute sur un tacle, gagné ou raté (`duel._FOUL_BASELINE`, amplitude Aggression 0,25 inchangée) | 30 % à Aggression 50 (5 % à 11, 55 % à 99) | une dizaine de fautes par match sur ~35 tacles ; avant, 15 % des seuls tacles ratés (3,5 fautes par match) |
| Avantage (`match.ADVANTAGE_DANGER_MIN`, `ADVANTAGE_S`) | danger ≥ 0,02 (environ 60 m de son but), 3 s | « quelques secondes » (loi 12) ; part réelle non trouvée |
| Coup franc (`restart.DEAD_S`) | 33 s, adversaires à 9,15 m | délai moyen réel, Premier League (The Analyst) |
| Penalty provisoire (`restart.PENALTY_CONVERSION`, `DEAD_S`) | 78 %, 60 s ; raté, le gardien garde le ballon | réel 76-82 % (ligue1.com, CIES) ; durée non sourcée ; remplacé par `v2-attributs-restants/02a` |
| Gravité (`duel._RECKLESS_SHARE`, `_EXCESSIVE_SHARE`) | inconsidérée 12 %, excès d'engagement 0,5 %, indépendantes d'Aggression | loi 12 ; réel non trouvé, à sourcer au 09a |

Fautes de contact (sans tacle) pour atteindre 21-26 fautes par match : **non retenues**, l'écart est renvoyé au ticket 22a.

## Livraison (04/11/2026)

- **Faute** (`duel.resolve_tackle`) : tirée sur tout tacle ; elle annule la récupération. Gravité tirée par `duel.foul_severity`.
- **Avantage** (`match._foul`, `_check_advantage`) : laissé si l'équipe fautée garde le ballon dans une zone qui vaut au moins 0,02 sur la carte du danger ; rappelé si elle le perd (porteur adverse, ou sortie qu'elle provoque) dans les 3 s ; acquis sinon, ou sur but. Une nouvelle faute pendant un avantage met fin au premier.
- **Coup franc** (`restart.foul_restart`, `match._play_restart`) : ballon mort au lieu de la faute, preneur le plus proche (le gardien dans sa propre surface). À la reprise, le preneur décide comme en jeu (ticket 33) entre frapper et passer : la conduite est retirée des options (`decision.choose_action`, `set_piece`), sans quoi une conduite perçue meilleure se changeait en passe et les frappes disparaissaient. Hors-jeu applicable. Pas de mur (ticket 02b).
- **Penalty provisoire** (`match._play_penalty`) : faute dans la surface, point de penalty, gardien sur sa ligne.
- **Trace** : `FoulEvent` (minute, fautif, fauté, lieu, gravité, issue : coup franc, penalty ou avantage) dans `MatchTrace.fouls` ; `RestartEvent.shot`. Non exposés par l'API (pas d'affichage demandé).
- **Tests** : `tests/test_v2engine_fautes.py` (11). Suite complète : 2354 passés, 13 désélectionnés.
- **Correctif A1 (expert)** : un tir de l'équipe fautée réalise l'avantage (`_settle_advantage` dans la branche tir de `_step_ball`) ; un tir arrêté ne ramène plus à la faute.

## Mesures (20 matchs, graines du banc, 04/11/2026)

Avant (`efa65c2`) → après, mêmes graines : fautes 3,5 (4 matchs, tacles ratés seuls) → 9,4 par match (réel 21-26) ; avantages acquis 16 % des fautes ; coups francs 7,75 par match ; penaltys 0,15 par match (réel environ 0,34) ; fautes inconsidérées 9,1 %, excès d'engagement 0 % (aucune sur 188) ; coups francs du dernier tiers frappés au but 37,5 % (très petit échantillon, quelques coups francs par lot de 5 matchs) ; temps de jeu effectif 72,6 → 68,7 % ; tacles 33,7 → 30,8 ; buts 2,95 → 2,70 ; tirs 30,6 → 28,3 par équipe ; passes 10,8 → 10,3 par minute ; passes réussies 67,0 → 67,4 % ; hors-jeu 0,8 → 1,0 ; touches 25,7 → 23,6 ; corners 7,8 → 7,85 ; sorties de but 29,4 → 28,6. Temps de calcul par match 234 → 300 s, faussé par la suite de tests lancée en parallèle de la mesure d'après. Profil Aggression 99 contre 11 (4 matchs) : 15,25 contre 0 faute par match (tacles 5,7 fois plus fréquents et fautes 11 fois plus probables à 99). Déterminisme : même empreinte sur deux exécutions d'un match de 20 min à graine fixée.

## Réserves acceptées par le propriétaire (04/11/2026)

- **R1, fautes** : 9,4 par match contre 21-26 ; renvoyée au ticket 22a (critère ajouté), avec les penaltys qui en découlent.
- **R2, coups francs frappés au but** : critère 10-25 % renvoyé au ticket 02b (preneur désigné par Free Kick Taking, délai de 74,5 s quand il frappe). Mesuré à 5 % avant la correction de la décision du preneur, à 37,5 % après, sur un échantillon trop petit pour conclure ; la surévaluation générale du tir (33 tirs par équipe, réserve du ticket 33, tickets 28 et 22) y pousse.

## Comments

- **04/11/2026, passage 1** (empreinte b7b3adf5) : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ. Réserve A1 : un tir arrêté pendant l'avantage ramenait à la faute (deux occasions pour une faute) ; correctif d'une ligne recommandé, appliqué par délégation du propriétaire (« Considère que je valide automatiquement toutes les reco d'experts », 03/11/2026). A2 (fautes, 22a) et A3 (coups francs frappés, 02b) : réserves déjà acceptées. A4 (hors-jeu pendant l'avantage) et A5 (temps de réception du gardien après un penalty raté) : facultatifs, non traités.
- **04/11/2026, passage 2** (empreinte b56c947e, après A1) : expert APPROVED_WITH_RESERVATIONS (A1 corrigée, condition : suite à 2354 passés, remplie) ; QC BLOQUÉ (sortie de la suite non fournie au contrôleur), puis VALIDÉ au passage 3 avec la sortie (2354 passés, 13 désélectionnés) et le déterminisme. Clôture : **VALIDÉ**. Réserves acceptées par le propriétaire : A2 « Renvoyons au 22.a » ; A2 (penaltys) et A3 « Oui, en réserves ».
