# EM-22 — Regagner la fluidité de l'écran V2

**Status:** livré (23/11/2026), validé expert + QC (créé le 23/11/2026 à la clôture de `v2-hauteur-ballon/02b`, décision du propriétaire : « Accepter, ticket de suite »)

**Constat mesuré** (`.scratch/v2-hauteur-ballon/mesures/02b-fluidite.txt`) : images par seconde de l'écran de match V2, même trace (Auxerre – Monaco, graine 20261123), lecture ×1, processeur ralenti 6 fois, Chromium sans affichage de la session cloud, API simulée, build de production :

| Version | Images par seconde |
|---|---|
| `41e573e` (base du ticket `v2-hauteur-ballon/01`) | 59,5 |
| `f42dc68` (ticket `v2-hauteur-ballon/01`) | 58,5 |
| `443e8c9` (interpolation courbe, `v2-correctifs-ecran/04b`) | 59,3 |
| `618c78c` (EM-04, écran en trois zones) | 55,4 |
| `1a9a38d` (EM-05) / `00dca4c` (EM-06) | 56,0 / 55,6 |
| `c057086` (EM-07, marqueurs en relief) | 52,6 |
| `6de4140` (EM-21a, ballon qui roule, traînée) | 46,9 |
| `b43d942` (juste avant `v2-hauteur-ballon/02b`) | 47,8 |
| `v2-hauteur-ballon/02b` | 49,0 |

La baisse (− 18 % depuis la base) vient surtout de l'EM-21a : `BallMarker` reconstruit à chaque image ses `<defs>` (motif de panneaux `pattern`, dégradés), et de l'EM-04 et de l'EM-07 (structure de l'écran, relief des marqueurs).

**What to build:** retrouver au moins 54 images par seconde (base − 10 %) dans les mêmes conditions de mesure, sans changer ce que voit l'utilisateur : profilage (Chrome DevTools sur la trace), puis par exemple `<defs>` du ballon posés une fois et déplacés par `transform`, filtres du relief des marqueurs remplacés par des dégradés, mémoïsation des zones qui ne changent pas à chaque image.

**Mesure :** script de mesure du 02b (dans le dossier de mesures du chantier `v2-hauteur-ballon`, à reprendre dans `scripts/` si ce ticket le généralise) ; limite : Chromium sans affichage, pas un navigateur visible (choix du propriétaire du 23/11/2026).

