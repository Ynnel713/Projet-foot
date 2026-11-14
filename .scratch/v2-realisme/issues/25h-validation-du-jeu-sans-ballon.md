# 25h: Validation du jeu sans ballon

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1. **Catégorie :** mesure.

**Constat vérifié (14/11/2026) :** voir 25a à 25g ; le banc (`scripts/v2_indicators.py`) mesure déjà les solutions de passe, le regroupement et les joueurs derrière le ballon (`v2-collectif/06`), entre autres indicateurs collectifs, mais sans vue par phase de jeu ni décompte des décrochages, leurres, dézonages et contre-appels.

**What to build:** indicateurs au banc (`scripts/measure_v2.py`, `scripts/v2_indicators.py`) et rapport `docs/INDICATEURS_V2.md` : solutions de passe par phase (construction, possession installée, dernier tiers), triangles, décrochages, leurres, dézonages et contre-appels par match et par poste, regroupement, distance à la place de référence ; effet de chaque attribut concerné (Off the Ball, Teamwork, Flair) à 99 contre 11 et à 80 contre 70 (banc du 24). Repères réels sourcés ou « non trouvé ».

**Attributs :** aucun.

**Blocked by:** 25a à 25g, 24.

**Bloque :** `v2-collectif/22b` (calibration tactique).

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : indicateurs tracés par les tickets 25a à 25g ; ce ticket les agrège.
Temps machine, non compté : suite complète ; mesure 50 matchs et profils.

## Tests

- **Comportementaux (profils comparés) :** Off the Ball, Teamwork et Flair à 99 contre 11 et à 80 contre 70 (banc du 24)
- **Statistiques (séries de matchs) :** 50 matchs : rapport publié dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [ ] Chaque indicateur rapporté avant (base du 25a) et après le 25g, aux mêmes graines
- [ ] Liste des attributs dont l'effet 80 contre 70 n'est pas significatif
- [ ] Écarts aux repères réels listés, sans réglage générique (calibration au `v2-collectif/22b`)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
