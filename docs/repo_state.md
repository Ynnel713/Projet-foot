# État du dépôt — travail préexistant non commité

Inventaire du **07/10/2026**, après le commit `f70b37d` (intégration PWA par iframe). **Aucun fichier listé ici n'a été commité, modifié ni supprimé par cet inventaire** : c'est un constat, suivi d'un plan de résorption **proposé, non exécuté** (§6). Le plan doit être validé avant toute exécution.

## 1. Méthode et limites

- Source : `git status`, `git diff HEAD`, lecture des diffs et des en-têtes de fichiers, exécution de la suite de tests et du lint sur l'arbre de travail.
- **Auteur** : un seul compte git (`Ynnel713`, 202 commits) ; ces changements n'étant pas commités, **aucun auteur git ne leur est attaché**. « Auteur probable » = déduit du style (commentaires datés du 26/09 au 02/10/2026, mentions « retour terrain/utilisateur du JJ/MM ») : sessions de développement assisté (Claude Code) pilotées par le propriétaire. Ce n'est pas vérifiable par git.
- **Testabilité** = les tests qui couvrent le périmètre passent-ils **avec** ces modifications ? Mesuré sur l'arbre de travail complet : `python -m pytest tests` → **1046 passed, 12 deselected** (tests d'intégration exclus par défaut) ; UI : `vite build` OK, `oxlint src` → **0 erreur, 5 avertissements** (`set-state-in-effect`, dont `PitchView.jsx:93`, `TeamRoster.jsx:35`, `CustomCompetition.jsx:348`). Ces résultats valent pour **l'ensemble** : la suite ne permet pas, à elle seule, d'isoler un lot.
- Ne sont pas inventoriés : les fichiers ignorés par git (`.venv`, `node_modules`, `ui/dist`, `__pycache__`, `.pytest_cache`, `ui/.env.local`, `data/joueurs_backup_*.xlsx`, `data/*_avant_*.xlsx`).

## 2. Synthèse

| | Nombre | Détail |
|---|---|---|
| Fichiers suivis modifiés | 53 | 56 changements avec les 3 suppressions ; +3 573 / −824 lignes (hors binaires) |
| Fichiers suivis supprimés | 3 | `data/entraineurs.xlsx`, `tests/test_scrape_fminside_attributes.py`, `ui/src/components/layout/BottomNav.jsx` |
| Entrées non suivies | 52 | 12 fichiers à la racine (notes, scripts jetables, sorties de débogage), 2 modules `api/`, 1 module `src/`, 5 fichiers de tests, 18 entrées UI (fichiers et dossiers), 2 scripts de scraping, 1 classeur, 10 fichiers d'échantillons NLG, `graphify-out/` ; poids notables : `data/nlg_samples/` 50 Mo, `graphify-out/` 9,8 Mo, `ui/public/logos/` 9,5 Mo, `ui/public/branding/` 0,5 Mo |

