# Revue des attributs V2 : regard d'analyste

> 25/10/2026. Revue des 18 attributs branchés dans le moteur V2 à cette date (`v2engine/`), à la demande du propriétaire.
> Méthode pour chaque attribut :
> 1. Comparer un joueur **très moyen** (≈ 55) et un joueur **très bon** (≈ 88) sur cet attribut.
> 2. Décrire où la différence se voit concrètement sur un terrain.
> 3. Comparer avec ce que fait le code aujourd'hui.
> 4. Proposer comment y réinjecter cette différence.
>
> Logique commune validée : **réussite = note comparée à la difficulté réelle de l'action**. L'écart entre joueurs est faible sur une action facile et énorme sur une action difficile, et **la qualité d'exécution compte en plus de la réussite**. Rien n'est codé ici : chaque proposition devient un ticket, avec ses constantes à faire valider.

---

## Principe : capacité physique contre envie (validé le 25/10/2026)

**Chaque attribut a un rôle et un seul. La richesse du jeu vient de leur combinaison.**
- **Les attributs physiques ne donnent que la capacité.** Pace = vitesse maximale, et rien d'autre. Acceleration = temps pour l'atteindre. Stamina = réserve d'énergie.
- **Les attributs mentaux décident quand et combien le joueur utilise cette capacité** : Work Rate (efforts sans ballon : pressing, repli), Off the Ball (volume et intensité des appels), Teamwork (tenir et reprendre sa place), Determination (garder l'intensité quand ça tourne mal), Aggression (engagement au contact).
- Exemple : un joueur à Work Rate bas est surtout actif avec le ballon. Sans ballon, il fait « semblant » de presser (il approche sans engager, à l'économie). Un joueur à Work Rate haut ne compte pas ses efforts, mais s'épuise vite si sa Stamina est basse.

---

## Données réelles de référence (critères)

Les critères de cette revue s'appuient sur des mesures publiées, pas sur des ordres de grandeur. Quand une donnée n'a pas été trouvée, c'est écrit (**non trouvé**), et le critère est à confirmer avant son ticket.

| Domaine | Donnée réelle | Source |
|---|---|---|
| Distance par match | 9 à 14 km par joueur | Biology of Sport, revue 2024 |
| Course à très haute vitesse (> 25 km/h) | 2 à 3 % de la distance, soit environ 200-360 m par match (calcul) | Biology of Sport, revue 2024 |
| Course à haute intensité (> 19,8 km/h) | environ 3 % du temps de jeu | Di Mascio & Bradley 2013 (Premier League) |
| Vitesse de pointe en match | 32,9 ± 1,4 km/h (élite portugaise) ; 31-35 km/h (élite) ; base FM : environ 36-37 km/h pour les meilleurs | Silva et al. 2024 ; Keiner et al. |
| Sprint 10 m | environ 2,2 s (sélection espoirs) | Slovaquie U21 |
| Sprint 30 m | 3,87-3,99 s (les plus rapides d'un club MLS) ; 4,59 s (moyenne d'une sélection espoirs) | Whitecaps FC ; Slovaquie U21 |
| Passes réussies, par équipe | de 70 % (équipe la plus faible) à environ 90 % (meilleurs joueurs : 91 % pour Flamini) | données Opta (presse) |
| Passes longues (plus de 32-35 m) | environ 47 % réussies ; 10,5 à 19 % des passes selon les saisons | Opta |
| Passes sous pression | effet confirmé (plus dur sous pression), **écart moyen chiffré non trouvé** ; meilleurs joueurs environ 90 % sous pression (Kroos) | StatsBomb, PFF |
| Conversion des tirs | 10,9 % (hors tirs contrés), 46 % des tirs cadrés (Premier League 2016/17) | Opta |
| Grosses occasions | environ 41-45 % converties | Opta (MLS, presse) |
| Arrêts des gardiens | environ 68 % des tirs cadrés en moyenne ; de 51,5 % (le plus faible) à 73,5 % (le meilleur, Raya) | Premier League, Opta 2024/25 |
| Duels contre un dribbleur | les meilleurs défenseurs gagnent 78-87 % de leurs un contre un ; le plus faible 32 % ; **moyenne non trouvée** | Opta 2024/25 et 2025/26 |
| Contrôles ratés, ballons perdus au contact | **non trouvé** | à chercher (FBref : « miscontrols », « dispossessed ») |

---

## 0. Trois défauts transversaux (à corriger avant tout attribut)

Ces défauts faussent tous les attributs à la fois. Tant qu'ils restent, régler un attribut, c'est régler le symptôme d'un autre.

| # | Défaut | Ce qu'on voit à l'écran | Ce que fait un vrai match |
|---|---|---|---|
| T1 | **Tout le monde sprinte en permanence.** `step()` vise toujours la vitesse max du joueur. | Des ronds qui filent dans tous les sens ; Pace ne sert qu'à départager deux sprinteurs, puisque tout le monde est déjà à fond. | Un joueur court environ 10-12 km par match, dont seulement 0,5 à 1 km de sprint. Il trottine, se replace, puis accélère quand l'action l'exige (course au ballon, appel, repli). **C'est dans ces moments-là que Pace fait la différence.** |
| T2 | **Les actions sont tirées « par tick ».** Un adversaire à 1,5 m tente un tacle avec 50 % de chance… **toutes les 0,1 s**, donc environ 5 tacles par seconde au contact. | Ballons arrachés en permanence : c'est une des sources des 27 % de passes perdues. | Un défenseur choisit **un moment** pour tacler (souvent un seul tacle par duel), ou temporise. |
| T3 | **La difficulté n'existe nulle part.** Passe, contrôle, tir et tacle ont chacun une probabilité qui ne dépend que de la note, pas de la situation. | Une passe à 5 m sans pression est ratée aussi souvent qu'une transversale de 40 m sous pression. | Toute action a une difficulté (distance, pression, vitesse du ballon, angle, couloir). |

**Recommandation : un ticket « socle » qui pose ces trois corrections avant de reprendre les attributs un par un.** Le socle comprend : une intensité de course selon la situation, des décisions de duel prises une fois par duel et non à chaque tick, et une fonction de difficulté commune.

---

## 1. Physique

### Pace (vitesse de pointe)
- **Moyen contre très bon.** Le très bon, c'est la course en profondeur où le défenseur ne revient jamais, et le repli qui rattrape une erreur. Sur 30 m lancé, il prend 3 à 4 m à un joueur moyen. Sur 5 m, la différence est quasi nulle : ça, c'est l'affaire d'Acceleration.
- **Aujourd'hui.** Vitesse max 25 à 36,5 km/h selon la note (repères du guide) : les valeurs sont bonnes. Mais à cause de T1, tout le monde court toujours à sa pointe, donc la note ne se « voit » pas comme un atout ponctuel.
- **Proposition.** Garder les repères. **Pace ne règle que la vitesse maximale** : c'est le mental (Work Rate, Off the Ball…) qui décide quand le joueur sprinte (ticket socle 02). L'écart entre deux joueurs n'apparaît donc que dans les courses où les deux sprintent.
- **Critère (données réelles).** Vitesse de pointe atteinte en match de 31 à 35 km/h selon la note, 36-37 km/h pour les meilleurs de la base. Distance totale de 9 à 14 km, dont 2 à 3 % au-dessus de 25 km/h (environ 200-360 m). Aujourd'hui, le moteur fait sprinter tout le monde en permanence, loin de ces chiffres.

### Acceleration
- **Moyen contre très bon.** Le très bon gagne le premier mètre : départ d'un appel, sortie de dribble, pressing après la perte. Sur 5-10 m, c'est lui qui arrive le premier, même contre un joueur plus rapide en pointe (le « diesel » du guide).
- **Aujourd'hui.** Temps pour atteindre sa pointe : 2,5 s à 5, 1,5 s à 50, 0,5 s à 99. **0,5 s est irréaliste** : même Mbappé met environ 3 à 4 s pour atteindre sa pointe. Ce qui distingue un explosif, ce sont les 5 premiers mètres.
- **Proposition.** Recaler sur les temps réels, avec une montée en vitesse plus forte au départ (courbe réelle d'un sprint) qu'à la fin.
- **Critère (données réelles).** Départ arrêté : 30 m en environ 3,9 s pour les plus rapides, environ 4,6 s pour un joueur moyen ; 10 m en environ 2,2 s pour un joueur moyen.

### Stamina
- **Moyen contre très bon.** Le joueur moyen baisse visiblement à partir de la 60e-70e : moins de sprints, replis tardifs. Le très bon tient ses courses jusqu'à la 90e. **La fatigue dépend de l'effort fourni**, pas seulement de l'horloge : un pressing constant épuise plus vite.
- **Aujourd'hui.** La vitesse baisse avec la minute seule : de 0,60 à 0,97 de la pointe à la 90e, avec un début de baisse entre la 45e et la 75e selon la note. C'est indépendant de l'effort, et comme tout le monde sprinte (T1), il n'y a aucune vraie différence d'effort.
- **Proposition.** Une réserve d'énergie qui se vide selon l'intensité de course (sprints) et se recharge un peu au trot. Stamina règle sa taille et sa recharge. Une réserve basse réduit la pointe ET le nombre de sprints possibles.
- **Critère.** À la 80e, un 88 a encore au moins 90 % de sa pointe, un 55 environ 80 % à effort égal.

### Strength
- **Moyen contre très bon.** Le très bon gagne l'épaule contre épaule, protège le ballon dos au but, sert de point d'appui. Le moyen se fait décaler au contact.
- **Aujourd'hui.** C'est la moitié de la « résistance » du porteur au tacle (avec Balance), dans un duel sans difficulté.
- **Proposition.** Distinguer deux types de duel. Le **duel de contact** (épaule, dos au but) se gagne surtout par Strength. Le **tacle** (pied au ballon) se gagne surtout par Tackling, contre Dribbling/Agility du porteur. Strength pèse aussi pour garder le ballon sous pression.
- **Critère.** Dans un duel de contact à 55 contre 55, environ 50/50 ; à 88 contre 55, environ 75 % pour le plus fort.

### Balance
- **Moyen contre très bon.** Le très bon reste debout et continue son action après un contact. Le moyen tombe ou perd le ballon au moindre accrochage.
- **Aujourd'hui.** C'est l'autre moitié de la résistance au tacle.
- **Proposition.** Balance joue **après** le contact : chance de garder le ballon et de continuer quand le duel est perdu de peu, plutôt que de compter à égalité avec Strength dans le duel lui-même.
- **Critère.** Après un contact perdu de peu, un 88 garde le ballon nettement plus souvent qu'un 55.

---

## 2. Technique

### First Touch (contrôle)
- **Moyen contre très bon.** Sur un ballon facile (passe lente, sans pression), les deux contrôlent. La différence apparaît sur un ballon **rapide, aérien ou sous pression** : le très bon l'amortit et **l'oriente** vers l'espace libre en un temps ; le moyen le contrôle trop loin et met une seconde de plus, le temps que l'adversaire arrive.
- **Aujourd'hui.** Réussite fixe selon la note (55 donne environ 60 %), quelle que soit la vitesse du ballon ou la pression. Un raté renvoie le ballon dans une direction imprévisible.
- **Proposition.** Difficulté = vitesse du ballon + pression + qualité de la passe reçue (dosage). Trois issues au lieu de deux : **contrôle orienté** (il enchaîne), **contrôle simple** (il perd un temps), **contrôle raté** (ballon qui s'échappe). La note règle surtout la part de contrôles orientés.
- **Critère.** Ballon facile : au moins 95 % de contrôles réussis pour tous. Ballon difficile : au moins 25 points d'écart entre 88 et 55. Contrôles orientés : au moins 2 fois plus à 88 qu'à 55.

### Passing
- **Moyen contre très bon.** Voir la discussion du 25/10. Sur les passes faciles, les deux réussissent environ 90 % : la différence est dans le **dosage** (dans la course, à la bonne vitesse). Sur les passes difficiles (longues, sous pression, dans le dos), l'écart est énorme.
- **Aujourd'hui.** Précision fixe : 55 donne environ 60 %, quelle que soit la passe. La vitesse de passe est fixe (15 m/s), donc les passes longues meurent avant d'arriver.
- **Proposition.** Difficulté = distance + pression sur le passeur + adversaires dans le couloir + receveur marqué + passe dans la course. Le **dosage** règle la vitesse et le point d'arrivée devant le receveur, et rend son contrôle plus ou moins facile.
- **Critère (données réelles).** Réussite globale par équipe entre 70 % (équipe faible) et 90 % (équipe de possession), autour de 80 % en moyenne. Passes longues (plus de 32 m) : environ 47 % réussies, et 10 à 19 % des passes. Écart sous pression : **chiffre moyen non trouvé**, à confirmer (référence : les meilleurs passeurs environ 90 % sous pression).

### Technique
- **Moyen contre très bon.** Technique, c'est la gamme de gestes : passe en une touche, extérieur du pied, volée, contrôle en pleine course. Sur un geste simple, aucune différence ; sur un geste **difficile** (ballon rapide, en mouvement, en une touche), le très bon le réussit, le moyen joue simple ou rate.
- **Aujourd'hui.** Moitié de la précision de passe, à égalité avec Passing, sur toutes les passes. Ça dilue Passing et ne reflète pas son vrai rôle.
- **Proposition.** Technique ne joue que sur les **gestes difficiles** : passe en une touche, reprise de volée, contrôle d'un ballon rapide ou aérien. Elle s'ajoute à la difficulté, elle ne fait pas moitié de chaque passe.
- **Critère.** Sur une passe en une touche d'un ballon rapide, au moins 20 points d'écart entre 88 et 55 ; sur une passe simple, quasiment aucun.

### Tackling
- **Moyen contre très bon.** Le très bon choisit le bon moment, gagne le ballon proprement, sans faute. Le moyen plonge trop tôt, se fait éliminer d'un crochet ou fait faute. **Un bon défenseur tacle peu et récupère beaucoup.**
- **Aujourd'hui.** Il y a un duel Tackling (plus un peu d'Aggression) contre Strength/Balance, mais retenté à chaque tick (T2). Le timing n'existe pas, la faute dépend d'Aggression seule, et l'échec du tacle n'élimine jamais le défenseur.
- **Proposition.** Un **duel par confrontation** : le défenseur décide de temporiser ou de tacler, et Tackling règle la qualité du **moment** choisi. Un tacle raté laisse le défenseur éliminé une à deux secondes (il se relève, se retourne). Le porteur oppose Dribbling/Agility, et non Strength. La faute dépend de Tackling (timing) **et** d'Aggression (engagement).
- **Critère (données réelles).** En un contre un face à un dribbleur, un défenseur d'élite gagne 78-87 % des duels, un défenseur faible environ 32 %. Moyenne de la ligue **non trouvée**, à confirmer.

### Finishing
- **Moyen contre très bon.** Face à une occasion **franche** (6 m, seul), le très bon marque environ 2 fois sur 3, le moyen environ 1 fois sur 2. Sur une occasion **difficile** (angle fermé, défenseur au contact, ballon rapide), l'écart explose. La différence est **dans le placement** : le très bon met le ballon loin du gardien, le moyen tire « sur » le gardien.
- **Aujourd'hui.** Finishing compte à 80 % (et Composure à 20 %) dans un duel contre le gardien, multiplié par des facteurs distance et angle. Il n'y a aucune notion de placement, ni de pression défensive.
- **Proposition.** Le modèle se rapproche des xG (buts attendus) réels. La **difficulté du tir** vient de la distance, de l'angle, de la pression et de la partie du corps. **Finishing règle le placement** : la part des tirs cadrés et leur distance au gardien. Le gardien s'oppose ensuite au tir cadré.
- **Critère (données réelles).** Conversion moyenne environ 11 % (hors tirs contrés) ; environ 46 % des tirs cadrés ; grosses occasions converties à environ 41-45 %. L'écart entre un 55 et un 88 sur une grosse occasion est **à confirmer** : il faudra comparer la conversion réelle de finisseurs connus.

---

## 3. Mental

### Aggression (tendance)
- **Moyen contre très bon.** Ce n'est pas une qualité (guide). Un joueur haut engage tôt et fort, récupère plus haut, mais fait plus de fautes et prend plus de cartons. Un joueur bas temporise et laisse jouer.
- **Aujourd'hui.** Règle la fréquence de tentative de tacle **par tick** (T2) et la faute. Les fautes n'ont encore aucune conséquence (pas de coup franc ni de carton).
- **Proposition.** Aggression règle **combien de temps il temporise** avant d'engager, et l'intensité de l'engagement (plus de chances de récupérer, plus de fautes). Les conséquences de la faute (coup franc, carton) viendront en phase 8.
- **Critère.** Un 88 engage environ 2 fois plus tôt et fait au moins 1,5 fois plus de fautes qu'un 30.

### Composure
- **Moyen contre très bon.** Le très bon garde sa précision **sous pression** et dans les moments clés (90e, 1-1). Le moyen se précipite quand un adversaire arrive. **Composure n'ajoute rien quand personne ne presse** : il amortit l'effet de la pression.
- **Aujourd'hui.** Fixé à 20 % de la qualité de tir, toujours, même sans pression. C'est faux dans les deux sens : effet absent sous pression sur les passes et contrôles, effet présent sans pression sur le tir.
- **Proposition.** Composure **réduit la part de difficulté due à la pression**, pour toutes les actions : passe, contrôle, tir, dribble. Sans pression, il ne sert à rien.
- **Critère.** Sous forte pression, la réussite d'un 88 baisse au plus de moitié autant que celle d'un 55 ; sans pression, aucune différence.

### Decisions (ticket 01)
- **Moyen contre très bon.** Le très bon choisit la bonne option et au bon moment (il tire quand il faut, passe quand il faut). Le moyen force : il tire alors qu'un partenaire est seul, ou dribble dans le trafic.
- **Aujourd'hui.** Il prend la meilleure option 95 % (99) / 70 % (55) / 45 % (11), sinon une autre **au hasard**. **Le défaut** : son erreur peut être absurde (tirer à 29 m quand une passe facile existe) aussi souvent qu'une erreur légère.
- **Proposition.** Quand il ne prend pas la meilleure, il prend plus souvent la **deuxième meilleure**, avec une probabilité proportionnelle à la valeur de l'option. Une erreur de décision d'un joueur moyen doit être « crédible », pas absurde.
- **Critère.** Les choix absurdes (option de valeur inférieure au tiers de la meilleure) restent sous 5 % des décisions, même à 30.

### Vision (ticket 02)
- **Moyen contre très bon.** Correct dans le principe : le très bon voit la passe longue et le changement de jeu.
- **Aujourd'hui.** Portée et repérage des passes qui font gagner beaucoup de terrain : c'est conforme. **Limite** : Vision ne voit pas les **couloirs** (passe entre deux adversaires), puisque la difficulté n'existe pas encore (T3).
- **Proposition.** Une fois la difficulté de passe en place, Vision fait repérer les passes **difficiles mais payantes** (entre les lignes) qu'un moyen n'envisage pas.

### Off the Ball (ticket 03)
- **Moyen contre très bon.** Le très bon fait l'appel **au bon moment** (quand le porteur peut donner), dans le dos du défenseur, en restant hors-jeu-proof. Le moyen bouge trop tôt, trop tard, ou pas du tout.
- **Aujourd'hui.** Recherche d'un espace libre toutes les 1 s, sans lien avec le moment où le porteur peut donner, et sans hors-jeu. Effet invisible en match tant qu'il n'y a pas de défense organisée (critère reporté en phase 6).
- **Proposition.** Synchroniser l'appel avec le porteur (l'appel part quand le porteur lève la tête : bon contrôle, pas de pression). Le hors-jeu viendra plus tard ; la qualité d'un appel, c'est aussi de rester en jeu.

### Anticipation (ticket 04)
- **Moyen contre très bon.** Correct dans le principe : le très bon démarre avant les autres.
- **Aujourd'hui.** Lecture d'une passe dans un couloir de 8 m et course vers l'arrivée du ballon libre. **Limite** : à cause de T2 et T3, une lecture mène trop souvent à une interception (ballons perdus).
- **Proposition.** Garder le modèle, mais l'interception passe par la difficulté du contrôle (ballon rapide qui arrive de face : contrôle difficile).

---

## 4. Gardien

### Reflexes
- **Moyen contre très bon.** Le très bon sort les frappes à bout portant et les déviations. Sur une frappe de loin, molle et centrée, aucune différence.
- **Aujourd'hui.** Reflexes compte à 50 % de la note du gardien dans le duel contre le tireur, quelle que soit la frappe.
- **Proposition.** Reflexes joue surtout sur les **tirs proches et rapides** (temps de réaction court). Sur un tir lointain, c'est le placement (Positioning) qui compte.
- **Critère (données réelles).** Pour l'ensemble des gardiens : environ 68 % des tirs cadrés arrêtés en moyenne, de 51,5 % pour le plus faible à 73,5 % pour le meilleur.

### One on Ones
- **Moyen contre très bon.** Le très bon sort au bon moment, ferme l'angle et reste debout le plus longtemps possible. Le moyen plonge trop tôt et se fait dribbler ou lober.
- **Aujourd'hui.** 30 % de la note, sur tous les tirs.
- **Proposition.** One on Ones ne joue **que sur les face-à-face** (tireur seul dans la surface, sans défenseur entre lui et le but).

### Handling
- **Moyen contre très bon.** Le très bon capte. Le moyen repousse devant lui, ce qui offre des secondes occasions.
- **Aujourd'hui.** 20 % de la note, dans la chance d'arrêt ; un tir arrêté donne toujours le ballon au gardien.
- **Proposition.** Handling ne change pas la chance d'arrêter. Il décide de ce qui arrive **après** l'arrêt : captée, repoussée dans l'axe (danger) ou repoussée sur le côté.
- **Critère.** Un 88 capte au moins 2 fois plus souvent qu'un 55 ; les ballons repoussés créent des secondes occasions.

---

## 5. Ordre recommandé

1. **Socle** (T1 intensité de course, T2 un duel par confrontation, T3 fonction de difficulté commune), avec la correction 1 déjà validée : le receveur vient au ballon.
2. **Passe et contrôle** (Passing avec dosage, First Touch avec contrôle orienté, Technique sur les gestes difficiles, Composure sous pression), puis remesurer les ballons perdus (cible 15-20 %).
3. **Duels** (Tackling avec timing, Aggression qui temporise, Strength contre Balance, Dribbling et Agility côté porteur).
4. **Tir et gardien** (Finishing placement, Reflexes/One on Ones/Handling selon le type de tir).
5. **Physique fin** (Acceleration recalée, Stamina par effort).
6. Petites retouches de Decisions (erreurs crédibles) et Off the Ball (appel synchronisé).

À chaque étape : constantes et critères soumis au propriétaire avant le code, et calibration remesurée (tirs, buts, ballons perdus) après.

---

## Sources

- [Biology of Sport, revue 2024 : distances et vitesses en match](https://doaj.org/article/477e7bfef68b49bc83e813929413802a)
- [Silva et al. 2024 : seuils de sprint en match (GNSS)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11167479/)
- [Di Mascio & Bradley 2013 : course à haute intensité en Premier League](https://lida.sport-iat.de/ta/Record/4028632?lng=en)
- [Keiner et al. : sprint en test et vitesse de pointe en match](https://fis.leuphana.de/en/publications/from-the-lab-to-the-field-correlations-between-in-match-running-m/)
- [Slovaquie U21 : temps sur 10 et 30 m](https://library.sk/arl-umb/en/detail-umb_un_cat-0207921-A-level-of-sprint-ability-of-elite-young-football-players-at-different-positions)
- [Whitecaps FC : tests de vitesse sur 30 m](https://vansoccer.deltatre.net/news/numbers-look-some-more-noteworthy-fitness-statistics-season)
- [Opta : passes longues (47,3 % de réussite)](https://www.planetfootball.com/quick-reads/chelsea-man-city-liverpool-revealed-as-premier-leagues-best-long-passers)
- [Opta Analyst : part des passes longues par saison](https://theanalyst.com/articles/premier-league-long-balls-pressing-errors-stats)
- [Bilan 2014-15 : réussite de passes par équipe et par joueur](https://www.arsenalreport.com/posts/end-of-season-premier-league-stats-facts-and-numbers)
- [StatsBomb : passes sous pression (milieux 2022/23)](https://blogarchive.statsbomb.com/articles/soccer/playing-under-pressure-central-midfielders-in-2022-23/)
- [PFF : passes sous pression en Premier League](https://pff.com/news/premier-league-passing-performance-under-pressure-finding-press-resistant-passers)
- [Opta : conversion des tirs 2016/17](https://www.balls.ie/football/zlatan-dreadful-season-according-damning-new-opta-stats-349850)
- [Grosses occasions converties (environ 45 %)](https://arseblog.news/?p=46984)
- [Opta : grosses occasions en MLS (environ 41 %)](https://www.mlssoccer.com/news/armchair-analyst-hardest-thing-do-sports)
- [Opta Analyst : gardiens 2024/25](https://theanalyst.com/articles/premier-league-goalkeeper-stats-2024-25)
- [Premier League : arrêts des gardiens (moyenne environ 68 %)](https://www.premierleague.com/news/638641)
- [Opta Analyst : meilleurs et pires défenseurs en un contre un](https://theanalyst.com/articles/premier-league-best-worst-one-v-one-defenders)
- [Premier League : défenseurs face aux dribbles 2025/26](https://www.premierleague.com/en/news/4461616/opta-analyst-on-quirkier-stats-in-2025-26-including-most-long-throws-and-best-defenders-v-dribbles)
