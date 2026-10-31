# Indicateurs de mesure du moteur V2

Référence du ticket `.scratch/v2-collectif/issues/01-banc-de-mesure-tactique.md`. Chaque indicateur est calculé par `scripts/measure_v2.py` sur N matchs à graines fixes.

**Principe (décision du propriétaire, 26/10/2026).** Les valeurs réelles sont des **indicateurs de calibration**, pas des objectifs. Les indicateurs sont lus comme des **distributions conditionnelles** (zone du ballon, score, minute ; phase de jeu une fois le ticket 03 livré), et pas comme une seule moyenne.

**Sources.** Les valeurs réelles des indicateurs tactiques viennent de la recherche documentaire fournie par le propriétaire le 26/10/2026. Les liens sont repris tels quels ; les chiffres sont à relire dans le texte intégral avant de servir de critère d'acceptation.

**Découpages communs.** Zone du ballon : tiers défensif, tiers médian, tiers offensif (du point de vue de l'équipe en possession). Score : mène, égalité, menée. Minute : tranches de 15 min. Situation de jeu (ticket v2-collectif/03) : possession installée, défense placée, transition offensive, transition défensive, dernier tiers ; pour les indicateurs autour du ballon, c'est la situation de l'équipe qui défend. La part du temps passée dans chaque situation est aussi rapportée.

## 1. Indicateurs classiques (cibles déjà validées)

| Indicateur | Définition | Unité | Cible |
|---|---|---|---|
| Passes par minute | Passes des deux équipes / minutes jouées | /min | 15-17 |
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
| Choix du porteur | Part de passes, conduites et tirs | % | suivi |
| Distance | Km par joueur de champ, par poste | km | 9-14 ; ordre des postes de Bradley 2009 |
| Haute intensité | Part de la distance au-dessus de 25 km/h ; part du temps au-dessus de 19,8 km/h | % | 2-3 ; 2-5 |
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
| 7 | Repli après une perte | Trois mesures distinctes : latence (délai avant que le centre de l'équipe recule à plus de 1 m/s), vitesse de recul, temps pour reformer le bloc (longueur revenue sous sa valeur défensive médiane) | s, m/s, s | Pas de valeur publique robuste |
| 8 | Pertes en transition | Ballon reperdu moins de 5 s après une récupération : nombre par match et part des récupérations, par zone | /match, % | Définition cohérente avec la littérature ([PubMed 38045740](https://pubmed.ncbi.nlm.nih.gov/38045740/)) |
| 9 | Couverture du presseur | Part du temps de pressing pendant lequel un second défenseur est dans la zone de couverture : ellipse orientée vers le but, d'environ 3 m derrière le porteur à 9 m devant lui | % | Zone de pression elliptique selon l'angle ([KIT](https://publikationen.bibliothek.kit.edu/1000187744/170106643), [PMC5968892](https://pmc.ncbi.nlm.nih.gov/articles/PMC5968892/)) |
| 10 | Appels et redondance | Appel : course de plus de 0,7 s au-dessus de 15 km/h d'un coéquipier du porteur ; appels par joueur et par match, par poste ; part des appels simultanés visant la même zone (moins de 5 m) | /joueur/match, % | 15,1 appels par joueur et par match, de 5,5 (défenseurs centraux) à 19,2 (milieux offensifs) ([PLOS One 2022](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0265540)) |
| 11 | Occasions de contre | Tirs dans les 15 s après une récupération, séparés selon la zone de récupération : son propre camp (contre-attaque) ou camp adverse (récupération haute) | /match | Fenêtre de 15 s jusqu'au tir ([FIFA EFI](https://www.fifatrainingcentre.com/media/native/tournaments/womens-world-cup/2023/FIFA%20Enhanced%20Football%20Intelligence%20(EFI)%20Explainations_EN%20v1.1.pdf)) |

**Plus tard, dans les tickets concernés** (ils demandent des mécanismes qui n'existent pas encore) : temps d'arrivée du défenseur (ticket 09), lignes adverses cassées et valeur de l'espace créé (ticket 13), contrôle de la profondeur (ticket 05), indicateurs par phase de jeu (ticket 03), conditionnement par style tactique et qualité relative des équipes (ticket 22).

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
| Appel | > 0,7 s au-dessus de 15 km/h, créant une option de passe (ou conclu par la réception) | Recherche du propriétaire |
| Appels redondants | Simultanés, finissant à moins de 5 m l'un de l'autre | Proposé |
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

**Soutien du porteur (ticket v2-collectif/06, 20 matchs, 31/10/2026).** Avant (`8043889`) → après : solutions de passe ouvertes (seuil 0,7) 1,86 → 1,96 ; regroupement avec ballon (coéquipiers à moins de 5 m hors duel) 6,8 → 7,0 %, dont la moitié à côté du porteur (diagnostic, 4 matchs) : le critère, validé par le propriétaire le 31/10/2026, l'exclut désormais (environ 3,3 %) ; sans ballon 8,4 → 8,6 % ; au moins un joueur derrière le ballon en possession installée 100 → 100 % ; buts 1,95 → 2,75 par match ; tirs 11,35 → 12,1 par équipe ; hors-jeu 0,6 → 1,05 par match ; appels des DC, latéraux et MC +30 à +50 % ; temps de calcul +9 %. Profils : Off the Ball 99 contre 11, solutions de passe 1,96 contre 1,92. Teamwork : la règle d'équilibre (2 joueurs de champ derrière le ballon) ne s'est déclenchée qu'une fois en 4 matchs, environ 7 joueurs y étant déjà ; son effet est vérifié par les tests unitaires, pas en match (critère validé le 31/10/2026).

**Correction C5 du ticket 06 (diagnostic, 4 matchs, 31/10/2026).** Les mesures de 20 matchs ci-dessus datent d'avant C5 : pendant une passe de son équipe, les coéquipiers autres que le receveur gardent leur appel au lieu de courir au ballon. Regroupement avec ballon, porteur inclus : 6,8 → **4,9 %**. Le reste est fait à 93 % de croisements passagers (les deux joueurs visent des points écartés de plus de 5 m), à 89 % en transition offensive. Point de départ du ticket 22, qui refera la mesure sur 20 matchs (réserve A1 du ticket 06).

**Le passeur ne reprend plus sa passe (ticket v2-collectif/26, 20 matchs, 31/10/2026).** Depuis le ticket 25 (`4d71418`), une passe sur deux (53 %) revenait au passeur au pas suivant et comptait comme réussie : toutes les mesures de passes, tirs, buts et hors-jeu depuis ce commit sont faussées. Avant (`c379ba6`) → après, mêmes graines : reprises par le passeur 53 → 0,8 % (2 matchs) ; receveur visé 19,5 → 60,8 % ; passes réussies 75,4 → 64,3 % ; passes chez l'adversaire 24,6 → 35,6 % (15 à 20 % au haut niveau) ; passes par minute 23,8 → 16,2 ; tirs 18,2 → 8,2 par équipe ; buts 4,3 → 1,75 par match ; hors-jeu 0,2 → 0,75 par match ; possession d'équipe 8,9 → 9,7 s. Nouvelle base pour la recalibration du hors-jeu et le ticket 22.

**Pressing coordonné (ticket v2-collectif/08, 20 matchs, 31/10/2026).** Avant (`8043889`) → après : pressings 1130 → 1122 par match, récupérés en 5 s 37 → 39 % ; solutions ouvertes 5,21 → 5,31 ; solutions faciles (≥ 0,8) 1,42 → 1,57 ; tacles 67,9 → 52,8 ; pertes 545 → 578 ; pertes en transition 24 → 29 % ; passes 18,5 → 17,6 par minute ; buts 2,1 → 2,0. Profils (99 contre 11) : Aggression, distance presseur-porteur 1,24 contre 1,49 m ; Anticipation, solutions faciles laissées 1,51 contre 1,59 ; Teamwork 1,69 contre 1,53 (sens inverse) ; Work Rate 1,62 contre 1,61. Réserve : le pressing n'a pas d'effet mesuré sur les passes, reprise au ticket 27.
