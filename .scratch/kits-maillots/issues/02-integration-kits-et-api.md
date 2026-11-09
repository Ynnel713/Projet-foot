# KM-02 — Couleurs réelles dans kits.py et l'API V2 (S) — 120 min (moyenne)

**Status:** livré (09/11/2026), validé expert + QC

Chantier : `.scratch/kits-maillots/spec.md`. Dépend de KM-01.

- **Décision du propriétaire (09/11/2026)** : « Tout extraire » : les couleurs extraites remplacent les couleurs actuelles
  pour les 185 clubs couverts, y compris les secondaires assombries des maillots à motif fin (PSG, Barça).
- **Objectif** : le jeu (V1 et V2) utilise les couleurs réelles 2025/26 ; l'API V2 expose aussi le maillot extérieur.
- **Composants** : `src/ligue1sim/kit_colors_data.py` (généré, `--module`), `src/ligue1sim/kits.py` (`Kit` gagne
  `away_primary` / `away_secondary`, fusion), `api/routers/v2.py` (`away_color`, `away_secondary`),
  `scripts/extract_kit_colors.py` (`write_module`), tests.
- **Critères** : PSG, OM, Lens prennent leurs couleurs extraites (domicile et extérieur) ; club hors packs inchangé ;
  motif dessiné conservé ; module régénéré à l'octet près ; suite complète sans échec.

## Réalisé

- `kit_colors_data.py` : 185 clubs, domicile et extérieur (tous ont un maillot extérieur), trié, généré par le script.
- `kits.py` : fusion après la table manuelle ; 212 clubs ont désormais un kit (160 avant, 52 nouveaux : Championship,
  Süper Lig, Metz, Nantes…). `match_kit_colors` (V1) inchangé dans sa règle : il utilise les nouvelles couleurs ; la
  règle de contraste avec le maillot extérieur reste pour EM-03.
- Effet attendu : les rendus V1 (pastilles, maillots SVG, animation) changent de couleur pour ces clubs.
- Tests : `tests/test_kits_extracted.py` (4) ; test d'EM-02 adapté (couleurs du PSG désormais extraites, clés
  `away_color` / `away_secondary`).

## Acceptance criteria

- [x] PSG, OM, Lens : couleurs extraites, domicile et extérieur ; motif conservé (`center_stripe`, `horizontal_stripes`)
- [x] Club hors packs inchangé (AEK Athens) ; club inconnu : gris par défaut
- [x] `/api/v2/lineup` : `away_color`, `away_secondary` (PSG `#f1f1f1` / `#c51c1c`)
- [x] Module régénéré à l'octet près (`test_generated_module_is_reproduced_exactly`)
- [x] Suite complète : 2 622 passés, 14 désélectionnés (50 min 49 s) = 2 618 + 4 tests ajoutés ; aucun test V1 cassé

## Durée

Estimée 120 min, confiance moyenne. Réelle (estimée, non chronométrée) : environ 75 min (− 38 %) ; écart > 30 % : la
fusion par un module généré a évité de réécrire la table de `kits.py`, et aucun test V1 n'a dépendu des couleurs.
Temps machine hors total : suite 51 min.

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
