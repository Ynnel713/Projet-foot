# Simulafoot — état actuel de l'application

Document de référence technique, écrit le 22/09/2026 en préparation du chantier "simulation physique" (moteur de match avec joueurs qui se déplacent sur le terrain, façon Football Manager). Objectif : donner une photo précise de ce qui existe, ce qui marche, ce qui est mort, pour ne pas repartir de suppositions.

---

## 1. Vue d'ensemble : deux interfaces, un seul moteur

Le projet a deux frontends distincts, à des stades très différents :

| | Streamlit (`app.py`) | React/FastAPI (`ui/` + `api/`) |
|---|---|---|
| Statut | **Interface réellement utilisée** (confirmé le 22/09 par Olivier) | Existe, buildée, mais pas l'interface utilisée au quotidien |
| Lancé par | `uv run streamlit run app.py` (manuel) | `Lancer l'appli.bat` : uvicorn (port 8000) + Vite (port 5173) |
| Ajouté | Dès le début du projet | Commit `9d43df1`, début septembre 2026 |
| Forme | App web classique, pensée desktop | PWA mobile-first, format paysage |

Le commentaire du `.bat` ("Streamlit n'est plus le point d'entrée") ne reflète donc pas l'usage réel : **Streamlit reste l'interface de référence pour tout développement UI**, y compris le futur habillage visuel de simulation physique. Le `.bat` mériterait d'être corrigé à l'occasion pour ne pas induire en erreur une future relecture du code, mais ce n'est pas urgent.

Le commit `86f2794` a unifié le déploiement de la PWA React (le backend FastAPI sert `ui/dist`), mais ça reste un chantier parallèle non prioritaire au regard de l'usage réel.

Les deux frontends partagent le **même moteur** : tout `src/ligue1sim/` (le "cœur" du jeu) est indépendant de Streamlit ou de React. C'est la bonne nouvelle structurelle pour la suite : le travail sur la simulation physique se fera dans ce cœur commun, utilisable par n'importe quelle interface.

---

## 2. Le moteur (`src/ligue1sim/`) — 3783 lignes, 17 modules

### 2.1 Modèle de données

