# 02: Nettoyages après la clôture du ticket 01 (Moyenne FM)

**What to build:** Les trois améliorations facultatives relevées par l'expert et le contrôle qualité à la clôture du ticket 01 (commit f16dd8a), sans changer aucune note.

**Demande du propriétaire (31/10/2026) :** « Yes, clean up ».

**Status:** livré (31/10/2026), validé expert + QC

## Critères d'acceptation

- [x] Commentaire de `players._FM_LEVELS` à jour : niveaux validés par le propriétaire le 31/10/2026 (plus « à valider »).
- [x] Docstring de `scripts/compute_moyenne_fm.py` : distribution 19-91, comme le rapport et le critère du ticket 01 (au lieu de « ~35-91 »).
- [x] `compute_moyenne_fm` ne plante pas si une famille n'a aucune note de référence ≥ 30 : ses joueurs gardent leur Moyenne joueur ; test dédié (`rank_rescale` renvoie {} sur référence vide).
- [x] Aucune note modifiée : `data/joueurs.xlsx` non touché ; recalcul sur une copie du classeur actuel : « Moyenne FM » identique (pandas `equals` : True).
- [x] Suite complète verte : 2 121 passés, 4 ignorés (Node absent, `test_canvas_html.py:463`), 13 désélectionnés, 0 échec (31/10/2026).

## Comments

**31/10/2026 — /valider-ticket-simulafoot** (empreinte a9452fd6…)
- Expert : APPROVED. Facultatif : total de tests 2 121 + 4 ignorés contre 2 124 de référence (hors ticket).
- QC : VALIDÉ. Même remarque non bloquante.
- Clôture : VALIDÉ (journal `donnees-moyenne-fm/02/cloture`).
