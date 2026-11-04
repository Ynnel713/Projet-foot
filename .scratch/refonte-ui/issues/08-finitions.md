# 08: Finitions (accueil, championnats, recherche d'équipes, V2)

**What to build:** lot 7 et dernier de la refonte UX/UI (« la loge de presse, de nuit »). Passer les écrans qui n'ont pas encore été repris aux règles de `docs/DESIGN.md` : accueil (`Home.jsx`), liste des championnats (`Leagues.jsx` + `LeagueCard.jsx`), choix des équipes de l'assistant (`CustomCompetition.jsx`, `StepTeams`), page des sélections (`Nations.jsx`), écran V2 (`V2Match.jsx`). Frontend seulement.

**Status:** livré (04/11/2026), validé expert + QC

**Décisions du propriétaire (04/11/2026) :** « Ok, tu peux continuer » → (a) à (e) tels que recommandés.

## Constat (code lu)
- `Home.jsx` : titre `text-3xl/4xl`, cartes `rounded-2xl` (16 px, hors échelle 8 / 12), bordures `border-white/10`, `hover:scale` animé (spectacle hors moments qui le méritent), `text-xs` et `text-sm` à la place des jetons, « Reprendre » déjà fait au lot 2. Compteur « 7 564 joueurs » codé en dur.
- `Leagues.jsx` / `LeagueCard.jsx` : `rounded-2xl`, `border-white/5`, `hover:scale`, bouton « Accueil / Tous les championnats » en haut (retour manuel), erreur déjà gérée.
- `StepTeams` : recherche + filtres par catégorie + grille 2/3 colonnes de cases 52 px ; compteur « n / N » ; pas de bouton pour tout effacer ni de tri affiché ; filtres 32 px de haut (cible < 44 px mobile), `text-xs`.
- `Nations.jsx` : route `/nations` encore déclarée, mais plus aucune tuile d'accueil n'y mène (retirée le 28/09/2026).
- `V2Match.jsx` : 699 lignes, écran bêta à part, hors cadre de compétition.

## Décisions de conception proposées
- **Accueil** : mêmes cartes que le reste (rayon 12 px, bordure `line`, fond `surface`), plus d'agrandissement au survol (simple changement de fond), titre 24 px, textes sur l'échelle 11 / 13 / 14, cibles ≥ 44 px sur mobile. « Reprendre » inchangé.
- **Championnats** : mêmes cartes ; le bouton d'en-tête garde sa place (pas d'onglets ici, ce n'est pas un espace de compétition) mais passe à 44 px.
- **Choix des équipes** : cases 44 px mini, filtres 44 px mobile / 32 px bureau, bouton « Tout effacer » si au moins une équipe est cochée, compteur en 13 px, jetons de couleur.
- **Page `/nations`** : à retirer (route orpheline) — voir point (c).
- **V2** : seulement le gabarit et les jetons (titres, rayons, couleurs en dur, cibles 44 px) ; ni la mécanique ni la mise en page de l'écran ne changent.

