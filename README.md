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

Un club n'a pas une seule force : sa compo du jour (`pick_best_formation`)
donne une note globale (`rating`, têtes de série/affichage) et quatre notes
sectorielles -- gardien, défense, milieu, attaque (`Lineup.gk_rating`/
`def_rating`/`mid_rating`/`att_rating`). Le milieu ne joue pas directement
dans les buts : il **module légèrement** l'attaque et la défense de sa
propre équipe selon qu'il est au-dessus ou en-dessous du niveau moyen de
SA compo (`_mid_modifier`, borné ±10%).

```
force_attaque(équipe)  = att_rating * mid_modifier(équipe)
force_defense(équipe)  = (0.35*gk_rating + 0.65*def_rating) * mid_modifier(équipe)

attack_ratio  = (force_attaque(équipe) / AVG_ATTACK) ** 1.8
defense_ratio = (AVG_DEFENSE / force_defense(adversaire)) ** 1.8

lambda_domicile  = min(3.0, 1.14 * attack_ratio(dom) * defense_ratio(ext) * 1.20)  # bonus domicile
lambda_exterieur = min(3.0, 1.14 * attack_ratio(ext) * defense_ratio(dom))

buts = min(6, Poisson(lambda))
```

`AVG_ATTACK`/`AVG_DEFENSE` sont les moyennes de ces forces sectorielles sur
le championnat chargé (`LeagueContext`, stables sur la saison). La formule
ratio-à-la-moyenne (façon Dixon-Coles) a remplacé en août 2026 un exposant
brut (`RATING_EXPONENT=7.0`) appliqué à la note globale, historique conservé
ci-dessous pour mémoire.

**Historique et audit qui a mené au remplacement.** L'exposant avait été
monté progressivement (0.8 → 1.8 → 1.98 → 2.2 → 5.5 → 7.0) au fil de
centaines de saisons simulées, uniquement pour que le classement d'une
saison se sépare suffisamment (champion médian ~87 pts à 7.0, contre ~73 à
2.2). Un audit complet (mesures sur des dizaines de milliers de matchs) a
montré que cette approche était un correctif de symptôme : à 7.0, le lambda
brut atteignait jusqu'à 13.6 buts attendus sur certaines affiches, et
`MAX_LAMBDA` (alors 2.0) était atteint sur **35% des matchs** -- un plafond
qui masquait en permanence une formule mal calibrée plutôt qu'un vrai
garde-fou. Conséquences mesurées : avantage du terrain écrasé par l'écart de
force (domicile 41% / extérieur 38% au lieu d'un écart réaliste), taux de
nuls sous la réalité (~21%), et quasiment plus aucune surprise pour un très
gros favori (1.2% de défaite, 0% de défaite par 3+ buts).

La formule ratio (puissance 1.8, testée de 1.0 à 2.0 sur 122 400 matchs des
18 vrais clubs de Ligue 1) ne dépasse jamais son plafond en pratique (max
observé 2.67 sur 3.0) et donne une distribution bien plus réaliste : nuls
~25-27%, 0-0 ~8-10%, écarts de 3+ buts ~13-17%, clean sheets ~50-54%, et un
rapport favori/outsider qui laisse une vraie place à la surprise même pour
un très gros favori (~10-13% de défaite à l'écart de force maximal). Le
`HOME_ADVANTAGE` a été recalibré à 1.20 (au lieu de 1.10) par un sweep
isolé : il n'affecte QUE le lambda de l'équipe qui reçoit (jamais celui de
l'adversaire), et une valeur trop haute (1.30+) érode le taux de nuls/0-0 en
échange d'un écart domicile/extérieur plus large -- 1.20 est le meilleur
compromis mesuré.

Contrepartie assumée : sans l'ancien exposant, le classement de saison se
sépare moins (champion médian ~72 pts au lieu de ~87). Plutôt que de
réintroduire un exposant artificiel, cette séparation est restaurée par la
**forme** (voir plus bas) -- une inertie sportive réelle plutôt qu'un second
levier de force.

`scripts/calibrate_engine.py` simule N saisons via le pipeline réel
(`Season`) et rapporte tous ces indicateurs -- à relancer après tout
changement des constantes de `simulation.py` :

```bash
uv run python scripts/calibrate_engine.py "Ligue 1" 40
```

Une piste `VARIANCE_SHRINK` (resserrer chaque tirage de buts autour de sa
moyenne avant arrondi) a été essayée puis abandonnée : en tassant l'écart
entre le tirage brut et son espérance avant l'arrondi à l'entier, elle fait
s'écrouler la quasi-totalité des scores sur le même entier dès que les deux
lambdas sont proches (fréquent en championnat), ce qui fait exploser le
taux de nuls -- 22-26% (réaliste) à variance pleine, jusqu'à 54% à
`VARIANCE_SHRINK`=0.45 (vérifié sur 6000 matchs). Laissée à 1.0 (Poisson
pur) : la variance du tirage doit rester intacte, seul l'écart de force
(`ATTACK_DEFENSE_POWER`) doit influencer le résultat.

### Forme (`FormTracker`, dans `simulation.py`)

Chaque club a une forme **offensive** et une forme **défensive**, distinctes
et persistées par club au fil d'une saison/compétition (même pattern que
`AvailabilityTracker`) -- testé contre une forme unique : la version séparée
donne un taux de nuls/0-0/clean-sheets mesurablement plus proche du réel.
Mise à jour après CHAQUE match avec la **performance réelle** par rapport à
l'attendu du moment (`buts réels - lambda`), jamais avec le seul résultat :
gagner 1-0 en étant dominé n'améliore pas la forme offensive.

Le signal brut est bruyant : un seul match à forte variance (ex. 4 buts
marqués pour 1.3 attendus) sature quasi instantanément une forme bornée
si on l'injecte tel quel dans l'EMA (vérifié : +0.32 après UN match avec
alpha=0.12, contre un plafond de ±0.15). Il est donc **plafonné puis
rétréci** avant d'entrer dans l'EMA (`_process_form_signal`) : un seul match
chanceux ne doit pas transformer durablement la force d'une équipe. La forme
module ensuite légèrement l'attaque/la défense du club pour ses matchs
suivants (borné ±15%, `_form_modifier`), exactement comme `_mid_modifier`.

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
  `ATTACK_DEFENSE_POWER`/`FORM_ALPHA` dans `simulation.py`, probabilités de
  cartons/blessures dans `events.py`) comme réglages dans l'UI.
- Sauvegarder/nommer une Compétition Perso pour y revenir plus tard.
- Historique de saison, sauvegarde persistante (fichier JSON ou base de
  données).
- Règle d'accumulation de jaunes sur plusieurs matchs (ex. 5 jaunes = 1 match
  de suspension), non implémentée pour l'instant.
- Chronologie des événements (minute simulée) pour un ordre buts/cartons/
  remplacements cohérent dans le temps.
