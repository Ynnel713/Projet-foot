# Design System — Simulafoot

Source de vérité du langage visuel de l'interface (`ui/`). Les valeurs vivent dans `ui/src/index.css` (`@theme`) ; ce document dit **quand** les utiliser. Refonte UX/UI validée par le propriétaire le 01/11/2026 ; chantier `.scratch/refonte-ui/`.

## Product Context
- **Quoi** : simulation de compétitions de football au niveau joueur (compos, buteurs/passeurs, cartons, blessures, classements), avec rendu animé 2D des actions marquantes.
- **Pour qui** : le propriétaire et, à terme, des joueurs qui suivent une saison ou une compétition perso, souvent pendant de longues sessions.
- **Espace** : jeux de management sportif (Football Manager) et applis de suivi (Sofascore, FotMob), pas un dashboard SaaS.
- **Type** : PWA React (mobile d'abord) + API FastAPI.

## Direction : « la loge de presse, de nuit »
- Interface sombre, calme, en retrait : la lumière va aux **données** et aux **clubs**, jamais à la décoration.
- Dense mais aérée : on lit un classement de 20 clubs d'un coup d'œil, sans tableau austère.
- Le caractère « foot » vient de trois sources : les **couleurs des clubs** (bandeau d'en-tête, champ `color` de l'API), une **typographie de retransmission** pour scores et titres, et le **contenu** (forme, zones, moments forts).
- Le spectacle est réservé aux moments qui le méritent (fin de saison, finale, résumé de journée), jamais aux tableaux.
- À proscrire : image ou dégradé de fond, halos et lueurs, ombres portées, accumulation de cartes sans logique, couleurs vives décoratives.

## Typography
- **Display** : Barlow Condensed (600/700) — scores, titres d'écran, gros chiffres (note, statistiques). Classe `font-display`.
- **Texte et tableaux** : IBM Plex Sans (400/500/600/700) — tout le reste. Chiffres alignés (`tabular-nums`) par défaut sur toute l'app.
- **Chargement** : Google Fonts (`ui/src/index.css`).
- **Échelle** : 11 (`text-caption`) / 13 (`text-data`, tableaux) / 14 / 16 / 18 / 24 / 32 / 48 px.
- **Plancher** : rien sous 11 px. Pas de taille arbitraire `text-[…px]` dans le nouveau code : utiliser l'échelle.

## Color
Une couleur = un sens, sans exception.

| Rôle | Token | Valeur | Usage |
|---|---|---|---|
| Fond | `bg` | `#0B0F14` | Fond uni de l'app |
| Surfaces | `surface`, `surface-2`, `surface-3` | `#121821`, `#18202B`, `#1F2834` | Panneaux, lignes survolées, éléments imbriqués (du plus bas au plus haut) |
| Filet | `line` | `#232D3A` | Séparateurs de lignes et de panneaux |
| Action (aplat) | `accent` | `#2F6FE4` | Bouton principal, élément actif ; texte blanc dessus (4,65:1) |
| Action (texte) | `link` | `#6EA1FF` | Liens, icônes et libellés d'action sur fond sombre |
| Victoire / bon | `win` | `#3FB950` | Résultat gagné, différence positive, note ou attribut > 70 |
| Nul / neutre | `draw` | `#8B98A9` | Résultat nul, différence nulle |
| Défaite / faible | `loss` | `#F85149` | Résultat perdu, différence négative, note < 50, erreurs |
| Note moyenne | `tier-avg` | `#E0B13A` | Note ou attribut de 50 à 70 (texte) |
| Aplats de note | `tier-good-fill`, `tier-avg-fill`, `tier-poor-fill` | `#1E8E3E`, `#C99A12`, `#C0392B` | Badge de note sous texte blanc (seuils : `utils/fmTier.js`) |
| Or | `gold` | `#E3B341` | **Uniquement** trophées, champion, club suivi |
| Gazon | `pitch` | `#0D3320` | Petits terrains d'illustration |

- **Neutres** : une seule palette (`gray-50` → `gray-950`, `slate` en alias). Texte principal `gray-100` (16:1 sur le fond), secondaire `gray-400` (7,9:1), discret `gray-500` (5,5:1). `gray-600` et plus foncés : icônes et filets seulement, jamais du texte utile.
- **Contraste** : tout texte utile ≥ 4,5:1 sur sa surface (WCAG AA). **Exception connue** : le texte blanc des badges de note sur les aplats conservés tels quels au lot 1 (4,21:1 sur `tier-good-fill`, 2,59:1 sur `tier-avg-fill`) ; correction (texte sombre sur l'aplat moyen ou aplats ajustés) à soumettre au propriétaire au lot 5, ces valeurs étant des constantes produit.
- **Live et animation** (désactivés en V1) : tokens `live*` et `ev-*` inchangés.
- **Pas de mode clair** : l'app est sombre par choix produit.

## Spacing
- **Base** : 4 px. Échelle Tailwind standard (1 = 4 px).
- **Densité** : lignes de tableau 32 px sur bureau, 36 px sur mobile (cible tactile).
- **Gouttière mobile** : 16 px.

## Layout
- **Mobile d'abord** : chaque écran est conçu à 375 px puis élargi. Jamais de défilement horizontal de page ; un tableau large défile dans son conteneur avec la colonne Club figée.
- **Navigation** : un espace par compétition (Journée · Classement · Stats · Clubs), barre d'onglets en bas sur mobile, colonne à gauche sur bureau ; le titre de la compétition et la progression restent visibles.
- **Action principale** : toujours au même endroit, en bas de l'écran, dans tous les formats de compétition.
- **Largeur max du contenu** : 1280 px.
- **Rayons** : 8 px (contrôles, badges), 12 px (panneaux). Pas d'autre valeur dans le nouveau code.
- **Listes denses** : lignes séparées par un filet, pas de cartes.

## Motion
- Uniquement pour marquer un changement d'état (score qui tombe, rang qui change), 150 à 250 ms, `ease-out`. S'appuie sur `framer-motion`.
- `prefers-reduced-motion` toujours respecté.

## Decisions Log
| Date | Décision | Rationale |
|------|----------|-----------|
| 2026-10-15 | Création initiale | /design — palette claire vert gazon/orange, Cabinet Grotesk + Plus Jakarta Sans. Jamais appliquée : l'UI est restée sur Inter, bleu marine et or. |
| 2026-11-01 | Refonte (lot 1) : direction « la loge de presse, de nuit » | Audit UX/UI du 01/11/2026, validé par le propriétaire. Demande : sombre, sobre, premium, dense sans surcharge. Fond d'écran du stade retiré (bruit derrière le contenu), une couleur = un sens (l'or désignait 4 choses, 3 verts coexistaient), Barlow Condensed + IBM Plex Sans (personnalité « retransmission » sans effet jeu vidéo, chiffres alignés), plancher de 11 px (77 occurrences sous 12 px dont 8-9 px), bleu d'action assombri pour passer le contraste AA avec du texte blanc. |
