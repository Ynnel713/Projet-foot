# EM-08e : Minute à la seconde dans le HUD

**Chantier :** `v2-ecran-match` (demande du propriétaire du 21/11/2026 : « dans le temps affiché pendant le match peut-on mettre également les secondes ? »). **Catégorie :** affichage (moteur inchangé).

**Constat vérifié (21/11/2026) :** le temps de lecture est continu (`interpolatedTick` donne une minute décimale) ; `clock()` (`ui/src/utils/matchClock.js`) l'arrondit à la minute (« 12' », « 45+2' ») pour le HUD comme pour les buteurs, la frise, le bandeau de but et le panneau d'intention.

**What to build:**
1. `clock()` renvoie en plus `precise` : temps joué de la période à la seconde, façon chronomètre télé. Temps réglementaire « mm:ss » (« 12:42 », « 64:12 ») ; temps additionnel « 45+m:ss » / « 90+m:ss », m:ss étant le temps joué au-delà de 45' dans la période (« 45+1:23 »). Secondes tronquées comme les minutes de `label`.
2. Le HUD affiche `precise` jusqu'à la vitesse de lecture `SECONDS_MAX_SPEED` incluse, `label` au-delà. La vitesse est celle choisie par le spectateur (le ralenti d'un but à x0,4 n'en change pas).
3. `label` inchangé : buteurs, frise, bandeau de but et panneau d'intention restent à la minute.

**Hors de ce ticket :** écran V1 (`render/canvas.html`, protégé) ; HUD en portrait étroit (défaut antérieur, colonne centrale à 0 px à 390 px de large, relevé dans `docs/PLAN_V2.md`).

**Attributs :** aucun.

**Constantes validées par le propriétaire le 21/11/2026 :** format du temps additionnel « 45+1:23 » (préféré à « 46:23 ») ; secondes masquées en lecture rapide (« oui ») ; `SECONDS_MAX_SPEED = 2` : secondes à x1, x1,5 et x2, masquées à x8 et x32, vitesse choisie seule (pas le ralenti) (« ok »).

**Blocked by:** aucun.

**Bloque :** aucun.

**Status:** livré (21/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 15 min |
| Tests unitaires et comportementaux | 10 min |
| Intégration et vérifications (dont vérification à l'écran) | 20 min |
| **Total (travail effectif)** | **55 min** |

Confiance : élevée. Hypothèses : fonction pure dans `matchClock.js` testée par `node --test` (`matchHud.test.js`) ; vérification à l'écran par Playwright sur une trace enregistrée (EM-00).
Temps machine, non compté : enregistrement d'une trace ; build et lint de l'UI ; suite complète.

## Acceptance criteria

- [x] Test (`node --test`) : `precise` sur 12 instants (0', réglementaire, bornes 44:59 / 45+0:00 et 89:59 / 90+0:00, 2e période, temps additionnel des deux périodes) et en direct sans 2e période connue
- [x] Test : texte du HUD à la seconde à x1, x1,5 et x2 ; à la minute à x8 et x32
- [x] Test : champs `second`, `label`, `announced` de `clock()` inchangés sur les 9 instants d'EM-08
- [x] Écran (Playwright, trace réelle) : minute lue à 1366×768 (x1, x2, x8), 1024×768, 844×390 ; aucun débordement du HUD, aucune erreur de console
- [x] `npm test` OK ; `npm run build` OK ; `npm run lint` : 0 erreur, 5 avertissements (inchangé)
- [x] Suite complète : compte comparé à l'attendu de `CLAUDE.md`
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] À vérifier à l'écran par le propriétaire : lisibilité du chrono à x1 et x2, passage à la minute en cliquant x8

## Réalisation (21/11/2026)

- `ui/src/utils/matchClock.js` : `SECONDS_MAX_SPEED = 2` ; champ `precise` de `clock()` (fonction `chrono` : minutes décimales en « m:ss », marge de 1e-6 s contre l'arrondi flottant, 12.7 × 60 = 761,999…) ; `hudClockText(time, speed)`.
- `ui/src/components/match/MatchHud.jsx` : la minute du HUD passe par `hudClockText(time, playback.speed)`.
- `ui/src/utils/matchHud.test.js` : test d'EM-08 limité aux trois champs d'avant (inchangés), deux tests ajoutés.

**Vérification à l'écran (trace réelle `em08e`, PSG 1-0 OM, graine 1, temps additionnel [1, 6], enregistrée par `scripts/record_v2_trace.py`, hors dépôt ; script Playwright hors dépôt) :**

| Instant, vitesse, écran | Texte affiché | Largeur | Débordement HUD |
|---|---|---|---|
| 12,7', x1, 1366×768 | 12:42 | 51,7 px | non |
| 45,5', x1, 1366×768 | 45+0:30 | 73,6 px | non |
| 45,5', x8, 1366×768 | 45+1' | 48,4 px | non |
| 70,3', x2, 1366×768 | 69:18 | 51,7 px | non |
| 96', x1,5, 1024×768 | 90+5:00 | 73,6 px | non |
| 96', x1, 844×390 | 90+5:00 | 55,2 px | non |

Aucune erreur de console. À 390×844 (portrait), le HUD déborde déjà avant ce ticket (486 px pour 390, colonne centrale à 0 px, même mesure à x32 avec « 90+6' ») : défaut antérieur, inchangé.

**Écart de lecture à noter :** en temps additionnel, le libellé à la minute compte la minute entamée (« 45+1' » de 45:00 à 45:59, règle de `v2engine.added_time.display_minute`) alors que le chrono compte le temps écoulé (« 45+0:30 ») ; passer de x2 à x8 fait donc lire « 45+0:30 » puis « 45+1' ». En temps réglementaire, les deux concordent (« 12:42 » / « 12' »).

**Vérifications :** `npm test` 84/84 ; `npm run build` OK ; `npm run lint` 0 erreur, 5 avertissements (inchangé) ; suite complète 3 441 passés, 0 ignoré, 14 désélectionnés (conforme à `CLAUDE.md`), 15 min 51. Déterminisme : fonctions pures sans hasard ni horloge, aucun effet sur le moteur ni la trace.

**Durée :** estimée 55 min ; réelle environ 50 min de travail effectif (analyse 10, développement 10, tests 10, intégration et vérifications 20), à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée ; écart − 9 %. Temps machine hors total : trace enregistrée (2 min 17), mesures Playwright, suite complète (15 min 51).

## Comments

- **21/11/2026, passage 1** — Expert : `APPROVED` (empreinte e45273b4…). Avant le QC, commentaire d'en-tête de `MatchHud.jsx` rejustifié (ligne trop longue), ce qui change l'empreinte : nouveau passage de l'expert.
- **21/11/2026, passage 2** — Expert : `APPROVED` (empreinte 170b8efa…). QC : `VALIDÉ`. Clôture journalisée : `VALIDÉ`. Anomalies bloquantes : aucune.
  - A1 facultatif (expert) : passage en temps additionnel à 45' jouées même avant l'annonce des minutes en direct ; comportement hérité de `label`, rien à corriger ici.
  - Remarque non bloquante (QC) : écart « 45+0:30 » (x2) / « 45+1' » (x8), documenté.
