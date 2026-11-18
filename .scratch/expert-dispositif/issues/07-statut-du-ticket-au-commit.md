# 07: Le verrou refuse un commit dont le ticket clôturé n'est pas passé « livré »

**What to build:** Cinq tickets clôturés `VALIDÉ` et commités ont gardé le statut « implémenté (…) — en attente de /valider-ticket-simulafoot » dans leur fichier : `v2-realisme/12a` et `27b` (14/11/2026), `11p` et `11s` (16/11/2026), `10a` (18/11/2026) ; constat et correction du 18/11/2026, décision du propriétaire : « oui, corrige les statuts et crée le ticket ». Le déroulé (`docs/agents/validation-tickets.md`, ligne 7) prévoit le passage à « livré, validé expert + QC » entre la clôture et le commit, mais rien ne le vérifie (même document, ligne 60 : « Le statut écrit dans le fichier ticket n'est protégé par aucun mécanisme »).

Ajouter cette vérification à la commande `verrou` de `.claude/skills/valider-ticket-simulafoot/cloture.py`, appelée par `.claude/qc/verrou-commit.ps1` : quand la dernière entrée du journal est une clôture `VALIDÉ` du ticket `<chantier>/<id>`, le fichier `.scratch/<chantier>/issues/<id>-*.md` **dans l'index** (`git show :<chemin>`) doit porter une ligne `**Status:** livré (JJ/MM/AAAA), validé expert + QC` ; sinon le commit est bloqué, avec une raison qui donne la ligne attendue. La correction de statut faisant partie du suivi documentaire (`HORS_REVUE` contient `.scratch/`), elle ne rouvre pas la revue.

**Blocked by:** aucun.

**Status:** à faire

## Critères d'acceptation

- [ ] Commit bloqué si le fichier ticket indexé porte encore « implémenté » (ou aucune ligne de statut) après une clôture `VALIDÉ` ; raison explicite, avec la ligne attendue.
- [ ] Commit autorisé si la ligne `**Status:** livré (JJ/MM/AAAA), validé expert + QC` est présente dans l'index, quelle que soit la suite de la ligne (réserves, précisions) ; la date n'est pas comparée à celle de la clôture.
- [ ] Ticket introuvable (aucun fichier `<id>-*.md`, ou plusieurs) : blocage, raison explicite (le verrou bloque déjà sur toute vérification indéterminée).
- [ ] La vérification lit l'index, pas l'arbre de travail.
- [ ] Autotest de `cloture.py` (`_selftest`) complété : statut « implémenté » bloqué, statut « livré » accepté, ticket introuvable bloqué.
- [ ] Empreintes du contrôle d'intégrité (`.claude/qc/empreintes.json`, `integrite.ps1`) mises à jour pour `cloture.py`, selon la procédure du ticket 04.
- [ ] `docs/agents/validation-tickets.md` : ligne 60 et table de décision mises à jour (le statut est désormais vérifié au commit).
- [ ] Essai réel dans la session : un commit refusé tant que le statut n'est pas corrigé, puis accepté.

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Développement | 20 min |
| Tests | 15 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 10** |

Confiance : moyenne. Hypothèses : l'identifiant du ticket dans la clôture (`v2-realisme/10a`) suffit à retrouver son fichier ; la mise à jour des empreintes d'intégrité suit la procédure existante du ticket 04 sans difficulté.
Temps machine, non compté : suite complète (environ 20 min).
