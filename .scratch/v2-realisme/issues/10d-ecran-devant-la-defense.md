# 10d: Protection de l'axe : le milieu récupérateur fait écran

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (l'axe devant la surface doit rester fermé quand le ballon est sur un côté). **Catégorie :** placement.

**Constat vérifié :** aucun rôle d'écran : la couverture ferme l'axe seulement derrière le porteur ; les compensations ne visent que les places des DC, LB et RB (`defense.py:108`).

**What to build:** Sans ballon, le rôle « milieu récupérateur » (02c) se place entre le ballon et le centre de son but, devant la ligne défensive, quand le ballon est sur un côté ; il quitte cette place seulement pour un rôle attribué (presseur, marqueur).

**Attributs :** aucun

**Blocked by:** 02e (Place de référence sans ballon selon le rôle).

**Bloque :** 10i, 10j.

**Status:** livré (19/11/2026), validé expert + QC. Périmètre réduit le 19/11/2026 par le propriétaire (« Ok pour ta recommandation, retire l'écran ») : l'écran, mesuré sans effet, est retiré du moteur ; seule la mesure des passes reçues en zone 14 est livrée. Protection de la poche entre les lignes : ticket `10d2`.

## Constantes et critères (19/11/2026, proposés par Claude, validés par le propriétaire : « Parfait vas y »)

Chiffre réel des passes reçues en zone 14 : non trouvé (The Analyst ne donne que la définition, https://theanalyst.com/articles/where-on-the-pitch-does-each-premier-league-team-attack-from ; données Opta payantes).

- **Qui fait l'écran :** un milieu axial par équipe (poste MDC ou MC, hors mezzala, box to box et meneur), par ordre de rôle sentinelle, regista, récupérateur, puis le plus bas de la forme (la lettre du ticket, « récupérateur », n'aurait couvert que 4 équipes sur 18).
- **Place :** sans ballon, sur la droite ballon-centre de son but, `SCREEN_GAP_M` = 8 m devant sa dernière ligne, si le ballon est plus loin que cette hauteur ; glissement linéaire de sa place habituelle à celle d'écran quand le ballon passe de 6 à 12 m de l'axe (`SCREEN_SIDE_M`).
- **Zone 14 (mesure) :** de 16,5 à 30 m du but adverse, 11 m ou moins de l'axe ; passes reçues = réceptions d'une passe au sol, en profondeur, en retrait ou d'un centre.
- **Critères (100 matchs appariés, « avant » = même moteur, écran neutralisé) :** passes reçues en zone 14 en baisse significative (IC à 95 %) ; buts, tirs, passes en profondeur réussies, hors-jeu rapportés, écart non expliqué bloquant.

## Estimation révisée

2 h 10 annoncées avant le code (désignation par ordre de rôle et indicateur zone 14 ajoutés au périmètre). Révisée à 3 h 25 après l'échec de la mesure (diagnostic de 20 matchs, retrait de l'écran, ticket `10d2`), annoncée au propriétaire avec la recommandation.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : priorité des rôles inchangée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Réalisation (19/11/2026)

**Essai de l'écran (retiré)** : `v2engine/bloc.py` (`screen_player`, `screen_place`, `screen_weight`, `Bloc.screens`, place dans `Bloc.reference`), 9 tests (`tests/test_v2engine_ecran.py`) ; le correctif complet est gardé dans `.scratch/v2-realisme/mesures/10d-ecran-retire.patch` pour le ticket `10d2`. Effet de bord relevé pendant l'essai : la garde de Flair (`tests/test_v2engine_garde_attributs.py`) ne divergeait plus en 60 s ; sans l'écran, elle repasse sans changement.

**Mesure, 100 matchs appariés** (collecteur des indicateurs `scripts.measure_v2.run`, graines `AUDIT_SEED + k`, k = 0 à 99 ; `.scratch/v2-realisme/mesures/10d-ecran.py` (sur le moteur de l'essai) et `10d-comparaison.py`, sortie `10d-comparaison.txt`) :

| Par match | avant | après | écart (IC 95 %) | critère |
|---|---|---|---|---|
| Passes reçues en zone 14 | 29,57 | 29,53 | − 0,1 % [− 5,7 ; + 5,5] | **baisse non atteinte** |
| Part des passes reçues en zone 14 | 2,84 % | 2,84 % | | |
| Buts | 5,04 | 4,96 | − 1,6 % [− 13,4 ; + 10,3] | rapporté |
| Tirs | 41,02 | 41,42 | + 1,0 % [− 2,9 ; + 4,8] | rapporté |
| Passes en profondeur réussies | 9,84 | 10,22 | + 3,9 % [− 5,4 ; + 13,1] | rapporté |
| Hors-jeu | 3,70 | 4,10 | + 10,8 % [− 2,8 ; + 24,5] | rapporté |
| Tacles / fautes | 40,06 / 19,64 | 39,39 / 19,32 | − 1,7 % / − 1,6 % | |

Une mi-série (54 paires) montrait + 2 tirs par match, significatif : effacé sur 100 paires (bruit).

**Diagnostic (20 matchs du moteur de l'essai, 582 passes reçues en zone 14 ; `.scratch/v2-realisme/mesures/10d-diagnostic.py`, relevés `10d-diagnostic-{0,5,10,15}.json`)** :
- 89 % de ces passes arrivent quand l'équipe qui défend est en défense placée (transition : 11 %) ;
- l'écran est à 5,8 m de l'axe en médiane : il ne part pas sur le côté ;
- il est entre le receveur et son but dans 20 % des cas seulement (12 % quand il est libre de rôle) : le ballon est reçu derrière lui, à 9 m en médiane, dans la poche entre l'écran et la dernière ligne ou au niveau de la ligne ; par type : passe au sol (51 %) 17 %, passe en retrait (26 %) 38 %, passe en profondeur (23 %) 6 % ;
- il tient un rôle défensif dans 47 % des cas (marquage 19 %, presseur 16 %, couverture 11 %) ; libre, il est à 8 m de sa place de référence en médiane.

**Conclusion** : défaut de conception, pas de réglage : un point fixe devant la ligne ne ferme pas la poche dans son dos. Fermer l'axe demande de prendre en charge l'adversaire qui décroche entre les lignes (rôle défensif dans `defense.py`) : ticket `10d2`, à lancer quand une référence réelle montre que la zone 14 est trop fréquentée.

**Livré** : place du receveur au contrôle dans la trace (`ReceptionEvent.x`, `.y`, écrite dans `match._step_loose_ball`, lecture seule) ; `scripts/v2_indicators.py` : `in_zone_14`, comptes « passes reçues » et « passes reçues en zone 14 » ; `scripts/measure_v2.py` : deux indicateurs du rapport. Tests : `tests/test_v2engine_zone14.py`, 3 tests (zone, comptage du collecteur, trace déterministe). Le jeu est inchangé (voir Déterminisme).

**Déterminisme et jeu inchangé** : matchs complets clubs[0] contre clubs[1], empreinte sha256 du score, des tirs (minute, tireur) et des réceptions (minute, joueur, origine) : 20260923 : 1-1, 1 391 réceptions, `f632b575faf2` ; 20260924 : 0-0, 1 267 réceptions, `19056e340088` ; identiques sur deux processus séparés de l'arbre de travail et sur le commit `58bf387` (avant le ticket) : le jeu ne change pas.

**Suite complète** (19/11/2026) : 3 440 passés, 0 ignoré, 14 désélectionnés (3 437 après le 10c + 3 tests nouveaux), 15 min 25.

**Durée réelle** : environ 3 h 25 de travail effectif (analyse 40 min, développement 50 min, tests 35 min, intégration et vérifications 80 min, dont diagnostic 45 min et retrait 35 min) contre 2 h 10 estimées avant le code, soit + 58 % ; cause : critère principal manqué, diagnostic puis retrait de l'écran et ticket de suite ; estimation révisée à 3 h 25 et annoncée avec la recommandation. Temps machine hors total : 200 matchs (environ 3 h, dont une reprise après arrêt des processus par manque de mémoire, la mémoire croissant par match dans un même processus), diagnostic de 20 matchs, deux suites complètes, trois paires d'empreintes. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée.

## Tests

- **Unitaires (scène contrôlée) :** ballon dans le couloir droit : le récupérateur est entre ballon et axe du but, devant la ligne (essai, retiré avec l'écran)

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (19/11/2026)
- [ ] ~~Passes adverses reçues dans l'axe devant la surface en baisse mesurée~~ : non atteint (− 0,1 %, IC ± 5,6 %) ; écran retiré, critère reporté au ticket `10d2` (décision du propriétaire, 19/11/2026)
- [x] Passes reçues en zone 14 mesurées (indicateur livré, 29,5 par match, 2,84 % des passes reçues)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (3 440 passés)

## Comments

- **19/11/2026, passage 1 :** expert APPROVED ; remarques facultatives : A1 `10d-ecran.py` ne tourne que sur le moteur de l'essai (appliquer `10d-ecran-retire.patch` avant de le relancer, au 10d2) ; A2 `x`/`y` à 0,0 par défaut dans `ReceptionEvent` (une trace qui ne les renseignerait pas compterait hors zone sans échouer ; seul producteur `match.py`, couvert par le test de trace). QC VALIDÉ. Clôture journalisée : VALIDÉ.
- **19/11/2026, passage 2 :** commit refusé par le verrou (`CLAUDE.md`, attendu de la suite passé à 3 440, indexé sans être revu) : `CLAUDE.md` ajouté aux fichiers revus. Expert APPROVED (hunks du code identiques au passage 1 ; A1 et A2 facultatives, inchangées). QC VALIDÉ. Clôture journalisée : VALIDÉ.
