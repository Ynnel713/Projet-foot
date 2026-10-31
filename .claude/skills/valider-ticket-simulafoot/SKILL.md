---
name: valider-ticket-simulafoot
description: Validation de clôture d'un ticket Simulafoot implémenté — revue indépendante par le sous-agent expert (réalisme, physique, tactique, numérique), contrôle qualité existant (/valider-etape), confrontation des deux, verdict de clôture journalisé. Seul chemin vers le statut « livré, validé ». Utilise sur /valider-ticket-simulafoot, « valide le ticket », « clôture le ticket », ou dès qu'un ticket `.scratch/<chantier>/issues/NN-*.md` est implémenté et testé, avant tout commit.
---

Un ticket n'est **validé** que si l'expert rend `APPROVED` (ou `APPROVED_WITH_RESERVATIONS` avec réserves acceptées explicitement par le propriétaire) **et** le contrôle qualité rend `VALIDÉ`. Tout le reste laisse le ticket non validé. Ton appréciation de développeur ne remplace aucun des deux verdicts.

`S` désigne `.claude/skills/valider-ticket-simulafoot/cloture.py` ; lance-le avec `python -I S ...` depuis la racine du dépôt. `SCRATCH` désigne le répertoire scratchpad de la session (hors dépôt).

## 1. Identifier le ticket et son état

- Identifiant `<chantier>/<NN>` (ex. `v2-collectif/24`) et fichier `.scratch/<chantier>/issues/<NN>-*.md`. Jamais inventé : s'il est ambigu, demande.
- Statut attendu : `implémenté (JJ/MM/AAAA) — en attente de /valider-ticket-simulafoot`. Si l'implémentation n'est pas terminée ou si la suite de tests n'a pas été passée, arrête-toi et dis ce qui manque.

## 2. Constituer le dossier de revue (dans SCRATCH, jamais dans le dépôt)

- `BASE` : la révision d'avant le ticket (`git log` pour la lire, jamais de mémoire).
- `FICHIERS` : les seuls fichiers du ticket. Le dépôt contient souvent des modifications préexistantes non liées : ne les inclus pas ; en cas de doute, demande.
- `SCRATCH/<NN>-diff.patch` : `git diff BASE -- FICHIERS` ; liste en plus les fichiers nouveaux non suivis (l'expert les lira).
- `EMPREINTE` : `python -I S empreinte --base BASE FICHIERS`.
- `SCRATCH/<NN>-tests.txt` : sortie de `PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider` sur l'état actuel (compte passés / ignorés / désélectionnés), et des mesures déjà faites pour le ticket.

## 3. Revue experte (contexte indépendant)

Lance le sous-agent `expert` avec l'outil Agent (`subagent_type: "expert"`, jamais `fork`), avec **uniquement** : identifiant et chemin du ticket, BASE, FICHIERS, chemin du diff, EMPREINTE, chemin du fichier de tests, et la consigne « Revue de clôture, rapport au format imposé ». Ni l'historique de la conversation, ni ton avis sur le code.

Quand le résultat revient :
- S'il contient `DEMANDE DE VÉRIFICATIONS` : traite chaque demande (étape 4), puis renvoie les résultats au même agent (SendMessage vers son identifiant) ; si la reprise est impossible, relance un `expert` neuf avec le dossier + la demande + les résultats.
- Sinon, enregistre le rapport **tel quel** dans `SCRATCH/<NN>-expert-<n>.md` (`n` = numéro de passage).
- Un appel qui échoue, ou un texte sans les lignes `Ticket :`, `Empreinte :`, `Verdict :`, n'est pas un verdict : ne le complète pas toi-même, relance l'expert une fois, sinon la clôture sera BLOQUÉ (étape 6 le constate).

## 4. Exécuter une vérification demandée (protocole sécurisé)

L'expert n'exécute rien ; c'est toi qui exécutes, à ces conditions :
1. Commande d'un script ou test **existant** du dépôt, lancée telle que demandée. Si elle exige un script nouveau, écris-le dans SCRATCH (jamais dans le dépôt, sans dépendance téléchargée, sans réseau) et transmets son chemin à l'expert pour qu'il le lise.
2. Avant et après : `python -I S empreinte` (tout le dépôt). Lance Python avec `PYTHONDONTWRITEBYTECODE=1` et pytest avec `-p no:cacheprovider`.
3. Si les deux empreintes diffèrent, la vérification a modifié le dépôt : signale-le, ne transmets pas le résultat comme preuve, restaure seulement après accord du propriétaire.
4. Transmets à l'expert la commande exacte, la sortie brute et les deux empreintes.

Une commande qui écrit dans le dépôt par conception, ou qu'on ne peut pas lancer, n'est pas exécutée : dis-le à l'expert, qui conclura en conséquence.

## 5. Contrôle qualité existant

Appelle le skill `valider-etape` (outil Skill), sous-étape = identifiant du ticket, sur le même diff, avec les critères d'acceptation du ticket. Ne lui transmets pas le rapport de l'expert : les deux revues restent indépendantes. Note son verdict (`VALIDÉ` / `REFUSÉ` / `BLOQUÉ`) ; il le journalise lui-même.

## 6. Décision de clôture

```
python -I S decision --ticket <id> --rapport SCRATCH/<NN>-expert-<n>.md --qc <verdict QC> --base BASE FICHIERS [--reserves-acceptees]
```

- `--reserves-acceptees` seulement si le propriétaire a accepté **dans cette conversation**, réserve par réserve, celles du rapport (cite ses mots dans le ticket). Jamais de ta propre initiative.
- Le script recalcule l'empreinte : si le code a changé depuis la revue, le rapport ne vaut plus et la clôture est BLOQUÉ. Il lit le verdict QC dans le journal (dernière entrée `<id>`) ; `--qc` doit lui correspondre.
- Le script **journalise lui-même** la décision, favorable ou non, comme dernière entrée `<id>/cloture`, avec ce qui la lie au code : ticket, base, fichiers, empreinte, chemin et sha256 du rapport, identifiant de l'entrée QC, verdict expert. N'écris jamais de clôture avec `append.ps1` : le verrou la refuse.
- Le verrou de commit (`S verrou`) revérifie tout au moment du commit : dernière entrée = clôture VALIDÉ complète, dernier QC du ticket VALIDÉ et cité, rapport présent, inchangé et favorable, empreinte identique, fichiers indexés = fichiers revus (plus le suivi documentaire `docs/`, `.scratch/`, plan, journal), sans modification non indexée. Toute entrée ajoutée après la clôture (un autre QC, même VALIDÉ) bloque le commit : commite **juste après** la clôture, avant de démarrer autre chose.

## 7. Confronter, corriger, réexaminer

- Désaccord (l'un favorable, l'autre non) : expose les deux positions et leurs preuves côte à côte ; la clôture reste non validée jusqu'à résolution. Le propriétaire tranche s'il s'agit d'un choix d'architecture ou de produit.
- REFUSÉ ou BLOQUÉ : transmets au développeur (toi-même, en implémentation) les anomalies exactes avec preuve et test de vérification. Après correction : nouveau diff, nouvelle EMPREINTE, **nouveau** passage de l'expert sur les changements réels (le rapport précédent est fourni comme historique, pas comme conclusion), puis QC à nouveau si les changements touchent ce qu'il a revu, puis étape 6.
- Si une correction sort du périmètre du ticket (nouvelle fonctionnalité, constante produit, fichier interdit par `CLAUDE.md`) : arrête et demande au propriétaire.
- Toute modification d'un fichier du ticket après une clôture VALIDÉ rouvre la revue (l'empreinte ne correspond plus).

