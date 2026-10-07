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

## PWA React — cible réelle du branchement

**Correction importante** : la section "Point de branchement Streamlit" ci-dessus documente `app.py`, mais ce n'est **plus** l'app que le propriétaire utilise au quotidien. `Lancer l'appli.bat` lance en réalité l'API FastAPI (port 8000) + la PWA React de `ui/` (port 5173) — commentaire du `.bat` : "L'appli est passée de Streamlit à une PWA React + API FastAPI". La reconnaissance ci-dessous porte sur cette PWA, la vraie cible d'un bouton "Voir temps forts" en usage réel.

### 2.1 — Racine, framework, gestionnaire de paquets

- **Racine** : [ui/](../ui) (à la racine du dépôt, à côté de `src/`, `api/`, `engine/`).
- **Framework** : React 19 + **Vite** (`ui/vite.config.js` : `@vitejs/plugin-react`, `@tailwindcss/vite`, `vite-plugin-pwa`) — ni Next.js ni Create React App.
- **Gestionnaire de paquets** : **npm** (`ui/package-lock.json` présent, aucun `yarn.lock`/`pnpm-lock.yaml`). Scripts (`ui/package.json`) : `npm run dev` (Vite dev server), `npm run build`, `npm run lint` (oxlint), `npm run preview`.
- Autres dépendances notables déjà en place : `react-router-dom` (routage), `zustand` (état global), `framer-motion` (animations de transition), `lucide-react` (icônes) — **aucune** dépendance canvas/animation existante côté JS.

### 2.2 — Composant liste des matchs d'une journée

- **Écran** : [ui/src/routes/Simulation.jsx](../ui/src/routes/Simulation.jsx) — composant fonctionnel (`export default function Simulation()`), état local via `useState`/`useCallback`/`useEffect` (pas de Context ni de Redux pour cet écran).
- **Ligne de match** : [ui/src/components/simulation/MatchRow.jsx](../ui/src/components/simulation/MatchRow.jsx) — composant fonctionnel dédié, `export default function MatchRow({ match, onClick })`.

### 2.3 — Génération des lignes et point d'ajout du bouton

- `Simulation.jsx:124-126` : boucle `matches.map((m) => <MatchRow key={...} match={m} onClick={() => openPitch(m)} />)` — un `.map()` React classique sur le tableau `matches` (état local, chargé depuis l'API), pas de `<table>`.
- Dans `MatchRow.jsx:25-31`, la ligne est un `<div className="flex items-center justify-between">` avec 3 enfants : nom domicile (`flex-1`), score (`shrink-0`), nom extérieur (`flex-1`). **Le bouton "Voir temps forts" s'ajouterait comme un 4e enfant de ce même `flex`**, après le `<span>` du nom extérieur (ligne 30), ou sous la ligne actuelle (à côté de `<ScorersLine>`, ligne 32).
- **Point d'attention concret** : toute la ligne `MatchRow` est déjà cliquable dans son ensemble (`onClick={clickable ? onClick : undefined}` sur le `motion.div` racine, ligne 20, qui ouvre `PitchView` via `openPitch`). Un nouveau bouton "Voir temps forts" à l'intérieur devra appeler `event.stopPropagation()` dans son propre `onClick`, sinon le clic déclenchera aussi la navigation vers `PitchView` portée par le conteneur parent.

### 2.4 — Récupération des données et état du match sélectionné

- **Mécanisme HTTP** : [ui/src/api/client.js](../ui/src/api/client.js) — un seul point d'entrée `request(path, options)` (lignes 8-18) qui fait un `fetch` JSON simple (`BASE_URL` vide en usage normal : même origine que l'API FastAPI qui sert aussi `ui/dist`, voir `api/main.py`). Chaque endpoint est une fonction exportée d'une ligne (ex. `export const getMatches = (id, journee) => request(...)`, ligne 36-37).
- **Endpoint de la liste des matchs** : `GET /api/competitions/{id}/matches?journee=N` (`getMatches`, `client.js:36-37`).
- **Endpoint le plus proche d'un "détail de match"** : `GET /api/competitions/{id}/pitch?home=&away=&journee=` (`getPitchView`, `client.js:42-45`), backend `api/routers/competitions.py:250-251` (`get_pitch_view`) — retourne aujourd'hui une **formation statique** (positions des 22 joueurs, sans animation), consommé par [ui/src/routes/PitchView.jsx](../ui/src/routes/PitchView.jsx). Aucun endpoint n'expose aujourd'hui une timeline/des clips animés.
- **État du "match sélectionné"** : ni Context, ni `useState` partagé, ni Zustand ([ui/src/store/useGameStore.js](../ui/src/store/useGameStore.js) ne contient que `activeCompetitionId/Label/Format` et `followedClub` — rien sur un match précis). Le match sélectionné transite **par l'URL** : `Simulation.jsx:155-159` (`openPitch`) construit des `URLSearchParams` (`home`, `away`, `journee`) et navigue vers `/competition/:id/pitch?...` ; `PitchView.jsx:16,21-27` les relit via `useSearchParams`. Un écran "temps forts" suivrait le même patron (nouvelle route + mêmes query params).

