# 01: Étendre le bouton "Animation" aux écrans poules et tableau

**What to build:** le bouton "Animation" qui ouvre l'animation sans révéler le score (déjà livré le 23/10/2026 sur l'écran championnat, `Simulation.jsx`) est étendu aux deux écrans qui ont le même défaut aujourd'hui — poules (`Groups.jsx`, `GroupMatchRow`) et tableau à élimination (`Bracket.jsx`, `TieCard`/`SingleLegRow`). Chacun réutilise déjà `LiveButton` directement (pas `MatchRow`) : même motif à appliquer, `AnimationButton`/`AnimationDialog` déjà construits et réutilisables tels quels.

**Blocked by:** None.

**Status:** livré (02/11/2026), validé expert + QC

- [ ] Sur l'écran poules, un bouton "Animation" ouvre l'animation du match sans jamais afficher son score au préalable
- [ ] Sur l'écran tableau, idem pour un match déjà joué
- [ ] Aucune régression sur les boutons LIVE existants des deux écrans
- [ ] Build + lint UI : 0 erreur (avertissements préexistants seulement)

**Note :** fichiers UI uniquement (`ui/src/routes/Groups.jsx`, `ui/src/routes/Bracket.jsx`), aucun fichier protégé `CLAUDE.md` touché.

**Mise à jour (23/10/2026) :** le propriétaire a demandé séparément que le bouton LIVE lui-même ouvre directement l'animation (au lieu du live textuel). Une fois corrigé, LIVE fait exactement ce que ce ticket demandait pour un match déjà joué — plus besoin d'un bouton Animation séparé sur ces deux écrans, ça aurait été redondant. Ticket fermé sans suite plutôt que livré tel quel.

## Comments

**02/11/2026 — reprise pour commit**
- Constat : la modification « LIVE ouvre directement l'animation » (note du 23/10/2026) n'a jamais été commitée ; elle est restée dans l'arbre de travail (`MatchRow.jsx`, `Groups.jsx`, `Bracket.jsx`, `Simulation.jsx`), désactivée en V1 (`LIVE_AND_ANIMATION_ENABLED = false`, commit `70ca9d1`). Le propriétaire demande de la commiter à part avant le lot 3 de la refonte UI qui refait ces fichiers (« Oui, commit à part »).
- Critères retenus pour cette validation (ceux de la note du 23/10, qui remplacent les cases ci-dessus, abandonnées) : (1) LIVE d'un match déjà joué ouvre l'animation (`AnimationDialog`) sans afficher le score au préalable, sur les écrans championnat, poules et tableau ; (2) LIVE d'un match pas encore joué simule la journée / le tour puis ouvre l'animation de ce match ; (3) écran championnat : bouton Animation sur les lignes de match jouées ; (4) avec le drapeau à `false`, aucun bouton LIVE ni Animation affiché, aucune régression ; (5) build OK, lint 0 erreur.

**02/11/2026 — passage 1 de /valider-ticket-simulafoot** (base 0ced8dd, empreinte a0d41bec…)
- Expert : APPROVED. Facultatif : A1 scores floutés visibles derrière « Lancement du live… » avant l'ouverture (ordre préexistant) ; A2 branche `tab`/`replay` morte dans `openPitch` ; A3 libellés de `LiveButton` hérités du live textuel. À reprendre au lot 3 de la refonte UI.
- QC (`animation-sans-spoiler-partout/01`) : VALIDÉ. Non bloquant : match absent de `matches_played` (improbable) ; rendu non vérifié à l'écran, pas de test JS.
- Clôture : VALIDÉ (cloture.py decision, journal `animation-sans-spoiler-partout/01/cloture`).
