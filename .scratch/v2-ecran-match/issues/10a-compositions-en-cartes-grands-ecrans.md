# EM-10a — Compositions en cartes, écrans ≥ 1280 px (V) — 90 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Ticket parent : `10-compositions-en-cartes.md` (découpé en 10a et 10b). Chantier : `.scratch/v2-ecran-match/spec.md`
(§ « Compositions (cartes) »). Suite : 10b (cartes compactes de 960 à 1279 px, tiroirs sous 960 px).

- **Problème** : listes de 11 px sans hiérarchie (numéro, poste, nom au même niveau), titulaires et remplaçants peu
  distingués. **Résultat attendu** : cartes aux couleurs d'équipe, gauche et droite en miroir, sans note ni statistique.
- **Dépendances** : EM-03 (jetons `--team-*`), EM-04 (colonnes de 220 px). **Risques** : entraîneur (conservé, discret) ;
  numéros des entrants (ticket coach/05, hors périmètre).

## Comments

### 19/11/2026 — estimation, constantes et critères validés par le propriétaire

- **Estimation** (travail effectif) : analyse 15 min, développement 40 min, tests et captures 20 min, intégration et
  clôture 15 min, **total 1 h 30**, confiance moyenne. Hypothèses : aucune modification de l'API (`number`, `poste`,
  `name`, `formation`, `coach` déjà fournis par `/api/v2/lineup`) ; seuls `LineupPanel.jsx` et son appel changent. Temps
  machine à part : suite complète (environ 13 min), enregistrement d'une trace et captures.
- **Écart à la spec signalé avant le code** : des cartes de 36 px ne tiennent pas dans la colonne de 576 px de
  1366×768 (11 × 36 = 396 px ; il resterait environ 9 px par remplaçant). Données réelles (816 clubs) : banc de 0 à 9
  joueurs, nom le plus long 27 caractères (« Ayoube Amaimouni-Echghouyab », Eintracht Frankfurt), club le plus long
  31 caractères, entraîneur le plus long 24.
- **Constantes validées (« valide 26/20 sans palier », 19/11/2026)** : carte titulaire 26 px, carte remplaçant 20 px à
  60 % d'opacité ; pastille de numéro 20 px à la couleur d'équipe, chiffre à l'encre d'équipe (EM-03) ; colonne poste
  28 px, gris ; liseré 3 px à la couleur d'équipe, à gauche pour le domicile et à droite pour l'extérieur (miroir) ; nom en
  13 px sur une ligne, tronqué par « … », nom complet en `title` ; en-tête : écusson 28 px et club (tronqué), puis
  « formation · entraîneur » en 11 px gris ; intertitres « Titulaires » et « Remplaçants » en 11 px majuscules. Un seul
  gabarit, **sans palier grand écran** (36/28 px à ≥ 720 px de haut écarté ; à revoir à EM-16 si besoin).
- **Critères d'acceptation** (DOM, 1366×768 et 1920×1080) : 11 titulaires et 9 remplaçants visibles, aucun défilement
  des deux colonnes ; symétrie : mêmes hauteurs de cartes et mêmes positions verticales des deux côtés (écart 0 px),
  liseré et numéro en miroir ; le nom de 27 caractères est tronqué sans débordement horizontal de la colonne, nom complet
  accessible ; aucune note ni statistique ; `npm test`, lint 0 erreur, build OK ; suite Python à 3 437 passés.

### 19/11/2026 — implémentation

- **Code** : `ui/src/utils/lineupCards.js` (nouveau : constantes du gabarit, budget vertical `lineupColumnHeight`,
  sous-titre « formation · entraîneur ») et son test ; `components/match/LineupPanel.jsx` réécrit (`PlayerCard`,
  `Section`, en-tête avec `ClubBadge`), reçoit `side` au lieu d'une couleur et lit les jetons `--team-<side>`,
  `--team-<side>-ink`, `--team-<side>-ui` ; `MatchScreen.jsx` : passe `side`, marge verticale des colonnes et tiroirs
  8 → 6 px (budget vertical). Section des remplaçants masquée quand le banc est vide.
