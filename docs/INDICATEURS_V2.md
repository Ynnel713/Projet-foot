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
| Issues du tir | Part des tirs tracés (`ShotEvent`, contrés et penaltys compris) cadrés (but, capté, repoussé, claqué), contrés, à côté, au-dessus, dévissés, et conversion (buts / tirs) (tickets 28b et 35b ; mesure du 35b sur 48 matchs : cadrés 32,4 %, à côté 26,1 %, au-dessus 20,9 %, dévissés 2,4 %) | % | cadrés 30-35 %, contrés 20-28 % (22,5 % Bundesliga 2015-16), conversion 10-11 % : ordres de grandeur du ticket 28 |
| Buts dans la surface | Part des buts marqués d'un tir parti de la surface de réparation (ticket 28b) | % | 80-90 % (ordre de grandeur du ticket 28) |
| Issues des arrêts | Part des arrêts captés, repoussés en jeu, claqués derrière la ligne (corner) ; arrêts par match (ticket 28b) | %, nombre | répartition non publiée (Opta la relève sans la publier) ; environ 20 % des corners viennent d'un arrêt (ordre de grandeur, sans méthode publiée) |
| Origine des tirs | Part des tirs selon la façon dont le tireur a eu le ballon : passe au sol, en retrait, en profondeur, centre, dribble (plus de 5 m porté), rebond, récupération, coup franc, penalty (ticket 28b) | % | suivi, pas de cible |
| Grosses occasions | Séquences dangereuses dont le pic de danger atteint 0,20 (`occasion.BIG_CHANCE_DANGER`), avec ou sans tir (`ChanceEvent` de la trace, ticket 28c) : nombre par match, part sans tir, danger moyen au pic, part par issue (tir et son issue, tacle, interception, gardien, dégagement, ballon non repris, danger retombé, ballon mort) et par origine. Danger d'une équipe à un instant : meilleure qualité d'occasion (28a) de ses joueurs de champ à 30 m du but ou moins, multipliée par la chance que le ballon leur parvienne (porteur 1 ; coéquipier : réussite de la passe, hors-jeu exclus ; ballon libre : course au ballon sur sa trajectoire, qualité lue au point de contact). Séquence : du premier instant à 0,10 ou plus jusqu'à la retombée sous 0,10, ou au tir. Mesure du 28c sur 50 matchs : 7,7 par match, 52 % sans tir | nombre, % | aucun chiffre réel pour cette définition large ; repère : les « big chances » d'Opta, tirs seulement, environ 3 à 5 par match (de mémoire, non sourcé) |
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
| Grosse occasion : pic de danger | ≥ 0,20 (chance de but d'un face-à-face à 8-9 m, gardien sur sa ligne) ; séquence ouverte à 0,10 ; course au ballon libre : retard de r s → exp(−r / 0,2), passe adverse en vol disputée seulement par ceux qui l'ont lue | Proposé (ticket 28c), accepté d'office par le propriétaire. Défini dans le moteur (`v2engine/occasion.py`) mais sans effet sur le jeu |

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

## 15. Gardien : tirs en vol retirés du déclencheur de sortie (ticket v2-realisme/03k, 50 matchs appariés, 08/11/2026)

`uv run python -m scripts.bench_series 50 --processus 7 --json .scratch/v2-realisme/mesures/03k.json` (graine d'audit 20260923, rapport `03k.txt`), comparée à `03j.json` (`--comparer`, rapport `03k-comparaison.txt`). **Changement de comportement, sans aucune constante nouvelle** : le moteur pose un drapeau `shot_wide` au départ d'un tir « à côté » (le tir qui entre avait déjà `shot_for`) ; `BallState.shot_in_flight` les réunit ; dans `cerveau._keeper`, un tir en vol n'entre plus dans `reach` : le gardien reste en placement, avec la raison tracée « tir en vol : il garde sa place pour l'arrêt, le ballon ne peut pas être pris ». Le drapeau est effacé aux cinq sites qui remettent déjà `pass_from` et `rebound` à zéro (touche d'un joueur, ballon sorti, ballon mort, remise en jeu, nouvelle action d'un porteur). Un ballon contré, repoussé ou claqué (`rebound`, sans drapeau) reste un ballon libre. Deux indicateurs ajoutés : placements du gardien sur tir en vol (état « placement, tir en vol », distinct de « ballon libre laissé ») et joueurs de champ en rôle `BALLON_LIBRE` pendant un tir en vol (mesure seule).

**Sorties du gardien par match (50 matchs appariés).**

| État du ballon à la première sortie | 03j (avant) | 03k (après) | Écart apparié |
|---|---|---|---|
| Tir à côté | 22,26 | 0,74 | −21,52 ± 1,6 |
| Tir qui entre (but) | 1,10 | **0** | −1,10 ± 0,31 |
| Tir contré | 7,32 | 7,48 | bruit |
| Tir claqué | 1,80 | 1,84 | bruit |
| Tir repoussé | 0,80 | 0,74 | bruit |
| Passe ou centre | 0,58 | 0,48 | bruit |
| Autre (dégagement, déviation) | 1,16 | 1,34 | bruit |
| **Ballons avec sortie** | **35,02** | **12,62** | **−22,4 ± 1,9** |

Les sorties (épisodes de l'état) sont 12,68 par match, contre 35,02 ; elles ne coïncident plus exactement avec les ballons avec sortie (écart de 0,06, dont 0,02 ballon non résolu en fin de match). La projection du ticket (environ 11,7) est dépassée de 8 % (12,6), sous les 20 % demandés : l'écart vient de la hausse de « autre » et de « contré » dans le bruit, et des tirs à côté touchés en route (ci-dessous).

**Les 0,74 sorties restantes sur « tir à côté » (critère du ticket : 0).** Aucune n'est un tir en vol : toutes sont « tir récent » au sens de l'indicateur (croisement avec le « hors tir » du 03i : 0). Une sonde sur 4 matchs (4 cas) montre un ballon à 12 à 13 m/s, `shot_wide` déjà faux depuis 0,1 à 0,3 s, dernier joueur à l'avoir touché (un défenseur) : le tir à côté a été **touché en route**, le drapeau est tombé comme le ticket le prévoit (« effacé dès que le ballon change d'état »), le ballon est redevenu un ballon libre ordinaire et le gardien peut le disputer. Ce sont 3 % des 23,4 tirs à côté par match. Le critère « 0 » est donc tenu pour un tir en vol et non pour un tir dévié.

**Placement sur tir en vol et courses des autres.**
- Placements des deux gardiens sur un tir en vol : 63,5 par match (deux gardiens, soit 31,8 par gardien) pour environ 26,5 tirs en vol par match (23,4 à côté et environ 3,1 qui entrent), soit environ 53 épisodes pour deux gardiens : la raison « tir en vol » est produite pour les deux gardiens, y compris celui du camp du tireur (réserve A3 de l'expert, trace trompeuse, comportement identique). Les 10 épisodes en plus ne sont pas expliqués (alternance d'état d'un gardien pendant un même tir, possible) : c'est un compte d'épisodes de trace, à lire avec prudence, sans effet sur le moteur (réserve A2 de l'expert). Les « ballons libres laissés » baissent de 42,5 à 34,3 (−8,2 ± 2,4) : l'indicateur ne compte plus les tirs en vol.
- **Joueurs de champ qui courent encore derrière un tir en vol (non modifiés, critère du ticket) :** 177,6 épisodes par match sur un tir à côté (soit 7,6 joueurs par tir à côté, pour 23,4 tirs à côté par match) et 18,2 sur un tir qui entre. Ce défaut reste entier côté joueurs de champ ; l'arrêt par portée reste au 05b, la correction éventuelle à proposer au propriétaire.

**Qualité des sorties restantes.** Sorties réussies 5,0 % → 13,9 % (+8,4 points), sorties disputées gagnées 4,9 % → 13,7 % (+8,6 points, IC [5,9 ; 11,3]), sorties disputées 33,3 → 12,2 par match, sorties très disputées 9,1 → 5,6. Ballon au gardien à 3 s : 4,6 % → 12,8 %. La « sortie gagnée » mesure maintenant des ballons disputables.

**Effets de jeu, sans réglage (écarts appariés, IC 95 %).** Aucun n'est au-delà du bruit : buts par match +0,04 [−0,50 ; +0,58] (3,08 → 3,12), tirs par équipe −0,30 [−1,31 ; +0,71], chance moyenne des tirs +0,00001 [−0,006 ; +0,006], arrêts par match −0,46 [−1,48 ; +0,56], corners par match −0,5 [−1,56 ; +0,56], conversion −0,0002, distance moyenne du gardien à son but +0,007 m [−0,05 ; +0,06]. Sur les 411 lignes comparées, 40 sortent de l'IC à 95 % : 32 sont des indicateurs du gardien ou de ses sorties, attendus ; les 8 autres sont de très petits écarts (réussite moyenne des passes +0,0018, largeur avec ballon −0,04 m, quelques indicateurs du milieu défensif sur 39 matchs) sans lien avec le gardien, que le hasard seul produit (à 5 %, 411 lignes en donnent environ 20).

**À décider par le propriétaire.** Les joueurs de champ qui courent derrière un tir à côté (177,6 épisodes par match) : ticket à créer après le 05b si l'on veut qu'ils gardent leur place comme le gardien. Le tir contré (7,5 par match) reste un ballon libre pour le gardien ; il finit en corner dans 55 % des cas.

## 16. Conduite : même risque de perte à l'évaluation et à la résolution (ticket v2-realisme/04a, 50 matchs appariés, 08/11/2026)

**Ce que fait le moteur.** Une seule fonction, `decision.keep_ball_probability`, donne la chance de garder le ballon en conduisant sur une durée de référence `DRIBBLE_REFERENCE_S` = 1,5 s. L'évaluation de l'option (`dribble_loss_probability`) et la résolution en match (`dribble_lost`, un tirage par intervalle de décision de 0,5 s, flux DUEL) la lisent toutes les deux ; la perte par intervalle vaut `1 − garde^(intervalle / 1,5 s)`. La perte « sous pression » (`PRESSURE_KEEP_SHARE`) a quitté la conduite pour ne pas compter deux fois avec le tacle, qui reste tiré à part ; elle reste pour les passes. Strength et Balance ne sont pas lus (règle R1 de la carte des attributs).

**Indicateurs ajoutés** (`scripts/measure_v2.py`, `scripts/v2_indicators.py`) : intervalles de conduite par match, pertes par match et par intervalle, ventilés conduite libre (gêne < 0,1) et serrée (gêne ≥ 0,5).

**Résultat de la série (50 matchs, graine d'audit 20260923, comparée à la série du 03k).**
- Conduite : 2 277 intervalles par match [2 203 ; 2 351], 87,6 pertes par match [84,1 ; 91,1], soit 3,85 % par intervalle. Libre : 141 intervalles, 0,64 % de perte ; serrée : 1 839 intervalles, 4,30 %. Le risque réel croît avec la gêne, comme l'évaluation.
- Chiffre de référence réel : non trouvé. Aucune source chiffrée sur la réussite moyenne des dribbles en conduite serrée ; l'ordre de grandeur, environ 50 % de dribbles réussis chez les dribbleurs de volume, vaut comme indication et non comme cible. Aucune constante n'a été réglée sur ce chiffre.

**Effets sur le jeu (écarts appariés, IC 95 %, sans réglage).** Le porteur ne voit plus la pression compter deux fois dans la conduite ; elle devient donc l'option la plus attractive.
- Choix de la conduite 45,3 % → 73,7 % des décisions (+28,4 points [26,5 ; 30,3]), passe 51,6 % → 24,7 %, tir 3,05 % → 1,52 %. Part des décisions, une conduite se prolonge sur plusieurs décisions.
- Passes par match 1 032 → 816 (−215,8 [−232,7 ; −198,9]), réussite des passes 69,5 % → 72,4 % (+2,9 points), pertes de balle par match 343 → 295 (−47,8), temps par possession de joueur 2,26 s → 3,02 s (+0,76 s), possession d'équipe +2,6 s.
- Tirs par équipe 23,5 → 19,4 (−4,1 [−5,7 ; −2,5]), part des tirs issus d'une conduite 60,2 % → 69,8 %, tirs de contre −9,4 par match. Buts par match 3,12 → 2,78 (−0,34 [−1,13 ; +0,45], dans le bruit), tirs cadrés +2,1 points, arrêts par match 15,2 → 13,0.
- Tacles par match 33,1 → 42,2 (+9,2 [7,9 ; 10,5]) : plus de conduites sous pression, donc plus de tacles tentés au taux calibré. Fautes +3,0 par match, coups francs +2,6, corners −2,6.
- Appels par match −153, course à plus de 19,8 km/h −2,3 points de la distance : moins de passes à préparer.
Sur les 413 lignes comparées, 219 sortent de l'IC (le moteur change vraiment de répartition entre conduite et passe) ; le but, la conversion et la répartition des tirs de près restent dans le bruit.

**Lecture.** Les passes passent de 91 au-dessus à 125 au-dessous de la référence R7 (941 par match, Premier League 2023-24) : la baisse ne vaut pas rapprochement du réel. Les tirs tracés par équipe (23,2 contre 28,7 au 03k) restent au-dessus des 8 à 15 de R1. Le surcroît de conduite est le point à surveiller (74 % des décisions, dont 81 % des intervalles avec un adversaire à moins de 2,5 m) ; ces volumes ne sont pas une référence de réalisme (réserve A1 de l'expert, à traiter aux tickets 04b et 04c). Le tir recule de 3,05 % à 1,52 % des décisions : à regarder au 04b/04c. Le tacle (calibré à 33 par match au ticket précédent) monte à 42 : son recalibrage est à décider avec le propriétaire, non fait ici.

**Déterminisme.** Deux exécutions de `measure_v2 2` à graine fixée donnent des sorties identiques, à la ligne de temps de calcul près.

**Suite complète.** 2 544 passés, 14 désélectionnés (trois tests existants adaptés : raison « face-à-face » du gardien admise par un test à graine fixée, conduite à 99 de Finishing pour le « bon finisseur » du bord de surface, choix de la passe imposé dans le test de réception).

## 17. Conduite : où va le ballon perdu (ticket v2-realisme/04b, 20 matchs, 08/11/2026)

**Ce que fait le moteur.** Une perte de conduite (04a) a deux issues, tirées dans le flux DUEL par `decision.lost_carry_outcome`. Un adversaire à moins de 1,5 m (la portée du tacle) prend le ballon avec la probabilité de la gêne (70 % à 1,5 m, 100 % au contact) : le ballon lui passe comme sur un tacle gagné. Sinon, c'est une touche trop longue : le ballon part devant le porteur et s'arrête, après une course de 1,5 à 4 m depuis le point où il est lâché (à environ 0,4 m du porteur), dans ± 30° de sa direction de conduite, puis il est disputé comme tout ballon libre (rôle `BALLON_LIBRE`, porteur écarté 0,5 s). Sans adversaire au contact, jamais de dépossession. Aucun attribut n'est lu (la déviation ne dépend plus de la vitesse de course, de Composure ni du flux PASSE). Chiffres réels pour ces bornes : non trouvés.

**Indicateurs ajoutés** (`scripts/measure_v2.py`, `scripts/v2_indicators.py`) : pertes par dépossession et par touche trop longue par match, part des dépossessions.

**Résultat (20 matchs, graine d'audit 20260923).** 86,6 pertes de conduite par match [79,6 ; 93,5] (87,6 sur 50 matchs au 04a) : **46,2 dépossessions (53,4 %)** [42,7 ; 49,7] et **40,4 touches trop longues (46,6 %)** [35,8 ; 45,0]. Perte par intervalle : 0,42 % en conduite libre, 4,36 % en conduite serrée (0,64 % et 4,30 % au 04a). Volumes voisins du 04a, hors comparaison appariée (20 contre 50 matchs) : conduite 72,5 % des décisions (73,7 %), passes 848 par match (816), tirs par équipe 18,3 (19,4), tacles 41,2 (42,2), buts 2,95 (2,78), tous dans le bruit.

**Lecture.** La part de dépossession vient de la proportion de pertes subies avec un adversaire à moins de 1,5 m, non d'un réglage. Ce que devient la touche trop longue (reprise par le porteur, par l'adversaire, par un coéquipier) n'est pas tracé ici : il est regardé au 04c. Les volumes de conduite (réserve A1 du 04a) restent à examiner au 04c ; ils ne sont pas une référence de réalisme.

**Déterminisme.** Deux exécutions de `measure_v2 2` à graine fixée donnent des sorties identiques, à la ligne de temps de calcul près.


## 18. Conduite : risque annoncé, probabilité calculée, résultat observé (ticket v2-realisme/04c, 50 matchs, 08/11/2026)

**Ce que mesure l'indicateur.** À chaque tirage de perte de conduite (un par intervalle de décision de 0,5 s, `decision.dribble_lost`), le banc note le risque évalué à cet instant (`dribble_loss_probability`, la fonction que lit l'évaluation de l'option) et la perte tirée, rangés par tranche de gêne du porteur (`pressure`) et par tranche de Dribbling (`CARRY_PRESSURE_BINS`, `CARRY_DRIBBLING_BINS`, `scripts/v2_indicators.py`). Écart = perte tirée − risque évalué, en points. Deuxième colonne : la perte « avec tacle gagné » compte aussi le tacle gagné sur ce porteur avant sa décision suivante (le tacle est tiré à part, 04a). Mesure seule : le jeu n'est pas modifié.

**Résultat (50 matchs, graine d'audit 20260923), par tranche de gêne.**

| Gêne | Intervalles par match | Risque évalué | Perte tirée | Écart (points) | Perte avec tacle | Écart avec tacle |
|---|---|---|---|---|---|---|
| [0 ; 0,1[ | 136,0 | 0,62 % | 0,63 % | +0,01 | 0,63 % | +0,01 |
| [0,1 ; 0,3[ | 92,9 | 1,62 % | 1,76 % | +0,15 | 1,76 % | +0,15 |
| [0,3 ; 0,5[ | 197,9 | 2,66 % | 2,47 % | −0,19 | 2,48 % | −0,18 |
| [0,5 ; 0,7[ | 597,4 | 3,72 % | 3,54 % | −0,19 | 3,59 % | −0,13 |
| [0,7 ; 0,9[ | 1 208,7 | 4,71 % | 4,76 % | +0,05 | 5,04 % | +0,33 |
| [0,9 ; +[ | 8,3 | 5,35 % | 5,76 % | +0,40 | 5,76 % | +0,40 |

Par Dribbling : [0 ; 40[ 36,7 intervalles, écart −0,18 ; [40 ; 55[ 349,0, −0,24 ; [55 ; 70[ 1 221,0, +0,03 ; [70 ; +[ 634,6, −0,02 (risque évalué 4,5 % → 3,5 % de la tranche basse à la haute).

**Lecture.**
- **Critère tenu** : écart maximal 0,40 point (sous 3 points) sur toutes les tranches de gêne, 0,24 sur celles de Dribbling. Le plus grand écart tombe sur la tranche la plus vide (8 intervalles par match, 417 sur la série, erreur type environ 1,1 point) : il est dans le bruit. Les autres écarts sont de 0 à 1,7 erreur type.
- **Ce que la mesure prouve et ne prouve pas.** L'évaluation et le tirage lisent la même fonction (04a) : l'accord est attendu, et l'indicateur sert de garde-fou si l'un des deux dérive (test synthétique : un moteur qui perdrait deux fois plus donne un écart égal au risque évalué). Il ne dit pas que le niveau de risque est réaliste : 3,86 % par intervalle de 0,5 s, soit 86,5 pertes de conduite par match ; chiffre de référence réel : non trouvé (voir la section 16).
- **Le tacle n'ajoute pas de perte cachée** : 3,8 tacles gagnés par match tombent dans un intervalle de conduite ouvert (sur 2 241 intervalles), soit +0,0 à +0,3 point selon la tranche. Les 42,1 tacles par match tombent donc pour l'essentiel hors d'un intervalle de conduite ouvert (porteur qui vient de recevoir, de passer ou de tirer) ; cette répartition n'est pas analysée ici.
- **Limite de la colonne « avec tacle »** (réserve A1 de l'expert) : un tacle gagné n'est compté que s'il tombe aux ticks +0,1 à +0,4 s après le tirage ; le tick +0,5 s, où le moteur résout le tacle juste avant la décision suivante, est exclu (`< DECISION_INTERVAL_S`). Environ un tacle sur cinq de ceux qui tombent dans un intervalle ouvert (3,8 par match) est donc manqué, soit au plus 0,8 par match et environ +0,1 point sur la tranche concernée. Le critère des 3 points (colonne « perte tirée ») n'est pas touché. Correctif d'une ligne si la colonne devient une mesure : `<= DECISION_INTERVAL_S + 1e-9`, avec un test à 0,5 s compté.
- **Dribbling pèse peu par intervalle** (3,5 à 4,5 % de la tranche haute à la basse) : l'effet est réel mais faible sur 0,5 s ; sur la durée de référence de 1,5 s il se cumule (section 16).

**À refaire** après les tickets 04e, 07 et 11 (`python -m scripts.measure_v2 50`, clés `calibration conduite, …`).

**Réserves du 04b non traitées ici** (le ticket 04c est une validation, sans changement de moteur) : A1, la dépossession ne reprend pas les garde-fous du tacle (`engaged`, `tackle_ban_until_s`, `offside_out_until`) ; A3, le porteur écarté 0,5 s dépasse le ballon libre. Le banc ne voit pas ces états depuis `lost_carry_outcome` : à traiter dans un ticket dédié si le propriétaire le décide.

## 19. Tir : occasion, exécution, gardien, par attribut (ticket v2-realisme/06b, 50 matchs et profils forcés, 09/11/2026)

**Ce que mesurent les indicateurs.** Chaque tir hors penalty (clés `décomposition du tir, …`, `scripts/v2_indicators.py`) est rangé, au moment de la frappe, dans la tranche de la note qui joue sur lui (`SHOT_NOTE_BINS`, mêmes bornes que Dribbling au 04c) : Finishing dans la surface ou Long Shots dehors (`shooting.shooting_note`), Composure si le tireur est pressé (`shot_pressure` > 0), Reflexes du gardien adverse. Par tranche :
- **occasion** : xG neutre moyen par tir (tireur et gardien moyens, section 06a), contrés compris ;
- **exécution** : xG après frappe moins xG neutre, par tir non contré (ce que la frappe ajoute ou retire à l'occasion) ;
- **gardien** : xG après frappe moins buts, par tir non contré (buts évités par le gardien par rapport à un gardien moyen ; positif : il en évite).
- **calibration de l'xG après frappe** (réserve A1 du 06a) : xG après frappe moins buts sur les tirs cadrés jugés par le gardien, par match, recalculé pour plusieurs étalements (`PSXG_SPREADS_M`) à partir de l'écart et du temps tracés.

**Calibration (50 matchs, graine d'audit, 10 lots de 5, jeu identique au 06a).** xG après frappe moins buts, par match : étalement 0,05 m −0,12 ± 0,07 ; 0,10 m −0,06 ± 0,08 ; **0,15 m +0,02 ± 0,09** ; 0,20 m +0,12 ± 0,11 ; 0,30 m (valeur du 06a) +0,33 ± 0,12. `shooting.PSXG_SPREAD_M` passe à 0,15 m (critère : écart sous 2 erreurs types, tenu).

**Par attribut : profils forcés (note 99 contre 11, 20 matchs par profil, 5 lots appariés de 4 matchs, étalement 0,15 m).** La copie neutre du tireur et du gardien (`shooting.NEUTRAL_ATTRIBUTES`, même valeur par défaut que `attributes=None`) n'est pas forcée (`measure_v2._force_attribute`, réserve A1 de l'expert : la première série avait un xG neutre qui recevait la note forcée). Écart 99 − 11 : moyenne des écarts par lot apparié (même graine, rôles inversés) ± erreur type.

| Profil | Tranche | Tirs (non contrés) | Occasion (xG neutre) | Exécution, par tir | Gardien, par tir |
|---|---|---|---|---|---|
| Finishing (surface) | 11 | 104 (79) | 0,221 | −0,027 | −0,018 |
| Finishing (surface) | 99 | 147 (114) | 0,146 | +0,117 | +0,003 |
| Finishing, écart 99 − 11 | | | −0,060 ± 0,034 | **+0,139 ± 0,036** | +0,021 ± 0,013 |
| Long Shots (dehors) | 11 | 189 (160) | 0,019 | −0,005 | −0,005 |
| Long Shots (dehors) | 99 | 369 (290) | 0,021 | +0,023 | +0,011 |
| Long Shots, écart 99 − 11 | | | +0,003 ± 0,001 | **+0,030 ± 0,008** | +0,015 ± 0,003 |

**Lecture.**
- **Exécution** : le gain croît avec la note, de 3,9 erreurs types pour Finishing dans la surface et de 4,0 pour Long Shots dehors. Une note de 11 retire de l'occasion (−0,03 et −0,005 par tir), une note de 99 en ajoute.
- **Occasion** : avec Finishing 99, l'équipe tire plus (147 tirs contre 104) depuis de moins bonnes positions (xG neutre 0,146 contre 0,221, 1,8 erreur type) : la décision de tirer lit `shot_probability`, qui contient la note. Effet de décision, pas un double comptage de l'exécution. Pour Long Shots, l'écart d'occasion (+0,003) est négligeable.
- **Gardien** : les notes du gardien n'agissent pas encore sur l'arrêt physique (portée neutre du 05b ; `v2-attributs-restants/03b`). Sur la série de 50 matchs, le gain du gardien vaut +0,009 par tir pour Reflexes 55-70 comme pour 70 et plus. Le résidu qui dépend du tireur (+0,015 ± 0,003 pour Long Shots, +0,021 ± 0,013 pour Finishing) ne vient pas du gardien : l'issue est déterministe (but si l'écart dépasse la portée) alors que l'xG après frappe est lissé (étalement 0,15 m). Un tir arrêté de peu compte donc un peu de gain, et un but de peu en retire un peu. Le solde dépend de la répartition des écarts autour de la portée, qui change avec le tireur. C'est l'explication probable ; elle n'a pas été mesurée tranche par tranche. À reprendre au 06c.
- **Niveau absolu** : l'exécution est biaisée vers le haut, d'environ xG × p_contre / (1 − p_contre), parce que l'xG neutre (`occasion_quality`) compte le contre alors que l'xG après frappe ne porte que sur les tirs non contrés (réserve A2 de l'expert). Le 06c comparera l'xG après frappe à la chance neutre non contrée. Ici, seules les différences entre tranches d'occasion proche comptent.
- **Composure sous pression** : tranches de 73 à 1 172 tirs sur la série, gain d'exécution +0,05 à +0,06 sans ordre net (étalement 0,3 m) ; pas de profil forcé dans ce ticket.

**À refaire** après 06c et `v2-attributs-restants/03b` (`python -m scripts.measure_v2 50`, puis `--profil Finishing` et `--profil "Long Shots"`).

## 20. Calibration de l'xG neutre : courbe et étages de l'écart (ticket v2-realisme/06c, 500 matchs, 09/11/2026)

**Ce que mesurent les indicateurs.** Clés `calibration xG neutre, …` et `gardien par écart à la portée, …` (`scripts/v2_indicators.py`, `xg_calibration`). Tirs hors penalty rangés par tranche d'xG neutre (`XG_BINS`), pour tous les tireurs et pour les tireurs moyens (note de tir dans [55 ; 70[, `AVERAGE_NOTE`, autour de la note neutre 60) : effectif, xG moyen, taux de buts et son intervalle de Wilson à 95 %, buts moins xG par match. L'écart est découpé tir par tir en trois étages dont la somme est exactement buts moins xG :
- **contre** : chance neutre hors contre (xG / (1 − chance de contre prévue, `shooting.block_probability`, lue à la frappe)) pour un tir non contré, buts pour un tir contré, moins l'xG ; négatif : plus de contres réels que prévu ;
- **exécution** : xG après frappe moins chance neutre hors contre, sur les tirs non contrés (corrige le biais du contre du §19, réserve A1 de l'expert au 06b) ;
- **gardien** : buts moins xG après frappe, sur les tirs non contrés.

Série : matchs 1000 à 1499 (indépendants des 50 matchs du 06b), banc 01e, 7 processus, 440 min machine (estimation affichée 240 min, à recaler) ; fichiers `.scratch/v2-realisme/mesures/06c-serie.*`. Intervalles à 95 % : Wilson sur le taux agrégé, banc 01e sur les valeurs par match (`…, par match` vaut 0 dans un match sans tir de la tranche).

**Courbe, tireurs moyens (11 128 tirs).** Étages en buts par match.

| Tranche d'xG | Tirs | xG moyen | Taux de buts [IC95] | Buts − xG par match [IC95] | Contre | Exécution | Gardien |
|---|---|---|---|---|---|---|---|
| [0 ; 0,03[ | 7 556 | 0,017 | 0,023 [0,020 ; 0,026] | +0,086 [+0,038 ; +0,134] | +0,007 | +0,095 | −0,015 |
| [0,03 ; 0,06[ | 2 177 | 0,041 | 0,088 [0,077 ; 0,101] | +0,206 [+0,149 ; +0,263] | −0,006 | +0,225 | −0,013 |
| [0,06 ; 0,1[ | 585 | 0,076 | 0,178 [0,149 ; 0,211] | +0,119 [+0,082 ; +0,156] | −0,001 | +0,131 | −0,010 |
| [0,1 ; 0,2[ | 392 | 0,140 | 0,250 [0,210 ; 0,295] | +0,086 [+0,053 ; +0,119] | +0,002 | +0,096 | −0,012 |
| [0,2 ; 0,35[ | 185 | 0,259 | 0,276 [0,216 ; 0,344] | +0,006 [−0,020 ; +0,032] | −0,001 | +0,012 | −0,004 |
| [0,35 ; 0,5[ | 45 | 0,424 | 0,111 [0,048 ; 0,235] | −0,028 [−0,040 ; −0,016] | +0,000 | −0,023 | −0,006 |
| 0,5 et plus | 188 | 0,777 | 0,378 [0,312 ; 0,449] | −0,150 [−0,187 ; −0,113] | −0,054 | −0,132 | +0,036 |
| **toutes** | **11 128** | **0,048** | **0,062 [0,058 ; 0,067]** | **+0,325 [+0,225 ; +0,426]** | **−0,053** | **+0,404** | **−0,025** |

**Tous les tireurs (23 340 tirs)** : taux de buts par tranche 0,021 ; 0,093 ; 0,198 ; 0,269 ; 0,240 ; 0,219 ; 0,383 pour des xG moyens 0,017 ; 0,042 ; 0,076 ; 0,140 ; 0,260 ; 0,412 ; 0,778. Au total, buts 3,88 et xG neutre 3,04 par match, écart +0,83 [+0,66 ; +0,99] : contre −0,17 [−0,21 ; −0,13], exécution +0,93 [+0,79 ; +1,08], gardien +0,07 [−0,00 ; +0,13]. L'écart de plus que chez les tireurs moyens est attendu : l'xG neutre ignore les notes, l'exécution des bons tireurs s'y ajoute (§19).

**Lecture.**
- **Courbe trop plate.** Une seule tranche est calibrée (0,2 à 0,35). En dessous de 0,2, le taux réel vaut 1,3 à 2,3 fois l'xG ; au-dessus de 0,35, il en vaut la moitié environ (0,38 pour un xG moyen de 0,78). L'xG neutre sous-estime les petites occasions et surestime les grosses.
- **L'écart vient de l'exécution.** Chez les tireurs moyens, l'étage exécution fait +0,40 des +0,33 buts par match d'écart ; le contre −0,05, le gardien −0,03. La résolution physique (trajectoire avec erreur de visée, portée du gardien) ne suit pas la formule analytique (`_XG_LOGIT` et facteurs de `shot_probability`) : une frappe de loin cadrée bat plus souvent le gardien que la formule ne le dit, une frappe de près sur une grosse occasion le bat moins souvent. C'est exactement l'objet du 05e (recaler la formule d'évaluation sur la résolution) : ce tableau lui sert de point de départ.
- **Contre.** Prévu juste pour les tranches sous 0,5 ; au-dessus, il y a plus de contres réels que prévu (−0,05 chez les moyens, −0,16 pour tous) : de près, le contre physique (05c) touche plus que le cône de la décision.
- **Gardien.** Proche de 0 au total (lissage seul, voir ci-dessous) ; +0,04 au-dessus de 0,5 : sur ces tirs, le ballon passe le plus souvent juste au-delà de la portée, là où l'xG après frappe lissé reste sous 1.

**Gain du gardien par écart à sa portée (réserve A2 de l'expert au 06b ; tirs cadrés jugés).** Écart = distance du ballon au gardien quand il passe, moins la portée du gardien moyen à cet instant (`keeper_reach_m`).

| Écart (m) | Tirs | xG après frappe moyen | Taux de buts | xG après frappe − buts, par match |
|---|---|---|---|---|
| moins de −0,3 | 4 346 | 0,015 | 0 | +0,129 |
| [−0,3 ; −0,15[ | 407 | 0,186 | 0 | +0,151 |
| [−0,15 ; 0[ | 404 | 0,375 | 0 | +0,303 |
| [0 ; 0,15[ | 344 | 0,614 | 1 | −0,266 |
| [0,15 ; 0,3[ | 302 | 0,815 | 1 | −0,112 |
| 0,3 et plus | 1 176 | 0,977 | 1 | −0,054 |

L'arrêt est déterministe (aucun but en deçà de la portée, aucun arrêt au-delà) alors que l'xG après frappe est lissé : tout le « gain du gardien » vient de ce lissage et de la répartition des écarts, qui change avec le tireur (Long Shots : écarts surtout très négatifs). Explication du résidu du §19 confirmée. Aucun gardien ne se juge sur cet indicateur tant que l'arrêt ne dépend pas des notes (`v2-attributs-restants/03b`).

**Étalement de l'xG après frappe, revérifié sur ces 500 matchs indépendants.** xG après frappe moins buts des tirs cadrés jugés, par match : 0,05 m −0,20 [−0,26 ; −0,15] ; 0,10 m −0,15 [−0,21 ; −0,09] ; **0,15 m −0,066 [−0,132 ; −0,001]** ; 0,20 m +0,039 [−0,032 ; +0,111] ; 0,30 m +0,28 [+0,20 ; +0,36]. La valeur en vigueur (0,15 m) sous-estime de peu, à la limite de l'intervalle (−0,07 sur 3,8 buts par match, 2 %) ; le zéro tombe vers 0,18 m. Aucun réglage dans ce ticket (constante de mesure, sans effet sur le jeu) : à proposer au propriétaire avec le 05e.

**Profils forcés relancés avec l'exécution corrigée (réserve A1 du 06b ; 20 matchs par profil, mêmes matchs, mêmes tirs que le §19).** Gain d'exécution par tir non contré, contre la chance hors contre : Finishing (surface) 11 : −0,055, 99 : +0,101, écart 99 − 11 **+0,148 ± 0,039** (3,8 erreurs types) ; Long Shots (dehors) 11 : −0,010, 99 : +0,020, écart **+0,032 ± 0,007** (4,4 erreurs types). Les deux niveaux baissent d'environ 0,02 (biais du contre retiré), l'écart entre notes ne change pas. Fichiers `06c-fin*`, `06c-ls*`.

**Déterminisme.** Deux exécutions de 10 matchs (1000 à 1004 : `06c-det1`, `06c-det2`, 784 indicateurs ; 1005 à 1009 : `06c-det1b`, `06c-det2b`, 797 indicateurs) : tout est identique, seul le temps de calcul diffère.

**À refaire** après le 05e (même commande : `uv run python -m scripts.bench_series 500 --debut 1000 --processus 7`) : la courbe des tireurs moyens doit alors passer par la diagonale, tranche par tranche.

## 21. Valeur du tir dans la décision : chance évaluée contre résolution physique (ticket v2-realisme/05e, scènes et 2 x 120 matchs, 10/11/2026)

Commande : `scripts/shot_calibration.py` (`scenes`, `relever`, `verifier`). Fichiers `.scratch/v2-realisme/mesures/05e-*`.

**Avant (formule analytique et cône ; 120 matchs, graines 2000 à 2119, 5 680 tirs).** Aucune tranche de chance évaluée calibrée, et l'ordre est faux : sous 8 m de distance, chance 0,40, buts 0,20 ; de 8 à 12 m, chance 0,12, buts 0,28. Contres : 0,2 % prévus pour 9,9 % observés sous 0,05 de chance prévue, 60 % pour 40 % au-dessus de 0,5. Scène à 11 m face au but : 15 % évalué, 33 % réels ; à 6 m : 37 % évalué, 22 % réels.

**Après (`shooting._flight_shares` : écart du ballon gaussien, cadre, portée du gardien coupée par la ligne au temps de vol, portée de chaque défenseur à sa place à l'arrivée du ballon, but et contre jugés ensemble, écart par écart ; aucune constante nouvelle).**

* Scènes, 2 000 tirs par position, tireur et gardien neutres : 20 positions sur 20 sans défenseur dans l'intervalle à 95 % du taux de buts (écart maximal 1,2 point, `05e-scenes.txt`) ; contres, 7 scènes sur 7 (défenseur dans l'axe, deux qui se cachent, au contact, en course, à 2 m du tireur) ; but avec défenseurs, 6 sur 7 (défenseur à 2 m : 11,2 % contre 13,1 %).
* Matchs (120, graines 2200 à 2319, 5 804 tirs) : chance évaluée moyenne 0,090, buts 0,093. Par tranche de chance évaluée, les 7 tranches calibrées : [0 ; 0,03[ 0,016 / 0,021 ; [0,03 ; 0,06[ 0,043 / 0,052 ; [0,06 ; 0,1[ 0,077 / 0,084 ; [0,1 ; 0,2[ 0,140 / 0,152 ; [0,2 ; 0,35[ 0,256 / 0,231 ; [0,35 ; 0,5[ 0,429 / 0,371 (89 tirs) ; [0,5 ; 1[ 0,758 / 0,712. Distance : 5 tranches sur 6 (12 à 16 m : 0,191 contre 0,146 [0,117 ; 0,180]). Angle : 3 sur 4 (15 à 25° : 0,062 contre 0,071 [0,063 ; 0,080]). Contres : 4 tranches sur 5 (sous 0,05 : 1,5 % prévus, 4,1 % observés).
* Jeu : 48,4 tirs et 4,52 buts par match (avant 47,3 et 4,26), 20,2 % de tirs contrés (18,5 %), distance moyenne 21,4 m (20,8 m). Le tir vaut désormais ce que donne la physique du moteur, plus généreuse que le réel (environ 23 % à 15 m), face aux passes valorisées sur la grille réelle (xT) : réglage du volume et de la conversion au 22c, aucun ici. Temps de calcul inchangé (86,7 min pour 120 matchs sur 7 processus, 88,1 avant).
* Déterminisme : 3 matchs (2200 à 2202) joués deux fois, mêmes 136 tirs, même empreinte (`72d464c777a8`), identiques aux mêmes matchs de la série.

**Reste à faire.** Courbe du 06c sur 500 matchs (§20) non relancée dans ce ticket (environ 7 h de machine) ; le contrôle sur 120 matchs ci-dessus porte sur la même chance (l'xG neutre en est la version à notes neutres).

## 22. Validation des tirs : trajectoire, cadrage, contres, arrêts (ticket v2-realisme/05g, 50 matchs et scènes, 10/11/2026)

Commande : `scripts/shot_calibration.py rapport` sur 50 matchs (graines 2400 à 2449, 2 383 tirs, moteur avec la réserve A1 du 05d). Fichiers `.scratch/v2-realisme/mesures/05g-*`. Aucun réglage.

**Issues par distance (part des tirs).**

| Distance | Tirs | But | Arrêté | À côté | Au-dessus | Dévissé | Contré |
|---|---|---|---|---|---|---|---|
| 0 à 8 m | 92 | 0,337 | 0,130 | 0,163 | 0,022 | 0,000 | 0,348 |
| 8 à 12 m | 108 | 0,231 | 0,241 | 0,102 | 0,176 | 0,009 | 0,241 |
| 12 à 16 m | 232 | 0,207 | 0,211 | 0,228 | 0,151 | 0,017 | 0,185 |
| 16 à 20 m | 337 | 0,107 | 0,187 | 0,344 | 0,139 | 0,021 | 0,202 |
| 20 à 25 m | 830 | 0,049 | 0,193 | 0,398 | 0,139 | 0,027 | 0,195 |
| 25 à 30 m | 784 | 0,031 | 0,168 | 0,422 | 0,128 | 0,042 | 0,209 |

Conversion décroissante avec la distance, sans exception. Par angle sous lequel le tireur voit le but : buts 0,035 (sous 15°), 0,061 (15 à 25°), 0,242 (25 à 40°), 0,325 (au-delà), croissants.

**Cadrage par note (tirs non contrés ni dévissés).** En match, l'effet de la note est noyé : Finishing (surface) 0,667 [0,53 ; 0,78] sous 55 (54 tirs), 0,439 [0,36 ; 0,52] de 55 à 70, 0,500 [0,44 ; 0,56] à 70 et plus ; Long Shots (dehors) 0,302, 0,296, 0,319. Distance, angle et pression moyens identiques d'une tranche à l'autre ; le cadrage prévu tir par tir (écart du ballon, géométrie, pression) ne varie que de 0,521 à 0,547 dans la surface et de 0,314 à 0,333 dehors : environ 3 points entre tranches, sous le bruit de 50 matchs. **Scène de référence** (position fixe, 2 000 tirs, gardien neutre, `05g-scenes-note.txt`) : à 14 m face au but, 0,398 (note 25), 0,563 (60), 0,694 (95) ; à 24 m, 0,243, 0,344, 0,432, intervalles disjoints. Le mécanisme agit ; son poids en match est faible : `duel_probability` cubique et exposant 0,5 de l'exécution (28a) donnent un coefficient de 0,979 à la note 45 et 1,049 à 80, soit ± 3,5 % sur l'écart du ballon (calcul de l'expert). **Critère du ticket non tenu en match**, écart consigné. L'inversion entre [40 ; 55[ (0,681, 47 tirs) et [55 ; 70[ (0,439, 139 tirs), z ≈ 2,9, dépasse l'effet prévu : fluctuation probable, à revérifier sur un échantillon plus grand. Sensibilité des attributs de tir (constante produit) à décider avec le propriétaire au 22c.

**Contres selon les défenseurs dans le cône au départ.** 0 : 0,076 [0,060 ; 0,095] (909 tirs : défenseurs qui entrent dans la trajectoire) ; 1 : 0,280 ; 2 : 0,388 ; 3 et plus : 0,50 (10 tirs). Croissant.

**Arrêts des tirs cadrés selon la vitesse au gardien.** Sous 20 m/s : 0,911 ; 20 à 24 : 0,816 ; 24 à 27 : 0,527 ; 27 et plus : 0,370. Décroissant.

**Écarts au réel (repères du 01c), listés sans réglage (22c).** 23,8 tirs par équipe (repère 8 à 15) ; conversion 8,6 % (10 à 11 %) ; 27,2 % de cadrés (environ 33 %) ; 68,3 % des cadrés arrêtés (environ 70 %) ; 20,8 % de contrés (20 à 28 %) ; 2,8 % de dévissés ; 6,3 corners par match (environ 10) ; 4,1 buts par match.

**Corners et contres (réserve A2 du 05d).** Suite directe d'un tir contré (remise en jeu dans les 5 s, dernier toucheur défenseur) : corner 25,9 %, touche 13,3 %, sortie de but 0,4 %, en jeu 60,4 %. Corners par match : 6,3, dont 2,56 après un contre et 0,94 après un tir claqué. Selon l'angle de sortie du contre : vers l'avant (moins de 30°), 71 % de corners ; de 30 à 90°, 43 % ; renvoyé vers le tireur (plus de 90°, 53 % des contres), 7 % de corners et 85 % en jeu. **Cause** : la déviation à plat (`possession.deflect`, 05d) renvoie la moitié des contres vers le tireur ; ni le ballon contré qui monte au-dessus de la barre (hauteur, `v2-hauteur-ballon/02a`) ni l'orientation de la jambe et du corps (`v2-realisme/07a`) n'existent. Traitement à ces tickets, aucun recalage compensatoire.

**Biais de 12 à 16 m (réserve A1 du 05e).** Par distance : contre prévu contre observé, chance hors contre contre buts des non contrés, écart moyen au gardien :

| Distance | Contre prévu | Contrés | Chance hors contre | Buts des non contrés | Écart au gardien (m) |
|---|---|---|---|---|---|
| 0 à 8 m | 0,190 | 0,348 | 0,528 | 0,517 | 1,81 |
| 8 à 12 m | 0,176 | 0,241 | 0,327 | 0,305 | 1,23 |
| 12 à 16 m | 0,162 | 0,185 | 0,227 | 0,254 | 1,23 |
| 16 à 20 m | 0,194 | 0,202 | 0,126 | 0,134 | 1,38 |
| 20 à 25 m | 0,198 | 0,195 | 0,064 | 0,061 | 1,24 |
| 25 à 30 m | 0,182 | 0,209 | 0,028 | 0,039 | 1,33 |

Sur ces 50 matchs, la tranche de 12 à 16 m n'est plus surévaluée (chance de but évaluée environ 0,19, buts 0,207) : l'écart du 05e (0,191 contre 0,146 sur 494 tirs) n'est pas reproduit, il relevait de l'échantillon. L'étage le plus faux est le contre près du but : 0,19 prévu contre 0,35 observé sous 8 m (défenseurs qui arrivent au contact, gardien et défenseurs en mouvement autour du tireur) ; le tir non contré reste juste à toutes les distances (écart au plus 0,03).

**Scènes de référence rejouées.** Grille du 05e, 2 000 tirs par position (`05g-scenes.txt`) : 20 positions sur 20 dans l'intervalle à 95 %.

**Réserve A1 du 05d.** Contre : point de contact et déviation pris à la place du défenseur au contact (`match._blocked`) ; défenseur qui traverse l'axe à 5 m/s : ballon dévié du côté du décalage au contact (test, au moins 36 cas sur 40 ; échoue sans la correction).

**Déterminisme.** 3 matchs (2400 à 2402) joués deux fois : mêmes 130 tirs, empreinte `664a9a991c15`, identiques à la série.

## 23. Rendement selon la minute : ce que la fatigue change aujourd'hui (ticket v2-realisme/19d, 50 matchs et scène A/B, 10/11/2026)

Commande : `scripts/bench_series.py 50 --processus 7` (graines de `measure_v2`, matchs 0 à 49), clé « rendement par tranche de 15 min » ; module `scripts/v2_tranches.py`. Fichiers `.scratch/v2-realisme/mesures/19d-det1.*` et `19d-det2.*`. Mesure seule, aucun réglage.

**Définitions.** Tranches de 15 minutes de **temps de jeu écoulé** (horloge du moteur) : 0-15 à 75-90, puis « 90 et plus » (temps additionnel de la seconde période). Le temps additionnel de la première période tombe dans la tranche 45-60. **Correctif du 11/11/2026 (réserve A1 de l'expert)** : l'horloge du moteur n'est pas le temps joué ; avec 2 à 3 minutes de temps additionnel en première période, la tranche « 75-90 » couvre environ les minutes jouées 72,5 à 87,5 et « 90 et plus » commence vers la 87e minute jouée : la baisse de fin de match est un peu sous-estimée. Découpage au temps joué : fait au ticket 19f, chiffres de la section 23 ter, qui remplacent ceux de cette section et de la 23 bis pour toute comparaison au réel. Course : joueurs de champ, distance par joueur et par minute (m/min, ce qui neutralise la durée inégale des tranches), part de la distance au-dessus de 19,8 et de 25 km/h, sprints (au moins 1 s au-dessus de 25 km/h, comptés dans la tranche où ils commencent) par joueur et par 15 min. Technique : passes reçues par le receveur visé, contrôles ratés (`contrôle raté` du journal 19b) pour 100 passes, tirs cadrés (but, capté, repoussé, claqué) parmi les tirs non contrés. Duels : tacles gagnés sur tacles tentés. Hauteur du bloc sans ballon (même mesure que la section 1). Comparaison de la première et de la dernière tranche réglementaire (0-15 et 75-90) par poste et par tranche de Stamina (0-40, 40-55, 55-70, 70 et plus).

**Par tranche (50 matchs).**

| Tranche | m/min | > 19,8 km/h | > 25 km/h | Sprints / 15 min | Passes réussies | Contrôles ratés / 100 passes | Cadrés | Tacles gagnés | Bloc (m) | Tirs / match | Buts / match |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-15 | 139,0 | 0,379 | 0,170 | 20,1 | 0,710 | 6,5 | 0,311 | 0,250 | 31,3 | 7,46 | 0,74 |
| 15-30 | 143,5 | 0,388 | 0,175 | 21,1 | 0,708 | 6,5 | 0,361 | 0,283 | 31,8 | 7,42 | 0,74 |
| 30-45 | 138,3 | 0,374 | 0,167 | 19,7 | 0,716 | 6,7 | 0,348 | 0,267 | 32,0 | 7,04 | 0,66 |
| 45-60 | 143,2 | 0,386 | 0,175 | 21,3 | 0,707 | 6,2 | 0,340 | 0,236 | 31,4 | 7,60 | 0,68 |
| 60-75 | 142,5 | 0,379 | 0,166 | 20,1 | 0,708 | 6,8 | 0,331 | 0,273 | 31,7 | 6,84 | 0,62 |
| 75-90 | 138,4 | 0,348 | 0,123 | 14,6 | 0,700 | 6,8 | 0,374 | 0,252 | 31,9 | 6,80 | 0,84 |
| 90 et plus | 131,4 | 0,309 | 0,076 | 8,7 | 0,722 | 7,5 | 0,357 | 0,306 | 31,9 | 5,38 | 0,52 |

**Par Stamina (0-15 contre 75-90).**

| Stamina | m/min 0-15 | m/min 75-90 | Rapport | > 19,8 km/h 0-15 (m/min) | > 19,8 km/h 75-90 (m/min) | Rapport |
|---|---|---|---|---|---|---|
| 0-40 | 111,3 | 112,0 | 1,01 | 36,9 | 27,1 | 0,73 |
| 40-55 | 133,7 | 133,2 | 1,00 | 45,5 | 35,6 | 0,78 |
| 55-70 | 137,1 | 136,2 | 0,99 | 52,3 | 46,3 | 0,89 |
| 70 et plus | 141,0 | 140,7 | 1,00 | 53,5 | 50,5 | 0,94 |

Par poste, la distance totale de la tranche 75-90 vaut 0,98 à 1,01 fois celle de la tranche 0-15 ; la course au-dessus de 19,8 km/h vaut 0,87 (MOC, AG) à 0,95 (MDC). Tous les autres indicateurs par poste, par Stamina et par joueur : section 23 bis.

**Constat : ce que la fatigue change.** Seule la course rapide baisse, et seulement en fin de match : de la tranche 0-15 à la tranche 75-90, la part au-dessus de 25 km/h passe de 0,170 à 0,123 (− 28 %) et les sprints de 20,1 à 14,6 par joueur et par 15 min (− 27 %), la part au-dessus de 19,8 km/h de 0,379 à 0,348 (− 8 %). La baisse suit la note de Stamina (course au-dessus de 19,8 km/h × 0,73 sous 40, × 0,94 à 70 et plus) : c'est le seul effet de `movement.stamina_factor`, qui abaisse la vitesse maximale à partir d'une minute qui dépend de Stamina. Les quatre premières tranches sont plates (aucune baisse avant la 75e).

**Ce qu'elle ne change pas.** La distance totale par minute est plate à toutes les notes (rapport 0,99 à 1,01) : le joueur fatigué ne court pas moins, il court moins vite, la course rapide perdue devient de la course modérée. La technique et les décisions sont plates : passes réussies 0,700 à 0,722, contrôles ratés 6,2 à 7,5 pour 100 passes, cadrage 0,31 à 0,37 et tacles gagnés 0,24 à 0,31 sans tendance (écarts dans le bruit de 50 matchs, environ 300 tirs non contrés par tranche), hauteur du bloc 31,3 à 32,0 m. Les buts n'augmentent pas en fin de match de façon nette (0,84 contre 0,62 à 0,74, dans le bruit). Hypothèse de l'audit confirmée : seules les grandeurs de course baissent.

**Scène A/B** (`tests/test_v2_tranches.py`, graine 19) : le même milieu balle au pied, sans adversaire devant lui, parcourt 18,8 m en 4 s à la 15e minute quel que soit son Stamina ; à la 85e, 15,2 m (Stamina 20), 15,6 m (60), 18,3 m (99). Sa probabilité de passe vers le même coéquipier est identique aux deux minutes (0,720) : `pass_success_probability` ne lit ni la minute ni la condition (`condition.effective_rating` rend la note intrinsèque, 19a).

**Suites.** Fatigue de la technique (20a), de la lucidité (20b), récupération (20c), intensité selon le rôle (12d), réserve d'énergie (12e) : ce tableau sert de point de départ ; validation fatigue et remplacements au 20d. Écarts au réel à confronter aux repères du 01c au 18a, sans réglage ici.

**Déterminisme.** Série de 50 matchs jouée deux fois : 1 918 valeurs identiques, seul le temps de calcul par match diffère. Jeu inchangé : aucun fichier du moteur (`v2engine/`) modifié, le banc ne fait que lire.

### 23 bis. Par poste, par Stamina et par joueur : tous les indicateurs (11/11/2026, reprise après le refus du contrôle qualité)

Le premier passage ne découpait par poste et par Stamina que la course ; passes, contrôles, cadrage, duels, sprints, position sans ballon et buts n'étaient que globaux, rien n'était donné par joueur, et les buts marqués et encaissés étaient confondus. Chaque événement est désormais attribué à son auteur, donc à son poste, à sa tranche de Stamina et à lui-même : passe au passeur, contrôle raté et passe visée au receveur, tir au tireur, tacle au tacleur, but personnel au buteur du journal (19b). Commande : `scripts/bench_series.py 50 --processus 6`, clés « rendement par tranche de 15 min » (postes et Stamina, toutes les tranches) et « rendement par joueur (tranches de 15 min) » (chaque joueur, chaque tranche, puis la synthèse). Fichiers `.scratch/v2-realisme/mesures/19d-v2-det1.*` (50 matchs) et `19d-v2-det2.*` (10 matchs).

**Définitions ajoutées.** Contrôles ratés pour 100 **passes visées** (le receveur est l'auteur, au lieu de 100 passes de tous). Tirs, buts personnels, buts **marqués** et **encaissés** par l'équipe du joueur **pendant qu'il est sur le terrain** : pour 90 minutes jouées par le groupe (temps cumulé de ses joueurs). Pour « tous », un but compte une fois par match, comme avant. **Position sans ballon** : distance moyenne du joueur à son propre but quand son équipe n'a pas le ballon. C'est la mesure individuelle qui remplace la hauteur du bloc, une grandeur d'équipe qui n'a pas de sens par joueur ni par poste et reste donnée par tranche pour l'équipe. Par joueur : les 180 joueurs des 50 matchs ont tous joué au moins 5 minutes dans chacune des deux tranches comparées et entrent dans la synthèse, qui donne les déciles de leurs écarts. Deux joueurs de même nom dans deux clubs seraient confondus : aucun cas dans ces 50 matchs (180 noms pour 180 joueurs).

**Par poste, 0-15 → 75-90 (50 matchs).**

| Poste | Passes réussies | Contrôles ratés / 100 visées | Cadrés | Tacles gagnés | Position sans ballon (m) | Sprints / 15 min | > 25 km/h (m/min) | Buts marqués / 90 | Buts encaissés / 90 |
|---|---|---|---|---|---|---|---|---|---|
| DC | 0,80 → 0,77 | 16,2 → 23,5 | — | 0,24 → 0,30 | 32,0 → 32,1 | 27,1 → 19,9 | 29,8 → 21,6 | 2,35 → 2,64 | 2,04 → 2,35 |
| LB | 0,73 → 0,73 | 7,4 → 6,8 | 0,17 → 0,33 | 0,20 → 0,20 | 36,4 → 37,5 | 13,7 → 10,3 | 16,7 → 12,3 | 2,30 → 2,55 | 2,23 → 2,62 |
| RB | 0,77 → 0,79 | 6,3 → 5,0 | 0,33 → 0 | 0,32 → 0,50 | 36,4 → 37,2 | 16,1 → 12,0 | 19,7 → 14,1 | 2,08 → 2,40 | 2,27 → 2,53 |
| MDC | 0,80 → 0,75 | 14,5 → 10,5 | 0,25 → 0,50 | 0,36 → 0,33 | 41,0 → 41,0 | 22,9 → 18,6 | 27,0 → 22,0 | 3,00 → 2,54 | 2,00 → 2,23 |
| MC | 0,74 → 0,75 | 6,3 → 6,4 | 0,62 → 0,60 | 0,39 → 0,23 | 42,6 → 43,6 | 19,2 → 13,9 | 22,5 → 16,1 | 1,72 → 2,45 | 2,79 → 2,90 |
| MOC | 0,68 → 0,69 | 4,9 → 5,1 | 0,16 → 0,30 | 0,26 → 0,31 | 53,8 → 53,7 | 17,3 → 11,4 | 20,4 → 13,5 | 2,18 → 2,27 | 1,91 → 2,45 |
| AG | 0,64 → 0,60 | 2,9 → 6,0 | 0,47 → 0,29 | 0,16 → 0,32 | 54,4 → 54,8 | 16,3 → 10,5 | 20,3 → 12,9 | 2,22 → 2,49 | 1,96 → 2,36 |
| AD | 0,61 → 0,62 | 6,2 → 6,3 | 0,11 → 0,47 | 0,13 → 0,27 | 53,9 → 53,9 | 16,4 → 11,3 | 20,0 → 13,7 | 2,32 → 2,80 | 2,05 → 2,66 |
| BU | 0,64 → 0,64 | 3,9 → 2,4 | 0,31 → 0,37 | 0,22 → 0,17 | 63,0 → 63,7 | 21,6 → 15,7 | 27,3 → 19,5 | 2,09 → 2,38 | 2,43 → 2,49 |

Effectifs par poste : DC 41 joueurs, MC 28, BU 19, LB 17, RB 17, AG 16, AD 16, MDC 14, MOC 12. Les buts sont des buts d'équipe pour 90 minutes jouées : chaque poste en voit autant, à l'aléa près (environ 0,7 but par match et par tranche).

**Par Stamina, 0-15 → 75-90.** Effectifs : 102 joueurs à 70 et plus, 71 de 55 à 70, 6 de 40 à 55 et **un seul sous 40** (sa ligne est un cas, pas une moyenne).

| Stamina | Passes réussies | Contrôles ratés / 100 visées | Tacles gagnés | Position sans ballon (m) | Sprints, 75-90 / 0-15 | > 25 km/h, 75-90 / 0-15 |
|---|---|---|---|---|---|---|
| 0-40 (1 joueur) | 0,64 → 0,50 | 33 → 59 | 0 → 0,33 | 40,6 → 42,5 | 0,16 | 0,21 |
| 40-55 (6) | 0,63 → 0,63 | 27 → 30 | 0,50 → 0,13 | 45,9 → 46,4 | 0,42 | 0,38 |
| 55-70 (71) | 0,70 → 0,67 | 8,2 → 7,4 | 0,24 → 0,21 | 42,5 → 43,5 | 0,64 | 0,64 |
| 70 et plus (102) | 0,71 → 0,71 | 3,9 → 4,2 | 0,24 → 0,28 | 44,8 → 44,8 | 0,81 | 0,80 |

**Par joueur (180 joueurs, déciles de l'écart entre 0-15 et 75-90).** Sprints : rapport médian 0,73 (1er décile 0,45, 9e décile 0,95) ; course au-dessus de 25 km/h : 0,73 (0,46 ; 0,92) ; au-dessus de 19,8 km/h : 0,92 (0,79 ; 1,04) ; distance totale : 0,995 (0,94 ; 1,06). La baisse des sprints suit Stamina (corrélation 0,67 sur 180 joueurs). Passes réussies : écart médian − 0,007 (− 0,20 ; + 0,13) ; contrôles ratés pour 100 passes visées : 0 (− 11 ; + 13) ; position sans ballon : + 1,6 m (− 5,6 ; + 5,0) ; tirs pour 90 min : 0 (− 2,4 ; + 1,2). Tacles gagnés et cadrage n'ont un écart que pour 95 et 46 joueurs (les autres n'ont ni tacle ni tir non contré dans l'une des deux tranches), centré sur 0.

**Constat (inchangé, maintenant par poste et par joueur).** À chaque poste et pour la médiane des joueurs, seule la course rapide baisse en fin de match : sprints de − 19 % (MDC) à − 36 % (AG), avec une baisse d'autant plus forte que Stamina est bas. La technique, les duels et la position sans ballon n'ont pas de tendance commune : les écarts par poste partent dans les deux sens (cadrage des AD 0,11 → 0,47, des RB 0,33 → 0), sur de petits nombres (une dizaine de tirs non contrés par poste et par tranche), et la médiane des joueurs est à 0. Les contrôles ratés des DC (16 → 24 pour 100 passes visées) sont le plus grand écart de technique, mais la même mesure baisse chez les MDC (15 → 11) et les RB (6,3 → 5,0), signe de bruit plutôt que de fatigue, puisque le moteur ne relie pas la technique à la minute (scène A/B). **Réserve A2 de l'expert (11/11/2026)** : le numérateur compte tout contact raté, interceptions manquées comprises, et le dénominateur les seules passes de son équipe qui visent le joueur ; le niveau des défenseurs (DC 16, contre 3,9 pour les BU) vient de leurs tentatives d'interception, pas d'un contrôle quatre fois moins bon. Seule la comparaison d'une tranche à l'autre dans un même groupe vaut. Dénominateur par tentative de contrôle : ticket 19f. Les buts marqués et encaissés montent un peu en fin de match à tous les postes (environ + 0,3 pour 90 min), dans le bruit de la tranche (0,84 contre 0,62 à 0,74 but par match). Les chiffres « tous joueurs » du tableau précédent sont identiques au premier passage : le jeu n'a pas changé.

**Déterminisme.** Les 10 premiers matchs rejoués à part (`19d-v2-det2.json`) : 21 730 valeurs par match identiques à celles de la série de 50 matchs. Les 77 chiffres « tous joueurs » du premier passage (`19d-det1.json`) sont identiques ; les autres clés ont été renommées (par groupe et par tranche).

### 23 ter. Au temps joué, contrôles par passe visée (ticket v2-realisme/19f, 50 matchs, 11/11/2026)

Réserves de l'expert sur le 19d et le 19e, acceptées par le propriétaire. Commande et graines inchangées (`scripts/bench_series.py 50 --processus 6`) ; fichiers `.scratch/v2-realisme/mesures/19f-det1.*` (50 matchs) et `19f-det2.*` (10 matchs). Lecture seule : aucun fichier `v2engine/` modifié.

**Ce qui change dans la mesure.**
- **Temps joué.** Les tranches suivent `played_minute` (`v2engine/added_time.py`), comme la fatigue : la seconde période commence au début de la tranche 45-60 quelle que soit la durée du temps additionnel de la première, qui a sa propre tranche « 45 et plus ». « 75-90 » couvre les minutes jouées 75 à 90 et « 90 et plus » le seul temps additionnel de la seconde période. La hauteur du bloc suit le même découpage (elle était découpée à part, à l'horloge).
- **Contrôles.** Un contrôle raté n'est compté comme tel que sur une passe ou une remise de son équipe qui vise le joueur (« contrôles ratés pour 100 passes visées », par groupe ; « pour 100 passes », tous joueurs). Tout autre contact raté (interception manquée, ballon libre, passe qui visait un coéquipier) est compté à part : « autres contacts ratés » pour 90 minutes (par groupe) ou par match (tous joueurs).
- **Buts personnels.** Un but contre son camp n'est plus le but personnel du dernier toucheur adverse.

**Par tranche, tous joueurs (50 matchs).**

| Tranche | m/min | > 19,8 km/h | > 25 km/h | Sprints / 15 min | Passes réussies | Contrôles ratés / 100 passes | Autres contacts ratés / match | Cadrés | Tacles gagnés | Bloc (m) | Tirs / match | Buts / match |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-15 | 139,0 | 0,379 | 0,170 | 20,1 | 0,710 | 3,1 | 4,2 | 0,311 | 0,250 | 31,3 | 7,46 | 0,74 |
| 15-30 | 143,5 | 0,388 | 0,175 | 21,1 | 0,708 | 3,4 | 4,0 | 0,361 | 0,283 | 31,8 | 7,42 | 0,74 |
| 30-45 | 138,3 | 0,374 | 0,167 | 19,7 | 0,716 | 3,2 | 4,4 | 0,348 | 0,267 | 32,0 | 7,04 | 0,66 |
| 45 et plus | 140,5 | 0,382 | 0,172 | 20,5 | 0,713 | 4,2 | 1,0 | 0,302 | 0,254 | 31,9 | 2,16 | 0,12 |
| 45-60 | 143,8 | 0,384 | 0,173 | 21,3 | 0,706 | 2,8 | 4,4 | 0,354 | 0,229 | 31,3 | 7,08 | 0,76 |
| 60-75 | 141,8 | 0,376 | 0,161 | 19,3 | 0,705 | 3,1 | 4,5 | 0,331 | 0,292 | 32,1 | 6,88 | 0,56 |
| 75-90 | 137,1 | 0,336 | 0,107 | 12,8 | 0,702 | 3,5 | 4,5 | 0,387 | 0,262 | 31,6 | 6,98 | 0,92 |
| 90 et plus | 129,2 | 0,304 | 0,071 | 7,8 | 0,732 | 3,7 | 1,9 | 0,336 | 0,284 | 32,1 | 3,52 | 0,30 |

Les tranches « 45 et plus » et « 90 et plus » sont courtes : leurs tirs et buts par match ne se comparent pas aux autres (les grandeurs par minute ou en part, oui).

**Horloge contre temps joué : la baisse de fin de match était sous-estimée.** De 0-15 à 75-90, les sprints passent de 20,1 à 12,8 par joueur et par 15 min (− 36 %, contre − 27 % à l'horloge) et la part au-dessus de 25 km/h de 0,170 à 0,107 (− 37 %, contre − 28 %) ; la part au-dessus de 19,8 km/h baisse de 11 % (contre 8 %). La distance totale par minute baisse à peine (139,0 → 137,1). Les tranches 0-15 à 30-45 sont identiques aux chiffres de l'horloge (seule la seconde période change de découpage).

**Par poste, 0-15 → 75-90.**

| Poste | Sprints, 75-90 / 0-15 | Contrôles ratés / 100 passes visées | Autres contacts ratés / 90 min |
|---|---|---|---|
| DC | 0,63 | 4,2 → 6,7 | 1,4 → 1,7 |
| LB | 0,65 | 4,1 → 3,3 | 0,6 → 0,8 |
| RB | 0,65 | 2,0 → 3,1 | 0,7 → 0,3 |
| MDC | 0,73 | 5,7 → 4,7 | 2,2 → 1,5 |
| MC | 0,64 | 4,0 → 4,0 | 1,0 → 1,5 |
| MOC | 0,57 | 1,7 → 3,6 | 2,4 → 2,0 |
| AG | 0,57 | 2,0 → 3,7 | 0,4 → 1,3 |
| AD | 0,60 | 3,9 → 3,5 | 1,1 → 1,6 |
| BU | 0,64 | 1,9 → 1,3 | 1,7 → 0,9 |

Séparés des contacts sur ballon adverse, les contrôles ratés des défenseurs reviennent au niveau des autres postes (DC 4,2 pour 100 passes visées en 0-15, contre 16,2 avec les interceptions manquées) : la réserve A2 est levée. Les écarts d'une tranche à l'autre restent sans tendance commune (DC et AG montent, MDC, LB et BU baissent), dans le bruit de quelques dizaines de ratés par poste et par tranche.

**Par Stamina, 75-90 / 0-15.** Sprints : 0,09 sous 40 (un joueur), 0,28 de 40 à 55 (6), 0,53 de 55 à 70 (71), 0,73 à 70 et plus (102) ; course au-dessus de 19,8 km/h : 0,67, 0,70, 0,84, 0,91 ; distance totale : 0,98 à 1,01.

**Par joueur (180 joueurs).** Sprints : rapport médian 0,65 (1er décile 0,36, 9e décile 0,86), contre 0,73 à l'horloge ; au-dessus de 19,8 km/h : 0,88 (0,75 ; 1,00) ; distance totale : 0,98 (0,93 ; 1,06). Contrôles ratés pour 100 passes visées et autres contacts ratés : écart médian 0.

**Constat (inchangé dans sa forme, plus net).** Seule la course rapide baisse, à partir de la 75e minute jouée, d'autant plus que Stamina est bas ; technique, duels, position sans ballon et bloc restent plats. Ce sont ces chiffres que le 18a et le 20d comparent au réel.

**Déterminisme.** Les 10 premiers matchs rejoués à part (`19f-det2.json`) : les 2 467 clés par match communes aux deux fichiers ont des valeurs identiques sur ces 10 matchs (les 29 clés de plus de la série de 50 sont des groupes rares absents des 10 premiers matchs).

## 24. Origine des buts : lecture de la chaîne (ticket v2-realisme/19e, 20 matchs, 11/11/2026)

Commande : `uv run python -m scripts.v2_chain 20` (parts par origine) ; `uv run python -m scripts.v2_chain --match 7 --but 0` (chaîne d'un but, exemple dans `.scratch/v2-realisme/mesures/19e-chaine-match7.txt`). Matchs : graines et affiches du banc (`measure_v2`), sans collecteur. Fichiers `.scratch/v2-realisme/mesures/19e-avant.jsonl` et `19e-apres.jsonl`. Lecture seule du journal (19b).

**Définitions.** En remontant la chaîne depuis le but, l'origine est le premier événement qui **donne le ballon** à l'équipe qui marque : remise en jeu de cette équipe, hors-jeu adverse (coup franc indirect, sans événement de remise), perte adverse (tacle, interception, conduite perdue au contact, contrôle raté, touche trop longue), arrêt ou contre de cette équipe sur un tir adverse. Les arrêts et contres adverses (rebond) et la faute adverse laissée en avantage ne rendent pas le ballon : l'attaque continue. Familles : **coup de pied arrêté** (corner, coup franc, coup franc de hors-jeu, penalty), **touche** (à part, pour l'ajouter selon la définition du repère), **jeu placé** (engagement, sortie de but, ou coup de pied arrêté et touche à plus de **15 s** du but, `SET_PIECE_WINDOW_S`), **erreur adverse** (contrôle raté, touche trop longue), **récupération** (interception, conduite perdue, tacle, arrêt, contre), **inclassable** (expliqué). Constantes recommandées et retenues par délégation du propriétaire (11/11/2026).

**Par origine (20 matchs, 108 buts).**

| Famille | Buts | Part | Détail |
|---|---|---|---|
| Récupération | 87 | 80,6 % | interception 52, conduite perdue 28, tacle 6, contre 1 |
| Erreur adverse | 16 | 14,8 % | contrôle raté 10, touche trop longue 6 |
| Jeu placé | 3 | 2,8 % | engagement 2, après touche 1 |
| Touche | 1 | 0,9 % | |
| Coup de pied arrêté | 1 | 0,9 % | corner 1 |
| Inclassable | 0 | 0 % | |

Délai médian entre l'événement d'origine et le but : 3,3 s.

**Repère réel.** Opta Analyst : 23,5 % des buts de Premier League sur toute son histoire viennent de coups de pied arrêtés, **hors penalties** ; la part récente est plus haute (environ 27 % en 2025-2026, selon les définitions). Part des penalties, des touches, des récupérations et du jeu placé : non trouvé (aucune source primaire lue dans ce ticket).

**Constat.** Le moteur produit presque tous ses buts en transition : 95 % viennent d'un ballon gagné à l'adversaire (récupération ou erreur), à 3 s du but en médiane. Les coups de pied arrêtés ne donnent presque rien (1 but sur 108, contre environ 1 sur 4 dans le réel), le jeu placé très peu (3 sur 108). Écart majeur, à attribuer au 18a : corners et coups francs peu dangereux (jeu aérien, 15f et `v2-attributs-restants/01`), attaque placée qui ne finit pas, et pertes de balle très nombreuses (« interception » compte aussi une passe ratée reprise par l'adversaire). Aucun réglage ici.

**Journal corrigé (réserve A1 de l'expert sur le 19b).** La faute laissée en avantage est écrite quand l'avantage est accordé (`match._foul`), plus au règlement ; si l'arbitre revient à la faute, la décision est écrite à sa minute (« coup franc, après avantage »). Sur 20 matchs : minutes du journal croissantes dans 20 matchs (11 avant la correction), aucune faute causée par un but, empreintes du jeu (ticks, buts, tirs, fautes, remises) identiques dans 20 matchs sur 20 : le jeu n'a pas changé. Origines des buts identiques sur les deux exécutions.

**Reprise au 19f (11/11/2026).** La remontée s'arrête aussi sur une perte ou un hors-jeu de l'équipe qui marque (le ballon est alors à l'adversaire ; but inclassable si sa reprise n'est pas écrite) ; `--but` hors limites donne une erreur claire. Sur les mêmes 20 matchs (`.scratch/v2-realisme/mesures/19f-chaine.json`) : 108 buts, parts identiques, aucun inclassable. Invariant du journal (minutes croissantes, aucune faute causée par un but) gardé par un test sur un match court à graine fixée.

## 25. Point d'étape après les fondations P0 (ticket v2-realisme/18a, 50 matchs, 11/11/2026)

Série exploratoire, **aucun réglage**. Moteur à `681d9e0` (dernier changement du jeu : 19e, journal seulement ; jeu identique depuis le 19b). Commande : `scripts/bench_series.py 50 --processus 6` (graine d'audit 20260923, matchs 0 à 49), fichiers `.scratch/v2-realisme/mesures/19f-det1.*` ; déterminisme : les 10 premiers matchs rejoués (`19f-det2.*`) donnent les mêmes valeurs (2 467 clés par match). Origine des buts : `scripts/v2_chain.py 20` (`19f-chaine.json`). Mesure précédente comparable : section 6 (`a9a74f9`, 20 matchs).

**Lecture des attributions.** *Mécanisme* : le moteur ne contient pas encore ce qui produit le comportement réel (une règle manque ou agit à tort) ; une constante ne suffirait pas sans fausser autre chose. *Calibration* : le mécanisme existe et va dans le bon sens, l'écart tient à des constantes (ticket de calibration provisoire 18d ou 18e). Une conséquence d'un autre écart est rattachée à sa cause.

### 25.1 Repères de calibration (section 6)

| # | Repère (réel) | Banc, 50 matchs | Section 6 (20 matchs) | Écart | Attribution |
|---|---|---|---|---|---|
| R1 | Tirs tracés par équipe : 8 à 15 (≈ 13,1) | 24,3 | 37,7 | × 1,85 | **Mixte, volume des transitions** (réserve A2 de l'expert sur le 18a). Sur 48,5 tirs par match, 33,2 partent dans les 15 s d'une récupération dans le camp adverse et 2,7 d'une récupération dans son camp ; 24 % des tirs viennent directement d'une récupération et 56 % d'un dribble. Le porteur choisit la conduite 73 % du temps (passe 26 %), perd le ballon haut, l'adversaire le perd aussi vite : le match est une suite de transitions courtes (2,55 passes par possession, cible 3 à 5). Ce n'est pas d'abord le seuil de tir (xG moyen par tir 0,094, proche du réel) : c'est le nombre de ballons gagnés près du but. Côté calibration : poids de la conduite contre la passe dans le choix du porteur et rythme de décision (18d), puis seuil de tir (18e) ; côté mécanisme : passes en profondeur et longues absentes (`v2-collectif/32a`, 32b). |
| R2 | Conversion : 10 à 12 % | 9,9 % | 5,4 % | − 0,1 point | **Calibration**, presque dans la fourchette depuis les tickets 03 et 05 (gardien, trajectoire, arrêt). xG neutre moyen 0,094 par tir, xG après frappe 0,118 par tir non contré : le tir et le gardien sont cohérents entre eux (06c). Ticket : 18e, sans urgence. |
| R3 | Buts dans la surface : 88 à 89 % | 61 % | 48 % | − 27 points | **Calibration de la valeur du tir dans la décision** (05e) **et de l'exécution de loin** (35b) : 390 des 656 tirs cadrés jugés partent de plus de 18 m (253 de 18 à 25 m, 137 au-delà), 173 de 11 à 18 m et 93 de moins de 11 m. Le mécanisme (chance évaluée alignée sur la résolution, 05e) existe ; la part des tirs de loin reste trop haute. Ticket : 18e. |
| R4 | Distance par joueur de champ : 10 à 12 km, MC en tête | 14,0 km (LB 12,4 à BU 16,6) | 17,4 km | + 2 à + 4,5 km ; ordre des postes faux | **Mécanisme** : hors presseur et repli, chaque intention vise l'intensité 1,0 (vitesse maximale) ; aucun rôle ne trotte. L'avant-centre court le plus (16,6 km, contre 10,3 au réel) parce qu'il enchaîne les appels. Tickets : 12d (intensité selon le rôle), puis 18d. |
| R5 | Appels par joueur et par 90 min : 5 à 20 (15,1) | 41,4 (DC 18 à BU 89) | 22 à 102 | × 2,7 | **Mécanisme** (même cause que R4 : appels au sprint, sans coût) et **définition** (le banc juge l'option par la réception, la source par la chance d'être choisi ; indicatif). L'ordre des postes est le bon (DC bas, BU et MOC hauts). Tickets : 12d, 12e, puis 18d. |
| R6 | Distance au-dessus de 19,8 km/h : 6 à 10 % | 36,9 % (au-dessus de 25 km/h : 15,4 %) | 17,2 % du temps | × 4 | **Mécanisme** (même cause que R4) : la course rapide est le régime par défaut. 4,2 à 6,2 km par joueur au-dessus de 19,8 km/h (réel 0,6 à 1,1 km) ; 123 sprints par joueur et par match. Tickets : 12d, 12e, 18d. |
| R7 | Passes par match : 890 à 940 ; par minute de jeu effectif : 15 à 17 | 844 ; 11,9 | 990 ; 14,9 | − 6 % ; − 25 % | **Mixte** : calibration du choix du porteur (conduite 73 %, 18d) et temps de jeu effectif trop haut (70,8 %, réel 53 à 56 % avec fautes et remplacements, que la V2 n'a pas encore : peu de fautes, aucun remplacement). La réussite est juste (72,7 % de passes réussies, cible 70 à 90 %), les passes longues absentes (1,5 %, cible 10 à 19 %). Tickets : 18d (choix du porteur, rythme de décision) ; mécanisme des passes en profondeur et longues : `v2-collectif/32a` (passes en retrait et en profondeur) et 32b (passe lobée), 14a pour la portée physique du ballon (réserve A1 de l'expert sur le 18a). |

**Lecture d'ensemble.** Les repères de **tir et de gardien** (R2, et en partie R3) sont désormais dans l'ordre de grandeur : les fondations P0 (03, 05, 06) ont fait leur effet (conversion 5,4 → 9,9 %, buts dans la surface 48 → 61 %). Les repères de **course** (R4, R5, R6) sont loin pour une seule raison de mécanisme, l'intensité par défaut, qui relève du 12d avant toute calibration. Le **volume de tirs** (R1) et les **passes** (R7) ont une cause commune : le porteur conduit trop et perd le ballon haut, ce qui fabrique des transitions.

### 25.2 Autres indicateurs (section 1)

| Indicateur | Cible | Banc | Attribution |
|---|---|---|---|
| Buts par match | 2 à 3,5 | 4,8 | Conséquence de R1 (volume de tirs) avec une conversion juste. |
| Tacles par match | 30 à 40 | 43,9 | Conséquence de R1 et R7 (conduites nombreuses, duels nombreux). |
| Fautes par match | 21 à 26,4 | 14,1 | **Calibration** (probabilité de faute par duel du `v2-collectif/30`, livré ; réglage au 18d ou au 18e) ; à revoir après 18d, qui changera le nombre de duels. |
| Penaltys par match | environ 0,34 | 0,02 | **Mécanisme** : presque aucune faute dans la surface (les duels y sont rares, les tirs partent de loin, R3). À relire après 18e. |
| Hors-jeu par match | 3,2 à 3,5 | 0,72 | **Mécanisme** : la passe en profondeur est presque absente (0,4 % des passes) alors que 21,7 appels dans le dos sont faits par match ; le hors-jeu se joue sur la passe, pas sur l'appel. Tickets : `v2-collectif/32a` et 32b (décision de la passe en profondeur et lobée), 18d. |
| Touches ; corners par match | ≈ 42 ; ≈ 10 | 23,7 ; 6,7 | Conséquence de R7 (peu de jeu long, peu de ballons qui sortent). |
| Possession d'équipe ; temps par possession de joueur | 11 à 16 s ; 2 à 3 s | 17,6 s ; 2,9 s | Possession d'équipe au-dessus de la fourchette, temps par joueur dans l'ordre de grandeur ; la possession d'équipe longue vient des conduites (R7). |
| Passes chez l'adversaire | ≤ 25 % | 24,7 % | À la limite. |
| Passes visées vers les défenseurs centraux | non sourcé (ordre de grandeur couramment cité : 40 à 60 passes reçues par match) | environ 2 par DC et par 15 min (216 en 0-15 sur 50 matchs, environ 113 créneaux DC ; constat de l'expert sur le 19f), soit environ 12 par match | **Mécanisme** : la relance passe peu par les DC, cohérent avec la conduite à 73 % (R7) et la possession courte. À relire au 18d avec le choix du porteur ; si l'écart reste, ticket de relance à créer à ce moment. |
| Hauteur du bloc sans ballon | suivi (section 2) | 31,7 m (porteur pressé 37,2 m, libre 43,0 m) | Suivi, sans repère chiffré. |

### 25.3 Condition physique (19d, 19f)

Ce que la fatigue change aujourd'hui (section 23 ter, temps joué) : la seule course rapide, à partir de la 75e minute jouée (sprints − 36 %, distance au-dessus de 25 km/h − 37 % de 0-15 à 75-90 ; rapport médian des sprints par joueur 0,65), d'autant plus que Stamina est bas (sprints × 0,28 de 40 à 55, × 0,73 à 70 et plus). Ce qu'elle ne change pas : la distance totale (rapport 0,98), la technique (passes, contrôles, cadrage), les duels, la position sans ballon et le bloc ; elle ne dépend ni des efforts fournis ni du rôle. Repère de la section 1 (« baisse de fin de match » de la course au-dessus de 19,8 km/h : 10 à 30 %) : − 11 %, dans la fourchette mais pour une mauvaise raison (la baisse suit l'horloge, `movement.stamina_factor`, pas l'énergie dépensée). **Mécanisme** : tickets 12e (réserve d'énergie, qui remplace la baisse par la minute), puis 20a à 20c (technique, lucidité, récupération) ; validation au 20d. Ordre de grandeur à revoir après 12d : avec 37 % de la distance au-dessus de 19,8 km/h, toute réserve d'énergie se viderait trop vite.

### 25.4 Garde probabiliste (19c)

Le test transversal (`tests/test_v2engine_garde_probabiliste.py`) garde 9 résolutions : ni infaillible (plancher 1 %, deux exceptions assumées) ni incapable, hiérarchie des notes respectée. Hors garde, avec leur ticket : arrêt sans note du gardien (03b, la portée physique décide seule), contre sans note du défenseur (17b, Bravery), dosage de la passe et passe ratée (23a, erreur d'exécution continue). Constat à suivre : le contrôle d'un 99 ne sent plus la difficulté (18d). Aucun de ces trous ne cause un écart de la section 25.1 ; ils comptent pour le réalisme d'une action, pas pour les volumes.

### 25.5 Causalité : origine des buts (19e, 19f)

108 buts sur 20 matchs : récupération 81 % (interception 48 %, conduite perdue 26 %, tacle 6 %), erreur adverse 15 %, jeu placé 3 %, coup de pied arrêté 1 %, touche 1 %, aucun inclassable ; 3,3 s en médiane entre l'origine et le but. Repère réel (Opta Analyst, source et définition en section 24) : environ 23,5 % des buts sur coup de pied arrêté hors penalties (Opta, Premier League). **Mécanisme** : le moteur ne travaille pas les coups de pied arrêtés (corners joués long à 91 %, mais aucun duel aérien ni placement offensif sur corner ; aucun coup franc du dernier tiers frappé au but ; 0,02 penalty par match). C'est cohérent avec R1 : tout le danger vient des transitions. Tickets existants : 15b à 15f (jeu aérien), 16a à 16i (coups de pied arrêtés), 16g (validation) ; ils sont P2 et ne changent pas l'ordre ci-dessous, mais la part des buts sur coup de pied arrêté doit entrer dans les critères du 16g (repère : environ 23,5 %).

### 25.6 Tickets à avancer ou à créer, et ordre confirmé

- **Ordre confirmé : 12d → 12e → 18d → 18e.** La plus grande famille d'écarts (R4, R5, R6) a une cause de mécanisme unique, l'intensité par défaut : le 12d la traite ; le 12e ne se règle qu'avec des intensités réalistes ; le 18d (course, rythme, passes) ne se calibre qu'après les deux ; le 18e (tirs, gardien) après le 18d, qui changera le nombre de transitions donc de tirs.
- **À inclure au 18d** : le choix du porteur (part des conduites, 73 %) et le rythme de décision, cause commune de R1 et R7 ; relire tacles, fautes et possession après réglage.
- **À inclure au 18e** : part des tirs de loin (R3) ; penaltys (0,02 par match) relus après 18d.
- **À rapprocher** : `v2-collectif/32a` et 32b (passes en profondeur et lobées : passes longues 1,5 %, passes en profondeur 0,4 %, hors-jeu 0,72 par match), après 18d ; 14a pour la portée physique.
- **À compléter** : critère du 16g (part des buts sur coup de pied arrêté, repère environ 23,5 %).
- **Aucun ticket nouveau aujourd'hui** : chaque écart a un ticket qui le traite ; seule la relance par les DC pourrait en demander un, après le 18d.

## 26. Intensité de course selon le rôle (ticket v2-realisme/12d, 50 matchs, 11/11/2026)

Commande : `scripts/bench_series.py 50 --processus 6`, fichiers `.scratch/v2-realisme/mesures/12d-det1.*` (après) contre `19f-det1.*` (avant, mêmes graines). Constantes recommandées et retenues par délégation du propriétaire (ticket 12d) : rejoindre sa place en possession au trot (0,40 de la vitesse max, Work Rate 0,32 → 0,48), sans ballon en course (0,55, Work Rate 0,45 → 0,65) ; appel vers un espace libre en course rapide (0,75, Off the Ball 0,65 → 0,85) ; appel dans la profondeur ou de contre-attaque au sprint ; pressing, repli, réception, interception, ballon libre et marquage inchangés. Code : `defense.replacement_intensity`, `off_ball.run_intensity`, appelés par `cerveau.decide`.

| Indicateur | Avant | Après | Repère |
|---|---|---|---|
| Distance par joueur de champ (km) | 14,0 | 12,5 | 10 à 12 (R4) |
| Distance au-dessus de 19,8 km/h (part) | 36,9 % | 15,6 % | 6 à 10 % (R6) |
| Distance au-dessus de 25 km/h (part) | 15,4 % | 5,4 % | suivi |
| Sprints par joueur et par match | 122,9 | 38,6 | suivi |
| Appels par joueur et par 90 min | 41,4 | 24,0 | 5 à 20, 15,1 en moyenne (R5, indicatif) |
| Passes par match ; par minute de jeu effectif | 844 ; 11,9 | 894 ; 12,4 | 890 à 940 ; 15 à 17 (R7) |
| Tirs tracés par équipe | 24,3 | 23,3 | 8 à 15 (R1) |
| Buts par match | 4,8 | 3,6 | 2 à 3,5 |
| Conversion ; buts dans la surface | 9,9 % ; 61 % | 7,8 % ; 64 % | 10 à 12 % ; 88 à 89 % |
| xG neutre moyen par tir | 0,094 | 0,083 | environ 0,10 |
| Tacles ; fautes par match | 43,9 ; 14,1 | 46,5 ; 14,9 | 30 à 40 ; 21 à 26 |
| Hauteur du bloc sans ballon (m) ; défense-milieu ; milieu-attaque | 31,7 ; 15,4 ; 16,1 | 31,5 ; 15,5 ; 16,0 | suivi |

**Par poste (km ; m au-dessus de 19,8 km/h ; appels par 90 min après).** DC 13,5 → 11,3 ; 5 529 → 890 ; 3,2. LB 12,4 → 10,9 ; 4 164 → 1 127 ; 7,7. RB 12,4 → 10,9 ; 4 358 → 1 115 ; 7,0. MDC 14,4 → 12,5 ; 5 572 → 1 753 ; 8,3. MC 13,9 → 12,4 ; 5 134 → 1 947 ; 20,3. MOC 15,2 → 14,0 ; 5 243 → 2 949 ; 53,5. AG 14,4 → 13,4 ; 4 971 → 2 719 ; 36,6. AD 14,5 → 13,5 ; 4 953 → 2 849 ; 36,6. BU 16,6 → 15,5 ; 6 187 → 3 907 ; 75,8. Repère réel au-dessus de 19,8 km/h : 586 à 1 113 m par poste (section 6, R6).

**Constat.** Le régime par défaut n'est plus le sprint : la course rapide est divisée par 2,4, les sprints par 3,2, les défenseurs reviennent dans l'ordre de grandeur réel (DC 890 m au-dessus de 19,8 km/h, latéraux 1 100 m). Le bloc garde sa compacité (distances entre lignes inchangées), les passes se rapprochent du repère (894 par match) et les buts reviennent dans la fourchette haute (3,6). Restent hors repère : la course rapide des joueurs offensifs (MOC, ailiers, avant-centre : 2,7 à 3,9 km au-dessus de 19,8 km/h), portée par les appels (BU 76, MOC 54 par 90 min) et par les rôles laissés à pleine intensité (réception, ballon libre, interception, marquage, pressing) ; l'ordre des postes en distance totale reste inversé (BU en tête, MC au réel). C'est la matière de la calibration provisoire 18d (volume d'appels, intensités dans leurs fourchettes), pas un mécanisme manquant. La conversion baisse (7,8 %, xG moyen 0,083) : moins de transitions au sprint, occasions un peu moins franches ; à relire au 18e.

**Fin de match (temps joué, tous joueurs).** Distance au-dessus de 19,8 km/h : 0,163 (0-15) → 0,131 (75-90), − 20 % (repère 10 à 30 %) ; sprints 6,3 → 3,6 par 15 min ; rapport médian par joueur de la course au-dessus de 19,8 km/h 0,76 (1er décile 0,55, 9e décile 1,01) ; par Stamina 0,49 (40 à 55), 0,68 (55 à 70), 0,83 (70 et plus). La baisse vient toujours de `movement.stamina_factor` (la minute), pas de l'effort : ticket 12e.

**Scène A/B du 19d (section 23), adaptée.** Le milieu balle au pied passe vers 2,5 s ; après sa passe il court à l'intensité de son nouveau rôle, que la scène ne compare pas. La mesure porte désormais sur 2 s de conduite : 7,6 m à la 15e, 5,3 m à la 85e pour Stamina 20, 7,4 m pour Stamina 99, probabilité de passe identique (0,72).

**Déterminisme.** Les 10 premiers matchs rejoués (`12d-det2.json`) : 2 444 clés par match communes, valeurs identiques. Rayon des attributs : Work Rate lu dans `defense.py`, Off the Ball dans `off_ball.py`, comme avant (`tests/test_v2engine_rayon_attributs.py` inchangé et vert) ; `docs/CARTE_ATTRIBUTS_V2.md` mis à jour.

## 27. Réserve d'énergie (ticket v2-realisme/12e, 50 matchs, 11/11/2026)

Commande : `scripts/bench_series.py 50 --processus 6`, fichiers `.scratch/v2-realisme/mesures/12e-det1.*` (après) contre `12d-det1.*` (avant, mêmes graines) ; premier réglage écarté : `12e-r1-det1.*`. Modèle et constantes : ticket 12e (`movement.spend_energy`, `energy_factor`, `PlayerCondition.energy`) ; la réserve se vide par la course au-dessus de 14,4 km/h et se recharge en dessous, Stamina règle sa taille et sa recharge, la vitesse max baisse sous 80 % de réserve (jusqu'à 0,6 réserve vide). La minute ne fatigue plus. Réserve tracée par joueur (`PlayerSnapshot.energy`).

**Course par tranche de temps joué, tous joueurs de champ (distance au-dessus de 19,8 km/h, part ; sprints par joueur et par 15 min ; m/min).**

| Tranche | 12d (fatigue par la minute) | 12e (réserve) |
|---|---|---|
| 0-15 | 0,163 ; 6,3 ; 126 | 0,164 ; 6,3 ; 127 |
| 15-30 | 0,169 ; 7,0 ; 129 | 0,160 ; 6,2 ; 126 |
| 30-45 | 0,163 ; 6,5 ; 127 | 0,152 ; 5,6 ; 126 |
| 45-60 | 0,165 ; 6,6 ; 128 | 0,140 ; 4,9 ; 129 |
| 60-75 | 0,162 ; 6,3 ; 129 | 0,129 ; 4,3 ; 125 |
| 75-90 | 0,131 ; 3,6 ; 120 | 0,126 ; 4,1 ; 127 |
| 90 et plus | 0,114 ; 2,3 ; 114 | 0,124 ; 4,0 ; 127 |

**Baisse de fin de match** (course au-dessus de 19,8 km/h, 75-90 contre 0-15) : − 23 % pour tous (repère 10 à 30 % ; − 20 % au 12d, mais concentrée après la 75e minute) ; par Stamina, rapport 0,62 (40 à 55), 0,71 (55 à 70), 0,82 (70 et plus) ; par joueur, rapport médian 0,91 (1er décile 0,46, 9e décile 1,29) ; sprints : rapport médian 0,84. La distance totale reste plate (126 à 129 m/min).

**Constat.** La fatigue suit maintenant l'effort : la course rapide baisse peu à peu dès le deuxième quart d'heure, au lieu d'une chute à partir de la 75e minute ; un joueur qui court beaucoup s'épuise plus tôt (1er décile 0,46) qu'un joueur économe (9e décile au-dessus de 1). Stamina garde son rôle (0,62 à 0,82). Le premier réglage, avec une recharge deux fois plus lente (`12e-r1-det1`), donnait − 38 % pour tous et − 36 % aux Stamina de 70 et plus : au-delà du repère, il a été écarté (ticket 12e, table des constantes).

**Autres indicateurs (12d → 12e).** Distance au-dessus de 19,8 km/h 15,6 % → 14,4 % (repère 6 à 10 %) ; km par joueur 12,5 → 12,6 ; sprints 38,6 → 34,2 par match ; appels 24,0 → 22,9 par 90 min ; tirs tracés 23,3 → 21,4 par équipe ; buts 3,6 → 3,5 ; conversion 7,8 → 8,2 % ; buts dans la surface 64 → 60 % ; passes 894 → 911 ; bloc inchangé (31,7 m, lignes à 15,4 et 15,9 m). Aucun écart au repère ne s'aggrave nettement ; volumes et tirs restent au 18d et au 18e.

**Déterminisme.** Les 10 premiers matchs rejoués (`12e-det2.json`) : 2 450 clés par match communes, valeurs identiques. Suite complète : 2 751 passés, 14 désélectionnés.

**Scène A/B du 19d, revue.** La minute ne fatigue plus : la scène compare le même joueur réserve pleine et réserve à 0,2 (5,3 m de conduite en 2 s contre 7,6 m), et un joueur réserve pleine à la 85e conduit autant qu'à la 15e ; probabilité de passe identique.

## 28. Calibration provisoire des volumes de course (ticket v2-realisme/18d, 500 matchs, 11/11/2026)

Commande : `scripts/bench_series.py 500 --processus 7`, fichiers `.scratch/v2-realisme/mesures/18d-500.*` ; série de réglage sur 50 matchs `18d-a.*` contre `12e-det1.*` (avant, mêmes graines) ; essais écartés : `18d-b.*` (marge de rattrapage 0,20). Constante **provisoire** retenue par délégation du propriétaire : le défenseur qui marque ou couvre suit l'allure de l'adversaire suivi plus `FOLLOW_CATCH_UP` = 0,10 de sa vitesse max, jamais sous sa course sans ballon (`defense.follow_intensity`, appelé par `cerveau.decide`). Avant : marquage et couverture au sprint quelle que soit l'allure de l'adversaire.

**Diagnostic avant réglage (12e, 6 matchs, distance au-dessus de 19,8 km/h par intention).** Marquage : 32 à 38 % de la course rapide des défenseurs et des milieux ; ballon libre : 27 à 52 % (sprint réaliste, gardé) ; appels : 33 à 44 % de celle des attaquants.

| Indicateur | 12e (50) | 18d (50) | 18d (500) | Repère |
|---|---|---|---|---|
| Distance au-dessus de 19,8 km/h (part) | 14,4 % | 9,8 % | 9,9 % [9,8 ; 9,9] | 6 à 10 % (R6) |
| Distance au-dessus de 25 km/h (part) | 4,8 % | 2,7 % | 2,7 % | suivi |
| Distance par joueur de champ (km) | 12,6 | 12,1 | 12,1 | 10 à 12 (R4) |
| Sprints par joueur et par match | 34,2 | 18,7 | 18,6 | suivi |
| Appels par joueur et par 90 min | 22,9 | 23,6 | 23,9 | 15,1 en moyenne (R5, indicatif) |
| Passes par match ; par minute de jeu effectif | 911 ; 12,5 | 912 ; 12,5 | 916 ; 12,6 | 890 à 940 ; 15 à 17 (R7) |
| Passes par possession | 2,58 | 2,70 | 2,70 | 3 à 5 |
| Tirs tracés par équipe | 21,4 | 21,6 | 21,9 | 8 à 15 (R1) |
| Buts par match ; conversion | 3,5 ; 8,2 % | 3,8 ; 8,8 % | 3,5 ; 8,1 % | 2 à 3,5 ; 10 à 12 % |
| Tacles ; fautes par match | 47,2 ; 14,8 | 46,5 ; 14,9 | 47,1 ; 14,6 | 30 à 40 ; 21 à 26 |
| Possession d'équipe (s) | 16,4 | 17,2 | 17,1 | suivi |
| Hauteur du bloc sans ballon (m) | 31,7 | 31,8 | 31,9 | suivi |

**Par poste, 500 matchs (km ; m au-dessus de 19,8 km/h, avant → après ; appels par 90 min).** DC 11,1 ; 956 → 433 ; 3,4. LB 10,6 ; 1 169 → 607 ; 8,2. RB 10,6 ; 1 185 → 602 ; 6,9. MDC 12,1 ; 1 849 → 881 ; 9,7. MC 12,0 ; 2 007 → 1 009 ; 21,2. MOC 13,4 ; 2 677 → 1 971 ; 55,0. AG 12,9 ; 2 471 → 1 987 ; 37,8. AD 13,0 ; 2 535 → 2 090 ; 37,4. BU 14,7 ; 2 687 → 2 478 ; 68,9. Repère réel au-dessus de 19,8 km/h (section 6, R6) : DC 586 à 716 m, MC 857 à 1 001 m, attaquants 811 à 1 113 m.

**Constat.** La course rapide globale entre dans le repère (9,9 %) ; les milieux y sont (MC 1 009 m, MDC 881 m) ; le bloc, les passes, les tirs, les tacles et les fautes ne bougent pas au-delà du bruit. Fin de match (500 matchs) : course au-dessus de 19,8 km/h 0,112 (0-15) → 0,087 (75-90), − 22 % (repère 10 à 30 %).

**Écarts restants, attribués.**
- Attaquants environ deux fois au-dessus du réel (MOC, ailiers, BU : 2,0 à 2,5 km au-dessus de 19,8 km/h ; appels BU 69, MOC 55 par 90 min) et ordre des postes en distance totale inversé (BU en tête) : **mécanisme**, pas de récupération entre deux efforts, un appel suit l'autre sans pause (ticket 12f, explosivité). Essai écarté : `off_ball.RUN_INTERVAL_S` 1,0 → 2,5 s, sans effet mesurable (l'appel poursuit un espace qui bouge, le délai ne coupe pas la course).
- Défenseurs sous le réel (DC 433 m contre 586 à 716 m) : **mécanisme**, presque aucune passe en profondeur (0,4 % des passes), donc peu de replis au sprint (`v2-collectif/32a`, 32b). Essai écarté : marge de rattrapage 0,20, sans effet sur les défenseurs (DC 434 → 464 m sur 50 matchs) et course rapide globale 10,1 %.
- Passes par minute de jeu effectif sous 15 à 17 : temps de jeu effectif trop haut (73 %), sans remplacements ni assez de fautes ; **calibration finale** et tickets de règles.
- Passes par possession (2,7 contre 3 à 5) et volume de tirs (R1) : choix du porteur (conduite 72 % des décisions), découpé au **18f**, puis tir et gardien au 18e.
- Intensité des appels vers un espace libre gardée à 0,75 de la vitesse max (course réelle d'appel entre 19,8 et 25 km/h, test du 12d).

**Attributs.** Work Rate garde son sens dans le marquage : il fixe le plancher de `follow_intensity` (Work Rate 5 / 50 / 99, adversaire arrêté : 0,45 / 0,55 / 0,65 ; adversaire à 0,8 de la vitesse max : 0,90 pour tous). Off the Ball et Stamina ne sont pas touchés.

**Déterminisme.** Les 10 premiers matchs rejoués (`18d-det2.json`) contre les 10 premiers de la série de 500 : 2 432 clés communes, valeurs identiques.

## 29. Choix du porteur : diagnostic et couloir de passe (ticket v2-realisme/18f, 50 matchs, 11/11/2026)

Commande : `scripts/bench_series.py 50 --processus 7`, fichiers `.scratch/v2-realisme/mesures/18f-det1.*` (après) contre les 50 premiers matchs de `18d-500.*` (avant, mêmes graines) ; essais : `18f-cone12.*` (12 matchs) et `18f-cone50.*` (50 matchs), cône seul, sans la portée de jambe. Aucune constante existante modifiée : la cause est un mécanisme (pression comptée deux fois dans la difficulté de passe), corrigé par une règle géométrique (cône de pente 1, soit 45°, près du passeur) et une constante de modèle nouvelle, `possession._LANE_REACH_M` = 1,0 m (portée de jambe, même valeur que `shooting.BLOCK_WIDTH_M`), retenues par délégation du propriétaire.

**Diagnostic (état 18d, 12 matchs, 37 440 décisions ; script de diagnostic du ticket 18f).**
- La conduite est le meilleur choix **réel** dans 80 % des décisions (passe 19 %, tir 1 %) ; 5,7 % seulement des conduites choisies laissaient une passe meilleure : la perception (Decisions, Composure, Anticipation) n'est pas la cause.
- La conduite est évaluée juste : garde évaluée sur 1,5 s contre ballon gardé 1,5 s après, par tranche de gêne du porteur : 0,98 / 0,98 (gêne 0), 0,91 / 0,93 (0,4), 0,88 / 0,89 (0,6), 0,86 / 0,84 (0,8). 84 % des conduites se jouent avec un adversaire à moins de 2,5 m.
- La meilleure passe offerte à un porteur pressé ne réussit qu'à 0,60 (Passing moyen 57) : difficulté 10 + distance 13,2 + pression 8,3 + **couloir 12,0** + receveur marqué 0,2. Le presseur au contact (1 à 2 m) comptait deux fois : dans la pression du passeur et comme adversaire dans le couloir de **toute** passe jouée de son côté (à moins de 2 m de toute trajectoire qui part vers lui), même à côté de lui.
- Correction (`possession._lane_opponents`) : près du passeur, un adversaire n'est dans le couloir que s'il est à moins de son avancée le long de la trajectoire (cône de 45°) ou à portée de jambe tendue (1 m, même portée que le contre d'un tir, `shooting.BLOCK_WIDTH_M`) ; au-delà de 2 m d'avancée, couloir de 2 m inchangé. Le cône seul (essai `18f-cone50`) laissait passer à côté d'un presseur à 1,2 m une passe qui frôle sa jambe (0,93 m) : le pressing coordonné ne fermait plus que 0,3 solution au lieu de 1,8 (`test_v2engine_pressing.py`) ; avec la portée de jambe, 1,7.
- Second écart, hors de ce ticket : la chance de passe évaluée (0,82 en moyenne pour les passes choisies) dépasse la passe reçue par le receveur visé (0,72) ; la coupe en vol et le contrôle du receveur ne sont pas dans l'évaluation, et l'adversaire du couloir pèse deux fois à la résolution (difficulté puis coupe en vol) : **mécanisme**, ticket `v2-realisme/18g`.

| Indicateur (moyenne par match, 50 matchs) | 18d | 18f, cône seul | 18f | Repère |
|---|---|---|---|---|
| Choix : conduite / passe / tir (part des décisions) | 70,8 / 27,8 / 1,4 % | 66,9 / 31,6 / 1,5 % | 68,3 / 30,2 / 1,4 % | suivi |
| Passes par possession | 2,71 | 2,88 | 2,82 [2,75 ; 2,88] | 3 à 5 |
| Passes par match ; par minute de jeu effectif | 912 ; 12,5 | 970 ; 13,1 | 945 [923 ; 968] ; 12,9 | 890 à 940 ; 15 à 17 (R7) |
| Passes réussies ; chez l'adversaire | 74,2 ; 23,6 % | 75,4 ; 22,7 % | 74,9 ; 23,1 % | 70 à 90 % ; 15 à 20 % |
| Solutions de passe ouvertes (nombre) | 1,93 | 2,24 | 2,11 | suivi |
| Pertes en conduite ; pertes de balle (agrégé) par match | 89,6 ; 333 | 80,2 ; 331 | 83,5 ; 331 | suivi |
| Tirs tracés par équipe | 21,6 | 21,4 | 21,3 | 8 à 15 (R1) |
| Buts par match ; conversion | 3,8 ; 8,8 % | 4,1 ; 9,5 % | 2,96 [2,46 ; 3,46] ; 6,8 % | 2 à 3,5 ; 10 à 12 % |
| Buts dans la surface (agrégé) | 59,0 % | 59,5 % | 64,9 % | 88 à 89 % (R3) |
| Tacles ; fautes par match | 46,5 ; 14,9 | 45,6 ; 14,6 | 46,3 ; 14,7 | 30 à 40 ; 21 à 26 |
| Possession d'équipe ; temps par possession de joueur (s) | 17,3 ; 2,88 | 17,3 ; 2,73 | 17,3 ; 2,79 | 11 à 16 ; 2 à 3 |
| Distance au-dessus de 19,8 km/h (part) | 9,8 % | 9,9 % | 9,9 % | 6 à 10 % (R6) |

Buts et conversion : 4,1 buts avec le cône seul, 2,96 avec la portée de jambe, pour deux règles presque identiques et des tirs inchangés ; la série de 500 matchs du 18d donnait 3,54 [3,37 ; 3,70]. Lu comme du bruit de 50 matchs (trajectoires de match divergentes), à relire sur 500 matchs au 18e.

**Écarts restants, attribués.**
- Passes par possession 2,82, sous 3 à 5 : les pertes de balle ne baissent pas (331 par match) ; une passe sur quatre finit chez l'adversaire, dont environ 10 points par la coupe en vol absente de l'évaluation : **mécanisme** (18g), puis réussite des passes à la calibration finale (`v2-collectif/22a`).
- Passes par match 945, à la limite haute de 890 à 940 (intervalle [923 ; 968]), alors que les passes par minute de jeu effectif (12,9) restent sous 15 à 17 : le temps de jeu effectif est trop haut (74 %, réel 53 à 56 %, sans remplacements ni assez de fautes) ; à temps effectif réel, le même rythme donnerait environ 730 passes. **Calibration finale** et tickets de règles, pas de réglage ici (il éloignerait le rythme par minute effective).
- Tirs tracés (R1) inchangés : les tirs viennent des récupérations hautes et des conduites (57 % après un dribble), pas du choix de la passe ; seuil et valeur du tir au **18e**.
- Passes visées vers les DC : non relues séparément ; la conduite reste majoritaire chez tous les postes, relance au 18g puis au 22a.

**Attributs.** Le cône ne lit aucune note. Scènes A/B (`18f-ab.txt`, 400 scènes de porteur pressé, 99 contre 11, règle d'avant contre d'après) : meilleure passe, Passing + 0,53 → + 0,51, Composure + 0,075 → + 0,072 ; part des passes choisies, Passing + 0,62 → + 0,62, Vision + 0,10 → + 0,11, Dribbling − 0,13 → − 0,15, Decisions − 0,30 → − 0,26 : aucun effet inversé ni annulé. Tests de garde (`test_v2engine_garde_probabiliste.py`, `test_v2engine_rayon_attributs.py`) verts dans la suite complète.

**Déterminisme.** Les 10 premiers matchs rejoués (`18f-det2.json`) contre les 10 premiers de `18f-det1.json` : 2 437 clés communes, valeurs identiques. Suite complète : 2 754 passés, 14 désélectionnés (`18f-suite.txt`).

**Série de 500 matchs (demande de l'expert, 12/11/2026).** `18f-500.*` (496 min de machine), comparaison appariée avec `18d-500` (`18f-comparaison.txt`, mêmes 500 matchs, après − avant) : passes par possession 2,70 → 2,81 (+ 0,12 [+ 0,10 ; + 0,13]) ; conduite − 2,3 points des décisions ; passes par match 916 → 948 (+ 32 [+ 28 ; + 36]), intervalle [941 ; 955], **0,8 au-dessus de la borne de 940** ; passes par minute de jeu effectif 12,6 → 12,9 ; temps par possession de joueur − 0,09 s. Sans écart significatif : buts (3,47 par match, écart − 0,07 [− 0,29 ; + 0,15]), conversion (8,1 %), buts dans la surface (58,8 %), tacles (46,9), fautes (14,7). La baisse des buts lue sur 50 matchs était du bruit.


## 30. Passe : même risque à l'évaluation et en vol (ticket v2-realisme/18g, 50 matchs, 12/11/2026)

Commande : `scripts/measure_v2.py` en 4 lots (`--debut 0, 13, 26, 39`), fichiers `.scratch/v2-realisme/mesures/18g-50-lot*.*`, synthèse `18g-50-synthese.txt` ; référence : `18f-det1.*` (18f livré, mêmes graines). Diagnostic et ajustement de la table : scripts hors dépôt (12 puis 50 matchs, 44 308 passes de jeu), résumés dans le ticket.

**Ce qui change.** La chance de passe que lit la décision (`possession.pass_success_probability`) devient la chance que la passe ne soit **pas perdue** (aucun adversaire ne touche le ballon le premier) : produit des (1 − coupe) de chaque adversaire, selon sa distance à la trajectoire (table mesurée, près du passeur ou sur le trajet), × [précise × (1 − 0,05) + imprécise × part non perdue selon la longueur (0,83 / 0,77 / 0,62)]. La précision (Passing contre difficulté, sans terme de couloir) reste tirée à la résolution par la même fonction (`pass_accuracy_probability`). Le terme de couloir (+ 12 de difficulté par adversaire) est supprimé : il sous-comptait la coupe (évaluée 0,96, reçue 0,56 avec un adversaire dans le couloir).

**Indicateur.** À chaque passe de jeu (remises exclues), le banc note la chance évaluée au lancement et l'issue au premier contact : perdue si un adversaire touche le ballon le premier ; reçue par le receveur visé, pour information. Par tranche de chance évaluée (`PASS_CHANCE_BINS`).

| Chance évaluée | Passes par match | Évaluée | Non perdue | Écart (points) | Reçue par le visé |
|---|---|---|---|---|---|
| [0 ; 0,1[ | 0,2 | 0,049 | 0,083 | − 3,4 | 0,083 |
| [0,1 ; 0,2[ | 2,5 | 0,168 | 0,113 | + 5,5 | 0,105 |
| [0,2 ; 0,3[ | 2,7 | 0,219 | 0,182 | + 3,7 | 0,182 |
| [0,3 ; 0,4[ | 0,2 | 0,369 | 0,500 | − 13,1 | 0,500 |
| [0,4 ; 0,5[ | 2,5 | 0,464 | 0,421 | + 4,4 | 0,357 |
| [0,5 ; 0,6[ | 14,6 | 0,561 | 0,528 | + 3,2 | 0,465 |
| [0,6 ; 0,7[ | 36,8 | 0,653 | 0,642 | + 1,1 | 0,557 |
| [0,7 ; 0,8[ | 137,1 | 0,756 | 0,775 | − 1,9 | 0,694 |
| [0,8 ; 0,9[ | 372,8 | 0,858 | 0,881 | − 2,3 | 0,771 |
| [0,9 ; +[ | 360,9 | 0,932 | 0,944 | − 1,2 | 0,866 |
| toutes | 930,5 | 0,854 | 0,869 | − 1,6 | 0,778 |

**Lecture.**
- **Critère (moins de 5 points par tranche)** : tenu sur les tranches qui portent 99 % des passes. Hors critère : [0,1 ; 0,2[ (+ 5,5 sur 125 passes, erreur type environ 2,8 points) et [0,3 ; 0,4[ (10 passes) ; dans le bruit.
- **Avant** (18f, même diagnostic) : évaluée 0,831, reçue 0,705 ; écart de 16 points sur [0,9 ; 1], de 40 points avec un adversaire dans le couloir.
- **Ce que la mesure prouve et ne prouve pas.** La table décrit le moteur, pas le football réel (chiffres réels : non trouvés) ; elle est à remesurer si le mouvement des joueurs change, et cet indicateur le signalera. La part reçue par le receveur visé reste plus basse (0,778) : passes touchées par un coéquipier, mortes, et contrôles ratés, qui ne sont pas des pertes.

**Effets sur le jeu (50 matchs, 18f → 18g ; repère).** Passes réussies 74,9 → 81,9 % (70 à 90 %) ; chez l'adversaire 23,1 → 14,9 % (15 à 20 %) ; passes par possession 2,81 → 4,35 (3 à 5) ; buts 2,96 → 2,50 (2 à 3,5) ; conduites 2 054 → 1 197 intervalles par match, pertes en conduite 83,5 → 46,3 ; **possession d'équipe 17,2 → 25,6 s (11 à 16, désormais au-dessus)** ; **passes par match 945 → 985 (890 à 940, plus au-dessus)** ; fautes 14,7 → 12,2 (21 à 26) ; solutions de passe ouvertes 2,1 → 4,8.

**Scènes A/B** (`18g-ab-script.py`, 400 scènes du 18f ; `18g-ab-avant.txt`, `18g-ab.txt`). Aucun effet inversé ni annulé. Effets réduits : meilleure passe Passing 99 contre 11 + 0,514 → + 0,086, Composure + 0,072 → + 0,012 ; part de passes choisies, Passing + 0,620 → + 0,143. Vision + 0,108 → + 0,182, Dribbling − 0,148 → − 0,203, Decisions − 0,262 → − 0,222. Cause : dans le moteur, une passe ratée ne dévie que de 10 à 25 % de sa longueur et n'est perdue que 2 fois sur 10 environ ; Passing pèse peu sur l'issue réelle, et l'évaluation le reflète désormais. Ticket 18h.

## 31. Passe ratée : déviation et perte de balle (ticket v2-realisme/18h, 50 matchs, 12/11/2026)

Commande : `scripts/measure_v2.py` en 4 lots, fichiers `.scratch/v2-realisme/mesures/18h-50-lot*.*`, synthèse `18h-50-synthese.txt` ; référence : 18g (`18g-50-lot*.*`) et 18f livré (`18f-det1.*`), mêmes graines. Diagnostics hors dépôt (12 et 50 matchs), résumés dans le ticket.

**Ce qui change.** Une passe ratée (tirage de précision perdu) dévie de 25 à 50 % de sa longueur, au lieu de 10 à 25 %. Une passe est désormais « perdue » si un adversaire touche le ballon le premier **ou** si le ballon sort ou est sifflé avec remise pour l'adversaire (réserve A3 du 18g) ; la table « passe imprécise non perdue » de l'évaluation est remesurée sur cette définition : 0,78 sous 10 m, 0,64 au-delà (coupe imprévue inchangée, 0,05).

**Réel indicatif** (Premier League 2024-25, Total Football Analysis d'après les catégories FBref ; Opta, passes de plus de 35 yards : 47,3 %) : courte (moins de 13,7 m) 89,4 %, moyenne (13,7 à 27,4 m) 87,1 %, longue (plus de 27,4 m) 51,7 %. Moteur (réussie = reçue par un coéquipier au premier contact) : avant 84,9 / 79,5 / 75,8 % ; après 82,9 / 76,3 / 71,2 %. Passe imprécise reçue par le receveur visé : 61,7 → 50,2 %. Le profil réel n'est pas atteint : une passe précise est coupée environ 15 % du temps quelle que soit sa longueur (ticket 18i).

**Calibration de la passe** (indicateur du 18g, définition du 18h).

| Chance évaluée | Passes par match | Évaluée | Non perdue | Écart (points) |
|---|---|---|---|---|
| [0,5 ; 0,6[ | 21,2 | 0,559 | 0,561 | − 0,3 |
| [0,6 ; 0,7[ | 65,7 | 0,664 | 0,653 | + 1,1 |
| [0,7 ; 0,8[ | 180,6 | 0,767 | 0,733 | + 3,4 |
| [0,8 ; 0,9[ | 260,8 | 0,845 | 0,817 | + 2,7 |
| [0,9 ; +[ | 333,9 | 0,932 | 0,917 | + 1,5 |
| toutes | 873,7 | 0,834 | 0,813 | + 2,2 |

Tranches basses (moins de 0,5 ; 11,5 passes par match en tout) : − 10,5 (0,4 passe par match), + 3,7, + 2,1, + 5,3 (0,8 passe par match), − 2,1. Sous 5 points sur toutes les tranches d'au moins 100 passes sauf [0,3 ; 0,4[ (40 passes, + 5,3).

**Effets sur le jeu (18f → 18g → 18h ; repère).** Passes par match 945 → 985 → **933** (890 à 940, de nouveau dans le repère) ; passes réussies 74,9 → 81,9 → 79,7 % (70 à 90 %) ; chez l'adversaire 23,1 → 14,9 → 16,6 % (15 à 20 %) ; passes par possession 2,81 → 4,35 → 3,84 (3 à 5) ; **possession d'équipe 17,2 → 25,6 → 23,8 s (11 à 16, toujours au-dessus)** ; buts 2,96 → 2,50 → 2,08 (2 à 3,5) ; pertes en conduite 83,5 → 46,3 → 56,3 ; une-deux par équipe 2,05 → 0,97 → 1,47.

**Scènes A/B** (`18g-ab-script.py`, 400 scènes ; `18g-ab.txt` avant, `18h-ab.txt` après). Aucun effet inversé ni annulé. Passing regagne du poids : meilleure passe + 0,086 → + 0,142, part de passes choisies + 0,143 → + 0,230 ; Composure + 0,012 → + 0,021 ; Dribbling − 0,203 → − 0,182 ; Vision + 0,182 → + 0,165 ; Decisions − 0,222 → − 0,257.

## 32. Passe précise coupée : portée du receveur et table remesurée (ticket v2-realisme/18i, 50 matchs, 12/11/2026)

Commande : `scripts/measure_v2.py` en 4 lots, fichiers `.scratch/v2-realisme/mesures/18i-50-lot*.*` (portée et table) et `18i-portee-50-lot*.*` (portée seule), synthèse `18i-50-synthese.txt` (`18i-synthese.py`) ; référence : 18h (`18h-50-lot*.*`), mêmes graines. Diagnostic : `18i-diag-script.py` (enveloppes de lecture seule ; 12 puis 50 matchs), ajustement de la table : `18i-ajustement.py`, sortie `18i-ajustement.txt`.

**Cause trouvée.** Le contact au ballon se faisait à `CONTROL_RADIUS_M` (0,41 m) pour tout le monde, receveur visé compris : le ballon lui passait à côté (0,5 à 0,85 m) dans 8,6 % des passes courtes précises, puis un défenseur le ramassait plus loin, ballon presque mort (2,6 m/s). 57 % des coupes de passes courtes précises avaient lieu dans les 3 derniers mètres, 82 % d'entre elles au-delà du point visé.

**Ce qui change.** Le receveur visé d'une passe touche le ballon à `match.RECEIVER_REACH_M` = 1,0 m (jambe tendue plus ballon, la valeur de `shooting.BLOCK_WIDTH_M` reprise ; donnée réelle non trouvée) ; tout autre joueur garde 0,41 m. Table de l'évaluation remesurée sur 50 matchs : coupe par adversaire du 18g inchangée (écarts dans le bruit) ; coupe imprévue d'une passe précise 0,05 → 0,01 (mesurée 0,007 à 0,009 : l'ancien terme comptait le ballon passé à côté du receveur) ; passe imprécise non perdue 0,78 / 0,64 → 0,85 / 0,68.

**Réussite par longueur** (réussie = reçue par un coéquipier au premier contact ; diagnostic de 50 matchs avec la portée seule, 48 520 passes) : 82,9 / 76,3 / 71,2 % (18h) → 92,0 / 85,3 / 76,6 % ; réel indicatif 89,4 / 87,1 / 51,7 %. Passe précise : environ 85 % quelle que soit la longueur → 93,2 / 93,5 / 90,0 %. La passe longue reste trop réussie (mécanisme distinct, hors de ce ticket).

**Calibration de la passe** (indicateur du 18g, définition du 18h).

| Chance évaluée | Passes par match | Évaluée | Non perdue | Écart 18i (points) | Écart 18h | Portée seule |
|---|---|---|---|---|---|---|
| [0,4 ; 0,5[ | 4,5 | 0,471 | 0,540 | − 6,9 | − 2,1 | − 9,7 |
| [0,5 ; 0,6[ | 18,3 | 0,564 | 0,623 | − 5,9 | − 0,3 | − 6,6 |
| [0,6 ; 0,7[ | 49,2 | 0,662 | 0,690 | − 2,8 | + 1,1 | − 5,7 |
| [0,7 ; 0,8[ | 128,1 | 0,753 | 0,794 | − 4,2 | + 3,4 | − 6,2 |
| [0,8 ; 0,9[ | 342,2 | 0,847 | 0,874 | − 2,7 | + 2,7 | − 6,0 |
| [0,9 ; +[ | 443,5 | 0,959 | 0,970 | − 1,1 | + 1,5 | − 4,9 |

Sous 5 points sur les tranches de 0,6 à 1 (97,8 % des passes) ; au-delà sur [0,4 ; 0,5[ et [0,5 ; 0,6[ (2,2 % des passes, chance sous-évaluée) : écart accepté par le propriétaire le 12/11/2026 (option 1), à reprendre à `v2-collectif/22a`. Le contrôle hors ligne de la table (précision tirée, et non chance de précision évaluée) prévoyait moins de 2 points partout : il ne mesurait pas la même chose que le banc.

**Effets sur le jeu (18h → portée seule → 18i ; repère).** Passes par match 933 → 1 001 → **1 043** (890 à 940, au-dessus) ; passes réussies 79,7 → 86,1 → 86,2 % (70 à 90 %) ; chez l'adversaire 16,6 → 11,7 → 11,6 % (15 à 20 %, en dessous) ; passes par possession 3,84 → 4,67 → 5,11 (3 à 5) ; **possession d'équipe 23,8 → 27,0 → 28,3 s (11 à 16, plus loin encore)** ; buts 2,08 → 2,26 → 2,64 (2 à 3,5) ; pertes en conduite 56,3 → 66,2 → 54,6 ; une-deux par équipe 1,47 → 1,78 → 1,44 ; corners 6,5 → 5,6 → 7,2.

**Scènes A/B** (`18g-ab-script.py`, 400 scènes ; `18i-ab.txt`). Aucun effet inversé ni annulé : Passing + 0,139 (meilleure passe), + 0,227 (part de passes choisies) ; Composure + 0,021 ; Dribbling − 0,185 ; Vision + 0,198 ; Decisions − 0,185.

## 33. Portée du défenseur qui lit la passe et table remesurée (ticket v2-realisme/18j, 50 matchs, 12/11/2026)

Commande : `scripts/measure_v2.py` en 4 lots (`PYTHONPATH=.`), fichiers `.scratch/v2-realisme/mesures/18j-50-lot*.*`, synthèse `18j-50-synthese.txt` (`18j-synthese.py`) ; référence : 18i (`18i-50-lot*.*`), mêmes graines. Essai de portée sur 12 matchs : `18j-variante.py`, `18j-var-*`. Diagnostic : `18i-diag-script.py` (portée seule : `18j-diag/` ; moteur final : `18j-diag-final/`), ajustement `18j-ajustement.py` (`18j-ajustement.txt`), longueurs `18j-longueurs.py` (`18j-longueurs.txt`).

**Ce qui change.** Le défenseur qui a lu la passe (`anticipation.pass_readers`) touche le ballon à `match.READER_REACH_M` = 1,0 m, comme le receveur visé (18i) ; les autres joueurs gardent 0,41 m. Sans délai : la lecture exige déjà qu'il atteigne la trajectoire avant le ballon. Donnée réelle : non trouvée. Essai sur 12 matchs, passes chez l'adversaire : 11,7 % (0,41 m), 13,3 % (0,7 m), 14,9 % (1,0 m). Table de coupe de l'évaluation remesurée : près du passeur 0,82 / 0,21 / 0,02 ; trajet 0,43 / 0,25 / 0,12 / 0,07 / 0,03 / 0,02 ; coupe imprévue 0,01 ; passe imprécise non perdue 0,85 / 0,69.

**Calibration de la passe** (indicateur du 18g, définition du 18h).

| Chance évaluée | Passes par match | Évaluée | Non perdue | Écart 18j (points) | Écart 18i |
|---|---|---|---|---|---|
| [0,3 ; 0,4[ | 3,0 | 0,369 | 0,439 | − 7,0 | − 20,5 (0,6 par match) |
| [0,4 ; 0,5[ | 10,7 | 0,462 | 0,489 | − 2,7 | − 6,9 |
| [0,5 ; 0,6[ | 20,5 | 0,553 | 0,572 | − 1,9 | − 5,9 |
| [0,6 ; 0,7[ | 59,3 | 0,656 | 0,702 | − 4,6 | − 2,8 |
| [0,7 ; 0,8[ | 116,0 | 0,756 | 0,759 | − 0,3 | − 4,2 |
| [0,8 ; 0,9[ | 289,3 | 0,852 | 0,877 | − 2,5 | − 2,7 |
| [0,9 ; +[ | 442,0 | 0,958 | 0,963 | − 0,5 | − 1,1 |

Sous 5 points sur toutes les tranches d'au moins 100 passes sauf [0,3 ; 0,4[ (0,3 % des passes).

**Réussite par longueur** (reçue par un coéquipier au premier contact ; 48 367 passes) : 92,0 / 85,3 / 76,6 % (18i) → 90,6 / 84,6 / 75,0 % ; réel indicatif 89,4 / 87,1 / 51,7 %.

**Effets sur le jeu (18i → 18j ; repère).** Passes par match 1 043 → 998 (890 à 940) ; passes réussies 86,2 → 85,2 % ; chez l'adversaire 11,6 → 12,5 % (15 à 20, en dessous) ; passes par possession 5,11 → 4,63 (3 à 5) ; possession d'équipe 28,3 → 26,9 s (11 à 16) ; buts 2,64 → 2,62 ; pertes en conduite 54,6 → 61,5 ; face-à-face 9,0 → 10,3 par match. Scènes A/B (`18j-ab.txt`) : aucun effet inversé ni annulé. Déterminisme : deux exécutions identiques hors temps de calcul.

## 34. Calibration provisoire 2 : tirs, conversion et gardien (ticket v2-realisme/18e, 50 matchs, 12/11/2026)

Commandes : état de départ, série du 18j (`.scratch/v2-realisme/mesures/18j-50-lot*.*`) ; tirs par zone, `18e-zones.py` (50 matchs, mêmes graines ; lecture seule), synthèse `18e-zones-synthese.py`, sortie `18e-zones-avant.txt` ; essai de contre, `18e-variante.py` (`BLOCK_CHANCE` 0,75, `18e-b075-lot*.*`) ; scène du contre, `18e-contre-scene.txt`.

**Aucune constante modifiée.** Les écarts aux repères viennent de mécanismes ; les régler ici les masquerait (règle des calibrations provisoires).

**Tirs par zone** (hors penaltys).

| Zone | Tirs par équipe | Conversion | Contrés | Cadrés | xG neutre moyen | Réel |
|---|---|---|---|---|---|---|
| Surface | 3,85 | 17,7 % | 17,4 % | 38,7 % | 0,187 | 14,7 % (penaltys compris) |
| Hors surface | 14,13 | 4,4 % | 17,6 % | 23,5 % | 0,041 | 4,2 % |
| [25 ; 30[ m | 6,93 | 2,3 % | 17,3 % | — | 0,021 | — |
| Ensemble | 17,98 | 7,2 % | 17,6 % | 26,8 % | 0,073 | 10 à 12 % |

Part des tirs dans la surface 21,4 % (réel 68,3 %). Avec le mélange réel, les taux par zone donneraient environ 33,8 % de cadrés et 13,5 % de conversion (0,683 × 17,7 + 0,317 × 4,4) : **l'exécution et le gardien sont dans l'ordre de grandeur, le mélange ne l'est pas.** Une fois le mélange corrigé, la conversion dépasserait le repère R2 (10 à 12 %) : la conversion dans la surface (17,7 % hors penaltys, erreur type environ 1,9 point, contre 14,7 % réel penaltys compris) est à surveiller au 18k et à revoir au `v2-collectif/22c`. Cause : un tir manqué ne coûte rien dans la décision (réserve A2 du `v2-collectif/28a`), le porteur tire de 25 à 30 m à 0,021 d'xG. Ticket `v2-realisme/18k`.

**Contrés.** 17,6 % (repère 22,5 %). `BLOCK_CHANCE` 0,75 donne 22,4 % sur 50 matchs (conversion 7,2 %, buts inchangés), mais l'estimateur de la décision (05e) place mal l'angle couvert par un défenseur en course (le test de cohérence échoue ; écart déjà présent à 0,6). Gardée à 0,6 ; ticket `v2-realisme/05j`.

**Gardien.** Taux d'arrêt des cadrés environ 73 % (repère environ 70 %) : 36 % sous 11 m, 62 % de 11 à 18 m, 77 % de 18 à 25 m, 89 % au-delà. Aucun réglage.

**Penaltys.** 0,04 par match (réel environ 0,34) : fautes dans la surface absentes (`21b`, `21c`).
