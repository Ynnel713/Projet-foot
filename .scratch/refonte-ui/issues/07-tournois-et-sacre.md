# 07: Tournois et moments forts (arbre des phases finales, écran de sacre)

**What to build:** lot 6 de la refonte UX/UI (« la loge de presse, de nuit »). Deux choses : (1) un **arbre des phases finales** lisible d'un coup d'œil (aujourd'hui : le tour en cours en cartes, les tours précédents empilés dessous) ; (2) un **écran de sacre** quand une compétition a son champion (aujourd'hui : une simple bannière « 🏆 Champion : X » dans `Bracket.jsx` et `Simulation.jsx`). `docs/DESIGN.md` : « le spectacle est réservé aux moments qui le méritent (fin de saison, finale, résumé de journée), jamais aux tableaux ».

**Status:** livré (04/11/2026), validé expert + QC

**Décisions du propriétaire (03/11/2026) :** « Oui c'est bon » → (a) à (e) tels que recommandés.

## Constat (code lu)
- `Bracket.jsx` : titre du tour courant, cartes `TieCard` (manche unique = ligne de match, aller-retour = cumul + manches), « tours précédents » empilés sous le tour courant ; aucune vue d'ensemble, aucune liaison visuelle entre un tour et le suivant. Données disponibles (`GET /bracket`) : tous les tours, leurs confrontations, vainqueur, manches, tirs au but, `current_legs`, `champion`, `is_complete` : **rien à changer côté API**.
- Sacre : bannière `bg-gold/10 … 🏆 Champion : X` dupliquée dans `Bracket.jsx` et `Simulation.jsx` (championnat). Pas de parcours, pas de finale, pas de buteur.
- `framer-motion` est déjà une dépendance (`LeagueCard`, `PitchView`) ; `prefers-reduced-motion` doit être respecté (`DESIGN.md`, section Motion). Or réservé à « trophées, champion, club suivi ».
- Les classements buteurs / passeurs existent (`GET /leaderboards`, écran Stats) ; classement final du championnat via `GET /standings`.

## Décisions de conception proposées
- **Arbre, bureau (≥ 1024 px)** : une colonne par tour (Barrages · 1/8e · 1/4 · 1/2 · Finale), cartes compactes (2 lignes : club + score cumulé, vainqueur en blanc gras, perdant en gris, exempt marqué), traits de liaison discrets (`line`) vers le tour suivant. L'arbre défile dans son conteneur (jamais la page) ; le tour courant est repéré (en-tête de colonne en `link`). À droite, le **détail du tour sélectionné** (par défaut le tour courant) avec les `TieCard` actuelles (manches, feuille de match au clic sur le score, tirs au but) ; cliquer l'en-tête d'une colonne sélectionne le tour.
- **Arbre, mobile (< 1024 px)** : pas d'arbre dessiné (illisible à 375 px) mais un **sélecteur de tours** (puces : Barrages · 1/8e · 1/4 · 1/2 · Finale, tour courant présélectionné) au-dessus de la liste des `TieCard` du tour choisi.
- **Écran de sacre** (composant unique `ChampionPanel`, utilisé par le championnat et par les tableaux) : coupe (icône `Trophy`, `gold`), écusson 64 px, nom du champion en `text-title`, intitulé « Champion · <compétition> » ; puis **le parcours** : une ligne par tour (adversaire, score, « tab » le cas échéant) pour un tableau, ou **le podium** (3 premiers, points) pour un championnat ; puis **les moments forts** : meilleur buteur et meilleur passeur de la compétition avec leur club (liens vers leurs fiches) et un lien « Voir les stats ». Une seule animation d'entrée (fondu + léger glissement, 250 ms, `ease-out`), supprimée si `prefers-reduced-motion`. Pas de confettis, pas d'ombre, pas de dégradé. L'or ne sert que pour la coupe et le nom du champion.
- **Placement** : en haut de la page Phase finale (au-dessus de l'arbre) et en haut de la page Journée du championnat, à la place de la bannière actuelle ; la barre d'action reste absente quand c'est terminé.
- Les libellés des tours existants sont conservés (`label` imposé du moteur, sinon déduit : Finale, 1/2 finale, 1/Ne de finale).

## Points soumis au propriétaire (recommandation en premier)
- (a) **Arbre dessiné sur bureau, sélecteur de tours sur mobile** — recommandé : seul l'écran large a la place pour un vrai arbre ; sur téléphone, un tour à la fois reste lisible et tactile. Alternative : arbre dessiné aussi sur mobile avec défilement horizontal (fidèle mais peu lisible, pas de cibles de 44 px).
- (b) **Détail du tour à droite de l'arbre** (bureau) plutôt que cartes dépliées dans l'arbre — recommandé : réutilise les cartes validées au lot 3 / ticket 05 (manches, feuille de match, boutons) sans les redessiner.
- (c) **Contenu du sacre** : champion + parcours (ou podium en championnat) + meilleur buteur et meilleur passeur — recommandé : tout existe déjà dans l'API, rien à inventer. Alternative plus riche (plus large victoire, match le plus prolifique…) : demande des calculs sur tous les matchs, à proposer plus tard.
- (d) **Un seul composant de sacre pour championnat et tableaux** — recommandé : même moment, même rendu, parcours remplacé par le podium en championnat.
- (e) **Animation d'entrée unique et sobre** (250 ms, désactivée si l'utilisateur réduit les animations) — recommandé, conforme à la section Motion de `DESIGN.md`. Alternative : aucune animation.

