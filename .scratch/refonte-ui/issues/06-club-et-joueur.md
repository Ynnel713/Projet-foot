# 06: Club et joueur (effectif en tableau, calendrier, fiche joueur en français)

**What to build:** lot 5 de la refonte UX/UI (« la loge de presse, de nuit »). Refaire la **page d'un club** (`TeamRoster.jsx`) et la **fiche joueur** (`PlayerPage.jsx` + `PlayerProfile.jsx`) avec les composants et les règles de `docs/DESIGN.md` : effectif en **tableau** au lieu d'une grille de cartes, **calendrier et forme** du club, fiche joueur **entièrement en français**.

**Status:** livré (03/11/2026), validé expert + QC

**Décisions du propriétaire (03/11/2026) :** « Oui, tout validé » → (a) à (f) tels que recommandés. Avis de l'architecte sur `fixtures` suivi : schémas `FixtureOut` / `ClubFixturesOut` (sans réutiliser `MatchOut`), 404 club inconnu, 409 hors championnat, forme = 5 derniers matchs joués.

## Constat (code lu)
- `TeamRoster.jsx` : grille de cartes `PlayerCard` (96 px) groupées par poste FM (12 sections : GK, DC, LB, RB, MDC…), bouton « Retour » (`navigate(-1)`, doublon des onglets du lot 2), en-tête `TeamHeader` en `rounded-2xl`.
- `PlayerPage.jsx` : bouton « Retour » idem ; charge **tout l'effectif** pour retrouver un joueur (pas d'endpoint « un joueur »). `PlayerProfile.jsx` : 268 lignes, nom à 36 px (`text-4xl`), note à 60 px (`text-6xl`), `rounded-2xl`, opacités blanches en dur (`text-white/55`…), `Preferred moves`, `Points forts` et les **~45 noms d'attributs en anglais** (`Crossing`, `Off the Ball`, `Work Rate`…) alors que le reste est en français.
- Aucune donnée de calendrier par club dans l'API : `MatchOut` n'a pas de numéro de journée (point déjà listé comme « décision API en attente » au Plan, §5bis).
- `RosterOut` / `PlayerOut` (nom, poste, postes secondaires, âge, note, nationalité, pied, taille, mauvais pied, gestes préférés, catégorie, valeur, attributs, photo) suffisent pour l'effectif et la fiche : rien à changer côté API pour ces deux écrans.

