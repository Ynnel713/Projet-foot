# 12f: Répéter les sprints et récupérer

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la capacité à enchaîner les efforts différencie les profils). **Catégorie :** physique.

**Constat vérifié :** aucune notion de sprint répété : un joueur peut sprinter sans fin (vitesse maximale bornée seulement par la minute).

**What to build:** Une composante rapide de la réserve (anaérobie) se vide pendant un sprint et se recharge en quelques dizaines de secondes ; vide, le joueur ne peut plus sprinter (intensité plafonnée). Natural Fitness reste hors du match (D-V10) ; Stamina règle la recharge.

**Attributs :** Stamina (recharge)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-collectif/12` : répétition des efforts.

**Blocked by:** 12e (Réserve d'énergie qui dépend de l'effort).

**Bloque :** 12g, 20d, 20g (ajouté le 10/11/2026, audit de la roadmap).

**Status:** livré (14/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : constantes de recharge à sourcer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** 5 sprints de 30 m espacés de 10 s : vitesse décroissante ; espacés de 60 s : stable

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (délégation du 13/11/2026 : « je valide automatiquement toutes tes recommandations »)
- [x] Effet de répétition mesuré en scène (5 sprints de 30 m, Pace 80, Stamina 55 : pointe 9,23 → 8,78 m/s à 10 s d'intervalle, − 4,9 % ; 9,23 → 9,02 à 20 s ; 9,23 → 9,21 à 60 s ; Stamina 5 / 99 à 20 s : 8,92 / 9,14)
- [x] Sprints par match rapportés (17,9 par joueur de champ et par match sur 50 matchs, graines 50 à 99 ; − 0,37, IC − 0,97 ; + 0,24, contre le 12b sur 30 matchs appariés)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (Stamina, champ dédié lu dans `movement` comme au 12e ; carte mise à jour ; pas de double comptage : la réserve lente du 12e règle l'endurance du match, la réserve rapide la répétition des sprints)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`12f-det1`, `12f-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 955 = 2 948 + 7)

## Comments

**14/11/2026, constantes proposées et validées par délégation du propriétaire** (« je valide automatiquement toutes tes recommandations », 13/11/2026). Réserve rapide (famille W' de Skiba) vidée de l'excès de vitesse au-dessus de 25 km/h (seuil de sprint du banc, 01d), taille 20 m d'excès ; rechargée sous ce seuil vers le plein, exponentiellement, constante de temps 40 s à Stamina 5, 30 s à 55, 20 s à 99 (la phosphocréatine se reconstitue à moitié en 20 à 30 s, Glaister 2005, ordre de grandeur) ; sous 80 % de réserve, la part de la vitesse max au-dessus de 25 km/h est multipliée par la racine de (réserve / 0,8) ; vide, 25 km/h au plus. Réel : baisse de 3 à 8 % sur une série de sprints courts avec 20 à 30 s de récupération (tests de répétition des sprints, ordre de grandeur) ; valeurs du modèle non trouvées telles quelles. Natural Fitness reste hors du match (D-V10). Estimation annoncée au démarrage : 1 h 55 (celle du ticket).

**14/11/2026, réglage en scène (avant le code définitif).** Première forme (genou 0,5, plafond proportionnel, réserve 6 m) écartée : le premier sprint de 30 m était déjà bridé et un sprint de 60 m perdait 23 %. Forme proportionnelle sans genou écartée : elle baissait la pointe de tout premier sprint (− 1,5 %), donc la vitesse calée par Pace. Retenue : genou 0,8, racine, réserve 20 m : premier sprint intact (9,23 m/s comme sans réserve), sprint de 60 m d'une traite − 5 % entre la pointe et l'arrivée, répétition à 10 s − 4,9 %, à 20 s − 2,3 %, à 60 s − 0,2 %.

**14/11/2026, implémentation.** `PlayerCondition.sprint_energy` (condition.py), `movement.spend_sprint_energy` et `movement.sprint_cap_mps` ; dans `movement.step`, le plafond de sprint s'applique à la vitesse max (Pace x réserve lente du 12e) avant la part d'intensité `speed_factor`. Tests : `tests/test_v2engine_sprints_repetes.py` (plafond, vidage et recharge selon Stamina, scène du ticket à 10 s et à 60 s, Stamina 99 > 55 > 5, sprint court intact).

**14/11/2026, mesure.** Série de 50 matchs (graines 50 à 99, `bench_series`, `.scratch/v2-realisme/mesures/12f-serie.txt`) ; comparaison appariée des 30 premiers contre l'état du 12b (`12f-comparaison-12b.txt`) : sprints par joueur − 0,37 (− 0,97 ; + 0,24), distance au-dessus de 25 km/h − 0,04 point, km − 0,05, buts + 0,3, xG − 0,12 : aucun écart significatif ; 156 indicateurs significatifs sur environ 2 660, le niveau du hasard. Diagnostic hors dépôt (`12f-diagnostic.py`, `12f-diagnostic.txt`, 2 matchs) : la réserve rapide n'est sous le genou (0,8) que 0,14 % des joueur-ticks et 2,1 % des ticks de sprint ; minimum 0,57. **Le mécanisme ne mord presque jamais en match** : les sprints du moteur sont courts et espacés (18 par joueur et par match), la réserve se recharge entre deux. Il agit dans les enchaînements rares (contre-attaque après un repli, pressing répété) et sur les longues courses (plafond à 25 km/h après environ 10 s à fond). Aucun réglage pour le faire mordre davantage : ce serait le caler sans repère réel de match (décrément de vitesse par sprint enchaîné en match : non trouvé) ; à reprendre si l'écran ou la calibration finale le demandent.

**14/11/2026, interaction avec le 12e (deux tests corrigés).** Première suite : 2 échecs dans `tests/test_v2engine_movement.py` (scènes du 12e : 60 s, puis 40 s, de course à fond). Le 12f plafonne cette course à 25 km/h après une dizaine de secondes, donc la réserve lente se vide moins (0,806 au lieu de moins de 0,8) et les deux niveaux de Stamina finissent au même plafond. Ces scènes isolent désormais la réserve lente (réserve rapide neutralisée par `monkeypatch`), et un test nouveau fixe l'interaction (course longue tenue à 25 km/h, réserve lente moins vidée qu'avec une réserve rapide infinie). Aucun test supprimé ni désélectionné.