## Points soumis au propriétaire (recommandation en premier)
- (a) **Accueil et championnats : alignement sur le système, sans nouveau contenu** — recommandé : le lot est un lot de finitions ; les statistiques par joueur sur la fiche (proposées plus tôt) demandent un nouvel endpoint et font un ticket à part.
- (b) **Compteur de joueurs** : le laisser tel quel — recommandé (hors périmètre, un endpoint juste pour un chiffre n'en vaut pas la peine). Alternative : le retirer.
- (c) **Supprimer `Nations.jsx` et sa route** — recommandé : code mort depuis le 28/09 (les sélections passent par Compétition perso). Alternative : le garder et le reprendre visuellement.
- (d) **V2 : jetons et gabarit seulement** — recommandé, l'écran est une bêta qui bouge encore (autre session en cours dessus, fichier modifié et non commité). Alternative : le laisser entièrement tel quel et ne rien y toucher dans ce lot.
- (e) **Choix des équipes : « Tout effacer » en plus** — recommandé : petit ajout qui évite de décocher 16 équipes une à une.

## Hors périmètre
Moteur, API, fichiers protégés ; statistiques par joueur sur la fiche (ticket à part) ; vrais raccords de l'arbre ; masquage d'erreur de `getClubFixtures` ; boutons LIVE compacts (flag désactivé).

## Critères d'acceptation
- [x] Accueil, Championnats, Choix des équipes : 0 rayon 16 px, 0 `hover:scale`, 0 couleur en dur ni `white/NN`, 0 ombre / dégradé, plancher 11 px
- [x] Mobile 375 px sur ces trois écrans : aucun défilement horizontal de la page, cibles ≥ 44 px
- [x] Bureau 1440 × 900 : mêmes écrans sans défilement de page là où le contenu tient
- [x] « Tout effacer » visible seulement si ≥ 1 équipe cochée ; remet le compteur à 0
- [x] `Nations.jsx` et la route `/nations` retirés si (c) est accepté, sans lien cassé (grep)
- [x] V2 : gabarit et jetons alignés, comportement du match inchangé (même requêtes réseau, mêmes boutons)
- [x] `npm run build` OK ; `npm run lint` : 0 erreur, 5 avertissements au plus
- [x] Parcours vérifiés à l'écran : accueil → championnats → lancement ; accueil → Compétition perso → choix des équipes ; accueil → V2
- [x] Aucun fichier Python ni fichier protégé touché ; suite Python non requise
- [x] Mise à jour de `Plan architecte Simulafoot.md`

## Comments

**04/11/2026 — implémentation**
- Fichiers : `routes/Home.jsx`, `routes/Leagues.jsx`, `components/league/LeagueCard.jsx`, `routes/CustomCompetition.jsx` (tout l'assistant, pas seulement le choix des équipes : mêmes classes hors échelle), `App.jsx` (route retirée), `routes/Nations.jsx` supprimé, `routes/V2Match.jsx` (11 lignes : `text-xs`, `text-[11px]`, `border-white/10`, retour 44 px).
- Fait : rayons 16 px → 12 px, `hover:scale` / `whileHover` retirés (framer-motion ne sert plus dans ces écrans), `white/NN` → jetons, `text-xs` → `text-data` (13 px), titre d'accueil 24 px, retours et filtres à 44 px sur mobile, étoiles de force en `tier-avg` (l'or est réservé aux trophées), « Tout effacer » dans l'assistant. Couleurs de terrain et d'équipe du SVG V2 conservées (données, pas décor). `text-gold` du chronomètre V2 laissé tel quel (sens à confirmer, voir ci-dessous).
- V2Match.jsx : le fichier porte aussi ~300 lignes non commitées d'une autre session ; la revue et le commit ne portent que sur la version HEAD + ces 11 lignes, les mêmes remplacements ont été appliqués à la version de travail.
- Mesures (API 8001, serveur Vite propre, bureau 1440 × 900 puis mobile 375) : Accueil, Championnats, assistant (étapes 1 à 4) : 0 rayon 16 px, 0 ombre, 0 dégradé, 0 texte sous 11 px, aucun défilement horizontal ; mobile : seule cible < 44 px = icône « Accueil » 32 px de la coque (lot 2, hors périmètre) ; « Tout effacer » absent à 0 équipe, visible à 2 (44 px), remet le compteur à 0. V2 : s'ouvre, 0 anomalie de gabarit.
- Build OK ; lint 0 erreur, 5 avertissements. Aucun fichier Python ni protégé touché : suite Python non relancée.
- Non vérifié : rendu à l'œil (pane masqué, aucune capture) ; écran de match V2 pendant un match ; `/nations` redirige vers l'accueil (route `*`).

**04/11/2026 — clôture**
- Expert : APPROVED_WITH_RESERVATIONS ; QC : VALIDÉ. Réserves acceptées par le propriétaire (« Oui, tu peux clôturer ») : A1 `hover:border-gray-700` (couleur de palette, pas un jeton, cosmétique), A2 parcours non vus à l'œil (à confirmer à sa recette). Reliquat signalé par le QC : `active:scale-[0.98]` sur deux boutons principaux de l'assistant.
