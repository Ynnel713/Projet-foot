# 11d: Le tacle selon l'angle d'approche et la vitesse relative

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un tacle par derrière ou à contre-courant n'a pas la même issue). **Catégorie :** exécution.

**Constat vérifié :** `duel.tackle_success_probability` (`duel.py:58`) ne lit que Tackling, Strength et Balance ; ni angle, ni vitesse.

**What to build:** La réussite et le risque de faute du tacle dépendent de l'angle entre l'approche du tacleur et le cap ou la course du porteur (de face, de côté, par derrière) et de leur vitesse relative ; par derrière : réussite plus faible et faute plus probable.

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 11e, 21b (ajouté le 10/11/2026, audit de la roadmap).

**Status:** livré (15/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : facteurs par angle : valeurs proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même duel de face, de côté, par derrière : réussite décroissante, faute croissante
- **Statistiques (séries de matchs) :** 50 matchs : fautes par match (repère 21-26, indicatif)

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Effet de l'angle mesuré en scène
- [x] Fautes rapportées
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**15/11/2026, constantes validées par le propriétaire** (« Je valide ») : angle entre le cap du corps du porteur (`facing`, 07a) et la direction d'où vient le tacleur, interpolé linéairement entre trois repères : de face (0°) réussite x 1,00 et faute x 1,0 ; de côté (90°) x 0,90 et x 1,3 ; par derrière (180°) x 0,60 et x 2,0. Vitesse de rapprochement (vitesse relative du tacleur vers le porteur) au-delà de 2 m/s : faute + 10 % par m/s (au plus x 1,5), réussite − 3 % par m/s (au plus x 0,85). Facteurs multipliés ; faute plafonnée à 0,90. Aucun attribut (Tackling, Strength, Aggression gardent leur seul rôle). Chiffre réel : non trouvé (loi 12 IFAB, qualitatif). Hors périmètre : gravité de la faute selon l'angle (cartons, 09a). Estimation annoncée au démarrage : 1 h 55 (celle du ticket), confirmée.

**15/11/2026, implémentation.** `duel.py` : constantes `TACKLE_*`, `tackle_approach_angle_deg`, `tackle_closing_speed_mps`, `tackle_approach_factors`, `tackle_probabilities` ; `resolve_tackle` tire réussite et faute sur ces probabilités (mêmes deux tirages du flux DUEL, signature inchangée) ; `tackle_success_probability` et `foul_probability` restent les fonctions d'attributs. Tests : `tests/test_v2engine_tacle_approche.py` (lecture de l'angle et de la vitesse, facteurs aux repères et entre eux, même duel de face, de côté, par derrière, plafonds, facteurs indépendants des attributs, 4 000 tacles tirés de face et par derrière : faute ~30 % contre ~60 %).

**15/11/2026, mesure, déterminisme.** 50 matchs appariés (`bench_series`, graine d'audit, matchs 0 à 49) contre l'état du 11c (`4c1cdcb`, worktree) : `11d-avant.txt` (identique à `11c-apres.txt` hors durée machine), `11d-apres.txt`, `11d-comparaison.txt` ; `docs/INDICATEURS_V2.md` section 43. Fautes **15,8 → 20,9 par match** (+ 5,1 [+ 3,9 ; + 6,3]), au bas du repère réel 21-26 ; coups francs + 3,1 ; tacles tentés − 1,6 (part des tacles gagnés : − 8 à − 20 points selon le quart d'heure) ; pertes au contact − 5,5 ; temps de jeu effectif − 1,8 point, d'où passes − 18 et km par joueur − 0,20 (plus d'arrêts de jeu) ; buts, tirs, passes réussies sans écart significatif. `11d-det1` et `11d-det2` identiques hors temps de calcul. V1 inchangée.

**15/11/2026, suite complète.** 3 105 passés, 0 ignoré, 14 désélectionnés (3 088 + 17 ; `11d-suite.txt`) ; `CLAUDE.md` mis à jour.

**15/11/2026, durée.** Estimation 1 h 55 ; durée réelle environ 1 h 20 (analyse 15, développement 15, tests 15, intégration 35), − 30 % (à la limite du seuil) : deux facteurs purs appliqués dans `resolve_tackle` sans toucher à `match.py` ; intégration allongée par la série « avant » à relancer (processus tué en fin de série, comme au 11c) et par la documentation. Durée estimée à l'horloge de la session hors attentes machine et échanges avec le propriétaire, non chronométrée. Temps machine hors total : trois séries de 50 matchs (dont la relance), suite complète (12 min), déterminisme 2 x 2 matchs.

**15/11/2026, passage 1 de l'expert : APPROVED ; QC VALIDÉ ; clôture VALIDÉ** (journal, ticket `v2-realisme/11d/cloture`), commit `9c59a2e`. Remarques facultatives : A1 libellé « tacles gagnés » au lieu de « tacles tentés » (section 43 et ce ticket) ; A2 ordre des entrées dans `docs/PLAN_V2.md`. Toutes deux corrigées au ticket 11e (le statut aussi : la fiche faisait partie des fichiers revus). Points à surveiller : renoncement au tacle par derrière (04j), gravité selon l'angle (09a), total des fautes (22a).

