# 02b: Garde du registre : contexte en argument nommé, poids comparés en nombre

**Chantier :** `v2-attributs-contextes` (ADR 0002, point 6). **Priorité :** P2. **Catégorie :** tests.

**Origine :** améliorations facultatives A2 et A3 de l'expert à la clôture du ticket 02 (17/11/2026), validées par le propriétaire le 17/11/2026 (« je valide ces ajustements »).

**What to build:** dans `tests/test_v2engine_rayon_attributs.py` :
- A2 : la vérification « un effet, un contexte » voit aussi un appel `contextual_rating(p, contexte=X)` en argument nommé (aujourd'hui ignoré, donc un contexte pouvait être relu hors de sa fonction sans échec) ; un contexte nommé non littéral est classé inconnu, donc refusé ;
- A3 : la vérification de la carte compare les poids en nombre, arrondis à trois décimales (1/3 s'écrit « 0,333 »), au lieu du texte `f"{w:g}"` (« 0,333333 »).

**Hors de ce ticket :** A1 (inventaire informatif des modules lecteurs), non retenu ; tout changement du moteur.

**Attributs :** aucun.

**Blocked by:** 02.

**Status:** livré (17/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 5 min |
| Développement | 10 min |
| Tests unitaires et comportementaux | 10 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **35 min** |

Confiance : élevée. Hypothèses : deux fonctions de la garde, un cas négatif chacune ; moteur inchangé.
Temps machine, non compté : suite complète.

## Acceptance criteria

- [x] Contexte passé en argument nommé compté par la vérification 4, avec cas synthétique (littéral et non littéral)
- [x] Poids comparés en nombre à trois décimales, avec cas synthétiques (1/3 bien écrit accepté, arrondi insuffisant et poids faux refusés)
- [x] Paragraphe « Garde automatique » de la carte complété
- [x] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md`

## Réalisation (17/11/2026)

- **A2** : `_context_uses` lit le contexte en argument positionnel ou nommé (`contexte=`) ; absent ou non littéral : « contexte non littéral », refusé par `effect_conflicts`. Test `test_a_context_passed_by_keyword_is_counted`.
- **A3** : `undocumented_contexts` lit le poids écrit après chaque attribut (`_documented_weight`, expression régulière ancrée sur un début de mot) et le compare au poids du registre arrondi à `WEIGHT_DECIMALS` = 3. Test `test_the_documentation_check_compares_weights_as_numbers` (1/3 écrit « 0,333 » accepté ; « 0,33 » et un poids faux refusés). Premier essai : ancre trop stricte (refusait l'espace avant l'attribut), corrigée avant la suite.
- **Carte** : points 1 et 4 du paragraphe « Garde automatique » complétés. `CLAUDE.md` : attendu 3 374.
- **Moteur inchangé** (aucun fichier de `v2engine/` touché) : pas de nouvelle empreinte nécessaire.
- **Suite complète** (17/11/2026) : 3 374 passés, 0 ignoré, 14 désélectionnés (14 min 36) ; 3 372 + 2.
- **Durée** : estimée 35 min ; réelle environ 30 min (− 14 %). Temps machine hors total : suite complète.

## Comments

- **17/11/2026, passage 1** : expert APPROVED ; QC VALIDÉ ; clôture journalisée VALIDÉ (empreinte `c785dc631529…`). Aucune anomalie bloquante. Amélioration facultative de l'expert : A1, `_documented_weight` ne lit que la première mention « Attribut nombre » d'une ligne (à reprendre si la colonne de description de la section « Contextes » cite un jour des attributs suivis de nombres ; correctif : restreindre la recherche à la colonne des poids).
