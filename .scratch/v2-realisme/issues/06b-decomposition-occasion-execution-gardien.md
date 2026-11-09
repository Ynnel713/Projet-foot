# 06b: Indicateurs : occasion, exécution, gardien, par attribut

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (permet de vérifier que chaque attribut agit au bon étage). **Catégorie :** mesure.

**Constat vérifié :** le banc rapporte une « qualité moyenne de l'occasion » qui inclut aujourd'hui Finishing et la note du gardien (`occasion_quality`) ; aucune décomposition.

**What to build:** Indicateurs : somme des xG neutres, gain d'exécution (xG après frappe moins xG neutre, tirs non contrés), gain du gardien (xG après frappe moins buts), par tranche de Finishing et de Long Shots, par Composure sous pression et par note du gardien. Définitions dans `docs/INDICATEURS_V2.md`.

**Attributs :** aucun

**Blocked by:** 06a (xG après frappe : la qualité d'exécution mesurée).

**Bloque :** 06c, 18a, 18e.

**Status:** livré (09/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** données synthétiques : décomposition exacte
- **Statistiques (séries de matchs) :** 50 matchs : gain d'exécution croissant avec Finishing dans la surface et Long Shots dehors

## Acceptance criteria

- [x] Indicateurs définis et ajoutés au banc (`docs/INDICATEURS_V2.md`, section 19)
- [x] Chaque attribut agit sur son étage seulement (Finishing et Long Shots sur l'exécution, gardien sur l'arrêt) : exécution croissante avec la note (profils forcés) ; notes du gardien sans effet sur l'arrêt physique, attendu (`v2-attributs-restants/03b`)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 610 passés, 14 désélectionnés (2 608 + 2 tests ajoutés)

## Reprise du 06a (réserve A1 de l'expert, 09/11/2026), préalable à toute exploitation de l'xG après frappe

- L'xG après frappe dépasse les buts de + 0,31 ± 0,12 par match (environ 8 %) à gardien neutre et issue déterministe : un gardien moyen paraîtrait éviter des buts. Ajouter au banc un indicateur de calibration (somme des xG après frappe moins buts sur tirs cadrés non contrés), puis fixer l'étalement (`shooting.PSXG_SPREAD_M`, 0,3 m) : le réduire, ou en faire une vraie dispersion du gardien avec ses notes (`v2-attributs-restants/03b`). Test : à graine d'audit, sur 50 matchs, écart sous 2 erreurs types.

## Réalisé (09/11/2026)

- **Banc** (`scripts/v2_indicators.py`, `scripts/measure_v2.py`) : au tir, tranches de Finishing (surface) ou Long Shots (dehors), de Composure sous pression et de Reflexes du gardien (`on_shot_notes`, contrés compris) ; par tranche, occasion (xG neutre moyen), exécution (xG après frappe − xG neutre) et gardien (xG après frappe − buts), par tir non contré (`shot_decomposition`) ; calibration de l'xG après frappe sur les tirs cadrés jugés, recalculée à cinq étalements. Penaltys exclus.
- **Réserve A1 du 06a** : `shooting.PSXG_SPREAD_M` 0,3 → 0,15 m (validé par délégation du propriétaire). xG après frappe − buts : + 0,33 ± 0,12 → + 0,02 ± 0,09 par match (critère : sous 2 erreurs types). Seul changement du moteur, en lecture seule : le jeu est inchangé.
- **Tests** : `tests/test_v2_indicators.py::test_shot_decomposition_splits_occasion_execution_and_keeper_by_note` (décomposition exacte sur données synthétiques, penalty exclu, recalcul à chaque étalement) ; `test_a_forced_profile_leaves_the_neutral_xg_neutral` (réserve A1 de l'expert : en profil forcé, l'xG neutre ne reçoit pas la note forcée ; échoue sans le correctif).

## Mesures (09/11/2026, graine d'audit, `.scratch/v2-realisme/mesures/06b-*`)

- **50 matchs** (10 lots de 5, `06b-on*`) : jeu identique au 06a (toutes les clés communes égales, lot par lot) ; déterminisme : `06b-on0.json` et `06b-det2.json` identiques hors temps de calcul.
- **Profils forcés** (99 contre 11, 20 matchs chacun, `06b-fin*`, `06b-ls*`, relancés après la réserve A1 de l'expert : copie neutre non forcée) : gain d'exécution par tir non contré, écart 99 − 11 par lot apparié, Finishing dans la surface + 0,139 ± 0,036, Long Shots dehors + 0,030 ± 0,008. Détail et lecture : `docs/INDICATEURS_V2.md`, section 19.
- **Constats pour la suite** : exécution biaisée vers le haut, parce que l'xG neutre compte le contre et que l'xG après frappe ne porte que sur les non-contrés (réserve A2, à corriger au 06c) ; résidu du gain du gardien lié au lissage de l'xG après frappe (06c) ; notes du gardien sans effet sur l'arrêt physique (`v2-attributs-restants/03b`).

## Comments

- 09/11/2026, passage 1 : expert REJECTED (empreinte 4ddf8470) ; QC VALIDÉ ; clôture REFUSÉ (journal `v2-realisme/06b/cloture`). A1 bloquant : en profil forcé, la copie neutre du tireur recevait la note forcée, donc l'xG neutre n'était pas neutre. Corrigé : `shooting.neutral_xg` marque sa copie neutre (`NEUTRAL_ATTRIBUTES`, dictionnaire vide non modifiable, même valeur par défaut que `attributes=None`, trace inchangée) et `measure_v2._force_attribute` ne force pas cette copie ; un test est ajouté. Un premier correctif (« ne pas forcer un joueur sans attributs ») cassait `test_profile_forces_physical_attributes_read_on_database_players` et a été remplacé. Profils relancés (effectifs de tirs identiques à la première série : jeu inchangé), profils relancés et section 19 réécrite. A2 (biais de l'exécution par le contre, à traiter au 06c) et A3 (erreur type appariée, publiée) sont des réserves. A4 facultatif (classer surface ou dehors d'après la position de frappe tracée) n'est pas fait.
- 09/11/2026, passage 2 : expert APPROVED_WITH_RESERVATIONS (empreinte b4862e41, calculée sur 9 fichiers, documentation comprise) ; QC VALIDÉ. Passage non utilisé pour la clôture : la documentation doit rester modifiable après la clôture.
- 09/11/2026, passage 3, clôture : expert APPROVED_WITH_RESERVATIONS (empreinte fa86e690, code et `CLAUDE.md`) ; QC VALIDÉ (passage 2) ; clôture VALIDÉ (journal `v2-realisme/06b/cloture`). Suite complète : 2 610 passés, 14 désélectionnés.
- Réserves acceptées par le propriétaire (« J'accepte A1 et A2 », 09/11/2026) : A1, exécution biaisée vers le haut par le contre (au 06c, comparer l'xG après frappe à la chance neutre hors contre, puis relancer les profils) ; A2, gain du gardien dépendant du tireur, probablement dû au lissage (au 06c, le ventiler par écart à la portée ; ne juger aucun gardien sur cet indicateur avant le 06c et le 03b).
- Facultatifs non traités : A3 (Composure citée à l'étalement 0,3 m dans le §19), A4 (`shot_notes` non purgé entre les matchs), A5 (surface ou dehors lu sur la position courante). À surveiller au 06c : revérifier l'étalement de 0,15 m sur une graine indépendante.
