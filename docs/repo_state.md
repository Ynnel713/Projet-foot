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
| `scripts/scrape_transfermarkt_coaches.py` | **Laissé en place** | **Non prouvé orphelin** : `scripts/scrape_transfermarkt_national_coaches.py` l'importe (`from scrape_transfermarkt_coaches import …`, ligne 44). Les deux écrivent `data/entraineurs.xlsx`, supprimé dans l'arbre de travail (suppression non commitée) mais encore lu par le `coaches.py` de `HEAD`. Décision reportée au Lot 3 de la séquence de résorption Catégorie B |

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

- **D1 — `data/joueurs.xlsx`** (Lot 2). Faits mesurés (lecture seule, comparaison `HEAD` / arbre de travail) : **82 « Moyenne joueur » modifiées** (60 hausses, 22 baisses ; médiane des écarts absolus 1,0 ; 17 écarts ≥ 5 ; maximum +50,5, ex. 19,5 → 70,0 pour « Flores », CA Boca Juniors) ; **1 ligne retirée, qui est un doublon** (7 564 → 7 563 : « Lucas Paquetá », CR Flamengo, note 81, présent deux fois dans `HEAD` ; voir §8.7) ; colonnes `Ability (0-99)` et `Note FM` supprimées ; onglet `Statuts` remplacé par `Preferred moves` ; onglet `Amérique` modifié. À décider : valider tel quel, corriger (ex. le joueur retiré, les notes aberrantes), ou écarter. **Tant que D1 n'est pas prise, le Lot 2 reste bloqué.**
- **D2 — calibration** (Lot 3, partie 3c). Voir le protocole de mesure ci-dessous ; **aucun commit du modulateur sans mesure**.

### 8.4 Lots

#### Lot 1 — Compétitions
- **Périmètre exact** : `src/ligue1sim/champions_league.py`, `world_cup.py`, `knockout.py`, `custom_competition.py`, `nations.py` ; tests `tests/test_champions_league.py`, `test_world_cup.py`, `test_knockout.py`, `test_nations.py`. Contenu : phase de ligue (36 clubs, 4 chapeaux, 8 journées, 8 directs, 16 barragistes), tirage de la Coupe du Monde par confédération, tirs au but, `knockout_legs`/`final_legs`, `knockout_builder`, `league_phase`.
- **Dépendances non suivies à inclure** : aucun fichier non suivi (aucun import vers `match_stats`, `live_commentary`, `nlg_live`). **Dépendances sur d'autres lots (mises en évidence par l'essai)** : (a) **3a** pour `simulate_match(..., suspended_*/injured_*)` ; (b) **Lot 2** pour le test `test_load_national_teams_returns_only_complete_squads_of_18` (données). Options : exécuter le Lot 1 **après** 3a et le Lot 2, ou **scinder** `nations.py`/`test_nations.py` pour laisser dans le Lot 2 ce qui dépend des données (à valider à l'exécution).
- **Prérequis** : 3a commité ; relecture des règles (phase de ligue, tirage, tirs au but).
- **Critère de vérification** : §8.1 ; les 9 tests de simulation de tournoi (`test_knockout`, `test_custom_competition`, `test_world_cup`, `test_champions_league`) et `test_nations` verts sur `git archive HEAD`.
- **Statut** : **prêt à commiter** depuis le commit de 3a, **à condition de scinder `tests/test_nations.py`** (essai à blanc vert, 996 verts avec 3a ; voir §8.7). *(Statut initial « bloqué » : levé par l'essai du 07/10/2026.)*

#### Lot 2 — Notes et attributs FM
- **Périmètre exact** : `src/ligue1sim/players.py`, `clubs.py` ; `scripts/scrape_fminside_attributes.py` ; `app.py` (Streamlit : `player.note` au lieu de `note_fm`) ; tests `tests/test_players.py`, `tests/test_clubs.py` ; **suppression** de `tests/test_scrape_fminside_attributes.py` (teste une fonction retirée) ; **`data/joueurs.xlsx`**, commité **avec** le code, jamais séparément.
- **Dépendances non suivies à inclure** : aucune.
- **Prérequis** : **D1** (décision explicite du propriétaire sur `data/joueurs.xlsx`). Produire d'abord un rapport lisible des 82 écarts et du joueur retiré (la liste complète, pas seulement la synthèse de §8.3).
- **Critère de vérification** : §8.1 ; contrôle que la suite lit bien le classeur commité (pas une copie locale).
- **Statut** : **BLOQUÉ** tant que D1 n'est pas prise.

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
- **Statut** : 3a et 3b **non bloqués par D1/D2 mais soumis à validation de la scission** ; **3c BLOQUÉ** jusqu'à la mesure et à la décision D2. Aucun commit du Lot 3 sans cette validation.

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

**3a (fait, `f5e37de`)** → **Lot 1** → `D1` → **Lot 2** → **3b** → `D2` (mesure + décision) → **3c** → **Lot 4** → **Lot 5**. *(Révisé le 07/10/2026 : le Lot 1 ne dépend plus du Lot 2 une fois `test_nations.py` scindé ; voir §8.7.)*
Les éléments qui ne dépendent d'aucune décision (3a, le Lot 1 scindé, éventuellement 3b après validation de la scission) peuvent passer avant `D1`. Le Lot 2 reste **bloqué** par D1 et 3c par D2.

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
