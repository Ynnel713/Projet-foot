# Indicateurs de mesure du moteur V2

Référence du ticket `.scratch/v2-collectif/issues/01-banc-de-mesure-tactique.md`. Chaque indicateur est calculé par `scripts/measure_v2.py` sur N matchs à graines fixes.

**Principe (décision du propriétaire, 26/10/2026).** Les valeurs réelles sont des **indicateurs de calibration**, pas des objectifs. Les indicateurs sont lus comme des **distributions conditionnelles** (zone du ballon, score, minute ; phase de jeu une fois le ticket 03 livré), et pas comme une seule moyenne.

**Sources.** Les valeurs réelles des indicateurs tactiques viennent de la recherche documentaire fournie par le propriétaire le 26/10/2026. Les liens sont repris tels quels ; les chiffres sont à relire dans le texte intégral avant de servir de critère d'acceptation.

**Découpages communs.** Zone du ballon : tiers défensif, tiers médian, tiers offensif (du point de vue de l'équipe en possession). Score : mène, égalité, menée. Minute : tranches de 15 min. Situation de jeu (ticket v2-collectif/03) : possession installée, défense placée, transition offensive, transition défensive, dernier tiers ; pour les indicateurs autour du ballon, c'est la situation de l'équipe qui défend. La part du temps passée dans chaque situation est aussi rapportée.

## 1. Indicateurs classiques (cibles déjà validées)

| Indicateur | Définition | Unité | Cible |
|---|---|---|---|
| Passes par minute | Passes des deux équipes / minutes jouées | /min | 15-17 par minute de **jeu effectif** ; 10-11 par minute de match (941 passes par match, Premier League 2023-24) : à redéfinir, voir section 6, R7 |
| Temps par possession de joueur | Temps entre la prise et la perte du ballon par un joueur | s | 2-3 |
| Possession d'équipe | Temps entre deux changements d'équipe en possession | s | 11-16 |
| Passes par possession | Passes pendant une possession d'équipe | nombre | 3-5 |
| Passes réussies | Passes reçues par un coéquipier / passes | % | 70-90 |
| Passes chez l'adversaire | Passes reçues par un adversaire / passes | % | ≤ 25 |
| Receveur visé | Passes reçues par le coéquipier visé / passes | % | ≥ 50 |
| Passes longues | Passes de plus de 32 m : part et réussite | % | 10-19 % des passes, ~47 % réussies |
| Tirs | Tirs par équipe et par match | nombre | 8-15 |
| Tirs de près | Tirs pris à 16 m ou moins du centre du but adverse : part des tirs et nombre par équipe (ticket 23, demande du propriétaire) | %, nombre | Non trouvé pour ce seuil précis : ce n'est pas la statistique « tirs dans la surface » (surface = 16,5 m de profondeur × 40,3 m, soit 665 m², contre un demi-disque de 402 m² ici), donc pas de comparaison directe possible. Mesure moteur : 1,05 par équipe, 7,8 % des tirs. |
| Buts | Buts par match | nombre | 2-3,5 |
| Tacles | Tacles tentés par match | nombre | 30-40 |
| Hors-jeu | Hors-jeu sifflés par match, et par équipe | nombre | 3,2-3,5 par match, soit 1,6-1,8 par équipe (Ligue 1 2023-24 et 2024-25 ; 3,54 en Premier League 2024-25) |
| Remises en jeu | Touches, sorties de but, corners et engagements joués par match (ticket 29, `RestartEvent` de la trace) | nombre | touches ≈ 42 (PL 2018-19), corners ≈ 10 ; sorties de but : non trouvé ; critère du ticket 29 : touches 30-55, corners 6-14, sorties de but 8-25 |
| Remises jouées long | Part des remises dont le receveur visé est à plus de 25 m du preneur (`restart.LONG_RESTART_M`), par type | % | sorties de but : environ 50 % sortent de la surface (PL 2024-25, Opta) ; touches et corners : suivi |
| Issues du tir | Part des tirs tracés (`ShotEvent`, contrés et penaltys compris) cadrés (but, capté, repoussé, claqué), contrés, à côté, et conversion (buts / tirs) (ticket 28b) | % | cadrés 30-35 %, contrés 20-28 % (22,5 % Bundesliga 2015-16), conversion 10-11 % : ordres de grandeur du ticket 28 |
| Buts dans la surface | Part des buts marqués d'un tir parti de la surface de réparation (ticket 28b) | % | 80-90 % (ordre de grandeur du ticket 28) |
| Issues des arrêts | Part des arrêts captés, repoussés en jeu, claqués derrière la ligne (corner) ; arrêts par match (ticket 28b) | %, nombre | répartition non publiée (Opta la relève sans la publier) ; environ 20 % des corners viennent d'un arrêt (ordre de grandeur, sans méthode publiée) |
| Origine des tirs | Part des tirs selon la façon dont le tireur a eu le ballon : passe au sol, en retrait, en profondeur, centre, dribble (plus de 5 m porté), rebond, récupération, coup franc, penalty (ticket 28b) | % | suivi, pas de cible |
| Qualité moyenne de l'occasion | Moyenne, par tir tracé, de la chance de but de l'occasion au moment du tir (ticket 28a, contre compris) | probabilité | environ 0,10-0,11 (xG moyen d'un tir en Big 5, ordre de grandeur) |
| Temps de jeu effectif | 1 − temps de ballon mort / temps de match (ticket 29 ; durée réelle du match, temps additionnel compris, depuis le ticket v2-realisme/01d) | % | réel 53-56 % (CIES 2026) avec fautes, remplacements et blessures ; sans eux, critère du ticket 29 : 65-80 % |
| Fautes | Fautes commises par match, sifflées ou laissées en avantage (ticket 30, `FoulEvent` de la trace) ; aussi par profil (Aggression haute ou basse) | nombre | 21 (Premier League) à 26,4 (Ligue 1) par match ([CIES](https://football-observatory.com/Foul-analysis-at-big-5-league-level-from-2219), saison non précisée) ; critère du ticket 30 : 18-28 |
| Avantages acquis | Fautes laissées en avantage et non rappelées / fautes (ticket 30) | % | Non trouvé |
| Coups francs et penaltys | Coups francs et penaltys sifflés par match (ticket 30) | nombre | penaltys environ 0,34 par match (Ligue 1 2023-24 : 105 penaltys) ; critère du ticket 30 : 0,15-0,5 |
| Coups francs frappés au but | Coups francs joués dans le dernier tiers adverse (35 m) et frappés directement / coups francs joués dans ce tiers (ticket 30) | % | environ 19 % (Manchester City, Opta, [The Analyst](https://theanalyst.com/articles/free-kicks-why-are-teams-not-shooting-as-much)) ; critère du ticket 30 : 10-25 % |
| Gravité des fautes | Part des fautes inconsidérées (jaune) et avec excès d'engagement (rouge), loi 12 (ticket 30, pour les cartons du ticket `v2-attributs-restants/09a`) | % | Non trouvé ; constantes 12 % et 0,5 % |
| Choix du porteur | Part de passes, conduites et tirs | % | suivi |
| Distance | Km par joueur de champ, par poste | km | 9-14 ; ordre des postes de Bradley 2009 ; 10,2 à 12,0 km par poste (section 6, R4) |
| Haute intensité, en distance (ticket v2-realisme/01d) | Distance des joueurs de champ au-dessus de 19,8 km/h / distance totale ; et distance au-dessus de 19,8 km/h par joueur, par poste | %, m | 6-10 % ; 586 à 1 113 m par poste (section 6, R6) |
| Temps au-dessus de 25 km/h (ticket v2-realisme/01d) | Temps cumulé des joueurs de champ au-dessus de 25 km/h / temps cumulé | % | suivi |
| Sprints (ticket v2-realisme/01d) | Passages au-dessus de 25 km/h tenus au moins 1 s, par joueur de champ et par match, et par poste | nombre | suivi, pas de repère sourcé |
| Passes par match (ticket v2-realisme/01d) | Passes tentées des deux équipes / matchs ; et passes / minutes de jeu effectif (durée réelle du match, temps additionnel compris, moins le ballon mort) | nombre, /min | 890-940 par match ; 15-17 par minute de jeu effectif (section 6, R7) |
| Haute intensité | Part de la distance au-dessus de 25 km/h ; part du temps au-dessus de 19,8 km/h | % | 2-3 ; 2-5 (la source mesure la distance au-dessus de 19,8 km/h : à redéfinir, voir section 6, R6) |
| Baisse de fin de match | Course au-dessus de 19,8 km/h : dernier quart d'heure contre premier | % | 10-30 |

## 2. Indicateurs tactiques

| # | Indicateur | Définition | Unité | Valeur réelle |
|---|---|---|---|---|
| 1 | Longueur et largeur d'équipe | Écart en x et en y entre joueurs de champ extrêmes, avec et sans ballon | m | Environ 31-46 m de long et 35-48 m de large en match professionnel ; bloc médian de la Coupe du monde 2022 : 27,2 × 40,1 m ([PMC8805357](https://pmc.ncbi.nlm.nih.gov/articles/PMC8805357/), [FIFA](https://www.fifatrainingcentre.com/en/fwc2022/technical-and-tactical-analysis/controlling-the-game-without-the-ball--the-mid-block-and-compactness.php)) |
| 1b | Surface et stretch index | Aire de l'enveloppe convexe des joueurs de champ ; distance moyenne des joueurs au centre de l'équipe | m², m | Suivi |
| 2 | Distance entre lignes | Joueurs de champ regroupés en 3 lignes selon x ; écart entre lignes successives | m | Défense-milieu 10,2 ± 3,8 m ; milieu-attaque 13,3 ± 4,2 m ([Forcher et al. 2023](https://pure.rug.nl/ws/portalfiles/portal/1058208693/forcher-et-al-2023-is-a-compact-organization-important-for-defensive-success-in-elite-soccer-analysis-based-on-player.pdf), [PMC12511544](https://pmc.ncbi.nlm.nih.gov/articles/PMC12511544/)) |
| 1c | Suivi du ballon par le bloc | Pente de la droite des moindres carrés du centre d'équipe (joueurs de champ) en fonction de la position du ballon, en longueur et en largeur, par match (ticket 04) | sans unité | Le centre suit surtout le ballon dans la longueur (Frencken et al. 2012, cité au ticket 04) ; pente non trouvée |
| 2c | Écart ligne-ballon | Sans ballon, distance entre le ballon et la ligne défensive, dans l'axe ; aussi selon que le porteur est pressé (défenseur à moins de 3 m) ou libre (9 m ou plus) (ticket 05) | m | Médiane 27,6 m, la moitié des cas entre 18 et 37 m ([arXiv 2511.06191](https://arxiv.org/html/2511.06191v1)) |
| 2d | Passes en profondeur | Passes dont le receveur est au-delà du dernier défenseur de champ adverse : part et réussite (ticket 05) | % | Non trouvé |
| 2b | Hauteur du bloc | Position x moyenne de la ligne défensive, depuis son propre but | m | Suivi |
| 3 | Compacité autour du ballon | Distance moyenne au ballon des 5 défenseurs les plus proches | m | Légèrement plus compacte sur les séquences défensives réussies, effet faible ([Forcher et al. 2023](https://research.rug.nl/en/publications/is-a-compact-organization-important-for-defensive-success-in-elit/)) |
| 3b | Supériorité locale | Défenseurs moins attaquants dans un rayon de 10 m autour du ballon | nombre | Supériorité à 10 m : récupération en moins de 5 s portée de 30,2 % à 36,2 % ([PMC13581790](https://pmc.ncbi.nlm.nih.gov/articles/PMC13581790/)) |
| 4 | Solutions de passe ouvertes | À chaque décision du porteur, coéquipiers dont la probabilité de réception sans interception dépasse un seuil de disponibilité (0,7 depuis le ticket 06, 0,5 avant) | nombre | Pas de moyenne universelle ; méthode par probabilité de réception ([Springer 2022](https://link.springer.com/article/10.1007/s10618-022-00827-2)) |
| 5 | Défense préventive | En possession, joueurs de champ derrière le ballon, comparés aux attaquants adverses dans cette zone ; et, 1 s après une perte, part des cas avec 4 joueurs ou plus derrière le ballon | nombre, % | 3,70 défenseurs contre 2,01 attaquants en moyenne ; 4 ou plus à 1 s : signal favorable au contre-pressing ([PMC13581790](https://pmc.ncbi.nlm.nih.gov/articles/PMC13581790/), [Springer 2021](https://link.springer.com/article/10.1007/s10618-021-00763-7)) |
| 6 | Récupération après une perte | Temps entre la perte et la reprise, en classes 0-5 s, 5-12 s, 12-15 s, plus de 15 s | % par classe | Bundesliga : 30,2 % en moins de 5 s sans supériorité locale ([PMC13581790](https://pmc.ncbi.nlm.nih.gov/articles/PMC13581790/)) |
| 7 | Repli après une perte | Trois mesures distinctes : latence (délai avant que le centre de l'équipe recule à plus de 1 m/s), vitesse de recul, temps pour reformer le bloc (longueur revenue sous sa valeur défensive médiane) ; depuis le ticket v2-collectif/10, vitesse vers son but, 1,5 s après la perte, des joueurs qui étaient devant le ballon (aussi par profil) | s, m/s, s | Pas de valeur publique robuste ; Bundesliga 2010/11 : les meilleures équipes récupèrent le ballon environ 1 s plus vite que les autres (Vogelbein, Nopp et Hökelmann 2014, temps de récupération, pas de réaction) |
| 8 | Pertes en transition | Ballon reperdu moins de 5 s après une récupération : nombre par match et part des récupérations, par zone | /match, % | Définition cohérente avec la littérature ([PubMed 38045740](https://pubmed.ncbi.nlm.nih.gov/38045740/)) |
| 9 | Couverture du presseur | Part du temps de pressing pendant lequel un second défenseur est dans la zone de couverture : ellipse orientée vers le but, d'environ 3 m derrière le porteur à 9 m devant lui | % | Zone de pression elliptique selon l'angle ([KIT](https://publikationen.bibliothek.kit.edu/1000187744/170106643), [PMC5968892](https://pmc.ncbi.nlm.nih.gov/articles/PMC5968892/)) |
| 10 | Appels et redondance | Appel : course de plus de 0,7 s au-dessus de 15 km/h d'un coéquipier du porteur ; appels par joueur et par match, par poste ; part des appels simultanés visant la même zone (moins de 5 m) | /joueur/match, % | 15,1 appels par joueur et par match, de 5,5 (défenseurs centraux) à 19,2 (milieux offensifs) ([CIES, rapport mensuel n° 88, octobre 2023](https://football-observatory.com/IMG/sites/mr/mr88/en/), données SkillCorner ; la référence PLOS One 2022 citée auparavant est une revue systématique qui ne contient pas ces chiffres, voir section 6, R5) |
| 11 | Occasions de contre | Tirs dans les 15 s après une récupération, séparés selon la zone de récupération : son propre camp (contre-attaque) ou camp adverse (récupération haute) | /match | Fenêtre de 15 s jusqu'au tir ([FIFA EFI](https://www.fifatrainingcentre.com/media/native/tournaments/womens-world-cup/2023/FIFA%20Enhanced%20Football%20Intelligence%20(EFI)%20Explainations_EN%20v1.1.pdf)) |
| 12 | Passe sans gain suivie d'une passe qui fait avancer (C2) | Passe réussie qui rapproche le receveur du but de moins de 5 m, suivie d'une passe du receveur (réussie ou non) qui gagne 10 m ou casse une ligne adverse (la moyenne d'une ligne est entre le passeur et la cible) (tickets 13 et 14) | % | Non trouvé ; 39 % visé, renvoyé au ticket 22 |
| 13 | Retour au passeur et une-deux | Passe réussie dont le receveur rend le ballon au passeur dans les 3 s (passe de retour réussie ou non) ; une-deux si le ballon a avancé de 5 m ou plus entre le départ de la première passe et l'arrivée de la seconde (ticket 14) | %, /équipe/match | Fréquence des une-deux non trouvée |
| 14 | Troisième homme | Passe réussie suivie de la passe prévue par le passeur (plan de passe), réussie. Vaut 0 sans plan : ne se compare pas entre les deux modes (ticket 14) | /équipe/match | Une à deux attaques réussies par match pour les meilleures équipes, définition plus étroite ([Footballytics](https://www.footballytics.ch/post/tactics-and-data-outplay-opponents-with-pass-combinations)) |
| 15 | Triangles | À une décision du porteur, deux coéquipiers à 30 m ou moins, les trois passes du triangle à 0,7 ou plus, angle au porteur de 20 à 160 degrés : part des décisions avec au moins un triangle (ticket 14) | % | Non trouvé |
| 16 | Plans de passe | Plans lus par match, hors contre-attaque, et leur sort : tenus, abandonnés (cible vue, ligne fermée), abandonnés (cible hors de la Vision ou hors-jeu évident), refusés (Teamwork) (ticket 14) | /match, % | Mesure interne |
| 17 | Épisodes APPEL | Épisodes du rôle `APPEL` (rôle APPEL après un autre rôle, `Collector.on_role`), par joueur et par 90 min, par poste. À distinguer de #10 : #10 compte les courses rapides de n'importe quel coéquipier, #17 les appels que le moteur a **décidés** (ticket v2-realisme/02h, réserve A1 du 02g) | /joueur/90 min | Pas de repère (le repère CIES de #10 juge la course, pas la décision) |
| 18 | Rôle des appels du banc | Part des appels de #10 selon le rôle du joueur au **départ** de la course (`appel`, `tenir sa place`, `replacement`, `soutien`…) : mesure la part du replacement à pleine vitesse comptée comme appel (02h) | % | Mesure interne |
| 19 | Appelants simultanés | Joueurs de l'équipe en possession au rôle `APPEL` au même tick, par situation de jeu : moyenne sur les instants de possession, maximum d'un match et maximum de la série (02h). À lire contre `cerveau.CALLER_CAP` (2, 3, 3) ; la situation du banc est la situation réelle, celle du moteur est la situation perçue (en retard) | nombre | Mesure interne |
| 20 | Alternance APPEL / TENIR dans une possession | Passages direct APPEL → TENIR ou TENIR → APPEL d'un joueur au sein d'une même possession (un autre rôle entre les deux interrompt la suite) ; part des états qui se terminent en moins de 1,5 s (02h, réserve A2 du 02g). Le compteur du 02g (`alternances appel / tenir`) mélange les possessions successives et reste rapporté | /joueur/match, % | Diagnostic du 02g : 24 % de moins de 1,5 s (10 min, 1 match, autre définition) |
| 21 | Appelant retenu et passe ouverte | À chaque seconde d'une possession, part des joueurs au rôle `APPEL` dont la passe du porteur a une chance de réception d'au moins 0,7 à moins de 40 m (02h, réserve A3 du 02g, filtre « espace exploitable » non réalisé) | % | Mesure interne |
| 22 | Place moyenne par poste | Profondeur (m depuis sa propre ligne de but) et côté (m depuis l'axe, négatif = gauche de l'équipe vu de son but, convention de `formation._LANE`) des joueurs de champ, moyennés par joueur puis par poste, avec et sans ballon (échantillon toutes les secondes, 02h) | m | Pas de repère sourcé |
| 23 | Part du temps du côté de son poste | Pour LB, AG (côté gauche) et RB, AD (côté droit) : part des échantillons où le joueur est du bon côté de l'axe ; aussi hors transition (situations ni `transition offensive` ni `transition défensive`) (02h) | % | Seuil de contrôle du ticket 02h : plus de 90 % hors transition (à valider) |

**Plus tard, dans les tickets concernés** (ils demandent des mécanismes qui n'existent pas encore) : temps d'arrivée du défenseur (ticket 09), lignes adverses cassées et valeur de l'espace créé (ticket 13 : mesurées hors du banc, dans le ticket ; lignes cassées intégrées au banc au ticket 14, valeur de l'espace créé encore hors du banc), contrôle de la profondeur (ticket 05), indicateurs par phase de jeu (ticket 03), conditionnement par style tactique et qualité relative des équipes (ticket 22).

## 3. Seuils de mesure

Ils définissent la mesure et ne changent pas le jeu (`scripts/v2_indicators.py`). Ceux qui sont marqués « proposé » sont soumis à la validation du propriétaire.

| Seuil | Valeur | Origine |
|---|---|---|
| Solutions de passe : probabilité de réception | ≥ 0,7 (ticket 06, 30/10/2026 ; 0,5 avant, sur la zone plate de la courbe de duel) | Recherche du propriétaire |
| Solutions de passe faciles : probabilité de réception | ≥ 0,8 | Validé par le propriétaire (31/10/2026, ticket 08) |
| Solutions de passe : portée | ≤ 40 m | Proposé |
| Presseur : distance au porteur | < 3 m | Proposé |
| Ellipse de couverture | 3 m derrière le porteur à 9 m devant, demi-largeur 4 m | Recherche du propriétaire ; demi-largeur proposée |
| Supériorité locale : rayon | 10 m | Recherche du propriétaire |
| Compacité autour du ballon | 5 défenseurs les plus proches | Forcher et al. 2023 |
| Appel | > 0,7 s au-dessus de 15 km/h, créant une option de passe (ou conclu par la réception) ; aussi ramené à 90 min (× 5 400 s / durée du match), comme la source (ticket v2-realisme/01d) | CIES n° 88 (section 6, R5) |
| Sprint | Au-dessus de 25 km/h pendant au moins 1 s (un sprint encore en cours au coup de sifflet final compte) | Proposé (ticket v2-realisme/01d), accepté d'office par le propriétaire |
| Appels redondants | Simultanés, finissant à moins de 5 m l'un de l'autre | Proposé |
| Alternance courte APPEL / TENIR | État qui se termine en moins de 1,5 s (`SHORT_SWITCH_S`) | Proposé (ticket v2-realisme/02h), accepté d'office par le propriétaire |
| Côté de son poste | Du bon côté de l'axe du terrain (y = 34 m), échantillon toutes les secondes, vu de son propre but | Proposé (ticket v2-realisme/02h), accepté d'office par le propriétaire |
| Perte en transition | < 5 s après la récupération | Recherche du propriétaire |
| Occasion de contre | Tir < 15 s après la récupération | Recherche du propriétaire |
| Repli : seuil de recul, fenêtre de suivi | 1 m/s ; 10 s | Proposé |
| Repli : bloc reformé | Longueur revenue sous sa médiane sans ballon du match, si elle la dépassait à la perte | Proposé |
| Passe longue | > 32 m | Opta |

**Cas particuliers.** Un but clôt la possession : l'engagement n'est compté ni comme une perte ni comme une récupération. Un appel interrompu par une perte de balle n'est pas compté. Les lignes sont obtenues en coupant aux deux plus grands écarts de profondeur : la coupe est fragile quand un attaquant est isolé (4-2-3-1).

## 4. Tests tactiques

- **Scénario rejouable** : positions de départ fixées, événement forcé (exemple : le latéral droit monte, le ballon est perdu), N graines ; un indicateur comparé avec et sans le mécanisme testé.
- **Profils** : un attribut forcé à 99 pour une équipe et à 11 pour l'autre, puis les rôles inversés pour neutraliser l'avantage du terrain.
- **Diversité** : dispersion des indicateurs d'une graine à l'autre, ni nulle ni excessive.
- **Déterminisme** : même graine, mêmes chiffres.

## 5. Mesure de référence (moteur à `07f33b3`, 26/10/2026)

`uv run python -m scripts.measure_v2 20` (graines 20260923 à 20260942). Point de comparaison pour les tickets suivants ; le découpage par zone, score et minute s'obtient avec `--detail`.

| Indicateur | Référence | Valeur réelle |
|---|---|---|
| Passes par minute | 15,1 | 15-17 |
| Passes réussies / chez l'adversaire | 75,5 % / 24,4 % | 70-90 % / ≤ 25 % |
| Receveur visé | 54,9 % | ≥ 50 % |
| Passes longues : part / réussite | 2,2 % / 81 % | 10-19 % / ~47 % |
| Tirs par équipe / buts par match | 11,4 / 3,65 | 8-15 / 2-3,5 |
| Tacles par match | 38,4 | 30-40 |
| Temps par possession de joueur / possession d'équipe | 2,0 s / 14,7 s | 2-3 s / 11-16 s |
| Km par joueur de champ | 24,3 (défenseurs centraux 20,2, avant-centres 32,5) | 9-14 |
| Distance au-dessus de 25 km/h / temps au-dessus de 19,8 km/h | 45 % / 37 % | 2-3 % / 2-5 % |
| Baisse de la course intense en fin de match | 18 % | 10-30 % |
| Longueur × largeur sans ballon | 45,0 × 35,9 m | 31-46 × 35-48 m |
| Défense-milieu / milieu-attaque (sans ballon) | 16,7 / 23,4 m | 10,2 / 13,3 m |
| Compacité autour du ballon | 19,6 m | — |
| Supériorité locale des défenseurs | -0,5 | — |
| Défense préventive : joueurs derrière le ballon / adversaires | 8,0 / 1,3 | 3,7 / 2,0 |
| 4 joueurs ou plus derrière le ballon 1 s après la perte | 98 % | — |
| Récupération 0-5 s / 5-12 s / 12-15 s / plus de 15 s | 33 / 26 / 8 / 34 % | 30 % en moins de 5 s |
| Pertes en transition (part des récupérations) | 32 % | — |
| Tirs de contre par match (récupération dans son camp / camp adverse) | 0,25 / 21,3 | — |
| Repli : latence / vitesse de recul / bloc reformé | 1,6 s / -0,25 m/s / 2,9 s | — |
| Couverture du presseur | 56 % | — |
| Solutions de passe ouvertes | 5,4 | — |
| Appels par joueur et par match | 156 (défenseurs centraux) à 507 (avant-centres) | 5,5 à 19,2 |
| Appels redondants | 28 % | — |

**Profils (20 matchs, 10 affiches jouées deux fois, rôles inversés).** Work Rate 99 contre 11 : chiffres identiques, car le moteur à `07f33b3` n'utilise pas encore Work Rate. Cela confirme que le plan d'expérience n'introduit pas d'écart parasite. Off the Ball 99 contre 11 : 271 contre 227 appels par joueur, 18,0 contre 11,1 km de course intense, 26,5 contre 19,5 km.

**Lecture.** Les écarts aux valeurs réelles reflètent les défauts connus du moteur actuel (tout le monde sprinte, bloc figé, personne ne couvre) que le chantier « intelligence collective » doit corriger : ce ne sont pas des cibles à régler une par une.

**Situations de jeu (ticket v2-collectif/03, 20 matchs, moteur à `4205ab9`).** Part du temps, deux équipes confondues : possession installée 29 %, défense placée 30 %, transition défensive 20 %, transition offensive 19 %, dernier tiers 2 %. Valeur réelle comparable : non trouvée ; le dernier tiers, très bas, est à surveiller quand le soutien du porteur et les appels (tickets 06 et 16) changeront la progression.

**Bloc de référence dynamique (ticket v2-collectif/04, 20 matchs, 27/10/2026).** Avant → après : bloc sans ballon 45,0 × 35,9 → 40,9 × 41,2 m ; avec ballon 38,2 × 39,0 → 42,5 × 48,7 m ; défense-milieu / milieu-attaque sans ballon 16,7 / 23,3 → 16,7 / 18,8 m ; suivi du ballon (pente, longueur / largeur) 0,15 / 0,16 → 0,54 / 0,40 ; compacité autour du ballon 19,6 → 13,7 m ; couverture du presseur 56 → 69 % ; passes 15,1 → 16,8 par minute ; passes chez l'adversaire 24,6 → 30,6 % ; tirs 11,1 → 13,7 par équipe ; buts 3,45 → 3,0 ; tacles 39,5 → 52,0 ; km par joueur 24,3 → 25,8 ; dernier tiers 2 → 6 % du temps. Profils : Positioning 99 contre 11, écart-type défense-milieu 4,68 contre 5,01 m ; Teamwork 99 contre 11, stretch index 19,85 contre 19,94 m (critère reporté au ticket 07).

**Hauteur de la ligne défensive (ticket v2-collectif/05, 20 matchs, 27/10/2026).** Ticket 04 → ticket 05 : hauteur de ligne sans ballon 16,7 → 32,7 m ; écart ligne-ballon 35,5 → 18,8 m ; défense-milieu / milieu-attaque sans ballon 16,7 / 18,8 → 13,0 / 13,4 m ; longueur sans ballon 40,9 → 30,1 m ; compacité autour du ballon 13,7 → 7,5 m ; passes en profondeur 4,1 % (réussies à 66 %) ; passes chez l'adversaire 30,6 → 33,8 % ; tirs 13,7 → 18,1 par équipe ; buts 3,0 → 4,7 ; tirs de contre (récupération dans son camp) 4,8 → 9,5 ; tacles 52 → 58 ; km par joueur 25,8 → 30,6. Écart sur tirs et buts reporté aux tickets 10 et 23. Profil Pace 99 contre 11 : ligne à 38,9 contre 27,1 m.

**Hors-jeu (ticket v2-collectif/23, 20 matchs, 28/10/2026).** Ticket 05 → ticket 23 (après la deuxième passe du 28/10/2026, le passeur n'est plus omniscient) : tirs 18,1 → 13,5 par équipe (fourchette réelle 8-15) ; buts 4,7 → 3,65 par match (2-3,5, donc légèrement au-dessus) ; tirs de contre après récupération dans son camp 9,5 → 5,6, dans le camp adverse 20,0 → 15,5 ; hors-jeu 3,65 par match, soit 1,83 par équipe (réel 3,2-3,5 par match, 1,6-1,8 par équipe) ; hauteur de ligne sans ballon 32,7 → 33,4 m ; écart ligne-ballon 18,8 → 17,8 m ; longueur sans ballon 30,1 → 30,3 m ; compacité autour du ballon 7,5 → 7,4 m ; passes par minute 16,8 → 17,3 ; passes chez l'adversaire 33,8 → 33,9 % ; passes en profondeur 4,1 → 0,9 % (valeur réelle non trouvée : l'attaquant est tenu derrière la ligne, donc moins de passes reçues au-delà du dernier défenseur ; cause mesurée, voir plus bas) ; tirs de près (16 m ou moins) 1,05 par équipe, soit 7,8 % des tirs ; tacles 58 → 59,9 ; km par joueur 30,6 → 30,5. Le hors-jeu fait **baisser** les tirs de contre au lieu de les faire exploser : le porteur ne sert plus un coéquipier qu'il voit nettement au-delà de la ligne (`PASS_OFFSIDE_MARGIN_M`, 0,5 m), et sans ce filtre le moteur en était à 21,5 hors-jeu et 28 tirs de contre par match (21,5 → 3,5 hors-jeu ; un seuil de 1 m laissait encore 7,5).

**Correction de la deuxième passe (29/10/2026, option S2 choisie par le propriétaire).** Le seuil du passeur grandissait avec la Vision, alors que tout ce qu'il dépasse la tolérance de l'arbitre est une passe sifflée : 5,52 passes vers un hors-jeu pour 1 000 passes à Vision 70 et plus, contre 1,55 à 50-69. Il devient un angle mort qui se resserre avec la Vision (0,79 m à 11, 0,5 m à 63,4, 0,3 m à 100). Mesure sur 20 matchs, mêmes graines : hors-jeu 3,65 → **3,1 par match, 1,55 par équipe** (réel 3,2-3,5 et 1,6-1,8, donc juste en dessous) ; passes vers un hors-jeu pour 1 000 : 6,39 (Vision < 50), 2,42 (50-69), 2,48 (70 et plus) ; tirs 13,2 par équipe ; buts 3,45 par match ; tirs de contre 5,55 (récupération dans son camp). Les chiffres de la deuxième passe ci-dessus (3,65 hors-jeu) sont ceux d'avant la correction ; les écarts autres que le hors-jeu ne sont pas attribuables (paragraphe suivant).

**Point d'ancrage du seuil du passeur (deuxième passe).** Le seuil moyen de 0,5 m devait rester 0,5 m après modulation par la Vision : il faut donc l'ancrer sur la Vision **moyenne des joueurs**, et non sur le milieu de l'échelle 11-99 (55). Mesuré sur la base (`uv run python -m scripts.vision_moyenne`) : 63,4 pour les 198 titulaires de Ligue 1 (joueurs sans attributs comptés 60, comme dans le moteur). Ancré sur 55, le seuil moyen montait à 0,58 m et le hors-jeu à 4,45 par match (20 matchs) ; ancré sur 63,4, il revient à 3,65. C'est la seule comparaison attribuable de cette passe : même code, une seule constante changée. L'erreur de lecture de la ligne est un second levier, volontairement modeste (0,25 m à Vision 0, 0,05 m à 99), à calibrer au ticket 22.

**Attribution des écarts (à lire avant les chiffres).** Le moteur est déterministe à graines fixes, mais le tirage de l'erreur de lecture consomme le flux aléatoire du match : il décale donc les scores de tous les matchs suivants. Les écarts entre la première et la deuxième passe (tacles 64,9 → 59,9, tirs 14,4 → 13,5, buts 3,25 → 3,65, hors-jeu 3,5 → 3,65) **ne sont donc pas attribuables** à la modulation par la Vision ; ils donnent un ordre de grandeur, pas une mesure d'effet. Pour un effet propre, il faudra un flux aléatoire dédié au tirage de perception (à faire au ticket 22).

**Réserve transmise au ticket 22 (validée par le propriétaire le 28/10/2026).** Les tacles sont à 59,9 par match alors que la valeur réelle est de 30 à 40 : la dérive ne vient pas du hors-jeu (elle est continue depuis le ticket 04 : 52 → 58), il faudra regarder du côté de la décision de tenter le tacle (Aggression, `should_attempt_tackle`) et de la densité des duels. Non traitée ici.

**Rôles défensifs (ticket v2-collectif/07, 10 matchs, 30/10/2026).** Avant (`4d71418`) → après : défenseurs à moins de 3 m du porteur 2,95 → 1,45 en moyenne, 3 ou plus 49 → 13 % des instants ; tirs 17,75 → 11,25 par équipe ; buts 5,3 → 1,4 par match (sous la fourchette réelle de 2-3,5) ; tacles 86 → 72,4 ; passes réussies 64,3 → 70,5 % ; hors-jeu 1,1 → 0,9 par match ; couverture du presseur (toutes zones) 79,5 → 70,4 %, la couverture n'existant plus que dans la moitié défendue ; km par joueur de champ 23,2 → 20,7. Profils : Marking 99 contre 11, distance marqueur-attaquant 4,21 contre 5,74 m (médianes, 4 matchs) ; Teamwork 99 contre 11, plus compact sur 5 affiches sur 5 (stretch index, Δ +0,26 m). Stabilité des rôles (4 matchs) : 0 % de ping-pong pour le presseur, 3,7 % pour le marqueur. Pendant une passe en vol (36 % du temps de jeu), aucun rôle défensif n'est encore attribué : reporté au ticket 09.

**Appelants et alternance (ticket v2-realisme/02g, 50 matchs, 06/11/2026, moteur à la base `a86589a` plus 02g).** Nouvel indicateur du banc : `alternances appel / tenir par joueur et par match` (passages de `APPEL` à `TENIR` ou l'inverse, `Collector.on_role`). Mesure : 136 par joueur et par match, soit un passage environ toutes les 40 s ; sur 10 minutes, 297 passages dont 24 % de moins de 1,5 s. Appels par joueur et par 90 min 48,5 → 45,4 (défenseurs centraux 22,3 → 19,8, milieux offensifs 88,0 → 80,7, avant-centres 97,2 → 99,1) : l'ordre des postes est cohérent mais les volumes restent 2 à 10 fois au-dessus du repère R5, le banc comptant aussi le replacement rapide des joueurs qui tiennent leur place.

**Soutien du porteur (ticket v2-collectif/06, 20 matchs, 31/10/2026).** Avant (`8043889`) → après : solutions de passe ouvertes (seuil 0,7) 1,86 → 1,96 ; regroupement avec ballon (coéquipiers à moins de 5 m hors duel) 6,8 → 7,0 %, dont la moitié à côté du porteur (diagnostic, 4 matchs) : le critère, validé par le propriétaire le 31/10/2026, l'exclut désormais (environ 3,3 %) ; sans ballon 8,4 → 8,6 % ; au moins un joueur derrière le ballon en possession installée 100 → 100 % ; buts 1,95 → 2,75 par match ; tirs 11,35 → 12,1 par équipe ; hors-jeu 0,6 → 1,05 par match ; appels des DC, latéraux et MC +30 à +50 % ; temps de calcul +9 %. Profils : Off the Ball 99 contre 11, solutions de passe 1,96 contre 1,92. Teamwork : la règle d'équilibre (2 joueurs de champ derrière le ballon) ne s'est déclenchée qu'une fois en 4 matchs, environ 7 joueurs y étant déjà ; son effet est vérifié par les tests unitaires, pas en match (critère validé le 31/10/2026).

**Correction C5 du ticket 06 (diagnostic, 4 matchs, 31/10/2026).** Les mesures de 20 matchs ci-dessus datent d'avant C5 : pendant une passe de son équipe, les coéquipiers autres que le receveur gardent leur appel au lieu de courir au ballon. Regroupement avec ballon, porteur inclus : 6,8 → **4,9 %**. Le reste est fait à 93 % de croisements passagers (les deux joueurs visent des points écartés de plus de 5 m), à 89 % en transition offensive. Point de départ du ticket 22, qui refera la mesure sur 20 matchs (réserve A1 du ticket 06).

**Transition défense-attaque (ticket v2-collectif/11, 4 matchs, 01/11/2026).** Avant (`e8114a0`) → après : tirs 7,9 → 9,625 par équipe ; buts 2,0 → 2,25 par match ; tirs de contre après récupération dans son camp 1,75 → 3,5 par match, dans le camp adverse 10,25 → 11,25 ; tacles 55,75 → 54,0 ; hors-jeu 1,0 → 1,0 ; pertes en transition 22,5 → 23,4 % des récupérations. Choix à la récupération (diagnostic hors dépôt) : contre-attaque sur 36 % des récupérations, 65,5 % quand elle est jouable et 29,6 % sinon ; tiers offensif atteint en 15 s 40,6 % en contre-attaque contre 25,3 % en conservation (récupération dans son camp : 31,8 contre 13,6 %). Pressé en contre-attaque, le porteur peut ressortir en retrait, mais après toute passe vers l'avant (réserve A2 de l'expert). Part réelle des contre-attaques : non trouvée. À hauteur égale, une contre-attaque non jouable progresse autant qu'une jouable ; elle est un peu plus souvent reperdue en moins de 5 s entre 20 et 40 m (27,9 contre 21,0 %) : la défense la sanctionne encore peu (tickets 10 et 22).

**Le passeur ne reprend plus sa passe (ticket v2-collectif/26, 20 matchs, 31/10/2026).** Depuis le ticket 25 (`4d71418`), une passe sur deux (53 %) revenait au passeur au pas suivant et comptait comme réussie : toutes les mesures de passes, tirs, buts et hors-jeu depuis ce commit sont faussées. Avant (`c379ba6`) → après, mêmes graines : reprises par le passeur 53 → 0,8 % (2 matchs) ; receveur visé 19,5 → 60,8 % ; passes réussies 75,4 → 64,3 % ; passes chez l'adversaire 24,6 → 35,6 % (15 à 20 % au haut niveau) ; passes par minute 23,8 → 16,2 ; tirs 18,2 → 8,2 par équipe ; buts 4,3 → 1,75 par match ; hors-jeu 0,2 → 0,75 par match ; possession d'équipe 8,9 → 9,7 s. Nouvelle base pour la recalibration du hors-jeu et le ticket 22.

**Pressing coordonné (ticket v2-collectif/08, 20 matchs, 31/10/2026).** Avant (`8043889`) → après : pressings 1130 → 1122 par match, récupérés en 5 s 37 → 39 % ; solutions ouvertes 5,21 → 5,31 ; solutions faciles (≥ 0,8) 1,42 → 1,57 ; tacles 67,9 → 52,8 ; pertes 545 → 578 ; pertes en transition 24 → 29 % ; passes 18,5 → 17,6 par minute ; buts 2,1 → 2,0. Profils (99 contre 11) : Aggression, distance presseur-porteur 1,24 contre 1,49 m ; Anticipation, solutions faciles laissées 1,51 contre 1,59 ; Teamwork 1,69 contre 1,53 (sens inverse) ; Work Rate 1,62 contre 1,61. Réserve : le pressing n'a pas d'effet mesuré sur les passes, reprise au ticket 27. Ces chiffres datent d'avant le ticket 26 et sont faussés.

**Pressing coordonné remis sur main (ticket v2-collectif/08, 20 matchs, 01/11/2026).** Avant (`e8114a0`) → après, mêmes graines, avec les corrections de l'expert (passe en retrait d'au moins 3 m, effort et ligne lue valables pour la détention en cours) : buts 2,1 → 2,65 ; tirs 9,0 → 10,3 par équipe ; tacles 55,8 → 48,6 ; pertes 555 → 613 ; passes réussies 64,5 → 60,8 % ; hors-jeu 0,85 → 0,5 ; pressings 1 060 → 1 079 par match, récupérés en 5 s 35,9 → 39,5 % (23 % au réel, CMU 2025, autre définition) ; pressings d'équipe déclenchés 685 par match ; solutions ouvertes (≥ 0,7) 2,06 → 2,16 ; solutions faciles (≥ 0,8) 1,59 → 1,68. Buts, tirs et hors-jeu varient d'une version à l'autre à graine égale (écart-type des buts d'environ 0,4 sur 20 matchs). Profils (99 contre 11, 4 matchs) : Aggression, distance presseur-porteur 1,31 contre 1,56 m ; Work Rate, temps de pressing 1 184 contre 1 150 s (+3 %) ; Anticipation, solutions faciles laissées 1,43 contre 1,43 (nul en match) ; Teamwork, 1,63 contre 1,59 (sens inverse). Suite aux tickets 27 et 12.

**Compensations et passe en vol (ticket v2-collectif/09, 20 matchs, 02/11/2026).** Avant (`81f3b3d`, sans le ticket 13 en cours) → après : passes 15,94 → 16,01 par minute ; tirs 12,3 → 12,8 par équipe ; buts 2,65 → 2,70 par match ; tacles 47,3 → 50,0 ; pertes en transition 28,8 → 27,1 % des récupérations ; tirs de contre après récupération dans son camp 3,35 → 4,55 par match (récupérations dans son camp inchangées, environ 400 par match : réserve C3, renvoyée au ticket 10), dans le camp adverse 15,5 → 15,7. Diagnostic hors dépôt, 4 matchs : rôle défensif attribué pendant 57,5 → 98,8 % de la possession adverse, passes en vol comprises ; distance médiane marqueur-attaquant à Marking 99 8,20 → 7,36 m (marquages du pressing d'équipe compris) ; milieu défensif en compensation 8,5 % du temps de possession adverse.

**Fautes, avantage et coups francs (ticket v2-collectif/30, 20 matchs, 04/11/2026).** Avant (`efa65c2`) → après, mêmes graines : fautes 3,5 (4 matchs) → 9,4 par match (réel 21-26, réserve renvoyée au ticket 22a) ; avantages acquis 16 % ; coups francs 7,75 et penaltys 0,15 par match ; coups francs du dernier tiers frappés au but 37,5 % (petit échantillon, réserve au ticket 02b) ; temps de jeu effectif 72,6 → 68,7 % ; tacles 33,7 → 30,8 ; buts 2,95 → 2,70 ; tirs 30,6 → 28,3 par équipe ; passes 10,8 → 10,3 par minute. Profil Aggression 99 contre 11 : 15,25 contre 0 faute par match.

**Compensations et passe en vol après corrections (ticket v2-collectif/09, passage 2, 20 matchs, 02/11/2026).** Avant (`7a94d64`) → après, mêmes graines, machine seule : passes 15,87 → 15,94 par minute ; tirs 12,5 → 12,3 par équipe ; buts 2,5 → 2,65 ; tacles 44,75 → 51,15 ; pertes en transition 25,9 % des récupérations ; tirs de contre après récupération dans son camp 3,45 → 4,05 par match (réserve C3, renvoyée au ticket 10), dans le camp adverse 15,5. Diagnostic hors dépôt, 4 matchs : rôle attribué 56,6 → 98,8 % ; distance médiane marqueur-attaquant à Marking 99 8,05 → 7,46 m ; milieu défensif en compensation 8,3 à 8,7 %. Le paragraphe précédent date d'avant les corrections A1 à A3 de l'expert.

## 6. Repères de calibration (ticket v2-realisme/01c, 06/11/2026)

Les 7 repères de l'audit de réalisme (`.scratch/v2-realisme/spec.md`, section 8), confrontés à une source primaire et à la définition du banc (`scripts/v2_indicators.py`, `scripts/measure_v2.py`). Statut : **bloquant** (critère d'acceptation des calibrations, la définition du banc et celle de la source coïncident), **indicatif** (ordre de grandeur, écart de définition connu et borné), **à redéfinir** (le banc ne mesure pas ce que mesure la source : à corriger au ticket 01d avant usage). Rappel du banc : pas de remplacement en V2, chaque joueur joue tout le match, temps additionnel compris ; « par minute » divise par 90 minutes.

| # | Repère | Source primaire | Population | Définition de la source | Unité | Indicateur du banc | Écart de définition | Statut |
|---|---|---|---|---|---|---|---|---|
| R1 | Tirs par équipe : 8 à 15 | Opta Analyst, « Finding Their Range » (31/03/2025) : 8,3 tirs par match hors de la surface, soit 31,7 % des tirs | Premier League 2024-25, au 31/03/2025 | Tir Opta : toute tentative au but, contrés et penaltys compris | tirs par équipe et par match | `tirs tracés par équipe` (`ShotEvent`, contrés et penaltys compris, ticket 28b) | Aucun sur le périmètre. Valeur réelle **calculée** (8,3 / 0,317 / 2 ≈ 13,1 par équipe), non publiée telle quelle. `tirs par équipe` (`on_shot`, décision de tirer) n'est pas le bon indicateur : il ne compte pas les penaltys. | **Bloquant**, sur `tirs tracés par équipe` |
| R2 | Conversion : 10 à 11 % | Même article : 14,7 % des tirs de la surface et 4,2 % des tirs extérieurs vont au but | Premier League 2024-25 | Buts / tirs, penaltys compris (« sauf mention contraire ») | % | `conversion des tirs (part)` : tirs tracés terminés en but / tirs tracés | Aucun sur le périmètre (penaltys compris, buts contre son camp exclus des deux côtés). Valeur réelle **calculée** : 14,7 % × 0,683 + 4,2 % × 0,317 ≈ 11,4 %, au-dessus de la fourchette proposée. | **Bloquant**, fourchette élargie à **10 à 12 %** |
| R3 | Buts dans la surface : 80 à 90 % | Même article : 11,5 % des buts marqués de l'extérieur de la surface en 2023-24 (plus bas historique), 11,7 % en 2024-25 au 31/03/2025 | Premier League 2023-24 et 2024-25 | Origine du tir dans la surface ou sur ses lignes, penaltys compris | % des buts | `buts dans la surface (part)` : buts sur tir dont l'origine est dans la surface / buts sur tir | Aucun (même origine, penaltys compris). Valeur réelle 88 à 89 %. | **Bloquant** |
| R4 | Distance par joueur de champ : 9 à 14 km | Modric, Versic, Morgans et Sekulic, *Biology of Sport* 2023, 40(4) : 949-958 | Ligue des champions 2020-21, phase de groupes, 20 matchs, 244 matchs complets de joueurs de champ (InStat, 25 Hz) | Distance totale des joueurs ayant joué tout le match | km par joueur et par match | `km par joueur de champ, par poste` | Le banc compte le temps additionnel ; la source aussi (match complet). Valeurs réelles par poste : 10,2 km (défenseurs centraux) à 12,0 km (milieux centraux). 9 à 14 km est une enveloppe large, pas une cible. | **Indicatif** (cible de calibration : 10 à 12 km, ordre des postes de la source) |
| R5 | Appels par joueur : 5 à 20 (15,1 en moyenne) | CIES Football Observatory, rapport mensuel n° 88 (octobre 2023), données SkillCorner. **Correction** : la section 2 citait PLOS One 2022, une revue systématique qui ne contient pas ces chiffres. | 3 261 matchs de 27 ligues (Europe et Amériques), saison 2023 ou 2023-24 | Course de plus de 0,7 s au-dessus de 15 km/h d'un joueur qui devient une option de passe, avec une forte probabilité d'être choisi par le porteur (position et orientation du corps) ; phases offensives seulement | appels par joueur et par 90 min | `appels par joueur` : course de plus de 0,7 s au-dessus de 15 km/h d'un coéquipier du porteur, comptée si le coureur est le receveur visé ou si, à la fin de la course, sa probabilité de réception atteint 0,7 | Vitesse, durée et phase identiques. Diffère sur l'option : le banc juge la réception (sans interception), la source juge la chance d'être choisi. Le banc peut donc compter des courses que la source exclut, et inversement. Moyennes par poste : 5,5 (défenseurs centraux) à 19,2 (milieux offensifs). | **Indicatif** (ordre de grandeur et ordre des postes) |
| R6 | Haute intensité : 2 à 5 % au-dessus de 19,8 km/h | Modric et al. 2023 (voir R4) | Voir R4 | Distance au-dessus de 5,5 m/s (19,8 km/h) | m, et part de la distance totale | `temps au-dessus de 19,8 km/h (part)` | La source donne une **distance** (586 à 1 113 m par poste, soit 5,8 à 10,3 % de la distance totale, part calculée), le banc une **part du temps**. 2 à 5 % ne correspond à aucune des deux mesures de la source. | **À redéfinir** (01d : part de la distance au-dessus de 19,8 km/h, cible 6 à 10 %). Par poste, distance totale et distance au-dessus de 19,8 km/h (Big 5 ; hors Big 5) : défenseurs centraux 10,24 km et 716 m (7,0 %) ; 10,17 km et 586 m (5,8 %) ; milieux centraux 11,97 km et 1 001 m (8,4 %) ; 11,82 km et 857 m (7,3 %) ; latéraux 11,07 km et 1 072 m (9,7 %) ; 10,84 km et 954 m (8,8 %) ; attaquants 10,32 km et 811 m (7,9 %) ; 10,85 km et 1 038 m (9,6 %) ; milieux excentrés 10,84 km et 1 113 m (10,3 %) ; 11,25 km et 1 070 m (9,5 %) |
| R7 | Passes par minute : 15 à 17 | Opta Analyst (16/01/2026) : 941,0 passes par match (deux équipes) en 2023-24, 893,4 en 2024-25 | Premier League 2023-24 et 2024-25 | Passes tentées des deux équipes, par match | passes par match | `passes par minute` : passes tentées des deux équipes / 90 min | 941 passes sur 90 min font **10,5 par minute de match** ; 15 à 17 ne s'obtient qu'en divisant par le temps de jeu effectif (941 / 56 min ≈ 16,8). La fourchette mêle donc un dénominateur de temps effectif et une mesure par minute de match. Le banc mesure aujourd'hui 10,96 passes par minute de match, soit environ 990 passes par match, proche de la source : la fourchette 15-17 appliquée à cette mesure pousserait à tort vers 50 % de passes en trop. | **À redéfinir** (01d : passes par match, cible 890 à 940, et passes par minute de jeu effectif, cible 15 à 17) |

**Mesure actuelle du banc (`a9a74f9`, 20 matchs, graine d'audit 20260923), pour situer chaque repère, pas pour le régler** : R1 37,7 tirs tracés par équipe ; R2 5,4 % ; R3 48 % ; R4 17,4 km par joueur (16,9 à 17,7 selon le poste, sans ordre des postes) ; R5 22 (défenseurs centraux) à 102 (avant-centres) appels par joueur ; R6 17,2 % du temps au-dessus de 19,8 km/h ; R7 10,96 passes par minute de match (temps de jeu effectif 62,8 % de 90 min, soit 17,5 par minute de jeu effectif ; recalculé au 01d sur la durée réelle du match, temps additionnel compris : 66,5 % et 14,9, voir section 7). Six repères sur sept hors de la valeur réelle (R7 seul en est proche), R1 à R6 très au-delà : les calibrations provisoires (18d, 18e) partent de loin.

**Écarts de définition à traiter au 01d** : R6 (temps → distance au-dessus de 19,8 km/h), R7 (dénominateur : passes par match et par minute de jeu effectif), R1 (lire `tirs tracés par équipe`, pas `tirs par équipe`). R5 reste indicatif tant que le banc juge l'option de passe par la réception plutôt que par la chance d'être choisi.

**Limites.** R1 et R2 sont calculés à partir de parts publiées, pas lus directement. Une seule ligue pour R1, R2, R3 et R7 (Premier League) ; pour la Ligue 1, aucune donnée publique équivalente trouvée. Bradley et al. 2009 (*Journal of Sports Sciences* 27(2) : 159-168, Premier League 2005-06), cité en section 1 pour l'ordre des postes : seuils vérifiés (course rapide 19,8-25,1 km/h, sprint au-delà de 25,1 km/h), texte intégral payant, distances totales non relues.

**Sources.**
- [CIES, rapport mensuel n° 88](https://football-observatory.com/IMG/sites/mr/mr88/en/)
- [Opta Analyst, tirs de Premier League 2024-25](https://theanalyst.com/eu/2025/03/premier-league-2024-25-shot-data)
- [Opta Analyst, passes par match](https://theanalyst.com/articles/premier-league-teams-still-more-direct-2025-26)
- [Modric et al. 2023, PMC10588580](https://pmc.ncbi.nlm.nih.gov/articles/PMC10588580/)
- [Bradley et al. 2009, PubMed 19153866](https://pubmed.ncbi.nlm.nih.gov/19153866/)

## 7. Référence physique du banc (ticket v2-realisme/01d, moteur à `adf431a`, 06/11/2026)

`uv run python -m scripts.measure_v2 50` (graine d'audit 20260923, 50 matchs, un seul processus). Indicateurs définis en section 1 et 3 ; repères réels en section 6. Mesure reproductible : deux exécutions de 2 matchs donnent la même sortie (empreinte 3abfd02d).

| Indicateur | Banc (50 matchs) | Repère réel (section 6) |
|---|---|---|
| Km par joueur de champ | 17,45 | 10,2 à 12,0 par poste (R4) |
| Distance au-dessus de 19,8 km/h (part) | 39,3 % | 6 à 10 % (R6) |
| Temps au-dessus de 19,8 km/h (part) | 17,3 % | suivi |
| Distance au-dessus de 25 km/h (part) | 14,8 % | 2-3 % (section 1) |
| Temps au-dessus de 25 km/h (part) | 5,7 % | suivi |
| Sprints par joueur et par match | 146,5 | suivi |
| Appels par joueur et par 90 min | 49,4 | 15,1 (R5) |
| Passes par match | 990 | 890 à 940 (R7) |
| Passes par minute de match / de jeu effectif | 11,00 / 14,92 | 10,5 / 15 à 17 (R7) |
| Temps de jeu effectif (part de la durée réelle du match) | 66,5 % | 53 à 56 % avec fautes, remplacements et blessures (section 1) |
| Tirs tracés par équipe | 38,05 | environ 13 (R1) |
| Conversion des tirs | 5,4 % | 10 à 12 % (R2) |
| Buts dans la surface | 57,0 % | 88 à 89 % (R3) |

**Par poste** (moyenne par joueur et par match) :

| Poste | Km | Distance au-dessus de 19,8 km/h (m) | Part de la distance | Sprints | Appels par 90 min |
|---|---|---|---|---|---|
| défenseur central (DC) | 17,33 | 6 924 | 40,0 % | 169,0 | 20,2 |
| latéral gauche (LB) | 17,72 | 7 396 | 41,7 % | 184,4 | 31,0 |
| latéral droit (RB) | 17,68 | 7 471 | 42,3 % | 194,8 | 25,3 |
| milieu défensif (MDC) | 16,96 | 6 092 | 35,9 % | 104,6 | 45,3 |
| milieu central (MC) | 17,38 | 6 616 | 38,1 % | 120,1 | 46,2 |
| milieu offensif (MOC) | 17,56 | 6 635 | 37,8 % | 112,8 | 81,8 |
| ailier gauche (AG) | 17,45 | 6 675 | 38,3 % | 121,9 | 76,7 |
| ailier droit (AD) | 17,45 | 6 723 | 38,5 % | 125,6 | 77,0 |
| avant-centre (BU) | 17,68 | 7 051 | 39,9 % | 150,5 | 91,8 |

**Lecture.** Les joueurs courent 45 à 70 % de trop (17,5 km contre 10,2 à 12,0), presque 40 % de leur distance au-dessus de 19,8 km/h (contre 6 à 10 %), et l'ordre des postes n'existe pas : 16,96 à 17,72 km pour tous, alors que la source sépare nettement les milieux centraux (11,97 km) des défenseurs centraux (10,24 km). Plus de 100 sprints par joueur, plus de 3 fois trop d'appels. Seul le volume de passes est proche du réel (990 par match, 14,9 par minute de jeu effectif, juste sous la fourchette). Les deux indicateurs de jeu effectif se calculent sur la durée réelle du match, temps additionnel compris (99,8 min en moyenne) : sur 90 min, ils valaient 62,8 % et 17,5. C'est le symptôme C5 de l'audit : la cible des calibrations provisoires (18d, 18e), pas un réglage à faire ici.

## 8. Séries longues et intervalles de confiance (ticket v2-realisme/01e, 06/11/2026)

`uv run python -m scripts.bench_series 500 --processus 7 --json serie.json` (options de `measure_v2` : `--profil`, `--pas`, `--sans-plan`, `--debut`). Un match par tâche, graine du match comme dans `measure_v2` (graine d'audit + indice), répartis sur plusieurs processus et agrégés dans l'ordre des matchs : le résultat ne dépend pas du nombre de processus (test `test_results_do_not_depend_on_the_number_of_processes`). Pour chaque indicateur, km par poste compris : valeur agrégée (celle de `measure_v2`), puis moyenne par match, écart-type et intervalle de confiance à 95 % de cette moyenne (approximation normale, valable pour les séries longues). Valeurs par match prises sur tous les matchs : une part tirée d'un compteur (choix, origine des tirs, situations, récupérations) vaut 0 dans un match où le compteur est nul ; un poste absent d'une formation est écarté. **Pour une part, la valeur agrégée (sommes) et la moyenne par match peuvent différer** : la sortie signale une valeur agrégée hors de l'intervalle ; une décision de calibration sur une part rare lit les deux. Le JSON garde les paramètres de la série et les valeurs par match.

**Comparaison appariée** : `uv run python -m scripts.bench_series --comparer avant.json apres.json` (mêmes matchs exigés : deux versions, ou deux profils ; avertissement si les paramètres diffèrent) donne l'écart moyen par match et son intervalle de confiance, et signale les écarts significatifs (intervalle qui exclut 0).

**Mémoire** : le collecteur fusionné garde toutes les valeurs brutes, comme `measure_v2` (environ 2 à 3 Go pour 500 matchs, 8 à 12 Go pour 2 000, estimation de l'expert au 01e) : mesurer le pic sur 100 matchs avant la première série de 2 000 (18b ou 18d).

**Durée machine** : estimée et affichée avant le lancement. Base : 75 s par match de 90 min sur un processus (01d) ; accélération mesurée en parallèle : 2,6 avec 7 processus sur 8 fils logiques (100 matchs en 48,5 min), soit 0,65 par cœur physique. Ordres de grandeur sur cette machine : 500 matchs en 4 h environ, 2 000 matchs en 16 h environ.

**Essai de 100 matchs (7 processus, moteur à `6b8d1b8`)** : passes par minute de match 10,97 [10,87 ; 11,07] ; passes par match 987 [978 ; 997] ; buts par match 4,13 [3,72 ; 4,54] ; tirs tracés par équipe 37,6 [36,8 ; 38,4] ; conversion 5,5 % [4,9 ; 6,0] ; temps de jeu effectif 66,3 % [65,8 ; 66,7] ; appels par joueur et par 90 min 49,7 [48,4 ; 51,0]. Écart-type par match des buts : 2,1 (une comparaison de 20 matchs ne détecte qu'un écart d'au moins 1,3 but par match).

## 9. Structure : côtés, rôles, appels (ticket v2-realisme/02h, 50 matchs, 07/11/2026)

`uv run python -m scripts.bench_series 50 --processus 7 --json .scratch/v2-realisme/mesures/02h-serie.json` (graine d'audit 20260923, moteur à `e458ee1`, aucun code moteur modifié : buts 3,88, passes 1 044, appels 45,4 par 90 min, identiques à la mesure du 02g). Indicateurs 17 à 23 de la section 2, seuils de la section 3. **Mesure seulement, aucune calibration.** Référence : section 7 (01d) pour les km et les appels du banc.

**Côté des postes latéraux (indicateur 23).** Part du temps du bon côté de l'axe, hors transition : AG 99,1 %, LB 99,4 %, RB 99,4 %, AD 98,9 % (toutes situations : 98,8 à 99,4 %). Le critère du ticket (plus de 90 % hors transition) est tenu avec une large marge, mais il est tolérant (un latéral à 1 m de l'axe du bon côté compte) : il se cite toujours avec la place moyenne (indicateur 22), qui donne la largeur (17 à 20 m de l'axe), et ne prouve pas à lui seul le couloir (réserve A2 de l'expert au 02h). Place moyenne, côté (m depuis l'axe, négatif = gauche) avec ballon / sans ballon : LB −19,1 / −17,5, AG −20,3 / −19,2, RB +18,8 / +17,4, AD +20,6 / +18,8 ; les postes axiaux restent à moins de 2 m de l'axe (MDC −1,8 / −1,7, MC +0,9 / +0,8, DC −0,1, MOC et BU à 0,1 près).

**Profondeur moyenne (m depuis son but), avec ballon / sans ballon.** DC 26,6 / 29,5 ; LB 35,2 / 34,8 ; RB 34,5 / 34,7 ; MDC 35,6 / 38,0 ; MC 40,7 / 41,7 ; MOC 54,1 / 51,5 ; AG 57,2 / 52,1 ; AD 57,5 / 51,8 ; BU 65,1 / 61,0. Sans ballon, les défenseurs centraux sont **plus hauts** (29,5 m) qu'avec le ballon (26,6 m) : écart à regarder au 09 (occupation), le bloc sans ballon montant avec la ligne défensive.

**Appels du banc et appels décidés (indicateurs 10, 17, 18), par joueur et par 90 min.**

| Poste | Appels du banc (course) | Épisodes APPEL (décision) | Km par match |
|---|---|---|---|
| DC | 19,8 | 2,3 | 14,24 |
| LB / RB | 27,5 / 25,0 | 17,5 / 10,0 | 12,95 / 12,96 |
| MDC | 41,2 | 17,4 | 14,97 |
| MC | 47,0 | 54,6 | 14,48 |
| MOC | 80,7 | 166,6 | 15,48 |
| AG / AD | 54,2 / 53,5 | 177,4 / 186,1 | 14,83 / 15,04 |
| BU | 99,1 | 211,3 | 17,02 |
| Tous | 45,4 | 78,6 | 14,59 |

Le rôle des joueurs au **départ** des courses que le banc compte comme appels (part des appels) : `tenir sa place` 32,6 %, `appel` 30,2 %, `receveur visé` 17,4 %, `ballon libre` 9,7 %, `replacement` 5,2 %, `repli` 1,1 %, `presseur` 1,1 %, `couverture` 1,1 %, `marquage` 1,1 %. **L'hypothèse du 02g est confirmée** : un tiers des « appels » du banc sont des joueurs qui tiennent leur place et la rejoignent vite, et seulement 30 % partent d'un vrai rôle `APPEL`. Les volumes du banc ne mesurent donc pas la sélection ; les épisodes APPEL le font. Les défenseurs centraux (2,3 épisodes par 90 min) n'appellent presque jamais, comme voulu. Les ailiers, milieux offensifs et avant-centres commencent en revanche 166 à 211 épisodes par 90 min (un toutes les 25 à 30 s) : voir plus bas. Asymétrie à suivre (facultatif A4 de l'expert) : LB 17,5 contre RB 10,0 épisodes alors que la place moyenne est symétrique.

**Appelants simultanés (indicateur 19).** Moyenne en possession : 1,20 en possession installée, 2,23 en transition offensive, 0,26 au dernier tiers (peu d'instants). Maximum de la série : 3 dans toutes les situations. Le plafond du moteur (2, 3, 3) est dépassé sur **2,6 % des instants de possession installée** (jamais ailleurs ; les lignes « défense placée » et « transition défensive » valent 0 par construction, `CALLER_CAP` n'ayant pas de plafond pour elles). Le maximum de 3 en possession installée vaut le plafond de la transition offensive. Hypothèse non vérifiée : la situation réelle du banc diffère de la situation perçue du joueur (en retard de son délai de réaction) ; en possession installée réelle, un joueur qui croit encore à une transition applique le plafond de 3. Ce chiffre ne se lit donc pas comme un défaut du moteur ; à recompter avec la situation perçue, ou avec le plafond effectivement appliqué, avant tout correctif de la sélection (réserve A1 de l'expert au 02h).

**Alternance APPEL / TENIR à l'intérieur d'une possession (indicateur 20).** 85,9 passages par joueur et par match (1 719 par match), dont 53 % après un état de moins de 1,5 s. Cette part mélange le délai voulu d'Off the Ball (TENIR → APPEL, 0,3 à 1,0 s) et le clignotement. Le clignotement seul, **APPEL qui s'arrête en moins de 1,5 s : 40 % des appels qui se terminent par TENIR** (diagnostic du 02g : 24 %, autre définition, 10 minutes d'un seul match). L'hystérésis du 02g réduit les alternances mais ne les supprime pas. À reprendre dans un ticket dédié si le jeu à l'écran montre des joueurs qui partent puis s'arrêtent.

**Appelant retenu et passe ouverte (indicateur 21, réserve A3 du 02g).** 30,1 % seulement des joueurs au rôle `APPEL` sont, à la seconde de la mesure, une solution de passe du porteur (chance de réception d'au moins 0,7). Le filtre « espace exploitable par une passe du porteur » non réalisé au 02g est donc visible : près de sept appelants sur dix ont une chance de réception sous 0,7 (cette chance dépend de la couverture, mais aussi de la distance et du Passing du porteur : la cause n'est pas isolée, et il n'y a pas de référence, par exemple la même part pour les joueurs en `TENIR`). Un ticket dédié peut se justifier ; ce ticket ne règle rien.

**Écarts au réel, sans réglage.** Km : 14,6 par joueur contre 10,2 à 12,0 selon le poste (R4), ordre des postes encore faible (LB / RB 12,95 à BU 17,02, la source place les milieux centraux au plus haut). Appels du banc : 45,4 contre 15,1 en moyenne (R5). Épisodes APPEL : pas de repère. Évolution depuis le 01d (50 matchs) : km 17,45 → 14,59, appels du banc 49,4 → 45,4.

## 10. Gardien : bissectrice et hauteur (tickets v2-realisme/03b et 03c, 20 matchs, 07/11/2026)

- **Au tir (03b)** : écart du gardien adverse à la bissectrice de l'angle ballon-poteaux (m), part des tirs sous `BISECTOR_TOLERANCE_M` (2 m), écart à son point visé, chance du tir (`shot_probability`). 03b : 0,25 m, 98,1 %, 1,76 m, 0,061.
- **Ballon loin (03c)** : ballon à `BALL_DISTANCE_M[1]` (40 m) ou plus de son but, distance du gardien à sa ligne de but et écart à la ligne défensive réelle (hauteur moyenne de la dernière ligne de champ), par tranche de ligne (sous 25 m, 25 à 35 m, 35 m et plus), échantillonné comme le reste de la géométrie. Avant / après le 03c : distance à sa ligne 7,1 à 7,7 → 11,5 à 13,4 m ; écart à la ligne 11,1 / 22,4 / 40,1 → 7,0 / 16,8 / 35,2 m. Pas de repère réel trouvé.
- **Sorties (03d, 50 matchs)** : épisodes de sortie par match, part réussie (de la sortie à la relance), part hors de la surface, point visé à son but, ballons libres à sa portée laissés (le gardien reste en placement). Avant / après le 03d : sorties 215 → 34,9 par match, part réussie 3,4 → 4,6 %, hors de la surface 43,2 → 0,17 %, distance maximale du gardien à son but 49,3 → 29,2 m. La part réussie compte aussi les remises en jeu et les rebonds ; pas de repère réel trouvé.
- **Face-à-face (03e, 50 matchs)** : au tir d'un adversaire seul face au gardien (à 25 m ou moins, sans défenseur sur la ligne de tir), vitesse du gardien, part arrêtée (sous `FACE_STOPPED_MPS`, 1,5 m/s), distance à sa ligne, distance du tireur au but, chance du tir ; épisodes de face-à-face du gardien par match. Avant / après le 03e : tirs de face-à-face 12,5 → 13,2 par match, gardien arrêté 65,2 → 92,1 %, vitesse 1,51 → 0,82 m/s, distance à sa ligne 3,57 → 4,54 m, chance 0,108 → 0,104 (sans écart significatif), 32,2 épisodes par match (l'état clignote avec les défenseurs qui entrent et sortent du cône de tir). Pas de repère réel trouvé (consigne d'entraîneur : 1 à 6 m de la ligne).


## 11. Gardien : validation du placement et des sorties (ticket v2-realisme/03g, 50 matchs, 07/11/2026)

`uv run python -m scripts.bench_series 50 --processus 7 --json .scratch/v2-realisme/mesures/03g-avant.json` puis `03g-apres.json` (graine d'audit 20260923, rapports `03g-avant.txt` et `03g-apres.txt`). **Avant** : moteur du 03e (`bdc4478`) avec les indicateurs du 03g ; **après** : même moteur avec le correctif 03e A1. **Mesure seulement, aucune calibration.** Les deux séries donnent les mêmes valeurs à tous les chiffres (voir « Correctif 03e A1 » ci-dessous) ; seuls deux indicateurs ajoutés entre les deux séries (sorties très disputées, avance sur l'adversaire) n'existent que dans « après ».

**Indicateurs ajoutés au banc (seuils de mesure proposés, acceptés d'office).**
- **Distance à sa ligne par zone du ballon** : zone = distance du ballon au but du gardien, bornes 12 m, 25 m et 40 m (`BALL_DISTANCE_M` et `FACE_RANGE_M`), échantillonnée comme le reste de la géométrie. Le « ballon loin » du 03c reste (même mesure au-delà de 40 m, par tranche de ligne défensive).
- **Sortie disputée** : au début d'une sortie, l'adversaire de champ le plus rapide arrive au point visé au plus **2,0 s** après le gardien (`DISPUTED_WINDOW_S`) ; **très disputée** : au plus 1,0 s (`TIGHT_WINDOW_S`) ; avance du gardien sur lui en secondes, plafonnée à 10 s ; **gagnée** : la sortie se termine par la relance (le gardien a le ballon).
- **Course gagnante masquée** (réserve A1 du 03d) : ballon libre qui ne vient pas de son équipe, que le gardien gagnerait (`gardien.race`) mais qu'il laisse en placement parce qu'il est à 15 m ou plus du ballon sans être le plus proche de son équipe (filtre de portée). `coéquipier` : le coéquipier le plus proche arrive avant l'adversaire le plus rapide (le filtre a raison) ; `battu` : il arrive après (course perdue pour l'équipe). Épisodes, comptés à chaque changement de catégorie (aucune, coéquipier, battu) : un ballon dont la course alterne est compté plusieurs fois, le chiffre est donc un **majorant** et non un nombre de ballons (réserve A1 de l'expert).
- **Écart à la profondeur visée au tir en face-à-face** (réserve A2 du 03e) : valeur absolue entre sa distance à sa ligne et `face_depth` pour la distance du tireur.

**Distance du gardien à sa ligne selon la zone du ballon (m, moyenne des échantillons).**

| Ballon à | Moins de 12 m | 12 à 25 m | 25 à 40 m | 40 m et plus |
|---|---|---|---|---|
| Distance à sa ligne | 5,16 | 4,70 | 7,29 | 11,96 |
| IC 95 % | 5,13 à 5,19 | 4,59 à 4,79 | 7,23 à 7,39 | 11,88 à 12,03 |

La courbe monte bien avec l'éloignement du ballon (4,7 → 7,3 → 12,0 m) mais la première colonne la casse : à moins de 12 m, la distance (5,2 m) est plus grande qu'à 12-25 m. Cette zone mélange le gardien qui a le ballon (relance, remise en jeu, ballon dans ses mains : il est alors avancé), les corners et les sorties ; elle ne mesure pas seulement le placement sur la bissectrice. À lire avec l'écart à la bissectrice au tir, qui vaut **0,30 m** (98,2 % des tirs sous 2 m) et l'écart au point visé au tir, **2,06 m** (le gardien est en mouvement au tir, voir 03f). Pas de repère réel trouvé.

**Limite du 03c (réserve A2) toujours valable.** Ballon à 40 m ou plus et ligne défensive à 35 m ou plus, le gardien reste à **35,3 m** derrière sa ligne (distance à sa ligne 12,1 m, plafond de 16 m) : le 03c ne couvre pas la profondeur derrière une ligne très haute. La sortie hors de sa surface est rare (0,34 % des sorties, distance maximale à son but 29,9 m pour un plafond de 35 m) : le mécanisme de profondeur du 03d joue surtout dans la surface.

**Sorties (50 matchs).** 35,0 par match, dont **33,3 disputées** (2,0 s ou moins ; 95 %) et **9,1 très disputées** (1,0 s ou moins) ; avance moyenne du gardien sur l'adversaire **1,34 s** [1,31 ; 1,37]. La fenêtre de 2,0 s est donc peu sélective ; la part gagnée (relance) est faible, **4,9 %** des sorties disputées contre 5,0 % de toutes les sorties, comme au 03d : elle compte la relance et non la prise du ballon, et une sortie qui se termine par une interception sur remise en jeu ou un rebond n'y entre pas. Les 35 sorties sont des **épisodes** (l'état bascule entre sortie et placement quand l'avance passe par la marge de 0,5 s, comme le face-à-face du 03e : 32 épisodes par match), pas un nombre de ballons : ne pas les lire comme des sorties réelles (réserve A2 de l'expert). Ces deux chiffres ne prouvent donc ni que le gardien gagne ses sorties ni qu'il les perd ; la preuve en match du cas « passe en profondeur coupée » (réserve A1 du 03d) reste à faire avec un indicateur d'issue du ballon (prise, dégagement, but) et non de relance, au ticket `03i`.

**Filtre de portée (réserve A1 du 03d).** Courses gagnantes masquées : **18,7 par match** où un coéquipier plus proche arrive avant l'adversaire (le filtre a raison), et **2,9 par match** [2,1 ; 3,7] où ce coéquipier arrive après lui, soit 13,5 % des courses gagnantes masquées : au plus environ trois épisodes par match où le gardien aurait gagné une course que son coéquipier ne gagne pas (majorant : les épisodes clignotent, et on ne sait pas si l'adversaire va réellement au ballon). Ce chiffre ne se cite pas comme un taux de courses perdues. Mesure seule ; une règle « le gardien y va si son coéquipier le plus proche perd la course » reste à décider (ticket dédié si le propriétaire le veut).

**Face-à-face.** 13,2 tirs par match, gardien arrêté (sous 1,5 m/s) **92,1 %** [89,7 ; 93,9], vitesse au tir 0,82 m/s, distance à sa ligne 4,54 m pour un tireur à 16,7 m (profondeur visée 4,2 m), **écart à la profondeur visée 1,32 m** [1,09 ; 1,49], chance du tir 0,104. Le gardien est dans l'ordre de grandeur de sa cible mais pas dessus : 1,3 m d'écart, soit près d'un tiers de la profondeur. Lecture facultative de l'expert du 03e (A2).

**Correctif 03e A1 (profondeur de face-à-face derrière une ligne haute).** Appliqué : `bisector_point` ne place plus le gardien en face-à-face derrière le placement que demande la ligne défensive. **Effet nul en match** : les deux séries donnent les mêmes valeurs à tous les chiffres. Sur un match instrumenté (300 instants de face-à-face), la ligne vaut 5 à 26 m, alors que l'écart n'apparaît que pour une ligne plus haute que 28 m (porteur à 25 m), 31,8 m (22 m) ou 38,8 m (18 m) ; le correctif ne change aucune cible. Il est démontré par la scène (ligne à 40 m, porteur à 22 m : 5,5 → 6,7 m) et reste une garantie pour une ligne plus haute. Déterminisme : deux exécutions de 2 matchs, même empreinte (`d183e42f14c5ba1b`).

**Écarts au réel, sans réglage.** Aucun repère réel pour la position du gardien (consigne d'entraîneur de 1 à 6 m de la ligne en face-à-face, tenue). Tirs par équipe 23,8 et buts 3,08 par match : voir le point d'étape 18a. La hausse de la chance des tirs due au 03c (0,061 → 0,081, aujourd'hui 0,064) reste à décomposer au ticket 03h.


## 12. Gardien : la ligne du 03c et la chance des tirs, saut de cible (ticket v2-realisme/03h, 50 matchs appariés, 07/11/2026)

`uv run python -m scripts.bench_series 50 --processus 7 --json .scratch/v2-realisme/mesures/03h-avec-ligne.json` (A, moteur du 03g) et `PYTHONPATH=. uv run python .scratch/v2-realisme/mesures/03h-serie-sans-ligne.py 50 --processus 7 --json .scratch/v2-realisme/mesures/03h-sans-ligne.json` (B, même moteur avec `gardien.LINE_RATIO = 0`, qui redonne le placement du 03b), puis `uv run python -m scripts.decomposition_tirs avec.json sans.json`. Graine d'audit 20260923, mêmes 50 matchs. **Mesure seulement, aucune constante modifiée.** La série A redonne exactement celle du 03g (chance 0,0637, buts 3,08).

**La hausse du 03c n'existe plus.** Le 03c avait mesuré, sur 20 matchs, une chance des tirs de 0,0611 → 0,0813 et 2,75 → 3,60 buts avec la ligne. Sur le moteur actuel (50 matchs) : chance **0,0637 avec la ligne contre 0,0684 sans**, écart A − B **−0,0037** [−0,0093 ; +0,0019] (non significatif), buts **3,08 contre 3,08** (écart 0 ± 0,58), tirs par équipe 23,8 contre 23,3 (+0,49 [−0,77 ; +1,75]). La ligne du 03c ne fait donc pas monter la chance des tirs aujourd'hui. Hypothèse non démontrée par cette mesure : la hausse venait en partie des 215 sorties par match du 03d (le gardien courait sur les passes de son équipe), supprimées depuis.

**Décomposition de l'écart (quatre termes qui se somment, IC 95 % sur les 50 écarts par match).** Chances moyennes par tir, agrégées sur tous les tirs (A / B ; les termes du tableau sont des moyennes des écarts par match, d'où de petits écarts avec la différence de ces moyennes) : à la place réelle du gardien 0,0637 / 0,0684 ; à son point visé 0,0577 / 0,0617 ; sur la bissectrice du 03b sans ligne 0,0598 / 0,0628.

| Terme | Valeur | IC 95 % |
|---|---|---|
| Dynamique avec la ligne : P(A, réelle) − P(A, visé) | +0,0059 | [+0,0042 ; +0,0077] |
| Cible (ligne et face-à-face) : P(A, visé) − P(A, 03b) | −0,0022 | [−0,0026 ; −0,0017] |
| Mélange de tirs : P(A, 03b) − P(B, 03b) | −0,0021 | [−0,0070 ; +0,0028] |
| Dynamique sans la ligne : P(B, 03b) − P(B, réelle) | −0,0054 | [−0,0069 ; −0,0040] |
| **Écart total** | **−0,0037** | [−0,0093 ; +0,0019] |

- **Dynamique** : le gardien n'est jamais exactement sur son point visé au moment du tir (**1,09 m** avec la ligne, 0,97 m sans) et cela *augmente* la chance de **+0,0055 à +0,0059** dans les deux séries ; la différence entre les deux dynamiques est nulle (+0,0005 [−0,0013 ; +0,0024]). C'est le plus gros terme et il ne dépend pas de la ligne. **Hypothèse, non démontrée** (réserve A2 de l'expert) : il relèverait du ticket 03f (appuis au moment du tir) ; mais les tireurs tirent peut-être de préférence quand le gardien est décalé (biais de sélection), et s'écarter d'un point visé optimisé augmente mécaniquement la chance. Le 03f est le ticket qui peut le tester.
- **Cible** : la ligne et la profondeur de face-à-face *baissent* la chance de 0,0022. Séparées : face-à-face seul (série B) −0,0011 [−0,0018 ; −0,0004], ligne seule (A moins B) **−0,0011** [−0,0020 ; −0,0001]. Le critère « P(B, 03b) = P(B, visé) » posé au ticket était faux : le point visé contient la profondeur de face-à-face du 03e, que la bissectrice du 03b ne contient pas.
- **Mélange de tirs** : non significatif. Chance de l'endroit (`base_chance`) 0,0774 avec la ligne contre 0,0817 sans (écart −0,0026 [−0,0086 ; +0,0035]), distance au but 21,65 contre 21,70 m (−0,11 m [−0,48 ; +0,25]).
- La somme des quatre termes est vérifiée par un test (`tests/test_v2_indicators.py`) à 1e-12 près.

**Effets sur la position du gardien (A − B).** Distance moyenne du gardien à son but **+3,87 m** [+3,80 ; +3,94] (significatif) ; écart à la bissectrice sans ligne au tir 0,30 contre 0,27 m (la bissectrice reste tenue, 98,2 % contre 97,6 % sous 2 m) ; écart à son point visé réel au tir 1,09 contre 0,97 m (+0,12 m [−0,01 ; +0,25]). Cet indicateur (« gardien au tir : écart à son point visé réel ») lit la cible réelle du gardien et corrige la réserve A4 du 03g : l'écart à la bissectrice sans ligne mesure l'avancée voulue par la ligne et non une erreur.

**Saut de cible (réserve A3 du 03c, réserve A1 du 03b).** Entre deux instants consécutifs où le gardien est en placement (accumulé par match) :

| | Avec la ligne | Sans la ligne | Écart A − B |
|---|---|---|---|
| Saut moyen entre deux instants (m) | 0,151 | 0,078 | +0,073 [+0,071 ; +0,075] |
| Part des sauts de plus de 1,0 m | 1,21 % | 0,30 % | +0,91 point |
| Part du temps en course à plus de 5,0 m/s (en placement) | 2,47 % | 0,85 % | +1,62 point |
| Saut maximal du match (m) | 20,22 | 20,22 | 0 |

La ligne multiplie par deux le saut moyen et par quatre les grands sauts, mais ces sauts restent rares (1,2 % des instants) et le gardien, limité par sa vitesse et son accélération, ne court plus de 5 m/s que 2,5 % du temps en placement. **Le saut maximal est le même dans les deux séries et à chaque match (20,22 m).** Relevé sur un match : le ballon passe du centre de la ligne de but au point de corner en un seul instant (remise en jeu), et le point visé passe du centre du but au bord de la surface (20,16 m de côté, plus 1,5 m de profondeur) ; c'est un changement de place du ballon, pas un défaut du placement. Conclusion : **pas de défaut mesuré** (moyenne, grands sauts, course) ; le saut n'est pas mesuré hors remises en jeu ni sur le mouvement rendu (inversions, accélérations), et pas en fonction de la distance du ballon (réserve A1 de l'expert) ; si le gardien paraît nerveux au rendu, la piste serait de lisser la cible sur environ 0,5 s (non faite, constante à proposer).

**Limites.** (1) Les chances sont des chances de but par tir non contré selon `shot_probability`, pas des buts : les buts observés (3,08 contre 3,08) sont trop bruités pour départager (±0,5 par match). (2) La dynamique est calculée sur le dernier point visé du gardien en placement ou en face-à-face ; au tir il l'est dans 100 % des cas mesurés. (3) La limite du 03c (A2) reste : sans effet sur cette décomposition. (4) La série A n'a pas la hausse du 03c : le plafond de 16 m, la ligne de référence du bloc et la couverture de la profondeur ne sont pas modifiés ici.

## 13. Gardien : issue du ballon après une sortie, par ballon (ticket v2-realisme/03i, 50 matchs, 07/11/2026)

`uv run python -m scripts.bench_series 50 --processus 7 --json .scratch/v2-realisme/mesures/03i.json` (graine d'audit 20260923, rapport `03i.txt`), moteur du 03h (`32209f1`) avec les indicateurs du 03i. **Mesure seulement, aucune calibration, aucun réglage du filtre de portée.**

**Indicateurs ajoutés au banc (seuils du ticket).** Un **ballon** est un épisode continu de ballon libre : de la perte du porteur à la prise du ballon par un joueur ou à l'arrêt du jeu (remise en jeu en attente). Pour chaque ballon où le gardien est en sortie au moins une fois, on suit sa **première** sortie : qui a le ballon **3 s** après (gardien, coéquipier, adversaire, ballon encore libre, ou jeu arrêté par type de remise), s'il y a eu un **tir adverse dans les 5 s après** la sortie, et (ajouté pendant la mesure) si le ballon **est lui-même un tir adverse** (tir de l'adversaire dans les 5 s **avant** la sortie). Les courses gagnantes masquées du 03g sont recomptées **par ballon**. Les ballons suivis moins de 5 s en fin de match sont comptés à part (« non résolus ») : le compteur est collecté mais **pas encore affiché dans le rapport** (réserve A2 de l'expert, à ajouter à un prochain ticket de bancs ; l'égalité ballons = épisodes indique qu'il est très faible). Les instants sont ceux du tick qui précède l'appel du gardien (retard d'un tick de 0,1 s).

**Les sorties sont déjà des ballons, pas des épisodes qui clignotent.** 35,0 ballons avec sortie par match [32,7 ; 37,3] pour 35,0 épisodes de sortie : le rapport est exactement 1. Même chose pour les courses gagnantes masquées (coéquipier plus rapide 18,68 [17,34 ; 20,02] contre 18,7 par épisode ; coéquipier battu 2,92 [2,14 ; 3,70] contre 2,92). Le clignotement supposé aux réserves A1 et A2 du 03g n'existe pas pour les sorties ; il existe pour le face-à-face (32 épisodes par match, 03e). Les chiffres du 03g restent donc exacts, y compris le majorant de 2,9 courses perdues par match, qui est en fait le nombre de ballons.

**Issue à 3 s, tous les ballons avec sortie (moyenne des parts par match, IC 95 %).**

| Ballon 3 s après la première sortie | Part | IC 95 % |
|---|---|---|
| Au gardien | 4,9 % | [3,7 ; 6,1] |
| À un coéquipier | 2,2 % | [1,5 ; 2,9] |
| À l'adversaire | 0,9 % | [0,5 ; 1,4] |
| Encore libre | 12,2 % | [10,6 ; 13,9] |
| Sortie de but | 57,2 % | [55,1 ; 59,2] |
| Corner | 19,4 % | [17,6 ; 21,2] |
| Engagement (but) | 3,2 % | [2,3 ; 4,1] |
| Autre arrêt de jeu | 0 % | |

**Trouvaille : 70,9 % de ces ballons sont des tirs adverses** [69,0 ; 72,8] (tir de l'adversaire dans les 5 s qui précèdent la sortie). Le gardien est donc surtout en « sortie » sur un tir qui part, et la sortie se termine en sortie de but (57 %), en corner (19 %) ou en but (3 %), pas en prise de balle. La part de sorties « gagnées » de 4,9 % du 03g (relance) correspond au 4,9 % de ballons au gardien ici : elle ne dit presque rien sur les sorties sur ballon en profondeur. Un tir adverse **après** la sortie est rare (1,3 % [0,8 ; 1,8]).

**Ballons qui ne sont pas des tirs** (10,16 par match [9,26 ; 11,07], 29 % des ballons) : c'est le cas visé par la réserve A1 du 03d (passe en profondeur coupée).

| Ballon 3 s après | Part | IC 95 % |
|---|---|---|
| Au gardien | 14,9 % | [11,6 ; 18,2] |
| À un coéquipier | 5,8 % | [2,8 ; 8,9] |
| À l'adversaire | 2,4 % | [1,2 ; 3,5] |
| Encore libre | 24,1 % | [20,5 ; 27,7] |
| Sortie de but | 5,9 % | [3,7 ; 8,1] |
| Corner | 45,5 % | [40,9 ; 50,2] |
| Engagement (but) | 1,4 % | [0,4 ; 2,3] |

Sur ces ballons, le gardien a le ballon 3 s après environ six fois plus souvent que l'adversaire (14,9 % contre 2,4 %), et l'adversaire ne l'a que dans 2,4 % des cas : le gardien ne perd pas le ballon au profit de l'attaquant. Mais seuls 20,7 % sont des prises nettes (gardien ou coéquipier), et **45,5 % finissent en corner**, ce que cet indicateur n'explique pas. Hypothèse, non démontrée : ballons déviés ou dégagés derrière la ligne par le gardien ou un défenseur, ou tirs plus anciens que la fenêtre de 5 s. Le ballon ne distingue pas non plus une passe en profondeur adverse d'un dégagement ou d'une passe en retrait de sa propre équipe ; la preuve du cas « passe en profondeur coupée » reste donc **indirecte**.

**Limites.** (1) Environ 10 ballons hors tir par match : les intervalles sont larges (±3 à ±5 points). (2) « Tir » = tir de l'adversaire dans les 5 s qui précèdent la première sortie (fenêtre du ticket, non calibrée). (3) Le ballon est suivi depuis la première sortie : un ballon qui change de nature (déviation, rebond) reste classé selon cet instant. (4) Les ballons où la sortie arrive en fin de match, avec moins de 5 s de suivi, sont écartés (compte « non résolus »).

**Réserve A1 de l'expert (acceptée).** Le « 71 % de tirs » est une **proximité temporelle** (tir adverse dans les 5 s qui précèdent la sortie), pas l'état du ballon : un rebond ou un ballon contré y sont aussi classés « tir ». Les 45,5 % de corners des ballons hors tir restent sans explication (pistes non testées : centres ou corners joués longs, tirs plus anciens que 5 s). **Condition :** avant de régler le filtre de portée ou la sortie sur tir (05b, 18e), trier par état du ballon (tir en vol, rebond, centre) dans le ticket concerné ; ne pas prendre ce 71 % pour une preuve de tir en vol.

**À décider par le propriétaire (aucun réglage fait ici).** Le moteur traite un tir en vol comme un ballon libre pour le déclenchement de la sortie du gardien (`gardien.race`, 03d) : sur 71 % des ballons à sortie, le gardien « va chercher le ballon » vers son point d'arrêt au lieu de se placer pour l'arrêt. Le rapprocher de l'arrêt par portée (`v2-realisme/05b`) ou du calibrage 18e est une piste ; elle n'est pas dans le périmètre du 03i.

**Déterminisme.** Deux exécutions de 2 matchs (`03i-det1.txt`, `03i-det2.txt`) : sorties identiques, hors la ligne de durée de calcul.

## 14. Gardien : sorties triées par état du ballon (ticket v2-realisme/03j, 50 matchs, 08/11/2026)

`uv run python -m scripts.bench_series 50 --processus 7 --json .scratch/v2-realisme/mesures/03j.json` (graine d'audit 20260923, rapport `03j.txt`), moteur du 03i (`e76ddf5`) avec les indicateurs du 03j. **Mesure seulement : aucune constante du moteur, aucun réglage du filtre de portée, de `gardien.race` ni de la sortie sur tir.** Réserve A1 de l'expert du 03i.

**Définition de l'état (proposée avant le code, acceptée d'office).** Chaque ballon avec sortie reçoit un seul état, lu à sa première sortie. Le moteur ne pose `shot_for` que pour un tir qui entre ; un tir « à côté », contré ou arrêté n'a aucun drapeau propre. L'état vient donc de **l'issue du dernier tir tracé de l'adversaire** (`ShotEvent`) dans les 5 s qui précèdent la sortie (but, à côté, contré, repoussé, claqué ; l'instant du tir et celui de la sortie coïncident au tick près, écart minimal 0,0 s sur un match instrumenté) ; à défaut, par les drapeaux du ballon : `rebound` (rebond sans tir récent), `receiver` (passe ou centre), sinon « autre » (dégagement, déviation, ballon perdu). Le tir de sa propre équipe ou plus ancien que 5 s n'entre pas. Le compteur « non résolus » (réserve A2 du 03i) est ajouté au rapport : **0,0 par match**.

**Nombre de ballons avec sortie par état (par match, IC 95 %).**

| État du ballon à la sortie | Par match | IC 95 % | Part |
|---|---|---|---|
| Tir à côté | 22,26 | [20,67 ; 23,85] | 63,6 % |
| Tir contré | 7,32 | [6,59 ; 8,05] | 20,9 % |
| Tir claqué par le gardien | 1,80 | [1,42 ; 2,18] | 5,1 % |
| Tir qui entre (but) | 1,10 | [0,79 ; 1,41] | 3,1 % |
| Tir repoussé par le gardien | 0,80 | [0,55 ; 1,05] | 2,3 % |
| Passe ou centre | 0,58 | [0,37 ; 0,79] | 1,7 % |
| Autre (dégagement, déviation) | 1,16 | [0,89 ; 1,43] | 3,3 % |
| Rebond sans tir récent | 0 | | 0 % |
| **Total** | **35,02** | [32,73 ; 37,31] | 100 % |

La somme des états égale les ballons avec sortie du 03i (35,02), vérifié par un test et par la mesure.

**Les tirs sont 95,0 % des ballons avec sortie, pas 71 %.** Le chiffre du 03i était sous-estimé : il s'appuyait sur l'appel du banc au tir (`on_shot`), qui ne voit pas les tirs contrés (deux cas relevés sur un match instrumenté : 61 appels pour 74 événements tracés). Les 10,2 ballons « hors tir » du 03i sont pour l'essentiel des **tirs contrés** (7,3 par match). Le corner, 45,5 % de ces ballons au 03i, est expliqué : un tir contré finit en corner dans 54,9 % des cas, un tir claqué dans 96,7 %.

**Croisement avec le « hors tir » du 03i (critère 4 du ticket).** Les 10,16 ballons par match que le 03i classait « hors tir » se répartissent ainsi, avec la part qui finit en corner (somme : 4,64 corners par match, soit 45,7 % ; le 03i donnait 45,5 %) :

| État du ballon | Ballons « hors tir » du 03i par match | dont corner par match |
|---|---|---|
| Tir contré | 7,32 | 4,02 |
| Autre (dégagement, déviation) | 1,16 | 0,32 |
| Tir à côté | 0,66 | 0,08 |
| Passe ou centre | 0,58 | 0,02 |
| Tir claqué | 0,20 | 0,20 |
| Tir qui entre | 0,14 | 0 |
| Tir repoussé | 0,10 | 0 |
| Tir capté, rebond sans tir récent | 0 | 0 |

Les corners « hors tir » sont donc des **tirs contrés** à 87 % (4,02 sur 4,64), pas des centres ni des dégagements : les centres et les dégagements pèsent 0,34 corner par match. L'état « tir capté » est classé mais vaut 0 (un tir capté laisse le ballon au gardien, il n'y a pas de sortie).

**Issue à 3 s selon l'état (agrégé sur 50 matchs).**

| État | Gardien | Coéquipier | Adversaire | Encore libre | Sortie de but | Corner | But |
|---|---|---|---|---|---|---|---|
| Tir à côté (1 113 ballons) | 0,7 % | 0,6 % | 0,4 % | 5,8 % | **89,1 %** | 3,2 % | 0 % |
| Tir contré (366) | 16,4 % | 1,1 % | 0 % | 26,8 % | 0,8 % | **54,9 %** | 0 % |
| Tir claqué (90) | 0 % | 0 % | 0 % | 1,1 % | 2,2 % | **96,7 %** | 0 % |
| Tir repoussé (40) | 0 % | 15,0 % | 7,5 % | **77,5 %** | 0 % | 0 % | 0 % |
| Tir qui entre (55) | 0 % | 0 % | 0 % | 0 % | 0 % | 0 % | **100 %** |
| Passe ou centre (29) | 3,4 % | 3,4 % | 3,4 % | **72,4 %** | 10,3 % | 3,4 % | 3,4 % |
| Autre (58) | 19,0 % | 32,8 % | 17,2 % | 3,4 % | 0 % | 27,6 % | 0 % |

**Ce que cela dit du gardien.**
- **Le gardien « sort » surtout sur un tir qui s'en va.** 22,3 ballons par match sont des tirs à côté, qui finissent en sortie de but dans 89 % des cas ; le gardien a le ballon à 3 s dans 0,7 %. Ces « sorties » sont une course vers un ballon qui quitte le terrain. La part de sorties « gagnées » (4,9 % au 03g et au 03i) mélange ces 22 courses perdues d'avance avec les rares vraies sorties.
- **Le cas visé par la réserve A1 du 03d (passe en profondeur coupée) est trop rare pour être prouvé.** « Passe ou centre » : 0,58 ballon par match (29 sur 50 matchs), « autre » 1,16 (58). À 72 % encore libre à 3 s pour les passes, aucune conclusion sur le gain du ballon n'est permise. Cette preuve ne se fera pas par le banc sur matchs entiers : une scène contrôlée (`tests/scenes.py`) ou un ticket qui force la situation est la voie.
- **Sur « autre »** (dégagements, déviations), le gardien a le ballon à 3 s dans 19 % des cas, un coéquipier dans 33 %, l'adversaire dans 17 % : seul état où la sortie ressemble à une vraie prise de ballon (58 ballons, intervalle large).

**Limites.** (1) L'état « tir » est une proximité de 5 s entre le tir tracé de l'adversaire et la sortie ; un tir dévié puis un second ballon dans la fenêtre seraient classés « tir ». (2) Un tir « à côté » peut encore être dévié en route (`ShotEvent`) : classé « à côté ». (3) « Rebond sans tir récent » vaut 0 : les drapeaux `rebound` ne servent jamais seuls. (4) Parts de l'issue à 3 s agrégées (pas d'intervalle par état) ; les états rares (passe 29, repoussé 40, but 55) ont des effectifs faibles. (5) « Passe ou centre » est lu par `receiver` seul : il mélange les passes adverses coupées et les passes de sa propre équipe vers le gardien (passe en retrait) ; 0,58 ballon par match, effectif trop faible pour les séparer, à faire par `last_pass_team` dans une prochaine mesure (réserve A2 du 03j).

**À décider par le propriétaire (aucun réglage fait ici).** Le moteur traite un tir en vol comme un ballon libre pour déclencher la sortie du gardien (`gardien.race`, 03d, `loose_in_reach`) : 63,6 % des sorties sont des courses vers un tir à côté. Les candidats à écarter de ce déclencheur sont les **tirs à côté et les tirs qui entrent : 23,4 ballons par match**, les seuls dont la trajectoire est décidée au départ du tir. Les 9,9 autres tirs par match (contrés, repoussés, claqués) sont des ballons déviés, donc des seconds ballons que le gardien peut jouer (16,4 % des contrés finissent au gardien, 77,5 % des repoussés restent libres) : ils restent des ballons libres. Projection : environ 11,7 sorties par match (35,02 − 22,26 − 1,10), **à mesurer, non affirmée** ; le chiffre « environ 2 » (tous les tirs retirés) est une borne basse, qui ferait perdre au gardien le réflexe de suivre un rebond. C'est une modification de comportement du gardien, à traiter en ticket dédié (`v2-realisme/03k`) ou avec le `05b` (arrêt par portée), avec mesure avant et après sur les deux populations (tirs en vol et ballons déviés).

**Déterminisme.** Deux exécutions de 2 matchs (`03j-det1.txt`, `03j-det2.txt`) : sorties identiques, hors la ligne de durée de calcul.
