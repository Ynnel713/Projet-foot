# 01g: Analyse des écarts entre durées estimées et réelles par catégorie

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (à lancer après 20 à 30 tickets clôturés). **Catégorie :** mesure.

**Constat vérifié :** la règle d'estimation est ajoutée à `CLAUDE.md` le 05/11/2026 avec le registre `docs/agents/suivi-estimations.md` ; aucune analyse n'existe encore.

**What to build:** Script qui lit le registre et donne, par catégorie (mesure, placement, décision, exécution, physique, perception, validation, documentation), le rapport réel / estimé médian, la dispersion et les postes (analyse, développement, tests, intégration) les plus sous-estimés. Proposer un coefficient de correction par catégorie, à valider par le propriétaire.

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** rien.

**Status:** livré (10/11/2026), validé expert + QC

## Réalisation (10/11/2026)

- Script `scripts/analyse_estimations.py` (`uv run python -m scripts.analyse_estimations [registre] [--min-n 5]`), tests `tests/test_analyse_estimations.py` (8 tests : registre factice aux ratios connus, registre réel lu sans rejet, sortie identique sur deux exécutions).
- Sortie sur le registre du 10/11/2026 (55 lignes dont celles du 01g et du 19b, 0 rejet ; lignes 05a, 05b, 05c, 05h reclassées de « autre » en « exécution », réserve A1 de l'expert) : `.scratch/v2-realisme/mesures/01g-analyse.md`. Relancée le 10/11/2026 sur le registre à jour, après la ligne du 19b.
- Mesures : ratio = réel / estimé de la ligne ; médiane, quartiles (méthode inclusive), extrêmes, part des écarts au-delà de 30 % ; postes classés par rapport des sommes réel / estimé (lignes aux deux répartitions connues ; poste à 0 estimé et réel > 0 : ∞).
- Limites : 48 durées réelles sur 55 sont estimées après coup (« non chronométrée ») ; pour 05e et 05g, le registre donne l'estimation révisée (l'initiale aurait donné + 69 % et + 74 %) ; les postes estimés de 05e ne somment pas au total révisé.

### Coefficients proposés au propriétaire (non codés, non appliqués ; valeurs après reclassement A1 et ligne du 01g)

| Catégorie | n | Médiane réel / estimé | Coefficient proposé |
|---|---|---|---|
| validation | 9 | 1,30 | 1,30 |
| décision | 9 | 1,08 | 1,10 |
| mesure | 9 | 1,00 | 1,00 |
| données | 6 | 0,90 | 0,90 |
| placement | 7 | 0,83 | 0,85 |
| exécution, autre, physique, documentation, perception, écran, architecture | 0 à 4 | — | 1,00 (échantillon < 5) |

Poste le plus sous-estimé dans presque toutes les catégories : **intégration** (× 1,56 toutes catégories ; × 1,91 en validation, × 1,90 en mesure) ; développement surestimé (× 0,90). **Décision du propriétaire (10/11/2026)**, relayée par la session du ticket 19b : « Ok avec ta recommandation ». Retenu : d'abord le constat par poste (augmenter la part « intégration » des futures estimations, développement légèrement réduit) ; les coefficients par catégorie ci-dessus servent de repère secondaire. Inscrit dans `docs/agents/suivi-estimations.md`, section « Corrections retenues ». Rien n'est appliqué automatiquement. Après la revue de l'expert (réserve A1, acceptée par délégation du propriétaire) : le repère « autre 1,10 » tombe (n = 3 < 5 une fois les 4 tickets d'exécution reclassés) et « mesure » reste à 1,00 avec la ligne du 01g (médiane 1,00 sur 9 tickets).

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : registre tenu à jour depuis le premier ticket du chantier.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** registre factice : ratios et médianes exacts

## Acceptance criteria

- [x] Analyse produite sur au moins 20 tickets clôturés
- [x] Coefficients proposés au propriétaire
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 10/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ (base 4feac8b, empreinte 27aea231…).
  - A1 [réserve] : 05a, 05b, 05c, 05h classés « autre » au registre au lieu d'« exécution » ; corrigé (registre, sortie relancée, tableau ci-dessus, « Corrections retenues ») : le repère « autre 1,10 » tombe (n = 3).
  - A2 [réserve] : ligne de durée du 01g absente ; ajoutée au registre (90 → 75 min, − 17 %).
  - A3, A4 [facultatif] : parseur sensible à une barre « | » dans une cause ; test du registre réel = garde-fou de format ; coefficients sur 6 à 9 lignes, à revoir à ~30 lignes chronométrées.
  - Réserves acceptées par délégation du propriétaire (consigne du 05/11/2026 : « Considère que je valide automatiquement toutes tes recommandations et celles des experts »).
- Durée (passage 1) : estimé 90 min, réel ≈ 75 min à ce stade ; total après le passage 2 dans l'entrée suivante.
- 10/11/2026, passage 2 (après rebase sur e14b247, ticket 19b ; `CLAUDE.md` ajouté aux fichiers revus pour le compte attendu 2 722) : expert APPROVED, QC VALIDÉ, clôture VALIDÉ.
  - A1 [facultatif] : mentions périmées du ticket et du registre (relance avant commit, « suite : 2 710 ») ; corrigées.
  - A2 [facultatif] : hérité du passage 1 (barre « | » dans une cause ; coefficients à revoir vers 30 lignes chronométrées).
- Durée totale : estimé 90 min, réel ≈ 100 min (+ 11 %, sous 30 %) : passage 1 ≈ 75 min, rebase, relance et second passage de clôture ≈ 25 min. Temps machine hors total : deux suites complètes (48 et 33 min ; état final 2 717 passés, 5 ignorés NLG propres au worktree, 14 désélectionnés).
