# 22b: Coût de mise en page du terrain V2 depuis l'écran en trois zones (EM-04)

**Ouvert le 27/11/2026** (décision du propriétaire, « B », à la clôture du diagnostic `22-regression-de-fluidite.md`).

**Constat (ticket 22, banc `mesures/22-banc.sh` à fenêtre égale, deuxième conteneur, ralenti × 6)** : fluidité 58,0 images/s à `41e573e`, 36,0 à `145a292` (− 38 %). La marche principale est `618c78c` (v2-ecran-match/04, écran en trois zones et responsive) : 51,9 → 40,2 images/s, environ 55 % de la perte ; le reste est diffus (caméra inclinée, 04b, 07, 21a et suite : 2 à 5 images/s chacun, proche du bruit). Au 04, le fil principal est saturé avant comme après ; le script ne coûte pas plus ; chaque mise en page (une par image) coûte deux fois plus (2,6 → 5,5 ms). `contain: strict` sur la zone terrain n'y change rien : le coût est dans la mise en page du SVG.

**What to build:**
1. **Mécanisme** : sondes dans des worktrees jetables, une variable à la fois, à partir de `618c78c` puis de l'état courant : taille de rendu du terrain (le 04 l'a agrandi), dimensionnement `w-full h-full` du `<svg>`, textes SVG (numéros, noms), éléments ajoutés au terrain par le 04 ; compteurs `Performance.getMetrics` (durée et nombre de mises en page) en plus des images par seconde.
2. **Correction** ciblée du coût, sans changer ce qui est affiché ; si le coût est inhérent à un choix d'affichage validé, proposition chiffrée au propriétaire.
3. **Mesure finale** à fenêtre égale, passages alternés avec `41e573e` sur la même machine.

**Points de vigilance (leçons du 22)** :
- Vérifier que la page s'anime pendant la fenêtre de mesure (mutations du terrain), pour chaque état mesuré.
- Ne comparer que des passages alternés sur une même machine ; noter le processeur ; un état au plafond (60 images/s) ne prouve rien.
- Trace figée : régénérer une fois (`02b2-fixture-fps.py`), noter son empreinte (`mesures/22-trace-figee.json` pour la série du 22).
- Port du serveur libre avant chaque mesure (`22-banc.sh` le vérifie).
- Réserves du 22 (acceptées par le propriétaire) : au moins 3 passages alternés par état (A1) ; archiver dans le jsonl les compteurs `getMetrics` et le contrôle d'animation de chaque état mesuré (A2) ; critère ≥ 90 % de la base repris ici (A3).

**Blocked by:** aucun.

**Bloque :** aucun.

**Estimation** (27/11/2026) : analyse (sondes) 45 min, développement 30 min, tests et mesures 45 min, intégration 30 min ; total 2 h 30 ; confiance faible (mécanisme inconnu, deux hypothèses déjà écartées au 22). Au-delà du seuil de 2 h : découpage possible en « mécanisme » et « correction » si les sondes ne concluent pas en 45 min. Temps machine à part : environ 6 états × 3 passages × 1 min 40, plus suite complète.

**Status:** livré (27/11/2026), validé expert + QC (critère de fluidité non tenu, 76 % de `443e8c9`, réserve A1 acceptée par le propriétaire : suite au ticket `22c`)

## Acceptance criteria

