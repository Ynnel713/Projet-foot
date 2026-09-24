# État de l'intégration du lecteur canvas dans Streamlit

Reconnaissance du 24/09/2026. Aucun code modifié. Décision d'implémentation à venir.

## État du lecteur

- **Fichier** : [render/canvas.html](../render/canvas.html) (472 lignes). C'est le seul fichier "lecteur" réel — deux autres fichiers portent un nom voisin mais ne sont pas du code :
  - [render/canvas_preview.html](../render/canvas_preview.html) et [render/canvas_player_preview.html](../render/canvas_player_preview.html) sont des **artefacts générés** (une copie de `canvas.html` avec du JSON déjà injecté), produits respectivement par `scripts/render_preview.py` (voir sa ligne 2 : "produisant `render/canvas_preview.html`") et `scripts/render_player_preview.py` (voir sa ligne 3). Les deux sont exclus de git (`.gitignore:21-24`, commentaire "artefact de build, pas du code — render/canvas.html lui-même reste suivi").

- **Contenu** : `canvas.html` est un document HTML/JS **autonome**, sans aucune dépendance externe (pas de CDN, pas de librairie tierce — vérifié dans le `<head>` et le `<script>` du fichier). Un unique `<canvas>` 2D (1200×780), dessiné à chaque frame via `requestAnimationFrame` (`render/canvas.html:280` et `:398`). Deux blocs de contrôles UI cohabitent dans le DOM et sont montrés/masqués en JS selon le mode détecté : `#controls`/`#toggle`/`#replay` (mode gabarit isolé, historique) et `#playerControls`/`#progressBar`/`#carton` (mode "player", ajoutés brief "canvas player" du 23/09/2026).

- **Format d'entrée** : le script injecte les données par un **remplacement textuel exact** de la chaîne littérale `/*__SEQUENCE_JSON__*/null` (`render/canvas.html:106`) — "un simple replace() textuel suffit, aucun templating" (commentaire du fichier, ligne 98-105). Le JSON injecté peut prendre deux formes, auto-détectées selon sa structure (`render/canvas.html:118-119`, `const isPlayerMode = clips.length > 1`) :
  - un objet unique (ou tableau à 1 élément) → **mode "gabarit isolé"** : une seule séquence/action, produite par `ligue1sim.animation.serialize.frame_sequence_to_json`.
  - un tableau de 2+ éléments → **mode "player"** (celui qui correspond aux "temps forts") : plusieurs clips, avec barre de progression cliquable, scoreboard, cartons intermédiaires entre les occasions — produit par `engine/narrative_player.py::clips_to_json` (ligne 310). Le schéma exact du JSON attendu est documenté dans [docs/canvas_json_schema.md](canvas_json_schema.md).

- **Statut** : ni purement "autonome" ni figé "à embarquer" — conçu pour les **deux** usages via le même mécanisme de remplacement de placeholder, et les deux sont déjà implémentés et fonctionnels aujourd'hui :
  1. **Fichier autonome** ouvrable seul dans un navigateur, une fois le JSON injecté dans une copie du fichier (`scripts/render_preview.py`, `scripts/render_player_preview.py`, servis en local via le serveur statique `canvas-static` de `.claude/launch.json`, port 8610).
  2. **Composant embarqué** dans Streamlit via `st.components.v1.html(html, height=..., scrolling=False)`, où `html` est le texte de `canvas.html` avec le placeholder déjà remplacé (`apps/streamlit_preview.py:220-225` pour le mode gabarit, `:233-241` pour le mode match/player).

- **Fonctionnel, vérifié** : capture d'écran [docs/previews/canvas/streamlit_integration.png](previews/canvas/streamlit_integration.png) prouve le rendu embarqué. Vérifié en direct dans cette session (`apps/streamlit_preview.py` lancé sur `http://localhost:8600`, mode "match") : les 4 premiers clips d'un match PSG–Monaco se sont enchaînés avec navigation (précédent/pause/rejouer/suivant), scoreboard, gardiens et 22 joueurs, comme attendu.

## Point de branchement Streamlit

