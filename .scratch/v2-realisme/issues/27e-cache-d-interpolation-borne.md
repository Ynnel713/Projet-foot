# 27e: Cache d'interpolation borné (mémoire des séries de matchs)

**Chantier :** `v2-realisme` (découvert pendant 27d, le 22/11/2026). **Priorité :** P1 (bloque les séries longues de 27d). **Catégorie :** technique (mémoire), sans effet sur le jeu.

**Constat vérifié (22/11/2026, ticket 27d) :** `v2engine/movement.py` décore `_lerp(note, points)` avec `@lru_cache(maxsize=None)`. La note est un réel continu (elle varie avec la fatigue, `effective_rating`), donc le cache grossit sans fin :
- 30 minutes de jeu : 336 836 entrées pour 6,2 millions de lectures ;
- un même processus : 449, 599 puis 872 Mo de pic après 1, 2 et 3 matchs de 90 min ;
- une série de 100 matchs sur 4 processus (25 matchs chacun) tuée par manque de mémoire à 3,5 Go par processus ;
- `scripts/bench_series.py` (`ProcessPoolExecutor` sans `max_tasks_per_child`) et l'API FastAPI enchaînent les matchs dans les mêmes processus : même gonflement.

**What to build:** borner le cache (`maxsize=4096`) plutôt que le retirer, si la mesure montre qu'il fait gagner du temps. La fonction est pure : aucun changement de résultat. Chercher les autres `lru_cache(maxsize=None)` appelés avec des réels continus dans `v2engine/`, et poser un test de garde.

**Attributs :** aucun.

**Blocked by:** aucun.

**Bloque :** les séries longues de 27d.

**Status:** livré (22/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 10 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 10** |

Confiance : élevée. Hypothèses : un seul cache en cause ; la réutilisation se fait surtout à l'intérieur d'un pas (même joueur, même note lue plusieurs fois), donc un petit cache garde presque tout le gain.
Temps machine, non compté : 3 matchs de 90 min avant et après dans un même processus (environ 15 min chacun), suite complète (environ 15 min).

## Tests

- **Unitaire :** `_lerp` porte un cache borné à 4096 entrées.
- **Garde :** aucun `lru_cache(maxsize=None)` ni `functools.cache` dans `v2engine/`.
- **Mesure :** 3 matchs de 90 min enchaînés dans un même processus, graine fixée, avant et après : empreinte sha256 de chaque pas (positions, vitesses, ballon), temps et pic mémoire par match.

## Acceptance criteria

- [x] Empreintes des 3 matchs identiques avant et après (graine fixée), et identiques sur deux exécutions après
- [x] Pic mémoire après 3 matchs de 90 min dans un même processus : croissance entre le match 1 et le match 3 inférieure à 50 Mo (avant : + 423 Mo au relevé du 27d, + 392 Mo à cette mesure)
- [x] Temps par match : au plus 3 % de plus qu'avant (le retrait complet du cache coûterait environ 12 s par match, mesuré)
- [x] Taux de réussite du cache borné à 1 point près de celui du cache illimité, sur la séquence réelle d'appels
- [x] Aucun autre cache illimité à clé réelle dans `v2engine/` (test de garde)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Suite complète verte ; compte comparé à l'attendu de `CLAUDE.md` (3 441 + tests ajoutés)

## Comments

### Mesures (22/11/2026)

**Séquence réelle d'appels** (10 min de jeu, graine d'audit 20260923 : 1 934 631 appels, 107 288 couples distincts, 9 suites de repères), rejouée contre chaque variante :

| Cache | ns par appel | Réussite |
|---|---|---|
| aucun | 904 | — |
| illimité | 223 | 94,5 % |
| 256 | 241 | 94,4 % |
| 1024 | 218 | 94,5 % |
| 4096 (retenu) | 235 | 94,5 % |

Retirer le cache coûterait environ 0,7 µs × 17 M appels, soit environ 12 s par match de 90 min : il est gardé, borné. La réutilisation se fait dans un même pas (même joueur, même note lue plusieurs fois).

**3 matchs de 90 min enchaînés dans un même processus** (graines 20260923 + k, empreinte sha256 de chaque pas : positions, vitesses, porteur et ballon) :

| Match | Empreinte (avant = après × 2) | Avant : s / pic Mo / entrées | Après, passe 1 : s / pic Mo | Après, passe 2 : s / pic Mo |
|---|---|---|---|---|
| 1 | `13f384a3ea245fd2` | 174,0 / 457 / 964 875 | 169,6 / 291 | 193,0 / 291 |
| 2 | `01fa2d5f6deca968` | 162,5 / 738 / 1 889 033 | 165,1 / 418 | 159,9 / 291 |
| 3 | `e12a5f8a215e900b` | 162,4 / 849 / 2 792 425 | 196,0 / 419 | 163,7 / 292 |

- Empreintes identiques avant et après, et sur les deux passes après.
- Mémoire : + 1 Mo du match 1 au match 3 (passe 2). Les + 128 Mo de la passe 1 venaient du script de mesure, qui gardait la trace du match précédent pendant le suivant (corrigé en passe 2) ; l'avant a ce même biais, sa croissance (+ 392 Mo) est dominée par le cache (2,79 M entrées).
- Temps : la durée d'un même match varie de ± 20 % d'une exécution à l'autre sur ce conteneur (193,0 contre 169,6 s pour le match 1, code identique). Meilleur temps des deux passes après contre avant : − 2,5 %, − 1,6 %, + 0,8 %. Coût CPU attendu par le rejeu : + 12 ns par appel, environ 0,2 s par match.
- Autres caches : aucun autre `lru_cache(maxsize=None)` dans `v2engine/`. Les cinq de `src/ligue1sim/` (V1 : `lineup.py`, `coaches.py`, `nations.py`) ont pour clés des chemins de fichiers, hors périmètre.

### Clôture (22/11/2026, passage 1)

- Expert : APPROVED. Facultatif A1 : le test de garde ne voit que les décorateurs (`lru_cache(maxsize=None)(g)` appelé en ligne passerait ; motif absent aujourd'hui). Facultatif A2 : `test_lerp_cache_stays_bounded_with_continuous_notes` presque tautologique.
- Contrôle qualité : VALIDÉ. Réserve : le critère de temps est tenu sur le meilleur temps de chaque match sur deux passes, pas sur chaque exécution (bruit du conteneur ± 20 %).
- Décision de clôture : VALIDÉ (expert APPROVED, QC VALIDÉ).
- Suite complète : 3 444 passés, 0 ignoré, 14 désélectionnés (19 min 21).
- Durée : estimée 70 min, réelle environ 65 min (− 7 %) : 15 analyse, 10 développement, 15 tests, 25 intégration et vérifications. Temps machine hors total : 3 passes de 3 matchs de 90 min (environ 25 min), suite complète.
