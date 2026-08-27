# Simulafoot 2026-2027

Mini application web qui simule soit une saison complète d'un grand
championnat européen (Premier League, LaLiga, Bundesliga, Serie A, Ligue 1,
Liga Portugal, Jupiler Pro League, Eredivisie), soit une **Compétition
Perso** entièrement personnalisée (championnat libre, élimination directe,
ou hybride façon Coupe du Monde, avec les clubs de ton choix, y compris ceux
d'"Autres clubs" hors des 8 championnats officiels). Calendrier généré
automatiquement, simulation au niveau **joueur** (pas juste un score de
club) : dispositif tactique adapté à chaque effectif, compos réalistes,
buteurs/passeurs, notes /10, cartons, suspensions, blessures et
remplacements, classement et classements buteurs/passeurs mis à jour en
direct.

## Stack technique

- **Python 3.12 + [Streamlit](https://streamlit.io/)** pour l'interface web
  (tout en Python, pas de HTML/JS à écrire).
- **pandas** pour manipuler joueurs / calendrier / classements sous forme de
  tableaux.
- **openpyxl** pour lire le fichier de données joueurs au format Excel
  (`.xlsx`).
- **numpy** pour tirer les scores selon une loi de Poisson et les
  buteurs/passeurs selon des tirages pondérés.
- **[uv](https://docs.astral.sh/uv/)** pour gérer l'environnement virtuel et
  les dépendances (`pyproject.toml` + `uv.lock`).
- **pytest** pour les tests de tous les modules métier (`src/ligue1sim/`).

## Lancer le projet

```bash
uv run streamlit run app.py
```

`uv` installe automatiquement l'environnement virtuel et les dépendances au
premier lancement. L'application s'ouvre dans le navigateur (par défaut
http://localhost:8501).

Pour lancer les tests :

```bash
uv run pytest
```

> Ce projet est stocké dans un dossier OneDrive. `pyproject.toml` force
> `uv` à copier les fichiers plutôt qu'à créer des liens physiques
> (`[tool.uv] link-mode = "copy"`), car OneDrive bloque le hardlinking sur
> les fichiers synchronisés dans le cloud.

## Architecture

```
ligue1-simulateur/
├── data/
│   └── joueurs.xlsx          # une ligne par joueur (voir "Modèle de données")
├── src/ligue1sim/             # logique métier (aucune dépendance à Streamlit, sauf season.py/custom_competition.py)
│   ├── players.py             # dataclass Player + tables poste -> groupe / poids buteur-passeur
│   ├── clubs.py                # chargement + validation -> list[Club] (par championnat) ou list[ClubOption] (vivier complet)
│   ├── lineup.py                # dispositifs tactiques, meilleure compo du jour, force de club calculée à la volée
│   ├── events.py                 # événements de match (buts/passes/cartons/blessures/remplacements/notes), trackers d'indisponibilité, classements
│   ├── schedule.py              # calendrier round-robin : 1/2/4 manches, effectifs pairs ou impairs (bye)
│   ├── simulation.py            # orchestration : compo du jour -> score Poisson -> événements -> mise à jour des indisponibilités
│   ├── standings.py             # calcul du classement à partir des matchs joués
│   ├── season.py                # état d'une saison "championnat" + championnat officiel sélectionné
│   ├── knockout.py              # tableau à élimination directe (têtes de série, exemptions, confrontations à N manches)
│   ├── groups.py                 # phase de poules façon Coupe du Monde (poules de 4, qualifiés)
│   └── custom_competition.py    # orchestration d'une Compétition Perso (championnat libre / élimination / hybride)
├── tests/                     # tests pytest sur tous les modules ci-dessus
└── app.py                     # interface Streamlit (accueil, écran de saison, détail de match, assistant + écrans Compétition Perso)
```

Le choix d'un layout `src/` avec un module `ligue1sim` séparé de `app.py`
permet de tester la logique métier sans dépendre de Streamlit.

### Modèle de données

`data/joueurs.xlsx` a une ligne par joueur (colonnes : `Prénom`, `Nom`,
`Nationalité`, `Âge`, `Poste`, `Club`, `Championnat`, `Note globale`). **Il n'y
a pas de note de club** : `Club(name: str, players: list[Player])` ne
stocke qu'un nom et un effectif. Toute notion de force d'équipe (calibrage
du moteur Poisson, têtes de série des poules/tableaux) est calculée à la
volée à partir des joueurs disponibles *au moment du calcul*, jamais
persistée (voir `lineup.club_strength`) — un club affaibli par des
suspensions/blessures est donc réellement plus faible ce jour-là, pas
seulement sur le papier.

`clubs.py` charge tous les championnats de `data/joueurs.xlsx` : les 8
championnats officiels (`list_championnats`) plus une catégorie
**"Autres clubs"**, exclue de la liste des championnats jouables en saison
complète mais disponible dans le vivier de la Compétition Perso
(`load_all_clubs`), exactement comme l'ancienne catégorie "Autres".

### Dispositifs tactiques et compo du jour (`lineup.py`)

Les 6 dispositifs jouables (4-2-3-1, 4-4-2, 4-3-3, 3-4-2-1, 3-5-2, 3-4-3)
sont définis place par place dans l'onglet **"Dispositifs tactiques"** de
`data/joueurs.xlsx` : une colonne par dispositif, 11 lignes donnant le poste
exact attendu à chaque place (certaines places acceptent l'un ou l'autre de
deux postes, ex. "MC ou MDC" pour un milieu qui peut être relayeur ou
sentinelle). `lineup.formation_slots()` charge cet onglet ("MO" y est un
raccourci pour MOC).

`select_best_xi` pourvoit chaque place, les plus strictes (un seul poste
accepté) en premier, en 3 passes :
1. le meilleur joueur dispo dont le **poste principal** correspond exactement ;
2. à défaut, le meilleur joueur dont un **poste secondaire déclaré**
   correspond (voir `Player.poste_secondaire`) ;
3. en tout dernier recours, si des places restent vides et qu'il reste des
   joueurs éligibles, les meilleurs joueurs restants quel que soit leur
   poste -- une équipe aligne toujours 11 joueurs quand son effectif le
   permet, quitte à dépanner hors de position plutôt que jouer à 10.

Un dispositif absent de l'onglet (ex. une formation préférentielle
Transfermarkt non répertoriée comme "4-1-4-1") retombe sur l'ancien système
par quotas génériques GK/DEF/MID/ATT (`parse_formation`, `FORMATIONS`), avec
un dépannage tolérant les postes tactiquement proches (`players.
poste_distance`) -- rare en pratique (2 clubs sur l'ensemble des
championnats chargés à ce jour).

`pick_best_formation` essaie tous les dispositifs connus avec l'effectif
*disponible aujourd'hui* (hors blessés/suspendus) et retourne celui qui
donne la meilleure compo moyenne — un effectif riche en ailiers/attaquants
penche naturellement vers un dispositif à 3 attaquants, un effectif riche au
milieu vers le 4-2-3-1, sans configuration manuelle par club. Si
l'entraîneur du club a une formation préférentielle connue (voir
`coaches.preferred_formations`), elle est imposée plutôt que ce choix
adaptatif. Ce même calcul sert à la fois de force d'équipe pour la
simulation Poisson (`club_strength`) et de compo affichée dans l'écran de
détail d'un match.

### Moteur de simulation en détail (`simulation.py`)

```
AVG_RATING = moyenne des forces des clubs du championnat chargé (club_strength, sans indisponibilité)
attack(équipe)  = (force_du_jour(équipe) / AVG_RATING) ** 7.0
defense(équipe) = (AVG_RATING / force_du_jour(équipe)) ** 7.0

lambda_domicile   = min(2.0, 1.14 * attack(dom) * defense(ext) * 1.10)   # bonus domicile, plafonné
lambda_exterieur  = min(2.0, 1.14 * attack(ext) * defense(dom))

buts = min(6, Poisson(lambda))
```

`force_du_jour` est la force calculée par `club_strength` en tenant compte
des indisponibilités du moment (voir plus bas) ; `AVG_RATING` reste stable
sur la saison (calibrage, pas un chiffre affiché). Les constantes
`LEAGUE_AVG_GOALS` (1.14), `HOME_ADVANTAGE` (1.10), `RATING_EXPONENT` (7.0)
et `MAX_LAMBDA` (2.0) sont ajustables dans `simulation.py` ; leur calibrage
(exposant 0.8 initial jugé trop plat -- le 2e du classement finissait
anormalement bas dans les championnats serrés -- porté à 1.8 puis 1.98 puis
2.2 puis 5.5 puis 7.0) a été validé par simulation de centaines de saisons
sur les 5 puis 8 championnats.

Un exposant aussi élevé rend le lambda de l'affiche la plus déséquilibrée
d'un championnat (le mieux noté à domicile contre le moins bien noté)
explosif (> 4 buts attendus), avec ~29% de scores type 5-0/6-0 rien que sur
cette affiche (vérifié sur 3000 tirages) -- beaucoup trop fréquent
(remonté par l'utilisateur : "quasi un par journée" sur une saison jouée).
`MAX_LAMBDA` plafonne le lambda de chaque équipe à 2.0 buts attendus quel
que soit l'écart de force, sans toucher à `RATING_EXPONENT` ni aux
classements (il ne joue que sur les quelques affiches vraiment
déséquilibrées, pas sur l'essentiel des matchs) : ce taux retombe à ~3.5%
sur l'affiche la plus déséquilibrée, et sur une saison Premier League
complète simulée (380 matchs), seuls 5 scores de ce type sont apparus --
un tous les 7-8 journées environ, plutôt qu'un par journée.

Une piste `VARIANCE_SHRINK` (resserrer chaque tirage de buts autour de sa
moyenne avant arrondi) a été essayée puis abandonnée : en tassant l'écart
entre le tirage brut et son espérance avant l'arrondi à l'entier, elle fait
s'écrouler la quasi-totalité des scores sur le même entier dès que les deux
lambdas sont proches (fréquent en championnat), ce qui fait exploser le
taux de nuls -- 22-26% (réaliste) à variance pleine, jusqu'à 54% à
`VARIANCE_SHRINK`=0.45 (vérifié sur 6000 matchs). `RATING_EXPONENT` n'a
pas ce défaut : il n'agit que sur l'espérance de buts (le lambda), jamais
sur la variance du tirage Poisson autour de cette espérance -- le taux de
nuls reste stable (~22-27%) quel que soit l'exposant, vérifié jusqu'à 9.0.
C'est ce qui a permis de le monter fortement (2.2 -> 7.0) pour séparer
franchement les classements sans reproduire le problème des nuls : sur des
saisons Premier League simulées, le champion termine en médiane à 82 pts à
5.5 (69 à 96) puis 87 pts à 7.0 (80 à 94), contre 73 pts (64-78) à 2.2. À
9.0 la médiane grimpe déjà à 95 pts (88-101) -- excessif, une bonne partie
des saisons ressemblerait alors à un record historique ; 7.0 est la valeur
retenue.

Une fois le score tiré, si les deux clubs ont un effectif réel (`events.py`,
`generate_match_events`) :

1. **Remplacements** — jusqu'à 5 par équipe, tirés parmi les titulaires de
   champ (jamais le gardien, sauf blessure), remplacés par le meilleur
   joueur du banc du même groupe de poste.
2. **Buteurs/passeurs** — chaque but est attribué à un joueur du groupe
   "titulaires + entrants" tiré au sort, pondéré par poste (`SCORER_WEIGHT`/
   `ASSIST_WEIGHT` dans `players.py`) et par sa note, les entrants ayant un
   poids réduit (moins de temps de jeu). Une passe décisive est ajoutée pour
   ~75% des buts.
3. **Cartons** — indépendamment par joueur : rouge direct, 2e jaune (= rouge),
   ou simple jaune, avec des probabilités calibrées pour rester réalistes à
   l'échelle d'un match.
4. **Blessures** — petite probabilité indépendante par joueur, durée courte
   (1 à 3 matchs) : volontairement rare et sans indisponibilité longue.
5. **Notes /10** — base + résultat d'équipe + buts/passes/cartons (+ bonus
   clean-sheet pour les gardiens) + bruit aléatoire, bornées à [3, 10].

### Suspensions et blessures (`events.AvailabilityTracker`)

Un même type de registre sert aux suspensions et aux blessures (deux
instances distinctes par compétition). Séquence appliquée à chaque
journée/manche simulée pour éviter tout décalage :

1. lire les indisponibilités héritées des matchs précédents (exclues de la
   sélection de compo) ;
2. simuler ;
3. décrémenter les indisponibilités déjà en cours pour les clubs qui ont
   joué ;
4. appliquer les nouvelles suspensions/blessures déclenchées par ce match
   (elles démarrent au match suivant, pas au match qui vient d'avoir lieu).

Règles de suspension implémentées : **rouge direct = 2 matchs**, **2 jaunes
dans le même match (= rouge) = 1 match**. Pas de règle d'accumulation de
jaunes sur plusieurs matchs.

Portée d'un tracker : toute la durée d'**une** compétition (`Season`, ou
`CustomCompetition` — un seul tracker partagé entre poules et élimination
au sein d'une même Compétition Perso hybride), jamais partagé entre deux
compétitions différentes.

## Compétition Perso

Depuis l'écran d'accueil, "🏆 Compétition Perso" lance un assistant en 4
étapes pour construire une compétition sur mesure, avec les clubs de son
choix dans le vivier complet (8 championnats + "Autres clubs", ~180 clubs) :

1. **Type** : championnat pur, élimination directe, ou hybride (poules de 4
   façon Coupe du Monde, les 2 premiers de chaque poule passent en
   élimination directe).
2. **Nombre d'équipes** : 3 à 50 pour un championnat pur ; pas de limite haute
   stricte pour les deux autres formats (bornée à 64 en pratique dans l'UI).
3. **Format des matchs** : simple, aller-retour, ou double aller-retour — ce
   réglage pilote aussi bien le nombre de journées d'un championnat/d'une
   phase de poules que le nombre de manches de chaque confrontation à
   élimination directe.
4. **Choix des clubs** : sélection libre dans le vivier complet (aucun
   indicateur de niveau affiché — voir "Modèle de données").

Deux mécanismes gèrent les effectifs qui ne tombent pas juste :

- **Championnat à effectif impair** (`schedule.py`) : une équipe "exemptée"
  par journée à tour de rôle, exactement comme un vrai calendrier à nombre
  impair de clubs.
- **Élimination directe à effectif hors puissance de 2** (`knockout.py`) :
  les clubs les mieux classés (`club_strength`) sont exemptés du 1er tour
  (qualifiés d'office pour le tour 2), têtes de série façon tableau de
  tournoi classique pour que les favoris ne se rencontrent qu'au plus tard.
- **Poules non multiples de 4** (`groups.py`) : les dernières poules ont 3
  clubs plutôt que 4 (pas de club fictif ajouté artificiellement) — chacune
  joue quand même un mini-championnat complet et qualifie 2 équipes, comme
  les autres.

`Season` (championnat pur), `Bracket` (élimination) et `Group` (poules)
réutilisent tous le même moteur (`simulation.py`), le même calcul de
classement (`standings.py`) et les mêmes classements buteurs/passeurs
(`events.compute_leaderboards`) que les 8 championnats officiels — aucune
logique dupliquée.

## Interface : matchs cliquables et classements

Une fois une journée/manche jouée, chaque match de la liste devient
cliquable (score affiché comme un bouton) et ouvre un écran de détail :
dispositif utilisé par chaque équipe, compos complètes (poste, buts,
passes, cartons, note /10), liste des buteurs (avec passeur éventuel) et
des remplacements. Sous chaque écran de compétition : un classement
buteurs/passeurs, et un panneau "Suspensions et blessures en cours".

## Limites connues (v2)

- Classement trié par points / différence de buts / buts pour, sans règle de
  confrontations directes en cas d'égalité stricte.
- L'état de la saison / compétition n'est pas sauvegardé sur disque : fermer
  le navigateur (ou changer de championnat/compétition) repart de zéro.
- Compétition Perso : en cas d'égalité agrégée dans une confrontation à
  élimination directe, le départage se fait par un tirage pondéré selon
  l'écart de force du jour (mini séance de tirs au but simplifiée), pas par
  une simulation de tirs au but tir par tir.
- Pas de chronologie précise des événements (pas de minute simulée) : un
  remplacement ne réduit pas rétroactivement le poids d'un joueur sorti,
  seuls les entrants ont un poids réduit.
- Séparation prénom/nom par simple découpage du premier mot (hérité des
  données sources) : imparfait pour certains noms composés ou ordres de nom
  non occidentaux.

## Évolutions possibles

- Exposer les constantes de calibrage (`LEAGUE_AVG_GOALS`/`HOME_ADVANTAGE`/
  `RATING_EXPONENT` dans `simulation.py`, probabilités de cartons/blessures
  dans `events.py`) comme réglages dans l'UI.
- Sauvegarder/nommer une Compétition Perso pour y revenir plus tard.
- Historique de saison, sauvegarde persistante (fichier JSON ou base de
  données).
- Règle d'accumulation de jaunes sur plusieurs matchs (ex. 5 jaunes = 1 match
  de suspension), non implémentée pour l'instant.
- Chronologie des événements (minute simulée) pour un ordre buts/cartons/
  remplacements cohérent dans le temps.