## Décisions de conception proposées
- **Page club** : en-tête compact (écusson, nom, championnat, trois chiffres : note globale, âge moyen, valeur estimée ; forme sur les 5 derniers matchs en pastilles `win` / `draw` / `loss` avec lettre V / N / D, la couleur n'étant pas le seul signal). Deux sous-onglets : **Effectif · Calendrier** (même geste que « Domicile · Extérieur » du lot 4 et « Classement · Matchs » du lot 3). Bouton « Retour » supprimé.
- **Effectif en tableau** : groupes par ligne (Gardiens, Défenseurs, Milieux, Attaquants), joueurs triés par note décroissante dans chaque groupe. Colonnes bureau `Joueur (photo 24 px + nom) · Poste · Âge · Pied · Note` ; mobile `Joueur · Poste · Note`. Lignes 32 px bureau / 36 px mobile, chiffres alignés, texte 13 px, en-tête de groupe 11 px. Toute la ligne ouvre la fiche (le nom est le lien). Note = pastille de la teinte FM déjà utilisée (`fmTierColor`), valeur neutre en chiffre.
- **Calendrier** : liste des matchs du club dans la compétition avec la journée, l'adversaire, le lieu (D / E), le score (score = lien vers la feuille de match, comme au lot 3) ou « – – » pour les matchs à venir ; la journée courante repérée. **Championnat seulement** dans ce lot ; en poules / phase finale l'onglet reste absent (le tableau et les poules ont déjà leur écran). Demande un petit ajout d'API en lecture seule (voir point b).
- **Fiche joueur** : même contenu, remis aux règles du design system : nom 32 px (nouveau jeton `text-title`, ajouté à l'échelle de `index.css`), note en pastille 48 px, rayons 8 / 12 px, jetons de couleur (`text-gray-*`) au lieu des opacités blanches, plancher 11 px, bouton « Retour » supprimé, trois colonnes d'attributs puis radar conservés, colonne unique sur mobile. **Aucun nouveau contenu** (pas de carrière ni de texte de scouting : la fiche garde la note de `PlayerProfile` sur l'absence de données d'historique).
- **Français partout dans la fiche** : noms d'attributs, « Preferred moves » → « Gestes préférés », « Points forts » traduits. Table de traduction ci-dessous (côté interface seulement ; les noms de données restent ceux du moteur).

### Table de traduction proposée (à valider, c'est du libellé produit)
| Catégorie | Traductions |
|---|---|
| Technique | Crossing → Centres · Dribbling → Dribble · Finishing → Finition · First Touch → Premier contrôle · Heading → Jeu de tête · Long Shots → Tirs de loin · Marking → Marquage · Passing → Passes · Tackling → Tacles · Technique → Technique |
| Gardien | Aerial Reach → Portée aérienne · Command of Area → Autorité dans la surface · Communication → Communication · Eccentricity → Excentricité · Handling → Prise de balle · Kicking → Jeu au pied · One on Ones → Un contre un · Punching (Tendency) → Boxe (tendance) · Reflexes → Réflexes · Rushing Out (Tendency) → Sorties (tendance) · Throwing → Relance à la main |
| Mental | Aggression → Agressivité · Anticipation → Anticipation · Bravery → Courage · Composure → Sang-froid · Concentration → Concentration · Decisions → Décisions · Determination → Détermination · Flair → Inspiration · Leadership → Leadership · Off the Ball → Appels sans ballon · Positioning → Placement · Teamwork → Esprit d'équipe · Vision → Vision · Work Rate → Volume de jeu |
| Physique | Acceleration → Accélération · Agility → Agilité · Balance → Équilibre · Jumping Reach → Détente · Natural Fitness → Condition naturelle · Pace → Vitesse · Stamina → Endurance · Strength → Force |
| Coups de pied arrêtés | Corners → Corners · Free Kick Taking → Coups francs · Long Throws → Touches longues · Penalty Taking → Penalties |

## Points soumis au propriétaire (recommandation en premier)
- (a) **Structure de la page club** : sous-onglets Effectif · Calendrier — recommandé (un écran par question, comme les lots 3 et 4, rien à faire défiler pour atteindre le calendrier). Alternative : tout sur une page.
- (b) **Calendrier = petit ajout d'API en lecture seule** (`GET /competitions/{id}/clubs/{club}/fixtures` : journée, adversaire, lieu, score, joué ou non ; aucune simulation, aucun fichier protégé, aucune écriture) — recommandé : sans lui, pas de calendrier ni de forme. Exception au « frontend seulement » du chantier à valider. Alternative : lot 5 sans calendrier ni forme, repoussé à une décision API ultérieure.
- (c) **Forme sur 5 matchs** dans l'en-tête du club (même endpoint) — recommandé : une lecture immédiate de la dynamique, très attendue dans un jeu de gestion. Alternative : sans.
- (d) **Colonnes de l'effectif** : bureau `Joueur · Poste · Âge · Pied · Note`, mobile `Joueur · Poste · Note` — recommandé. Pas de tri par colonne dans ce lot (ordre fixe par ligne puis note). Alternative : tri par colonne (plus de code, utile sur un effectif de 25 à 30 joueurs).
- (e) **Table de traduction** ci-dessus, termes usuels des jeux de gestion français — recommandé. Les « gestes préférés » restent dans leur forme de données tant que leur catalogue n'est pas figé (un ticket V2 « catalogue des gestes préférés » existe) ; ils sont seulement relibellés « Gestes préférés ».
- (f) **Photos** : 24 px dans les lignes de l'effectif, 112 px sur la fiche (taille actuelle) — recommandé ; placeholder « ? » remplacé par les initiales (comme `ClubLogo`).

## Hors périmètre
- Statistiques de saison d'un joueur (buts, passes, cartons) sur sa fiche : le classement buteurs existe mais l'association par joueur demande un endpoint de plus. À proposer en lot 7 si tu le veux.
- Compos de matchs (lot 4), arbre et sacre (lot 6), accueil et recherche (lot 7), mode V2.
- Moteur, fichiers protégés, `LiveEventOut`, drapeau `LIVE_AND_ANIMATION_ENABLED` (reste à `false`).

## Critères d'acceptation
- [x] Page club : un tableau d'effectif par ligne (G / D / M / A), trié par note, colonnes bureau et mobile comme au point (d), lignes 32 px bureau / 36 px mobile, aucun défilement horizontal à 375 px, aucun texte sous 11 px
- [x] Clic sur une ligne de l'effectif → fiche du joueur (cible ≥ 36 px de haut mobile) ; aucun bouton « Retour » sur les deux écrans
- [x] Sous-onglets Effectif · Calendrier fonctionnels (clavier et tactile) ; calendrier absent hors championnat
- [x] Calendrier : tous les matchs du club avec journée, adversaire, lieu, score ou « – – » ; le score d'un match joué ouvre sa feuille de match ; la journée courante repérée ; forme sur 5 matchs en pastilles V / N / D (lettre + couleur)
- [x] API : endpoint `fixtures` en lecture seule, 404 pour un club inconnu, 409/vide hors championnat ; tests unitaires (club, journée, ordre, joué / non joué) ; aucun fichier protégé touché
- [x] Fiche joueur : 0 nom d'attribut en anglais (les ~45 de la table), « Gestes préférés » ; nom 32 px, note en pastille 48 px, rayons 8 / 12 px, jetons de couleur uniquement (0 `text-white/NN`, 0 hexadécimal, 0 `text-[Npx]`)
- [x] Fiche joueur mobile 375 px : colonne unique, radar visible entièrement, aucun défilement horizontal ; bureau 1440 × 900 : en-tête + 3 colonnes d'attributs + radar lisibles
- [x] Test (ou vérification scriptée) : tout nom d'attribut de `FM_ATTRIBUTE_CATEGORIES` a une traduction
- [x] `npm run build` OK ; `npm run lint` : 0 erreur, 5 avertissements au plus
- [x] Parcours vérifiés à l'écran, bureau et mobile : championnat (club → effectif → joueur, calendrier → feuille de match), compétition perso à poules (effectif seul)
- [x] Suite Python lancée une fois avant la clôture (le ticket touche l'API) ; compte comparé à l'attendu
- [x] Mise à jour de `Plan architecte Simulafoot.md`, `docs/TRD_MAJ.md` (endpoint), `docs/known_issues.md` si un ticket est ouvert ou fermé

## À vérifier avant de coder
- Avis de `simulafoot-architect` sur l'endpoint `fixtures` : où vit le calendrier d'un championnat (`Season`), comment numéroter les journées, comportement quand la saison est terminée.
- Absence de tout import de `PlayerProfile` / `PlayerCard` ailleurs (`MatchSheet`, `Leaderboards`) avant de les modifier.

## Comments

**03/11/2026 — implémentation**
- Fichiers : `api/schemas.py` (`FixtureOut`, `ClubFixturesOut`), `api/serializers.py` (`club_fixtures_out`), `api/routers/competitions.py` (route `fixtures`), `tests/test_competitions.py` (4 tests : calendrier frais, résultat et forme après 7 journées, lecture seule, erreurs 404 / 409), `ui/src/api/client.js`, `routes/TeamRoster.jsx`, `routes/PlayerPage.jsx`, `components/team/` (`RosterTable`, `FixturesList` nouveaux ; `TeamHeader`, `PlayerProfile`, `SectionPanel`, `StarRating` ; `PlayerCard` supprimé), `utils/fmAttributes.js` (`attributeLabel`), `index.css` (`text-title`).
- Étoiles du « mauvais pied » : or → ambre (`tier-avg`), l'or étant réservé aux trophées et au club suivi.
- Mesures (API de démonstration port 8001, navigateur masqué donc sans capture) : bureau 1440 × 900 : 5 colonnes, lignes 33 px, police mini 11 px, aucun défilement horizontal ; mobile 375 : 3 colonnes, lignes 36 px, adversaire et score du calendrier 44 px (premier jet : adversaire à 20 px, corrigé), fiche joueur sur une colonne, radar de 283 px ; aucun nom d'attribut anglais dans la fiche ; élimination directe : 409, ni onglets ni forme.
- Clôture : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ. Réserves de l'expert acceptées par le propriétaire (« Oui, j'accepte ») : A1 contrôle visuel à l'œil à faire par le propriétaire (aucune capture prise) ; A2 documentation (vérifiée ensuite par le QC : Plan et TRD_MAJ à jour). Réserves du QC : Coupe du Monde non vue à l'écran ; `getClubFixtures` masque silencieusement toute erreur (réseau comprise).
- Non vérifié : Coupe du Monde à l'écran (création trop longue ; cas hors championnat couvert par le 409 et l'écran en élimination directe) ; rendu visuel à l'œil (aucune capture).
- Suite Python complète sur l'arbre entier : 2 324 passés, 13 désélectionnés, 0 échec (44 min) ; état exact revu (autres chantiers mis de côté) : build OK, 18 tests passés sur `test_competitions` + `test_api_animation` ; lint 0 erreur, 5 avertissements.
