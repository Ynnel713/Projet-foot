# Design System — Simulafoot

## Product Context
- **Quoi** : simulation de championnat de foot au niveau joueur (compos, buteurs/passeurs, cartons, blessures, classements en direct), avec rendu animé 2D des actions marquantes.
- **Pour qui** : le propriétaire et, à terme, des joueurs qui suivent une saison ou une compétition perso.
- **Espace** : jeux de manager sportif (Football Manager, FIFA Career Mode) plutôt que dashboard SaaS B2B.
- **Type** : web app (PWA React + API FastAPI).
- **Memorable thing** : « un outil de simulation fun et ludique ».

## Aesthetic Direction
- **Direction** : jeu de manager sportif — personnalité et fun portés par les scores, titres et moments d'accroche, jamais par les tableaux de stats.
- **Décoration** : intentionnel — accents ludiques réservés aux écrans d'accroche (résumé de match, accueil), jamais plaqués sur les tableaux denses.
- **Mood** : chaleureux et dynamique sans sacrifier la lisibilité d'un classement de 20 clubs ou d'une feuille de match.
- **Références** : Football Manager, FIFA Career Mode — densité de données + personnalité visuelle, pas un dashboard analytics générique.

## Typography
- **Display/Hero** : Cabinet Grotesk — scores, titres d'écran, nom du produit ; apporte la personnalité "jeu" qu'une sans-serif neutre n'aurait pas.
- **Body** : Plus Jakarta Sans — lisible, chaleureux, pas un Inter de plus.
- **Data/Tables** : DM Sans (`font-variant-numeric: tabular-nums`) — classements, buteurs/passeurs, feuilles de match.
- **Code** : JetBrains Mono — accents techniques rares (ex. identifiants, détails de debug visibles ponctuellement).
- **Loading** : Google Fonts (`Plus+Jakarta+Sans`, `DM+Sans`, `JetBrains+Mono`) + Fontshare (`cabinet-grotesk`).
- **Scale** : 12 / 14 / 16 / 20 / 24 / 32 / 48 / 64 px.

## Color
- **Approche** : balanced — primaire + secondaire, sémantiques dédiées pour la hiérarchie.
- **Primary** : `#1E9E5A` (vert gazon vif) — actions principales, identité produit.
- **Secondary** : `#F5A623` (orange carton) — accents ludiques, badges, CTA secondaires.
- **Neutrals** : `#F7F8FA` → `#E7EAEF` → `#C7CDD6` → `#8A93A3` → `#4B5564` → `#1F2733` → `#0F172A` (lightest → darkest).
- **Semantic** : success `#2BAA5D`, warning `#F5C518`, error `#E63946`, info `#3B82F6`.
- **Dark mode** : fond ardoise profond (`#0F172A`), vert gazon et orange conservés comme accents, textes clairs sur fond sombre — prioritaire sur les écrans de classement, les plus consultés.

## Spacing
- **Base** : 8px.
- **Densité** : confortable — assez d'air pour rester ludique, assez dense pour un classement de 20 clubs.
- **Scale** : 2xs(2) xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48) 3xl(64).

## Layout
- **Approche** : hybrid — grid-disciplined pour classements/calendrier/feuilles de match, creative-editorial pour les écrans d'accroche (accueil, résumé de match).
- **Grid** : 12 colonnes desktop, 4 colonnes tablette, 1 colonne mobile.
- **Max content width** : 1280px.
- **Border radius** : sm:6px, md:10px, lg:16px, full:9999px.

## Motion
- **Approche** : intentionnel — transitions qui marquent un changement d'état (score qui tombe, classement qui bouge), pas de chorégraphie complète. S'appuie sur `framer-motion`, déjà présent dans `ui/`.
- **Easing** : enter(ease-out) exit(ease-in) move(ease-in-out).
- **Duration** : micro(50-100ms) court(150-250ms) moyen(250-400ms) long(400-700ms).

## Decisions Log
| Date | Décision | Rationale |
|------|----------|-----------|
| 2026-10-15 | Création initiale | /design — produit = simulation de championnat au niveau joueur, PWA React ; mémorable = « fun et ludique » ; direction retenue : jeu de manager sportif plutôt que dashboard SaaS, fun réservé aux écrans d'accroche pour ne jamais sacrifier la lisibilité des tableaux de stats. |
