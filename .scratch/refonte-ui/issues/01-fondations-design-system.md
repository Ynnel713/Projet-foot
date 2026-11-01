# 01: Fondations du design system (tokens, typographie, fond)

**What to build:** Lot 1 de la refonte UX/UI validée par le propriétaire le 01/11/2026 (direction « la loge de presse, de nuit »). Poser les tokens de couleur et de typographie dans `ui/src/index.css`, retirer le fond d'écran du stade, migrer les couleurs et tailles codées en dur des écrans V1 visibles vers ces tokens, réécrire `docs/DESIGN.md`. Aucun changement de mise en page ni de comportement : c'est le socle des lots 2 à 7.

**Status:** livré (01/11/2026), validé expert + QC

**Décisions du propriétaire (01/11/2026)**
- Direction artistique, palette, typographies (Barlow Condensed + IBM Plex Sans) et plan en 7 lots : « Valider, lancer lot 1 ».
- Sens des couleurs : bleu = action, vert/rouge/gris = résultat ou note, or = trophée et club suivi.

**Hors périmètre (volontairement)**
- `MatchRow.jsx`, `Groups.jsx`, `Bracket.jsx`, `Simulation.jsx` : modifications non commitées d'un autre chantier (animation) en cours ; refaits au lot 3. Ils héritent des tokens globaux sans être édités.
- Écrans désactivés en V1 (`PitchView`, `LivePanel`, `GoalAlerts`, `MatchAnimation`, boutons LIVE/Animation) et V2 (`V2Match`) : lot 7.
- Seuils des paliers de note (`fmTier`) : inchangés (constante produit).
- Bug d'en-têtes BP/BC du classement mobile : lot 3 (le tableau y est refait).

## Critères d'acceptation

- [x] Tokens déclarés dans `@theme` : fond + 3 surfaces + ligne, action, or, victoire/nul/défaite, paliers de note (texte et aplat), polices `sans` et `display`, tailles `caption` (11 px) et `data` (13 px)
- [x] Échelle `gray` et `slate` de Tailwind remappée sur une seule palette neutre ; texte secondaire (`gray-400`) ≥ 7:1 et texte discret (`gray-500`) ≥ 4,5:1 sur le fond
- [x] Plus aucune image ni dégradé de fond : `.app-bg` supprimé, fond uni
- [x] Dans les fichiers du périmètre : 0 taille `text-[…px]` sous 11 px, 0 couleur hexadécimale en dur hors `index.css` (sauf rendu du terrain `PitchField`, hors V1)
- [x] Paliers de note : mêmes seuils, mêmes couleurs d'aplat qu'avant (aucun écart de sens)
- [x] `npm run build` OK ; `npm run lint` : 0 erreur, 5 avertissements (référence CLAUDE.md)
- [x] Contrôle visuel avant/après, bureau 1440 px et mobile 375 px : accueil, championnats, journée, classement, club, joueur, phase de ligue, phases finales, assistant perso — aucune régression de mise en page
- [x] Aucun fichier interdit par CLAUDE.md touché ; aucun fichier Python modifié
- [x] `docs/DESIGN.md` réécrit (palette, typographie, échelle, règles d'usage des couleurs, journal des décisions)

## Comments

**01/11/2026 — implémentation**
- Mesures : 0 taille `text-[…px]` et 0 couleur hexadécimale en dur dans les 15 fichiers du périmètre ; build OK ; lint 0 erreur, 5 avertissements (préexistants : PlayerPage, TeamRoster, Simulation, CustomCompetition, PitchView).
- Contrastes (WCAG, sur `#0B0F14`) : gray-100 16,3:1, gray-400 7,9:1, gray-500 5,5:1 ; blanc sur `accent` 4,65:1 (l'ancien bleu `#3B82F6` donnait 3,7:1).
- Contrôle visuel bureau 1440 px et mobile 375 px : accueil, championnats, journée, club, joueur, phase de ligue, phases finales, assistant perso. Aucune régression de mise en page ; la journée mobile reste cassée comme avant (lot 3). Console sans erreur après rechargement.
- Écarts de rendu voulus : fond uni (image du stade retirée, fichier conservé dans `ui/public/branding/`) ; Barlow Condensed sur le titre d'accueil, le nom et la note du joueur, le nom et les chiffres de l'en-tête de club ; tailles 9 à 10,5 px portées à 11 px et 12 à 12,5 px à 13 px ; note globale du club et valeurs d'attributs en couleur de texte claire (avant : couleur d'aplat) ; vert/rouge du radar `#3ddc70`/`#e0645a` → `#3fb950`/`#f85149` (un seul vert, un seul rouge).
- `ScorersLine.jsx` supprimé (aucun importeur).
- Revue `simulafoot-reviewer` : accepter, aucun bloquant ni majeur. Mineurs corrigés : commentaire périmé (`playerName.js`), couleur du manifeste PWA et `theme-color` alignées sur le nouveau fond, `font-extrabold` (graisse absente) → `font-bold`. Mineur 4 (texte blanc des badges de note sous 4,5:1 : 4,21:1 et 2,59:1, valeurs inchangées) consigné comme exception dans `docs/DESIGN.md`, à soumettre au propriétaire au lot 5.

**01/11/2026 — passage 1 de /valider-ticket-simulafoot** (base 81f3b3d, empreinte c643af8a…)
- Expert : APPROVED. Facultatif : A1 hexadécimal du fond dans le manifeste PWA et `theme-color` (non remplaçable par un token, à réaligner si `--color-bg` change) ; A2 `Groups.jsx` garde l'ancien vert (lot 3) ; A3 graisse 500 de Barlow Condensed chargée sans usage.
- QC (`refonte-ui/01`) : VALIDÉ. Non bloquant : contraste des badges de note (exception consignée, lot 5) ; 2 259 tests passés contre 2 124 de référence (tests ajoutés par d'autres chantiers).
- Contrôle visuel non rejoué par les deux revues (pas d'accès à l'écran) ; repose sur le contrôle du développeur.
- Clôture : VALIDÉ (cloture.py decision, journal `refonte-ui/01/cloture`).
