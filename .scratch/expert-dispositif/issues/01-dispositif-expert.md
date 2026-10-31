# 01: Dispositif d'expertise indépendante à la clôture des tickets

**What to build:** Aucun ticket Simulafoot ne peut être déclaré validé sans un verdict favorable d'un sous-agent `expert` indépendant (réalisme, physique, tactique, numérique) et un contrôle qualité favorable. Le dispositif réutilise le QC existant (`controle-qualite`, `/valider-etape`, journal, verrou de commit) sans le dupliquer, et s'appelle par le skill `/valider-ticket-simulafoot`. Ce commit range aussi dans git la configuration Claude du projet qui était restée hors suivi (`CLAUDE.md`, agents `simulafoot-*`, skill `to-tickets`, `docs/agents/`), à la demande du propriétaire (31/10/2026).

**Blocked by:** None (can start immediately).

**Status:** livré (31/10/2026), validé expert + QC

- [x] Agent `expert` en lecture seule réelle : outils Read, Grep, Glob seulement, sans shell, sans MCP, sans écriture (`.claude/agents/expert.md`)
- [x] Contexte indépendant : l'expert ne reçoit que le dossier de revue (ticket, base, fichiers, diff, empreinte, tests), jamais l'historique
- [x] Verdict parmi APPROVED, APPROVED_WITH_RESERVATIONS, REJECTED, INCONCLUSIVE, au format imposé (en-tête lisible par script, 5 sections)
- [x] Calculs : l'expert demande, le skill exécute hors dépôt avec une empreinte du dépôt avant et après ; aucun MCP Python n'est installé (dit, pas simulé)
- [x] Seul APPROVED (ou réserves acceptées par le propriétaire) + QC VALIDÉ donne une clôture VALIDÉ ; rapport absent, incomplet, d'un autre ticket ou d'un code modifié depuis la revue → jamais VALIDÉ (`cloture.py --selftest`)
- [x] Le verrou de commit refuse tout commit sans clôture VALIDÉ encore vraie (`cloture.py verrou`, banc `tests/test-verrou.sh`)
- [x] `expert.md` et `cloture.py` couverts par le contrôle d'intégrité (`.claude/qc/integrite.ps1`)
- [x] Règle de clôture dans `CLAUDE.md`, documentation dans `docs/agents/validation-tickets.md`
- [x] Tests d'acceptation sur l'agent réel (31/10/2026) : T2 physique REJECTED, T3 tactique REJECTED, T4 esthétique APPROVED, T5b mesure impossible INCONCLUSIVE, T9 aucun outil d'écriture
- [x] Aucun fichier moteur touché ; suite de tests inchangée

## Comments

**31/10/2026, passage 1.** Expert : APPROVED (empreinte `baa8d820`, base `3fdc067`). QC : VALIDÉ. Clôture : VALIDÉ (`expert-dispositif/01/cloture`). Aucune anomalie bloquante ni réserve. Remarques facultatives de l'expert : référence de tests de `CLAUDE.md` périmée (1 648 vs 2 124 passés) ; `cloture.py decision` ne se replace pas à la racine du dépôt ; `docs/` et `.scratch/` passent le verrou sans revue (choix documenté, n'y jamais mettre de script appelé par le verrou ou le moteur) ; liste des fichiers protégés de `to-tickets` différente de celle de `CLAUDE.md`. Tests : suite 2 124 passés, 13 désélectionnés ; selftest OK ; banc du verrou 36/36.
