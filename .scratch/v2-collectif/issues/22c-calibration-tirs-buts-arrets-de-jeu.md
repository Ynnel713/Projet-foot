# 22c: Calibration, lot 3 : tirs, buts et arrêts de jeu

**Découpé du ticket 22 le 04/11/2026** (audit de granularité). Bases de référence et réserves : `22-calibration-generale.md`.

**What to build:** régler les constantes de tir, d'issue et d'arrêts de jeu sur le moteur calé par 22a et 22b. Chaque levier est proposé avant d'être appliqué. Clôt aussi le ticket 18 (critères de mesure en match reportés) et les critères reportés des tickets `v2-cerveau-joueurs/01` et `03`.

**Attributs :** tous.

**Blocked by:** 22b.

**Bloque :** passent après la calibration, avec un simple contrôle de non-régression : `v2-attributs-restants/10a` et `10b`, `05`, `04a`, `04b`, `09a`, `09b`, `09c`.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Reprise du ticket socle 05 : tirs 8-15 par équipe, buts 2-3,5 par match
- [ ] Indicateurs des tickets 28 à 32 : touches, sorties de but, corners, fautes, tirs par zone, passes à une touche, grosses occasions
- [ ] Temps de jeu effectif (réserve A2 du ticket 29) : 65 à 80 % tant que fautes et remplacements manquent, sinon 53 à 56 % (CIES)
- [ ] Critères reportés des tickets 18, `v2-cerveau-joueurs/01` (écart mesuré sur matchs simulés) et `03` (critère en match) mesurés et clos
- [ ] Les volumes du 22a et la tactique du 22b restent dans leurs fourchettes (contrôle de non-régression)
- [ ] Les chiffres réels sont des indicateurs, pas des objectifs ; leviers et critères validés par le propriétaire avant le code
- [ ] Repris du ticket 22 : courbes partagées de `attributes` ; chiffres réels sourcés, ou « non trouvé »
- [ ] Série d'au moins 40 matchs avec dispersion rapportée ; suite V2 verte ; V1 inchangée

## Reprise du v2-realisme/05g (10/11/2026)

- Poids de la note de tir sur le cadrage presque nul en match : `duel_probability` cubique et exposant 0,5 de l'exécution donnent un coefficient de 0,979 (note 45) à 1,049 (note 80), ± 3,5 % sur l'écart du ballon, soit 2 à 3 points de cadrage entre tranches (50 matchs, `docs/INDICATEURS_V2.md` §22 ; net en scène aux notes extrêmes : 40 % à 69 % à 14 m de 25 à 95). Sensibilité des attributs de tir (forme de la courbe ou exposant) : constante produit, à proposer au propriétaire avec la calibration.

## Repris du ticket v2-realisme/18e (12/11/2026, calibration provisoire 2 sans réglage)

- Faire d'abord `v2-realisme/18k` (le tir manqué coûte le ballon dans la décision) : par zone la conversion est réaliste, le mélange ne l'est pas (21 % des tirs dans la surface contre 68 %).
- Faire d'abord `v2-realisme/05j` (estimateur du contre pour un défenseur en course) avant de relever `shooting.BLOCK_CHANCE` (0,75 mesuré : contrés 22,4 %, repère 22,5 %).
- Rapport : section 34 de `docs/INDICATEURS_V2.md`.