## 8. Traçabilité et synthèse

- Ticket (`## Comments`, une entrée par passage) : date, verdict expert, verdict QC, décision de clôture, anomalies bloquantes et réserves (une ligne chacune), réserves acceptées avec les mots du propriétaire. Pas de copie intégrale du rapport.
- Statut : `livré (JJ/MM/AAAA), validé expert + QC` **seulement** si la clôture journalisée est VALIDÉ ; sinon `implémenté (JJ/MM/AAAA) — validation refusée/bloquée, voir Comments`.
- Le reste suit `CLAUDE.md` (Plan architecte, known_issues, TRD_MAJ). Si un verdict dégage une règle générale (physique, tactique, critère de test, architecture), propose au propriétaire de la documenter à l'endroit approprié (`docs/TRD_V2.md`, `docs/CARTE_ATTRIBUTS_V2.md`, `docs/INDICATEURS_V2.md`, `docs/adr/`) ; n'écris pas sans son accord.
- Synthèse au propriétaire : verdict expert, verdict QC, décision de clôture, ce qui a été vérifié par calcul ou mesure, ce qui ne l'a pas été, réserves et actions restantes.

## Ce que ce skill garantit et ne garantit pas

- Garanti par un mécanisme : l'expert ne peut rien modifier (outils Read/Grep/Glob seulement) ; la décision suit une table déterministe testée (`python -I S --selftest`) ; un rapport absent, incomplet, d'un autre ticket ou d'un autre état du code ne donne jamais VALIDÉ ; le verrou de commit bloque tout commit sans clôture VALIDÉ encore vraie (une entrée QC seule ne suffit jamais ; banc d'interruptions : `bash .scratch/expert-dispositif/tests/test-verrou.sh <dossier vide>`).
- Garanti par instruction seulement : que ce skill soit appelé avant de passer un ticket en « livré », que la liste FICHIERS soit complète, que l'acceptation des réserves vienne réellement du propriétaire. Le statut écrit dans le fichier ticket n'est protégé par aucun mécanisme.
