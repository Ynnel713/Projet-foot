# EM-01 — Découpage de `V2Match.jsx` et mémoïsation (S) — 120 min (moyenne)

**Status:** livré (09/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : un assembleur léger + composants dédiés ; l'écran de réglage (choix des clubs) séparé de l'écran de lecture.
- **Problème** : 840 lignes, redessin complet à chaque image.
- **Résultat** : aucun changement visible ; composants `React.memo` ; boucle de lecture déplacée telle quelle dans un hook.
- **Périmètre** : déplacement et mémoïsation seulement ; pas de style.
- **Composants** : `V2Match.jsx`, nouveaux fichiers de `components/match/`, `hooks/useMatchPlayback.js`.
- **Critères** : sur trace enregistrée, score, minutes de but, instants de ralenti et mi-temps **identiques** à l'ancien
  code ; médiane de durée d'image ≤ celle d'avant (build de production, x8) ; `npm run build` OK ; `npm run lint` : pas
  d'avertissement nouveau.
- **Tests** : comparaison des sorties (score, buts révélés) sur 3 traces ; mesure d'images par seconde avant/après ;
  capture avant/après identique.
- **Dépendances** : EM-00. **Risques** : boucle de lecture (fermetures sur les refs) → déplacement sans réécriture.

## Réalisé

- `routes/V2Match.jsx` (887 → 139 lignes) devient l'assembleur : chargement des clubs, lancement et sondage de l'API, mode
  `?fixture=` (EM-00) ; affiche `MatchSetup` (réglage) tant qu'aucune trace n'est lue, puis `MatchScreen` (lecture).
- `hooks/useMatchPlayback.js` : état de lecture, refs et **boucle de lecture recopiée à l'identique** (diff vide avec
  l'ancien effet) ; les remises à zéro, autrefois dupliquées entre le lancement et le mode `?fixture=`, sont regroupées
  dans `begin(trace, départ, lecture)` (au départ 0 : mêmes valeurs qu'avant) ; `receive` (trace reçue pendant le calcul)
  et `skipReplay` (bouton « RALENTI ⏭ »), stables (`useCallback`).
- `components/match/` : `MatchSetup`, `MatchScreen`, `V2Pitch` (terrain), `Momentum`, `LineupPanel`, `IntentionPanel`,
  `trace.js` (`clock`, `halfStart`, `interpolatedTick`, `rotated`, `situationAt`). Aucun style, texte ni constante changé.
- Mémoïsation (`React.memo`) : pelouse et marquages (`PitchGround`, dessinés une fois), cages (`GoalFrame`), bancs
  (`Bench`, ne reçoivent le temps qu'une fois l'échauffement commencé), compositions (`LineupPanel`), momentum (reçoit les
  minutes entamées et le nombre de buts vus au lieu de l'instant : redessiné une fois par minute ou par but), panneau
  d'intention (ne reçoit l'image que si un joueur est sélectionné), numéros de maillot (`useMemo`).
- Banc de comparaison (`.scratch/v2-ecran-match/mesures/01/`) : `harness-prod.js` sert une trace EM-00 à la place de l'API
  (interception de `fetch`) dans une build de production, puis soit rejoue image par image sur une horloge synthétique
  (pas de 50 ms, x8 ; journal score / minute / ralenti / mi-temps / fin + empreinte FNV du DOM complet à chaque image),
  soit mesure la fluidité en temps réel ; `run-bench.mjs` le lance dans un Chrome headless non bridé (le pane du
  navigateur intégré, caché, tombait à 10 images/s). Pour le réutiliser : `vite build --outDir <dossier>`, copier les
  traces et `harness-prod.js` (renommé `harness.js`) dans `<dossier>/__fx/`, servir le dossier, puis
  `node run-bench.mjs <port> <trace> log|fps|shot [secondes|image] [ralentissement CPU]`.

## Mesures (09/11/2026, builds de production avant = `85f9ea6`, après = arbre de travail)

| Trace | Images | Événements (identiques avant/après) | Empreinte DOM avant = après | Journal avant = après |
|---|---|---|---|---|
| `sans-but` | 14 459 | mi-temps image 7 049, fin 0-0 à 90+4' | `1813302683` | oui (`865953917`) |
| `buts-nombreux` | 18 264 | 6 buts (25', 26', 39', 45+4', 64', 75'), 6 ralentis, mi-temps image 9 544, fin 3-3 à 90+6' | `2014265515` | oui (`3535817494`) |
| `trois-buts-exterieur` | 16 577 | 3 buts (30', 48', 77'), 3 ralentis, mi-temps image 7 700, fin 0-3 à 90+7' | `1681800777` | oui (`1478679162`) |

Fluidité, `buts-nombreux`, x8, Chrome headless 1024×768, 3 passes alternées de 15 s : durée d'image médiane **16,7 ms
avant comme après** (p95 16,8 ms) ; temps de script par image **2,87 → 1,89 ms** (− 34 %), temps total du moteur de rendu
par image 6,71 → 5,78 ms (− 14 %) ; 247 nœuds SVG des deux côtés. Mesure faite pendant la suite Python (machine chargée) :
les écarts relatifs comptent, pas les valeurs absolues.

Captures avant/après à deux instants (`buts-nombreux`, image 9 560 : bandeau MI-TEMPS ; image 12 700 : ralenti en
2e période, remplaçants à l'échauffement) : PNG identiques au pixel (SHA-256 égaux).

Mode développement (serveur Vite, Chrome headless) : `?fixture=buts-nombreux&t=49.9&speed=8` → écran de jeu à 5,7 s,
bandeau MI-TEMPS 0,7 s plus tard, score 1-3, x8 actif ; `&t=44&paused=1` → 1-2 à 44', figé.

## Acceptance criteria

- [x] Sur les 3 traces : score, minutes de but, ralentis, mi-temps et fin identiques à l'ancien code (journal et DOM
  complet identiques à chaque image)
- [x] Médiane de durée d'image ≤ celle d'avant (build de production, x8) : 16,7 ms = 16,7 ms ; travail par image en baisse
- [x] Capture avant/après identique (2 instants, au pixel)
- [x] `npm run build` OK
- [x] `npm run lint` : 0 erreur, 5 avertissements (les 5 d'avant, aucun dans les fichiers du ticket)
- [x] Suite Python complète : 2 611 passés, 14 désélectionnés (55 min 10 s, machine chargée par les rejeux) ; un de plus que
  l'attendu (2 610) : `test_xg_calibration_splits_goals_minus_xg_into_block_execution_and_keeper`, ajouté dans l'arbre de
  travail par le ticket `v2-realisme/06c` en cours, hors de ce ticket

## Durée

Estimée 120 min (analyse 15, développement 45, tests et mesures 40, intégration 20), confiance moyenne. Réelle (estimée,
non chronométrée) : environ 140 min (analyse 15, développement 40, tests et mesures 65, intégration 20), + 17 %, sous le
seuil de 30 % ; cause : banc de rejeu image par image à construire, et détour par Chrome headless après le bridage du
pane caché. Temps machine hors total : rejeux et mesures ~35 min, suite Python 55 min.

## Points à vérifier à l'écran

- Aucun attendu (captures identiques au pixel) ; un essai réel `/v2` avec l'API (lancement, attente du calcul, « calcul
  NN' » pendant la lecture) n'est pas couvert par le banc, qui rejoue des matchs finis (limite d'EM-00).

## Comments

- 09/11/2026, passage 1 : expert **APPROVED** ; QC **VALIDÉ** ; clôture **VALIDÉ** (empreinte `5470376b…055d`).
  Anomalies bloquantes : aucune. Réserve facultative A1 (expert) : la médiane de durée d'image est plafonnée à 60 Hz
  (16,7 ms des deux côtés) et ne départage rien ; pour les tickets suivants du chantier, suivre le temps de script par
  image ou mesurer avec ralentissement CPU (`run-bench.mjs`, 5e argument). Les deux revues recommandent un essai réel de
  `/v2` avec l'API (démarrage après le tampon, « calcul NN' », « (en attente…) »), non couvert par le banc.
