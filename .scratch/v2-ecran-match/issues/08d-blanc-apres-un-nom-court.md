# EM-08d — Blanc après un nom court dans les buteurs du HUD (V) — 30 min (élevée)

**Status:** livré (19/11/2026), validé expert + QC

Défaut d'EM-08c relevé pendant EM-13 (captures `mesures/em13/`) : côté extérieur, « Openda      2', 7', 16' ». Le nom
a une largeur minimale de 4,5 rem (pour ne pas disparaître derrière les minutes à 1024 px) : un nom plus court que 4,5 rem
occupe quand même 4,5 rem, d'où un blanc avant les minutes.

## Comments

### 19/11/2026 — estimation et critères

- **Estimation** : analyse 5 min, développement 5 min, mesures 10 min, clôture 10 min, **total 30 min**, confiance
  élevée.
- **Correctif** : largeur minimale du nom = la plus petite de 4,5 rem et de la largeur du nom lui-même ; aucune constante
  nouvelle.
- **Critères** : écart entre la fin du nom et le début des minutes = 4 px (`gap-1`) pour tout nom non tronqué, des deux
  côtés, à 1024, 1366 et 1920 px ; troncature d'EM-08c inchangée (à 1024 px, Kvaratskhelia garde au moins 4,5 rem) ;
  `npm test`, lint 0 erreur, build OK ; suite Python 3 437 passés.

### 19/11/2026 — implémentation

- **Code** (`components/match/ScoreBlock.jsx`) : largeur minimale du nom = `min(4.5rem, largeur du texte)`, la largeur
  du texte étant mesurée à chaque rendu de la liste mémoïsée (donc à chaque but) (`textWidth`, canvas `measureText` à 12 px dans la police de l'écran,
  arrondie au pixel inférieur). Premier essai à 0,5 em par caractère écarté : blanc résiduel jusqu'à 4,3 px (« Gouiri »,
  « Abdelli »).
- **Mesures** (`mesures/em08d-mesure.cjs`, traces `em11-om-ol` et `em11-psg-havre` à 104', résultats
  `em08d-apres.json`) : écart entre la boîte du nom et les minutes 4,0 px partout ; blanc résiduel dans la boîte du nom
  ≤ 0,3 px une fois la police chargée, ≤ 1,8 px au tout premier affichage (police web pas encore chargée au moment de la
  mesure) ; avant : environ 30 px (« Openda », 4,5 rem = 72 px pour 42 px de texte) ; Kvaratskhelia à 1024 px : 72 px,
  tronqué comme en EM-08c.
- **Vérifications** : `npm test` 77 passés (aucun test node : mesure dépendante du navigateur, couverte par la mesure) ;
  lint 0 erreur, 5 avertissements ; build OK ; suite Python 3 437 passés, 0 ignoré, 14 désélectionnés.
- **À vérifier à l'écran** : buteurs extérieurs (noms courts) ; premier affichage après chargement de la page.

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `67f21d91`) : **APPROVED**. A1 [facultatif] mesure non refaite au chargement de la police web
  (blanc ≤ 1,8 px jusqu'au but suivant ; correctif possible : nouveau rendu après `document.fonts.ready`) ; A2
  [facultatif] formulation « une fois par buteur » inexacte : corrigée ci-dessus (implémentation).
- Contrôle qualité : **VALIDÉ**.
- **Décision de clôture** : VALIDÉ.
- **Durée** : estimée 30 min ; réelle environ 30 min (analyse 5, développement 10 avec un premier essai écarté, mesures
  10, clôture 5), écart 0 %. Temps machine hors total : mesures navigateur, suite complète (15 min 10).