- **Écran** : [app.py](../app.py), fonction `_render_match_rows` (ligne 1261) — c'est elle qui affiche la liste verticale des matchs de la journée, appelée depuis l'écran de saison à la ligne 847 (`_render_match_rows(journee.matches)`), juste au-dessus du bouton "Simuler la journée" / "Journée suivante →" (lignes 849-857).

- **Génération des lignes** : une boucle Python `for index, match in enumerate(matches)` (app.py:1263) sur `matches: list[Match]` (`ligue1sim.schedule.Match`) — **pas** de `st.dataframe`. Chaque ligne est un `st.container` avec une clé unique (`key=f"ms_card_{id(match)}_{index}"`), découpé en 3 colonnes `st.columns([3, 1, 3])` (app.py:1265) : équipe domicile / score / équipe extérieure. Le score est un `st.button` (activé seulement si `match.played and match.events is not None`, app.py:1279) qui, au clic, écrit le match choisi dans `st.session_state` (`_OPEN_MATCH_KEY`, `_OPEN_MATCH_LIST_KEY`, `_OPEN_MATCH_INDEX_KEY`) puis appelle `st.rerun()` pour ouvrir l'écran de détail (app.py:1285-1288).

- **Mécanisme d'ajout d'un bouton "Voir temps forts"** : la structure actuelle le permet **sans refonte**. Deux points d'appui déjà en place dans ce même fichier, sur ce même type de ligne :
  - `st.columns([3, 1, 3])` peut devenir `st.columns([3, 1, 3, 2])` (ou un bouton ajouté dans la colonne score existante, sous le score) pour loger le nouveau bouton.
  - Le mécanisme "bouton → écrit dans `st.session_state` → `st.rerun()` → un autre bloc du script affiche l'écran cible" est **déjà utilisé deux fois** dans ce fichier pour un besoin similaire : ouvrir le détail d'un match (`_OPEN_MATCH_KEY`, ci-dessus) et ouvrir la fiche d'un club (`_OPEN_CLUB_KEY`, `_render_team_cell`, app.py:1314-1316). "Voir temps forts" suivrait exactement ce même patron (ex. `_OPEN_HIGHLIGHTS_KEY`), sans nouveau mécanisme Streamlit à introduire.
  - Condition d'activation naturelle : comme le bouton score, seulement si `match.played and match.events is not None` (un match non joué n'a pas de résumé à montrer).

## Chemin de données (match → résumé → lecteur)

Aucune fonction existante ne fait aujourd'hui ce chemin complet pour un **vrai** match de `app.py` — la chaîne qui fonctionne réellement de bout en bout est celle d'`apps/streamlit_preview.py`, mode "match", avec des données **synthétiques** (clubs fictifs, seed fixe) :

