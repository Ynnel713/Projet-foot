# Simulateur de championnat 2026-2027

Mini application web qui simule soit une saison complète d'un grand
championnat européen (Ligue 1, Premier League, Liga, Serie A, Bundesliga),
soit une **Compétition Perso** entièrement personnalisée (championnat libre,
élimination directe, ou hybride façon Coupe du Monde, avec les clubs de ton
choix). Calendrier généré automatiquement, simulation des matchs avec un
moteur basé sur une loi de Poisson pondérée par la note des clubs, classement
mis à jour en direct.

## Stack technique

- **Python 3.12 + [Streamlit](https://streamlit.io/)** pour l'interface web
  (tout en Python, pas de HTML/JS à écrire).
- **pandas** pour manipuler clubs / calendrier / classement sous forme de
  tableaux.
- **openpyxl** pour lire le fichier de données clubs au format Excel
  (`.xlsx`), tel que fourni/édité par l'utilisateur.
- **numpy** pour tirer les scores selon une loi de Poisson.
- **[uv](https://docs.astral.sh/uv/)** pour gérer l'environnement virtuel et
  les dépendances (`pyproject.toml` + `uv.lock`).
- **pytest** pour les tests du calendrier, du classement et du chargement
  des clubs.

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
│   └── clubs.xlsx           # colonnes : Championnat, Club, Note_globale (0-100)
├── src/ligue1sim/            # logique métier (aucune dépendance à Streamlit, sauf season.py/custom_competition.py)
│   ├── clubs.py              # chargement + validation -> list[Club] (5 championnats) ou list[ClubOption] (vivier complet)
│   ├── schedule.py           # calendrier round-robin : 1/2/4 manches, effectifs pairs ou impairs (bye)
│   ├── simulation.py         # moteur de simulation (loi de Poisson)
│   ├── standings.py          # calcul du classement à partir des matchs joués
│   ├── season.py             # état d'une saison "championnat" + championnat officiel sélectionné
│   ├── knockout.py           # tableau à élimination directe (têtes de série, exemptions, confrontations à N manches)
│   ├── groups.py             # phase de poules façon Coupe du Monde (poules de 4, qualifiés)
│   └── custom_competition.py # orchestration d'une Compétition Perso (championnat libre / élimination / hybride)
├── tests/                    # tests pytest sur tous les modules ci-dessus
└── app.py                    # interface Streamlit (accueil, écran de saison, assistant + écrans Compétition Perso)
```

Le choix d'un layout `src/` avec un module `ligue1sim` séparé de `app.py`
permet de tester la logique métier sans dépendre de Streamlit, et facilite
l'ajout d'autres championnats ou d'autres interfaces plus tard.

### Flux de données

1. `clubs.py` charge `data/clubs.xlsx`, liste les championnats disponibles
   (`list_championnats`, tous sauf "Autres"), et charge/valide les clubs
   d'un championnat donné (`load_clubs`) : colonnes attendues, aucune valeur
   manquante, notes entre 0 et 100, pas de club en double, et un **nombre
   pair de clubs** (nécessaire pour le round-robin).
2. `app.py` affiche d'abord un écran d'accueil listant les championnats
   disponibles ; le choix de l'utilisateur est stocké dans
   `st.session_state` par `season.select_championnat`.
3. `schedule.py` génère le calendrier une seule fois par saison, pour
   n'importe quel nombre pair de clubs : méthode du cercle pour produire
   (n-1) journées où chaque club rencontre chaque autre une fois, puis
   (n-1) journées miroir (domicile/extérieur inversés). 18 clubs → 34
   journées de 9 matchs (Ligue 1, Bundesliga) ; 20 clubs → 38 journées de
   10 matchs (Premier League, Liga, Serie A).
4. `simulation.py` calcule, pour chaque match, un nombre de buts attendus
   (lambda) par équipe à partir de la note des deux clubs et d'un bonus
   modéré à domicile (+10 %), puis tire un score selon une loi de Poisson
   (plafonné à 6 buts par équipe).
5. `standings.py` recalcule le classement (points 3/1/0, buts pour/contre,
   différence de buts) à partir de tous les matchs déjà joués.
6. `season.py` garde l'état de la saison (calendrier, journée courante,
   championnat sélectionné) dans `st.session_state`, pour qu'il survive aux
   rechargements de page tant que la session du navigateur est ouverte.
7. `app.py` affiche l'écran de saison : journée courante, boutons
   "Simuler la journée", "Journée suivante", "Changer de championnat" et
   "Réinitialiser la saison", ainsi que le classement.

### Modèle de club

Le fichier source ne fournit qu'une seule note par club (`Note_globale`,
0-100), pas de distinction attaque/défense. `Club` reflète ça honnêtement :
`Club(name: str, rating: float)`. Le moteur de simulation utilise `rating`
à la fois comme force offensive et défensive du club.

### Moteur de simulation en détail

```
AVG_RATING = moyenne des notes des clubs du championnat chargé
attack(équipe)  = (rating(équipe) / AVG_RATING) ** 1.8
defense(équipe) = (AVG_RATING / rating(équipe)) ** 1.8

lambda_domicile   = 1.14 * attack(dom) * defense(ext) * 1.10   # bonus domicile
lambda_exterieur  = 1.14 * attack(ext) * defense(dom)

buts = min(6, Poisson(lambda))
```

La moyenne du championnat est recalculée à partir des clubs chargés (pas de
valeurs codées en dur liées à un championnat particulier), donc ce moteur
fonctionne pour n'importe quel jeu de clubs. Les constantes
`LEAGUE_AVG_GOALS` (1.14), `HOME_ADVANTAGE` (1.10) et `RATING_EXPONENT`
(1.8) sont ajustables dans `simulation.py`.

L'exposant `RATING_EXPONENT` amplifie l'écart de lambda entre équipes fortes
et faibles ; `LEAGUE_AVG_GOALS` est recalibré à chaque changement d'exposant
pour garder une moyenne de buts réaliste (~2,7-2,8 buts/match). Le réglage a
été ajusté par simulation de centaines de saisons avec le vrai moteur
(`ligue1sim.simulation`, pas une réimplémentation à part), vérifié sur les 5
championnats à la fois. Premier ajustement (exposant 0.8) : les favoris trop
écrasants dans les championnats à gros écart de notes (Ligue 1, Bundesliga)
étaient corrigés, mais dans les championnats plus serrés le 2e du classement
pouvait finir anormalement bas (ex. Barcelone, 0,3 point derrière le Real
Madrid, terminant 6e de Liga). Deuxième ajustement (exposant 1.8, retenu) :

| Championnat | Défaites moy. du favori (max) | % saisons favori champion | Rang moy. du 2e (max) |
|---|---|---|---|
| Ligue 1 (PSG 92 vs Lyon 66) | 1,4 (5) | 100 % | 3,6 (11) |
| Bundesliga (Bayern 90 vs RB Leipzig 76) | 2,6 (7) | 88 % | 3,2 (9) |
| Liga (Real Madrid 86 vs Barcelone 85,7) | 4,4 (10) | 46 % | **1,9 (5)** |
| Premier League (Arsenal 90 vs Man City 87) | 5,2 (14) | 52 % | 2,3 (9) |
| Serie A (Inter 82 vs Juventus 78) | 6,7 (15) | 42 % | 3,8 (12) |

Le rang du 2e du classement reflète maintenant l'écart de notes réel : très
proche du 1er en Liga (Real/Barça quasi à égalité) → il reste presque
toujours sur le podium, plus loin derrière en Ligue 1/Bundesliga (où le
favori est un outlier bien plus large) → plus de variance. Ligue 1 et
Bundesliga restent très dominées par leur favori, ce qui reflète l'écart de
notes que tu as toi-même fixé dans le fichier de données (PSG et Bayern très
loin devant leur dauphin) plutôt qu'un excès d'aléatoire du moteur — pour
les rendre moins prévisibles, la manière la plus honnête serait de resserrer
leurs notes dans `data/clubs.xlsx`, pas de rebaisser `RATING_EXPONENT`
(ça referait replonger la Liga dans l'incohérence).

## Compétition Perso

Depuis l'écran d'accueil, "🏆 Compétition Perso" lance un assistant en 4
étapes pour construire une compétition sur mesure, avec les clubs de son
choix dans le vivier complet (5 championnats + "Autres", ~140 clubs) :

1. **Type** : championnat pur, élimination directe, ou hybride (poules de 4
   façon Coupe du Monde, les 2 premiers de chaque poule passent en
   élimination directe).
2. **Nombre d'équipes** : 3 à 50 pour un championnat pur ; pas de limite haute
   stricte pour les deux autres formats (bornée à 64 en pratique dans l'UI).
3. **Format des matchs** : simple, aller-retour, ou double aller-retour — ce
   réglage pilote aussi bien le nombre de journées d'un championnat/d'une
   phase de poules que le nombre de manches de chaque confrontation à
   élimination directe.
4. **Choix des clubs** : sélection libre dans le vivier complet.

Deux mécanismes gèrent les effectifs qui ne tombent pas juste :

- **Championnat à effectif impair** (`schedule.py`) : une équipe "exemptée"
  par journée à tour de rôle, exactement comme un vrai calendrier à nombre
  impair de clubs.
- **Élimination directe à effectif hors puissance de 2** (`knockout.py`) :
  les clubs les mieux notés sont exemptés du 1er tour (qualifiés d'office
  pour le tour 2), têtes de série façon tableau de tournoi classique pour
  que les favoris ne se rencontrent qu'au plus tard.
- **Poules non multiples de 4** (`groups.py`) : les dernières poules ont 3
  clubs plutôt que 4 (pas de club fictif ajouté artificiellement) — chacune
  joue quand même un mini-championnat complet et qualifie 2 équipes, comme
  les autres. C'est une simplification volontaire par rapport à un système
  de clubs fictifs "bye" : plus simple, pas de risque de division par zéro
  dans le moteur de simulation, et pas de ligne de classement à expliquer
  pour une équipe qui n'existe pas vraiment.

`Season` (championnat pur), `Bracket` (élimination) et `Group` (poules)
réutilisent tous le même moteur (`simulation.py`) et le même calcul de
classement (`standings.py`) que les 5 championnats officiels — aucune
logique dupliquée.

## Limites connues (v1)

- Classement trié par points / différence de buts / buts pour, sans règle de
  confrontations directes en cas d'égalité stricte.
- L'état de la saison / compétition n'est pas sauvegardé sur disque : fermer
  le navigateur (ou changer de championnat/compétition) repart de zéro.
- La catégorie "Autres" n'a pas de calendrier dédié comme les 5 grands
  championnats, mais ses clubs sont disponibles dans le vivier de la
  Compétition Perso.
- Compétition Perso : en cas d'égalité agrégée dans une confrontation à
  élimination directe, le départage se fait par un tirage pondéré selon
  l'écart de note (mini séance de tirs au but simplifiée), pas par une
  simulation de tirs au but tir par tir.

## Évolutions possibles

- Donner un calendrier dédié à la catégorie "Autres", ou ajouter de nouveaux
  championnats (ils apparaissent automatiquement sur l'écran d'accueil dès
  qu'ils sont dans `data/clubs.xlsx`, à condition d'avoir un nombre pair de
  clubs).
- Exposer `LEAGUE_AVG_GOALS` / `HOME_ADVANTAGE` / `RATING_EXPONENT` comme
  réglages dans l'UI.
- Sauvegarder/nommer une Compétition Perso pour y revenir plus tard.
- Ajouter des statistiques joueurs, un historique de saison, une sauvegarde
  persistante (fichier JSON ou base de données).
