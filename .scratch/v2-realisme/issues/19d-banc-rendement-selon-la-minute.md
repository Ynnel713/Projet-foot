# 19d: Banc : rendement selon la minute et la fatigue (état des lieux)

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P0 (avant 18a : mesurer ce que la fatigue change aujourd'hui avant de construire 12d, 12e et 20). **Catégorie :** mesure.

**Constat vérifié :** la fatigue ne dépend que de la minute et de Stamina, et n'agit que sur la vitesse maximale (`movement.stamina_factor`, `movement.py:60`) ; aucun indicateur du banc ne découpe le match par tranche de temps.

**What to build:** Indicateurs par tranche de 15 minutes, par joueur et par poste : distance, distance au-dessus de 19,8 et 25 km/h, sprints, réussite des passes et des contrôles, cadrage, duels gagnés, hauteur du bloc, buts marqués et encaissés. Comparaison de la première et de la dernière tranche par note de Stamina. Scène A/B : même joueur à la 15e et à la 85e. Section nouvelle de `docs/INDICATEURS_V2.md`. Lecture seule.

**Attributs :** aucun

**Blocked by:** 01d, 01e (livrés).

**Bloque :** 18a ; 20d.

**Status:** livré (11/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : élevée. Hypothèses : lecture de la trace et de l'observateur existant.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : profil par tranche publié ; hypothèse à vérifier : seules les grandeurs de course baissent, la technique et les décisions sont plates

## Acceptance criteria

- [x] Section publiée dans `docs/INDICATEURS_V2.md`
- [x] Constat chiffré sur ce que la fatigue change et ne change pas
- [x] Jeu inchangé
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (10/11/2026)

- Critères chiffrés posés avant le code : indicateurs par tranche de 15 min (0-15 à 75-90, puis « 90 et plus ») et par poste ; comparaison 0-15 contre 75-90 par tranche de Stamina (0-40, 40-55, 55-70, 70 et plus) ; scène A/B où la course baisse à la 85e et la probabilité de passe est identique ; aucun fichier du moteur modifié ; série identique sur deux exécutions ; suite complète égale à l'attendu plus les tests ajoutés.
- Code : `scripts/v2_tranches.py` (`MinuteProfile`, `minute_report`, `block_height_by_tranche`), nourri par `v2_indicators.Collector` (course à chaque tick, passes du journal du banc, tacles, tirs, buts, contrôles ratés lus dans `MatchTrace.events`) ; clé « rendement par tranche de 15 min » de `measure_v2.report` ; fusion des tranches dans `bench_series` (séquentiel et parallèle identiques, test). Aucun fichier de `v2engine/` modifié.
- Tests : `tests/test_v2_tranches.py` (6 tests, dont la scène A/B : 18,8 m en 4 s à la 15e, 15,2 m à la 85e avec Stamina 20, 18,3 m avec Stamina 99, probabilité de passe 0,720 aux deux minutes) ; `tests/test_bench_series.py` étendu (fusion des tranches).
- Mesure (50 matchs, `docs/INDICATEURS_V2.md` section 23, `.scratch/v2-realisme/mesures/19d-det1.*`) : seule la course rapide baisse, et seulement dans la tranche 75-90 : sprints 20,1 → 14,6 par joueur et par 15 min (− 27 %), part au-dessus de 25 km/h 0,170 → 0,123, au-dessus de 19,8 km/h 0,379 → 0,348 ; baisse selon Stamina (course au-dessus de 19,8 km/h × 0,73 sous 40, × 0,94 à 70 et plus). Distance totale par minute plate (rapport 0,99 à 1,01 à toutes les notes), passes réussies 0,70 à 0,72, contrôles ratés 6,2 à 7,5 pour 100 passes, cadrage, tacles et hauteur du bloc sans tendance. Hypothèse du ticket confirmée.
- Déterminisme : série de 50 matchs jouée deux fois (`19d-det1.json`, `19d-det2.json`), 1 918 valeurs identiques, seul le temps de calcul diffère.
- Suite complète : 2 728 passés, 14 désélectionnés (2 722 + 6, `.scratch/v2-realisme/mesures/19d-suite.txt`, 19 min).
- Durée : estimée 105 min, réelle environ 110 min (analyse 25, développement 35, tests 25, intégration 25 ; estimée, non chronométrée), + 5 %. Temps machine hors total : 2 séries de 50 matchs (46 min chacune, contre 10 min estimées : environ 6 min par match et par processus sur 7 processus, au lieu des 75 s de référence) ; suite complète.
- Points à vérifier : aucun à l'écran (mesure seule).

## Reprise après le refus du contrôle qualité (11/11/2026)

- Refus QC du 10/11/2026 : « par joueur et par poste » n'était tenu que pour la course ; passes, contrôles, cadrage, duels, bloc, sprints et course au-dessus de 25 km/h seulement globaux ; buts marqués et encaissés confondus ; réduction de périmètre non déclarée.
- Critères posés avant le code : chaque indicateur du What to build par poste, par tranche de Stamina et par joueur, à chaque tranche ; buts marqués et encaissés séparés ; écarts de définition déclarés ; chiffres « tous joueurs » du premier passage identiques (jeu inchangé) ; mêmes valeurs sur deux exécutions.
- Code : `MinuteProfile` attribue chaque événement à son auteur (passeur, receveur visé, tireur, tacleur, buteur du journal) et le compte pour « tous », son poste, sa tranche de Stamina et lui-même ; `on_goal` compte le but marqué ou encaissé pour chaque joueur de champ présent ; `group_metrics`, `minute_report` (postes et Stamina, toutes les tranches et comparaison 0-15 / 75-90), `player_report` (chaque joueur, puis déciles des écarts). Le collecteur passe le tacleur (`on_tackle`, `on_tackle_won`), le tireur et la position sans ballon ; la série parallèle fusionne aussi les joueurs (`MinuteProfile.merge`).
- **Écarts déclarés** (section 23 bis) : la hauteur du bloc reste une grandeur d'équipe, donnée par tranche ; par joueur et par poste, elle est remplacée par la **position sans ballon** (distance moyenne à son but quand son équipe n'a pas le ballon). Les buts par joueur et par poste sont ceux de son équipe pendant qu'il est sur le terrain (marqués, encaissés), plus ses buts personnels, pour 90 minutes jouées. Les contrôles ratés d'un groupe se rapportent à ses passes visées.
- Tests : 3 ajoutés à `tests/test_v2_tranches.py` (attribution au joueur, au poste et à Stamina de tous les indicateurs, buts marqués et encaissés ; rapport par joueur et synthèse ; collecteur branché : tacleur, buts, position sans ballon) ; `tests/test_bench_series.py` : synthèse par joueur identique en séquentiel et en parallèle.
- Mesure (50 matchs, `19d-v2-det1.*`, section 23 bis) : sprints de − 19 % (MDC) à − 36 % (AG) entre 0-15 et 75-90 ; par joueur, rapport médian des sprints 0,73 (déciles 0,45 et 0,95), corrélé à Stamina (0,67 sur 180 joueurs) ; technique, duels et position sans ballon sans tendance commune (médiane des joueurs à 0). Seulement 7 joueurs sous 55 de Stamina, dont un seul sous 40 : ces lignes sont des cas, pas des moyennes.
- Déterminisme : 10 matchs rejoués (`19d-v2-det2.json`), 21 730 valeurs par match identiques ; 77 chiffres « tous joueurs » du premier passage identiques.
- Suite complète : 2 731 passés, 14 désélectionnés (2 728 + 3, `.scratch/v2-realisme/mesures/19d-v2-suite.txt`, 25 min).
- Durée de la reprise : environ 60 min (analyse 10, développement 25, tests 15, intégration 10). Total du ticket : estimé 105 min, réel environ 170 min, + 62 %. Cause : le What to build demandait « par joueur et par poste » pour tous les indicateurs, lu au premier passage comme « par poste pour la course » ; le refus du contrôle qualité a imposé une reprise complète du découpage. Temps machine hors total : une série de 50 matchs (66 min sur 6 processus, en parallèle d'une série de 10 matchs sur 2), suite complète (25 min).

## Comments

- 10/11/2026, passage 1 : QC REFUSÉ (indicateurs par poste seulement pour la course, rien par joueur, buts marqués et encaissés confondus, réduction non déclarée) ; repris le 11/11/2026.
- 11/11/2026, passage 2 : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ.
  - Réserve A1 : tranches découpées sur l'horloge du moteur, pas sur le temps joué (« 75-90 » couvre environ 72,5 à 87,5 minutes jouées). Définition corrigée au §23 ; découpage au temps joué au ticket 19f, avant le 18a.
  - Réserve A2 : contrôles ratés (tout contact raté, interceptions comprises) rapportés aux seules passes visées ; niveau des défenseurs gonflé. Lecture corrigée au §23 bis ; dénominateur par tentative au 19f.
  - Facultatif A3 (but contre son camp compté en but personnel du dernier toucheur adverse) : repris au 19f ; A4 (homonymes) déjà déclaré.
  - Réserves acceptées par le propriétaire : « Considère que je valide automatiquement toutes les recommandations, tous les conseils d'expert et tous les commits si la situation est favorable » (11/11/2026).
