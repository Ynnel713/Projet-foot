# Audit global de la roadmap V2 et des exigences de réalisme

> 10/11/2026. Mission du propriétaire : vérifier que la roadmap permet d'atteindre un moteur de football réaliste, probabiliste, sensible à la fatigue et aux lois du jeu ; compléter la roadmap sans toucher au code. **Aucun fichier de code n'a été modifié.**
> Référence : moteur à `9eb0869`, plus l'arbre de travail du 10/11/2026 (`v2-realisme/05e` en cours dans `shooting.py`, non touché par cet audit).
> Méthode : lecture de `docs/PLAN_V2.md`, `docs/TRD_V2.md`, `.scratch/v2-realisme/spec.md`, des tickets ouverts des chantiers V2 (descriptions, dépendances, critères) et vérification dans `v2engine/` (recherches et lecture des fonctions concernées).

## 1. Verdict

**Non : la roadmap actuelle, même entièrement livrée, ne remplit pas l'objectif.** Elle est solide sur la structure tactique, le gardien, le tir et la mesure, mais elle laisse quatre trous de fondation :

1. **La fatigue n'existe presque pas.** Aujourd'hui, elle dépend seulement de la minute et de Stamina, et ne réduit que la vitesse maximale (`movement.stamina_factor`, `movement.py:60`). Les tickets prévus (12d à 12f, `v2-collectif/21`, coach `05a`) apportent l'effort et la récupération partielle, mais **aucun ne fait baisser la technique ni la lucidité** d'un joueur fatigué. Un excellent tireur de loin frappe aussi bien à la 85e qu'à la 15e.
2. **Aucun endroit ne permet de distinguer la note du joueur et ce qu'il en exprime à un instant donné.** Chaque module lit la note brute (environ 50 appels dans 12 fichiers, plus 12 lectures directes de Pace, Acceleration et Stamina sur 10 lignes). Sans un point d'entrée unique, la fatigue, la forme du jour et les blessures devraient être rebranchées partout, ticket par ticket : c'est la dette la plus coûteuse si on attend.
3. **L'arbitre n'existe pas : le moteur siffle la vérité.** Toute faute tirée est sifflée, le hors-jeu est jugé sur les positions réelles. Sans écart entre le fait et la décision, la VAR n'a rien à corriger. La V2 n'a **aucun ticket VAR**, ni main, ni simulation, ni passe en retrait au gardien ; la gravité d'une faute est tirée dans des parts fixes, quelle que soit l'action.
4. **Les événements ne sont pas reliés entre eux.** La trace range les événements par type, sans identifiant ni cause. On ne peut pas vérifier une chaîne « passe en retrait → contrôle raté → but », ni synchroniser une animation avec un événement de façon fiable, ni reconnaître un but contre son camp.

**Avec la roadmap révisée (22 tickets ajoutés, 11 complétés, environ 41 h de travail effectif en plus ; 28 tickets et 52 h 35 avec les compléments des §12 et §13 sur le hors-jeu, les coups de pied arrêtés et le gardien), la réponse devient oui**, à trois conditions : la façade des notes (19a) est adoptée par tous les tickets qui suivent ; la calibration finale attend les effets de la condition et les fautes hors du tacle ; l'arbitre (21a) précède les cartons.

**Ce qui est déjà bon, et qu'il ne faut pas refaire** : la courbe partagée qui borne toute réussite entre 5 et 95 % ; les flux aléatoires par sous-système (D-V13) ; la fabrique de scènes et les séries longues avec intervalles de confiance ; l'xG neutre, l'xG après frappe et leur décomposition ; le tir physique (trajectoire, arrêt par portée, contre, déviation) ; un hors-jeu juste (jugé au départ de la passe, hors-jeu passif non sifflé, piège de la ligne, attaquant qui règle son appel) ; la structure par rôles ; le gardien placé.

## 2. Réponse à la précision du propriétaire : quoi faire avant 18a

Il reste avant 18a : `05e` (en cours), puis `05g`. Cet audit ajoute **quatre tickets courts avant 18a** (7 h 40 de travail effectif), tous sans effet sur le jeu, donc sans risque pour les mesures de 18a :

| Ordre | Ticket | Pourquoi avant 18a | Durée |
|---|---|---|---|
| 1 | `v2-realisme/19a` Façade des notes (performance momentanée) | Moins cher maintenant (50 appels et 12 lectures physiques) qu'après les 58 tickets P1 qui vont en ajouter ; pré-requis de toute la fatigue | 2 h 20 |
| 2 | `19c` Garde probabiliste | Vérifie l'exigence centrale (jamais infaillible, jamais incapable) sur toutes les résolutions, et nourrit le rapport 18a | 1 h 30 |
| 3 | `19b` Journal des événements et causes | 18a doit attribuer les écarts à des mécanismes : il faut savoir d'où vient chaque but | 2 h 05 |
| 4 | `19d` Banc : rendement par tranche de 15 minutes | 18a doit dire ce que la fatigue change aujourd'hui avant qu'on construise 12d, 12e et 20 | 1 h 45 |

19a, 19b et 19c touchent des fichiers que `05e` modifie : ils attendent son commit. 19d peut partir tout de suite (banc seulement).

