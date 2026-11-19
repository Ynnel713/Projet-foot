# EM-04 — Mise en page en trois zones et responsive (E) — 120 min (moyenne)

**Status:** livré (18/11/2026), validé expert + QC (réserve A1 acceptée par le propriétaire, critère reporté à EM-15)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : HUD / centre / zone basse ; terrain dominant ; adaptation 844×390 à 1920×1080.
- **Problème** : terrain petit, compositions masquées sous 1024 px, en-tête global qui mange 56 px.
- **Résultat** : grille CSS à trois zones, en-tête global masqué sur `/v2`, colonnes de compositions à 200 à 230 px, repli
  tiroirs sous 960 px ; coquilles vides stylées pour les zones (contenu inchangé à ce stade).
- **Périmètre** : structure uniquement. **Composants** : `V2Match.jsx`, `AppShell.jsx`, `index.css`.
- **Critères** : captures aux 4 tailles (844×390, 1024×768, 1366×768, 1920×1080) ; surface du terrain ≥ +30 % à 1280×720
  (mesurée) ; aucun défilement de page ; autres routes gardent leur en-tête.
- **Tests** : captures avant/après ; contrôle manuel des autres routes ; build, lint.
- **Dépendances** : EM-01. **Risques** : `AppShell` partagé.

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 25 min |
| Développement | 45 min |
| Tests (mesures, captures) | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **120 min** (révisé à 150 min le 18/11/2026 : zone basse compacte et repli selon la hauteur, seconde série de mesures) |

Confiance : moyenne. Au seuil indicatif de 2 h, pas au-delà : pas de découpage (la frontière avec EM-10b est nette : EM-04 la structure, 10b le contenu des cartes compactes et des tiroirs). Temps machine hors total : enregistrement d'une trace (2 min 14), suite complète.

## Décisions du propriétaire (18/11/2026)

