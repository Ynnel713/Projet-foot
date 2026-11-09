# KM-01 — Extraction des couleurs et correspondance des clubs (S) — 120 min (moyenne)

**Status:** livré (09/11/2026), validé expert + QC

Chantier : `.scratch/kits-maillots/spec.md`.

- **Objectif** : tirer de chaque image de maillot deux couleurs (principale, secondaire) pour les maillots domicile,
  extérieur et troisième, et associer chaque fichier à son club du jeu.
- **Périmètre** : script et table de correspondance ; le jeu n'est pas modifié (intégration : KM-02).
- **Composants** : `scripts/extract_kit_colors.py`, `tests/test_extract_kit_colors.py`.
- **Critères** : 3 maillots synthétiques (uni, rayé rouge/blanc, rouge ombré + reflet rose) donnent les couleurs
  attendues ; la table ne vise que des clubs existants, sans doublon ; extraction déterministe (deux passages, même
  JSON) ; planche relue par le propriétaire.

## Réalisé

- Lecture directe des 16 archives (aucune extraction) ; blocs de texte PNG retirés avant lecture (un fichier a des
  métadonnées que Pillow refuse par sécurité ; la limite de Pillow reste en place).
- Méthode : maillot réduit à 140 px, pixels opaques, palette médiane à 16 couleurs, teintes fusionnées sous un écart
  CIELAB de 22 (ombrage), représentant = teinte la plus franche du groupe ; secondaire = plus grande surface (≥ 4 %)
  distincte de la principale (écart ≥ 30, et pas la même teinte à moins de 35 de clarté : évite le « rose » d'un rouge).
- Table `CLUB_BY_STEM` : 184 fichiers -> 185 clubs (Heidenheim est en double dans les données), correspondance
  automatique relue à la main (10 corrections : stvv, wba, wolves, psg, rennes, heidenheim, az, nec, qpr, hsv).
  6 clubs des packs absents des données, ignorés : Cremonese, NAC Breda, AVS, Real Oviedo, Eyüpspor, Karagümrük.
- Limite connue : sur les motifs fins mêlés (treillis rouge du PSG, rayures du Barça), la secondaire sort plus sombre
  (bordeaux) que la vraie couleur. À arbitrer en KM-02 (garder la secondaire actuelle de `kits.py` quand elle existe ?).

## Acceptance criteria

- [x] Maillots synthétiques (uni, rayé, rouge ombré + reflet rose) : couleurs attendues (`tests/test_extract_kit_colors.py`)
- [x] Table : 185 clubs existants, sans doublon
- [x] Déterministe : deux extractions, JSON identique (SHA-256 `9faf7afd…c023d`)
- [x] Planche relue par le propriétaire (09/11/2026) : choix « Tout extraire » pour les secondaires des maillots à motif
- [x] Suite complète : 2 618 passés, 14 désélectionnés (2 613 + 5 tests ajoutés)

## Durée

Estimée 120 min, confiance moyenne. Réelle (estimée, non chronométrée) : environ 135 min (+ 13 %) ; réglage des seuils
sur échantillon et bloc PNG géant non prévus. Temps machine hors total : extractions 2 × 2 min, suite 71 min.

## Comments

- 09/11/2026, revue commune `kits-maillots/01-03+v2-ecran-match/02` (EM-02, KM-01, KM-02, KM-03) :
  - passage 1 : expert **REJECTED** (A1 bloquant : `match_kit_colors` laissait deux équipes de la même couleur en V1 pour
    les maillots unis, ex. Arsenal / Manchester United) ; QC VALIDÉ ; clôture REFUSÉ.
  - correctifs A1 à A5 appliqués par délégation du propriétaire (« Considère que je valide automatiquement toutes tes
    recommandations et celles des experts », 05/11/2026) : repli sur le vrai maillot extérieur en cas de clash, critère
    EM-02 annoté, test du module indépendant des fins de ligne, docstring, import de Pillow local.
  - passage 2 : expert APPROVED ; QC **REFUSÉ** (import de Pillow placé après `Image.new` dans `contact_sheet`).
  - passage 3 : expert **APPROVED** (A1 facultatif : archives ouvertes par `contact_sheet` jamais fermées) ; QC
    **VALIDÉ** ; clôture **VALIDÉ** (empreinte `1878931e…b827`, base `5bd30e1`). Suite : 2 626 passés, 14 désélectionnés.
