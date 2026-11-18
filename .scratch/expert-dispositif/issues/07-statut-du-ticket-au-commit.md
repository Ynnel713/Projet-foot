# 07: Le verrou refuse un commit dont le ticket clôturé n'est pas passé « livré »

**What to build:** Cinq tickets clôturés `VALIDÉ` et commités ont gardé le statut « implémenté (…) — en attente de /valider-ticket-simulafoot » dans leur fichier : `v2-realisme/12a` et `27b` (14/11/2026), `11p` et `11s` (16/11/2026), `10a` (18/11/2026) ; constat et correction du 18/11/2026, décision du propriétaire : « oui, corrige les statuts et crée le ticket ». Le déroulé (`docs/agents/validation-tickets.md`, ligne 7) prévoit le passage à « livré, validé expert + QC » entre la clôture et le commit, mais rien ne le vérifie (même document, ligne 60 : « Le statut écrit dans le fichier ticket n'est protégé par aucun mécanisme »).

Ajouter cette vérification à la commande `verrou` de `.claude/skills/valider-ticket-simulafoot/cloture.py`, appelée par `.claude/qc/verrou-commit.ps1` : quand la dernière entrée du journal est une clôture `VALIDÉ` du ticket `<chantier>/<id>`, le fichier `.scratch/<chantier>/issues/<id>-*.md` **dans l'index** (`git show :<chemin>`) doit porter une ligne `**Status:** livré (JJ/MM/AAAA), validé expert + QC` ; sinon le commit est bloqué, avec une raison qui donne la ligne attendue. La correction de statut faisant partie du suivi documentaire (`HORS_REVUE` contient `.scratch/`), elle ne rouvre pas la revue.

**Blocked by:** aucun.

**Décision du propriétaire (18/11/2026), clôture qui ne désigne aucun fichier ticket :** « Selon le chantier ». Si le dossier `.scratch/<chantier>/issues/` n'existe ni sur le disque ni dans l'index (`fusion/...`, `projet/...`, `backlog-v2/...`), le statut n'est pas vérifié. S'il existe, le fichier `<id>-*.md` doit être unique et porter « livré », sinon blocage. Une clôture de lot dans un chantier existant (`v2-realisme/25-26`) prend désormais un préfixe hors chantier (`projet/...`).

**Status:** livré (18/11/2026), validé expert + QC

## Critères d'acceptation

- [x] Commit bloqué si le fichier ticket indexé porte encore « implémenté » (ou aucune ligne de statut) après une clôture `VALIDÉ` ; raison explicite, avec la ligne attendue.
- [x] Commit autorisé si la ligne `**Status:** livré (JJ/MM/AAAA), validé expert + QC` est présente dans l'index, quelle que soit la suite de la ligne (réserves, précisions) ; la date n'est pas comparée à celle de la clôture.
- [x] Ticket introuvable (aucun fichier `<id>-*.md`, ou plusieurs) : blocage, raison explicite (le verrou bloque déjà sur toute vérification indéterminée).
- [x] La vérification lit l'index, pas l'arbre de travail.
- [x] Autotest de `cloture.py` (`_selftest`) complété : statut « implémenté » bloqué, statut « livré » accepté, ticket introuvable bloqué.
- [x] Empreintes du contrôle d'intégrité (`.claude/qc/empreintes.json`, `integrite.ps1`) mises à jour pour `cloture.py`, selon la procédure du ticket 04.
- [x] `docs/agents/validation-tickets.md` : ligne 60 et table de décision mises à jour (le statut est désormais vérifié au commit).
- [x] Ticket introuvable dans un chantier existant, ou fichier ticket retiré de l'index alors que son dossier existe sur le disque : blocage ; clôture hors chantier (`fusion/...`) : commit autorisé (décision du propriétaire).
- [x] Banc `test-verrou.sh` : 45 scénarios sur 45 (39 existants inchangés ; I39 implémenté, I40 livré non indexé, I41 fichier retiré de l'index, I42 doublon, I43 livré suivi de précisions, I44 hors chantier).
- [x] Essai réel dans la session : un commit refusé tant que le statut n'est pas corrigé, puis accepté (voir Comments, 18/11/2026, clôture).

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

## Comments

- 18/11/2026, implémentation. `cloture.py` : fonction `raison_statut` (pure, testée par `--selftest`), appelée en fin de `verrou()` avec la liste de l'index (`git ls-files`) et le contenu indexé (`git show :<chemin>`) ; la première ligne `**Status:**` du fichier doit commencer par `**Status:** livré (JJ/MM/AAAA), validé expert + QC`. Le banc a révélé un contournement de la première version (retirer de l'index le seul fichier du chantier le faisait passer pour « hors chantier ») : le chantier existe désormais si son dossier `issues/` est présent sur le disque ou dans l'index. `empreintes.json` régénéré par `integrite.ps1 -Action MettreAJour` (seule l'empreinte de `cloture.py` change ; les dates `maj` des 7 entrées sont réécrites par la procédure). Documentation : `docs/agents/validation-tickets.md` (verrou, banc, table, limites), `SKILL.md` du skill de clôture, `CLAUDE.md` (section verrou).
- 18/11/2026, passage 1, clôture : expert APPROVED (empreinte `e149d16d`) ; QC VALIDÉ ; clôture VALIDÉ (journal, sous-étape `expert-dispositif/07/cloture`). A1 facultatif (non bloquant) : `integrite.ps1 -Action MettreAJour` réécrit la date `maj` de toutes les entrées alors qu'une seule empreinte change ; bruit de diff, hors périmètre.
- 18/11/2026, essai réel : premier `git commit` refusé par le hook avec « statut du ticket non passé à « livré » dans l'index (… « **Status:** implémenté (18/11/2026) — en attente de /valider-ticket-simulafoot ») ; ligne attendue : « **Status:** livré (JJ/MM/AAAA), validé expert + QC » » ; statut corrigé et indexé, commit accepté (ce commit).
- **Durée réelle** : environ 45 min de travail effectif (analyse 10, développement 10, tests 10, intégration et vérifications 15), contre 80 min estimées après l'extension du périmètre (70 au départ) : − 44 %. Cause : changement concentré dans une fonction pure de `cloture.py`, banc existant réutilisable en ajoutant six scénarios, expert APPROVED et QC VALIDÉ au premier passage. Durée estimée à l'horloge de la session hors attentes machine et réponse du propriétaire, non chronométrée. Temps machine hors total : suite complète (14 min 06, 3 415 passés), banc 45 scénarios (deux passes).
