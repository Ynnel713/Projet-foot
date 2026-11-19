# EM-08b — Score aligné sur la ligne médiane (V) — 30 min (élevée)

**Status:** livré (19/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md`. Correction d'EM-08 (livré le 19/11/2026).

- **Problème** (signalé par le propriétaire sur les captures d'EM-08, 19/11/2026) : le score est centré entre le bouton
  « Retour » (étroit) et les commandes de vitesse (larges), pas sur l'écran. Mesure au navigateur : centre du score
  86 px à gauche de la ligne médiane du terrain en 1366×768, 1920×1080, 1100×700 et 844×390.
- **Résultat** : HUD en trois colonnes, les deux colonnes latérales de même largeur (celle du plus large de leurs
  contenus), de sorte que score, minute et badge soient centrés sur l'écran, donc sur la ligne médiane du terrain
  (compositions symétriques au-dessus de 960 px, terrain pleine largeur en dessous).
- **Composants** : `MatchHud`.
- **Critères d'acceptation** : écart entre le centre du score et le centre du terrain ≤ 2 px aux 4 tailles ci-dessus ;
  minute et badge centrés de même ; aucun débordement horizontal, noms longs compris (844×390, 960×600, 1366×768) ;
  `npm test`, lint 0 erreur, build OK ; suite Python inchangée.
- **Estimation** : analyse 5 min, développement 10 min, tests 10 min, intégration 5 min, total 30 min, confiance élevée ;
  hypothèse : seule la mise en page du HUD change. Aucune constante nouvelle.
- **Dépendances** : EM-08. **Risque** : en 844×390, colonne centrale plus étroite (noms coupés plus tôt) tant qu'EM-09
  n'a pas resserré les commandes.

## Comments

### 19/11/2026 — implémentation

- **Code** : `MatchHud.jsx` passe d'une rangée flexible à une grille de trois colonnes ; les deux colonnes latérales ont
  la largeur du plus large de leurs contenus (bouton « Retour » à gauche, commandes à droite), relevée par un
  `ResizeObserver` (premier relevé avant l'affichage, puis à chaque changement de taille, apparition du bouton RALENTI
  comprise). Contenu du HUD inchangé.
- **Mesures** (Playwright, trace `buts-nombreux`, centres horizontaux en px, avant → après) :
  - centre du score : 1366×768 597 → **683** (terrain 683) ; 1920×1080 874 → **960** (960) ; 1100×700 464 → **550**
    (550) ; 844×390 336 → **422** (422) ; écart 86 px → **0 px** ; minute et badge centrés de même ;
  - pendant le ralenti d'un but (bouton RALENTI affiché, 1366×768) : score 683, terrain 683, HUD dans l'écran ;
  - noms longs : débordement horizontal 0 en 844×390, 960×600 et 1366×768 ; en 844×390, colonne centrale de 350 px
    (247 à 597), noms coupés par « … », bouton lecture à 834 px sur 844.
- **Vérifications** : `npm test` 37 passés, 0 échec ; `npm run lint` 0 erreur, 5 avertissements (attendu ; un 6e,
  « accès à une ref pendant le rendu », apparu en cours de route, corrigé en renvoyant les refs séparément) ; build OK.
- **À vérifier à l'écran** : rien de plus qu'EM-08.
- **Durée** : estimée 30 min ; réelle environ 25 min (analyse 5, développement 10, tests 10), hors temps machine (suite
  complète). Écart sous 30 %.

### 19/11/2026 — clôture (passage 1)

- Expert : **APPROVED** (empreinte `6a5ac5bf`). Réserves facultatives : A1, `Math.ceil` sans effet sur `offsetWidth`
  (déjà entier ; décalage possible sous 1 px, sous la tolérance) ; A2, colonne centrale de 350 px en 844×390, à revoir
  avec EM-09.
- Contrôle qualité : **VALIDÉ**. Décision de clôture : **VALIDÉ** (expert APPROVED, QC VALIDÉ).