1. `apps/streamlit_preview.py::build_match_clips_json(seed, max_occasions)` (lignes 178-201) — simule un match (`ligue1sim.simulation.simulate_match`), puis enchaîne :
2. `engine/narrative.py::match_result_from(match, events, home_lineup, away_lineup, date=...)` (ligne 233) → assemble un `MatchResult`.
3. `engine/narrative.py::build_timeline(match_result)` (ligne 744) → construit la `Timeline` narrative (occasions + buts réels fusionnés).
4. `engine/narrative_player.py::build_clips(timeline, max_occasions)` (ligne 244) → construit les `Clip` (frames d'animation par occasion retenue).
5. `engine/narrative_player.py::clips_to_json(clips, timeline)` (ligne 310) → sérialise en JSON, forme "mode player" attendue par `canvas.html`.

**Ce chemin n'est pas directement rebranchable tel quel sur un match réel de `app.py`** — voir Inconnues ci-dessous, point 1.

Séparément, [src/ligue1sim/animation/render/component.py](../src/ligue1sim/animation/render/component.py), fonction `render_sequence` (ligne 12), est présentée dans sa docstring comme LE point d'entrée prévu pour "l'écran de détail de match (app.py)" — mais son corps est :
```python
raise NotImplementedError
```
avec un commentaire `# TODO(animation): ...` juste au-dessus (ligne 21). **Jamais implémentée, jamais appelée nulle part** (recherche exhaustive : aucune occurrence de `render_sequence(` dans le dépôt en dehors de sa propre définition et de deux mentions dans `docs/simulation_physique_archi.md`). De plus, sa signature (`render_sequence(sequence: Sequence, ...)`) prend **une seule** `Sequence` — la forme "mode gabarit isolé", pas la forme multi-clips ("mode player"/Timeline) que les "temps forts" demandent. Ce stub n'est donc probablement pas la bonne fonction à compléter telle quelle pour ce brief ; voir Inconnue 2.

## Inconnues restantes

1. **Lineups des matchs déjà joués non conservées.** `ligue1sim.schedule.Match` (`src/ligue1sim/schedule.py:13-18`) ne stocke que `home`, `away`, `home_goals`, `away_goals`, `events` (`MatchEvents`). `MatchEvents.home_lineup`/`away_lineup` (`src/ligue1sim/events.py:273-274`) ne sont que des `list[PlayerMatchStat]` (nom/poste/titulaire), **pas** des `ligue1sim.lineup.Lineup` complets (note, âge...). Or `match_result_from` exige un vrai `Lineup` en plus de `events` (voir ci-dessus). Le `Lineup` réellement utilisé à la simulation est calculé par `pick_best_formation` **à l'intérieur** de `simulate_match` (`src/ligue1sim/simulation.py:401-402`) et n'est jamais retourné à l'appelant. Pour un vrai match de la journée, il faudrait donc soit (a) recalculer `pick_best_formation(club, ...)` au clic sur "Voir temps forts" — avec le risque que le club ait changé depuis (`Season.injuries`/`Season.suspensions`, `src/ligue1sim/season.py:28-29`, évoluent au fil des journées) et ne reproduise plus exactement la compo historique, soit (b) faire persister le `Lineup` au moment de la simulation. **Décision à prendre, pas devinée ici.**
2. **Quelle fonction compléter : `render_sequence` ou une nouvelle fonction ?** `render_sequence` (stub existant, pensé pour app.py) a la signature d'une "Sequence" isolée, pas d'un match complet à plusieurs clips. Le vrai besoin ("temps forts" = plusieurs occasions d'un match) correspond au chemin `build_timeline` → `build_clips` → `clips_to_json`, jamais branché sur `render_sequence`. Compléter le stub existant ou écrire une fonction dédiée (sur le modèle de `build_match_clips_json`) est une décision d'implémentation, pas traitée ici.
3. **Aucun test ne couvre le rendu visuel du lecteur.** `tests/test_canvas_e2e.py` teste bout-en-bout la chaîne `build_timeline`/`build_clips`/`clips_to_json` (JSON produit, invariants de score) mais dit explicitement ne PAS couvrir le rendu navigateur ("aucune dépendance navigateur... le rendu visuel est couvert par les captures de `docs/previews/canvas/`, pas par ce test", tests/test_canvas_e2e.py, docstring). Aucun test Selenium/Playwright ou équivalent n'existe dans le dépôt (aucune dépendance de ce type dans `pyproject.toml`).
4. **Performance au clic.** `build_match_clips_json` est décoré `@st.cache_data` dans le preview, mais génère les frames d'animation de plusieurs occasions à la volée (coût non mesuré ici pour un vrai match — voir le diagnostic de lenteur de la suite de tests de cette même session, où le même type de génération de frames pour 100 matchs domine à 84% le temps total : cela suggère un coût non négligeable PAR MATCH, à vérifier avant de brancher un bouton par ligne × N matchs par journée).

## Point d'escalade

Aucun — tous les éléments demandés (lecteur, point de branchement, fonction de génération du résumé) ont été localisés avec un chemin exact. La structure Streamlit actuelle (`st.columns` + `st.session_state` + `st.rerun()`) permet d'ajouter un bouton par ligne **sans refonte**. Les inconnues listées ci-dessus (surtout l'Inconnue 1, lineups non conservées) sont des décisions de conception pour le prochain brief, pas des blocages de reconnaissance.