- **Détail non listé dans les constantes** : pastille de numéro des remplaçants à 16 px (une pastille de 20 px remplirait
  la carte de 20 px sans marge). À confirmer par le propriétaire.
- **Tests** : `utils/lineupCards.test.js` (4 tests : constantes 26/20, 11 + 9 cartes ≤ 576 px, section du banc retirée
  du budget quand il est vide, sous-titre avec ou sans entraîneur), ajouté au script `npm test`.
- **Mesures** (`mesures/em10a-mesure.cjs`, Playwright, serveur de développement, trace réelle `em10a` enregistrée par
  `scripts/record_v2_trace.py` : Eintracht Frankfurt – Borussia Mönchengladbach, graine 20261107, 9 remplaçants de
  chaque côté et le nom le plus long de la base ; résultats `mesures/em10a-apres.json`, captures `mesures/em10a/`) :
  - 1366×768 : colonnes de 220 × 570 px (HUD plus haut de 6 px depuis EM-04), 20 cartes sur 20 visibles, défilement
    0 px des deux côtés ; 1920×1080 : 220 × 882 px, 20 sur 20, 0 px ;
  - cartes de 26 et 20 px exactement ; positions verticales des 20 cartes identiques à gauche et à droite (écart 0 px) ;
    liseré 3 px à gauche (domicile), 3 px à droite (extérieur) ; pastille à 17 px du bord extérieur des deux côtés ;
  - « Ayoube Amaimouni-Echghouyab » tronqué (`scrollWidth > clientWidth`), `title` complet, débordement horizontal de
    la colonne 0 px ; aucun défilement de page aux cinq tailles ;
  - hors critère : 1280×720 (colonne de 522 px) défile de 40 px (18 cartes sur 20 visibles), annoncé avant le code ;
    1024×768 tient (200 × 570 px, 0 px) ; 844×390 : colonnes masquées, tiroirs (10b).
- **Vérifications** : suite Python 3 437 passés, 0 ignoré, 14 désélectionnés (15 min 02, attendu inchangé) ; `npm test` 47 passés, 0 échec ; `npm run lint` 0 erreur, 5 avertissements (attendu) ; build OK.
- **Déterminisme** : rendu seul, aucun aléa ni horloge ajoutés ; moteur et trace non touchés.
- **À vérifier à l'écran** : lisibilité des pastilles à fond très sombre (Francfort : fond quasi noir sur `surface-2`,
  chiffre blanc lisible mais pastille peu détachée) ; rendu des tiroirs (contenu identique, gabarit 10b à venir).
- **Durée** : estimée 1 h 30 ; réelle environ 1 h 15 de travail effectif (analyse 20, développement 25, tests et
  captures 15, intégration et clôture 15), écart − 17 % (sous 30 %). Temps machine hors total : enregistrement de la
  trace `em10a` (environ 8 min), mesures navigateur (environ 2 min), suite complète (15 min 02).

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `eb947666`) : **APPROVED_WITH_RESERVATIONS**. Budget vertical recalculé indépendamment (562 px pour
  570, positions mesurées 70 et 376 px retrouvées ; 40 px de défilement prévus et mesurés à 1280×720).
  - A1 [réserve] pastille de numéro des remplaçants à 16 px, constante non listée dans la validation du 19/11/2026.
  - A2 [facultatif] test de budget comparé à 576 px au lieu des 570 px mesurés.
  - A3 [facultatif] hauteurs du budget recopiées des classes Tailwind sans lien dans le code.
  - A4 [facultatif] commentaire sur la prop `color` de `LineupSide`, qui ne sert plus qu'à la languette.
- Contrôle qualité : **VALIDÉ**, avec deux points à confirmer : la pastille à 16 px (= A1) et la marge verticale des
  colonnes et tiroirs passée de 8 à 6 px.
- **Réserves acceptées par le propriétaire** : « j'accepte A1 à 16 px et la marge à 6 px » (19/11/2026).
- **Décision de clôture** : VALIDÉ. A2 à A4 reportés à 10b. À surveiller : contraste de la pastille et du liseré pour
  les couleurs très sombres (EM-03) ; défilement de 40 px à 1280×720 (10b ou EM-16).
