# Simulafoot — instructions permanentes

Simulation de football : moteur statistique (Poisson, `src/ligue1sim/`) + rendu animé 2D rejouant un résultat déjà décidé (`src/ligue1sim/animation/`, `engine/`, `render/canvas.html`). Interface : PWA React (`ui/`) + API FastAPI (`api/`) ; Streamlit (`app.py`) historique.

## Références (ordre de priorité)
1. **TRD** : `docs/TRD_SIMULAFOOT.pdf` (+ `docs/TRD_MAJ.md` pour les mises à jour postérieures). Référence fonctionnelle et technique. PRD : `docs/PRD – Simulafoot.pdf`.
2. `Plan architecte Simulafoot.md` : chantier en cours et ordre d'exécution. `docs/known_issues.md` : tickets. `PROJET_SIMULAFOOT.md` : état du projet.
3. Le code réel prime sur toute description : vérifier avant de supposer qu'une fonctionnalité existe.

## Commandes (vérifiées)
- API + UI : `simulafoot.bat` (uvicorn :8000, Vite :5173), ou `uv run uvicorn api.main:app --port 8000` et `npm run dev --prefix ui`.
- Tests : `PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider` (marqueur `integration` exclu par défaut ; `-m integration` à la demande, ~30 min).
- UI : `npm run build` et `npm run lint` dans `ui/` (attendu : build OK, 0 erreur, 5 avertissements).
- Mesures : `scripts/measure_geometry.py` (pipeline réel, graine d'audit 20260923).
- `pytest` nu échoue (ticket 9) : toujours `uv run`.

## Règles d'architecture et de modification
- Le résultat sportif (score, buts, cartons, remplacements) n'est jamais modifié par le rendu ou la narration.
- Déterminisme : toute variabilité du rendu dérive de sha256 d'une clé stable ; jamais `hash()`, `random`, horloge.
- **Interdits sauf exception validée explicitement par le propriétaire** : moteur Poisson, 3c, `render/canvas.html`, `engine/narrative.py`, `engine/narrative_player.py`, `engine/ball_events.py`, `animation/types.py`, `serialize.py`, `motion.py`, `sequence_generator.py`, `ball.py`, `templates.py`. Demander l'exception avant de les toucher.
- Toute constante produit est proposée avant modification (« soumise à validation du propriétaire »).
- Modifications ciblées, pas de refonte ; ne corriger que les tickets traités ; ne supprimer ni désélectionner un test pour le faire passer.
- Imports privés entre modules : ne pas en ajouter (ticket 19).
- Projet sur OneDrive : `link-mode = copy`, ne jamais supprimer récursivement une jonction `ui/node_modules`. Fichiers stockés en LF (index), CRLF dans l'arbre : respecter le style existant.

## Validation avant de déclarer une tâche terminée
1. Critères d'acceptation chiffrés définis avant le code.
2. Tests ajoutés/adaptés, suite complète passée (compte comparé à l'attendu : 2 124 passés, 13 désélectionnés le 31/10/2026 (arbre de travail sur 25514b5)).
3. Déterminisme : mêmes empreintes sur deux exécutions ; mesure avant/après sur le pipeline réel si le rendu change.
4. Revue par `simulafoot-reviewer` pour toute modification significative.
5. Rapport distinguant tests réussis, échoués, non exécutés, et points à vérifier à l'écran.
6. Pour un ticket : `/valider-ticket-simulafoot` (voir « Clôture des tickets »), qui inclut `/valider-etape`.
7. Commit seulement après vérification, avec isolation des hunks, **jamais de push** sans demande. Ne jamais écrire un hash de mémoire : le lire dans `git log`. Ne pas inclure de modifications préexistantes non liées.

## Clôture des tickets (règle obligatoire)
- Aucun ticket ne passe en « livré, validé » sans les deux conditions : verdict `APPROVED` du sous-agent `expert` (ou `APPROVED_WITH_RESERVATIONS` dont chaque réserve est acceptée explicitement par le propriétaire) **et** verdict `VALIDÉ` du contrôle qualité (`controle-qualite` via `/valider-etape`). Les deux passent par `/valider-ticket-simulafoot`, qui journalise la décision dans `.claude/qc/journal.jsonl` (sous-étape `<id>/cloture`).
- Implémentation terminée ≠ ticket validé. Statuts : `implémenté (JJ/MM/AAAA) — en attente de /valider-ticket-simulafoot` → `livré (JJ/MM/AAAA), validé expert + QC`. Les statuts antérieurs (« livré, validé QC ») restent tels quels.
- Le développeur ne remplace jamais le verdict de l'expert par son appréciation. Désaccord, rapport absent ou incomplet, vérification impossible, `REJECTED` ou `INCONCLUSIVE` : le ticket reste non validé jusqu'à résolution ou réexamen.
- Toute modification d'un fichier du ticket après validation rouvre la revue (l'empreinte du changement ne correspond plus).
- Les améliorations facultatives sans incidence démontrée sur le réalisme ou la conformité n'empêchent pas la clôture.
- Détails, table de décision, limites : `docs/agents/validation-tickets.md`.

## Sous-agents (`.claude/agents/`)
- `simulafoot-architect` (lecture seule) : avant une modification complexe ou transverse ; plan, risques, exigences TRD.
- `simulafoot-reviewer` (lecture seule) : après une modification significative.
- `simulafoot-test-advisor` (consultatif) : quand le rendu, le mouvement ou la physique changent.
- `expert` (lecture seule stricte : Read, Grep, Glob) : réalisme, physique, tactique et validation numérique d'un ticket implémenté ; appelé uniquement par `/valider-ticket-simulafoot`. Il n'exécute rien : il demande les calculs, le skill les exécute hors dépôt et lui renvoie les résultats.
- Pas pour une petite correction (sauf `expert`, obligatoire à chaque clôture de ticket, proportionné au ticket). Lancer séquentiellement, avec le contexte TRD utile dans le prompt. Un seul agent écrit dans un fichier donné ; aucun de ces agents ne modifie le code.

## Documentation
- Après chaque sous-étape : mettre à jour `Plan architecte Simulafoot.md` (statut, commits), `docs/known_issues.md` (tickets), et `docs/TRD_MAJ.md` (statut des exigences touchées) ; le PDF du TRD n'est pas édité à la main.
- Citer les commits par préfixe lu dans `git log`.

## Agent skills

### Issue tracker

Tickets locaux en Markdown sous `.scratch/<feature-slug>/` (la CLI `gh` n'est pas installée ; à repasser en GitHub plus tard). Voir `docs/agents/issue-tracker.md`.

### Domain docs

Single-context (un seul `GLOSSARY.md` + `docs/adr/` à la racine, un domaine unique pour Simulafoot). Voir `docs/agents/domain.md`.
