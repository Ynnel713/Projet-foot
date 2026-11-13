# Simulafoot — instructions permanentes

Simulation de football, deux moteurs :
- **V1** : moteur statistique (Poisson, `src/ligue1sim/`) qui décide le résultat, puis rendu animé 2D qui le rejoue (`src/ligue1sim/animation/`, `engine/`, `render/canvas.html`).
- **V2** : moteur physique piloté par les attributs des joueurs, le résultat émerge du jeu (`v2engine/`).

Interface : PWA React (`ui/`) + API FastAPI (`api/`) ; Streamlit (`app.py`) historique.

## Références
- Le **code réel** prime sur toute description : vérifier avant de supposer qu'une fonctionnalité existe.
- V1 : `docs/TRD_SIMULAFOOT.pdf` (+ `docs/TRD_MAJ.md` pour les mises à jour), PRD `docs/PRD – Simulafoot.pdf`, chantier en cours `Plan architecte Simulafoot.md`, tickets `docs/known_issues.md`, état du projet `PROJET_SIMULAFOOT.md`.
- V2 : `docs/TRD_V2.md` (décisions D-V..), `docs/PLAN_V2.md`, `docs/CARTE_ATTRIBUTS_V2.md` (rôle de chaque attribut, règle anti double comptage), `docs/INDICATEURS_V2.md`.
- Tickets de chantier : `.scratch/<chantier>/issues/NN-*.md` (format : `docs/agents/issue-tracker.md`). Domaine : `GLOSSARY.md`, `docs/adr/` (`docs/agents/domain.md`).

## Commandes
- API + UI : `uv run uvicorn api.main:app --port 8000` et `npm run dev --prefix ui` (Vite :5173). (`simulafoot.bat` : ancien poste Windows.)
- Tests : `PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider` (environ 10 min en session cloud). Toujours via `uv run` : `pytest` nu échoue (ticket 9). Marqueur `integration` exclu par défaut (`-m integration`, ~30 min).
- Attendu : **2 927 passés, 0 ignoré, 14 désélectionnés** (13/11/2026, session cloud, ticket v2-realisme/07d). Des tests NLG ignorés signalent un venv `simulafoot_nlg/.venv` absent.
- UI, dans `ui/` : `npm run build` (OK) et `npm run lint` (0 erreur, 5 avertissements).
- Mesures : `scripts/measure_geometry.py` (V1, graine d'audit 20260923), `scripts/measure_v2.py` et `scripts/v2_indicators.py` (V2).

## Règles de modification
- Le résultat sportif (score, buts, cartons, remplacements) est fixé par le moteur ; rendu et narration l'habillent sans le changer.
- Déterminisme :
  - V1 (rendu, narration) : toute variabilité dérive de sha256 d'une clé stable (jamais `hash()`, `random` non semé, horloge).
  - V2 : module `random`, déterminisme assoupli (D-V06) ; mesures reproductibles par graine (`random.seed`) ; jamais `hash()` ni horloge.
- **Fichiers protégés**, modifiables seulement sur exception accordée par le propriétaire pour la tâche en cours : moteur Poisson, 3c, `render/canvas.html`, `engine/narrative.py`, `engine/narrative_player.py`, `engine/ball_events.py`, `animation/types.py`, `serialize.py`, `motion.py`, `sequence_generator.py`, `ball.py`, `templates.py`.
- Toute constante produit est proposée au propriétaire avant d'être codée.
- Modifications ciblées sur le ticket traité. Un test qui échoue se corrige ; il n'est ni supprimé ni désélectionné.
- Imports entre modules par leur API publique uniquement (ticket 19).
- Développement en session cloud Linux uniquement, environnement `projet-foot` : son setup script installe PowerShell 7 (liens `powershell` et `powershell.exe`, pour le verrou et `valider-etape`), les venvs Python (racine et `simulafoot_nlg/`) et les dépendances npm de `ui/`. Fins de ligne : garder celles du fichier modifié.

## Estimer la durée d'un ticket
- Tout ticket porte une estimation en travail effectif : analyse, développement, tests, intégration et vérifications, total, confiance (élevée, moyenne, faible), hypothèses. Le temps machine (suite complète, séries de matchs) est noté à part, hors total.
- Avant de commencer : annoncer l'estimation du ticket. Si le périmètre change en cours de route : annoncer la nouvelle estimation avant de continuer.
- À la clôture : temps réellement passé, comparé à l'estimation ; cause expliquée si l'écart dépasse 30 %. Intégré au rapport de clôture et ajouté au registre `docs/agents/suivi-estimations.md`.
- Un ticket estimé au-delà d'environ 2 h est examiné pour découpage avant le code (seuil indicatif).

## Terminer une tâche
1. Critères d'acceptation chiffrés posés avant le code.
2. Tests ajoutés ou adaptés ; suite complète passée, compte comparé à l'attendu ci-dessus.
3. Déterminisme : mêmes empreintes sur deux exécutions (V2 : à graine fixée) ; mesure avant/après sur le pipeline réel si le comportement change.
4. Rapport séparant tests réussis, échoués, non exécutés, et points à vérifier à l'écran ; il donne aussi la durée estimée et la durée réelle (voir « Estimer la durée d'un ticket »).
5. Ticket : clôture par `/valider-ticket-simulafoot` (voir ci-dessous).
6. Commit avec les seuls hunks de la tâche, puis push sur la branche de travail de la session juste après (conteneur éphémère : un commit non poussé se perd) ; jamais sur `main` sans demande. Dans la documentation, un commit se cite par son préfixe, lu dans `git log`, jamais de mémoire.

## Clôture des tickets et verrou de commit
- Un ticket devient `livré (JJ/MM/AAAA), validé expert + QC` seulement avec **deux verdicts** : `APPROVED` du sous-agent `expert` (ou `APPROVED_WITH_RESERVATIONS`, chaque réserve acceptée par le propriétaire) **et** `VALIDÉ` du contrôle qualité. Avant : `implémenté (JJ/MM/AAAA) — en attente de /valider-ticket-simulafoot`. Les anciens statuts (« livré, validé QC ») restent tels quels.
- Le verdict de l'expert fait foi ; `REJECTED`, `INCONCLUSIVE`, rapport absent ou désaccord laissent le ticket non validé. Les améliorations facultatives ne bloquent pas.
- **Verrou** (`.claude/qc/verrou-commit.ps1`) : tout commit, même purement documentaire, exige que la dernière entrée de `.claude/qc/journal.jsonl` soit une clôture `VALIDÉ` dont l'empreinte correspond aux fichiers indexés. Commiter juste après la clôture ; toute modification d'un fichier revu rouvre la revue.
- Détails et table de décision : `docs/agents/validation-tickets.md`.

## Sous-agents (`.claude/agents/`)
- `simulafoot-architect` avant une modification transverse ; `simulafoot-reviewer` après une modification significative ; `simulafoot-test-advisor` quand mouvement, physique ou décisions des joueurs changent. Inutiles pour une petite correction.
- `expert` : uniquement via `/valider-ticket-simulafoot`, à chaque clôture.
- Lancés un par un, avec le contexte TRD utile dans le prompt ; ils lisent, le code est modifié par la session principale.

## Documentation après chaque sous-étape
- Mettre à jour `Plan architecte Simulafoot.md` (statut, commits), `docs/known_issues.md` et `docs/TRD_MAJ.md` (V1), ou `docs/PLAN_V2.md` et le ticket `.scratch/` (V2). Le PDF du TRD reste tel quel.
