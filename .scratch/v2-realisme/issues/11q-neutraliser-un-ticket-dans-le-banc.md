# 11q: Neutraliser un ticket dans le banc de mesure (essais A/B)

**Chantier :** `v2-realisme` (anomalie A2 de l'expert à la clôture du 11h ; demande du propriétaire du 16/11/2026 : « indispensable pour nos futurs tests A/B »). **Priorité :** P1. **Catégorie :** mesure.

**Constat :** la série « avant » du 11h (facteur de tentative forcé à 1,0) a été obtenue par un script hors dépôt : elle n'est pas reproductible depuis le code commité.

**What to build:** option `--neutraliser TICKETS` de `scripts/bench_series.py` (liste séparée par des virgules). Chaque ticket neutralisable remplace une fonction du moteur dans le processus du match, avant l'instrumentation du banc, puis la rétablit. Un ticket inconnu est refusé avant tout lancement. Les tickets neutralisés sont notés dans les paramètres de la série (JSON). Premier ticket : `11h` (facteur de tentative de tacle à 1,0) ; les tickets suivants ajoutent leur entrée (`NEUTRALISATIONS`), à commencer par le `11p`.

**Attributs :** aucun. **Constantes :** aucune (outil de mesure, sans effet sur le jeu).

**Blocked by:** 11h (livré). **Bloque :** 11p (sa mesure avant/après utilise l'option).

**Status:** livré (16/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 5 min |
| Développement | 15 min |
| Tests unitaires et comportementaux | 10 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **40 min** |

Confiance : élevée. Hypothèses : remplacement d'une fonction du moteur par processus, sans changer le jeu.
Temps machine, non compté : deux mesures de 2 matchs ; suite complète.

**Durée réelle : 40 min** (analyse 5, développement 15, tests 10, intégration 10) : conforme à l'estimation. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée.

## Tests

- **Unitaires :** analyse de la liste (doublons, ticket inconnu refusé) ; moteur rétabli après le match, même en cas d'erreur ; série neutralisée notée dans ses paramètres, aucun tacle évité par le 11h ; ligne de commande refusant un ticket inconnu.
- **Reproduction :** `bench_series 2 --neutraliser 11h` contre les matchs 0 et 1 de `.scratch/v2-realisme/mesures/11h-avant-serie.json` ; sans option contre `11h-apres-serie.json`.

## Résultat (16/11/2026)

`--neutraliser 11h` : 2 523 indicateurs par match comparés aux matchs 0 et 1 de la série « avant » du 11h, **0 différent** (fautes 13 et 15, tacles 31 et 23, buts 2 et 3). Sans option : 2 526 indicateurs comparés à la série « après », 0 différent. Commande de la série « avant » d'un essai A/B : `uv run python -m scripts.bench_series 50 --processus 2 --neutraliser 11h --json avant.json`.

## Acceptance criteria

- [x] `--neutraliser 11h` reproduit au chiffre près les matchs de la série « avant » du 11h (2 matchs)
- [x] Ticket inconnu refusé avec un message clair, avant tout lancement
- [x] Sans l'option, résultats identiques à ceux d'avant le ticket
- [x] Suite complète comparée à l'attendu de `CLAUDE.md` : 3 201 passés (3 197 + 4 tests ajoutés), 0 ignoré, 14 désélectionnés ; attendu de `CLAUDE.md` mis à jour
- [x] Durée réelle relevée et comparée à l'estimation (`docs/agents/suivi-estimations.md`)

## Comments

- 16/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture journalisée VALIDÉ. Facultatif A1 : `run_series(neutral="11h")` (chaîne au lieu d'une liste) est refusé avec un message trompeur ; la ligne de commande n'est pas concernée. Facultatif A2 : au 11p, la neutralisation doit viser un nom global de `match` relu par l'instrumentation, et être vérifiée par une reproduction exacte.