**Juste après 18a, avant 18d** : `12d` (intensité par rôle) puis `12e` (réserve d'énergie), promus P0. Raison : 18d calibre les volumes de course ; le faire alors que toutes les intentions visent la vitesse maximale et que la fatigue ne dépend que de la minute masquerait deux mécanismes absents, ce que la règle des calibrations provisoires interdit.

Ordre résultant : `05e` → `05g` ; `19d` dès maintenant ; `19a` → `19c` → `19b` → **18a** → `12d` → `12e` → **18d** → **18e** → P1.

## 3. Matrice de couverture

Statuts : **C** couvert (livré ou ticket ouvert suffisant) · **P** partiel · **A** absent · **V** à vérifier techniquement. « Après » : tickets qui couvrent la lacune après l'audit (nouveaux en gras).

### 3.1 Principe probabiliste (exigence 3)

| Fonctionnalité | État | Où / tickets | Lacune | Action |
|---|---|---|---|---|
| Notes = probabilités, jamais 0 ni 100 % | P | `attributes._cubic_curve` (5-95 %) | passe et contrôle en tout ou rien ; passe ratée : point visé décalé de 10 à 25 % de la distance dans une direction aléatoire (au plus environ 15° d'écart au départ), ampleur indépendante de la note ; arrêt déterministe à position donnée ; quelques bornes 0-1 | **19c** (garde), puis correction par ticket (`03b` complété, `32a`/`36a`, voir §7.2) |
| Distribution d'issues (exceptionnel → raté) | P | tir : écart gaussien (35b), xG après frappe (06a) ; passe : non | passes et centres sans dispersion continue | voir §7.2 (recommandation : reprendre le principe du 35b dans `32a` et `v2-attributs-restants/11`) |
| Contexte de l'action (distance, angle, pression, pied, équilibre) | P | tir et passe : distance, pression, Composure ; pied : `04a` ; équilibre : `12c` ; orientation : `07` | fatigue absente du contexte | **20a** |
| Pas de bonus / malus empilés | C | règle anti double comptage (`v2-collectif/18`, carte des attributs) | — | rejouer la garde après chaque calibration (22a complété) |
| Reproductible par graine, analysable en masse | C | D-V13, `01e`, `06b`, `06c` | — | — |
| Forme du jour (« un bon joueur passe à côté de son match ») | A | — | chaque match moyenne la chance ; aucune variance par match | **20f** |

### 3.2 Fatigue, condition, remplacements (exigence 4)

| Fonctionnalité | État | Où / tickets | Lacune | Action |
|---|---|---|---|---|
| Attribut intrinsèque distinct de la performance momentanée | A | note lue brute partout | pas de point d'entrée | **19a** |
| Fatigue selon l'effort | A (prévu) | `12d`, `12e` | — | promus P0 avant 18d |
| Fatigue explosive (répéter les sprints) | A (prévu) | `12f` | — | — |
| Dimensions de fatigue | — | — | recommandation : deux composantes (endurance 12e, explosivité 12f) ; fatigue mentale portée par la lucidité (20b) ; pas de variable musculaire séparée (aucune différence observable distincte) | complément 12e |
| Effet sur les capacités physiques | P | vitesse maximale seulement | accélération, freinage, duels | 12e (vitesse), 12a et 11b lisent la façade ; **20a** pour le tacle |
| Effet sur la technique | A | — | passes, contrôles, frappes, centres, tacles | **20a** |
| Effet sur la lucidité et les décisions | A | `21` le mentionne sans critère | Concentration non lue | **20b** ; `21` recentré |
| Récupération (arrêts, mi-temps) | A | `12e` « au repos » ; mi-temps : `coach/07` point 6 renvoyé | arrêts de jeu, pause | **20c** |
| Remplacements | A (prévu) | coach `05a`, `05b` | aucun critère « remplaçant frais contre titulaire fatigué » | `05a` complété ; **20d** |
| Conséquences tactiques de la fatigue | A | — | bloc, pressing | **20e** (sans seuil, par la capacité restante) |
| Fatigue et blessures | A | `09b` : contact seulement | sans contact, coups, crampes | **20g** ; `09b` complété |
| Tests A/B de fatigue | A | — | les cinq comparaisons demandées | **19d** (état des lieux), **20d** (validation) |

### 3.3 Événements footballistiques (exigence 5)

| Fonctionnalité | État | Où / tickets | Action |
|---|---|---|---|
| Passes trop courtes / trop appuyées | P | dosage ± 5 à 30 % (`possession.pass_velocity`) | dispersion continue (§7.2) ; `36a`, `36b` |
| Passes imprécises | P | ratée = point visé décalé de 10 à 25 % de la distance (au plus environ 15° au départ), ampleur indépendante de la note ; issue binaire | §7.2 |
| Mauvais contrôle, contrôle trop long | P | contrôle raté dévié de 20 à 60° (`missed_control_velocity`) ; touche trop longue en conduite (`04b`) | `31`, `07c`, `07d`, `04e` |
| Centres courts, longs, dévissés, 2e et 3e poteau | A (prévu) | `v2-attributs-restants/01`, `11` | dispersion continue à exiger (§7.2) |
| Frappes écrasées, dévissées, trop puissantes, contrées | P | cadrage et dévissé (35b), contre physique (05c) ; puissance `35a` ; au-dessus `05f` | — |
| Déviations involontaires, rebonds | C / A | déviation au contact (05d) ; rebond : `v2-hauteur-ballon/02a`, `14c` | — |
| Mauvaise remise, dégagement raté | A (prévu) | tête : `15c`, `15d` ; relance gardien : `03c` | — |
| Erreurs défensives (alignement, dos, couverture, marquage) | P | ligne avec retard (Teamwork), marquage (07), perception `08e` ; couverture `10b`, `10c` | — |
| Tacle manqué, défenseur éliminé sur crochet | P | tacle debout ; crochet `04h`, contournement `04g`, glissé `04j` | — |
| Collision entre coéquipiers | P | collisions symétriques (`match.py:114`) ; `11a`, `11b` | — |
| But contre son camp | V | possible physiquement (05d) mais non reconnu | **19b** |
| Faute inutile | A | — | **21c** (faute tactique, tirage de maillot) |
| Gardien : placement, sorties, face-à-face | C | `03a` à `03k` | — |
| Gardien : boulettes, ballon relâché, mauvaise appréciation | P | capté / repoussé / claqué selon la difficulté, gardien neutre | `v2-attributs-restants/03b` complété |
| Gardien : relance ratée, sortie au pied, passe en retrait | A (prévu en partie) | `03c` ; règle de la passe en retrait absente | **21e** |
| Gardien : double parade, parade réflexe | P | second ballon après repoussé (28b) ; réflexe : `03b` | — |
| Hors-jeu : jugement, passif, piège, appel réglé | P (corrigé au §12 : rebond après un tir, déviation contre jeu volontaire, gêne d'un adversaire) | `v2-collectif/23`, `offside.py` | **21i** |
| Appels en arc, temporisés, dans les intervalles | P | appels dans le dos (16), délai Off the Ball (02g) | **09i** ; intervalles `09c`, `09e` |
| Défenseur qui décroche involontairement | C | retard de ligne selon Teamwork (`bloc.py`) | — |
| Fautes, avantage, penalty | P | fautes de tacle seulement (9,4 par match contre 21-26) ; avantage selon le danger | **21c** |
| Gravité, jaune, 2e jaune, rouge direct | A (prévu) | `09a` ; gravité en parts fixes | **21b** ; `09a` complété |
| Main, simulation | A | — | **21d**, **21f** |
| Arbitre qui se trompe | A | — | **21a** |
| VAR | A | aucun ticket V2 | **21g**, **21h** |
| Blessures | A (prévu) | `09b` | **20g** |
| Échauffourées | A (prévu) | `09c` | — |
| Comportements humains (protestations, encouragements…) | A | célébrations `v2-mise-en-scene/04` | **`v2-mise-en-scene/06`** |

### 3.4 Tactique collective (exigence 6)

| Fonctionnalité | État | Tickets | Remarque |
|---|---|---|---|
| Permutations, décrochages, appels croisés, latéraux intérieurs / débordants | P | rôles 02c à 02g livrés ; `09b` à `09d`, `16`, `17`, `19` | couvert par la roadmap |
| Compensations, couverture des latéraux | C / P | `v2-collectif/09`, `10i` | — |
| Hauteur du bloc, pressing coordonné, déclencheurs | C | `05`, `08`, `10a` | — |
| Changements selon le score | A (prévu) | `21`, coach `02`, `04` | — |
| Transitions | C | `10`, `11` | — |
| Influence de la fatigue sur le bloc | A | — | **20e** |
| Sortir de sa position sans systématisme | P | rôles + tendances `19` (Flair) | couvert |

### 3.5 Rendu (exigence 7)

| Fonctionnalité | État | Tickets | Action |
|---|---|---|---|
| Ballon qui monte et descend, rebonds | A (prévu) | `v2-hauteur-ballon/02a`, `02b` | — |
| Filets qui réagissent | A | filet dessiné, fixe | **`v2-mise-en-scene/05`** |
| Chutes, glissades, tacles, plongeons | A | — | **`v2-mise-en-scene/05`** |
| Célébrations | A (prévu) | `v2-mise-en-scene/04` | — |
| Réactions (erreur, occasion, décision) | A | — | **`v2-mise-en-scene/06`** |
| VAR, soins, remplacements à l'écran | A | — | critère « visible à l'écran » dans 21g, 20g, coach 05a |
| Animation seulement si l'événement a eu lieu | P | règle « visible à l'écran » du 03/11 | garantie par le journal **19b** |

### 3.6 Doublons et recouvrements relevés

- `v2-collectif/12` (chapeau) et `v2-realisme/12d` à `12f` : déjà réglé par la découpe du 05/11.
- `v2-collectif/21` et le nouveau `20b` : la partie « fatigue → choix » passe au 20b ; 21 garde le score, la minute et Determination. Complément écrit dans 21.
- `v2-attributs-restants/09b` et le nouveau `20g` : contact d'un côté, charge de l'autre. Complément écrit dans 09b.
- Tickets `but-refuse`, `var-intervention-favorable`, `carton-rouge-autonome` : chantiers V1 (moteur Poisson), sans recouvrement avec la V2.

## 4. Fondations techniques

| Système | État vérifié | Risque | Décision |
|---|---|---|---|
| Événements | Listes typées dans `MatchTrace` ; pas d'identifiant, pas de cause ; boucle unique `simulate_match` → `_step_ball` (ordre fixe, donc pas de vraie simultanéité à gérer) | chaque nouveau type ajoute une liste ; tests de causalité impossibles | **19b** : journal additif, sans réécrire la trace |
| Décision | Valeur réelle et perception (33), pression, risque de conduite unifié (04a), tir aligné sur la résolution (05e) | ne lit ni fatigue ni forme | **20b**, **20f** par la façade |
| Probabiliste | Courbe partagée, flux nommés, xG décomposé | résolutions en tout ou rien hors tir | **19c** |
| Physique | Cinématique (25), tir physique, déviation ; collisions symétriques ; freinage commun | prévu (11, 12, 14, hauteur) | inchangé |
| Fatigue | Fonction de la minute, vitesse seulement | absence de couche « condition » | **19a**, puis 12d, 12e, 20a à 20g |
| Règles | Hors-jeu juste ; faute = vérité ; gravité en parts fixes ; temps additionnel avec fond « VAR, blessures, cartons » | VAR impossible tant que fait = décision | **21a** avant 09a ; 21b à 21h |

**Décision d'architecture à acter (recommandation) : la couche « condition ».**
- Option A, une façade unique `condition.effective_rating` (19a) : un seul endroit module la note exprimée, par famille d'attributs, y compris Pace, Acceleration et Stamina, aujourd'hui lus comme champs de `PlayerState` dans 6 modules. Avantages : chaque effet n'est écrit qu'une fois, la règle anti double comptage se vérifie au même endroit, un test statique empêche les contournements (appels à `player_attribute` et lectures de `.pace`, `.acceleration`, `.stamina` hors `movement.py` et `condition.py`). Risque : un appel de plus par lecture (coût faible, les courbes sont déjà en cache).
- Option B, chaque ticket ajoute sa fatigue dans son module. Avantage : pas de refonte. Risques : effets dispersés, oubli d'un module, double comptage, coût qui grandit avec chaque ticket P1.
- **Recommandation : A, maintenant**, tant qu'il n'y a que 50 appels et que le comportement ne change pas (traces identiques, vérifiable).

**Décision d'architecture à acter (recommandation) : l'arbitre perçoit.** Le moteur produit le fait réel ; un arbitre placé sur le terrain en tire une décision (vue, angle, distance) ; la VAR compare les deux. Sans cette séparation, une VAR ne pourrait qu'être un tirage déguisé, ce que la règle de diversité du 03/11 interdit.

## 5. Système probabiliste : analyse

- **Les notes ne sont jamais des garanties** : vrai pour toute action qui passe par `success_probability` ou `duel_probability` (bornes 5-95 %). **Faux ou non vérifié** pour : l'arrêt du gardien (déterministe à position donnée depuis 05h, et notes du gardien sans effet, constat 06b et 06c) ; la passe, réussie ou ratée en tout ou rien, dont l'erreur une fois ratée (10 à 25 % de la distance, `possession.pass_aim`) ne dépend pas de la note ; `dosage_quality` (0 à 1). 19c les liste ; `03b` est complété.
- **Exploits des joueurs moyens** : possibles au tir (écart gaussien : une frappe peut finir en lucarne quelle que soit la note). Non mesurés : 19c ajoute la vérification des queues.
- **Erreurs des meilleurs** : possibles partout sauf l'arrêt (voir ci-dessus).
- **La fatigue modifie les distributions** : non, sauf la vitesse. 20a et 20b.
- **Les circonstances comptent** : oui (pression, distance, angle, contreurs, gardien, orientation à venir).
- **La hiérarchie est respectée** : oui en moyenne (06b : gain d'exécution 99 contre 11 de + 0,148 par tir pour Finishing).
- **Les événements rares restent rares** : non mesuré pour les événements à venir ; les tickets 20g, 21d, 21f, 21g exigent des séries de 200 à 1 000 matchs (01e le permet).

## 6. Fatigue et remplacements : analyse

État : la fatigue est une courbe fixe (début de la baisse entre la 45e et la 75e selon Stamina, plancher de 60 à 97 % de la vitesse maximale à la 90e), identique pour un joueur qui a sprinté 90 minutes et pour un joueur qui a marché. Il n'y a ni remplacement, ni récupération, ni effet sur la technique, les décisions ou le bloc.

Après la roadmap révisée :
- **effort** : 12d (intensité par rôle), 12e (réserve), 12f (sprints répétés) ;
- **expression** : 19a (façade), 20a (technique), 20b (lucidité, Concentration dans sa condition), 20f (forme du jour) ;
- **récupération** : 20c (arrêts, mi-temps, plafond par l'effort cumulé) ;
- **collectif** : 20e (bloc et pressing par la capacité restante, sans seuil) ; coach 13b (style Pressing qui use l'équipe) ;
- **remplacements** : coach 05a (mécanique, sortant le plus fatigué), 05b (choix tactiques), critères ajoutés « remplaçant frais contre titulaire fatigué » et « dynamique après le changement » ;
- **blessures** : 09b (contact), 20g (charge, coups, crampes), jamais automatiques ;
- **validation** : 19d (état des lieux), 20d (cinq comparaisons A/B demandées, plancher « jamais inutilisable »).

Règle de non double comptage : Stamina n'agit qu'à un endroit, la réserve (12e). Tous les effets de fatigue lisent la réserve, jamais Stamina.

## 7. Modifications de la roadmap

### 7.1 Nouveaux tickets (22, 41 h 10 de travail effectif)

| Ticket | Titre | Prio | Durée | Dépend de |
|---|---|---|---|---|
| `v2-realisme/19a` | Performance momentanée : façade des notes | P0 | 2 h 20 | 05e |
| `19b` | Journal des événements et chaîne de causes | P0 | 2 h 05 | 05e |
| `19c` | Garde probabiliste : jamais infaillible, jamais incapable | P0 | 1 h 30 | 05e |
| `19d` | Banc : rendement selon la minute | P0 | 1 h 45 | 01d, 01e (livrés) |
| `20a` | La fatigue dégrade l'exécution technique | P1 | 2 h | 19a, 12e |
| `20b` | La fatigue dégrade la lucidité | P1 | 2 h | 19a, 12e |
| `20c` | Récupération : arrêts de jeu et mi-temps | P1 | 1 h 30 | 12e |
| `20d` | Validation fatigue et remplacements | P1 | 1 h 30 | 19b, 19d, 20a, 20b, 20c, 12f |
| `20e` | Bloc et pressing selon la capacité restante | P1 | 2 h | 12e, 10a, 10c, 13b |
| `20f` | Forme du jour | P1 | 1 h 45 | 19a, 01e |
| `20g` | Blessures sans contact, coups, crampes | P2 | 2 h | 12f, 19a, 09b |
| `21a` | L'arbitre décide sur ce qu'il voit | P1 | 2 h 05 | 19b |
| `21b` | Gravité de la faute selon l'action | P1 | 2 h | 11d, 04j |
| `21c` | Fautes hors du tacle | P1 | 2 h | 11c, 04g, 04i, 21b |
| `21d` | La main | P2 | 2 h | hauteur 02a, réalisme 07a, 21a |
| `21e` | Passe en retrait au gardien | P1 | 1 h 30 | 03c ou 32a |
| `21f` | Simulation | P2 | 1 h 45 | 21a, 09a |
| `21g` | VAR : buts et penalties | P2 | 2 h 10 | 21a, 21d, 21f, 19b, 09a |
| `21h` | VAR : rouge direct et identité | P2 | 1 h 30 | 21g, 21b, 09a |
| `09i` | Appels en arc et temporisés | P1 | 1 h 45 | 07e, 08e, 02g |
| `v2-mise-en-scene/05` | Gestes visibles : chute, glissé, plongeon, filet | P3 | 2 h | 19b, hauteur 02b, 04j |
| `v2-mise-en-scene/06` | Réactions des joueurs | P3 | 2 h | 19b, 04, 21a |

P0 : 4 tickets, 7 h 40 · P1 : 11 tickets, 20 h 05 · P2 : 5 tickets, 9 h 25 · P3 : 2 tickets, 4 h. Temps machine à part (séries de 50 à 1 000 matchs).

### 7.2 Tickets complétés (section « Complément de l'audit de la roadmap (10/11/2026) » ajoutée en fin de fichier, lignes de dépendances étendues avec la mention « ajouté le 10/11/2026 »)

| Ticket | Modification |
|---|---|
| `v2-realisme/18a` | bloqué aussi par 19a à 19d ; trois sections de rapport en plus (condition, garde, causalité) |
| `v2-realisme/18d` | bloqué aussi par 12d et 12e |
| `v2-realisme/12d`, `12e` | promus P0, avant 18d ; 12e : réserve dans `PlayerCondition`, Stamina n'agit qu'ici, deux composantes seulement, test « sollicité contre économe » |
| `v2-collectif/21` | bloqué par 20b ; la fatigue sur les choix passe au 20b |
| `v2-collectif/22a` | bloqué aussi par 20a, 20b, 20c, 20d, 20f, 21c, 19c |
| coach `05a` | bloqué par 12e et 20c ; critères « remplaçant frais contre titulaire fatigué » et « dynamique après le changement » |
| `v2-attributs-restants/09a` | bloqué par 21b (et 21a recommandé) ; carton sur la décision de l'arbitre |
| `v2-attributs-restants/09b` | bloque 20g ; périmètre contact seulement |
| `v2-attributs-restants/03b` | bloqué par 18e ; notes du gardien dans la portée physique, centrées sur le gardien calibré ; boulettes possibles même à 99 |
| `v2-mise-en-scene/02` | moments VAR ajoutés à la livraison de 21g et 21h |

**Recommandation non appliquée (décision du propriétaire)** : la passe et le centre devraient, comme le tir depuis le 35b, avoir une erreur d'exécution continue (direction et dosage tirés autour de la cible, plus larges si la note est basse ou le joueur fatigué) au lieu du « réussi ou dévié au hasard ». C'est ce qui fait naître naturellement les passes trop courtes, trop appuyées et les centres au troisième poteau. Deux options : l'ajouter au `v2-collectif/32a` (passes) et au `v2-attributs-restants/11` (centres), ou créer un ticket dédié avant eux. Recommandation : **ticket dédié**, parce que 32a et 11 traitent du choix du type de passe, pas de son exécution ; la constatation 19c le chiffrera d'abord.

### 7.3 Tickets qui peuvent attendre

Ballon avancé (14a à 14d), coups de pied arrêtés travaillés (16), Bravery et Leadership (17b, 17c), échauffourées (09c), main, simulation et VAR (21d, 21f à 21h), immersion (`v2-mise-en-scene/05`, `06`), écran Match (déjà en attente).

## 8. Dépendances réorganisées et roadmap priorisée

**P0, fondations (reste environ 18 h de travail effectif sur ce chemin, hors fin du 05e et hors orientation et prise d'information)**
1. `05e` (en cours) → `05g`
2. `19d` (en parallèle, banc seulement)
3. `19a` → `19c` → `19b` (après le commit du 05e)
4. **18a** (point d'étape, rapport complété)
5. `12d` → `12e` (promus)
6. **18d** → **18e**
7. Orientation et prise d'information P0 déjà prévues (`07a`, `07c`, `07e`, `07f`, `08a` à `08c`) : inchangées, avant `v2-collectif/31`.

**P1, réalisme fondamental** (ordre du spec v2-realisme section 6, avec les insertions suivantes)
- condition : `20a`, `20b`, `20f` dès 12e livré ; `20c` ; puis `12f` → `20d` (en scène, sans attendre coach `05a`, qui dépend de `v2-attributs-restants/04b`, placé après la calibration finale) ;
- arbitrage : `21a` tôt (il ne dépend que de 19b) ; `21b` après 11d et 04j ; `21c` après 11c, 04g, 04i ; `21e` avec 32a ou 03c ; puis `v2-attributs-restants/09a` ;
- tactique : `09i` dans le domaine 09 ; `20e` après 13b ;
- gardien : `v2-attributs-restants/03b` après 18e.

**Calibration finale** : `v2-collectif/22a` → `22b` → `22c`, après les P1 ci-dessus ; garde 19c rejouée après chaque lot ; puis `18c` (validation indépendante).

**P2** : `20g`, `21d`, `21f`, `21g`, `21h`, plus les P2 existants. **P3** : `v2-mise-en-scene/04` à `06`, écran Match.

## 9. Risques techniques

| Risque | Probabilité | Effet | Parade |
|---|---|---|---|
| La façade 19a contournée par un ticket futur | moyenne | effets de fatigue incomplets | garde statique dans 19a ; critère « façade » dans les tickets 20 |
| Double comptage de la fatigue (Stamina lue à plusieurs endroits) | moyenne | joueurs à Stamina basse inutilisables | Stamina n'agit que dans 12e (complément écrit) ; 20d vérifie le plancher |
| Les calibrations provisoires 18d et 18e invalidées par 20a et 20b | élevée | réglages à refaire | assumé : ce sont des valeurs provisoires ; la finale (22) vient après 20 |
| Coût de calcul (orientation, vision, arbitre, journal) | moyenne | rejeu en direct plus lent | mesure du temps par match exigée dans 07a, 08a ; à ajouter à 21a et 19b si le surcoût dépasse 5 % |
| Fichiers partagés (`match.py`, `decision.py`, `cerveau.py`) | élevée | sessions qui se bloquent | séquentiel, comme aujourd'hui ; 19d, 20d, 21a sont les plus indépendants |
| Événements rares impossibles à calibrer sur 50 matchs | élevée | fréquences fausses | séries de 200 à 1 000 matchs exigées dans les tickets concernés |
| Le volume de la roadmap (environ 250 h) use la motivation | moyenne | abandon | P0 court (environ 18 h jusqu'à 18e), puis des lots qui se voient à l'écran |
| Constantes non sourçables (erreurs d'arbitrage, simulation, forme du jour) | élevée | valeurs arbitraires | « non trouvé » assumé, marqué hypothèse, une constante par mécanisme |

## 10. Tests et calibration

- **Tests probabilistes** : 19c (garde sur toutes les résolutions), 06b et 06c (décomposition et courbe de calibration de l'xG), séries longues 01e.
- **Tests de fatigue** : 19d (état des lieux), tests de scène des 12e, 12f, 20a à 20c, validation 20d (cinq comparaisons).
- **Tests tactiques** : 02h, 09h, 10j, 13i existants ; 20e (bloc et fatigue) ; 09i (appels en arc et hors-jeu).
- **Tests réglementaires** : scènes de la loi 12 dans 21b, 21d, 21e, 21f ; VAR 21g, 21h ; hors-jeu existant.
- **Tests de causalité** : 19b (chaîne de la scène de référence), 20d (chaîne « fatigue défensive → appel → occasion »), 21g (VAR qui remonte la phase d'attaque).
- **Calibration** : repères sourcés du 01c ; provisoires 18d, 18e ; finale 22a à 22c sur au moins 500 matchs ; validation indépendante 18c sur graines réservées. Chaque valeur est classée : mesurée (sourcée), hypothèse de conception, provisoire (datée), validée. Aucune statistique de référence n'est inventée : « non trouvé » quand aucune source n'existe.

## 11. Traçabilité

- Nouveaux fichiers : `.scratch/v2-realisme/issues/19a` à `19d`, `20a` à `20g`, `21a` à `21h`, `09i` ; `.scratch/v2-mise-en-scene/issues/05`, `06` ; ce rapport.
- Fichiers complétés (ajouts seulement, aucun texte supprimé) : voir §7.2 ; lignes « Bloque » (ou « Blocked by » pour 09h) prolongées avec la mention datée, pour que les liens soient lisibles dans les deux sens : `v2-realisme/04g`, `04i`, `04j`, `07e`, `08e`, `09h`, `11c`, `11d`, `12e`, `12f`, `13b`, `v2-attributs-restants/09a`, `v2-collectif/22b` ; `.scratch/v2-realisme/spec.md` (section 11) ; `docs/PLAN_V2.md` (paragraphe « Audit de la roadmap »).
- Aucun ticket livré modifié ; aucun ticket supprimé ; aucun fichier de code modifié.

## 12. Complément : hors-jeu et coups de pied arrêtés (10/11/2026, question du propriétaire)

Relecture ciblée de `offside.py`, `restart.py` et `match.py` (`_play_restart`, `_award_offside_free_kick`, passage du tir), puis des tickets 16a à 16g, `v2-attributs-restants/02a` et `02b`. Le §3.3 classait le hors-jeu « couvert » : c'était trop rapide.

**Hors-jeu.** Juste aujourd'hui : jugement au départ d'une passe (coup franc joué en passe compris), tolérance de 0,3 m, hors-jeu passif non sifflé, pas de hors-jeu sur touche, sortie de but ni corner, piège de la ligne avec retard selon Teamwork, appel réglé par Off the Ball, passeur qui lit la ligne avec une erreur selon Vision, environ 3,1 hors-jeu par match (réel 3,2 à 3,5). Absent :

| Cas de la loi 11 | État vérifié | Ticket |
|---|---|---|
| Attaquant hors-jeu au moment d'un tir, qui reprend le ballon repoussé ou renvoyé par un poteau | A : le tir efface le signalement (`match._step_ball`, branche du tir) ; but accordé à tort | **21i** |
| Ballon dévié par un adversaire (le hors-jeu tient) ou joué volontairement par lui (il tombe, sauf arrêt volontaire, par n'importe quel joueur) | A : non distingué (`offside.py`, « Non modélisé ») ; la déviation existe depuis 05d | **21i** |
| Gêne d'un adversaire sans toucher le ballon (devant le gardien, ballon disputé) | A | **21i** |
| Sanction par coup franc indirect | A : le hors-jeu rend le ballon en jeu au défenseur le plus proche (`match._award_offside_free_kick`, « coup franc indirect simplifié »), sans ballon mort ni placement ; aucune faute ne donne d'indirect | **16h** |

**Coups de pied arrêtés et touches.** Aujourd'hui : chacun reste à sa place dans le bloc, les adversaires repoussés à la distance réglementaire (`restart.place`) ; le preneur est le joueur le plus proche (`restart._taker`) ; le corner et la touche sont joués comme une passe ; le coup franc est frappé ou passé par le preneur, sans mur ; le penalty est provisoire (78 %, sans attribut). Couverture par la roadmap :

| Fonctionnalité | État | Tickets | Action |
|---|---|---|---|
| Placement offensif sur corner | A (prévu) | 16a | — |
| Défense de corner en zone, individuelle ou mixte | A (prévu) | 16b | — |
| Appels et écrans sur corner | A (prévu) | 16c | — |
| Exécution du corner (zone, rentrant, sortant, court) | A (prévu) | 16d | tireur par **16j** |
| Mur et coup franc direct | A (prévu) | 16e | tireur par **16j** |
| Touche longue | A (prévu) | 16f | tireur par **16j** |
| Penalty : tireur, frappe, rebond | A (prévu) | `v2-attributs-restants/02a` | tireur par **16j** ; empiètement et gardien avancé (loi 14) ajoutés au 02a |
| Coup franc indirect (hors-jeu, passe en retrait, jeu dangereux) | A | — | **16h** |
| Coup franc centré : placement, ligne défensive, hors-jeu | A | 16a et 16b ne traitent que le corner | **16i** |
| Choix des tireurs (une table par équipe, mise à jour après un changement) | A | chaque ticket refaisait « le meilleur » | **16j** |
| Touche ordinaire : appels, marquage ; remise rapide | A | — | **16k** |
| Balle à terre après un arrêt pour soins (loi 8) | A | — | ajoutée au `v2-attributs-restants/09b` |
| Seconds ballons, jeu aérien | A (prévu) | 15a à 15f | — |
| Validation | A (prévu) | 16g | bloqué aussi par 16i et 16k |

**Nouveaux tickets (5, 9 h 25)** : `v2-realisme/21i` hors-jeu, cas de la loi 11 absents (P1, 2 h, dépend de 19b, 21a, 16h) ; `16h` coup franc indirect, le hors-jeu en vraie remise en jeu (P2, 2 h 10, prêt) ; `16i` coup franc centré (P2, 2 h, dépend de 16a, 16b, 16e, 16h) ; `16j` tireurs désignés (P2, 1 h 30, prêt) ; `16k` touche ordinaire et remise rapide (P2, 1 h 45, prêt). Liens réciproques ajoutés, avec la mention datée, dans 16a, 16b, 16d, 16e, 16f, 16g, `v2-attributs-restants/02a` et `09b` (tous à faire), et dans les tickets ouverts 19b, 21a, 21e, 21g (créés au premier passage de l'audit).

**Totaux après ce complément** : 27 tickets, 50 h 35 de travail effectif (P0 4 tickets, 7 h 40 ; P1 12 tickets, 22 h 05 ; P2 9 tickets, 16 h 50 ; P3 2 tickets, 4 h).

**Ordre** : 16h et 16j peuvent partir tout de suite (16j avant le penalty `02a`) ; 21i après 21a ; 16i et 16k avec le lot des coups de pied arrêtés, avant la validation 16g.

## 13. Complément : le gardien battu sans plonger, et le dribble du gardien (10/11/2026, question du propriétaire)

**Un gardien peut-il encaisser sans plonger, pris à contre-pied ou figé sur une frappe parfaite ?** Dans le résultat, oui : depuis le tir physique (05b, 05h), le but est marqué quand l'écart entre le ballon et le gardien dépasse sa portée au passage du ballon (1 m sans plonger, puis 3 m/s après 0,30 s, jusqu'à 2,8 m ; `shooting.keeper_reach_m`). Une lucarne opposée à bout portant est donc imparable. Mais le gardien n'a aucune décision : il ne devine jamais un côté, il ne peut pas partir du mauvais côté (sauf sa vitesse au moment du tir, prévue au 03f), et rien ne distingue « il plonge et ne l'a pas » de « il ne bouge pas » : la trace ne garde que l'écart et le temps de vol. La tête croisée à bout portant n'existe pas encore (jeu aérien, 15a à 15c). **Nouveau ticket `v2-realisme/03l`** (P1, 2 h) : anticipation d'un côté selon la lecture du tireur (Anticipation pour la justesse, Eccentricity pour la tendance à partir tôt), contre-pied qui réduit la portée de l'autre côté, gardien figé quand le ballon arrive avant sa réaction ou qu'il est pris à contre-pied ou masqué, plongeon en vain sinon (décision sur ce qu'il perçoit au départ du tir) ; réaction tracée et montrée à l'écran (`v2-mise-en-scene/05`, complété).

**Un dribbleur peut-il éliminer le gardien en face-à-face, avec une faute possible (penalty, expulsion) ?** Partiellement, et pas avec les bons attributs. Le dribble du gardien n'existe que comme une conduite ordinaire autour de lui ; le gardien, s'il est à portée du porteur, intervient avec le tacle des joueurs de champ (tentative selon Aggression, réussite selon Tackling, faute environ 30 % des tacles). Une faute dans la surface donne déjà un penalty, mais sans carton (cartons : `v2-attributs-restants/09a`). Le ticket `v2-attributs-restants/10b` (lob et dribble du gardien, après la calibration finale) prévoyait le dribble par Dribbling contre One on Ones, sans la faute. **Complété** : intervention du gardien par One on Ones (et Bravery, 17b) au lieu de Tackling et Aggression ; faute du gardien sanctionnée selon `v2-realisme/21b` (jaune dans la surface s'il tente de jouer le ballon, rouge sinon ; rouge hors de la surface) ; finition après le dribble encore incertaine (but vide, angle fermé, défenseur sur la ligne). Bloqué aussi par 21b.

**Le piqué par-dessus le gardien en face-à-face** (ajout du propriétaire) : prévu au même ticket `v2-attributs-restants/10b` comme un lob générique ; **précisé** comme une option de plus dans le choix de la finition (10a), jamais imposée : intéressant surtout quand le gardien sort ou se couche tôt (03l, 03e) ; réussite selon Technique et Composure ; Flair et « Likes To Lob Keeper » ne changent que la fréquence ; ratés physiques (trop long, trop court, à côté) avec la hauteur du ballon (`v2-hauteur-ballon/02a`) et la portée du gardien (05b) ; fréquence rare, rapportée sur 500 matchs sans réglage. 10b dépend aussi de 03l et de `v2-hauteur-ballon/02a`.

Liens ajoutés, avec la mention datée : 03f et `v2-attributs-restants/03b` bloquent 03l ; `v2-mise-en-scene/05` dépend de 03l.

**Totaux après les compléments des §12 et §13** : 28 tickets, 52 h 35 (P0 4 tickets, 7 h 40 ; P1 13 tickets, 24 h 05 ; P2 9 tickets, 16 h 50 ; P3 2 tickets, 4 h).
