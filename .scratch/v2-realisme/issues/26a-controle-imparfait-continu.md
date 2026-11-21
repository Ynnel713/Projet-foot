# 26a: Contrôle imparfait continu, plus de tout ou rien

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : contrôles contextuels, une passe trop appuyée rebondit sur le pied ou force le joueur à s'ajuster ; audit `docs/AUDIT_ROADMAP_V2.md`, « passe et contrôle en tout ou rien »). **Priorité :** P1. **Catégorie :** geste technique.

**Constat vérifié (14/11/2026) :** `possession.attempt_control` tire un succès ou un échec (First Touch contre la difficulté : vitesse du ballon par rapport au ballon idéal, pression). Réussi, le ballon est collé au pied ; raté, il repart à `MISS_SPEED_SHARE` de sa vitesse avec une déviation (`missed_control_velocity`). Entre les deux, rien : pas de contrôle un peu long qui oblige à faire un pas, pas de ballon qui rebondit à 2 m. La posture (type de réception 07c, orientation 07a) joue sur la durée (07d), pas sur la qualité du contact.

**What to build:** l'issue du contrôle devient continue, sur le principe de l'écart gaussien du tir (`v2-collectif/35b`) : distance et direction du ballon après le contact tirées autour de l'intention (pied, ou direction orientée du 31b), avec une dispersion qui croît avec la difficulté (vitesse et angle d'arrivée du ballon, hauteur, type de réception, pression) et décroît avec First Touch (Technique pour les ballons difficiles, rayons de la carte). Le joueur va chercher le ballon là où il est (physique de course existante) ; s'il est trop loin ou qu'un adversaire est plus près, le ballon est libre. Le contrôle raté actuel devient la queue de la distribution, pas un cas à part.

**Hors de ce ticket :** passe à une touche (`v2-collectif/36a`), pied faible (`v2-attributs-restants/04a`), amorti de la poitrine ou de la cuisse (après la hauteur des joueurs, hors périmètre de D-V03).

**Attributs :** First Touch, Technique (rayons existants : la carte doit dire lequel règle la dispersion de quel ballon).

**Ticket 24 en cours :** toute courbe d'attribut de ce ticket passe par `success_probability` / `duel_probability`, dont la forme change au 24 ; les constantes de niveau sont proposées après la livraison du 24.

**Blocked by:** 07c, 07d, `v2-collectif/31b` (livrés) ; 04e, 04f (ballon devant le porteur, ballon jouable entre deux touches : à faire, ils posent la notion de ballon à distance du pied que ce ticket réutilise).

