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
1. **Le travail préexistant change le résultat sportif.** `src/ligue1sim/simulation.py` ajoute des modulateurs de **coach** (±1 % sur les lambdas) et de **styles de jeu** (jusqu'à ±5 % cumulés) au modèle de Poisson ; `data/joueurs.xlsx` modifie la « Moyenne joueur » (la note qui pilote le moteur) de **82 joueurs** et supprime 1 ligne en double (« Lucas Paquetá », CR Flamengo). Rien de tout cela n'est dans `f70b37d`.
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
| `data/joueurs.xlsx` (binaire, 1,28 → 2,11 Mo) | Données : −1 ligne en double (« Lucas Paquetá », 7 564 → 7 563), **82 « Moyenne joueur » modifiées**, colonnes `Ability`/`Note FM` retirées, onglet `Statuts` remplacé par `Preferred moves`, onglet `Amérique` modifié | propriétaire / scripts d'enrichissement | Aucun diff de données relisible ; les tests utilisent des classeurs de test | **Élevé** : pilote les notes du moteur donc le résultat sportif ; binaire non relisible en revue |
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

- **Résultat sportif modifié sans calibrage validé** (coach/styles dans le Poisson ; 82 notes de joueurs ; −1 ligne en double).
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

### Catégorie B — Revue préalable nécessaire, puis commit par lot *(ordre révisé après essai à blanc : voir §8)*
4. **Lot « Compétitions »** : `champions_league.py`, `world_cup.py`, `knockout.py`, `custom_competition.py`, `nations.py` + leurs tests. Peu de dépendances externes ; relire les règles (phase de ligue, tirage, tirs au but). Tests à relancer sur l'export.
5. **Lot « Notes/attributs FM »** : `players.py`, `clubs.py`, `scripts/scrape_fminside_attributes.py`, suppression de `tests/test_scrape_fminside_attributes.py`, `app.py` + tests. **Prérequis : décision sur `data/joueurs.xlsx`** (82 notes modifiées, −1 ligne en double : lister les différences dans un rapport lisible avant tout commit du binaire). Commiter le classeur avec le code, jamais séparément.
6. **Lot « Coachs + stats de match + moteur »** : `coaches.py`, `data/Coachs-Simulafoot.xlsx`, suppression de `data/entraineurs.xlsx`, `match_stats.py`, hunks restants de `events.py`, **`simulation.py`** + tests. **Décision explicite du propriétaire requise** sur la calibration (le Poisson change) : mesurer avant/après (scores moyens, buts/match, répartition domicile/extérieur) sur ≥ 1 000 matchs, vérifier que `match_stats` n'altère pas le flux `np.random` du moteur. Mettre à jour/supprimer `scripts/scrape_transfermarkt_coaches.py` (écrit encore `entraineurs.xlsx`).
7. **Lot « API »** : `schemas.py`, `serializers.py`, `live_commentary.py`, `nlg_live.py`, hunks restants de `competitions.py` + 5 fichiers de tests. Dépend des lots 5–6 (`match_stats`, `coaches`). Vérifier le comportement sans le venv NLG (les tests de bout en bout sont ignorés).
8. **Lot « UI refonte »** : composants et écrans listés en §3.6, **y compris la réconciliation de `PitchView.jsx`** (ticket 7 : repartir de la refonte et réintégrer les 4 hunks d'animation à côté de « Retour »). Dépend du lot 7. Vérifier : `vite build`, `oxlint`, lancement en dev, modale d'animation sur un match animable et sur un match sans snapshot. Décider du sort des 10 Mo d'images (`ui/public/logos`, `branding`) : les commiter, les ignorer, ou les sortir du dépôt (droits à confirmer).

### Catégorie C — À abandonner, archiver ou ignorer (ne pas commiter)
9. ~~**Supprimer** `_coloring.txt`, `_comp_id.txt`.~~ **Fait le 07/10/2026** (voir §7).
10. ~~**Archiver** `add_*.py`, `update_penalties.py`, `update_saves_and_reds.py`.~~ **Fait le 07/10/2026** : déplacés dans `scripts/archive/` (dossier ignoré par git, non supprimés ; voir §7).
11. ~~**Ajouter à `.gitignore`** `graphify-out/`, `data/nlg_samples/`.~~ **Fait le 07/10/2026** (voir §7, avec une réserve : un fichier de `data/nlg_samples/` est déjà suivi).
12. **Stasher ou conserver localement** tout lot dont la décision est en attente (surtout lot 6), plutôt que de le commiter à moitié.

### Garde-fous pour chaque étape
- Un seul lot par commit ; message qui cite le ticket ou le document concerné.
- Après chaque commit : `git archive HEAD` dans un dossier vierge, `pytest tests` (commande nue), build/lint UI.
- Aucune opération destructive (`checkout --`, `reset --hard`, `clean`) sans sauvegarde et validation explicite : l'arbre de travail est aujourd'hui la **seule copie** de ces modifications.

## 7. Nettoyage de la Catégorie C — exécuté le 07/10/2026

Aucun fichier de code suivi n'a été modifié. Le commit de nettoyage ne contient que `.gitignore` et ce document.

| Élément | Action | Résultat / justification |
|---|---|---|
| `graphify-out/` | Ajouté à `.gitignore` | Aucun fichier suivi par git (0) ; sortie générée de l'outil graphify (~9,8 Mo) |
| `data/nlg_samples/` | Ajouté à `.gitignore` | Les 10 fichiers non suivis (~50 Mo) ne figurent plus dans `git status`. **Réserve : `data/nlg_samples/conditions_larges.md` (4 384 octets) est déjà suivi par git** ; la règle d'ignorance ne le retire pas du suivi et il n'a pas été retiré (validation explicite requise pour le sortir de l'index) |
| `_coloring.txt` (287 o : suite d'entiers), `_comp_id.txt` (37 o : un identifiant de compétition) | **Supprimés** | Fichiers d'outillage sans usage produit ; aucune référence trouvée dans les fichiers suivis ni dans les notes ; jamais suivis par git (donc pas de trace dans un commit) |
| `add_buildup.py`, `add_goals.py`, `add_nicknames.py`, `add_preferred_moves.py`, `add_prematch.py`, `add_saves.py`, `add_situational.py`, `update_penalties.py`, `update_saves_and_reds.py` | **Déplacés, non supprimés**, de la racine vers **`scripts/archive/`** | Chacun contient le chemin codé en dur `C:\Users\omariani\Downloads\banque_de_phrases_simulafoot.xlsx` ; aucun n'est importé. `scripts/archive/` est **ignoré par git** (`.gitignore`) : ces 9 fichiers n'existent donc plus **que sur ce poste** (copie locale unique, non versionnée) — à sauvegarder si leur historique compte. Une note tracée, `simulafoot_nlg/data/seed/AUDIT_COUVERTURE_DONNEES_JOUEUR.md` (§2), analyse `add_preferred_moves.py` à son ancien emplacement racine : le chemin cité n'existe plus |
| `scripts/scrape_transfermarkt_coaches.py` (puis `…_national_coaches.py`) | ~~Laissé en place~~ → **archivés ensemble dans `scripts/archive/` le 07/10/2026 (§8.10)** | **Non prouvé orphelin** : `scripts/scrape_transfermarkt_national_coaches.py` l'importe (`from scrape_transfermarkt_coaches import …`, ligne 44). Les deux écrivent `data/entraineurs.xlsx`, supprimé dans l'arbre de travail (suppression non commitée) mais encore lu par le `coaches.py` de `HEAD`. Décision reportée au Lot 3 de la séquence de résorption Catégorie B |

## 8. Séquence de résorption Catégorie B (proposée, NON exécutée)

Rédigée le 07/10/2026 après un **essai à blanc** (§8.2). Elle **remplace l'ordre indicatif du §6** pour la Catégorie B. Aucun commit de la Catégorie B n'a été fait ; les décisions préalables (D1, D2) reviennent au Chef d'Orchestre et au propriétaire du projet. **L'arbre de travail est la seule copie de ces modifications.**

### 8.1 Règles communes à chaque lot

1. **Un lot = un commit**, construit par la méthode « `HEAD` + hunks du lot » (reconstruction du contenu, jamais de `git add -p` interactif ni de `git checkout --`).
2. **Vérification obligatoire** : `git archive HEAD` (après le commit) dans un dossier vierge, puis `pytest tests` **commande nue** : la collecte doit réussir et la suite être verte. Pour le Lot 5 : build, lint et lancement en dev en plus.
3. **Aucune opération destructive sans validation** (`reset --hard`, `clean`, `checkout --`, suppression de fichiers). Avant de commencer : sauvegarde complète (`git diff HEAD > sauvegarde.patch` + copie des fichiers non suivis) hors du dépôt.
4. Un lot dont la vérification échoue **n'est pas commité** ; l'écart est consigné ici.

### 8.2 Essai à blanc du 07/10/2026 (copie de `HEAD`, aucune modification du dépôt)

Superposition **cumulative** des fichiers de l'arbre de travail sur un `git archive HEAD`, suite complète (`pytest tests` nu) après chaque étape :

| Étape | Résultat | Lecture |
|---|---|---|
| Lot 1 seul (Compétitions) | **10 échecs**, 983 verts | 9× `TypeError: simulate_match() got an unexpected keyword argument 'suspended_home'` (`knockout.py` appelle `simulate_match` avec des paramètres qui n'existent que dans le `simulation.py` du Lot 3) ; 1× `test_nations.py::test_load_national_teams_returns_only_complete_squads_of_18` (dépend des données de `data/joueurs.xlsx`, Lot 2) |
| Lots 1 + 2 | **9 échecs**, 987 verts | Les 9 échecs restants sont tous le même `TypeError` (vérifié) |
| Lots 1 + 2 + 3 | **1015 verts**, 5 ignorés | Vert |
| Lots 1 + 2 + 3 + 4 | **1041 verts**, 5 ignorés (= 1046, total de l'arbre de travail) | Vert ; les 5 ignorés sont les tests NLG de bout en bout (venv `simulafoot_nlg` absent des archives ; présent sur ce poste) |
| Lot 5 (UI) sur `HEAD` | `vite build` OK (0 occurrence de `localhost:8000` dans le bundle) ; `oxlint` **0 erreur, 5 avertissements** (référence) ; les 4 hunks d'animation sont déjà présents dans le `PitchView.jsx` de l'arbre de travail | Vert (lancement en dev non rejoué dans l'essai : il l'a été sur l'arbre de travail aux étapes précédentes) |

**Conséquence : l'ordre « Lot 1 → 2 → 3 » est impossible avec une suite verte.** Le Lot 1 dépend (a) d'un **extrait du Lot 3** (voir 3a) et (b) des **données du Lot 2** pour un test. Comme le Lot 2 est bloqué par D1 et le Lot 3 par D2, le Lot 1 ne peut pas être commité tel que défini tant qu'on n'en sépare pas ces dépendances.

### 8.3 Décisions préalables (hors périmètre de l'exécutant)

- **D1 — `data/joueurs.xlsx`** (Lot 2). Faits mesurés (lecture seule, comparaison `HEAD` / arbre de travail) : **82 « Moyenne joueur » modifiées** (60 hausses, 22 baisses ; médiane des écarts absolus 1,0 ; 17 écarts ≥ 5 ; maximum +50,5, ex. 19,5 → 70,0 pour « Flores », CA Boca Juniors) ; **1 ligne retirée, qui est un doublon** (7 564 → 7 563 : « Lucas Paquetá », CR Flamengo, note 81, présent deux fois dans `HEAD` ; voir §8.7) ; colonnes `Ability (0-99)` et `Note FM` supprimées ; onglet `Statuts` remplacé par `Preferred moves` ; onglet `Amérique` modifié. À décider : valider tel quel, corriger (ex. le joueur retiré, les notes aberrantes), ou écarter. **D1 tranchée par le propriétaire le 07/10/2026 (voir §8.8) : les changements sont volontaires et le Lot 2 est commité.**
- **D2 — calibration** (Lot 3, partie 3c). Voir le protocole de mesure ci-dessous ; **aucun commit du modulateur sans mesure**.

### 8.4 Lots

#### Lot 1 — Compétitions
- **Périmètre exact** : `src/ligue1sim/champions_league.py`, `world_cup.py`, `knockout.py`, `custom_competition.py`, `nations.py` ; tests `tests/test_champions_league.py`, `test_world_cup.py`, `test_knockout.py`, `test_nations.py`. Contenu : phase de ligue (36 clubs, 4 chapeaux, 8 journées, 8 directs, 16 barragistes), tirage de la Coupe du Monde par confédération, tirs au but, `knockout_legs`/`final_legs`, `knockout_builder`, `league_phase`.
- **Dépendances non suivies à inclure** : aucun fichier non suivi (aucun import vers `match_stats`, `live_commentary`, `nlg_live`). **Dépendances sur d'autres lots (mises en évidence par l'essai)** : (a) **3a** pour `simulate_match(..., suspended_*/injured_*)` ; (b) **Lot 2** pour le test `test_load_national_teams_returns_only_complete_squads_of_18` (données). Options : exécuter le Lot 1 **après** 3a et le Lot 2, ou **scinder** `nations.py`/`test_nations.py` pour laisser dans le Lot 2 ce qui dépend des données (à valider à l'exécution).
- **Prérequis** : 3a commité ; relecture des règles (phase de ligue, tirage, tirs au but).
- **Critère de vérification** : §8.1 ; les 9 tests de simulation de tournoi (`test_knockout`, `test_custom_competition`, `test_world_cup`, `test_champions_league`) et `test_nations` verts sur `git archive HEAD`.
- **Statut** : **FAIT** — commit `7fa9f68` (996 verts sur archive propre), avec `tests/test_nations.py` scindé ; voir §8.8. *(Statuts antérieurs : « bloqué », puis « prêt à commiter ».)*

#### Lot 2 — Notes et attributs FM
- **Périmètre exact** : `src/ligue1sim/players.py`, `clubs.py` ; `scripts/scrape_fminside_attributes.py` ; `app.py` (Streamlit : `player.note` au lieu de `note_fm`) ; tests `tests/test_players.py`, `tests/test_clubs.py` ; **suppression** de `tests/test_scrape_fminside_attributes.py` (teste une fonction retirée) ; **`data/joueurs.xlsx`**, commité **avec** le code, jamais séparément.
- **Dépendances non suivies à inclure** : aucune.
- **Prérequis** : **D1** (décision explicite du propriétaire sur `data/joueurs.xlsx`). Produire d'abord un rapport lisible des 82 écarts et du joueur retiré (la liste complète, pas seulement la synthèse de §8.3).
- **Critère de vérification** : §8.1 ; contrôle que la suite lit bien le classeur commité (pas une copie locale).
- **Statut** : **FAIT** — D1 tranchée par le propriétaire ; commit `ddfad09` (999 verts sur archive propre) ; voir §8.8. *(Statut antérieur : « bloqué » par D1.)*

#### Lot 3 — Coachs, `match_stats`, moteur *(proposé : scindé en 3a / 3b / 3c)*
Les trois parties se trouvent dans les mêmes fichiers (`events.py`, `simulation.py`) : elles se séparent **par hunks**. Cette scission **n'a pas été validée par un essai à blanc** (seul l'ensemble 1+2+3 l'a été) ; elle commite des parties du Lot 3 **avant** la mesure D2, sans y inclure les modulateurs : elle exige donc une **validation explicite** du propriétaire.

- **3a — Affichage des absents (sans effet sportif)** : champs `home_/away_ suspended/injured` de `events.py`, paramètres `suspended_*`/`injured_*` de `simulation.simulate_match` et de la boucle de saison. Débloque le Lot 1. Vérification : suite verte sur `git archive HEAD` ; aucun test de score modifié.
- **3b — Couche de données coachs et statistiques de match** : `src/ligue1sim/coaches.py`, `data/Coachs-Simulafoot.xlsx` (nouveau), **suppression** de `data/entraineurs.xlsx`, `src/ligue1sim/match_stats.py` (nouveau), hunks `stats` / `home_lambda` / `away_lambda` de `events.py` et de `simulation.py` ; tests `tests/test_coaches.py`, `tests/test_match_stats.py` ; `scripts/scrape_transfermarkt_national_coaches.py` et `scripts/scrape_transfermarkt_coaches.py` (ce dernier est importé par le premier ; tous deux écrivent encore `data/entraineurs.xlsx`, supprimé : décider de les mettre à jour vers `Coachs-Simulafoot.xlsx` ou de les archiver ensemble). **Point de vigilance** : `match_stats` consomme `np.random` (flux global) après chaque match : il ne modifie pas la distribution des scores d'un match, mais décale la séquence aléatoire des matchs suivants ; le vérifier avant commit.
- **3c — Modulateurs du modèle de Poisson (change le résultat sportif)** : dans `simulation.py`, `COACH_INFLUENCE`, `_COACH_MODIFIER_BOUNDS`, `STYLE_*`, `_coach_modifier`, `_style_attack_modifier`, `_style_defense_modifier` et leur application aux lambdas ; tests `TestCoachModifier`, `TestStyleModifiers` de `tests/test_simulation.py`. **Prérequis : D2 — mesure comparative avant commit.**
  - **Protocole de mesure proposé** : ≥ 1 000 matchs par bras (5 000 recommandés), mêmes affiches, domicile/extérieur équilibrés, **deux bras** : A = sans modulateurs (modulateurs neutralisés à 1,0, équivalent au `simulation.py` de `HEAD`), B = avec modulateurs (arbre de travail). Graines indépendantes par bras (le flux `np.random` étant décalé par `match_stats`, ne pas apparier match à match).
  - **Mesures** : moyenne de buts par match (total, domicile, extérieur) ; **écart-type** du total ; **queue** : P(total ≥ 5), P(total ≥ 6), P(un score ≥ 4), quantiles 90/95/99 % ; histogramme 0…7+ ; % victoire domicile / nul / victoire extérieure ; **dispersion de la hiérarchie** (points moyens par club selon sa note de compo) — l'effet attendu porte surtout sur la dispersion des forces, pas sur la moyenne globale (ratio coach jusqu'à ±2 % sur les lambdas, ratio de styles jusqu'à ±10 % entre attaque et défense).
  - **Tests** : intervalle de confiance bootstrap à 95 % de la différence de moyennes ; Kolmogorov-Smirnov bi-échantillon sur le total de buts ; χ² sur l'histogramme ; proportions pour les queues.
  - **Seuil proposé** (à confirmer par le propriétaire) : écart **significatif** si l'IC 95 % de Δ(moyenne du total) exclut 0 **et** |Δ| ≥ 0,03 but/match (≈ 1 %), ou si ΔP(queue) ≥ 0,5 point, ou si Δ(victoires à domicile) ≥ 1 point. **Si significatif : décision explicite** (accepter, recalibrer `COACH_INFLUENCE`/`STYLE_*`, ou abandonner) **avant** tout commit.
- **Critère de vérification (chaque partie)** : §8.1.
- **Statut** : 3a **fait** (`f5e37de`) et 3b **fait** (`3070543`, scission validée par le propriétaire) ; **3c BLOQUÉ** : mesure D2 (§8.11) et balayage d'amplitudes (§8.12) faits, décision du propriétaire sur l'amplitude (ou l'abandon) en attente.

#### Lot 4 — API
- **Périmètre exact** : `api/schemas.py`, `api/serializers.py`, `api/live_commentary.py` (nouveau), `api/nlg_live.py` (nouveau), `api/routers/competitions.py` (hunks restants : `get_roster`, routes `/bracket/*` pour le format KNOCKOUT, `knockout_legs`/`final_legs`, libellé du match), `api/main.py` (hunk `/media/faces` restant) ; tests `tests/test_competitions.py`, `test_serializers.py`, `test_live_commentary.py`, `test_nlg_live.py` (nouveaux).
- **Dépendances non suivies à inclure** : `api/live_commentary.py`, `api/nlg_live.py` (importés par `serializers.py`) et `src/ligue1sim/match_stats.py` (Lot 3b). Imports de `serializers.py` vers d'autres lots : `champions_league.DIRECT_SPOTS`/`PLAYOFF_SPOTS` (Lot 1), `coaches.coach_name` (3b), `players.Player` (Lot 2), `match_stats.TeamMatchStats` (3b). `ligue1sim.faces` et `kits` sont déjà suivis.
- **Prérequis** : Lots 1, 2, 3a, 3b commités (essai : vert uniquement avec 1+2+3 cumulés).
- **Critère de vérification** : §8.1 ; exécuter aussi la suite **sur ce poste** (venv `simulafoot_nlg` présent) pour couvrir les 5 tests NLG ignorés dans une archive propre.
- **Statut** : bloqué (dépend des lots précédents).

#### Lot 5 — Refonte UI, avec réconciliation de `PitchView.jsx` (ticket 7)
- **Périmètre exact** : tous les fichiers de `ui/src` modifiés (écrans, `components/layout`, `simulation`, `standings`, `index.css`, `store/useGameStore.js`), la **suppression** de `components/layout/BottomNav.jsx`, les fichiers non suivis (`components/common/`, `components/team/`, `components/pitch/{GoalAlerts,LivePanel,PitchField}.jsx`, `routes/{PlayerPage,TeamRoster}.jsx`, `utils/{clubInitials,clubSlug,fmAttributes,fmTier,liveReplay,nationalityFlags,playerName,posteCoordinates,posteLabels}.js`), le hunk `getRoster` de `ui/src/api/client.js`, le hunk couleurs de `ui/vite.config.js`, et `ui/public/{branding,logos}` (10 Mo : décision à prendre — commiter, ignorer ou sortir du dépôt ; droits d'usage des logos non vérifiés).
- **Réconciliation de `PitchView.jsx`** : l'essai montre que la version de l'arbre de travail contient **déjà** les 4 hunks d'animation (import `MatchAnimation`, état `showAnimation`, bouton « Voir l'animation » à côté de « Retour », composant `AnimationDialog`). La réintégration consiste donc à **commiter ce fichier tel quel** après vérification, ce qui remplace la version adaptée au contexte `HEAD` (ticket 7).
- **Dépendances non suivies à inclure** : tous les fichiers non suivis ci-dessus ; dépend du **Lot 4** à l'exécution (endpoints `roster`, stats de match, fil live) pour le test en dev.
- **Critère de vérification** : `vite build` ; `oxlint` (0 erreur ; 5 avertissements = référence actuelle, ne pas en ajouter) ; **lancement en dev sans `.env.local`** (l'API doit être jointe sur 8000) ; modale d'animation fonctionnelle sur un match animable **et** sur un match sans snapshot (message §2.10, aucune iframe) ; puis §8.1 pour la partie Python.
- **Statut** : bloqué (dépend du Lot 4). Clôture du ticket 7 à la fin de ce lot.

### 8.5 Ordre d'exécution recommandé

**3a (fait, `f5e37de`)** → **Lot 1 (fait, `7fa9f68`)** → **Lot 2 (fait, `ddfad09`)** → **3b (fait, `3070543`)** → **mesure D2 (faite, §8.11)** → **décision D4 (option C : balayage d'amplitudes)** → **balayage d'amplitudes (fait, §8.12)** → **décision du propriétaire sur l'amplitude de 3c (en attente)** → **3c (commit à l'amplitude retenue, ou abandon)** → **Lot 4** → **Lot 5**. *(Révisé le 07/10/2026 ; voir §8.7, §8.8, §8.10, §8.11 et §8.12.)*
Les éléments qui ne dépendent d'aucune décision (3a, le Lot 1 scindé, éventuellement 3b après validation de la scission) peuvent passer avant `D1`. 3c reste **bloqué** par D2.

### 8.6 Hors séquence — `PROJET_SIMULAFOOT.md` (non commité, bloqué)

Le document (881 lignes, mis à jour le 28/09/2026) **n'est pas cohérent avec l'état commité** : il décrit comme acquis `players.weighted_attributes` (4 mentions) et le retrait de `Ability`/`Note FM`, alors que `HEAD` n'a pas `weighted_attributes` (0 occurrence dans `src/`) et que `Player.note_fm` existe encore (2 occurrences) ; il décrit aussi des écrans non commités (`TeamRoster`, `PlayerPage`). Il ignore en outre les étapes commitées depuis (`LineupSnapshot`, iframe d'animation, `known_issues.md`). Le commiter maintenant documenterait du code absent de `HEAD`. **À mettre à jour (entrée de changelog, état réel) puis commiter après le Lot 2**, ou en dernier.

### 8.7 Avancement du 07/10/2026 — 3a commité, Lot 1 vérifié (note de suivi)

**Aucune décision n'a été prise sur D1 ni sur D2 : elles restent en attente de décision du propriétaire.** Les Lots 2, 3b, 3c, 4 et 5 et `PROJET_SIMULAFOOT.md` ne sont **pas** commités ; `data/joueurs.xlsx` n'a pas été touché ; aucune modulation du modèle de Poisson n'a été commitée.

**1. 3a identifié (contenu exact).** Il se limite à la transmission de la **raison** des absences (suspension / blessure), sans aucun changement des lambdas de Poisson :
- `src/ligue1sim/events.py` — 3 hunks : les 4 champs `home_suspended` / `home_injured` / `away_suspended` / `away_injured` de `MatchEvents` (avec leur commentaire) ; les 4 paramètres `suspended_*` / `injured_*` de `generate_match_events` ; les 4 arguments correspondants dans le `return MatchEvents(...)`.
- `src/ligue1sim/simulation.py` — 4 hunks : les 4 paramètres de la signature de `simulate_match` ; le paragraphe de docstring qui les décrit ; leur transmission à `generate_match_events` ; `simulate_journee`, qui sépare désormais suspensions et blessures avant de les fusionner en `unavailable_*` (la compo reste décidée par l'ensemble fusionné).
- **Exclus de 3a** (restent dans 3b / 3c) : les imports `coaches` et `match_stats`, le champ `stats`, les paramètres `home_lambda` / `away_lambda`, l'appel `compute_match_stats` (3b) ; `COACH_INFLUENCE`, `STYLE_*`, `_coach_modifier`, `_style_*_modifier` et leur application aux lambdas (3c).
- **Tests ajoutés avec 3a** (`tests/test_events.py`, 3 tests) : valeurs par défaut et enregistrement des raisons ; **même graine ⇒ même score, mêmes buts, même compo** avec ou sans raisons (preuve que 3a n'influence pas le match) ; `simulate_journee` distingue suspension et blessure.

**2. Essai à blanc de 3a** (dans un clone jetable du dépôt, supprimé après usage : le dépôt réel n'a reçu aucun commit temporaire ni aucun `reset`) : `git archive` du commit temporaire, `pytest tests` nu → **985 passés** (982 + les 3 nouveaux tests), 5 ignorés (NLG), 12 désélectionnés. Résultat : **vert**.

**3. 3a commité** : `f5e37de` (`feat(sim): raison des absences … lot 3a`). Vérification sur `git archive HEAD` propre, `pytest` nu : **985 passés, 5 ignorés**.

**4. Faisabilité du Lot 1 après 3a** (essai à blanc sur `git archive HEAD` de `f5e37de`, aucun fichier du dépôt modifié) :
- Lot 1 **intégral** : **33 tests verts, 1 échec** (sur les 5 fichiers de test concernés). Les **9 `TypeError: simulate_match() got an unexpected keyword argument 'suspended_home'` ont disparu** (3a les résout). Le seul échec restant est `test_nations.py::test_load_national_teams_returns_only_complete_squads_of_18` : l'assertion modifiée (Brésil attendu à 17 joueurs) dépend des **données** du Lot 2.
- Lot 1 **scindé** : `nations.py` en entier ; `tests/test_nations.py` = version de `HEAD` + imports + le **nouveau** test `test_as_national_player_keeps_the_enriched_fm26_fields` (code pur : `_as_national_player` conserve les champs FM26 enrichis). **Reste dans le Lot 2** : l'assertion `counts … Brésil 17` et son commentaire (dépendent du classeur). Les 9 tests de simulation de tournoi sont verts.
- **Réponse : le Lot 1 peut être commité seul, sans les Lots 2, 3b, 3c, 4, 5, à condition de scinder `test_nations.py` comme ci-dessus.** Aucune autre dépendance manquante n'a été trouvée (aucun import vers `coaches`, `match_stats`, `live_commentary`, `nlg_live`).

**5. Superposition 3a + Lot 1 (scindé)** : suite complète sur `git archive`, `pytest` nu → **996 passés, 5 ignorés**. Résultat : **vert**. (3a étant déjà dans `HEAD`, cette superposition est l'état exact qu'obtiendrait le commit du Lot 1.)

**6. Conséquences sur la séquence.** L'ordre recommandé du §8.5 est **modifié pour une raison factuelle** (le Lot 1 n'a plus besoin du Lot 2 une fois `test_nations.py` scindé) : **3a (fait) → Lot 1 → `D1` → Lot 2 → 3b → `D2` → 3c → Lot 4 → Lot 5.** Les autres lots, leurs périmètres et leurs prérequis sont inchangés.

**7. Précision sur D1 (fait nouveau, vérifié en lecture seule).** Le « joueur retiré » n'est **pas** un joueur perdu : `HEAD` contient **deux lignes identiques « Lucas Paquetá », CR Flamengo, note 81** (IDs 2358 et 6252) ; l'arbre de travail supprime la ligne d'ID 6252 (doublon de saisie, documenté par un commentaire de `tests/test_nations.py` du 28/09/2026) et conserve la ligne d'ID 2358 avec une note de **79,0** (modifiée parmi les 82 écarts). Cela réduit la portée de « −1 joueur » à « −1 ligne en double », mais ne règle pas la décision D1 sur les 82 notes modifiées.

### 8.8 Avancement du 07/10/2026 (suite) — Lot 1 et Lot 2 commités, D1 résolue

**Séquence mise à jour : 3a (fait) → Lot 1 (fait) → Lot 2 (fait) → 3b → D2 (mesure + décision) → 3c → Lot 4 → Lot 5.** `PROJET_SIMULAFOOT.md` reste non commité (voir la fin de ce paragraphe).

**Commit Lot 1 — `7fa9f68`** (`feat(competitions): phase de ligue, tirage par confédération, tirs au but, formats perso — lot 1`).
- **Périmètre exact (9 fichiers)** : `src/ligue1sim/champions_league.py`, `world_cup.py`, `knockout.py`, `custom_competition.py`, `nations.py` ; `tests/test_champions_league.py`, `test_world_cup.py`, `test_knockout.py`, `test_nations.py` (**scindé** : version de `HEAD` + imports + le nouveau test `test_as_national_player_keeps_the_enriched_fm26_fields` ; l'assertion « Brésil 17 » et son commentaire en sont exclus).
- **Écart avec la consigne initiale (consigné pour mémoire)** : la liste « `nations.py` + `test_nations.py`, aucun autre fichier » ne pouvait pas couvrir le Lot 1 prouvé à 996 verts (les 9 tests qui échouaient dépendent de `knockout.py`, `world_cup.py`, `champions_league.py`, `custom_competition.py`). Le commit contient donc le **périmètre complet du Lot 1 défini au §8.4**, avec la scission annoncée.
- **Vérification** : `git archive HEAD` propre, `pytest tests` nu → **996 passés, 5 ignorés** (tests NLG, venv absent de l'archive). Les 9 tests qui échouaient avec `simulate_match() got an unexpected keyword argument 'suspended_home'` passent tous.

**Commit Lot 2 — `ddfad09`** (`feat(data): Moyenne joueur fait foi — retrait d'Ability/Note FM, attributs recalés, joueurs.xlsx — lot 2`).
- **Périmètre exact (9 fichiers)** : `data/joueurs.xlsx` ; code strictement lié : `src/ligue1sim/players.py` (`weighted_attributes`, retrait des champs `ability`/`note_fm`), `src/ligue1sim/clubs.py`, `scripts/scrape_fminside_attributes.py`, `app.py` ; tests `tests/test_players.py`, `tests/test_clubs.py` ; **suppression** de `tests/test_scrape_fminside_attributes.py` ; `tests/test_nations.py` (l'assertion « Brésil 17 » + son commentaire).
- **Périmètre vérifié avant commit** : toutes les références à `note_fm` / `ability` / `NOTE_FM_*` / `Ability (0-99)` / `Note FM` du code suivi se trouvent dans ces seuls fichiers ; aucun autre lot n'en dépend. Aucun code ne lit les onglets `Statuts` ni `Preferred moves` ; le chargement de la **colonne** « Preferred moves » (`PREFERRED_MOVES_COLUMN`, `Player.preferred_moves`) existe déjà dans `HEAD` : aucun code « attributs préférés » n'était à ajouter.
- **Vérification** : essai à blanc sur copie de `HEAD` (999 passés), puis après commit, `git archive HEAD` propre, `pytest` nu → **999 passés, 5 ignorés**, dont `test_load_national_teams_returns_only_complete_squads_of_18`.

**Superposition 3a + Lot 1 + Lot 2** (`git archive HEAD` propre, `pytest` nu) : **999 passés, 5 ignorés**. Avec le venv NLG local rendu accessible à l'archive (jonction vers `simulafoot_nlg/.venv`, retirée ensuite), les 5 tests NLG s'exécutent : **1004 passés, 0 ignoré, 12 désélectionnés** (tests d'intégration). Les tests NLG ne sont donc pas ignorés par défaut seulement parce que ce venv, ignoré par git, n'existe pas dans une archive propre.

**Décision D1 — tranchée par le propriétaire.** Les modifications de `data/joueurs.xlsx` sont **volontaires et conservées** : **82 « Moyenne joueur » modifiées** ; **doublon « Lucas Paquetá » (CR Flamengo, ID 6252) supprimé** (l'ID 2358 est conservé, note 79,0 au lieu de 81) ; **colonnes `Ability (0-99)` et `Note FM` supprimées** ; **onglet `Statuts` remplacé par l'onglet `Preferred moves`** (et onglet `Amérique` modifié). Ces changements sont commités avec leur code (`ddfad09`).

**Décision D2 — reste en attente du propriétaire.** Les modulateurs coach (±1 %) et styles (jusqu'à ±5 %) du modèle de Poisson ne sont **pas** commités. **Mesure comparative obligatoire (≥ 1 000 matchs par bras, protocole du §8.4, partie 3c) avant tout commit de 3c.** Aucun commit de 3b, 3c, Lot 4, Lot 5.

**`PROJET_SIMULAFOOT.md`** : toujours non commité. Le Lot 2 étant commité, sa mise à jour est possible, mais il décrit encore des écrans et des modules non commités (`TeamRoster`, `PlayerPage`, etc.) ; il restera bloqué tant que ces lots ne sont pas commités, ou jusqu'à sa réécriture sur l'état réel.

### 8.9 Étape suivante (préparée, NON exécutée) — commit de 3b : couche coachs et `match_stats`

- **Périmètre attendu** (relevé le 07/10/2026 sur l'arbre de travail) :
  - `src/ligue1sim/coaches.py` (lecture de `data/Coachs-Simulafoot.xlsx` : note /100, styles, formation ; sélectionneurs) ;
  - `data/Coachs-Simulafoot.xlsx` (nouveau) et **suppression** de `data/entraineurs.xlsx` (le `coaches.py` de `HEAD` le lit encore : à commiter ensemble) ;
  - `src/ligue1sim/match_stats.py` (nouveau : possession, tirs, tirs cadrés, xG) ;
  - `src/ligue1sim/events.py` : les **7 hunks restants** (imports `coaches` et `match_stats`, champ `stats`, paramètres `home_lambda` / `away_lambda` et leur docstring, appel `compute_match_stats`, argument `stats=`) — depuis 3a, tout ce qui reste de `events.py` relève de 3b ;
  - `src/ligue1sim/simulation.py` : **un seul hunk** (2 lignes : `home_lambda=lambda_home`, `away_lambda=lambda_away` dans l'appel à `generate_match_events`) ; les autres hunks restants (import `coaches`, constantes `COACH_INFLUENCE` / `STYLE_*`, application aux lambdas dans `_draw_score`, fonctions `_coach_modifier` / `_style_*_modifier`) sont du **3c** et **ne doivent pas** être inclus ;
  - tests `tests/test_coaches.py` (modifié) et `tests/test_match_stats.py` (nouveau) ;
  - décision à prendre sur `scripts/scrape_transfermarkt_coaches.py` et `scripts/scrape_transfermarkt_national_coaches.py` (le second importe le premier ; tous deux écrivent encore `data/entraineurs.xlsx`, supprimé) : les mettre à jour vers `Coachs-Simulafoot.xlsx` ou les archiver ensemble.
- **Prérequis** : 3a, Lot 1 et Lot 2 commités (fait) ; validation explicite de la scission 3b / 3c par le propriétaire (la séquence « 3b puis D2 puis 3c » la présuppose) ; vérification que 3b **n'embarque aucun modulateur** (`grep` de `COACH_INFLUENCE`, `STYLE_`, `_coach_modifier` dans les fichiers stagés : 0 occurrence).
- **Critère de vérification** : (1) méthode « `HEAD` + hunks », essai à blanc sur copie de `HEAD` puis `git archive HEAD` propre et `pytest` nu (collecte OK, suite verte) ; (2) **point de vigilance `np.random`** : `match_stats` consomme le flux aléatoire global après chaque match, ce qui décale la séquence des matchs suivants sans changer la distribution d'un match — vérifier sur ≥ 1 000 matchs, 3b seul (modulateurs absents), que moyenne et écart-type des buts ne varient pas de façon significative par rapport à `HEAD` ; (3) `coaches.py` et le nouveau classeur chargent sans erreur sur une archive propre.
- **Statut** : **FAIT** — commit `3070543` (voir §8.10). *(Statut antérieur : « non exécuté ».)*

### 8.10 Avancement du 07/10/2026 (suite) — 3b commité

**Séquence mise à jour : 3a (fait) → Lot 1 (fait) → Lot 2 (fait) → 3b (fait) → D2 (mesure + décision) → 3c → Lot 4 → Lot 5.** `PROJET_SIMULAFOOT.md` reste non commité.

**1. Vérification du flux `np.random` (avant commit, archives jetables, jamais sur l'arbre de travail).**
- **Dispositif** : A = `HEAD` avant 3b (`7003bf0`) ; B = A + 3b ; **B′ = B avec les dispositifs préférentiels de A imposés** (isole le code de 3b : `match_stats` et `coaches`). Ligue 1 réelle (18 clubs, 306 affiches ordonnées jouées en boucle), `simulate_match` complet (événements et statistiques inclus). Deux modes : **apparié** (graines `random` et `numpy` refixées avant chaque match : le score d'un match ne dépend que de son numéro) et **flux continu** (une graine, matchs à la suite : la séquence aléatoire est partagée, donc décalée si 3b consomme `np.random`).
- **Résultats bruts, 1 000 matchs, flux continu** (effectifs de buts 0 / 1 / 2 / 3 / 4+ par équipe) :

| Version | Graine | Domicile : moy σ — effectifs | Extérieur : moy σ — effectifs | Total : moy σ |
|---|---|---|---|---|
| A `HEAD` | 1 | 1,583 1,274 — 210 316 265 137 72 | 1,181 1,110 — 314 357 209 86 34 | 2,764 1,697 |
| B `HEAD`+3b complet | 1 | 1,554 1,298 — 236 308 232 144 80 | 1,227 1,168 — 325 327 199 103 46 | 2,781 1,665 |
| B′ 3b, dispositifs de `HEAD` | 1 | 1,606 1,304 — 222 290 267 140 81 | 1,172 1,105 — 310 376 197 75 42 | 2,778 1,658 |
| A `HEAD` | 2 | 1,552 1,291 — 226 321 242 132 79 | 1,150 1,096 — 327 348 217 74 34 | 2,702 1,646 |
| B `HEAD`+3b complet | 2 | 1,539 1,286 — 231 320 238 134 77 | 1,146 1,098 — 322 363 208 76 31 | 2,685 1,653 |
| B′ 3b, dispositifs de `HEAD` | 2 | 1,509 1,238 — 220 345 237 127 71 | 1,121 1,096 — 350 322 226 72 30 | 2,630 1,634 |

  Bruit de référence à 1 000 matchs (A graine 1 contre A graine 2, `HEAD` contre lui-même) : écart de moyenne totale **+0,062** ; les écarts A↔B et A↔B′ sont du même ordre. Aucun test significatif (Welch, KS, χ² : tous les p ≥ 0,28 pour A↔B).
- **Mode apparié, 1 000 matchs, scores différents par rapport à A** : **B : 37 / 1 000** ; **B′ : 0 / 1 000**.
- **Confirmation à grande échelle (30 612 matchs par bras, 100 fois chaque affiche)** :
  - **B′ en apparié** : **0 / 30 612** scores différents, **0 / 30 612** buteurs ou minutes différents ; les statistiques de match sont présentes dans 30 612 / 30 612 matchs.
  - **B′ en flux continu** : seuls 2 087 / 30 612 scores sont identiques match à match (**`match_stats` consomme bien `np.random` : la séquence est décalée**, comme prévu), mais la distribution est indiscernable : buts/match total A 2,7859 → B′ 2,7758, **Δ −0,0100 ± 0,0267** (IC 95 %) ; χ² sur les effectifs 0 / 1 / 2 / 3 / 4+ : **6,20 (domicile) et 4,25 (extérieur)** pour un seuil de 5 % à 4 ddl de 9,49 ; Δ des points par match par club (18 clubs) : σ 0,029, de −0,058 à +0,036.
  - **B (3b complet) en flux continu** : Δ buts/match total **−0,0131 ± 0,0267** ; P(total ≥ 5) 0,1553 → 0,1534 ; aucun écart significatif.
- **Conclusion.** À dispositifs identiques, **3b ne change aucun match** (0 écart sur 30 612) : la consommation de `np.random` décale seulement la séquence, sans effet sur la distribution. **Le seul effet sur le résultat sportif vient des données du nouveau classeur de coachs : le dispositif préférentiel change pour 6 clubs sur 18 en Ligue 1** — Le Havre (4-2-3-1 → 4-3-3 Attacking), Paris FC (3-4-2-1 → 4-2-3-1), Lens (4-2-3-1 → 3-4-2-1), Angers (4-3-1-2 → 4-2-3-1), Troyes et PSG (4-3-3 → 4-3-3 Attacking). Les notes de secteur utilisées par le Poisson changent pour 4 d'entre eux (ex. Le Havre, milieu 67,17 → 74,00 ; la note globale de composition passe de 69,09 à 70,95). En apparié, **5,67 %** des matchs impliquant l'un de ces 4 clubs ont un score différent, et **0,74 %** (134 / 18 209) des autres matchs (les moyennes de la ligue servant à normaliser les lambdas bougent légèrement) ; l'effet sur les points par match de ces clubs reste de l'ordre du bruit (Le Havre +0,025, Lens +0,028, Paris FC −0,003). **Limite** : seule la Ligue 1 a été mesurée ; les autres championnats et les sélections ne l'ont pas été.
- **Décision au regard du critère fixé** (écart significatif de distribution à 1 000 matchs) : **aucun écart significatif** ; le passage au commit a été autorisé. L'effet « données » est consigné ici pour le propriétaire.

**2. Grep des modulateurs (diff indexé de 3b, lignes ajoutées et retirées)** : motif `COACH_INFLUENCE | STYLE_ATTACK_BONUS | STYLE_DEFENSE_* | STYLE_ATTACK_MALUS | STYLE_PRESSING | STYLE_COUNTER_ATTACK | _coach_modifier | _style_attack_modifier | _style_defense_modifier | _COACH_MODIFIER_BOUNDS | _STYLE_MODIFIER_BOUNDS` → **0 occurrence**. Trois mentions textuelles de `COACH_INFLUENCE` / `STYLE_*` existaient dans des commentaires de `coaches.py` (renvois vers du code du lot 3c) ; elles ont été **reformulées dans la version commitée uniquement** (le fichier de travail garde les commentaires d'origine, qui réapparaîtront dans le diff du lot 3c). Faux positifs du motif large `STYLE_` : `STYLE_COLUMNS` (noms de colonnes du classeur, ×4), `_POSSESSION_STYLE_BONUS` (possession affichée, ×3). Le diff de `simulation.py` ne contient que **2 lignes ajoutées** (`home_lambda=lambda_home,` et `away_lambda=lambda_away,`) et **aucune ligne retirée** ; les `lambda_home *=` du fichier sont ceux, préexistants, du milieu, du banc et de la forme.

**3. Commit 3b — `3070543`** (`feat(coachs): couche de données entraîneurs et statistiques de match — lot 3b`).
- **Périmètre exact (8 fichiers)** : `src/ligue1sim/coaches.py` ; `data/Coachs-Simulafoot.xlsx` (nouveau) ; **suppression** de `data/entraineurs.xlsx` ; `src/ligue1sim/match_stats.py` (nouveau) ; `src/ligue1sim/events.py` (les 7 hunks restants) ; `src/ligue1sim/simulation.py` (le hunk de 2 lignes) ; `tests/test_coaches.py` ; `tests/test_match_stats.py` (nouveau).
- **Vérification** : essai à blanc sur archive jetable `HEAD` + 3b : **1010 passés** ; après commit, `git archive HEAD` propre, `pytest` nu : **1010 passés, 5 ignorés** (tests NLG, venv absent de l'archive).

**4. Archivage des scripts Transfermarkt.** `scripts/scrape_transfermarkt_coaches.py` et `scripts/scrape_transfermarkt_national_coaches.py` sont déplacés dans **`scripts/archive/`** (dossier ignoré par git ; copie locale unique, non versionnée — à sauvegarder si leur historique compte). **Raison** : ils écrivent (et lisent) `data/entraineurs.xlsx`, supprimé par 3b et désormais remplacé par `data/Coachs-Simulafoot.xlsx` ; plus aucune référence dans les fichiers suivis de `HEAD` (`git grep` : 0 résultat hors ce document). Le second importe le premier : les deux ont été archivés **ensemble**, donc l'import reste valide dans le dossier d'archive. Ce déplacement concerne des fichiers jamais suivis : il ne figure dans aucun commit hors cette documentation. Il remplace la ligne « laissé en place » du §7.

**5. Superposition 3a + Lot 1 + Lot 2 + 3b** (`git archive HEAD` propre, `pytest` nu) : **1010 passés, 5 ignorés, 12 désélectionnés**. Avec le venv NLG local rendu accessible à l'archive (jonction retirée ensuite) : **1015 passés, 0 ignoré, 12 désélectionnés**.

**6. D2 reste en attente du propriétaire — mesure comparative obligatoire avant tout commit de 3c.** Précision de méthode pour cette mesure : le **bras A (sans modulateurs) est le `HEAD` actuel, qui inclut 3b et donc les dispositifs du nouveau classeur de coachs** ; il ne faut pas comparer à l'ancien `HEAD` d'avant 3b, sous peine de mêler l'effet des modulateurs à celui des données de coachs mesuré ci-dessus. Le protocole du §8.4 (partie 3c) est inchangé par ailleurs. Aucun commit de 3c, du Lot 4 ni du Lot 5.

### 8.11 Avancement du 07/10/2026 (suite) — décision D3 et mesure D2 (3c non commité)

**Séquence mise à jour : 3a (fait) → Lot 1 (fait) → Lot 2 (fait) → 3b (fait) → mesure D2 (faite) → décision du propriétaire sur 3c (en attente) → 3c → Lot 4 → Lot 5.** Ce paragraphe présente des chiffres ; **il ne conclut pas sur l'opportunité de commiter 3c**, décision qui revient au propriétaire.

**1. Décision D3 — dispositifs clubs conservés.** Le propriétaire a tranché : les dispositifs préférentiels du nouveau classeur de coachs (6 clubs de Ligue 1, §8.10) sont **conservés tels quels**, sans neutralisation ; l'effet est une caractéristique produit assumée. Entrée documentaire : `docs/known_issues.md`, « Décision propriétaire — dispositifs clubs conservés (D3) » (statut : résolu). **Écart consigné** : la consigne citait « +0,062 but par match (+2,3 %) » et « 7 % des matchs des clubs concernés » ; mes mesures donnent **+0,062 = bruit** (écart entre deux graines du `HEAD` seul) et **4,25 %** des matchs des 6 clubs (le hash de 3b est `3070543`, non `38705437`). Les chiffres mesurés sont ceux de l'entrée D3.

**2. Protocole de la mesure D2** (exécutée sur **archives jetables** `git archive`, jamais sur l'arbre de travail) :
- **Bras A** = `HEAD` actuel (`be168d3`) : 3a, Lots 1 et 2 et 3b inclus (dispositifs du nouveau classeur de coachs appliqués), **aucun modulateur**.
- **Bras B** = A + le `simulation.py` de l'arbre de travail, soit **3c seul** : 4 hunks (import `coaches`, constantes `COACH_INFLUENCE` = 0,3 avec bornes 0,99–1,01 et `STYLE_*` avec bornes cumulées 0,95–1,05, application des modulateurs aux lambdas dans `_draw_score`, fonctions `_coach_modifier` / `_style_attack_modifier` / `_style_defense_modifier`). Le bras B ne diffère de A que par ce fichier (vérifié par `diff -rq`). 3c n'est **pas** commité.
- **Simulation** : Ligue 1 réelle (18 clubs, 306 affiches ordonnées jouées en boucle, `simulate_match` complet), **mêmes graines et même ordre dans A et B**. Deux modes : **apparié** (graines `random` et `numpy` refixées avant chaque match ; 1 000 matchs, puis 30 612 en supplément) et **flux continu** (une graine, matchs à la suite ; 1 000 matchs graine 1, puis 30 612 matchs graine 7 en supplément).
- **Mesures** : moyenne, écart-type et effectifs de matchs à 0, 1, 2, 3, 4, 5+ buts, pour le domicile, l'extérieur et le total.
- **Tests** : **Welch** sur la moyenne (p-valeur par approximation normale, IC 95 % de la différence) ; **Kolmogorov-Smirnov** bi-échantillon sur la distribution (p-valeur asymptotique, conservatrice sur données discrètes) ; **écart apparié** match à match (test t apparié, IC 95 %), seulement pertinent en mode apparié. Seuil : p < 0,05.
- **Hasard** : le code de 3c n'appelle aucune fonction aléatoire (0 occurrence de `random` dans les lignes ajoutées), mais il modifie les lambdas, donc le **nombre de tirages consommés** par `poisson` et par la génération des événements ; en flux continu, les deux bras **ne partagent donc pas** la même séquence aléatoire au-delà du premier match différent (voir le pourcentage de scores identiques ci-dessous). C'est pourquoi le mode apparié est le plus informatif pour l'effet de 3c.
- **Limites** : seule la Ligue 1 est mesurée (pas les autres championnats ni les sélections) ; un seul jeu d'affiches (306, jouées en boucle).

**3. Résultats bruts** (sortie du script, inchangée).

```
======================================================================================================================
MODE APPARIÉ — graine (random + numpy) refixée avant CHAQUE match (mêmes graines, même ordre) — 1000 matchs par bras
======================================================================================================================
          bras   moyenne       σ        0       1       2       3       4      5+   (effectifs de matchs avec k buts)
Domicile  A       1.5780  1.2937      205     341     253     115      54      32
Domicile  B       1.6080  1.3115      196     348     248     114      58      36
Extérieur A       1.1670  1.1271      324     358     194      90      23      11
Extérieur B       1.1850  1.1428      325     346     198      98      20      13
Total     A       2.7450  1.6908       65     187     239     211     146     152
Total     B       2.7930  1.7038       61     187     231     207     153     161

            Δ moyenne (B−A)         IC 95 % Welch   p Welch    KS D     p KS   Δ apparié       IC 95 % apparié  p apparié
Domicile            +0.0300  [ -0.0842 ;  +0.1442]     0.607   0.009    1.000     +0.0300  [ +0.0160 ;  +0.0440]     0.0000
Extérieur           +0.0180  [ -0.0815 ;  +0.1175]     0.723   0.011    1.000     +0.0180  [ -0.0014 ;  +0.0374]     0.0687
Total               +0.0480  [ -0.1008 ;  +0.1968]     0.527   0.016    0.999     +0.0480  [ +0.0243 ;  +0.0717]     0.0001

scores identiques match à match : 919/1000 = 91.90 %  (différents : 81 = 8.10 %) ; buteurs/minutes identiques : 919/1000
répartition des écarts de buts totaux B−A par match : -4: 1, -2: 1, -1: 10, +0: 943, +1: 32, +2: 9, +3: 2, +4: 2

======================================================================================================================
MODE FLUX CONTINU — une graine (1), 1 000 matchs à la suite (séquence aléatoire partagée : elle diverge dès qu'un match consomme un nombre différent de tirages) — 1000 matchs par bras
======================================================================================================================
          bras   moyenne       σ        0       1       2       3       4      5+   (effectifs de matchs avec k buts)
Domicile  A       1.5540  1.2980      236     308     232     144      58      22
Domicile  B       1.5820  1.3301      234     304     238     129      69      26
Extérieur A       1.2270  1.1683      325     327     199     103      38       8
Extérieur B       1.2570  1.1594      291     367     194     108      25      15
Total     A       2.7810  1.6649       73     170     220     213     175     149
Total     B       2.8390  1.7269       67     178     212     210     169     164

            Δ moyenne (B−A)         IC 95 % Welch   p Welch    KS D     p KS   Δ apparié       IC 95 % apparié  p apparié
Domicile            +0.0280  [ -0.0872 ;  +0.1432]     0.634   0.015    1.000     +0.0280  [ -0.0810 ;  +0.1370]     0.6147
Extérieur           +0.0300  [ -0.0720 ;  +0.1320]     0.564   0.034    0.603     +0.0300  [ -0.0639 ;  +0.1239]     0.5314
Total               +0.0580  [ -0.0907 ;  +0.2067]     0.444   0.015    1.000     +0.0580  [ -0.0840 ;  +0.2000]     0.4233

scores identiques match à match : 98/1000 = 9.80 %  (différents : 902 = 90.20 %) ; buteurs/minutes identiques : 28/1000
répartition des écarts de buts totaux B−A par match : -6: 7, -5: 20, -4: 33, -3: 63, -2: 108, -1: 172, +0: 180, +1: 177, +2: 110, +3: 59, +4: 38, +5: 20, +6: 10, +7: 1, +8: 2

======================================================================================================================
SUPPLÉMENT (puissance) — MODE APPARIÉ — 30612 matchs par bras
======================================================================================================================
          bras   moyenne       σ        0       1       2       3       4      5+   (effectifs de matchs avec k buts)
Domicile  A       1.5902  1.2969     6615    9676    7680    4021    1768     852
Domicile  B       1.6125  1.3100     6517    9582    7682    4077    1852     902
Extérieur A       1.1812  1.1130     9663   10917    6293    2647     811     281
Extérieur B       1.1986  1.1273     9549   10871    6322    2688     870     312
Total     A       2.7713  1.6692     1956    5380    7244    6758    4610    4664
Total     B       2.8112  1.6873     1886    5291    7143    6742    4683    4867

            Δ moyenne (B−A)         IC 95 % Welch   p Welch    KS D     p KS   Δ apparié       IC 95 % apparié  p apparié
Domicile            +0.0224  [ +0.0017 ;  +0.0430]     0.034   0.006    0.582     +0.0224  [ +0.0201 ;  +0.0246]     0.0000
Extérieur           +0.0175  [ -0.0003 ;  +0.0352]     0.054   0.005    0.796     +0.0175  [ +0.0142 ;  +0.0207]     0.0000
Total               +0.0399  [ +0.0133 ;  +0.0664]     0.003   0.009    0.165     +0.0399  [ +0.0359 ;  +0.0438]     0.0000

scores identiques match à match : 28550/30612 = 93.26 %  (différents : 2062 = 6.74 %) ; buteurs/minutes identiques : 28543/30612
répartition des écarts de buts totaux B−A par match : -5: 2, -4: 5, -3: 18, -2: 40, -1: 291, +0: 29030, +1: 950, +2: 167, +3: 62, +4: 33, +5: 11, +6: 3

======================================================================================================================
SUPPLÉMENT (puissance) — MODE FLUX CONTINU, graine 7 — 30612 matchs par bras
======================================================================================================================
          bras   moyenne       σ        0       1       2       3       4      5+   (effectifs de matchs avec k buts)
Domicile  A       1.5957  1.3015     6564    9778    7511    4110    1779     870
Domicile  B       1.6055  1.3155     6587    9682    7498    4151    1741     953
Extérieur A       1.1771  1.1205     9798   10800    6331    2543     836     304
Extérieur B       1.1977  1.1233     9596   10717    6464    2684     846     305
Total     A       2.7728  1.6777     1972    5338    7384    6628    4593    4697
Total     B       2.8032  1.6852     1881    5321    7211    6732    4663    4804

            Δ moyenne (B−A)         IC 95 % Welch   p Welch    KS D     p KS   Δ apparié       IC 95 % apparié  p apparié
Domicile            +0.0098  [ -0.0109 ;  +0.0305]     0.354   0.003    1.000     +0.0098  [ -0.0100 ;  +0.0296]     0.3331
Extérieur           +0.0206  [ +0.0029 ;  +0.0384]     0.023   0.009    0.140     +0.0206  [ +0.0035 ;  +0.0378]     0.0185
Total               +0.0304  [ +0.0038 ;  +0.0571]     0.025   0.009    0.151     +0.0304  [ +0.0043 ;  +0.0566]     0.0227

scores identiques match à match : 2102/30612 = 6.87 %  (différents : 28510 = 93.13 %) ; buteurs/minutes identiques : 204/30612
répartition des écarts de buts totaux B−A par match : -9: 5, -8: 14, -7: 70, -6: 224, -5: 535, -4: 1153, -3: 2117, -2: 3564, -1: 4705, +0: 5376, +1: 4887, +2: 3635, +3: 2296, +4: 1199, +5: 539, +6: 214, +7: 61, +8: 16, +9: 1, +10: 1
```

**4. Arbre de travail** : restauré à l'identique après la mesure (la mesure n'a rien modifié) : `git status` (55 entrées), hash du diff `HEAD` hors docs (`a22f5cb5b83b51ff`) et hash de `simulation.py` (`4b44301c…`, avec 3c) identiques avant et après ; `PROJET_SIMULAFOOT.md` inchangé et non commité.

**5. Statut** : mesure D2 **faite**. **Décision du propriétaire sur 3c : en attente.** Aucun commit de 3c, du Lot 4 ni du Lot 5 ; aucun modulateur dans `HEAD`.

### 8.12 Avancement du 07/10/2026 (suite) — décision D4 (option C) et balayage d'amplitudes de 3c

**Séquence mise à jour : 3a (fait) → Lot 1 (fait) → Lot 2 (fait) → 3b (fait) → mesure D2 (faite) → décision D4 (option C) → balayage d'amplitudes (fait) → décision du propriétaire sur l'amplitude de 3c (en attente) → 3c (commit à l'amplitude retenue, ou abandon) → Lot 4 → Lot 5.** Ce paragraphe présente des chiffres ; **il ne conclut pas sur l'amplitude à adopter**, décision qui revient au propriétaire. 3c n'est **pas** commité.

**1. Décision D4 — option C retenue.** Le propriétaire a décidé de **conserver les modulateurs de 3c** et de **tester des amplitudes renforcées** pour obtenir un effet statistiquement mesurable sur la distribution des scores ; si aucune amplitude testée ne produit d'effet significatif, retour au propriétaire avec une recommandation d'abandon. Fait de contexte : les commentaires de `simulation.py` (section « Coach », 29/09/2026) consignent une demande explicite de garder cette influence « très légère » ; D4 lui est postérieure.

**2. Correction de hash demandée — non appliquée, vérifiée.** La demande citait le hash de 3b comme `30785437` et celui de la mesure D2 comme `acb1f71a` (après un `38705437` du rapport précédent). **Aucun de ces trois hash n'existe** (`git rev-parse --verify` : aucun commit). Les hash réels sont : **3b = `3070543`** (`307054370d97abe9c2b1d7fb3b425262cbcbfb35`) et **commit documentaire de la mesure D2 = `ac4b1f7`**. Le §8.11 et `docs/known_issues.md` contiennent **déjà** `3070543` ; les « corriger » vers un hash inexistant aurait introduit une erreur. **Aucune modification de contenu n'a été faite au §8.11 ni dans `known_issues.md`.**

**3. Protocole.** Archives jetables `git archive` du `HEAD` actuel (`ac4b1f7`, 3b inclus, dispositifs clubs conservés — D3), **jamais l'arbre de travail**.
- **Bras A** : `HEAD`, **aucun modulateur** (baseline).
- **Bras B0** (ajouté comme référence, non demandé) : A + `simulation.py` de l'arbre de travail, soit 3c à l'amplitude actuelle (**×1** : coach ±1 %, styles ±5 %).
- **Bras B1 (×3)** : coach ±3 %, styles ±15 %. **Bras B2 (×6)** : coach ±6 %, styles ±30 %.
- **Amplification** : le facteur multiplie uniformément `COACH_INFLUENCE` **et** les `STYLE_*`, **ainsi que l'écart des deux bornes à 1** (`_COACH_MODIFIER_BOUNDS`, `_STYLE_MODIFIER_BOUNDS`) : sans cela, la borne de ±1 % annulerait l'effet de `COACH_INFLUENCE` ×3. Les formules d'application aux lambdas sont **inchangées**. Valeurs vérifiées par import dans chaque archive :

| Bras | `COACH_INFLUENCE` | bornes coach | `STYLE_*` (attaque+ / défense− / défense+ / attaque− / pressing / contre-attaque) | bornes styles |
|---|---|---|---|---|
| A | (absent) | — | — | — |
| B0 ×1 | 0,3 | 0,99–1,01 | 0,02 / 0,015 / 0,02 / 0,015 / 0,01 / 0,03 | 0,95–1,05 |
| B1 ×3 | 0,9 | 0,97–1,03 | 0,06 / 0,045 / 0,06 / 0,045 / 0,03 / 0,09 | 0,85–1,15 |
| B2 ×6 | 1,8 | 0,94–1,06 | 0,12 / 0,09 / 0,12 / 0,09 / 0,06 / 0,18 | 0,70–1,30 |

- **Simulation** : Ligue 1 réelle (18 clubs, 306 affiches ordonnées jouées en boucle), `simulate_match` complet, **mêmes graines et même ordre dans tous les bras**. **Mode apparié privilégié** : graines `random` et `numpy` refixées avant chaque match (1 000 matchs) ; **mode flux continu** donné pour information (graine 1, 1 000 matchs) ; **supplément de puissance** à 30 612 matchs par bras (apparié, graine 3 ; flux continu, graine 7).
- **Mesures** : moyenne, écart-type, effectifs de matchs à 0, 1, 2, 3, 4, 5+ buts (domicile, extérieur, total). **Tests** : Welch sur la moyenne (p-valeur par approximation normale, IC 95 %) ; Kolmogorov-Smirnov sur la distribution (p-valeur asymptotique, conservatrice sur données discrètes) ; en plus, test t **apparié** match à match (IC 95 %) ; seuil p < 0,05 ; pourcentage de scores identiques.
- **Limites** : Ligue 1 seulement ; un seul jeu de 306 affiches.

**4. Résultats bruts** (sortie du script, inchangée).

```
============================================================================================================================
MODE APPARIÉ (graine random+numpy refixée avant chaque match ; mêmes graines, même ordre) — 1000 matchs par bras
============================================================================================================================
          bras   moyenne       σ        0       1       2       3       4      5+   (effectifs de matchs avec k buts)
Domicile  A       1.5780  1.2937      205     341     253     115      54      32
Domicile  B0      1.6080  1.3115      196     348     248     114      58      36
Domicile  B1      1.6600  1.3668      196     335     247     115      64      43
Domicile  B2      1.7410  1.4401      191     323     243     117      72      54
Extérieur A       1.1670  1.1271      324     358     194      90      23      11
Extérieur B0      1.1850  1.1428      325     346     198      98      20      13
Extérieur B1      1.2250  1.1789      320     338     198     105      24      15
Extérieur B2      1.2800  1.2301      314     329     194     113      32      18
Total     A       2.7450  1.6908       65     187     239     211     146     152
Total     B0      2.7930  1.7038       61     187     231     207     153     161
Total     B1      2.8850  1.7734       61     181     219     203     157     179
Total     B2      3.0210  1.8607       60     171     204     209     137     219

          A vs    Δ moyenne         IC 95 % Welch   p Welch    KS D     p KS   Δ apparié       IC 95 % apparié  p apparié
Domicile  B0        +0.0300  [ -0.0842 ;  +0.1442]     0.607   0.009    1.000     +0.0300  [ +0.0160 ;  +0.0440]     0.0000
Domicile  B1        +0.0820  [ -0.0346 ;  +0.1986]     0.168   0.021    0.979     +0.0820  [ +0.0574 ;  +0.1066]     0.0000
Domicile  B2        +0.1630  [ +0.0430 ;  +0.2830]     0.008   0.042    0.334     +0.1630  [ +0.1279 ;  +0.1981]     0.0000
Extérieur B0        +0.0180  [ -0.0815 ;  +0.1175]     0.723   0.011    1.000     +0.0180  [ -0.0014 ;  +0.0374]     0.0687
Extérieur B1        +0.0580  [ -0.0431 ;  +0.1591]     0.261   0.024    0.933     +0.0580  [ +0.0240 ;  +0.0920]     0.0008
Extérieur B2        +0.1130  [ +0.0096 ;  +0.2164]     0.032   0.039    0.425     +0.1130  [ +0.0651 ;  +0.1609]     0.0000
Total     B0        +0.0480  [ -0.1008 ;  +0.1968]     0.527   0.016    0.999     +0.0480  [ +0.0243 ;  +0.0717]     0.0001
Total     B1        +0.1400  [ -0.0119 ;  +0.2919]     0.071   0.038    0.459     +0.1400  [ +0.0987 ;  +0.1813]     0.0000
Total     B2        +0.2760  [ +0.1202 ;  +0.4318]     0.001   0.067    0.021     +0.2760  [ +0.2169 ;  +0.3351]     0.0000

scores identiques A vs B0 : 919/1000 =  91.90 %  (différents   8.10 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 15 matchs
scores identiques A vs B1 : 801/1000 =  80.10 %  (différents  19.90 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 51 matchs
scores identiques A vs B2 : 661/1000 =  66.10 %  (différents  33.90 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 113 matchs

============================================================================================================================
MODE FLUX CONTINU (graine 1, matchs à la suite ; INFORMATIF) — 1000 matchs par bras
============================================================================================================================
          bras   moyenne       σ        0       1       2       3       4      5+   (effectifs de matchs avec k buts)
Domicile  A       1.5540  1.2980      236     308     232     144      58      22
Domicile  B0      1.5820  1.3301      234     304     238     129      69      26
Domicile  B1      1.6100  1.3385      223     305     251     123      66      32
Domicile  B2      1.6870  1.4419      234     279     233     141      62      51
Extérieur A       1.2270  1.1683      325     327     199     103      38       8
Extérieur B0      1.2570  1.1594      291     367     194     108      25      15
Extérieur B1      1.1970  1.1556      321     355     188      92      31      13
Extérieur B2      1.2870  1.2050      306     323     219     103      32      17
Total     A       2.7810  1.6649       73     170     220     213     175     149
Total     B0      2.8390  1.7269       67     178     212     210     169     164
Total     B1      2.8070  1.7392       69     177     230     208     149     167
Total     B2      2.9740  1.8212       69     161     196     225     151     198

          A vs    Δ moyenne         IC 95 % Welch   p Welch    KS D     p KS   Δ apparié       IC 95 % apparié  p apparié
Domicile  B0        +0.0280  [ -0.0872 ;  +0.1432]     0.634   0.015    1.000     +0.0280  [ -0.0810 ;  +0.1370]     0.6147
Domicile  B1        +0.0560  [ -0.0596 ;  +0.1716]     0.342   0.018    0.997     +0.0560  [ -0.0505 ;  +0.1625]     0.3025
Domicile  B2        +0.1330  [ +0.0128 ;  +0.2532]     0.030   0.033    0.641     +0.1330  [ +0.0198 ;  +0.2462]     0.0213
Extérieur B0        +0.0300  [ -0.0720 ;  +0.1320]     0.564   0.034    0.603     +0.0300  [ -0.0639 ;  +0.1239]     0.5314
Extérieur B1        -0.0300  [ -0.1319 ;  +0.0719]     0.564   0.024    0.933     -0.0300  [ -0.1241 ;  +0.0641]     0.5319
Extérieur B2        +0.0600  [ -0.0440 ;  +0.1640]     0.258   0.023    0.952     +0.0600  [ -0.0395 ;  +0.1595]     0.2370
Total     B0        +0.0580  [ -0.0907 ;  +0.2067]     0.444   0.015    1.000     +0.0580  [ -0.0840 ;  +0.2000]     0.4233
Total     B1        +0.0260  [ -0.1232 ;  +0.1752]     0.733   0.018    0.997     +0.0260  [ -0.1136 ;  +0.1656]     0.7151
Total     B2        +0.1930  [ +0.0401 ;  +0.3459]     0.013   0.049    0.176     +0.1930  [ +0.0417 ;  +0.3443]     0.0124

scores identiques A vs B0 : 98/1000 =   9.80 %  (différents  90.20 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 471 matchs
scores identiques A vs B1 : 95/1000 =   9.50 %  (différents  90.50 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 508 matchs
scores identiques A vs B2 : 51/1000 =   5.10 %  (différents  94.90 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 530 matchs

============================================================================================================================
SUPPLÉMENT (puissance) — MODE APPARIÉ — 30612 matchs par bras
============================================================================================================================
          bras   moyenne       σ        0       1       2       3       4      5+   (effectifs de matchs avec k buts)
Domicile  A       1.5902  1.2969     6615    9676    7680    4021    1768     852
Domicile  B0      1.6125  1.3100     6517    9582    7682    4077    1852     902
Domicile  B1      1.6574  1.3397     6339    9418    7644    4175    1997    1039
Domicile  B2      1.7209  1.3902     6185    9142    7508    4311    2178    1288
Extérieur A       1.1812  1.1130     9663   10917    6293    2647     811     281
Extérieur B0      1.1986  1.1273     9549   10871    6322    2688     870     312
Extérieur B1      1.2358  1.1553     9310   10749    6392    2821     965     375
Extérieur B2      1.2895  1.2085     9106   10502    6376    2951    1159     518
Total     A       2.7713  1.6692     1956    5380    7244    6758    4610    4664
Total     B0      2.8112  1.6873     1886    5291    7143    6742    4683    4867
Total     B1      2.8931  1.7256     1780    5062    6950    6729    4773    5318
Total     B2      3.0104  1.7900     1706    4761    6654    6530    4959    6002

          A vs    Δ moyenne         IC 95 % Welch   p Welch    KS D     p KS   Δ apparié       IC 95 % apparié  p apparié
Domicile  B0        +0.0224  [ +0.0017 ;  +0.0430]     0.034   0.006    0.582     +0.0224  [ +0.0201 ;  +0.0246]     0.0000
Domicile  B1        +0.0672  [ +0.0463 ;  +0.0881]     0.000   0.019    0.000     +0.0672  [ +0.0630 ;  +0.0714]     0.0000
Domicile  B2        +0.1307  [ +0.1094 ;  +0.1520]     0.000   0.037    0.000     +0.1307  [ +0.1246 ;  +0.1368]     0.0000
Extérieur B0        +0.0175  [ -0.0003 ;  +0.0352]     0.054   0.005    0.796     +0.0175  [ +0.0142 ;  +0.0207]     0.0000
Extérieur B1        +0.0546  [ +0.0366 ;  +0.0726]     0.000   0.017    0.000     +0.0546  [ +0.0488 ;  +0.0604]     0.0000
Extérieur B2        +0.1083  [ +0.0899 ;  +0.1267]     0.000   0.032    0.000     +0.1083  [ +0.1002 ;  +0.1165]     0.0000
Total     B0        +0.0399  [ +0.0133 ;  +0.0664]     0.003   0.009    0.165     +0.0399  [ +0.0359 ;  +0.0438]     0.0000
Total     B1        +0.1218  [ +0.0949 ;  +0.1487]     0.000   0.027    0.000     +0.1218  [ +0.1147 ;  +0.1289]     0.0000
Total     B2        +0.2390  [ +0.2116 ;  +0.2664]     0.000   0.055    0.000     +0.2390  [ +0.2291 ;  +0.2489]     0.0000

scores identiques A vs B0 : 28550/30612 =  93.26 %  (différents   6.74 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 341 matchs
scores identiques A vs B1 : 24900/30612 =  81.34 %  (différents  18.66 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 1307 matchs
scores identiques A vs B2 : 20602/30612 =  67.30 %  (différents  32.70 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 2847 matchs

============================================================================================================================
SUPPLÉMENT (puissance) — MODE FLUX CONTINU, graine 7 (INFORMATIF) — 30612 matchs par bras
============================================================================================================================
          bras   moyenne       σ        0       1       2       3       4      5+   (effectifs de matchs avec k buts)
Domicile  A       1.5957  1.3015     6564    9778    7511    4110    1779     870
Domicile  B0      1.6055  1.3155     6587    9682    7498    4151    1741     953
Domicile  B1      1.6632  1.3510     6403    9367    7461    4326    1972    1083
Domicile  B2      1.7151  1.3967     6241    9242    7327    4415    2051    1336
Extérieur A       1.1771  1.1205     9798   10800    6331    2543     836     304
Extérieur B0      1.1977  1.1233     9596   10717    6464    2684     846     305
Extérieur B1      1.2336  1.1545     9303   10778    6471    2675     995     390
Extérieur B2      1.2868  1.2120     9208   10362    6447    2938    1124     533
Total     A       2.7728  1.6777     1972    5338    7384    6628    4593    4697
Total     B0      2.8032  1.6852     1881    5321    7211    6732    4663    4804
Total     B1      2.8968  1.7316     1812    5008    6982    6658    4808    5344
Total     B2      3.0019  1.8028     1754    4784    6701    6536    4845    5992

          A vs    Δ moyenne         IC 95 % Welch   p Welch    KS D     p KS   Δ apparié       IC 95 % apparié  p apparié
Domicile  B0        +0.0098  [ -0.0109 ;  +0.0305]     0.354   0.003    1.000     +0.0098  [ -0.0100 ;  +0.0296]     0.3331
Domicile  B1        +0.0675  [ +0.0464 ;  +0.0885]     0.000   0.020    0.000     +0.0675  [ +0.0474 ;  +0.0875]     0.0000
Domicile  B2        +0.1194  [ +0.0980 ;  +0.1408]     0.000   0.034    0.000     +0.1194  [ +0.0992 ;  +0.1397]     0.0000
Extérieur B0        +0.0206  [ +0.0029 ;  +0.0384]     0.023   0.009    0.140     +0.0206  [ +0.0035 ;  +0.0378]     0.0185
Extérieur B1        +0.0565  [ +0.0385 ;  +0.0746]     0.000   0.017    0.000     +0.0565  [ +0.0392 ;  +0.0738]     0.0000
Extérieur B2        +0.1097  [ +0.0912 ;  +0.1282]     0.000   0.034    0.000     +0.1097  [ +0.0919 ;  +0.1275]     0.0000
Total     B0        +0.0304  [ +0.0038 ;  +0.0571]     0.025   0.009    0.151     +0.0304  [ +0.0043 ;  +0.0566]     0.0227
Total     B1        +0.1240  [ +0.0970 ;  +0.1510]     0.000   0.029    0.000     +0.1240  [ +0.0976 ;  +0.1504]     0.0000
Total     B2        +0.2291  [ +0.2015 ;  +0.2567]     0.000   0.051    0.000     +0.2291  [ +0.2022 ;  +0.2560]     0.0000

scores identiques A vs B0 : 2102/30612 =   6.87 %  (différents  93.13 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 15644 matchs
scores identiques A vs B1 : 2099/30612 =   6.86 %  (différents  93.14 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 15721 matchs
scores identiques A vs B2 : 2012/30612 =   6.57 %  (différents  93.43 %) | écart de buts totaux : médiane +0, |écart| ≥ 2 : 15864 matchs
```

**5. Synthèse factuelle des p-valeurs** (tirée des tableaux ci-dessus ; « oui » = p < 0,05), pour le **total de buts** :

| Amplitude | 1 000 matchs apparié : Welch / KS | 1 000 matchs apparié : t apparié | 30 612 matchs apparié : Welch / KS | Δ moyenne totale (1 000 / 30 612) | Scores identiques à A (1 000 / 30 612) |
|---|---|---|---|---|---|
| ×1 | non (0,527) / non (0,999) | oui (0,0001) | oui (0,003) / non (0,165) | +0,048 / +0,040 | 91,90 % / 93,26 % |
| ×3 | non (0,071) / non (0,459) | oui (< 0,0001) | oui (< 0,001) / oui (< 0,001) | +0,140 / +0,122 | 80,10 % / 81,34 % |
| ×6 | oui (0,001) / oui (0,021) | oui (< 0,0001) | oui (< 0,001) / oui (< 0,001) | +0,276 / +0,239 | 66,10 % / 67,30 % |

Faits constatés (sans recommandation) : au critère demandé (Welch et KS sur 1 000 matchs), seule l'amplitude ×6 est significative sur le total ; à 30 612 matchs, ×3 et ×6 le sont aux deux tests, ×1 seulement au test de Welch. La **moyenne de buts augmente avec l'amplitude** (+1,7 %, +5,1 %, +10,1 % de la moyenne du bras A à 1 000 matchs ; +1,4 %, +4,4 %, +8,6 % à 30 612) : les modulateurs ne sont pas neutres sur la moyenne de buts de la ligue. En flux continu (informatif), seul ×6 est significatif sur le total à 1 000 matchs (Welch p = 0,013).

**6. Arbre de travail** : restauré à l'identique (rien n'a été modifié) : `git status` (55 entrées), hash du diff `HEAD` hors docs (`a22f5cb5b83b51ff`) et hash de `simulation.py` (`4b44301c…`) identiques avant et après ; les constantes de 3c y restent à **±1 % / ±5 %** (`COACH_INFLUENCE = 0.3`, bornes 0,99–1,01 et 0,95–1,05). `PROJET_SIMULAFOOT.md` inchangé et non commité.

**7. Statut** : balayage **fait**. **Décision du propriétaire sur l'amplitude de 3c (ou abandon) : en attente.** Aucun commit de 3c, du Lot 4 ni du Lot 5 ; aucun modulateur dans `HEAD`.

### 8.13 Avancement du 07/10/2026 (suite) — décision D5 (option B), 3c commité à ×3

**Décision D5 (propriétaire) : option B retenue, les modulateurs de 3c sont commités à l'amplitude ×3** (coach ±3 %, styles ±15 %), en connaissance du balayage d'amplitudes du §8.12.

**Valeurs finales des constantes** (`src/ligue1sim/simulation.py`) :

| Constante | Valeur finale | Valeur ×1 (§8.12) |
|---|---|---|
| `COACH_INFLUENCE` | 0,9 | 0,3 |
| `_COACH_MODIFIER_BOUNDS` | (0,97 ; 1,03) | (0,99 ; 1,01) |
| `STYLE_ATTACK_BONUS` (Offensif) | 0,06 | 0,02 |
| `STYLE_DEFENSE_MALUS` (contrepartie d'Offensif) | 0,045 | 0,015 |
| `STYLE_DEFENSE_BONUS` (Défensif) | 0,06 | 0,02 |
| `STYLE_ATTACK_MALUS` (contrepartie de Défensif) | 0,045 | 0,015 |
| `STYLE_PRESSING_BONUS` | 0,03 | 0,01 |
| `STYLE_COUNTER_ATTACK_BONUS` | 0,09 | 0,03 |
| `_STYLE_MODIFIER_BOUNDS` | (0,85 ; 1,15) | (0,95 ; 1,05) |

Les formules d'application aux lambdas de Poisson sont inchangées ; seules les constantes diffèrent de ×1.

**Commit 3c : `8ee3e7d`** (`feat(simulation): 3c -- modulateurs coach et styles de jeu (amplitudes x3, D5)`). Périmètre : `src/ligue1sim/simulation.py` (+112 lignes : constantes, `_coach_modifier`, `_style_attack_modifier`, `_style_defense_modifier`, application dans `_draw_score`) et `tests/test_simulation.py` (+80 lignes : `TestCoachModifier`, `TestStyleModifiers`, test de bornes adapté à 0,97–1,03). Aucun autre fichier. Les modifications de docstrings de `src/ligue1sim/coaches.py` (qui décrivent encore la note comme « pas encore utilisée par le moteur ») **ne sont pas** dans ce commit : elles restent dans l'arbre de travail, à traiter avec la suite.

**Précision sur la note du 29/09/2026** : le commentaire de `simulation.py` demandait de garder l'influence **coach** sous 3 %. ×3 place l'influence coach **à la borne** (±3 %) ; décision assumée. Les **styles** passent à ±15 % cumulés, ce qui sort du périmètre de la note initiale (qui ne portait que sur le coach). Un commentaire de 3 lignes dans `simulation.py` documente D5.

**Vérifications sur `git archive HEAD` propre (`8ee3e7d`)** :
- `pytest` nu avec le venv principal : s'interrompt à la collecte (`simulafoot_nlg/tests/conftest.py` importe `duckdb`, absent de ce venv). Sans rapport avec le code de 3c (dépendance du conftest NLG ; non testé sans 3c).
- `pytest --ignore=simulafoot_nlg` (venv principal) : **1018 passed, 5 skipped, 12 deselected** (tests d'intégration exclus par défaut).
- `simulafoot_nlg/tests` dans le venv NLG (`simulafoot_nlg/.venv`) : **874 passed, 23 skipped** (le seuil de couverture 85 % sur `engine/` échoue depuis ce venv, sans lien avec les tests).
- **Superposition complète : 1 892 passed, 28 skipped.**

**Faisabilité du Lot 4 seul (essai à blanc, non commité)** : HEAD + les 4 fichiers `api/` suivis modifiés (`main.py`, `routers/competitions.py`, `schemas.py`, `serializers.py`) : **non commitable seul**. La collecte échoue (`ModuleNotFoundError: No module named 'api.live_commentary'`, importé par `api/serializers.py`). Dépendances non suivies manquantes : `api/live_commentary.py`, `api/nlg_live.py`. Avec ces deux fichiers ajoutés, la suite passe (1018 passed, 5 skipped). Les tests `tests/test_competitions.py`, `test_serializers.py`, `test_live_commentary.py`, `test_nlg_live.py` sont également non suivis. `engine.db` et `engine.selectivity`, importés dans un script exécuté dans le venv NLG (`api/nlg_live.py`), ne sont pas des dépendances de la suite racine.

**Séquence mise à jour** : 3a (fait, `f5e37de`) → Lot 1 (fait, `7fa9f68`) → Lot 2 (fait, `ddfad09`) → 3b (fait, `3070543`) → 3c (fait, `8ee3e7d`) → Lot 4 (à faire) → Lot 5 (à faire) → mise à jour de `PROJET_SIMULAFOOT.md` (à faire) → entrée Phase 5 (à faire).

**Statut** : aucun commit du Lot 4, du Lot 5 ni de `PROJET_SIMULAFOOT.md`. Moteur de rendu, mode standalone de `canvas.html` et tickets 1, 2, 3, 4, 6, 7 de `known_issues.md` inchangés.
