# Relais : ticket v2-collectif/09 (compensations défensives), mis en pause le 02/11/2026

Lire d'abord `CLAUDE.md`, puis `.scratch/v2-collectif/issues/09-compensations.md` (constantes validées, résultats, réserve C3, `## Comments` avec le passage 1).

## État

- Code : `v2engine/defense.py`, `v2engine/cerveau.py` (non commités). Tests : `tests/test_v2engine_compensations.py` (nouveau, 16 tests), `tests/test_v2engine_rayon_attributs.py` (commentaires). Docs : `docs/CARTE_ATTRIBUTS_V2.md` (3 lignes : Teamwork, Anticipation, Positioning), `docs/INDICATEURS_V2.md` (dernier paragraphe), tickets 09 et 10 (renvoi de C3).
- Base : `7a94d64` (ticket 13 commité). Les fichiers du ticket 09 n'ont pas été touchés par les commits `316d2ef` et `7a94d64`.
- Passage 1 de `/valider-ticket-simulafoot` : expert REJECTED (rapport : `09-expert-1.md` ici), QC BLOQUÉ, clôture REFUSÉ, tous trois journalisés dans `.claude/qc/journal.jsonl`.
- Corrections faites après le passage 1 : A1 (le compensateur arrivé tient la place jusqu'au retour de l'absent), A2 (seuls les attaquants marqués sont exclus des menaces, le porteur pressé compte), A3 (niveaux de cascade gardés sur un tick de ballon libre), tests V1, A2, A3 ajoutés.
- Suite complète après corrections : 2 265 passés, 13 désélectionnés (02/11/2026).
- Vérifications de l'expert rejouées après corrections (`verif_09.py`) :
  - V1 : rôle de compensation encore attribué 2 s après l'arrivée de l'ailier : 96,2 % (62,5 % avant), aucun retrait tant que le latéral est absent.
  - V2 : compensation 0 % pendant la passe vers l'ailier et quand il a le ballon ; mais l'ailier est pressé ET couvert dans 100 % des ticks, et, porteur, il est toujours à plus de 20 m de la place (bloc) du latéral, qui recule avec le ballon. Point à soumettre à l'expert au passage 2 (scène synthétique : ailier immobile pendant la passe, défenseurs sans rôle immobiles).

## Reste à faire

1. Remesurer sur `7a94d64` + le code corrigé (la mesure a été interrompue) : copie propre hors dépôt (`git archive 7a94d64 v2engine scripts`, plus `data/joueurs.xlsx`, puis copier `defense.py` et `cerveau.py` de l'arbre de travail), lancée DEPUIS la copie (sinon le moteur du dépôt est importé) :
   - `uv run --project <dépôt> python -m scripts.measure_v2 20` (C3, C5, tacles ; environ 1 h 15) ;
   - `uv run --project <dépôt> python diag_roles.py 4 --profil` (C4, C6) ;
   - `empreinte.py` deux fois (déterminisme).
   Références avant (`7a94d64` seul, 20 matchs) : contres récupération dans son camp 3,45, passes 15,87/min, tirs 12,5, buts 2,5, tacles 44,75, calcul 182 s ; rôle attribué 56,6 %, marqueur Marking 99 8,05 m. Passage 1 (avant corrections) : 4,5 ; 15,90 ; 12,25 ; 2,7 ; 50,0 ; 207 s ; 98,8 % ; 7,48 m ; milieu défensif en compensation 7,7 %.
2. Mettre à jour la section Résultats du ticket et `docs/INDICATEURS_V2.md` avec ces chiffres.
3. Passage 2 de `/valider-ticket-simulafoot` : nouveau diff `git diff 7a94d64 -- v2engine/defense.py v2engine/cerveau.py tests/test_v2engine_compensations.py tests/test_v2engine_rayon_attributs.py` (+ le fichier de test nouveau), nouvelle empreinte, dossier de tests ; fournir `09-expert-1.md` à l'expert comme historique, avec les résultats V1/V2 rejoués. Puis `/valider-etape` (QC), puis `cloture.py decision`.
4. Réserve C3 (tirs de contre 3,45 → 4,5, venant de la passe en vol) : acceptée par le propriétaire dans la session précédente (« Ok avc ta recommandation », 02/11/2026), renvoyée au ticket 10. Le skill n'autorise `--reserves-acceptees` que si le propriétaire accepte DANS la conversation en cours : lui redemander explicitement, réserve par réserve, celles du rapport du passage 2.
5. Si clôture VALIDÉ : commiter juste après, en isolant les hunks. Ne pas inclure les modifications non liées de l'arbre (API, UI, `docs/PLAN_PRODUIT.md`, `tests/test_api_animation.py`, autres tickets, etc.). Jamais de push.

## Scripts (hors moteur, à lancer depuis une copie propre)

- `diag_roles.py` : rôle attribué pendant la possession adverse, distance marqueur-attaquant par niveau de Marking (`--profil`), part du temps du milieu défensif en compensation.
- `diag_trous.py` : indicateur de « trou » abandonné (non discriminant), gardé pour mémoire.
- `verif_09.py` : vérifications V1 et V2 de l'expert (lancer depuis la racine du dépôt : `PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 uv run python .scratch/v2-collectif/relais-09/verif_09.py v1|v2`).
- `empreinte.py` : sha256 de la trace, 10 minutes, graine d'audit.
- `09-tests.txt` : dossier de tests du passage 1 (chemins de l'ancienne session, périmés).
