# EM-03 — Règle de couleurs d'équipe + jetons (V) — 120 min (moyenne)

**Status:** livré (14/11/2026), validé expert + QC (commit `9856e48`)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : couleurs d'équipe fidèles aux clubs, toujours distinctes, numéros lisibles ; variables CSS d'équipe.
- **Problème** : bleu et or codés en dur, sans lien avec les clubs.
- **Résultat** : `teamColors.js` applique la règle de 2.2 ; variables `--team-home|away` et `-ink` posées à la racine ;
  les huit couleurs en dur remplacées.
- **Périmètre** : couleurs seulement (aucune mise en page).
- **Composants** : `utils/teamColors.js`, `MatchScreen.jsx` (variables posées en ligne à la racine de l'écran, conformément à la spec ; `index.css` inchangé, réserve A4 de l'expert), `V2Pitch.jsx`, `Momentum.jsx`.
- **Critères** : ΔE ≥ seuil entre équipes dans 100 % des paires testées (toutes les paires d'un échantillon de ≥ 40 clubs
  dont blanc/blanc, rouge/rouge, club vert, club noir) ; contraste du numéro ≥ 4,5:1 ; domicile garde sa principale dans
  100 % des cas ; résultat identique à chaque appel (pas d'aléa).
- **Tests** : `node --test` sur la règle (paires pathologiques, déterminisme).
- **Dépendances** : EM-02. **Constantes à valider avant code** : seuil ΔE (25), pas de décalage de clarté, anneau.
- **Risques** : club à la couleur proche du gazon ; un seuil trop strict dénature les clubs.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (captures, build, lint) | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : couleurs fournies par l'API depuis EM-02 ; règle en JavaScript pur testée par `node --test` ; aucune modification de l'API ni du moteur.
Temps machine, non compté : deux traces enregistrées (EM-00), suite complète Python.

## Acceptance criteria

- [x] ΔE2000 ≥ 25 entre les deux équipes dans 100 % des paires testées : les 341 kits connus de `ligue1sim.kits.CLUB_KIT`, toutes les paires ordonnées (116 281), blanc contre blanc, rouge contre rouge, club vert, club noir et même club compris ; règle appliquée : principale 90 772, secondaire 17 744, clarté décalée 7 765, dernier recours 0
- [x] Contraste du numéro ≥ 4,5:1 sur toutes les couleurs de l'échantillon (encre blanche ou noir pur, décision du propriétaire)
- [x] Domicile garde sa principale dans 100 % des cas
- [x] Résultat identique à chaque appel (fonction pure, test)
- [x] Variables `--team-home|away`, `-ink`, `-ink-edge`, `-ring`, `-ui` posées à la racine de l'écran ; plus aucune couleur d'équipe en dur (`MatchScreen`, `LineupPanel`, `V2Pitch` joueurs et bancs, `Momentum`)
- [x] Variante d'interface (`-ui`, texte des compositions et de la phase de jeu, barres du momentum) à 4,5:1 au moins sur le fond `#0b0f14` pour les 341 kits (principale et secondaire), teinte gardée (écart ≤ 20°) ; inchangée si déjà lisible (correction du rejet A1)
- [x] `npm test` (10 tests), `npm run build` OK, `npm run lint` 0 erreur et 5 avertissements (inchangé)
- [x] Captures aux 4 tailles sur trois vraies traces (PSG - Marseille, Brest - Lille, Angers - Lille, club noir)
- [x] Suite complète Python : 3 035 passés, 0 ignoré, 14 désélectionnés (inchangée : aucun fichier Python touché), 14 min 43
- [x] Durée réelle : environ 55 min pour 2 h estimées (− 54 %), correction du rejet comprise, voir `docs/agents/suivi-estimations.md`

## Comments

**14/11/2026, constantes validées par le propriétaire** (« ok EM03 je valide ») : seuil ΔE2000 25 ; pas de clarté 5 unités L* ; anneau de 0,12 m, clair sur un maillot sombre, sombre sur un maillot clair. **Écart à la spec tranché par le propriétaire** : le numéro sombre est le noir pur `#000000` et non `#0B0F14`, car avec `#0B0F14` cinq maillots rouge vif (Mayence, Courtrai, Willem II, Guinée, Mozambique) plafonnaient à 4,38 à 4,43:1.

**14/11/2026, implémentation.** `ui/src/utils/teamColors.js` : conversions sRGB et CIELAB (D65), écart CIEDE2000 (contrôlé sur sept paires de référence de Sharma, Wu et Dalal), contraste WCAG ; règle de la section 2.2 : principale de l'extérieur si l'écart avec le domicile atteint 25, sinon sa secondaire si elle se détache aussi du gazon, sinon sa teinte à clarté décalée par pas de 5 (d'abord à l'opposé du domicile), sinon blanc cassé ou noir. Liseré du numéro de la couleur opposée à l'encre (0,2 m, inchangé). Échantillon de test exporté dans `teamColors.sample.json`. **Choix à confirmer par le propriétaire** : un club sans kit connu (`known_kit` faux, gris par défaut pour 656 clubs sur 816) ou une feuille de match sans couleur (traces d'avant EM-02) garde les couleurs historiques de l'écran (bleu `#4f8ef7` à domicile, or `#e0b84a` à l'extérieur), passées par la même règle. **À regarder à l'écran** : une équipe blanche (Lille en secondaire face à Brest) et le ballon blanc ; le ballon garde son contour sombre et les joueurs leur anneau sombre (règle 5), le ballon n'est pas comparé au maillot par la règle.


**14/11/2026, passage 1 de l'expert : REJECTED.** A1 [bloquant] : la couleur d'équipe servait aussi de couleur de texte et de barres sur le fond sombre de l'écran, illisible pour les clubs sombres (PSG 1,6:1, Angers 1,1:1, contre 6:1 avant). A2 [réserve] : la principale et la couleur décalée ne sont pas comparées au gazon, et aucune couleur au ballon. A3 [facultatif] : couleurs du gazon recopiées. A4 [facultatif] : `index.css` annoncé mais non modifié.

**14/11/2026, décisions du propriétaire.** A1 : variante d'interface au contraste minimal de **4,5:1 pour le texte et les barres** (« 4,5:1 texte et barres »). A2 : **écart accepté** (« J'accepte l'écart ») : l'anneau clair ou sombre de 0,12 m reste la garantie de lisibilité sur le gazon et face au ballon ; à revérifier quand le gazon et le ballon changeront (EM-05, EM-07).

**14/11/2026, correction.** `uiColor` : même teinte, clarté montée par pas de 5 jusqu'à 4,5:1 sur `#0b0f14` (PSG `#293657` → `#737da3`, Angers `#191919` → `#808080`, Brest `#e51b33` → `#f5323e`), variables `--team-home-ui` et `--team-away-ui` lues par le texte et le momentum ; jetons, bancs et anneaux gardent la vraie couleur. A3 : `PITCH_COLORS` devient la source unique des bandes du gazon, lue par `V2Pitch`. A4 : ligne « Composants » corrigée.

**14/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (passage 2), QC VALIDÉ, clôture VALIDÉ, commit `9856e48`.** Réserve A1 du passage 2 (repli des clubs sans kit connu et des traces d'avant EM-02 sur les couleurs historiques bleu `#4f8ef7` et or `#e0b84a`) **acceptée par le propriétaire** : « Oui, bleu et or ». Facultatifs ouverts : variantes d'interface parfois identiques entre elles (A2, à reprendre avec les cartes de composition) ; gazon à revérifier à EM-05 (A3).