**Bloque :** `v2-collectif/36a` (même calcul de l'arrivée du ballon), `v2-collectif/22a`.

**Status:** livré (21/11/2026), validé expert + QC (réserve A1 acceptée, renvoyée au `v2-collectif/36a`)

## Conception et constantes (21/11/2026, validées par délégation du propriétaire : « Je valide automatiquement tes recommandations et les conseils d'experts », 20/11/2026)

- **Un seul tirage, même chance de garder le ballon** (`possession.control_probability`, First Touch contre la difficulté, inchangée) : le volume de contrôles ratés ne bouge pas par construction. Le tirage u est lu comme le quantile d'un écart demi-normal |z| ; l'échelle met le seuil du raté exactement à la chance p (`possession.control_touch`).
- **Trois issues continues en z** : au pied (z sous `LONG_CONTROL_START` x z_p, 0,8 ; 0,7 au premier jeu) ; contrôle long (le ballon file dans sa direction et s'arrête à 1 à 2 m du joueur, `LONG_CONTROL_M` (1 à 2,5 m au premier jeu), linéaire en z ; si un adversaire est plus près que lui de ce point, le ballon est libre et le joueur ne peut le reprendre qu'après `MISS_RETRY_S`, comme la touche trop longue ; sinon il le garde et décide plus tard du temps d'aller le chercher à sa vitesse de réception, `possession.long_chase_s`, sans jeu en une touche) ; raté au-delà de z_p (la queue, `missed_control_velocity` inchangé). Part des contrôles longs parmi les réussis : 4 % (p = 0,98), 7 % (0,95), 13 % (0,8), 17 % (0,6).
- **Attributs** : First Touch seulement, par la chance p (vitesse et pression y sont déjà) ; aucun attribut ajouté. Technique (ballon dur, 31c) et type de réception (07d) gardent leur rôle sur l'orientation et la durée : pas de double comptage. Le type de réception et l'angle d'arrivée n'élargissent pas la dispersion (écart au texte du ticket, assumé : ils jouent déjà sur la durée du contrôle) ; hauteur du ballon : sans objet avant `v2-hauteur-ballon/02a`.
- Gardien (il capte) et ballon quasi arrêté : jamais de contrôle long. Journal : événement « contrôle long » ; une perte qui suit est une perte « contrôle ».
- Données réelles : non trouvées.

**Critères d'acceptation chiffrés (posés avant la mesure) :**
- [x] Loi : succès identique à l'ancien tirage pour tout u ; distance croissante et continue en u (plus de 100 valeurs distinctes sur une grille) ; parts de contrôles longs 4 / 7 / 13 / 17 % à p = 0,98 / 0,95 / 0,8 / 0,6 (± 0,5 point ; 8 / 13 / 21 / 26 % au premier jeu). **`tests/test_v2engine_controle_continu.py`.**
- [x] Scènes : moins de contrôles au pied à 20 m/s qu'à 8 m/s ; plus avec First Touch 99 qu'avec 11 ; moteur : contrôle long de 2 m avec un adversaire plus près, ballon arrêté à 2 m ± 5 cm, joueur écarté `MISS_RETRY_S` ; sans adversaire plus près, ballon gardé, décision retardée du temps d'aller le chercher, pas de jeu en une touche. **13 tests.**
- [x] 50 matchs appariés (banc, graines 0 à 49, avant : moteur du 04f) : contrôles longs comptés par match ; pertes au journal après un contrôle (raté ou long) en hausse d'au plus 5 par match ; réussite des passes de jeu au-dessus de 80 % ; tirs et buts dans le bruit, tout écart significatif expliqué. **Contrôles longs 73,3 par match ; pertes après un contrôle + 4,4 ± 1,9 (borne haute 6,3) ; réussite 84,87 % ; tirs + 0,7 ± 2,3, buts − 0,36 ± 0,90 ; `docs/INDICATEURS_V2.md` section 66. Troisième jeu de constantes : les deux premiers manquaient ce critère (voir commentaires).**
- [x] Rayon de First Touch inchangé (`docs/CARTE_ATTRIBUTS_V2.md` mise à jour) ; déterminisme à graine fixée ; suite complète comparée à l'attendu (3 480 + tests ajoutés). **Empreinte des comptes du match 3 `57b9428aa58464f9` deux fois ; suite complète 3 493 passés (3 480 + 13), 0 ignoré, 14 désélectionnés.**

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : 04e et 04f livrés avant (ballon à distance non nulle du pied) ; pas de nouvel état du ballon.
Temps machine, non compté : suite complète ; mesure 50 matchs.

Réestimation annoncée le 21/11/2026 : **3 h** (conception de la loi continue sur le tirage existant, journal, mesure appariée).

## Tests

- **Scènes :** même joueur, ballon à 8 puis 20 m/s : distance moyenne du ballon après contact plus grande à 20 ; First Touch 99 contre 11 à vitesse égale ; dos au jeu contre de face.
- **Statistiques (50 matchs) :** distribution de la distance après contrôle, pertes au contrôle, temps par possession de joueur.

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Distance après contrôle continue (pas deux valeurs) et croissante avec la vitesse d'arrivée, décroissante avec First Touch (scènes)
- [x] Pertes au contrôle par match dans la marge validée par rapport à avant
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 21/11/2026, premier jeu (ballon toujours libre après un contrôle long) mesuré sur 50 matchs appariés : 139 contrôles longs par match, 48 perdus ; pertes après un contrôle + 49,0 ± 3,4 par match (critère : + 5 au plus), réussite des passes − 2,2 points, buts − 0,96 ± 0,67. Critère manqué : conception revue avant toute clôture (ballon libre seulement si un adversaire est plus près du point d'arrêt, suivant le texte du ticket « s'il est trop loin ou qu'un adversaire est plus près, le ballon est libre » ; sinon gardé avec le temps d'aller le chercher). Contrôle rapide sur 12 matchs : + 1,8 ± 5,4. Série de 50 refaite.
- 21/11/2026, second jeu (ballon gardé si personne n'est plus près du point d'arrêt, 0,7 ; 1 à 2,5 m), 50 matchs appariés : pertes après un contrôle + 6,7 ± 2,1, critère encore manqué ; portée seule ramenée à 1 à 2 m sans effet sur 12 matchs ; troisième jeu : `LONG_CONTROL_START` 0,8, `LONG_CONTROL_M` (1,0 ; 2,0), validés par délégation : + 4,4 ± 1,9 sur 50 matchs, critère tenu en moyenne.
- Non mesuré : temps par possession de joueur (le banc apparié ne le relève pas ; effet attendu faible : 73 contrôles longs gardés ou perdus par match, délai moyen de recherche d'environ 0,4 s).
- 21/11/2026, première suite complète : 9 échecs, tous au banc (`Collector.on_contact` additionnait le résultat du contrôle, devenu un `ControlTouch`) ; corrigé (`bool(controlled)`, `scripts/v2_indicators.py`), les 129 tests concernés repassent ; suite relancée.

- 21/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte 0845d99b), QC VALIDÉ. A2 (portée « 1 à 2,5 m » périmée dans `docs/CARTE_ATTRIBUTS_V2.md` et le commentaire de `trace.CONTROLE_LONG`) et A3 (docstring de `26a-apparies.py`) corrigés ; revue refaite. A1 (contrôle long gardé : un délai de décision, ballon au pied, rien à l'écran) acceptée par délégation du propriétaire (« Je valide automatiquement tes recommandations et les conseils d'experts », 20/11/2026), renvoyée au `v2-collectif/36a` (ballon placé au point d'arrêt puis ramené au pied sur `long_chase_s`).
- 21/11/2026, passage 2 : expert APPROVED_WITH_RESERVATIONS (empreinte cf321201 ; A2 et A3 corrigées, A1 seule restante), QC VALIDÉ, clôture VALIDÉ avec réserves acceptées. Facultatifs non faits : A4 (un contrôle long suivi d'une perte compte comme « reçu » dans la calibration des passes, environ 6 cas par match), A5 (le contrôle long gardé pourrait déclencher le pressing). À surveiller : pertes après un contrôle sur une autre série de graines (borne haute de l'IC 6,3, constantes réglées trois fois sur les mêmes graines) ; rendu au 36a ; temps par possession non mesuré.

## Durée réelle

Environ 3 h 10 de travail effectif pour 3 h réestimées (+ 6 %) ; 2 h à l'origine (+ 58 %) : analyse 25 min, conception de la loi 30 min, développement 35 min, tests 30 min, intégration et vérifications 70 min (trois jeux de constantes, contrôles rapides sur 12 matchs, rapport, correction du banc). Écart sur l'estimation d'origine : la loi continue posée sur le tirage existant n'était pas prévue, et le critère de pertes a exigé deux réglages. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée ; temps machine hors total : 3 x 50 + 3 x 12 matchs appariés, deux suites complètes (16 min chacune).