### 2.5 — Évaluation des 3 options d'intégration (pas de décision)

| Option | Faisabilité | Effort | Avantages | Inconvénients |
|---|---|---|---|---|
| **A. Iframe** (`<iframe srcDoc={html} />`) | Haute — `canvas.html` est déjà 100% autonome (aucune dépendance externe, confirmé section "État du lecteur"), exactement le même document HTML que celui déjà injecté et embarqué avec succès via `st.components.v1.html` côté Streamlit. | Faible — même recette qu'`apps/streamlit_preview.py:220-225` (lire `canvas.html`, remplacer le placeholder par le JSON), juste servi en `srcDoc` d'un `<iframe>` React au lieu d'un composant Streamlit. | Isolation totale du DOM/CSS (aucun risque d'interférence avec Tailwind/React), **zéro réécriture** du JS existant donc risque de régression minimal sur l'animation (score/minute/buteur exacts, invariant "intouchable"). | Communication avec le reste de l'app (fermer l'écran, ajuster la hauteur à l'écran mobile) demande `postMessage`/redimensionnement manuel ; se sent moins "natif" que le reste de la PWA. |
| **B. Composant React natif** (réécrire en `<canvas>` + hooks) | Moyenne — techniquement faisable, mais `canvas.html` embarque ~370 lignes de logique (détection de mode, interpolation `findSegment`/`lerp`, dessin `drawFrame`, scoreboard, carton intermédiaire avec timer, barre de progression cliquable, machine à états play/pause/next/prev) à porter fidèlement. | Élevé — réécriture complète de cette logique en JS/React (`useRef` + `useEffect` + `requestAnimationFrame`), sans test navigateur existant pour détecter une régression de comportement (voir Inconnue 3 ci-dessus). | Intégration native totale (thème Tailwind, transitions `framer-motion`, partage d'état avec le reste de l'app) ; pas d'iframe à dimensionner. | Effort et risque les plus élevés ; double maintenance de la même logique d'animation en deux endroits (Python ne génère plus de HTML, mais l'invariant visuel doit rester identique) ; aucun filet de test pour garantir la fidélité du portage. |
| **C. Web Component** (wrapper `customElements.define`) | Moyenne-haute — envelopper le JS existant du `<script>` de `canvas.html` dans une classe `HTMLElement` (essentiellement la même logique, pas réécrite, juste déplacée dans `connectedCallback`), utilisable comme `<canvas-player clips={...} />` (React 19 gère bien les custom elements). | Moyen — pas de réécriture de la logique d'animation (même risque de régression que l'option A), mais **nouvelle plomberie de build** : `render/canvas.html` ne fait aujourd'hui partie d'aucun pipeline Vite (`ui/`) — il faudrait le faire empaqueter par Vite ou le charger comme script séparé. | Réutilise la logique JS quasi telle quelle (bas risque de régression) tout en devenant un vrai nœud de l'arbre React (pas de `postMessage`). | Pattern inconnu du code actuel (aucun Web Component existant dans `ui/src`, aucune dépendance de ce type dans `package.json`) ; passage de props complexes (le tableau de clips) à un custom element demande une assignation impérative de propriété (via `ref`), pas un simple attribut HTML. |

