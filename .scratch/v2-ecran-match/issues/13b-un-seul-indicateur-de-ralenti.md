# EM-13b — Un seul indicateur de ralenti (V) — 25 min (élevée)

**Status:** livré (19/11/2026), validé expert + QC

Doublon relevé pendant EM-14b (capture `mesures/em13/em13-ralenti.png`) : pendant un ralenti, la pastille rouge
« RALENTI » des commandes de vitesse (EM-09) et le badge d'état RALENTI à côté de la minute (EM-13, spec § Interactions)
s'affichent ensemble.

## Comments

### 19/11/2026 — décision, estimation et critères

- **Décision du propriétaire** (19/11/2026) : « Badge près de la minute » ; la pastille rouge des commandes disparaît, le
  bouton « Passer le ralenti » reste.
- **Estimation** : analyse 5 min, développement 5 min, mesures 5 min, clôture 10 min, **total 25 min**, confiance élevée.
- **Critères** : plus aucune pastille « RALENTI » dans les commandes, badge d'état RALENTI pendant le ralenti ; bouton
  « Passer le ralenti » inchangé ; HUD : hauteur inchangée, score toujours centré (écart ≤ 1 px) à 1024, 1366 et 1920 px ;
  `npm test`, lint 0 erreur, build OK ; suite Python 3 438 passés.

### 19/11/2026 — implémentation

- **Code** (`components/match/SpeedControls.jsx`) : pastille rouge « RALENTI » et sa ligne réservée retirées ;
  commentaire mis à jour. Bouton « Passer le ralenti », vitesses et clavier inchangés.
- **Mesures** (`mesures/em13b-mesure.cjs`, trace `em11-om-ol`, résultats `em13b-apres.json`, capture `em13b/`) :
  hauteur du HUD 89 px sans but (1366×768), 131 px avec 3 lignes de buteurs (1024, 1366, 1920), 69 px à 844×390 :
  mêmes valeurs qu'en EM-08c ; score centré à 0 px dans tous les cas ; pendant un ralenti : badge d'état RALENTI, 0
  pastille dans les commandes, bouton « Passer le ralenti » présent.
- **Vérifications** : `npm test` 82 passés ; lint 0 erreur, 5 avertissements ; build OK ; suite Python 3 438 passés, 0 ignoré, 14 désélectionnés.

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `9e946dc5`) : **APPROVED**, aucune anomalie ; à vérifier à l'écran : commandes moins hautes, alignées
  en haut de leur colonne (décalage vertical par rapport au score ?).
- Contrôle qualité : **VALIDÉ**.
- **Décision de clôture** : VALIDÉ.
- **Durée** : estimée 25 min ; réelle environ 20 min (analyse 5, développement 5, mesures 5, clôture 5), écart − 20 %.
  Temps machine hors total : suite complète (15 min 32).