- [x] Mécanisme identifié par sonde, avec la part du coût de mise en page qu'il explique : SVG du terrain en élément flex `w-full h-full` (EM-04), remis en page par l'algorithme flex à chaque image ; 9,2 → 2,6 ms par mise en page en position absolue, temps de mise en page divisé par deux sur 30 s (7,5 → 3,5 s)
- [ ] **Non tenu** (76 %, voir Comments ; décision du propriétaire du 27/11/2026 « B » : correctif livré, suite au ticket `22c`) : fluidité finale ≥ 90 % de celle de `443e8c9` (dernier état d'avant l'EM-04, même travail d'animation par image) sur le même banc et la même machine, en 3 passages alternés ; critère redéfini par le propriétaire le 27/11/2026 (« Ok avec ta recommandation », option A), l'ancien critère (≥ 90 % de `41e573e`) comparant deux charges de travail différentes (voir Comments)
- [x] Affichage inchangé : placement du SVG identique au pixel à 5 tailles d'écran ; captures pleine page identiques hors curseur de la frise (`mesures/22b-captures.json`)
- [x] `npm run build` OK, `npm run lint` 0 erreur (5 avertissements, inchangé), `npm test` 97 passés ; suite complète 3 610 passés, 0 ignoré, 14 désélectionnés (compte attendu) ; V1 inchangée

## Comments

**27/11/2026, implémentation.**
- **Correctif livré** (`ui/src/components/match/MatchScreen.jsx`) : le `<svg>` du terrain passe de `w-full h-full` (élément flex de la zone terrain, centré) à `absolute left-2 top-2 w-[calc(100%-1rem)] h-[calc(100%-1rem)]` : même boîte (zone moins la marge de 0,5 rem), le dessin reste centré par `preserveAspectRatio`. Plus mesuré par le flex, le SVG redevient la racine de sa mise en page à chaque image (trace Chrome : mise en page partielle, 338 objets au lieu de 647, mêmes ~120 objets sales).
- **Sondes** (worktrees jetables, trace Chrome `devtools.timeline` sur 3 s) : objets sales identiques avant et après l'EM-04 (~116 sur ~650) mais 3,1 → 9,2 ms par mise en page ; tailles du SVG et des zones stables d'une image à l'autre (hypothèse d'un redimensionnement écartée) ; `contain: strict` sur la zone terrain sans effet ; tests de survol (`LayoutView::HitTest`, environ 30 % du temps) déclenchés par le mouvement de souris fictif que Chrome rejoue à chaque image, pointeur au centre du terrain (là où le banc a cliqué « Lancer le match ») : déjà présents avant l'EM-04, `pointer-events: none` hors joueurs et bancs sans effet.
- **Relief des joueurs sans masque, essayé puis abandonné** : anneau tracé (evenodd) à la place du masque `v2-relief-ring`. Avec un `d` recalculé à chaque image, plus lent ; avec un anneau fixe déplacé par `transform`, aucun gain mesurable (38,4 contre 39,8 sans lui) ; bords différents jusqu'à 7/255 (anticrénelage simple au lieu de double). Code revenu à l'état du dépôt.
- **Mesure finale** (ralenti × 6, 3 passages alternés, page animée contrôlée à chaque passage : 4 900 à 12 300 mutations du terrain par seconde ; série `22b-4-finale` de `mesures/22-fps-resultats.jsonl`, compteurs Chrome archivés) : `443e8c9` 48,1 (42,6 ; 49,8 ; 51,9) ; `41e573e` 54,4 ; `145a292` 29,3 (32,0 ; 31,4 ; 24,5) ; **correctif 36,7 (39,3 ; 35,1 ; 35,7)**, soit + 25 % sur l'état courant dans cette série (+ 14 % en médiane, le 3ᵉ passage de l'état courant étant aberrant ; + 15 à + 27 % selon les séries 22b-1, 22b-3 et 22b-4), 76 % de `443e8c9` ; images de plus de 50 ms : 43 à 132 par passage avant, 15 à 32 après ; temps de mise en page 7,5 → 3,5 s sur 30 s. Critère de 90 % non tenu.
- **Pourquoi** : l'EM-04 n'est que la marche la plus haute. Les pas classés « dans le bruit » au ticket 22 (05, 06, 07, 21a, HUD, frises, statistiques) s'additionnent à environ 11 images/s, au dessin et à la composition (dessin 2,8 → 5,9 ms, tramage 0,9 → 3,9 ms, envoi au compositeur 0 → 2,2 ms par image entre la base et l'état courant corrigé).
- **Changement de critère** (décision du propriétaire du 27/11/2026, « Ok avec ta recommandation ») : référence `443e8c9` au lieu de `41e573e`, la base n'animant que la moitié des éléments par image (environ 4 900 mutations du terrain par seconde contre 8 000 à 12 000 depuis les 04a et 04b : joueurs à 2 images par seconde avant l'interpolation).
- **Banc** (`mesures/22-fps.js`) : compteurs `Performance.getMetrics` de la fenêtre de mesure et contrôle d'animation (mutations du terrain en 1 s, juste après la fenêtre) archivés avec chaque passage (réserves A1 et A2 du ticket 22).
- **Décision du propriétaire du 27/11/2026** : « B » (correctif livré, critère non tenu en réserve, coût de dessin au ticket neuf `22c-cout-de-dessin-de-l-ecran-de-match.md`).

**27/11/2026, clôture, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. QC : BLOQUÉ (acceptation de l'écart 76 % contre 90 % attestée par le seul texte du ticket ; première capture 1280 × 800 expliquée sans preuve).
- A1 [réserve, expert ; blocage du QC] : critère de fluidité non tenu (76 % de `443e8c9` au lieu de 90 %), suite au 22c.
- A2 [facultatif] : gain écrit « + 15 à + 25 % selon les séries » plutôt qu'un chiffre unique (fait, ici et dans PLAN_V2).
- A3 [facultatif ; point secondaire du QC] : capture 1280 × 800 non reprise (la reprendre modifierait un fichier revu) ; placement du SVG identique à 6 tailles, capture de fin de série 1280 × 801 limitée au curseur de la frise.
- Confirmation du propriétaire, demandée pour la réserve A1 (« tu acceptes de livrer le 22b avec la réserve A1, c'est-à-dire un critère de fluidité à 76 % de `443e8c9` au lieu de 90 %, et la suite au ticket 22c ? ») : « J'accepte ».

**27/11/2026, clôture, QC passages 2 et 3.** Passage 2 : BLOQUÉ (même motif qu'au passage 1 : acceptation du propriétaire attestée par le seul ticket). Passage 3, avec un argument nouveau soumis au QC (ticket support des décisions du propriétaire selon CLAUDE.md et `docs/agents/validation-tickets.md` ; précédent `v2-hauteur-ballon/02b2`, VALIDÉ sur la même forme de preuve) : VALIDÉ. Clôture : VALIDÉ (expert APPROVED_WITH_RESERVATIONS, réserve A1 acceptée, QC VALIDÉ). Décision du propriétaire sur la démarche : « Ok avec ta recommandation » (passage 3, puis ticket de dispositif `expert-dispositif/08`). Incohérence du QC entre le 02b2 et le 22b sur la preuve d'une décision du propriétaire : ticket `expert-dispositif/08`.
- Durée : estimée 2 h 30 (45/30/45/30) ; réelle environ 2 h (40/15/35/30), − 20 % ; registre `docs/agents/suivi-estimations.md`.