- **Source unique** : `data/joueurs.xlsx`, classeur Excel édité manuellement (avec assistance IA ponctuelle), une ligne par joueur. Onglets : "Infos principales" (le gros de l'effectif), "notice" (conventions de saisie), "Dispositifs tactiques" (postes acceptés par place, par dispositif), "Statuts", "Postes", "Roles", "Caractéristiques", "Description catégories joueurs", "Ligue des Champions", "Europe"/"Afrique"/"Amérique"/"Asie"/"Océanie" (sélections nationales).
- **`Player`** (`players.py`) : prénom, nom, nationalité, âge, poste, note, club, championnat, poste secondaire (tuple), finition, catégorie (style de jeu), id. 12 postes possibles (GK, RB, LB, DC, MDC, MC, MOC, AD, AG, SA, BU, ATT), regroupés en 4 familles (GK/DEF/MID/ATT).
- **`Club`** (`clubs.py`) : pas de note de club stockée, la force se calcule toujours à la volée depuis l'effectif (`lineup.club_strength`). Cache `@lru_cache` sur la lecture Excel (perf).
- 9 championnats chargeables (Ligue 1, Premier League, Championship, LaLiga, Bundesliga, Serie A, Eredivisie, Liga Portugal, Jupiler Pro League), plus un vivier "Autres clubs" pour la Compétition Perso.

### 2.2 Sélection de compo (`lineup.py`, 423 lignes)

- `select_best_xi` : pour un dispositif donné (ex. 4-2-3-1, lu depuis l'onglet "Dispositifs tactiques"), attribue les 11 places par **appariement glouton global** — chaque paire (joueur, place) possible devient un lien noté (poste principal = note pleine, poste secondaire déclaré = note × 0.95), tous les liens triés par note décroissante, attribution gloutonne. **Revu aujourd'hui même** (22/09) suite à un bug signalé : un joueur au poste secondaire ne pouvait jamais battre un titulaire médiocre au poste principal exact (cas réel : le jeune Hamza Abdelkarim, 59 de note, prenait systématiquement la place de BU à Barcelone devant Raphinha/Gordon, meilleurs mais avec BU en secondaire).
- Repli en cascade si des places restent vides : joueur tactiquement proche (`poste_distance`, distance ≤ 1) puis blind backfill par note.
- `pick_best_formation` : respecte le dispositif préférentiel du coach (`coaches.py`, sourcé Transfermarkt) sauf trou d'effectif significatif (facteur de fidélité 1.03) qui fait basculer sur un dispositif alternatif mieux adapté à l'effectif du jour.

### 2.3 Simulation du résultat (`simulation.py`, 682 lignes) et des événements (`events.py`, 618 lignes)

**Point central pour le chantier "simulation physique" : le moteur ne simule PAS le déroulé du match.** Il fonctionne à l'envers du réalisme physique :

1. **`simulation.py`** tire d'abord un **score final** via une loi de Poisson, dont le lambda de chaque équipe dépend du ratio note attaque/défense (formule façon Dixon-Coles, `ATTACK_DEFENSE_POWER=2.6`), modulé par la force du milieu (`MID_INFLUENCE`), l'avantage du terrain (`HOME_ADVANTAGE`), l'apport du banc (`BENCH_INFLUENCE`), un bonus de "grand match", et une **forme persistante** par club (`FormTracker`, moyenne mobile exponentielle bornée ±6%, qui capture les séries positives/négatives sur plusieurs journées).
2. **`events.py`** distribue ensuite ce score déjà connu : les buteurs/passeurs sont tirés au sort pondérés par poste et note (`_generate_goals`), puis chaque but, carton, blessure, remplacement reçoit une **minute aléatoire** (`_random_minute`) sans aucune cohérence de déroulé (pas de possession, pas de zone du terrain, pas de tir non cadré hors penalty manqué).
3. Le fichier documente un historique de calibrage très détaillé (7 campagnes de recalibrage entre août et septembre 2026, chacune avec ses mesures avant/après sur des dizaines à centaines de saisons simulées via `scripts/calibrate_engine.py`) : exposant d'attaque/défense, avantage du terrain, bornes de la forme, distorsion des notes individuelles. C'est un moteur **statistiquement mûr et validé**, mais entièrement **agnostique de l'espace et du temps** au sein d'un match.

**Conséquence directe pour la suite** : le "cœur" à construire pour la simulation physique (positions, mouvements, duels, possession, tirs) est un chantier neuf, qui ne peut pas être branché sur l'existant sans le réécrire — voir section 6.

### 2.4 Compétitions disponibles

| Compétition | Module | Format |
|---|---|---|
| Championnat (les 9 ligues) | `season.py` + `schedule.py` (round-robin 1/2/4 manches) | Championnat pur |
| Coupe du Monde | `world_cup.py` | 32 sélections, 4 chapeaux de 8, 8 poules de 4, élimination directe |
| Ligue des Champions | `champions_league.py` | 36 clubs (onglet dédié), 4 chapeaux de 9, 9 poules de 4, élimination directe — approximation assumée du vrai format Swiss à 36 |
| Sélections nationales (hors CDM) | `nations.py` | Sélections COMPLET (23/23) uniquement, utilisables dans la Compétition Perso |
| Compétition Perso | `custom_competition.py` | Championnat libre, élimination directe, ou poules + élimination — clubs ET sélections mélangeables |

Poules (`groups.py`) et tableau à élimination (`knockout.py`, gère les exemptions et les confrontations à 1/2/4 manches) sont des modules génériques réutilisés par toutes les compétitions à ce format, plutôt que dupliqués.

### 2.5 Autres modules

- `kits.py` (317 lignes) : maillots SVG dessinés à la main (pas de logo officiel), un par club des championnats simulables + quelques clubs notables hors championnat.
- `pitch_layout.py` (245 lignes) : placement statique des 11 titulaires sur un terrain, ligne par ligne, avec logique de symétrie gauche/droite par couloir. **Pas d'animation, une seule position calculée par joueur.**
- `standings.py` : calcul de classement (3/1/0 points) à partir du calendrier joué.

---

## 3. Frontend secondaire (non utilisé au quotidien) : React + FastAPI (`ui/`, `api/`)

### 3.1 Stack technique

- **Backend** : FastAPI (`api/main.py`), routers `leagues` (référentiel championnats/clubs/nations) et `competitions` (cycle de vie complet d'une compétition : création, simulation journée par journée, classement, matchs). Sérialisation via Pydantic (`api/schemas.py`) et convertisseurs dédiés moteur → DTO (`api/serializers.py`).
- **État des compétitions** : `api/store.py`, un dict en mémoire process-local (pas de persistance entre redémarrages, assumé pour un usage perso hébergé en local ; migration SQLite/shelve possible sans toucher au moteur).
- **Frontend** : React 19 + Vite + Tailwind 4 + `react-router-dom` 7 + Zustand (state global) + `framer-motion` (déjà installé, utile pour la suite — animations à ressort) + `lucide-react` (icônes) + `vite-plugin-pwa` (installable, icônes/manifest déjà en place dans `ui/public/icons/`).
- **CORS** ouvert en dev uniquement (frontend Vite séparé sur 5173) ; sans effet une fois le build servi par le même serveur que l'API.

### 3.2 Écrans (`ui/src/routes/`)

`Home`, `Leagues` (liste des championnats), `Nations` (sélections), `CustomCompetition` (assistant de création), `Simulation` (simuler journée par journée), `Standings` (classement), `PitchView` (compo sur le terrain, statique), `Groups` (poules), `Bracket` (tableau à élimination), `Leaderboards` (buteurs/passeurs).

`PitchView.jsx` reprend exactement la même logique de placement statique que le moteur (`pitch_layout.place_starting_xi`), juste réaffichée en React avec une permutation d'axes pour le format paysage. **Aucune animation aujourd'hui**, côté React comme côté Streamlit.

---

## 4. Frontend de référence : Streamlit (`app.py`, 2298 lignes)

Reste dans le repo, fonctionnel si lancé manuellement, mais plus l'entrée officielle. Contient historiquement : écran d'accueil (récemment refondu visuellement : tuiles circulaires, fond de stade, hiérarchie à 3 zones), écran de saison, écran de détail de match avec vue "stade" (terrain horizontal en CSS pur, sans animation), fiches club/joueur cliquables, gestion de session via `st.session_state`.

`season.py` et `custom_competition.py` ont encore des fonctions d'aide `st.session_state` (sauvegarde/lecture/effacement de l'état) — **non utilisées par l'API**, qui gère son propre état via `api/store.py`. Le moteur sous-jacent (les dataclasses `Club`, `CustomCompetition`, etc.) est lui totalement indépendant de Streamlit.

---

## 5. Tests (2475 lignes, `tests/`)

Un fichier de test par module du moteur, tenu à jour au fil des évolutions (dernier ajout : les deux tests de régression du fix de sélection de compo du jour). Aucun test ne porte sur `app.py` ni sur `ui/`/`api/` — la couverture s'arrête à la frontière du moteur. `pytest -q` : 163 tests, tous verts au 22/09/2026.

---

## 6. Ce que ça implique pour le chantier "simulation physique"

Deux décisions de cadrage prises le 22/09/2026 avec Olivier :

- **Interface cible : Streamlit.** Pas la PWA React (non utilisée au quotidien). La couche de rendu animé devra donc s'intégrer dans `app.py`, très probablement via un composant HTML/JS embarqué (`streamlit.components.v1.html`, canvas ou SVG piloté par `requestAnimationFrame`) puisque Streamlit n'a aucune primitive d'animation native — voir section 4. `framer-motion`, déjà installé côté `ui/`, n'est pas utilisable ici (React uniquement).
- **Nature du projet : un habillage visuel, pas un remplacement du moteur.** Le score final et les événements (buteur, minute) restent décidés par le moteur Poisson existant (`simulation.py`/`events.py`, calibrage validé sur des centaines de saisons — voir section 2.3), qui reste la seule "vérité" du résultat. La simulation physique vient AJOUTER une couche de détail visuel par-dessus un résultat déjà connu à l'avance : pour chaque moment clé (but, occasion, carton...), générer un déroulé de mouvement crédible des joueurs impliqués vers la zone de l'action, sans jamais influencer qui gagne, perd, ou marque. Aucun risque de perdre le travail de calibrage déjà fait.

Prochaine étape technique (à cadrer séparément) : donner une zone de terrain aux événements du moteur (aujourd'hui ils n'ont qu'une minute, pas de position), puis générer une trajectoire interpolée entre la position de formation et cette zone, avant de s'attaquer au rendu animé lui-même dans `app.py`.

---

*Document généré le 22/09/2026 à partir d'une lecture directe du code (pas de la mémoire de conversation) — structure, docstrings et historique git vérifiés.*