- Constantes : « Valider tel quel » : en-tête global masqué sur toute la route `/v2` (réglage compris) ; trois zones (HUD, centre, zone basse avec le momentum déplacé sous le terrain et le panneau d'intention) ; colonnes de 220 px dès 1280 px de large, 200 px de 960 à 1279 px ; sous 960 px, tiroirs de 260 px ouverts par une languette de 28 px, fermés par défaut, terrain pleine largeur ; contenu des listes inchangé.
- Après la première mesure (terrain −12 % à 1280×720, −11 % à 1366×768 avec une zone basse de 150 px), « Zone basse compacte » : zone basse de 110 px au plus, frise du momentum de 72 px au plus ; objectif ne rien perdre à 1280 et 1366 (écart ≥ −3 %) ; le critère « +30 % à 1280×720 » est reporté à la fin d'EM-06 (piste et bancs sortis du dessin, proportions du terrain changées), noté dans le ticket 06.
- Téléphone en paysage (terrain de 285×176 px à 844×390), « Zone basse repliée » : sous 500 px de haut, la zone basse se réduit à la ligne d'intention, sans la frise.

## Critères d'acceptation (chiffrés avant le code, C1 reformulé par décision)

- [x] C1 : surface dessinée du terrain ≥ −3 % à 1280×720 et 1366×768, en hausse à 1024×768 et 1920×1080 (le +30 % à 1280×720 est reporté à EM-06). Mesuré : +1,0 % (820×505 → 824×508), +2,9 % (896×552 → 909×560), +16,2 % (564×347 → 608×375), +149,6 % (896×552 → 1415×872).
- [x] C2 : aucun défilement de page aux 4 tailles et à 1280×720 (document et zones) ; défilement interne seulement dans les tiroirs (liste plus haute que 390 px) et dans la zone basse quand un joueur est sélectionné.
- [x] C3 : colonnes de 220 px à 1366 et 1920, 200 px à 1024 ; à 844×390, colonnes masquées, tiroirs fermés hors écran (−260..0 et 844..1104), ouverts au toucher de la languette (0..260 et 584..844, `aria-expanded`), refermés par la même languette.
- [x] C4 : en-tête global absent sur `/v2` (lecture et réglage, bouton Retour présent), présent sur `/`.
- [x] C5 : `npm run build` OK ; `npm run lint` 0 erreur, 5 avertissements (préexistants) ; `npm test` 18/18.
- [x] C6 : captures avant/après aux 4 tailles et à 1280×720 (hors dépôt, scratchpad de la session) ; sélection d'un joueur conservée (intention affichée).
- [x] Déterminisme : deux passes de mesure identiques au pixel près sur la même trace (`?fixture=em04&t=30&paused=1`).

## Comments

- 18/11/2026, implémentation. `MatchScreen.jsx` en grille à trois zones (`data-zone` : `hud`, `centre`, `terrain`, `bas`, `composition-*`, `tiroir-*`, `languette-*`) ; composant local `LineupSide` (colonne dès 960 px, tiroir en dessous, `inert` quand fermé, transition 200 ms désactivée par `prefers-reduced-motion`) ; `AppShell.jsx` masque l'en-tête sur `/v2` ; `LineupPanel.jsx` prend la largeur que l'écran lui donne (plus de `hidden lg:flex w-52`) ; `V2Pitch.jsx` reçoit sa taille par `className` (défaut inchangé), le dessin se centre dans sa case ; `Momentum.jsx` se contracte avec la zone basse (`h-full`, 72 px au plus). Contenu des zones inchangé (HUD : EM-08 ; cartes : EM-10 ; intention en tiroir : EM-15). Mesures : trace réelle enregistrée `em04` (Paris Saint-Germain 6-3 Olympique Marseille, graine 20261118, `scripts/record_v2_trace.py`), scripts et résultats dans `.scratch/v2-ecran-match/mesures/em04-*` (surface dessinée calculée depuis le viewBox, le SVG remplissant sa case). Point connu : quand un joueur est sélectionné, le panneau d'intention prend la zone basse (la frise se contracte) et y défile ; réglé par EM-15.
- 18/11/2026, passage 1, clôture : expert APPROVED_WITH_RESERVATIONS (empreinte `6c6c9cbc`) ; QC VALIDÉ ; clôture VALIDÉ (journal, sous-étape `v2-ecran-match/04/cloture`).
  - A1 [réserve] : avec un joueur sélectionné, le panneau d'intention prend toute la zone basse (110 px), la frise du momentum tombe à 0 px et 24 px d'intention sont cachés derrière un défilement interne. Acceptée par le propriétaire : « J'accepte A1 » ; critère « frise visible et intention lisible sans défilement avec un joueur sélectionné » ajouté au ticket EM-15.
  - A2 [facultatif] : `pathname === "/v2"` ne reconnaît pas `/v2/` (risque négligeable avec le routeur actuel).
  - QC, remarques non bloquantes : repli de la frise sous 500 px de haut non isolé dans les mesures ; le ticket citait `V2Match.jsx` et `index.css`, les fichiers réels depuis EM-01 sont `MatchScreen.jsx`, `LineupPanel.jsx`, `Momentum.jsx`, `V2Pitch.jsx` et `AppShell.jsx` (`index.css` inchangé).
- **Durée réelle** : environ 50 min de travail effectif (analyse 15, développement 15, tests et mesures 15, intégration et vérifications 5 hors clôture), contre 150 min estimées après extension (120 au départ) : − 67 %. Cause : structure concentrée dans `MatchScreen.jsx` (grille et un composant local), banc de rejeu d'EM-00 et outillage de mesure Playwright directement réutilisables, premières mesures qui ont tranché les deux décisions sans itération de code ; QC VALIDÉ et expert favorable au premier passage. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée. Temps machine hors total : enregistrement de la trace (2 min 14), suite complète (13 min 15), quatre passes de mesure.
- 18/11/2026, suite : le critère « +30 % à 1280×720 » reporté à EM-06 y a été remplacé par « ≥ +18 % » (décision du propriétaire, « Retenir la mesure » : plafond ≈ +19,6 % avec les colonnes de 220 px et la marge de 3 m) ; mesuré à +20,0 % après EM-06.