**Constats transverses**
1. **Le travail préexistant change le résultat sportif.** `src/ligue1sim/simulation.py` ajoute des modulateurs de **coach** (±1 % sur les lambdas) et de **styles de jeu** (jusqu'à ±5 % cumulés) au modèle de Poisson ; `data/joueurs.xlsx` modifie la « Moyenne joueur » (la note qui pilote le moteur) de **82 joueurs** et retire 1 joueur. Rien de tout cela n'est dans `f70b37d`.
2. **Dépendances cachées entre lots** (§4) : plusieurs fichiers suivis modifiés importent des fichiers **non suivis** (`events.py` → `match_stats.py` ; `api/serializers.py` → `match_stats`, `live_commentary`, `nlg_live` ; `ui/src/routes/PitchView.jsx`, `App.jsx`, `Groups.jsx`, `Bracket.jsx`… → composants/utilitaires UI non suivis). Un commit partiel casserait le build ou l'import.
3. **`pytest` seul échoue sur un checkout propre de `HEAD`** (ticket 8 de `docs/known_issues.md`) : le `pythonpath = ["engine", "."]` de `pyproject.toml` n'est pas commité.
4. **`PitchView.jsx` commité ≠ arbre de travail** (ticket 7).
5. **Fichiers de travail jetables** à la racine (`_coloring.txt`, `_comp_id.txt`, `add_*.py`, `update_*.py` avec chemin codé en dur vers `C:\Users\omariani\Downloads\…`) et **~70 Mo de sorties générées** non ignorées (`data/nlg_samples/`, `graphify-out/`).
6. **Données orphelines** : `scripts/scrape_transfermarkt_coaches.py` écrit encore `data/entraineurs.xlsx`, supprimé dans l'arbre de travail et plus lu par `coaches.py` (qui lit `data/Coachs-Simulafoot.xlsx`).

## 3. Inventaire des fichiers suivis modifiés ou supprimés

Légende risque : **faible** (peut être commité tel quel), **moyen** (relecture ou dépendance), **élevé** (change le comportement sportif/les données, ou rupture si commité seul).

### 3.1 Configuration, lanceur et documentation

| Fichier | Nature | Auteur probable | Testabilité | Risque si commité tel quel |
|---|---|---|---|---|
| `pyproject.toml` | Correction : `pythonpath = ["engine", "."]` (+ commentaire daté 26/09) pour importer le paquet `api` en test | session 26/09 | Requis par `tests/test_serializers.py`, `tests/test_competitions.py` **et** `tests/test_api_animation.py` (commité) | **Faible, et urgent** (ticket 8) |
| `.claude/launch.json` | Config dev : serveurs `api` (8000), `api-8010`, `ui-dev` (5173) | session récente | Sans objet (outillage) | Faible ; la config `api-8010` peut être retirée (décision du propriétaire) |
| `api/main.py` (hors hunk déjà commité) | Docs : « Lancer l'appli.bat » → « simulafoot.bat » ; montage statique `/media/faces` (photos joueurs) | session ~26/09 | Montage conditionnel (`if FACES_DIR.is_dir()`), non testé en soi | Faible |
| `apps/streamlit_preview.py` | 1 ligne de commentaire (« simulafoot.bat ») | idem | Sans objet | Faible |
| `docs/ETAT_ACTUEL.md`, `docs/next_step_canvas.md`, `docs/canvas_integration_state.md` (ligne 64) | Docs : renommage du lanceur | idem | Sans objet | Faible |

### 3.2 Notes des joueurs et attributs FM (« Moyenne joueur fait foi », 26/09)

| Fichier | Nature | Auteur probable | Testabilité | Risque |
|---|---|---|---|---|
| `src/ligue1sim/players.py` (+143) | Refonte : table d'importance des attributs par poste (`_RAW_IMPORTANCE`), `weighted_attributes` ; retrait de `ability`/`note_fm` | sessions 26–28/09 | `tests/test_players.py` (+72, modifié) passe | Moyen : les attributs affichés changent ; API `Player` modifiée (champs retirés) |
| `src/ligue1sim/clubs.py` | Utilise `weighted_attributes` ; retire les colonnes `Ability`/`Note FM` du chargement | 26/09 | `tests/test_clubs.py` (+20, modifié) passe | Moyen : couplé à `players.py` et au classeur |
| `data/joueurs.xlsx` (binaire, 1,28 → 2,11 Mo) | Données : −1 joueur (7 564 → 7 563), **82 « Moyenne joueur » modifiées**, colonnes `Ability`/`Note FM` retirées, onglet `Statuts` remplacé par `Preferred moves`, onglet `Amérique` modifié | propriétaire / scripts d'enrichissement | Aucun diff de données relisible ; les tests utilisent des classeurs de test | **Élevé** : pilote les notes du moteur donc le résultat sportif ; binaire non relisible en revue |
| `scripts/scrape_fminside_attributes.py` | Retire l'écriture d'`Ability`/`Note FM` (consigne du 26/09) | 26/09 | Test dédié supprimé (cf. ci-dessous) | Moyen |
| `tests/test_scrape_fminside_attributes.py` **(supprimé)** | Teste `note_fm_weight_moyenne`, fonction retirée du script | 26/09 | Cohérent avec le script modifié | Faible, **si** le script est commité en même temps |
| `app.py` (19 lignes) | Streamlit : affiche `player.note` au lieu de `note_fm` | 26/09 | Pas de test Streamlit | Moyen : dépend de `players.py` (champ `note_fm` retiré) |

### 3.3 Entraîneurs, styles et statistiques de match

| Fichier | Nature | Auteur probable | Testabilité | Risque |
|---|---|---|---|---|
| `src/ligue1sim/coaches.py` (+195) | Refonte : lit `data/Coachs-Simulafoot.xlsx` (note /100, styles, formation), coachs de sélections | sessions 28–29/09 | `tests/test_coaches.py` (+96, modifié) passe | Élevé : dépend d'un classeur non suivi ; remplace `entraineurs.xlsx` |
| `src/ligue1sim/simulation.py` (+158) | **Moteur Poisson** : modulateurs coach (`COACH_INFLUENCE`, bornes 0,99–1,01) et styles (`STYLE_*`, bornes 0,95–1,05) sur les lambdas ; passage de `suspended_*`/`injured_*`/`*_lambda` à `generate_match_events` | 29/09 | Tests unitaires des modulateurs présents (`TestCoachModifier`, `TestStyleModifiers`) et verts ; effet global sur la distribution des scores **non mesuré** (aucune mesure statistique identifiée) | **Élevé** : change la distribution des scores ; décision de calibrage du propriétaire requise |
| `src/ligue1sim/events.py` (hors hunks commités) | Champs `home_/away_ suspended/injured`, `stats` (possession/tirs/xG), paramètres `*_lambda` | 28–29/09 | `tests/test_events.py` passe | Élevé en isolation : importe `match_stats.py` (non suivi) et `coaches` |
| `src/ligue1sim/match_stats.py` **(nouveau, 113 l.)** | Possession/tirs/tirs cadrés/xG dérivés du score et des lambdas | 29/09 | `tests/test_match_stats.py` (nouveau, 92 l.) passe | Moyen : utilise `np.random` global (peut altérer le flux aléatoire du moteur — à vérifier) |
| `data/Coachs-Simulafoot.xlsx` **(nouveau)**, `data/entraineurs.xlsx` **(supprimé)** | Données entraîneurs : nouveau classeur remplace l'ancien | propriétaire | Lu par `coaches.py` | **Élevé** : suppression + création à commiter ensemble avec `coaches.py` |
| `scripts/scrape_transfermarkt_coaches.py`, `…_national_coaches.py` **(nouveaux)** | Scraping Transfermarkt ; le premier écrit encore `entraineurs.xlsx` (obsolète) | 28–29/09 | Aucun test (réseau) | Moyen : sortie vers un fichier supprimé |

### 3.4 Compétitions (poules, tableau, Ligue des Champions, Coupe du Monde)

| Fichier | Nature | Auteur probable | Testabilité | Risque |
|---|---|---|---|---|
| `src/ligue1sim/champions_league.py` (+220) | **Phase de ligue** à 36 clubs (4 chapeaux, 8 journées, 8 directs, 16 barragistes), minimisation des conflits de championnat | 28–29/09 | `tests/test_champions_league.py` (+138) passe | Moyen : changement de format de compétition |
| `src/ligue1sim/world_cup.py` (+150) | Tirage par confédération, plafonds UEFA par groupe | 29/09 | `tests/test_world_cup.py` (+92) passe | Moyen |
| `src/ligue1sim/knockout.py` (+59) | Tirs au but : scores réalistes, tableau construit par `_seed_order` | 29/09 | `tests/test_knockout.py` (+38) passe | Moyen |
| `src/ligue1sim/custom_competition.py`, `nations.py` | `knockout_legs`/`final_legs`, `knockout_builder`, `league_phase` ; confédérations | 28/09 | `tests/test_nations.py` (+40) passe | Moyen : API publique étendue (valeurs par défaut préservées) |
| `api/routers/competitions.py` (hors hunks commités) | `get_roster`, routes `/bracket/*` ouvertes au format KNOCKOUT, `knockout_legs`/`final_legs` à la création, libellé du match passé à `pitch_view` | 26–29/09 | `tests/test_competitions.py` (nouveau) couvre `get_roster` | Moyen : dépend de `api/serializers.py` / `schemas.py` |

### 3.5 API : sérialisation, commentaire en direct, NLG

| Fichier | Nature | Auteur probable | Testabilité | Risque |
|---|---|---|---|---|
| `api/schemas.py` (+108), `api/serializers.py` (+152) | Nouveaux schémas (banc, indisponibles, stats d'équipe, fil live, effectif) ; `pitch_view` enrichi | 28/09 | `tests/test_serializers.py` (nouveau, 96 l.) passe | Élevé en isolation : `serializers.py` importe `match_stats`, `live_commentary`, `nlg_live` (non suivis) |
| `api/live_commentary.py` **(nouveau, 146 l.)**, `api/nlg_live.py` **(nouveau, 240 l.)** | Fil de commentaire en direct ; appel du générateur NLG (sous-processus, venv `simulafoot_nlg`) | sessions NLG | `tests/test_live_commentary.py`, `tests/test_nlg_live.py` (nouveaux) passent ; les tests de bout en bout NLG sont **ignorés** si le venv NLG est absent | Moyen : dépend du dossier `simulafoot_nlg/` et de son venv |
| `tests/test_competitions.py`, `test_serializers.py`, `test_live_commentary.py`, `test_nlg_live.py`, `test_match_stats.py` **(nouveaux)** | Tests des modules ci-dessus | idem | Passent | Faible, mais inutiles sans les modules qu'ils testent |

### 3.6 Interface PWA (refonte)

Constat : refonte visuelle « maquette FM » (28/09 → 02/10) ; **build OK, 0 erreur de lint, 5 avertissements** ; aucun test JS dans le dépôt (pas de runner), donc aucune testabilité automatisée.

| Fichier(s) | Nature | Auteur probable | Risque |
|---|---|---|---|
| `ui/src/routes/PitchView.jsx` (+403) | Refonte : `LivePanel`, `MatchHeader`, stats, replay en direct, alertes de buts ; contient **déjà** les 4 ajouts d'animation, placés à côté de « Retour » | 28/09–02/10 | **Élevé** : diverge de la version commitée (ticket 7) |
| `ui/src/routes/CustomCompetition.jsx` (+532), `Bracket.jsx` (+319), `Groups.jsx` (+323), `Home.jsx` (+164), `Simulation.jsx` (+107), `Standings.jsx`, `Leaderboards.jsx`, `Leagues.jsx`, `Nations.jsx` | Refonte des écrans (assistant Compétition Perso, tableau, poules/phase de ligue, accueil) | 28–29/09 | Moyen : couplés à l'API (`knockout_legs`, `league_phase`…) |
| `ui/src/App.jsx`, `components/layout/AppShell.jsx`, `Header.jsx`, **`BottomNav.jsx` (supprimé)** | Navigation : bouton d'accueil dans l'en-tête, ruban du bas retiré, routes `TeamRoster`/`PlayerPage` | 28/09 | Moyen : `App.jsx` importe des écrans non suivis |
| `components/simulation/MatchRow.jsx`, `MiniStandings.jsx`, `ScorersLine.jsx`, `components/standings/*`, `index.css`, `store/useGameStore.js` | Composants et thème | 28/09 | Faible à moyen |
| `ui/src/api/client.js` (hors hunk déjà commité) | `getRoster` ; + (cette étape) défaut du port | 26/09 | Faible |
| `ui/vite.config.js` (hors hunk déjà commité) | Couleurs du manifest PWA `#0B0E14` → `#0A1220` | 28/09 | Faible |
| Non suivis : `components/common/` (4 composants), `components/team/` (7), `components/pitch/{GoalAlerts,LivePanel,PitchField}.jsx`, `routes/{PlayerPage,TeamRoster}.jsx`, `utils/{clubInitials,clubSlug,fmAttributes,fmTier,liveReplay,nationalityFlags,playerName,posteCoordinates,posteLabels}.js` | Nouveaux écrans et briques (fiche équipe/joueur, radar FM, fil live) | 28/09–02/10 | Moyen : requis par les fichiers suivis modifiés (dépendances cachées) |
| Non suivis : `ui/public/logos/` (9,5 Mo, 1 dossier `clubs/`), `ui/public/branding/stadium-wallpaper.png` (0,5 Mo) | Images (logos de clubs, fond d'écran) | propriétaire | Moyen : 10 Mo binaires ; droits d'usage des logos à confirmer (non vérifié) |

### 3.7 Fichiers de travail, sorties générées et documentation non suivie

| Fichier(s) | Nature | Auteur probable | Testabilité | Risque |
|---|---|---|---|---|
| `PROJET_SIMULAFOOT.md` (881 l.) | Documentation vivante du projet (rédigée le 28/09) | session 28/09 | Sans objet ; contient des constats **antérieurs** à l'étape actuelle (dates 22–28/09) | Faible, mais à relire/mettre à jour avant commit |
| `add_buildup.py`, `add_goals.py`, `add_nicknames.py`, `add_preferred_moves.py`, `add_prematch.py`, `add_saves.py`, `add_situational.py`, `update_penalties.py`, `update_saves_and_reds.py` | Scripts jetables d'alimentation de la banque de phrases NLG, avec chemin codé en dur `C:\Users\omariani\Downloads\banque_de_phrases_simulafoot.xlsx` | sessions NLG | Aucun | Moyen : pollution de la racine, non portables ; à archiver ou supprimer |
| `_coloring.txt`, `_comp_id.txt` | Sorties de débogage (suite d'entiers ; un identifiant de compétition) | scratch | Sans objet | Faible : à supprimer |
| `data/nlg_samples/` (10 fichiers, **50 Mo**) | Rapports/échantillons générés par le NLG | scratch | Sans objet | **Élevé** pour le dépôt (poids) : ne pas commiter |
| `graphify-out/` (9,8 Mo) | Sortie du skill graphify (graphe de connaissances) | outil | Sans objet | Moyen : généré, à ignorer |

## 4. Carte des dépendances (ce qui ne peut pas être commité seul)

```
pyproject.toml("." dans pythonpath) ───────────────► tests/test_api_animation.py  [DÉJÀ commité : ticket 8]
match_stats.py ─► events.py ─► simulation.py ─► coaches.py ─► data/Coachs-Simulafoot.xlsx (+ suppression entraineurs.xlsx)
match_stats.py + live_commentary.py + nlg_live.py ─► api/serializers.py ─► api/schemas.py ─► api/routers/competitions.py
api (get_roster, pitch stats, KNOCKOUT bracket) ─► ui (TeamRoster, PitchView refonte, Bracket, CustomCompetition)
players.py(weighted_attributes) ─► clubs.py ─► data/joueurs.xlsx ─► app.py (note_fm retiré)
ui/src/components/{common,team,pitch}/* , utils/* ─► ui/src/routes/*.jsx (refonte)
```

## 5. Risques d'un commit « tel quel » de tout l'arbre

- **Résultat sportif modifié sans calibrage validé** (coach/styles dans le Poisson ; 82 notes de joueurs ; −1 joueur).
- **~70 Mo de sorties générées** et 10 Mo d'images dans l'historique.
- **Chemins personnels codés en dur** (`C:\Users\omariani\Downloads\…`) dans 9 scripts.
- **Suppression de `data/entraineurs.xlsx`** alors qu'un script de scraping l'écrit encore.
- **Tests NLG de bout en bout non exécutés** si le venv NLG n'existe pas sur la machine de revue.

## 6. Plan de résorption proposé (NON EXÉCUTÉ — à valider avant exécution)

Principe : des commits **par lot cohérent**, dans l'ordre des dépendances, chacun vérifié par la méthode déjà utilisée (reconstruction « `HEAD` + hunks », export de l'index dans un dossier temporaire, **suite complète** + build/lint UI sur l'export, diff intégral relu). Un lot est commité **seulement si** ses tests passent sur l'export.

### Étape 0 — Immédiat (corrige un défaut de `f70b37d`)
- Commiter le seul hunk `pythonpath = ["engine", "."]` de `pyproject.toml` (ticket 8). Vérifier : `pytest tests` (commande nue) passe sur un `git archive HEAD` propre.

### Catégorie A — Commitables tels quels (périmètre clair, tests verts, risque faible)
1. **Renommage du lanceur** : `api/main.py` (docstring uniquement), `apps/streamlit_preview.py`, `docs/ETAT_ACTUEL.md`, `docs/next_step_canvas.md`, `docs/canvas_integration_state.md` (ligne 64). Documentation seule.
2. **`.claude/launch.json`** (après retrait de la config `api-8010` devenue inutile, décision du propriétaire).
3. **`PROJET_SIMULAFOOT.md`** après relecture et mise à jour de ses constats (il date du 28/09 ; il ignore les étapes `LineupSnapshot` et iframe).

### Catégorie B — Revue préalable nécessaire, puis commit par lot
4. **Lot « Compétitions »** : `champions_league.py`, `world_cup.py`, `knockout.py`, `custom_competition.py`, `nations.py` + leurs tests. Peu de dépendances externes ; relire les règles (phase de ligue, tirage, tirs au but). Tests à relancer sur l'export.
5. **Lot « Notes/attributs FM »** : `players.py`, `clubs.py`, `scripts/scrape_fminside_attributes.py`, suppression de `tests/test_scrape_fminside_attributes.py`, `app.py` + tests. **Prérequis : décision sur `data/joueurs.xlsx`** (82 notes modifiées, −1 joueur : lister les différences dans un rapport lisible avant tout commit du binaire). Commiter le classeur avec le code, jamais séparément.
6. **Lot « Coachs + stats de match + moteur »** : `coaches.py`, `data/Coachs-Simulafoot.xlsx`, suppression de `data/entraineurs.xlsx`, `match_stats.py`, hunks restants de `events.py`, **`simulation.py`** + tests. **Décision explicite du propriétaire requise** sur la calibration (le Poisson change) : mesurer avant/après (scores moyens, buts/match, répartition domicile/extérieur) sur ≥ 1 000 matchs, vérifier que `match_stats` n'altère pas le flux `np.random` du moteur. Mettre à jour/supprimer `scripts/scrape_transfermarkt_coaches.py` (écrit encore `entraineurs.xlsx`).
7. **Lot « API »** : `schemas.py`, `serializers.py`, `live_commentary.py`, `nlg_live.py`, hunks restants de `competitions.py` + 5 fichiers de tests. Dépend des lots 5–6 (`match_stats`, `coaches`). Vérifier le comportement sans le venv NLG (les tests de bout en bout sont ignorés).
8. **Lot « UI refonte »** : composants et écrans listés en §3.6, **y compris la réconciliation de `PitchView.jsx`** (ticket 7 : repartir de la refonte et réintégrer les 4 hunks d'animation à côté de « Retour »). Dépend du lot 7. Vérifier : `vite build`, `oxlint`, lancement en dev, modale d'animation sur un match animable et sur un match sans snapshot. Décider du sort des 10 Mo d'images (`ui/public/logos`, `branding`) : les commiter, les ignorer, ou les sortir du dépôt (droits à confirmer).

### Catégorie C — À abandonner, archiver ou ignorer (ne pas commiter)
9. **Supprimer** (après confirmation du propriétaire) : `_coloring.txt`, `_comp_id.txt`.
10. **Archiver hors dépôt ou supprimer** : `add_*.py`, `update_penalties.py`, `update_saves_and_reds.py` (chemin personnel codé en dur, outils jetables). Si utiles, les déplacer dans `scripts/archive/` en retirant le chemin personnel.
11. **Ajouter à `.gitignore`** : `graphify-out/`, `data/nlg_samples/` (50 Mo générés). Ne jamais les commiter.
12. **Stasher ou conserver localement** tout lot dont la décision est en attente (surtout lot 6), plutôt que de le commiter à moitié.

### Garde-fous pour chaque étape
- Un seul lot par commit ; message qui cite le ticket ou le document concerné.
- Après chaque commit : `git archive HEAD` dans un dossier vierge, `pytest tests` (commande nue), build/lint UI.
- Aucune opération destructive (`checkout --`, `reset --hard`, `clean`) sans sauvegarde et validation explicite : l'arbre de travail est aujourd'hui la **seule copie** de ces modifications.
