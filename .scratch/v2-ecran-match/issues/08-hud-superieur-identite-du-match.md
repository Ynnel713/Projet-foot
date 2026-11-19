# EM-08 — HUD supérieur : identité du match (V) — 120 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : écussons, noms, score central très visible, minute, période, état.
- **Résultat** : `MatchHud`/`ScoreBlock` aux jetons du design system ; écussons `ClubBadge` à 40 à 48 px ; lignes techniques
  (« transition défensive », « calcul… ») retirées de l'écran principal (hors-jeu : repris par la frise).
- **Composants** : `MatchHud`, `ScoreBlock`, `ClubCrest`. **Critères** : score lisible à 2 m (≥ 56 px à 1366×768) ; minute
  avec temps additionnel (45+2') identique à la logique `clock()` ; score jamais en avance sur la lecture (test sur trace).
- **Tests** : sortie de `clock()` comparée avant/après sur 3 traces ; captures des 6 états.
- **Dépendances** : EM-01, EM-03, EM-04. **Risques** : noms de clubs longs (troncature, tailles).

## Comments

### 19/11/2026 — estimation et décisions avant le code

- **Estimation** (travail effectif) : analyse 15 min, développement 55 min, tests 25 min, intégration et vérifications
  25 min, **total 2 h**, confiance moyenne. Hypothèses : `clock()` et le score révélé sont déplacés ou lus, jamais
  modifiés ; commandes de vitesse inchangées (EM-09) ; pas de bouton « Stats » (EM-14). Temps machine à part : suite
  complète (environ 12 min). Validée par le propriétaire le 19/11/2026.
- **Constantes validées par le propriétaire (19/11/2026)** : score Barlow Condensed 700 à 56 px (36 px sous 960 px de
  large ou 500 px de haut) ; écussons 44 px (32 px) ; noms de club 20 px (16 px), majuscules, espacement +0,04 em,
  tronqués par « … » ; minute Barlow Condensed 600 à 24 px (18 px) ; badge d'état « EN DIRECT » (`live`), « MI-TEMPS »,
  « TERMINÉ » (`gold`) ; HUD d'environ 88 px sur bureau.
- **Décisions du propriétaire (19/11/2026)** : la ligne de hors-jeu reste dans le HUD jusqu'à EM-12 (frise) ; quand la
  lecture a rattrapé le calcul, le badge affiche « CHARGEMENT… » en gris à la place de la mention « calcul … ».
- **Critères d'acceptation** : score ≥ 56 px en 1366×768 (mesuré au navigateur) ; `clock()` inchangé (mêmes libellés
  avant/après sur 3 traces) ; score jamais en avance sur la lecture (test aux minutes de but) ; aucun débordement
  horizontal en 844×390 avec deux noms longs ; `npm test`, lint 0 erreur, build OK ; suite Python inchangée ; captures
  des 6 états (1re période, temps additionnel, mi-temps, 2e période, chargement, fin).

### 19/11/2026 — implémentation

- **Code** : `components/match/MatchHud.jsx` (HUD : retour, identité, minute, période, badge, hors-jeu, commandes de vitesse
  inchangées), `ScoreBlock.jsx` (écusson, nom, score, nom, écusson), `ClubCrest.jsx` (`ClubBadge` cerclé de la couleur
  d'équipe, initiales sur `--team-*` en repli) ; `utils/matchClock.js` (`clock()` et `halfStart()` déplacés sans
  modification depuis `trace.js`, qui les ré-exporte) ; `utils/matchHud.js` (`revealedScore`, logique du score déplacée
  telle quelle depuis `MatchScreen.jsx`, et `matchBadge`). `MatchScreen.jsx` : HUD remplacé par `MatchHud` ; ligne de
  situation tactique et mention « calcul … » retirées ; colonne de grille bornée (`minmax(0,1fr)`) : sans elle, le HUD
  prenait la largeur de deux noms longs et poussait le bouton lecture hors de l'écran en 844×390 (+ 32 px).
- **Tests** : `utils/matchHud.test.js` (4 tests : libellés de `clock()` dont 45+1', 90+4' et 2e période inconnue en
  direct ; un but compte à partir de sa minute exacte, jamais avant ; ordre du badge), ajouté au script `npm test`.
- **Mesures** (3 traces réelles enregistrées par `scripts/record_v2_trace.py` : `buts-nombreux` graine 1, `sans-but`
  graine 11, `trois-buts-exterieur` graine 12) :
  - `clock()` avant (HEAD) / après sur chaque image et chaque image + 0,25 min : 23 280, 24 000 et 24 000 instants,
    **0 différence** ;
  - navigateur (Playwright) : score **56 px** en 1366×768 et 1920×1080, 36 px en 844×390 ; HUD 89 px de haut sur
    bureau, 69 px en 844×390 ; débordement horizontal 0 dans les 6 états ;
  - 6 états capturés en 1366×768 : 1re période (23', EN DIRECT), temps additionnel (45+1' (+1)), mi-temps (MI-TEMPS),
    2e période (66'), chargement (trace tronquée à 32', CHARGEMENT…), fin (90+6', TERMINÉ, 1-0) ;
  - noms longs (« Borussia Mönchengladbach », « Wolverhampton Wanderers FC ») en 844×390, 960×600 et 1366×768 :
    tronqués par « … » sous 1366 px, entiers à 1366 px, HUD dans l'écran (bouton lecture à 834 px sur 844) ;
  - score révélé sur la trace `buts-nombreux` (but domicile à 67,58') : 0-0 à t = 67,5, 1-0 à t = 67,6.
- **Vérifications** : `npm test` 37 passés, 0 échec ; `npm run lint` 0 erreur, 5 avertissements (attendu) ;
  `npm run build` OK ; suite Python 3 437 passés, 0 ignoré, 14 désélectionnés (750 s). Moteur non touché : déterminisme
  V2 inchangé par construction (aucun fichier `v2engine/`).
- **À vérifier à l'écran** : lisibilité du score à 2 m ; rendu des initiales en repli pour un club sans logo.
- **Durée** : estimée 2 h ; réelle environ 30 min de travail effectif (analyse 10, développement 10, tests et captures
  10), hors temps machine (enregistrement des traces 2 min, suite complète 12,5 min) et hors clôture. Écart − 75 % :
  composants simples, logique existante seulement déplacée, banc de rejeu et traces d'EM-00 réutilisés ; seul imprévu,
  le débordement de grille en 844×390.

### 19/11/2026 — clôture (passage 1)

- Expert : **APPROVED** (empreinte `8ec07ccb`). Réserves facultatives, non bloquantes : A1, initiales blanches de
  l'écusson de repli peu lisibles sur un maillot clair (passer `--team-*-ink`) ; A2, pendant un ralenti le score suit
  l'instant le plus avancé déjà vu et la minute l'instant rejoué (comportement antérieur, US-29, à garder en tête pour
  EM-12).
- Contrôle qualité : **VALIDÉ**. Décision de clôture : **VALIDÉ** (expert APPROVED, QC VALIDÉ).

