# EM-00 — Banc de rejeu d'une trace enregistrée (S, dev seulement) — 90 min (moyenne)

**Status:** livré (07/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : pouvoir atteindre n'importe quel état (but, mi-temps, fin, x8) en quelques secondes, de façon reproductible.
- **Problème** : un match demande environ 3 min de calcul et 11 min de lecture à x8 ; impossible de comparer avant/après ou
  de mesurer la fluidité proprement.
- **Résultat** : script qui enregistre une **vraie trace** du moteur (appel en processus de la route publique `create_match` de l'API) dans `ui/src/dev/fixtures/` (ignoré par git),
  et un mode de développement (`?fixture=<nom>`, absent du build de production) qui la rejoue à la place de l'API, avec un
  paramètre `?t=<minute>` pour partir d'un instant donné.
- **Périmètre** : lecture seule d'une trace réelle ; aucune donnée inventée ; aucune modification du moteur.
- **Composants** : `scripts/record_v2_trace.py`, `V2Match.jsx` (point d'entrée dev), `ui/src/dev/fixture.js`.
- **Critères** : 3 traces enregistrées (match avec 3 buts ou plus, match 0-0, match avec temps additionnel) ; build de
  production sans le mode ; départ à `t=44` affiche la mi-temps en moins de 5 s.
- **Tests** : script rejoué deux fois (mêmes octets à graine fixée) ; `npm run build` ; vérification que le mode est
  absent de `dist/`.
- **Dépendances** : aucune. **Risques** : traces volumineuses (taille du dépôt) → hors dépôt ou compressées.

## Réalisé

- `scripts/record_v2_trace.py <nom> <domicile> <extérieur> [graine]` : calcule un match (graine fixée) et l'écrit dans
  `ui/src/dev/fixtures/<nom>.json` (ignoré par git, ~19 Mo) avec **la même sérialisation que l'API** + les deux feuilles de match.
- `ui/src/dev/fixture.js` + effet dans `V2Match.jsx`, derrière `import.meta.env.DEV` :
  `/v2?fixture=<nom>[&t=<minute>][&speed=<x>][&paused=1]`. Les buts et la mi-temps d'avant `t` sont réputés vus (pas de
  ralenti ni de bandeau rétroactifs). Fichiers lus par `fetch` (l'`import` JSON de Vite mettait plus de 20 s).
- Traces enregistrées : `buts-nombreux` (PSG 3-3 OM, graine 1, 6 buts, temps additionnel [5, 6]), `sans-but`
  (Le Havre 0-0 Lorient, graine 11, [2, 4]), `trois-buts-exterieur` (Le Havre 0-3 Lorient, graine 12, [3, 7]).

## Acceptance criteria

- [x] 3 traces enregistrées : ≥ 3 buts, 0-0, temps additionnel (les trois)
- [x] Départ à `t=44` : score 1-2 attendu (buts à 25', 26', 39') ; départ à `t` juste avant `second_half_start_minute` (`t=49.9` sur `buts-nombreux`, 2e période à 50') : bandeau « MI-TEMPS » visible en moins de 5 s après chargement (critère reformulé après la revue de l'expert, réserve A2 ; ne pas le recopier tel quel dans les tickets suivants)
- [x] Chargement de la page jusqu'à l'écran de jeu : ~2,2 s (critère < 5 s)
- [x] Mêmes octets à graine égale : `sans-but` enregistré deux fois, SHA-256 identique
- [x] Build de production sans le mode : `npm run build` OK, aucune trace de `record_v2_trace` ni du message dans `dist/assets`
- [x] `npm run lint` : 0 erreur, 5 avertissements (les 5 d'avant, aucun dans `V2Match.jsx`)
- [x] Suite Python complète : 2 510 passés, 14 désélectionnés (15 min 05 s, 07/11/2026), identique à l'attendu

## Traces de référence (réserve A1 de l'expert)

Les traces ne sont pas versionnées (`ui/src/dev/fixtures/`, ignoré par git) : elles dépendent du moteur au commit `bdc4478`
et de `data/joueurs.xlsx` (SHA-256 `dcd0a0bf…b8942`, fichier modifié dans l'arbre de travail à cette date). **Ne pas les
régénérer pendant le chantier** ; avant chaque comparaison avant/après, vérifier les empreintes :
`Get-FileHash ui/src/dev/fixtures/*.json -Algorithm SHA256`.

| Fichier | SHA-256 | Match | Graine | Commande |
|---|---|---|---|---|
| `buts-nombreux.json` | `ae6252c4c9b294f694f37a130f5b2505405d171757e663575b016149d8778cfc` | PSG 3-3 OM, temps additionnel [5, 6] | 1 | `uv run python -m scripts.record_v2_trace buts-nombreux "Paris Saint-Germain" "Olympique Marseille" 1` |
| `sans-but.json` | `31df4eba1d0e2aac8b55f169e2616ddc0f8dde3b52e979da9b3c2a9e2405477d` | Le Havre 0-0 Lorient, [2, 4] | 11 | `uv run python -m scripts.record_v2_trace sans-but "Le Havre AC" "FC Lorient" 11` |
| `trois-buts-exterieur.json` | `61d6223ae9a3cfc38b9f2a84465c268e3231973218d33188a6bf60ff941a6d6a` | Le Havre 0-3 Lorient, [3, 7] | 12 | `uv run python -m scripts.record_v2_trace trois-buts-exterieur "Le Havre AC" "FC Lorient" 12` |

Les traces ont été réenregistrées avec le script final (routes publiques) ; leur contenu est identique à celui des premiers enregistrements (comparaison des JSON, 3 sur 3 dont la trace à 6 buts : reproductibilité à graine fixée démontrée sur un match riche).

Limites : le banc rejoue des matchs **finis** (`done` vrai, toutes les images présentes) ; les états « calcul en cours » et
« rejeu qui rattrape le calcul » ne s'y valident pas. Les noms `essai-11` et `essai-12` des dossiers de travail sont devenus
`sans-but` et `trois-buts-exterieur`. Reproductibilité à graine fixée vérifiée sur une trace (`sans-but`, SHA-256 identique
sur deux enregistrements).

## Estimation

Annoncée : 90 min (15/40/15/20, confiance moyenne), temps machine ~15 min hors total.
Réel : environ 115 min de travail effectif (15/40/20/40 ; durée estimée, non chronométrée) ; temps machine ~35 min (traces, contre-épreuve, suite complète 15 min 05 s).
Écart + 28 % (sous 30 %). Causes : l'import JSON de 19 Mo par Vite (> 20 s) a obligé à passer par `fetch` ; le premier passage de QC a refusé des imports privés dans le script (réécriture, nouvel enregistrement des traces, second passage de l'expert et du QC).

## Comments
- 07/11/2026, clôture (passage 1) : expert APPROVED_WITH_RESERVATIONS (A1 empreintes des traces non consignées, A2 critère mi-temps mal formulé ; facultatifs A3 à A5), QC REFUSÉ (le script importait `v2._find_club`, `_Job`, `_run_job`, `_jobs` : règle « API publique uniquement »). Clôture non prononcée.
- 07/11/2026, clôture (passage 2) : script réécrit sur `create_match` et `club_lineup` ; garde sur `?t` ; traces réenregistrées (contenu identique aux premières, 3 sur 3) ; A1, A2, A5 traitées dans ce fichier. Expert APPROVED (aucune anomalie, facultatif A6 : retirer la phrase redondante des Limites), QC VALIDÉ, clôture VALIDÉ. Aucune réserve à faire accepter.
  - Facultatif non repris (changerait le code revu) : `asked_t` en snake_case dans `V2Match.jsx`.
  - À surveiller : EM-01, EM-08, EM-11, EM-13 vérifient les SHA-256 des traces avant chaque comparaison avant/après et ne valident pas sur ce banc « calcul en cours » ni « rejeu qui rattrape le calcul ».