**14/11/2026, suite et déterminisme.** Après correction des deux scènes du 12e : 2 955 passés, 0 ignoré, 14 désélectionnés (2 948 + 7 : 6 tests du 12f et le test d'interaction ; `12f-suite.txt`) ; `CLAUDE.md` mis à jour. `12f-det1` et `12f-det2` identiques hors temps de calcul (moteur inchangé depuis : seuls des tests ont été corrigés). V1 inchangée.

**14/11/2026, durée.** Estimation 1 h 55 ; durée réelle environ 1 h 50 (analyse 15, développement 40 dont le réglage en scène de trois formes, tests 25, intégration 30 dont le diagnostic et la correction des scènes du 12e), − 4 %, sous 30 %. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : série de 50 matchs (environ 48 min), diagnostic 2 matchs, deux suites complètes, déterminisme 2 x 2 matchs.

**14/11/2026, passage 1 de l'expert : APPROVED_WITH_RESERVATIONS (empreinte a91907c1).** Réserves traitées, sur la délégation du propriétaire (« Considére que je valide automatiquement toutes tes recommandations et tous les conseils d'experts », 13/11/2026) : A1, `test_one_short_sprint_is_untouched` ne vérifiait rien (référence retombée à une réserve de 1) : référence par `monkeypatch` de `SPRINT_RESERVE_M` à l'infini ; le test échoue bien avec une réserve de 6 m (vérifié), passe avec 20 m. A2, calage sous le repère réel cité : commentaire de `movement.py` corrigé (− 2,3 % à 20 s, − 1,0 % à 30 s, sous les 3 à 8 % réels mesurés sur le temps de sprint ; recalage laissé à la calibration finale). A3, mécanisme presque inerte en match : inscrit dans `docs/INDICATEURS_V2.md` (écart des attaquants du 18d, non résolu) et dans les tickets 12g et 20d. A4 (facultatif) : la documentation part dans le même commit que le code. Suite après corrections : 2 955 passés, 0 ignoré, 14 désélectionnés (inchangé, `12f-suite.txt`).

**14/11/2026, clôture (passage 2).** Expert : APPROVED (empreinte d4d909a1). QC : VALIDÉ. Clôture journalisée : VALIDÉ. Facultatifs de l'expert : A1, plafond de sprint appliqué avant `speed_factor` (un porteur à réserve vide conduit à 0,8 x 25 km/h au lieu de 0,8 x sa vitesse max ; négligeable, 0,14 % des joueur-ticks ; correctif `min(v_max·speed_factor, plafond)` à évaluer à la calibration) ; A2, documentation dans le même commit (fait). À surveiller : calage sous le repère réel, mécanisme presque inactif en match (12g, 20d, calibration finale).

