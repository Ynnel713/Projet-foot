# 03h: Gardien : expliquer la hausse des tirs du 03c et le saut de cible

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (une hausse de buts non expliquée fausse le point d'étape 18a). **Catégorie :** validation.

**Constat vérifié :** au 03c, la chance moyenne des tirs est passée de 0,061 à 0,081 et les buts de 2,75 à 3,60 par match, alors que sur une scène statique un gardien avancé la fait baisser (tir de 20 m axial : 0,055 → 0,049). La cause n'est pas établie (réserve A1 du 03c). Le gardien saute aussi de 5 à 11 m environ entre la ligne de but et la profondeur visée quand le ballon passe de 12 à 40 m (réserve A3 du 03c, reprise du A1 du 03b).

**What to build:** Décomposer la hausse sur 50 à 100 matchs : chance des tirs avec la position réelle du gardien, puis recalculée avec le gardien posé sur la bissectrice, puis mélange de tirs (distances, angles) à position égale. Mesurer le saut de cible (distance à sa ligne en fonction de la distance du ballon, 12 à 40 m) et dire s'il est trop brutal pour le rendu. Aucune constante recalée dans ce ticket : le rapport propose, le propriétaire tranche.

**Attributs :** aucun

**Blocked by:** 03g (Validation du placement et des sorties du gardien).

**Bloque :** 18a, 18e.

**Status:** livré (07/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement (observateurs de décomposition) | 35 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications (rapport) | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : séries appariées sur la graine d'audit, outils de `bench_series.py` (comparaison appariée).
Temps machine, non compté : suite complète (environ 40 min) ; séries de 50 à 100 matchs.

## Tests

- **Unitaires (scène contrôlée) :** décomposition sur des tirs synthétiques à résultat connu
- **Statistiques (séries de matchs) :** 50 à 100 matchs, rapport dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [x] Constantes de mesure proposées avant le code (voir Comments)
- [x] La différence de chance des tirs entre le moteur avec la ligne du 03c et le même moteur sans (`LINE_RATIO = 0`) est répartie en quatre termes qui se somment exactement (dynamique du gardien avec la ligne, effet de sa cible, mélange de tirs, dynamique sans la ligne), 50 matchs appariés, intervalles de confiance à 95 % (`scripts/decomposition_tirs.py`, `docs/INDICATEURS_V2.md` section 12) : écart total −0,0037 [−0,0093 ; +0,0019], termes +0,0059 / −0,0022 / −0,0021 / −0,0054
- [x] Le saut de cible est chiffré (moyen entre deux instants, part au-dessus de 1 m, maximum du match, part du temps en course au-dessus de 5 m/s) et pas de défaut mesuré, aucune correction (piste facultative : lisser la cible sur environ 0,5 s, pas appliquée)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`) : environ 140 min contre 90 estimées (+ 56 %, durée estimée, non chronométrée)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`789933483e9ccb38`, 2 matchs, rapport sans la ligne du temps de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 520 passés, 14 désélectionnés (07/11/2026, état final) ; 2 517 à la clôture du 03g + 3 tests nouveaux ; `CLAUDE.md` indiquait 2 510 (03e) : mis à jour à 2 520 dans ce ticket (fichier revu)

## Comments

- 07/11/2026 : **Point de départ corrigé avant le code.** La hausse du 03c (chance 0,061 → 0,081, buts 2,75 → 3,60, 20 matchs) a été en grande partie résorbée par le 03d (chance 0,063, buts 2,90) puis mesurée à 0,064 et 3,08 au 03g (50 matchs). Il ne s'agit donc plus d'expliquer une hausse présente, mais d'isoler **ce que le placement avec la ligne du 03c fait aujourd'hui** au tir, en comparant deux séries appariées du moteur actuel : avec la ligne (`LINE_RATIO = 0,4`) et sans (`LINE_RATIO = 0`, qui redonne le placement du 03b, méthode du 03c). Estimation inchangée (1 h 30).
- 07/11/2026 : **Constantes de mesure proposées avant le code** (par Claude, validées par délégation du propriétaire, consigne permanente ; aucune constante du jeu). **Décomposition** : pour chaque tir avec gardien adverse, trois chances calculées par `shot_probability` : gardien à sa **place réelle**, à son **point visé** au dernier instant où il pensait en placement ou en face-à-face (sinon sa place réelle), et **sur la bissectrice sans ligne** (`bisector_point` sans hauteur de ligne ni profondeur de face-à-face). Avec A = série avec ligne, B = série sans : P(A,réelle) − P(B,réelle) = [P(A,réelle) − P(A,visé)] + [P(A,visé) − P(A,03b)] + [P(A,03b) − P(B,03b)] + [P(B,03b) − P(B,réelle)] : dynamique de A, effet de sa cible, mélange de tirs, dynamique de B. Mélange de tirs documenté en plus par la chance de l'endroit (`base_chance`) et la distance au but. **Saut de cible** : entre deux instants consécutifs où le gardien est en placement, distance entre les deux points visés ; seuil de **1,0 m** pour un « grand saut » ; course = plus de **5,0 m/s**. Pour limiter la mémoire, ces quatre mesures sont accumulées par match (une valeur par match). **Critères chiffrés** : (1) les quatre termes de la décomposition se somment à l'écart mesuré à 1e-9 près (test sur tirs synthétiques et sur le calcul des séries) ; (2) la série B (`LINE_RATIO = 0`) redonne la chance du 03b sur la bissectrice sans ligne : P(B,03b) = P(B,visé) ; (3) le saut de cible est chiffré sur 50 matchs avec son IC ; (4) aucune constante du moteur n'est modifiée.
- 07/11/2026 : **Mesure (50 matchs appariés, graine d'audit ; A = moteur actuel avec la ligne, B = `LINE_RATIO = 0`)** : chance des tirs **0,0637 contre 0,0684**, écart A − B **−0,0037** [−0,0093 ; +0,0019] ; buts **3,08 contre 3,08** ; tirs par équipe 23,8 contre 23,3. **La hausse du 03c n'existe plus** (elle avait été mesurée sur 20 matchs avant le 03d). Décomposition exacte : dynamique avec la ligne +0,0059, cible −0,0022 (face-à-face seul −0,0011, ligne seule −0,0011), mélange de tirs −0,0021 (non significatif), dynamique sans la ligne −0,0054. La **dynamique** (le gardien est à 1,0 à 1,1 m de son point visé au tir) augmente la chance d'environ 0,0055 dans les deux séries : c'est le plus gros terme, indépendant de la ligne ; hypothèse non démontrée : il relèverait du ticket 03f (biais de sélection possible : les tireurs tirent peut-être quand le gardien est décalé). **Saut de cible** : moyen 0,151 m (0,078 sans la ligne), 1,21 % de sauts de plus de 1 m (0,30 %), 2,47 % du temps en course à plus de 5 m/s (0,85 %), maximum de 20,22 m à chaque match (ballon posé au point de corner). Distance moyenne du gardien à son but +3,87 m avec la ligne.
- 07/11/2026 : **Critère corrigé.** Le critère (2) des Comments précédents (« P(B, 03b) = P(B, visé) ») était faux : le point visé contient la profondeur de face-à-face du 03e, que la bissectrice du 03b ne contient pas (écart de 0,0011 mesuré). La décomposition reste exacte ; le terme « cible » est étiqueté « ligne et face-à-face ». L'écart à la bissectrice au tir du 03g (réserve A4) est complété par « écart à son point visé réel » (cible réelle du gardien, ligne comprise).
- 07/11/2026 : **Limites.** (1) Chances de but par tir non contré selon `shot_probability`, pas des buts : trop bruités pour départager (±0,5 par match). (2) La cause de la disparition de la hausse (le 03d, qui a supprimé les 215 sorties par match sur les passes de son équipe) est une hypothèse, non démontrée par cette mesure. (3) Aucune correction du placement n'est proposée : la ligne ne dégrade pas la chance des tirs. (4) Le plafond de 16 m et la profondeur découverte derrière une ligne haute (03c A2) ne sont pas traités.
- 07/11/2026 : **Clôture (/valider-ticket-simulafoot)** : expert `APPROVED_WITH_RESERVATIONS` (empreinte `f6299535…`), contrôle qualité `VALIDÉ` (un seul passage), décision de clôture `VALIDÉ` (journal). **Réserves A1 à A3** acceptées par délégation permanente du propriétaire (« je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026, non reprise mot à mot dans cette conversation, qui contient « Oui » à la question « Lancer la clôture ... puis le commit ? ») et **leurs conditions sont remplies** : A1 le saut de cible n'est pas mesuré hors remises en jeu ni selon la distance du ballon, conclusion reformulée « pas de défaut mesuré » (doc section 12, ticket, plan) ; A2 l'attribution du terme de dynamique au 03f est une hypothèse, biais de sélection possible (doc, ticket, plan) ; A3 durée réelle relevée ci-dessus et au registre. Facultatifs : A4 l'IC de l'écart total n'exclut pas un effet résiduel de +0,002, très inférieur à la hausse de 0,020 du 03c ; A5 `data/joueurs.xlsx` exclu du commit. QC, non bloquant : la section 12 mélange des moyennes agrégées par tir et des moyennes d'écarts par match (précisé dans le texte). `CLAUDE.md` : compte attendu mis à jour à 2 520.

