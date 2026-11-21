# 28a: Engagement autour du ballon : mesure et diagnostic par rôle

**Chantier :** `v2-realisme` (audit de réalisme du propriétaire du 21/11/2026, point « effet grappe »). **Priorité :** P1 (premier défaut visible à l'écran). **Catégorie :** mesure.

**Constat vérifié (21/11/2026, script d'audit hors dépôt, 2 matchs moteur à graines `20260923 + 500 + k` contre les 2 matchs Metrica, gardiens exclus, une image par seconde ; ballon mort exclu côté moteur seulement : côté Metrica, seules les images sans ballon détecté sont exclues, les arrêts de jeu où le ballon reste suivi sont comptés ; 2 matchs de chaque côté, images autocorrélées) :**

| Indicateur | Moteur | Metrica |
|---|---|---|
| joueurs de champ (deux équipes) à moins de 10 m du ballon | 4,6 (Q1–Q3 3–6) | 3,4 (2–5) |
| à moins de 15 m | 7,5 (6–9) | 5,9 (4–8) |
| à moins de 20 m | 10,7 (9–13) | 8,6 (6–11) |
| distance moyenne au coéquipier le plus proche | 9,8 m | 11,0 m |
| largeur d'équipe | 41,1 m (36,9–45,6) | 42,1 m (34,9–49,4) |
| part de l'équipe du côté du ballon (ballon hors du couloir central) | 68 % | 69 % |

L'excès est **local** (+ 35 % à 10 m) ; la largeur moyenne et le décalage latéral du bloc sont au niveau du réel. L'écart minimal entre appels existe déjà (`off_ball.SPACING_MIN_M = 8 m`) et ne vise que les appelants. On ne sait pas aujourd'hui **qui** converge : chasseur (`11l`), presseur et suiveurs (`v2-collectif/08`, `27`), soutien, couverture, receveur qui vient au ballon (`v2-socle/01`).

**What to build:**
1. Indicateurs au banc (`scripts/v2_indicators.py`, partagés avec `scripts/suivi_distributions.py` comme au 27b) : joueurs de champ à moins de 10, 15 et 20 m du ballon, par équipe (avec / sans ballon) et au total ; distance au coéquipier le plus proche. Même définition côté moteur et côté suivi réel (SkillCorner toutes positions et Metrica), référence chiffrée écrite dans `docs/INDICATEURS_V2.md` ; la référence qui fait foi est SkillCorner ballon en jeu (possession connue), avec la dispersion entre matchs, avant tout chiffrage du plafond du 28b.
2. Diagnostic : pour chaque joueur à moins de 15 m du ballon, son intention du pas (`cerveau` : chasseur, presseur, suiveur, soutien, appel, couverture, place de référence, receveur) ; part de chaque intention dans l'excès, par zone du ballon.
3. Recommandation chiffrée pour le `28b` (quelles intentions plafonner, de combien).

**Hors de ce ticket :** toute modification du jeu.

**Attributs :** aucun.

**Blocked by:** 27b (livré).

**Bloque :** 28b.

**Status:** livré (21/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (indicateurs, diagnostic par intention) | 45 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications (référence réelle, rapport) | 30 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : l'intention de chaque joueur est lisible dans `cerveau` sans changer le jeu ; les lecteurs du suivi réel du 27b sont réutilisés tels quels.
Temps machine, non compté : suite complète ; banc de 50 matchs ; lecture des 20 + 2 matchs réels (environ 1 min 10 s).

## Acceptance criteria

- [x] Mêmes fonctions de mesure pour le moteur et le suivi réel ; références SkillCorner et Metrica écrites (médiane, quartiles)
- [x] Scène fixe : le compte de joueurs à moins de 10 m est exact (test unitaire)
- [x] Diagnostic sur 50 matchs : part de chaque intention parmi les joueurs à moins de 15 m, par zone du ballon
- [x] Recommandation pour le 28b, chiffrée, soumise au propriétaire
- [x] Jeu inchangé : mêmes empreintes à graine fixée avant / après
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**Implémentation (21/11/2026).**
- Code : `scripts/v2_indicators.py` (`NEAR_BALL_RADII_M`, `ENGAGEMENT_RADIUS_M`, `engagement_role`, `players_within`, `mean_nearest_teammate`, `Collector.on_target`, `Collector._engagement`, appelé par `_geometry`, ballon mort exclu, zones vues de chaque équipe) ; `scripts/measure_v2.py` (cible, action et raison de l'intention transmises au collecteur, `engagement_report`) ; `scripts/suivi_distributions.py` (`near_ball`, une image par seconde, par zone vue de chaque équipe, moyenne par match pour la dispersion, moyenne regroupée dans le rapport). Aucun fichier du moteur modifié.
- Tests : `tests/test_v2_indicators_engagement.py` (11 tests : comptes à rayon strict, distance au plus proche coéquipier, fonctions partagées avec le réel, scène réelle et ballon hors jeu, zones réelles vues de chaque équipe, scène moteur et diagnostic par rôle, ventilation du rôle presseur, presseur attribué et sortie de bloc en deux entrées, ballon mort non échantillonné, rapport, rapport sans échantillon) ; `tests/test_suivi_distributions.py` adapté (compteur d'images d'engagement dans les volumes).
- Mesures : `.scratch/v2-realisme/mesures/28a-moteur-50.json` (50 matchs, graines 0 à 49), `28a-reel.json` (20 matchs SkillCorner, 2 Metrica) ; rapport `docs/INDICATEURS_V2.md`, section 55.

**Passage 1 de l'expert (21/11/2026) : REJECTED.** A1 et A2 bloquants : la « couverture » mesurée est celle de `defense.py` (`COVER_DEPTH_M`, 6 m), pas celle du 11g, et la lecture de zone était inversée (les 0,80 de couverture au « tiers offensif » de l'équipe en possession sont la défense près de son propre but, pas un pressing haut). A3 bloquant : le rôle « presseur » réunissait presseur attribué, couverture du 11g et sortie de bloc. Corrigé : ventilation du rôle presseur par l'action de l'intention, zones vues de chaque équipe, référence réelle par zone (A5), moyenne regroupée réelle (A4) ; recommandation réécrite.

**Résultat.** Joueurs de champ à moins de 10 m du ballon : moteur 4,50 (moyennes par match 4,43–4,57) contre SkillCorner 3,83 (3,76–3,99), + 18 %. Par zone vue de l'équipe qui défend : près de son but 2,83 contre 2,77 (conforme), **tiers médian 2,58 contre 1,85 (+ 40 %)**, pressing haut 1,68 contre 1,31 (+ 28 %). Équipe en possession : dernier tiers **1,57 contre 2,11 (− 26 %)**, relance 2,25 contre 1,73 (+ 30 %).

**Diagnostic, équipe sans ballon au tiers médian, à moins de 15 m (joueurs par échantillon)** : marquage 1,19, replacement 1,02 (cible ailleurs dans 36 % des cas, tous tiers), presseur attribué 0,90, couverture attribuée 0,46, couverture du 11g 0,07, sortie de bloc vers le ballon < 0,01, ballon libre 0,08.

**Recommandation pour le 28b (à valider par le propriétaire)** : viser l'équipe qui défend au tiers médian (10 m : 2,58 vers 1,85 ; 15 m : 4,20 vers 3,29), puis son pressing haut (1,68 vers 1,31) ; ne rien plafonner près de son propre but. Leviers : marquage qui suit son homme dans la zone du ballon, replacement qui la traverse, couverture attribuée. La dépendance du 28b au `11l` peut être levée (chasseur 0,09 ; à trancher). Le manque de monde de l'équipe en possession dans le dernier tiers (− 26 %) relève du jeu sans ballon (`25c`, `25e`, `09f`), pas du 28b.

**Vérifications.** Jeu inchangé : 2 519 indicateurs sur 2 519 identiques sur les matchs 0 et 1 (code d'avant contre code d'après). Déterminisme : 82 indicateurs d'engagement identiques sur deux exécutions (`c0fbfdda…`) ; référence réelle identique sur deux exécutions (`e8122f3f…`). Suite complète : voir le rapport de clôture.

**Constat hors ticket.** Buts par match 5,06 sur ces 50 matchs (4,72 à la série du 21c1, 16/11 ; repère réel 2 à 3,5) : dérive connue, hors du périmètre (mesure seule), à traiter en calibration (`18l`, `v2-collectif/22a`).

**Clôture (21/11/2026).** Expert : passage 1 REJECTED (A1 à A3 bloquants, corrigés, voir plus haut), passage 2 APPROVED, passage 3 **APPROVED** (même contenu, périmètre FICHIERS ramené au code, aux tests et à `CLAUDE.md` selon la convention du verrou ; empreinte `a5498581…`). QC : **VALIDÉ**. Clôture journalisée : VALIDÉ. Points facultatifs de l'expert non repris (une retouche du code rouvrirait la revue), à reprendre au passage dans le 28b : couverture du 11g au pressing haut écrite « — » dans la table de la section 55 au lieu de 0,03 ; côté réel, à 10 m par zone, moyenne des moyennes par match (tiers médian 1,85) au lieu de la moyenne regroupée (1,83) ; docstring de `suivi_distributions.py` sans la ventilation par zone. À surveiller au 28b (expert) : ne rien plafonner dans le dernier tiers défensif ; mesurer l'effet sur les cibles par zone ; vérifier zone 14 et passes en profondeur subies ; levée de la dépendance au 11l à trancher par le propriétaire.

**Durée.** Estimée 2 h (20 / 45 / 25 / 30 min) ; réelle environ 1 h 40 (analyse 15, développement 35 dont la correction du passage 1, tests 20, intégration et vérifications 30), à l'horloge de la session hors attentes machine (deux bancs de 50 matchs d'environ 30 min, deux suites complètes de 13 min), non chronométrée : − 17 %, sous le seuil de 30 %.
