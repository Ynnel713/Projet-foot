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