**Blocked by:** aucun.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et profilage | 30 min |
| Développement | 40 min |
| Tests | 15 min |
| Intégration et vérifications (mesure, captures) | 25 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : faible (gain de chaque correctif inconnu d'avance). Temps machine, non compté : mesures de fluidité (environ 3 min par série), suite complète (environ 17 min). Aucune constante produit.

**Critères chiffrés** (posés avant le code) : ≥ 54 images par seconde dans les conditions du 02b (même trace, ×1, processeur ralenti 6 fois, 30 s, trois lectures alternées avec la version d'avant) ; captures identiques (au sol, ballon en l'air, ballon rapide avec traînée) ; `npm test`, `npm run build`, `npm run lint` (0 erreur) ; suite complète au compte attendu.

## Acceptance criteria

- [x] Images par seconde ≥ 54, même trace, ×1, processeur ralenti 6 fois, 30 s, trois lectures alternées avec la version d'avant (moyenne 54,0, au ras : une lecture sur trois à 53,6)
- [x] Captures avant / après identiques à l'œil (ballon, motif, traînée, marqueurs, hauteur du ballon) : identiques au pixel près
- [x] `npm run build`, `npm run lint` (0 erreur), `npm test`

## Résultats (23/11/2026)

- **Cause trouvée** (trace Chromium, suivi des invalidations, détail `.scratch/v2-ecran-match/mesures/22-mesures.txt`) : depuis l'EM-04, le dessin du terrain a une hauteur en pourcentage (`h-full`). Chromium ne peut alors pas isoler sa mise en page : à chaque image, elle repart de la racine du document et tout le SVG est invalidé (environ 100 groupes, 60 rectangles, 60 textes par mise en page, au lieu des seuls éléments qui bougent). Mise en page : 1,9 ms par image avant l'EM-04, 4,4 après ; terrain masqué : 0,1 ms.
- **Correctif** (`ui/src/components/match/MatchScreen.jsx`, `V2Pitch.jsx`) : la case du terrain est mesurée par un `ResizeObserver` (relue seulement quand elle change de taille) et le dessin reçoit sa largeur et sa hauteur en pixels (prop `size` de `V2Pitch`) ; sans taille connue (premier rendu, autres écrans), comportement d'avant. Mise en page 4,4 → 2,2 ms par image.
- **Pistes mesurées et écartées** : `contain: strict` sur la case (sans effet) ; unités de conteneur `cqw`/`cqh` (pire : styles 2,6 ms) ; couronne du relief des marqueurs tracée sans masque (51 à 53 contre 53 à 56 images par seconde) ; ballon sans `<pattern>` (panneaux découpés par `clipPath`, traînée à dégradé fixe : 50 à 53 contre 55 à 56) ; `contain: layout paint` sur le bandeau, le bas et les compositions (sans gain). Le motif du ballon (EM-21a) et le relief (EM-07) restent donc tels quels.
- **Mesure finale** (`22-fluidite.js`, 30 s, trois lectures alternées) : avant 48,7 images par seconde (49,9 ; 50,1 ; 46,2), après **54,0** (54,3 ; 54,2 ; 53,6), soit + 11 % ; mise en page 4,2 à 4,7 → 2,2 ms par image. Objectif tenu au ras (une lecture sur trois sous 54). Limite : Chromium sans affichage, pas un navigateur visible.
- **Rendu identique** (`22-captures-comparees.js`, rejeu de développement, avant = `2e8f447`) : 1280×800 et 375×812, corner au départ, au sommet (5,5 m) et ballon à 26 m/s avec traînée : 0 pixel différent sur les 6 captures, boîte du terrain identique. Redimensionnement 1280×800 → 1000×700 → 375×812 → 1600×900 : le terrain suit sa case (moins 16 px de marge).
- Tests : `npm test` 85 passés ; `npm run build` OK ; `npm run lint` 0 erreur, 5 avertissements (inchangés). Aucun test ajouté : le correctif est une taille de mise en page, vérifiée par les captures et la mesure (pas de banc DOM dans `npm test`).
- Suite complète : 3 619 passés, 0 ignoré, 14 désélectionnés (compte attendu, inchangé : aucun fichier Python touché).
- Durée réelle : environ 1 h 20 (analyse et profilage 40, développement 15, tests 5, intégration et vérifications 20), − 27 % : cause trouvée par la trace Chromium dès le premier tiers du ticket, correctif de 31 lignes ; deux pistes essayées puis écartées après mesure comprises. À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : environ 25 min de mesures et de constructions, suite complète (16 min).

## Comments

- 23/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte `41ff2178…`). Réserve A1 : seuil de 54 images par seconde atteint sans marge (moyenne 54,03, une lecture à 53,6, erreur type environ 0,21 ; gain de + 11 % établi). Facultatifs : A2 (taille négative possible si la case est plus petite que ses marges : `Math.max(0, …)`), A3 (`className="w-full h-full"` resté sur le SVG, remplacé par le style en ligne). Propriétaire : « J'accepte A1 ». QC VALIDÉ (non bloquant : marge de 0,03 image par seconde, Chromium sans affichage). Clôture VALIDÉ. À surveiller (expert) : refaire `22-fluidite.js` à chaque ticket d'écran qui ajoute des éléments au terrain ; prochain levier probable : le calcul React par image (environ 5,3 ms) ou le ballon et sa traînée.
