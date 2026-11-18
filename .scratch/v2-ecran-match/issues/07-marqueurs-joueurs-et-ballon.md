# EM-07 — Marqueurs joueurs et ballon (V) — 120 min (moyenne)

**Status:** livré (18/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : cercles lisibles, relief subtil, équipes distinctes au premier coup d'œil.
- **Résultat** : `PlayerMarker` (couleur d'équipe, anneau, numéro à contraste garanti, relief 10 %), ballon plus visible.
- **Périmètre** : apparence ; rayon, ombre et sélection inchangés. **Composants** : `PlayerMarker`, `PitchView2`.
- **Critères** : numéro lisible à 1366×768 (capture zoomée) pour les 40 clubs de l'échantillon ; aucune équipe confondue
  avec l'autre sur les paires pathologiques ; fluidité ≥ EM-01.
- **Tests** : planche de rendu de toutes les couleurs du banc d'essai ; mesure d'images par seconde.
- **Dépendances** : EM-03, EM-05. **Risques** : coût de rendu des dégradés (utiliser un seul `<defs>` partagé).

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 25 min |
| Développement | 35 min |
| Tests (planche, pixels, fluidité) | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **120 min** |

Confiance : moyenne. Au seuil indicatif, pas au-delà. Temps machine hors total : suite complète, six passes de fluidité de 15 s, deux builds de production.

## Décision du propriétaire (18/11/2026)

« Valider tel quel » : relief = éclaircissement de 10 % en haut à gauche, dégressif, limité à l'anneau extérieur du rond (de 75 % du rayon au bord), jamais sous le numéro ; un seul `<defs>` partagé ; ballon au sol 0,4 → 0,5 m (aérien 0,6 m et contour noir de 0,1 m inchangés) ; anneau 0,12 m, rayon 1,3 m, ombre et anneau de sélection inchangés ; marqueur extrait dans `PlayerMarker`. Motif mesuré avant la proposition (`.scratch/v2-ecran-match/mesures/em07-contraste-sous-relief.mjs`) : un relief de 10 % sous le numéro ferait passer 40 couleurs sur 557 sous 4,5:1 (minimum 3,79:1, `#5a8036` à numéro blanc), 7 à 5 %.

## Critères d'acceptation (chiffrés avant le code)

- [x] C1 : relief nul sous le numéro, actif au bord. Pixels comparés avec et sans relief à 1366×768 (`em07-marqueurs.cjs`, `em07-pixels-sous-le-numero.py`) : 0 pixel modifié sur 3 408 dans la zone du numéro (≤ 0,7 R, hors recouvrement par un voisin) ; bord haut gauche (0,88 R) éclairci de 8,5 niveaux en moyenne (20 joueurs mesurables). Géométrie : masque à partir de 0,75 R = 0,975 m. Le coin du cadre d'un numéro à angles vifs (« 77 ») peut atteindre ≈ 1,0 m (estimation de l'expert, remarque A1 ; la première rédaction disait « sous 0,93 m », non mesuré) : le numéro et son liseré étant peints au-dessus du relief, le contraste n'en dépend pas ; la mesure retenue est celle des pixels (≤ 0,7 R).
- [x] C2 : contraste du numéro ≥ 4,5:1 pour les 557 couleurs (principales, secondaires, replis) : minimum 4,59:1, inchangé ; planche de rendu des 557 marqueurs (vrai marqueur cloné, variables de la règle d'EM-03, numéro « 88 »), capturée (hors dépôt) : tous les numéros lisibles.
- [x] C3 : ballon au sol de rayon 0,5 m (mesuré dans le DOM) ; aérien 0,6 m, rayon 1,3 m, anneau 0,12 m, ombre et sélection inchangés ; un clic sélectionne (anneau blanc de 0,4 m, panneau d'intention), un second désélectionne (`em07-selection.cjs`).
- [x] C4 : fluidité (banc d'EM-01, build de production, x8, 3 passes alternées de 15 s, `em07-fluidite.txt`) : médiane d'image 16,7 ms avant comme après (seuil : avant + 0,5 ms) ; script 0,90 → 0,93 ms par image (+3,7 %, seuil +15 %) ; tâche totale 3,44 → 3,79 ms (+10 %), dont style 0,30 → 0,42 ms ; 277 → 305 nœuds SVG.
- [x] C5 : 5 points de projection à 0 px et aucun défilement aux 5 tailles ; `npm test` 18/18, build OK, lint 0 erreur (5 avertissements préexistants) ; suite pytest : voir clôture.

## Comments

- 18/11/2026, implémentation. Nouveau `ui/src/components/match/PlayerMarker.jsx` : `PlayerMarker` (trait de cap, rond, relief masqué, numéro ; comportement de sélection identique), `ReliefDefs` (dégradé `v2-relief` et masque `v2-relief-ring`, posés une fois dans les `<defs>` de la pelouse), `PlayerNumber` et `PLAYER_R` déplacés depuis `V2Pitch.jsx`, qui les importe ; `BALL_R` 0,4 → 0,5. Banc de fluidité d'EM-01 réutilisé avec un lanceur pointé sur le Chromium de la session (`em07-run-bench-linux.mjs`).
- 18/11/2026, passage 1, clôture : expert APPROVED (empreinte `b04c417c`) ; QC VALIDÉ ; clôture VALIDÉ (journal, sous-étape `v2-ecran-match/07/cloture`).
  - A1 [facultatif] : « numéro sous 0,93 m » non mesuré (≈ 1,0 m au coin d'un « 77 ») ; sans effet sur le contraste (numéro peint au-dessus du relief) ; C1 reformulé dans ce ticket. Le commentaire de `RELIEF_INNER` dans `PlayerMarker.jsx` reprend encore la phrase (réserve mineure du QC) : correction reportée à EM-16 (finitions), noté dans son ticket, pour ne pas rouvrir la revue.
  - A2 [facultatif] : le relief éclaircit d'au plus 10 % la moitié intérieure de l'anneau d'équipe en haut à gauche ; la moitié extérieure (contraste avec le gazon) est intacte.
  - À surveiller à l'écran : ballon de 0,5 m au contact d'un rond sur téléphone (≈ 2 px de rayon à 844×390) ; relief quasi invisible sur les couleurs très claires (attendu).
- **Durée réelle** : environ 75 min de travail effectif (analyse 15, développement 15, tests et mesures 40, intégration 5 hors clôture), contre 120 min estimées : − 38 %. Cause : risque du relief sur le contraste chiffré avant la proposition (masque décidé d'emblée) ; banc de fluidité d'EM-01 réutilisé ; le gros du temps est passé dans la vérification par pixels (une fausse piste du décodeur PNG maison, remplacé par PIL) ; expert APPROVED et QC VALIDÉ au premier passage. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée. Temps machine hors total : suite complète (14 min 07), six passes de fluidité de 15 s, deux builds de production.
