# 08c: Scan visuel avant la réception

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** aucun regard volontaire : le seul geste de « lever la tête » est l'intention textuelle pendant la réception (`cerveau.py:152`).

**What to build:** Un joueur sans ballon peut tourner brièvement la tête (scan) pour mettre à jour sa mémoire hors de son cône ; la fréquence des scans dépend d'un attribut à trancher (recommandation : Vision, qui règle déjà « quelles options il voit » ; Anticipation déjà chargée de la lecture). Un scan coûte un court instant pendant lequel il ne suit plus le ballon.

**Attributs :** Vision (fréquence des scans) ; porteur : Dribbling + Technique cumulés (tête haute) ; parts et constantes proposées au propriétaire avant le code

**Blocked by:** 08b (Mémoire de perception : positions vues, datées et vieillissantes); 07c (Réception de face, de profil ou dos au jeu).

**Bloque :** 08e, `v2-collectif/31`.

**Status:** livré (13/11/2026), validé expert + QC

**Point de vigilance :** Vision règle déjà la portée des passes envisagées (`decision.visible_teammates`) : le scan ne doit pas recompter cette portée.

**Élargi le 13/11/2026 (propriétaire, pendant le 08a).** « Le champ de vision dépend de si le joueur a le ballon ou pas, s'il est arrêté ou en mouvement, un joueur technique a moins besoin de regarder le ballon [...] Un joueur avec un gros QI foot prend l'info plus tôt » ; « ça dépend de la vitesse et de s'il a du monde autour de lui [...] si les adversaires sont plus éloignés il est plus libre et peut mieux prendre l'info ». À intégrer :
- **le porteur aussi** : en conduite, il garde la tête basse une part du temps (il voit peu au-delà du ballon), d'autant moins qu'il est à l'aise balle au pied : **cumul Dribbling + Technique**, parts à proposer (décision du propriétaire : « un peu de dribbling et un peu de technique avec un coeff bien dosé », R2 révisée) ;
- **fréquence des scans** selon Vision (prise d'information, « QI foot »), **la vitesse** (moins de scans à pleine course) et **la gêne** (`possession.pressure` : adversaires proches, moins de temps pour scanner loin) ;
- sources à chercher : fréquences de scan de Jordet (Premier League, avant la réception, selon le poste et la pression), effet de la vitesse ; à défaut, « non trouvé ».
Périmètre plus large que l'estimation de 2 h : à réestimer et à examiner pour découpage avant le code (par exemple sans ballon, puis porteur).

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h**, réestimé à **3 h 10** le 13/11/2026 (périmètre élargi : porteur, vitesse, gêne ; pas de découpage, décision du propriétaire) |

Confiance : moyenne. Hypothèses : fréquences réelles de scan à sourcer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** après un scan, la mémoire des joueurs dans le dos est à jour
- **Comportementaux (profils comparés) :** Vision 99 contre 11 : plus de scans par minute avant réception

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (proposées le 13/11/2026, validées par « fais tout dans le même ticket » ; sources et « non trouvé » dans `scan.py` et Comments)
- [x] Scans tracés (`MatchTrace.scans`, un `ScanEvent` par début ; banc : `measure_v2`, `v2_indicators.on_scans`)
- [x] Effet de l'attribut retenu mesuré en scène A/B (Vision 99 contre 11 : 4,4 contre 0,7 scans dans les 10 s avant la réception ; tests unitaires et `measure_v2 2 --profil Vision`, `08c-vision.txt`)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (`ALLOWED` : Vision, Dribbling, Technique, Pace lus dans `scan` ; cumul Dribbling + Technique dans `TOLERATED_MIXES` ; carte : lignes des quatre attributs et dérogation A15)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`08c-det1`, `08c-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 843 passés, 0 ignoré, 14 désélectionnés = 2 833 + 10 ; `08c-suite.txt`)

## Comments

**13/11/2026, lancement.** « lance le 08c ». Périmètre élargi à examiner pour découpage : découpage proposé (08c sans ballon, 08g porteur), refusé par le propriétaire : « fais tout dans le même ticket ». Estimation annoncée : 3 h 10, confiance moyenne.

**13/11/2026, constantes.** Proposées, puis validées avec la réponse du propriétaire (porteur compris) : scan de 0,3 s pendant lequel le joueur voit tout autour (cône de 100° plus environ 80° de rotation de tête) ; fréquence de base par Vision 99 → 0,6 scan/s, 55 → 0,3, 11 → 0,1 (Lampard 0,62 et Gerrard 0,61 scan/s avant la réception, Jordet 2013 ; environ 3 scans en 10 s en moyenne, Jordet et al. 2020 ; le bas : non trouvé) ; fréquence × (1 − 0,5 × gêne) (direction sourcée, ampleur non trouvée) ; fréquence × (1 − 0,5 × vitesse / vitesse de pointe) (non trouvé) ; porteur : fréquence × part de temps tête haute selon la note 0,6 × Dribbling + 0,4 × Technique, 99 → 100 %, 55 → 60 %, 11 → 25 % (non trouvé). L'article de 2020 n'a pas pu être lu en entier (hôte `pmc.ncbi.nlm.nih.gov` non autorisé dans la session) : chiffres par poste et ampleur de l'effet de la pression non vérifiés. Pas de paramètre de poste.

**13/11/2026, code.** `v2engine/scan.py` : `scan_rate_per_s`, `head_up_share`, `ScanTracker` (tirage par pas dans un nouveau flux `regard`, indépendant des autres ; fréquence recalculée tous les 0,5 s, décalée d'un joueur à l'autre pour le coût) ; `perception_memory.update` : un joueur qui scanne voit tous les autres ; `trace.ScanEvent`, `MatchTrace.scans` ; `flux.REGARD` ; branchement dans `match.simulate_match` (avant la mise à jour de la mémoire, recréé à la mi-temps). Banc : `measure_v2`, `v2_indicators`. Sans effet sur le jeu : le « il ne suit plus le ballon » n'a pas de consommateur avant 08d et 08e.

**Défaut trouvé par la suite complète.** Le rapport du banc lisait `collector.minutes_per_match`, absent hors de `run()` : 4 tests de `test_v2_indicators.py` en échec au premier passage. Corrigé (`getattr(c, "minutes_per_match", 90.0)`, comme ailleurs dans le fichier), suite relancée sur l'état final.

**13/11/2026, mesures (`.scratch/v2-realisme/mesures/08c-*`).**
- Aucun effet sur le jeu : un match à graine fixée (20260923), empreinte sur événements, buts, tirs, décisions, réceptions et positions échantillonnées identique sur le code du 08b et sur celui du 08c (`625f5ce17d50985c`, 2 444 décisions, 1 332 événements) ; `measure_v2 2` : seules 6 lignes de mémoire du 08b changent (la mémoire est rafraîchie par les scans), aucune autre ligne ; test `test_a_simulated_match_traces_scans_without_changing_the_game` : mêmes décisions et mêmes événements avec et sans scans.
- Déterminisme : `08c-det1` et `08c-det2` identiques hors temps de calcul.
- Scans (2 matchs, base) : environ 34 000 par match, 17,1 par minute et par joueur ; 2,65 scans en moyenne dans les 10 s avant une réception ; part du porteur 1,3 % des scans.
- Vision 99 contre 11 (`--profil Vision`, 2 matchs) : 29,8 contre 5,4 scans par minute et par joueur ; 4,37 contre 0,74 scans dans les 10 s avant une réception (réel : 6 à 8 pour les meilleurs, 3 à 4 en moyenne, Jordet).
- Mémoire de perception (base) : âge moyen de la dernière vue 2,19 s → 1,48 s côté porteur, 3,25 s → 1,44 s côté receveur ; erreur moyenne 3,4 → 2,5 m côté porteur, 3,8 → 2,3 m côté receveur.
- Temps de calcul : 94,9 s par match mesuré pendant cinq jobs parallèles (non comparable) ; coût propre mesuré ensuite sur machine libre (micro-banc, 22 joueurs) : les scans ajoutent 36 µs par pas, soit environ 1,9 s par match de 90 min, en plus des 7,6 s de la mémoire du 08b (environ 9,5 s au total).
- Tests : 10 ajoutés (`tests/test_v2engine_scan.py`). Suite : 2 843 passés, 0 ignoré, 14 désélectionnés ; `CLAUDE.md` mis à jour.

**À regarder au 08d et au 08e.** La fréquence moyenne avant réception (2,65 scans en 10 s) est un peu sous la moyenne réelle d'environ 3 ; les meilleurs (4,4) restent sous les 6 à 8 réels. Le porteur ne scanne que 1,3 % du temps total : cohérent avec sa tête basse, mais non étalonné. L'ampleur des effets de gêne et de vitesse n'est pas sourcée.

**Durée.** Estimée 3 h 10. Réelle environ 3 h, non chronométrée (analyse 30 min, développement 1 h 05, tests 45 min, intégration et vérifications 40 min) : − 5 %. Temps machine hors total : suite complète deux fois (8 min 55 s dont 4 échecs, puis 8 min 25 s), 2 x 2 matchs, mesure de profil, comparaison d'empreinte.

**13/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS (rapport `08c-expert-1.md`), aucune anomalie bloquante. QC : VALIDÉ (tests non exécutés par lui, preuves du ticket). Réserves, chacune acceptée par le propriétaire (« j'accepte A1, A2, A3 ») :
- **A1** : le « il ne suit plus le ballon pendant un scan » n'est pas branché, faute de consommateur ; à inscrire au périmètre du 08d et du 08e, avec un test (un joueur qui scanne ne réagit pas au ballon pendant 0,3 s).
- **A2** : fréquence un peu basse avant réception (2,65 scans en 10 s contre environ 3 en réel ; 4,4 pour Vision 99 contre 6 à 8) et taux appliqués à tout joueur sans ballon ; à recaler au 08d ou au 08e sur l'effet observé dans le jeu.
- **A3** : coût de calcul non mesuré au moment de la revue ; mesuré ensuite (voir Mesures : 1,9 s par match pour les scans).
Facultatif A4 : environ 34 000 `ScanEvent` (environ 8 Mo) par match gardés dans la trace ; à surveiller si elle est un jour sérialisée pour l'API. Observation du QC : la docstring de `perception_memory.py` dit encore « recaler au 08c et au 08d » (reste de rédaction, à corriger au prochain ticket qui touche ce fichier). Clôture : VALIDÉ (expert APPROVED_WITH_RESERVATIONS, réserves acceptées, QC VALIDÉ).