### 2.6 — Fichiers à modifier pour brancher le lecteur (identifiés, non modifiés)

- [ui/src/components/simulation/MatchRow.jsx](../ui/src/components/simulation/MatchRow.jsx) — ajouter le bouton "Voir temps forts" (voir 2.3).
- [ui/src/routes/Simulation.jsx](../ui/src/routes/Simulation.jsx) — passer un nouveau callback à `MatchRow` (même patron que `onClick={() => openPitch(m)}`, ligne 125).
- Un **nouveau fichier route** (n'existe pas encore), ex. `ui/src/routes/Highlights.jsx`, sur le modèle de [ui/src/routes/PitchView.jsx](../ui/src/routes/PitchView.jsx) (lecture des query params, fetch, affichage).
- [ui/src/App.jsx](../ui/src/App.jsx) — enregistrer la nouvelle route dans `<Routes>` (à côté de la route `pitch`, ligne 25).
- [ui/src/api/client.js](../ui/src/api/client.js) — nouvelle fonction d'appel (ex. `getHighlights`), même patron que `getPitchView` (lignes 42-45).
- Côté backend (hors PWA à proprement parler, mais nécessaire) : [api/routers/competitions.py](../api/routers/competitions.py) — un nouvel endpoint (voisin de `get_pitch_view`, ligne 250-251) qui produirait le JSON des clips pour un match réel — **butte directement sur l'Inconnue 1 ci-dessus** (lineups des matchs déjà joués non conservées).
- `render/canvas.html` : selon l'option choisie (2.5), soit **non modifié** (A, C réutilisent son JS tel quel), soit remplacé par une réécriture React (B).

### 2.7 — Compo persistée dans le Match (Étape B, 07/10/2026) — Inconnue 1 levée côté moteur

`MatchEvents` porte désormais `home_lineup_snapshot` / `away_lineup_snapshot` (`LineupSnapshot | None`, défaut `None`), pris dans `events.generate_match_events` au moment où la compo est consommée. **Source de vérité unique** : le moteur graphique lit ces compos via `lineup_snapshot.persisted_lineups` / `require_persisted_lineups` et n'appelle jamais `pick_best_formation`. Purement additif : aucun tirage, score ni événement modifié.

**Schéma JSON** (`match_persistence.match_to_json`, `format_version` 1) :

```
{"format_version": 1, "home", "away", "home_goals", "away_goals",
 "events": {…MatchEvents existant…,
   "home_lineup_snapshot": <LineupSnapshot>, "away_lineup_snapshot": <LineupSnapshot>} | null}

LineupSnapshot = {
  "schema_version": 1,
  "lineup": {club_name, formation, rating, gk_rating, def_rating, mid_rating, att_rating,
             bands: {nom: ligne}, substitutes: [],            # le Lineup EXACT de la simulation
             players: [Player complet ×11]},                 # id, prenom, nom, poste, poste_secondaire, categorie,
                                                             # note, age, nationalite, attributes (47), preferred_moves, pied…
  "starters": [{player_id, name, poste, band, x, y} ×11],     # onze de départ ; x/y 0-100 = place_starting_xi(attacking_up=True) à la simulation (trace d'audit)
  "entered_substitutes": [Player complet, …]                  # remplaçants ayant réellement joué (statut "remplaçant")
}
```

Limites assumées (rien d'inventé) : le moteur n'a ni « rôle tactique » ni « consigne individuelle » distincts ; leurs équivalents portés tels quels sont `Player.categorie` (rôle/style) et `Player.preferred_moves`, plus `Lineup.bands` (ligne du dispositif). `enrich_with_background` recalcule ses positions depuis `lineup` (poste + bande) ; `starters[].x/y` ne sont pas lus par lui. Le banc non utilisé n'est pas persisté.

**Règle de fallback (matchs sans snapshot)** : la lecture est tolérante (clé absente → défaut du champ, clé inconnue ignorée, `dataclass_codec`). Un match ancien se recharge sans erreur avec snapshots à `None` ; `persisted_lineups` renvoie alors `None` et `require_persisted_lineups` lève `LineupNotPersistedError`. **Aucun recalcul via `pick_best_formation`** : le moteur graphique doit dégrader (pas d'animation de compo pour ce match). Rappel : aucune persistance disque de Match n'existe encore (`api/store.py` est en mémoire) ; `match_persistence` fournit le format, il n'est pas branché au store.

Fichiers : `src/ligue1sim/{lineup_snapshot,match_persistence,dataclass_codec}.py` (nouveaux), `src/ligue1sim/events.py` (2 champs + 2 lignes) ; tests `tests/test_{lineup_snapshot,dataclass_codec}.py`.

### 2.8 — Chaîne de remplacement, qui est sur le terrain à la minute m (Étape B bis, 07/10/2026)

**Réponse : oui, les remplacements sont déjà dans le Match et persistés — rien n'a été ajouté au `LineupSnapshot` pour eux** (les dupliquer créerait une 2ᵉ source de vérité). `Match.events.substitutions` est une `list[SubstitutionEvent]`, écrite par `events._play_match_squad`, sérialisée avec tout `MatchEvents` par `match_persistence` (test `test_substitution_events_are_persisted_with_the_match`) :

```
SubstitutionEvent = {club_name: str, player_off: str, player_on: str, minute: int, zone: Zone | None}
```

Les joueurs y sont identifiés par **nom** (clé d'effectif de tout le moteur, comme `PlayerMatchStat.player_name`), pas par `player_id`. Le nom se résout en `Player` complet via `snapshot.lineup.players` (titulaires) et `snapshot.entered_substitutes` (entrants). Cartons : `Match.events.cards` (`CardEvent{club_name, player, minute, card_type: "yellow"|"second_yellow"|"direct", zone}`), aussi persistés.

**API** : `lineup_snapshot.players_on_pitch(match, club_name, minute) -> list[Player]`, depuis le seul Match rechargé (jamais `pick_best_formation`). Convention : un joueur est présent de `minute_on` à `minute_off` (un remplacement à la minute m fait sortir le sortant et entrer l'entrant dès m, comme `_SquadEntry.minute_range`) ; un rouge (`direct`/`second_yellow`) retire le joueur à sa minute sans remplaçant ; un titulaire blessé sans remplaçant disponible reste sur le terrain (comportement du moteur).

**Incohérence du moteur, à arbitrer (non corrigée, résultat sportif intact)** : remplacements et cartons sont tirés indépendamment, donc un joueur déjà expulsé peut être « remplacé » plus tard (ex. seed 11 : second jaune à la 17ᵉ, remplacé à la 64ᵉ). `players_on_pitch` suit l'événement persisté à la lettre (l'entrant joue à partir de la 64ᵉ, l'équipe reste à 10 jusque-là) ; le cas est figé par `test_engine_substitutes_an_already_sent_off_player_and_the_helper_does_not_hide_it`.

### 2.9 — Déterminisme de `enrich_with_background` (audit + preuve)

Audit du chemin `enrich_with_background` → `_opponent_positions` → `pitch_layout.place_starting_xi` / `_tactical_drift` : pas d'horloge (`time`/`datetime`), pas d'`uuid`, pas de `hash()` builtin, pas de `np.random` ; `random` n'est importé que pour `deterministic_rng` (graine sha256, hors de ce chemin) ; aléas de drift = `_deterministic_unit` (sha256, `PYTHONHASHSEED`-indépendant) ; regroupement par bande via `dict`/`sorted(band)` (ordre d'insertion garanti) ; aucun état global mutable.
Seul point théorique : `inactive_scorer_ids = set(...)` est itéré, et `sum(scorer_cb_ys)` additionne des flottants dans l'ordre de ce `set` (qui varie avec `PYTHONHASHSEED` pour des ids `str`) — une addition flottante n'étant pas associative, un écart au dernier bit est concevable avec ≥ 3 défenseurs centraux. **Mesuré : aucun écart** (toutes les permutations donnent la même somme sur 6 dispositifs, et séquence identique sous 4 `PYTHONHASHSEED`). Latent, non masqué ; un `sorted(...)` lèverait le doute si on veut le fermer (code d'animation, hors périmètre de cette étape).
Preuves : `test_enrich_with_background_is_deterministic_on_a_reloaded_lineup` (deux appels, séquences égales) et `test_enrich_with_background_is_stable_across_processes[0|1|42|2026]` (même hash de séquence dans des processus à `PYTHONHASHSEED` différents).

### 2.10 — Match sans `LineupSnapshot` : comportement attendu côté UI

Quand `persisted_lineups(match)` renvoie `None` (match antérieur au snapshot, ou sans `MatchEvents`) :
- **Pas de crash** : l'API attrape `LineupNotPersistedError` (levée par `require_persisted_lineups` / `players_on_pitch`) ; l'endpoint de clips répond un état explicite, jamais une 500.
- **Pas de recalcul** (`pick_best_formation` interdit) et **pas de reconstruction approximative** depuis `PlayerMatchStat` (même pas « les titulaires seulement »).
- **Indisponibilité signalée** : l'animation de composition n'est pas proposée ; le bouton « Voir temps forts » est désactivé (ou remplacé) avec le message **« Animation indisponible : la composition de ce match n'a pas été enregistrée. »** Réponse API suggérée : `{"available": false, "reason": "lineup_not_persisted"}`.
- Le reste de la fiche match (score, buteurs, cartons, remplacements, notes) reste affiché normalement : seuls les composants qui exigent la compo exacte sont désactivés.

### 2.11 — Intégration PWA par iframe : contrat parent ↔ `canvas.html` (protocole `version` 1, 07/10/2026)

Décision d'architecte : **iframe**, `render/canvas.html` réutilisé tel quel (source unique, aucune copie dans `ui/`). Ni réécriture React native, ni Web Component. Aucune persistance disque.

**Chaîne de données.** `Match` (en mémoire, avec `LineupSnapshot`, voir 2.7) → `GET /api/competitions/{id}/animation?<mêmes paramètres que /pitch>` ([api/routers/competitions.py](../api/routers/competitions.py), [api/animation.py](../api/animation.py)) → `ui/src/utils/matchAnimation.js` (`buildAnimationPayload`) → `MatchAnimation.jsx` → iframe. Le calcul des clips reste en Python (`narrative.match_result_from` → `build_timeline` → `build_clips` → `clips_to_json`, moteur de rendu inchangé) **à partir de `persisted_lineups(match)` uniquement** : ni `pick_best_formation`, ni reconstruction depuis `PlayerMatchStat`. *Écart avec la consigne initiale :* la fonction de construction du payload est donc en deux temps — le calcul des frames côté API (seul endroit où le moteur existe), puis un adaptateur React qui valide la réponse (version, forme, clips non vides) et signale l'indisponibilité au lieu de produire un payload partiel.

**Service de l'iframe.** `GET /render/canvas.html` ([api/main.py](../api/main.py)) sert uniquement ce fichier. URL : `{API}/render/canvas.html?embed=1&parent_origin=<origine de la PWA, encodée>`. Le mode embarqué n'existe que si `embed=1` ; sans ce paramètre le fichier est strictement le lecteur standalone (placeholder `/*__SEQUENCE_JSON__*/null` inchangé, `startPlayer(SEQUENCE_DATA, null)`). Le service worker de la PWA buildée exclut `/render/` et `/api/` de `navigateFallback` ([ui/vite.config.js](../ui/vite.config.js)), sinon l'iframe recevrait `index.html`.

**Messages.** Un seul canal `window.postMessage`. Tout message porte `source`, `version` (entier, `1`) et `type`. Protocole **fermé** : seuls les types ci-dessous existent, tout autre message est ignoré sans réponse.

| Sens | `source` | `type` | Champs | Quand |
|---|---|---|---|---|
| iframe → parent | `simulafoot-canvas` | `ready` | — | une fois, au chargement, handshake |
| parent → iframe | `simulafoot-host` | `init` | `payload: { match: {home, away, home_goals, away_goals}, clips: [...] }` | **une seule fois**, après `ready` ; `clips` = le tableau JSON « mode player » déjà consommé par `canvas.html` (voir `docs/canvas_json_schema.md`), qui porte déjà noms de clubs, score progressif et couleurs de maillots (`metadata.teams`, `home_team`, `away_team`, `score_before/after`) |
| iframe → parent | `simulafoot-canvas` | `clipchange` | `index`, `total`, `minute` | initial, puis à chaque changement de clip |
| iframe → parent | `simulafoot-canvas` | `ended` | — | une fois par passage, à la fin du carton du dernier clip |
| iframe → parent | `simulafoot-canvas` | `error` | `code`, `message`, + `supported`/`received` pour `version_mismatch` | `version_mismatch`, `invalid_payload` (payload vide/non tableau), `render_error` |

**Versionnement.** `version` figure dans les deux sens. Le parent ignore et signale (`version_mismatch`) tout message de l'iframe de version ≠ 1 ; l'iframe répond `error{code:"version_mismatch", supported:[1], received}` à un `init` de version ≠ 1 et ne démarre pas. Évolution : tout changement incompatible incrémente `version` ; l'API répond aussi `version` (≠ 1 ⇒ le parent affiche « version du protocole incompatible », sans monter l'iframe).

**Isolation.** L'iframe n'accède ni au store, ni à l'API, ni au système de fichiers : tout ce dont elle a besoin arrive dans `init`. Elle n'émet que vers `parent_origin` (jamais `'*'`) et n'accepte que les messages dont `event.source === window.parent` et `event.origin === parent_origin`. Le parent n'accepte que `event.source === iframe.contentWindow` et `event.origin === origine de l'iframe`, et poste `init` avec cette origine pour cible. `sandbox="allow-scripts allow-same-origin"` (pas d'`allow-top-navigation` : l'iframe ne peut déclencher aucune navigation de la PWA ; `allow-same-origin` est requis pour que `event.origin` soit l'origine réelle et non `"null"`). Les boutons de lecture restent dans `canvas.html`.

**Match sans `LineupSnapshot` (voir 2.10).** L'API répond 200 `{"version":1,"available":false,"reason":"lineup_not_persisted"}` ; **le parent ne monte pas l'iframe** et affiche, dans un `role="status"`, le message *« Animation indisponible : la composition de ce match n'a pas été enregistrée. »* L'iframe n'est jamais chargée pour un match non animable. Autres `reason` (même traitement, message propre) : `no_highlights` (« Aucun temps fort à animer pour ce match. »), `not_played` ; côté client : `protocol_version_mismatch`, `invalid_payload`, `load_error`, `no_handshake` (pas de `ready` sous 10 s : lecteur injoignable).

**Point d'insertion dans l'UI.** [ui/src/routes/PitchView.jsx](../ui/src/routes/PitchView.jsx) (fiche match, route `/competition/:id/pitch`) : un bouton « Voir l'animation » sur la ligne du bouton « Retour », qui ouvre une fenêtre modale plein écran (`AnimationDialog`) contenant `MatchAnimation`. La mise en page de la fiche (calée sur la hauteur de la fenêtre, 4 colonnes) n'est pas modifiée ; fermer la fenêtre (bouton ou Échap) démonte le composant, donc l'iframe et son écouteur de messages.

**États de chargement (retour visuel continu, 07/10/2026).** La modale s'ouvre immédiatement au clic (mesuré : 212 ms) et ne se vide jamais entre le clic et le premier frame :
1. *Appel API en cours* : pastille qui tourne + « Calcul des temps forts du match en cours… » + compteur en secondes (`N s — cela peut durer une quinzaine de secondes pour un match riche en occasions.`), `role="status"`.
2. *Payload reçu, iframe montée, lecteur pas encore prêt* : l'iframe est recouverte d'un calque « Chargement du lecteur… » (même pastille) jusqu'au premier `clipchange`.
3. *Premier `clipchange` reçu* : le calque disparaît, le statut affiche « Temps fort i/N · minute' ».
Mesure (match de 15 clips, `npm run dev`, React `StrictMode` donc 2 appels API concurrents) : indicateur visible à 212 ms ; compteur de 0 s à 18 s ; iframe montée à 19,3 s ; **premier frame à 19,8 s** après le clic. Même mesure hors StrictMode (appel unique) : 13,6 s (22 clips) / 7,3 s (10 clips), voir `docs/known_issues.md` ticket 4.

**Note : React `StrictMode` en développement.** En mode développement (`npm run dev`), `StrictMode` exécute les effets deux fois : l'appel `GET /api/competitions/{id}/animation` est donc **émis deux fois** et le serveur calcule les deux réponses en concurrence, ce qui explique une latence perçue environ **double** de la latence réelle d'un appel unique (19,8 s en dev pour un match de 15 clips, contre 13,6 s pour un appel unique de 22 clips ; les deux matchs n'ont pas le même nombre de clips, le rapport est indicatif). Comportement attendu : aucune correction n'est nécessaire, et le build de production (sans `StrictMode`) n'est pas concerné (un seul appel : 7,3 s pour 10 clips).

**Point de départ du timeout de 10 s (`no_handshake`).** Il est compté **à partir du montage de l'iframe, après réception du payload** — jamais depuis le clic. Il est armé dans l'effet du handshake de `MatchAnimation`, qui ne s'exécute que lorsque le payload existe ; pendant l'appel API (états 1 ci-dessus) aucun chronomètre de handshake n'existe. Il ne couvre donc que : téléchargement de `canvas.html`, exécution du script et émission de `ready`. Conservé tel quel, car l'iframe émet `ready` au chargement, avant tout traitement du payload (un payload de 9,5 Mo n'allonge pas ce délai). Preuve : sur le match de 15 clips, l'appel API a duré 19 s (> 10 s) sans aucun message d'erreur. Aucun faux positif « le lecteur n'a pas répondu » ne peut donc se produire pendant la génération de l'animation ; il ne se produit que si l'iframe est montée et ne répond pas (lecteur injoignable).

**Port de l'API en développement.** `simulafoot.bat` lance l'API sur le port 8000 ; `ui/.env.local` fixait `VITE_API_URL=http://localhost:8010`, donc `npm run dev` appelait un serveur absent. Corrigé en deux temps : (1) localement, `ui/.env.local` (ignoré par git, règle `*.local` de `ui/.gitignore`) mis à `http://localhost:8000` ; (2) **dans le code** : `ui/src/api/client.js` prend `http://localhost:8000` par défaut **en développement** quand `VITE_API_URL` est absente, et `ui/.env.example` (versionné) documente la variable ; `.env.local` n'est donc plus nécessaire sur un checkout propre. En build de production le défaut reste `""` (URL relative, l'API sert le frontend : même origine, y compris via tunnel ngrok ou IP locale d'un téléphone) — un défaut absolu `localhost:8000` casserait ces accès. Vérifié : en `npm run dev` (5173) les requêtes `/pitch`, `/matches`, `/animation` et `/render/canvas.html` vont vers `localhost:8000` et la modale d'animation fonctionne (match animable : lecteur affiché ; match sans snapshot : message §2.10, 0 iframe).

**Limites connues.** (1) **Latence/poids au clic** : voir `docs/known_issues.md` ticket 4 (13,6 s et 9,5 Mo pour 22 clips) ; non traité. (2) *Correction du 07/10/2026* : la docstring de `build_clips` (23/09/2026) décrit l'omission des événements dont le protagoniste n'est pas dans le onze de départ ; **non reproduite** depuis la correction des remplaçants (0 omission sur 299 événements, dont 27 à protagoniste remplaçant, tous rendus) ; le `continue` silencieux subsiste, voir ticket 5. (3) `requestAnimationFrame` est suspendu quand l'onglet/le volet n'est pas peint : le lecteur (et donc `ended`) n'avance qu'à l'écran.
