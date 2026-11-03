# 03: Boucle centrale (ligne de match, classement unifié, barre d'action commune)

**What to build:** Lot 3 de la refonte UX/UI (direction validée le 01/11/2026 ; ordre inversé avec le lot 4 le 02/11/2026 ; retours du propriétaire du 02/11/2026 sur la phase de ligue de la Ligue des Champions). Refaire les trois écrans où l'on simule et lit les résultats (Journée d'un championnat, Poules / Phase de ligue, Phase finale) autour de trois composants partagés : une **ligne de match**, un **classement** et une **barre d'action** en bas de l'écran. Les fichiers `MatchRow.jsx`, `Groups.jsx`, `Bracket.jsx`, `Simulation.jsx` sont propres depuis le commit `819e7e9` (travail d'animation commité à part) ; le lot 4 est commité (`c5468e6`).

**Status:** livré (03/11/2026), validé expert + QC

**Retours du propriétaire (02/11/2026, captures de la phase de ligue)**
1. Classement : police un peu plus petite, colonnes V / N / D retirées (peu utiles), **un seul bloc** (aujourd'hui deux moitiés 1-18 et 19-36 côte à côte) ; les matchs avec leurs scores **à droite du classement** ; tout doit **tenir sans défiler**.
2. Un clic sur un **buteur** ouvre la **fiche du joueur**, jamais la feuille de match. La feuille de match ne s'ouvre qu'en cliquant sur le **score**.
3. (Hors lot, voir plus bas) simuler les manches à élimination directe une par une.

**Constats de l'audit et des lots 1 et 2 repris ici**
- Journée mobile cassée (grille de 5 colonnes + bouton, impossible à 375 px) ; en-têtes BP / BC du classement mobile décalés (les cellules sont masquées, pas les titres).
- Textes sous le plancher de 11 px (buteurs à 8 px, en-têtes de poules à 10 px), couleurs brutes (`#3ddc70`…) au lieu des tokens, ombre portée et boutons ronds sur « Simuler » (DESIGN.md : ni ombre, ni autre rayon que 8 / 12 px).
- Boutons « Retour » (`navigate(-1)`) dans Groups et Bracket, bouton « Classement » dans Simulation : doublons des onglets du lot 2.
- Reportés du lot 2 : la mention « Champion » du cadre n'apparaît qu'au changement d'onglet suivant ; `Groups.jsx` propose « Lancer les barrages » quand l'élimination a déjà été lancée ailleurs.
- Facultatifs de l'expert (lot animation) : code mort `tab` / `replay` dans `openPitch` ; libellés de `LiveButton` encore ceux de l'ancien live textuel.

**Décisions de conception (dans la direction validée)**
- **Classement unique** (`StandingsTable` généralisé, remplace aussi `MiniStandings` et le tableau de `Groups.jsx`) : colonnes `# · Club · J · BP · BC · Diff · Pts`, chiffres alignés ; options pour la flèche de variation de rang et l'étoile « suivre » (écran Classement plein), et pour les zones de qualification (phase de ligue, poules). Sur mobile : `# · Club · J · Diff · Pts` (BP / BC masqués **avec** leurs titres).
- **Ligne de match** (`MatchRow`, utilisée par les trois écrans, `GroupMatchRow` supprimée) : `Club — score — Club` ; buteurs sous le score (domicile à gauche, extérieur à droite) ; mobile sur deux lignes, bureau sur une. Le **score** est le seul lien vers la feuille de match ; chaque **club** mène à sa page, chaque **buteur** à sa fiche (`/clubs/<club>/players/<nom complet>`, nom abrégé à l'affichage). Un match non joué affiche « – – », non cliquable. La ligne elle-même n'est plus cliquable.
- **Barre d'action commune** (nouveau composant) : au même endroit (bas de l'écran), mêmes dimensions et mêmes états dans les trois écrans (« Simuler la journée » / « Journée suivante » et « Simuler tout » ; « Simuler la journée N » / « Lancer les barrages » ; « Simuler ce tour » / « Tour suivant »). Rayon 8 px, pas d'ombre.
- **Phase de ligue, bureau** : classement 36 lignes à gauche, matchs de la journée à droite en une colonne. **Poules classiques** (Coupe du Monde, perso) : grille des groupes conservée, mêmes composants. **Phase finale** : cartes de confrontation conservées (l'arbre est le lot 6), ligne de match et barre d'action partagées.
- « Champion » du cadre à jour dès la fin de la dernière simulation : les pages demandent le rechargement du statut au cadre (contexte de la route, déjà fourni).

**Points soumis au propriétaire, tous validés tels que recommandés le 03/11/2026**
- (a) **Taille du classement dense** : texte 11 px, lignes de 20 px sur bureau (36 lignes = 720 px, la page tient sans défiler à 1440 × 900). Aujourd'hui 12 px et 22 px donneraient 800 px : ça ne tient pas. 11 px est le plancher de DESIGN.md (**recommandé**) ; en dessous, plus lisible du tout.
- (b) **V / N / D retirés partout** (championnat, poules, phase de ligue, écran Classement) pour un seul classement identique, plutôt que seulement en phase de ligue (**recommandé** : c'est le sens du « classement unifié » du plan ; V / N / D restent sur la page du club). Les points et la différence de buts disent déjà l'essentiel.
- (c) **Colonne de droite de la phase de ligue** : les résultats de la dernière journée jouée avec leurs scores ; avant toute simulation, les matchs de la journée 1 (« – – ») ; une bascule « Résultats · À venir » quand les deux existent (**recommandé** : 18 matchs d'une journée tiennent, 36 non). Seuls les matchs de la journée courante restent cliquables (l'API ne détaille que celle-là).
- (d) **Mobile** : bascule « Classement · Matchs » (même geste que « Domicile · Extérieur » du lot 4) plutôt qu'un empilement ; « tout sans défiler » ne vaut que pour le bureau, 36 clubs ne tiennent pas sur 375 × 812 (**recommandé**).
- (e) **Zones de qualification** : bande verte pour les 8 premiers, rouge pour les 12 derniers, **rien pour les barrages** (la légende les nomme), car le jaune sert aux notes et l'or aux trophées (« une couleur = un sens »). Si tu préfères une teinte pour les barrages, il faut un nouveau token.
- (f) **Cible tactile d'un nom de buteur** : 32 px de haut minimum sur mobile (texte courant, plus haut ferait des lignes de match énormes) ; 44 px pour le score, les clubs et les boutons d'action.

**Hors périmètre (volontairement)**
- **Simulation des manches à élimination directe une par une** : le moteur joue l'aller et le retour d'un bloc (`knockout.py`, avec suspensions, blessures et forme entre les deux manches) ; c'est un changement de moteur et d'API, donc un ticket à part avec l'avis de l'architecte.
- Arbre des phases finales et écran de sacre (lot 6) ; club et joueur (lot 5) ; accueil, championnats, recherche (lot 7) ; mode V2.
- API (champ `journee` dans `MatchOut`, cache, persistance), fichiers interdits par `CLAUDE.md`, drapeau `LIVE_AND_ANIMATION_ENABLED` (reste à `false`).

## Critères d'acceptation

- [x] Phase de ligue, bureau 1440 × 900 et 1920 × 1080 : un seul tableau de 36 lignes (pas de deux moitiés), sans V / N / D, matchs à droite avec leurs scores, **aucun défilement de la page** (`scrollHeight` ≤ `clientHeight` du conteneur) ; sous 850 px de haut, c'est le classement qui défile dans son bloc, en-tête figé, jamais la page
- [x] Lignes du classement dense : texte 11 px, hauteur 20 px (bureau), 36 px (mobile) ; aucun texte sous 11 px dans les trois écrans ; chiffres alignés
- [x] Un seul composant de classement pour championnat (colonne de droite et écran Classement), poules, phase de ligue ; colonnes `# · Club · J · BP · BC · Diff · Pts` (bureau), `# · Club · J · Diff · Pts` (mobile), titres alignés avec leurs cellules
- [x] Clic sur un buteur (championnat, poules / phase de ligue, phase finale) → sa fiche joueur dans la compétition, sans ouvrir la feuille de match ; clic sur le score d'un match joué → feuille de match ; clic ailleurs sur la ligne (hors clubs) : rien ; match non joué : score « – – » non cliquable
- [x] Mobile 375 px : journée lisible sur deux lignes par match, aucun défilement horizontal de la page, score et boutons ≥ 44 px, nom de buteur ≥ 32 px
- [x] Mobile 375 px, phase de ligue : bascule Classement · Matchs fonctionnelle, aucun défilement horizontal
- [x] Barre d'action : même composant, même position (bas), mêmes dimensions dans championnat, phase de ligue / poules, phase finale ; libellés inchangés ; rayon 8 px, aucune ombre
- [x] Boutons « Retour » de Groups et Bracket et bouton « Classement » de Simulation supprimés
- [x] « Lancer les barrages » absent quand l'élimination est déjà lancée ; « Champion » du cadre affiché dès la fin de la dernière simulation, sans changer d'onglet
- [x] Tokens uniquement (`win`, `draw`, `loss`, `surface*`, `line`, `link`…) : plus de `#3ddc70` / `#9ca3af` / `#e0645a`, plus de `text-[8px]` / `text-[10px]`
- [x] Code mort `tab` / `replay` de `openPitch` retiré ; libellés de `LiveButton` alignés sur l'animation
- [x] `npm run build` OK ; `npm run lint` : 0 erreur, 5 avertissements au plus
- [x] Parcours vérifiés à l'écran, bureau et mobile : championnat (journée simulée), Ligue des Champions (phase de ligue → barrages → tour suivant), Coupe du Monde ou perso à poules, élimination directe avec aller-retour
- [x] Aucun fichier Python ni fichier interdit par `CLAUDE.md` touché ; suite Python lancée une fois avant la clôture : 2 296 passés, 13 désélectionnés, 0 échec (58 min) ; les 2 282 du lot 4 + 4 tests de préchauffage d'animation restaurés dans l'arbre + environ 10 tests V2 d'une autre session (écart non vérifié ligne à ligne, aucun Python de ce ticket en cause)

## Comments

**03/11/2026 — implémentation**
- Fichiers : `components/matches/MatchRow.jsx` (nouveau, remplace `simulation/MatchRow.jsx` et `GroupMatchRow`), `components/common/ActionBar.jsx` (nouveau), `components/standings/StandingsTable.jsx` (généralisé), `components/simulation/MiniStandings.jsx` (utilise le classement unique), `routes/Simulation.jsx`, `Groups.jsx`, `Bracket.jsx`, `Standings.jsx`, `components/layout/CompetitionLayout.jsx` (rechargement du statut demandé par les pages), `TeamLink.jsx` (taille d'écusson), `ClubLogo.jsx` (initiales de repli à 11 px), `LiveButton.jsx` / `AnimationButton.jsx` (libellés, échelle typo), `ProgressBar.jsx` (plus de dégradé ni d'or).
- Build OK ; lint 0 erreur, 5 avertissements (préexistants).
- Mesures dans la page (navigateur intégré masqué, pas de capture ; API de démonstration sur le port 8001, celle du 8000 appartenant à une autre session), phase de ligue de la Ligue des Champions (36 clubs) : 1440 × 900 et 1920 × 1080 : un seul tableau, 36 lignes de 20 px à 11 px, colonnes `# Club J BP BC Diff Pts`, 18 lignes de match de 36 px sur une ligne, aucun défilement (page ni blocs) ; 1366 × 768 : la page ne défile pas, seuls les deux blocs défilent. Mobile 375 px : bascule Classement · Matchs (2 × 44 px), lignes du classement de 36 px, colonnes `# Club J Diff Pts`, aucun défilement horizontal, aucun texte sous 11 px ; lignes de match sur deux lignes, score 44 px, nom de buteur 32 px.
- Clics vérifiés : buteur → `/clubs/FC Barcelona/players/Pedri` ; score → feuille de match, onglet « Phase de ligue » actif ; clic ailleurs sur la ligne → rien ; matchs à venir : « – – » sans bouton (2 matchs joués avec bouton, 2 à venir sans, dans une poule de la Coupe du Monde).
- Championnat (Ligue 1, 1440 × 900) : liste de 9 matchs à gauche, classement à droite sans V / N / D, aucun défilement, barre d'action 44 px collée en bas (rayon 8 px, aucune ombre), pas de bouton « Classement » ni « Retour ». « Simuler tout » : « Champion : OGC Nice » apparaît dans le cadre sans changer d'onglet, la barre d'action disparaît. Écran Classement mobile : titres BP / BC masqués avec leurs colonnes.
- Phase de ligue → « Lancer les barrages → » → tableau ouvert, onglet « Phase finale » actif et activé sans rechargement ; barrages simulés : score cumulé 5-1, aller 4-0, retour 1-1 (club à domicile inversé), clic sur le score du retour → feuille « Tour 1 · Retour » ; « Tour suivant → » → « 8es de finale » (16 confrontations affichées, barrages en tours précédents) ; retour sur Groups : seul « Voir la phase finale → » est proposé. Poules classiques (Coupe du Monde) : 8 cartes sur 3 colonnes, en-tête « Pays ».
- Corrigés en cours de route : lignes de match de 45 px (la liste dépassait de 60 px) → 36 px ; légende de la phase de ligue coupée sur mobile → retour à la ligne ; nom de club dépassant sa colonne de 3 px → `max-w-full` ; initiales de repli des écussons à 6-7 px → 11 px (une seule lettre sous 24 px).
- Limites : captures impossibles (panneau masqué), donc le rendu fin n'a été contrôlé que par des mesures ; à surveiller à l'activation du drapeau : colonne des boutons LIVE / Animation de `MatchRow` (jamais affichée en V1).

**03/11/2026 — suite à la 1re revue (expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ sur l'état précédent)**
- A1 (expert) / point 10 (QC) : régression, le club suivi n'était plus surligné dans la colonne de la Journée → surlignage en doré sur tous les classements (étoile « suivre » seulement sur l'écran Classement) ; vérifié à l'écran.
- A2 : bascule « Résultats · À venir » à 24 px → 44 px sous `lg` (mesuré à 375 px). A3 : nom de club dans une ligne de match 44 px sur mobile ; dans le classement 36 px (hauteur de ligne du design system), mesuré.
- Choix assumé, mentionné par le QC : la colonne du classement de la Journée apparaît à partir de `lg` (1024 px) au lieu de `md` (768 px) : entre les deux, la colonne des matchs serait trop étroite ; l'onglet Classement reste disponible.
- Non traité (facultatif) : A4 `LiveButton` / `AnimationButton` en mode compact à `h-6`, sans effet tant que le drapeau est à `false`.
- Écart d'attendu de tests : `CLAUDE.md` indique 2 281 ; l'arbre en porte 2 296 à cause de tests d'autres chantiers non commités. Non modifié ici (à mettre à jour quand ces chantiers seront commités).
- 2e passage QC : REFUSÉ sur un seul point : la bascule « Résultats · À venir » à `min-h-11` était dans un en-tête de hauteur fixe `h-7` (28 px) d'un bloc `overflow-hidden` : la boîte de 44 px était mesurée mais rognée, zone cliquable réelle inférieure. Corrigé : en-tête `min-h-7 lg:h-7` (45 px sous `lg`, 28 px sur bureau, inchangé). Mesuré avec `elementFromPoint` aux bords haut et bas : bascule (2 boutons de 44 px), scores (44 px), clubs d'une ligne de match (44 px), noms de buteur (32 px), tous entièrement cliquables ; bureau 1440 x 900 : en-tête 28 px, 36 lignes de 20 px, aucun défilement.

**03/11/2026 — passages de /valider-ticket-simulafoot** (base c5468e6)
- 1er passage (empreinte 9db40094…) : expert APPROVED_WITH_RESERVATIONS (A1 club suivi non surligné, A2 bascule à 24 px) ; QC VALIDÉ (non journalisé : l'état a changé ensuite). Corrections, voir ci-dessus.
- 2e passage (empreinte f29ba77f…) : expert APPROVED ; QC REFUSÉ (bascule à 44 px rognée par un en-tête fixe), journalisé.
- 3e passage (empreinte 04670f78…) : expert APPROVED, QC VALIDÉ. Facultatif : A3 clubs du classement à 36 px (hauteur de ligne du design system) ; A4 mode compact des boutons LIVE / Animation à `h-6` (drapeau à `false`). À surveiller à l'activation du drapeau : colonne des boutons de `MatchRow`, largeur de 576 à 640 px.
- Clôture : VALIDÉ (cloture.py decision, journal `refonte-ui/03/cloture`).