## Hors périmètre
- Accueil / « Reprendre » (lot 7), phase de ligue et poules (lot 3), feuille de match (lot 4), club et joueur (lot 5).
- Nouvelles statistiques calculées (voir c), partage / export du tableau, mode V2, moteur, API, fichiers protégés.

## Critères d'acceptation
- [x] Bureau 1440 × 900 : arbre à une colonne par tour, cartes compactes (club, score cumulé, vainqueur en blanc gras), traits de liaison, tour courant repéré ; la page ne défile pas, l'arbre défile dans son conteneur quand il est plus grand que l'espace (avec le sacre affiché, la page entière défile sur écran bas)
- [x] Bureau : clic sur l'en-tête d'une colonne ou sur une confrontation → détail du tour à droite (manches, score cliquable vers la feuille de match, tirs au but) ; tour courant présélectionné
- [x] Mobile 375 px : sélecteur de tours (puces ≥ 44 px de haut), liste des confrontations du tour choisi, aucun défilement horizontal de la page, cibles ≥ 44 px, aucun texte sous 11 px
- [x] Ligue des Champions (barrages puis 8es à deux manches, exemptions), Coupe du Monde (manche unique), compétition perso avec exemptions et finale à deux manches : arbre juste (bons qualifiés d'un tour à l'autre, exempts marqués)
- [x] Sacre : `ChampionPanel` affiché dès la fin de la finale (et de la dernière journée en championnat) sans changer d'onglet, avec champion, parcours (une ligne par tour) ou podium, meilleur buteur et meilleur passeur ; remplace les deux bannières actuelles
- [x] Or uniquement sur la coupe et le nom du champion ; 0 ombre, 0 dégradé, 0 couleur en dur ; animation unique ≤ 250 ms, absente avec `prefers-reduced-motion`
- [x] Barre d'action absente quand la compétition est terminée ; aucun bouton « Retour »
- [x] `npm run build` OK ; `npm run lint` : 0 erreur, 5 avertissements au plus
- [x] Parcours vérifiés à l'écran, bureau et mobile : élimination directe perso (avec exemptions, finale à deux manches), Ligue des Champions, championnat (sacre avec podium)
- [x] Aucun fichier Python ni fichier protégé touché (frontend seulement) ; suite Python non requise si aucun `.py` n'est modifié (à confirmer à la clôture)
- [x] Mise à jour de `Plan architecte Simulafoot.md`

