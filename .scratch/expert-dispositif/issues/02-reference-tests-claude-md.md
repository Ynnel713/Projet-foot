# 02: Référence de tests à jour dans CLAUDE.md

**What to build:** La règle 2 de « Validation avant de déclarer une tâche terminée » de `CLAUDE.md` compare la suite complète à un compte attendu périmé (1 648 passés, 5 ignorés, 12 désélectionnés à 44497d1). Elle donne désormais le compte mesuré le 31/10/2026 (remarque facultative A1 de l'expert au ticket 01, à la demande du propriétaire).

**Blocked by:** 01.

**Status:** livré (31/10/2026), validé expert + QC

- [x] Compte attendu = dernier compte mesuré : 2 124 passés, 13 désélectionnés, 0 ignoré (`PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider`, 31/10/2026)
- [x] La référence dit honnêtement sur quel état elle a été mesurée (arbre de travail sur 25514b5, modifications non commitées présentes)
- [x] Aucune autre modification de `CLAUDE.md`

## Comments

**31/10/2026, passage 1.** Expert : APPROVED (empreinte `b7ffd2d2`, base `25514b5`). QC : VALIDÉ. Clôture : VALIDÉ (`expert-dispositif/02/cloture`). Aucune anomalie bloquante ni réserve. Remarque facultative de l'expert : préciser au prochain recomptage « modifications non commitées présentes » et indiquer un commit propre une fois les tests en cours commités.
