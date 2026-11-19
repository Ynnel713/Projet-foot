# EM-12 — Chronologie : buts et cartons sur la frise (V) — 90 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC (buts seulement ; cartons avec `v2-attributs-restants/09a`)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : buts (minute, équipe) et cartons rouges (emplacement) sur l'axe du momentum.
- **Résultat** : `EventMarker` ; info-bulle (« 23' · équipe », + buteur après EM-D1) ; plus d'emoji.
- **Critères** : marqueur n'apparaît qu'à sa minute de lecture ; nombre de marqueurs = buts révélés ; cartons : composant
  prêt, testé sur propriété simulée **dans les tests seulement**, rien d'affiché tant que 09a n'existe pas.
- **Tests** : trace enregistrée ; test du composant carton avec propriétés de test.
- **Dépendances** : EM-11. **Risques** : buts rapprochés (chevauchement) → décalage vertical.

## Comments

### 19/11/2026 — décisions, estimation et critères

- **Décisions du propriétaire** (19/11/2026) : marqueur « Pastille 8 px + info-bulle » (rond de 8 px à la couleur de
  l'équipe dans la rangée des buts de son côté, à la minute du but ; info-bulle au survol ou au toucher « 23' · Nom »,
  csc indiqué ; deux buts trop proches décalés horizontalement ; l'emoji ⚽ disparaît) ; cartons : « Rien pour les
  cartons » (marqueur fait avec `v2-attributs-restants/09a`). Le périmètre se réduit aux buts.
- **Estimation** (travail effectif) : analyse 10 min, développement 25 min, tests et mesures 20 min, clôture 15 min,
  **total 1 h 10** (90 min au découpage, cartons compris), confiance moyenne. Temps machine hors total : suite complète,
  mesures navigateur.
- **Choix de détail (à confirmer à l'écran)** : écart minimal de 9 px entre deux pastilles du même côté (la seconde est
  poussée vers la droite) ; zone de toucher de 16 px autour de la pastille ; info-bulle dans la frise (au-dessus des
  barres pour l'extérieur, en dessous de la rangée pour le domicile), refermée par un second toucher ou en quittant le
  marqueur ; nom au format du HUD (sans prénom) ; minute au libellé de l'horloge.
- **Critères d'acceptation** : pastille seulement pour un but déjà lu ; nombre de pastilles = buts révélés ; côté et
  couleur de l'équipe qui marque ; aucun chevauchement (écart ≥ 9 px, mesuré sur PSG–Le Havre à 1024 px) ; info-bulle au
  survol et au toucher, contenu juste ; plus aucun emoji dans la frise ; frise toujours 72 px ; `npm test`, lint 0
  erreur, build OK ; suite Python 3 437 passés.

### 19/11/2026 — implémentation

- **Code** :
  - `utils/momentumLayout.js` : `GOAL_DOT_PX` (8), `GOAL_GAP_PX` (9), `goalMarkers(goals, width, domain)` (abscisse à la
    minute du but, 9 px au moins entre deux buts du même côté, dans la frise ; ordonnée de la rangée de l'équipe) ;
  - `MomentumTimeline.jsx` : emoji ⚽ remplacé par des pastilles (`data-goal-marker`, rôle bouton, focus clavier),
    zone de toucher de 16 px ; info-bulle HTML `GoalTip` dans la frise (texte `goalLabel` : minute de l'horloge · nom du
    HUD, csc) ouverte au survol de la souris, au focus ou au toucher (second toucher : fermeture) ; ancrée à gauche ou à
    droite près des bords ; curseur de lecture transparent au pointeur (il masquait le marqueur d'un but tout juste
    révélé : trouvé par la mesure).
- **Tests** : `utils/momentumLayout.test.js` + 3 tests (taille et position, écart de 9 px sur les buts réels 22,2' et
  23,1' à 1004 px, trois buts dans la même minute, bords) ; `npm test` 75 passés.
- **Mesures** (`mesures/em12-mesure.cjs`, traces réelles `em11-om-ol` et `em11-psg-havre`, résultats `em12-apres.json`,
  captures `em12/`, 6 cas + toucher) :
  - pastilles = buts révélés : 0 à 1', 1 à 2,05', 9 à 104' (6-3), 5 à 30' (5-0), 10 à 104' (10-0) ; côté et couleur de
    l'équipe (`--team-*-ui`) ; rayon 4 px ;
  - écart minimal entre pastilles d'un même côté : 9,00 px (PSG à 1024, 23' poussé), 12,0 px (PSG à 1366, 30'),
    17,0 px (1920) ; plus aucun emoji ; frise 72 px ;
  - info-bulle à la souris : « 2' · Openda », « 5' · Kvaratskhelia », fermée en quittant le marqueur ; au toucher
    (1024×768, dernier but près du bord droit) : « 90+4' · Kvaratskhelia », dans la zone basse, sans défilement
    horizontal, fermée au second toucher.
- **Vérifications** : lint 0 erreur, 5 avertissements ; build OK ; suite Python 3 437 passés, 0 ignoré, 14 désélectionnés.
- **Déterminisme** : affichage seul.
- **Fluidité** : non mesurée au banc : marqueurs dans la partie mémoïsée de la frise (redessinée au changement de
  minute ou de but), seule l'info-bulle dépend d'un état local.
- **À vérifier à l'écran** : taille de la pastille (8 px) et zone de toucher (16 px) sur téléphone (frise masquée sous
  500 px de haut) ; contraste de la pastille domicile claire (OM : `rgb(213, 212, 211)`).

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `e4ee2b0d`) : **APPROVED**. A1 [facultatif] la borne droite l'emporte sur l'écart de 9 px (plus de
  5 buts groupés en toute fin de frise : improbable) ; A2 [facultatif] `goalMarkers` suppose les buts dans l'ordre du
  match (vrai pour une trace du moteur).
- Contrôle qualité : **VALIDÉ** (même remarque sur la borne droite, non bloquante).
- **Décision de clôture** : VALIDÉ.
- **Durée** : estimée 1 h 10 ; réelle environ 1 h 05 de travail effectif (analyse 10, développement 25, tests et mesures
  20, clôture 10), écart − 7 %. Temps machine hors total : mesures navigateur, suite complète (14 min 56).