## À vérifier avant de coder
- Pas besoin d'architecte (frontend seulement). À confirmer avant de commencer : que `GET /leaderboards` renvoie bien le club du buteur et du passeur (champ `club` de `LeaderboardRow`, oui d'après `api/schemas.py`) et qu'il reste accessible une fois la compétition terminée.

## Comments

**03/11/2026 — implémentation**
- Fichiers (frontend seulement) : `routes/Bracket.jsx` (arbre + détail + sélecteur de tours, sacre), `routes/Simulation.jsx` (sacre du championnat), `components/bracket/BracketTree.jsx` et `ChampionPanel.jsx` (nouveaux), `utils/bracketLabels.js` (libellés de tours et parcours d'un club, sortis de `Bracket.jsx`).
- Choix de réalisation : traits de liaison = petits traits horizontaux entre colonnes (pas de raccords verticaux entre paires : les tours de la Ligue des Champions ne se divisent pas par deux) ; sélection du tour ramenée sur le tour courant après chaque simulation.
- Mesures (API de démonstration port 8001, navigateur masqué donc sans capture) : bureau 1440 × 900, perso Ligue 1 à exemptions et finale à deux manches : 3 colonnes (1/16 : 16 cartes, 1/8 : 8, 1/4 : 4) puis 5 colonnes à la fin, tour courant présélectionné, clic sur l'en-tête → détail du tour, arbre qui défile dans son conteneur (976 px de contenu pour 771 px), page 900/900 sans défilement, police mini 11 px ; sacre : coupe et nom en or (`rgb(227,179,65)` = `gold`), pas d'ombre, parcours en 5 lignes (exempt, 9-0, 5-4, 6-3, 6-1), meilleur buteur et passeur avec liens vers leurs fiches ; mobile 375 : arbre masqué, 5 puces de 44 px, 8 confrontations du 1/8e après sélection, aucun défilement horizontal, « Voir les stats » 44 px ; championnat terminé : podium à 3 lignes à la place du parcours, ancienne bannière absente ; Ligue des Champions : colonnes Barrages (8) et 8es de finale (8, tour courant).
**03/11/2026 — premier passage de revue et corrections**
- Expert (passage 1) : APPROVED_WITH_RESERVATIONS (A1 traits de liaison non raccordés, A2 podium brièvement absent si le classement charge après le statut). Contrôle qualité (passage 1) : REFUSÉ : avec le sacre affiché sur bureau à faible hauteur, `lg:overflow-hidden` supprimait le défilement de la page et écrasait l'arbre. Corrigé : le conteneur défile toujours (`overflow-y-auto`), la zone arbre + détail garde 24 rem minimum sur bureau (`lg:min-h-[24rem]`) ; podium conditionné à `standings.length > 0` (A2). Mesuré à 1440 × 700 avec le sacre : arbre 384 px (contenu 976 px, il défile), détail 384 px, conteneur 652 px pour 714 px de contenu, donc la page défile et rien n'est écrasé.
- Coupe du Monde rejouée : après les poules, colonnes « 1/8e de finale » (8) et « 1/4e de finale » (4), « Simuler ce tour », page 700/700.
- Non vérifié : rendu visuel à l'œil (aucune capture) ; compétition à poules classiques non rejouée (mêmes composants) ; effet de l'animation d'entrée (250 ms, `useReducedMotion`) non observé ; raccords visuels des traits de liaison.
- Aucun fichier Python touché : suite Python non relancée pour ce ticket (dernière complète : 2 324 passés, 0 échec, au lot 5). Build OK ; lint 0 erreur, 5 avertissements.

**04/11/2026 — clôture**
- Expert (passage 2) : APPROVED_WITH_RESERVATIONS ; QC (passage 2) : VALIDÉ. Réserves acceptées par le propriétaire (« Oui ») : A1 traits de liaison non raccordés (décoratifs), A2 rendu à l'œil, animation d'entrée et poules classiques non observés à l'écran, à confirmer à sa recette.
