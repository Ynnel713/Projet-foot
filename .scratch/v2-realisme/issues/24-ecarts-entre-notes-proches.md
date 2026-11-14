# 24: Vrais écarts entre notes proches (70 contre 80) : banc, puis nouvelle forme de courbe

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026). **Priorité :** P1, avant la calibration finale (`v2-collectif/22a` à `22c`), qui repartira des nouvelles courbes. **Catégorie :** mesure et moteur.

**Constat vérifié (14/11/2026, calcul sur les fonctions du moteur) :** les actions probabilistes passent par `attributes._cubic_curve` (forme t³). Elle est plate au centre et centrée sur 55, alors que la base est centrée sur 60 à 65 (485 joueurs de Ligue 1 : médiane 60, 80 % des notes entre 35 et 75 ; entre 60 et 90 pour les attributs du poste). Conséquence, sur un écart de 10 points :

| Mécanisme | 50 | 60 | 70 | 80 | 90 |
|---|---|---|---|---|---|
| Passing : passe précise (difficulté 60) | 49,3 % | 50,0 % | 50,7 % | 55,9 % | 69,8 % |
| Tackling : tacle gagné (porteur 60) | 49,4 % | 50,0 % | 50,6 % | 55,0 % | 66,9 % |
| Dribbling : garder le ballon au contact | 83,0 % | 83,0 % | 83,5 % | 85,2 % | 89,0 % |
| Decisions : meilleur choix | 70,0 % | 70,0 % | 71,0 % | 74,6 % | 82,6 % |
| Finishing : facteur d'exécution du tir | 0,994 | 1,000 | 1,006 | 1,049 | 1,157 |
| Pace : vitesse max (linéaire) | 30,0 | 31,3 | 32,7 | 34,0 | 35,3 km/h |
| First Touch : contrôle orienté (linéaire) | 47 % | 53 % | 59 % | 64 % | 70 % |

Entre 60 et 70, les attributs techniques, mentaux et de duel ne font presque aucune différence ; entre 70 et 80, très peu. Or c'est là que se trouvent presque tous les joueurs. Les tests de profils du banc ne comparent que 99 et 11 (`measure_v2.HIGH, LOW`) : l'effet en match de notes proches n'a jamais été mesuré.

**Exigence du propriétaire (14/11/2026) :** « J'aimerais qu'il y ait une réelle différence entre un joueur qui a 70 et un joueur qui a 80. Peu importe la caractéristique [...] La majorité, c'est entre 60 et 80, ou voire 90. Et du coup, c'est là que doivent se concentrer les différences pour le réalisme. »

**What to build:** deux étapes dans un même ticket (un seul ticket, décision du propriétaire du 14/11/2026, malgré une estimation au-delà de 2 h).

**1. Banc et mesure de référence (avant la nouvelle courbe).**
- `scripts/measure_v2.py --profil <Attribut> --niveaux 80 70` : même plan d'expérience que le test de profils actuel (affiche jouée deux fois, rôles inversés, une équipe à la note haute, l'autre à la note basse), mais avec deux niveaux choisis. Défaut inchangé : 99 contre 11.
- Pour chaque attribut lu par le moteur (liste de `docs/CARTE_ATTRIBUTS_V2.md`, colonne « branché »), un indicateur cible déjà au banc : celui que l'attribut doit faire bouger (Passing : passes réussies ; Tackling : tacles gagnés ; Finishing : conversion ; Dribbling : pertes en conduite ; First Touch : contrôles ratés et temps de possession ; Decisions : écart au meilleur choix ; Pace : course au-dessus de 25 km/h ; etc.), avec son écart haut / bas et son intervalle de confiance.
- Une table de scène (sans match) : pour chaque fonction du moteur qui lit un attribut, sa valeur à 50, 60, 70, 80 et 90 (le tableau ci-dessus, complété, généré par un script `scripts/attribute_curves.py`), qui servira d'avant / après à l'étape 2.
- Rapport : `docs/INDICATEURS_V2.md`, section nouvelle ; liste des attributs dont l'écart 70 / 80 n'est pas significatif en match.

**2. Nouvelle forme de courbe : deux tests.** Remplacer la forme de la courbe partagée (une seule fonction, `_cubic_curve`, qui sert à `success_probability` et `duel_probability`), en comparant **deux variantes**, puis garder la meilleure :
- **Variante A, cubique recentrée et adoucie :** centre sur la médiane réelle des notes (environ 62, mesurée sur la base au moment du ticket), exposant 1,5 au lieu de 3 (signe gardé : `sign(t)·|t|^1,5`), mêmes bornes. Changement minimal de forme.
- **Variante B, logistique :** `baseline + amplitude · tanh(k · t)` (forme en S), pente maximale au centre, centre sur la médiane réelle ; `k` choisi pour que l'écart 70 → 80 soit au moins celui visé ci-dessous.
- **Objectif chiffré (à valider par le propriétaire avant le code) :** pour chaque mécanisme probabiliste, l'écart de 70 à 80 vaut au moins le tiers de l'écart de 50 à 99, et l'écart de 60 à 70 au moins le quart ; en duel, 10 points d'écart entre les deux joueurs donnent au moins 58 / 42 (contre 50,6 / 49,4 aujourd'hui).
- Les courbes linéaires des attributs physiques sont relues : elles restent ancrées sur des valeurs réelles mesurables (vitesse de pointe, temps d'accélération) ; on ne les rend plus raides entre 60 et 90 que si une source réelle le justifie (sinon : « non trouvé », et on garde).
- Les `baseline` et `amplitude` de chaque action ne bougent pas dans ce ticket : seule la forme change ; le recalage des niveaux (passes réussies, conversion, tacles…) revient à la calibration finale, qui repart de ces courbes.
- Choix entre A et B : sur la table des courbes de l'étape 1 (avant / après) et sur le banc de l'étape 1 (70 contre 80 en match, attribut par attribut), en retenant la variante qui fait le plus d'attributs significatifs entre 70 et 80 sans faire sortir les indicateurs globaux de leur repère (buts, passes réussies, tirs). Le propriétaire tranche s'ils sont proches.

**Attributs :** tous ceux qui passent par `success_probability` ou `duel_probability` (Passing, First Touch au contrôle, Tackling, Strength, Balance, Dribbling, Finishing, Long Shots, Decisions, Vision, Composure, Anticipation, Positioning, Marking, Teamwork, Off the Ball, Flair, Aggression, attributs du gardien…) ; aucun rayon ne change (`docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by:** rien.

**Bloque :** `v2-collectif/22a`, `22b`, `22c` (calibration finale : elle doit partir des nouvelles courbes).

**Status:** livré (14/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 1 h 05 (banc `--niveaux`, script des courbes ; deux variantes derrière un choix unique, puis la retenue seule) |
| Tests unitaires et comportementaux | 50 min |
| Intégration et vérifications | 1 h (mesure de référence, deux mesures A et B, choix, documentation) |
| **Total (travail effectif)** | **3 h 25** |

Confiance : moyenne. Hypothèses : le forçage d'attribut du banc (`_force_attribute`) accepte deux niveaux quelconques ; une seule fonction de forme à changer (`attributes._cubic_curve`) ; beaucoup de tests existants fixent des probabilités calculées avec la courbe actuelle et devront être recalculés (sans être supprimés ni affaiblis) : principal risque de dépassement. Au-delà de 2 h : découpage examiné (24a banc, 24b courbe), refusé par le propriétaire le 14/11/2026 (« Fais un seul ticket »).
Temps machine, non compté : banc 70 contre 80 à 20 matchs par attribut, trois fois (référence, variante A, variante B) : environ 10 à 12 h par passage pour une vingtaine d'attributs sur 4 processus, à limiter aux 14 attributs les plus lus (Passing, First Touch, Technique, Dribbling, Tackling, Finishing, Decisions, Composure, Anticipation, Positioning, Pace, Acceleration, Agility, Strength) si la durée est trop longue ; série appariée de 50 matchs pour les indicateurs globaux ; suite complète.

## Tests

- **Unitaires (banc) :** `--niveaux 80 70` force bien 80 et 70 (défaut inchangé, 99 / 11) ; la table des courbes reproduit `attributes.success_probability` et `duel_probability`.
- **Unitaires (courbe) :** variante retenue : écart 70 → 80 au moins le tiers de 50 → 99 ; 60 → 70 au moins le quart ; duel à 10 points d'écart au moins 58 % ; bornes jamais dépassées (jamais 0 ni 1) ; monotone ; symétrique en duel (p(a, b) + p(b, a) = 1).
- **Comportementaux (profils comparés) :** 70 contre 80, attribut par attribut, avant (courbe actuelle), variante A, variante B : plus d'attributs avec un écart significatif qu'avant.
- **Statistiques (séries de matchs) :** 50 matchs appariés avant / après la variante retenue : buts, xG, tirs, passes réussies, tacles, pertes rapportés, écarts expliqués.

## Acceptance criteria

- [x] `--niveaux` ajouté au banc, défaut inchangé (99 / 11), testé
- [x] Table des courbes à 50, 60, 70, 80, 90 pour chaque fonction qui lit un attribut, générée par script, avant et après
- [x] Mesure de référence 70 contre 80 en match pour chaque attribut retenu, avec intervalle de confiance, rapportée dans `docs/INDICATEURS_V2.md`
- [x] Constantes produit (centre, exposant ou pente ; objectif chiffré validé le 14/11/2026) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code de l'étape 2
- [x] Variantes A et B mesurées sur la table des courbes et sur le banc 70 contre 80 ; choix argumenté (propriétaire s'ils sont proches) — **écart décidé par le propriétaire (14/11/2026, « oublions le A ») :** A mesurée sur la table des courbes seulement, sans banc en match, car elle rate l'objectif révisé (10 % / 21 % pour ≥ 25 % / ≥ 20 % ; duel 55 % pour ≥ 58 %)
- [x] Variante retenue seule dans le code, objectif chiffré tenu (tests de courbe)
- [x] Écart 70 / 80 significatif en match pour plus d'attributs qu'avant, rapporté attribut par attribut
- [x] Indicateurs globaux mesurés avant / après (50 matchs appariés) ; écarts transmis à la calibration finale, aucun recalage de niveau ici
- [x] Tests existants recalculés sur la nouvelle courbe, aucun supprimé ni désélectionné
- [x] Rayon des attributs inchangé (`docs/CARTE_ATTRIBUTS_V2.md`), test de rayon vert
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`24-det1`, `24-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 978 passés = 2 962 + 16 : 14 tests de courbe et 2 du banc, 0 ignoré, 14 désélectionnés ; `24-suite.txt`)

## Comments

**14/11/2026, objectif chiffré validé par le propriétaire** (« Je valide ») : pour chaque mécanisme probabiliste, écart de 70 à 80 au moins le tiers de l'écart de 50 à 99, écart de 60 à 70 au moins le quart ; en duel, 10 points d'écart donnent au moins 58 / 42 (50,6 / 49,4 aujourd'hui). Restent à proposer avant le code de l'étape 2 : centre (médiane réelle mesurée), exposant de la variante A, pente de la variante B. Ticket à réaliser dans une autre session.

**14/11/2026, constantes de l'étape 2 (recommandations validées par le propriétaire, qui valide d'office les recommandations de la session et des experts pour ce ticket) :**
- **Centre mesuré :** médiane des 19 attributs probabilistes = 60 sur les 485 joueurs de Ligue 1, 65 sur les 198 titulaires ; **62 retenu**.
- **Objectif révisé** (« Réviser l'objectif ») : l'objectif du matin (70 → 80 au moins le tiers de 50 → 99) est impossible avec une courbe centrée sur la médiane : à centre 62, la variante B plafonne vers 23 % entre 70 et 80 quelle que soit la pente, la variante A donne 10 % / 20 %, une droite 20 % / 20 %. Le tiers n'est tenu qu'avec une courbe centrée sur 70 et très raide (tanh, k = 3,5), qui ferait tomber un joueur à 60 de 0,60 à 0,37 sur une action de base 0,6 (niveau global effondré, plus de différence sous 55 ni au-dessus de 85). Nouvel objectif : **60 → 70 au moins 1/4 et 70 → 80 au moins 1/5 de l'écart 50 → 99**, pour chaque action seule (`success_probability`) ; duel inchangé (10 points d'écart : au moins 58 %).
- **Variante B, pentes :** action seule k = 2 ; duel k = 1, pente propre (k = 2 donnerait 69 à 72 % à 10 points d'écart, jugé trop fort) : 62,9 % au tacle pour 10 points, 74,3 % pour 20.
- **Demi-étendues (recommandation de la session) :** 37 au-dessus du centre et 51 en dessous, pour que les extrêmes validés de chaque action restent atteints aux mêmes notes (99 → maximum, 11 → minimum) ; seule la valeur de base passe de la note 55 à la note 62. Avec une demi-étendue unique de 44, 99 n'atteignait plus que 97 % de l'amplitude.
- **Courbes physiques (linéaires) :** gardées. Pace (guide : 30 km/h à 50, 36,5 à 99) et Acceleration (Samozino et Morin) sont déjà ancrées sur des repères réels ; aucune source trouvée dans ce ticket ne justifie une pente plus forte entre 60 et 90.
- **Pas de commit intermédiaire** (recommandation de la session) : le verrou de commit est respecté, commit à la clôture.

**14/11/2026, reprise et résultats (session suivante).** Patch WIP réappliqué sur `fc49ac9`. Le résumé de la sauvegarde est gardé ci-dessous (« Reprise »), ses étapes 1 à 6 sont faites :
- **Banc B** (80 contre 70, 20 matchs, 14 attributs, copie figée du code) : `banc_80_70_B.json`, agrégé avec l'avant dans `synthese.md`. Significatifs : **2 sur 14 (Decisions, Dribbling) contre 1 sur 14 avant (Decisions)**. Non significatifs : Passing (réussite ; le volume, + 58 passes, l'est), First Touch, Technique, Tackling, Finishing, Composure, Anticipation, Positioning, Agility, Strength ; Pace, Acceleration sans intervalle. Cause principale : 20 matchs n'ont pas la puissance de voir l'écart de la table sur des compteurs bruités, et une part des actions courantes est au plafond de l'action (0,97 dès 70). Banc A non lancé (décision du propriétaire, critère ci-dessus).
- **Variante A retirée** du code (`_SHAPE`, `_POWER_A`, branche A) : seule reste la forme en S.
- **Série appariée 50 matchs** (`fc49ac9` / après) : buts 3,98 → 4,12 (non significatif), xG et tirs inchangés ; passes réussies + 1,7 point, pertes − 13, passes + 58, tacles − 1,5, fautes + 1,3, possession + 1,1 s, km par joueur 12,21 → 12,69 (tous significatifs). Transmis à `v2-collectif/22a`, aucun recalage ici. Sortie filtrée : `serie_comparaison.txt`.
- **Déterminisme :** `24-det1.txt` et `24-det2.txt` (2 matchs, graine fixée) identiques hors temps de calcul.
- **Documentation :** `docs/INDICATEURS_V2.md` section 40, `docs/PLAN_V2.md` (point 3), `CLAUDE.md` (compte attendu).
- **Suite complète :** 2 978 passés, 0 ignoré, 14 désélectionnés (2 962 + 16 nouveaux ; un test renommé : vitesse de conduite « à la médiane » au lieu de « à 55 »).

**14/11/2026, durée.** Estimation 3 h 25 (révisée à 4 h 30 à la sauvegarde) ; durée réelle environ 4 h 30 (analyse 40, développement 60, tests 70, intégration 100), + 32 % : recalcul de 27 tests existants sur la nouvelle courbe, objectif révisé en cours de route (centre mesuré, objectif du tiers impossible), agrégation et documentation des deux bancs ; durée estimée à l'horloge des sessions hors attentes machine, non chronométrée ; installation de l'environnement cloud de la seconde session non comptée. Temps machine hors total : banc avant et banc B (2 x 14 x 20 matchs, environ 2 h 20 chacun), série appariée 2 x 50 matchs (environ 55 min), suite complète (12 min), déterminisme 2 x 2 matchs.

**14/11/2026, clôture (passage 1).** Expert : APPROVED_WITH_RESERVATIONS. QC : VALIDÉ. Clôture : VALIDÉ (réserves acceptées par le propriétaire, choix des trois réserves A1, A2, A3 dans la conversation).
- A1 [réserve acceptée] effet en match 70 / 80 peu démontré (2 / 14 contre 1 / 14, dans le bruit d'environ 0,7 faux positif attendu) : banc d'au moins 100 matchs sur 3 ou 4 attributs prioritaires dans `22a`.
- A2 [réserve acceptée] indicateurs cibles en comptes bruts (contrôles ratés, tacles gagnés, pertes en conduite), pas en taux : rapporter des taux dans le banc de `22a`.
- A3 [réserve acceptée] niveaux globaux décalés sans recalage (passes 1 144, km 12,7, fautes + 1,3, buts 4,5 au banc 80 / 70) : `22a` est la prochaine étape de calibration.
- Facultatifs non traités : docstring de `scripts/attribute_curves.py` (objectif « 1/4 et 1/3 » au lieu de 1/4 et 1/5) ; commentaires du moteur citant « 55 -> Y » (`defense.py`, `bloc.py`, `decision.py`) ; commentaire au milieu d'une expression (`test_v2engine_situation.py:505`) ; import de `HORS_JEU` depuis `cerveau` (`measure_v2.py`).

**14/11/2026, intégration sur `main` (demande du propriétaire : « fusionne sur le main »).** `main` avait avancé de 4 commits (tickets 25-26, 27, 27a, 27b ; moteur non touché). Changements du ticket rejoués sur `97746de` : conflits documentaires seulement (`CLAUDE.md`, `INDICATEURS_V2` où la section du ticket devient la 40, `PLAN_V2`, registre, journal). Suite sur l'état fusionné : 2 998 passés (2 982 + 16), 0 ignoré, 14 désélectionnés. Nouvelle clôture sur la base `97746de` (passage 2).

**14/11/2026, clôture (passage 2, base `97746de`).** Expert : APPROVED_WITH_RESERVATIONS (code et tests identiques au passage 1, blob par blob). QC : VALIDÉ. Clôture : VALIDÉ (réserves A1, A2, A3 reconfirmées par le propriétaire dans la conversation, mêmes termes qu'au passage 1). Facultatifs inchangés (A4 à A7).

## Reprise (14/11/2026, sauvegarde WIP à la demande du propriétaire, pour finir dans une autre session)

Commit de sauvegarde **non validé** (verrou contourné à la demande explicite du propriétaire, pas une clôture) : le ticket reste à clore par `/valider-ticket-simulafoot` ; toute la revue porte sur l'état final.

**Fait :**
- Banc : `scripts/measure_v2.py --niveaux 80 70` (défaut 99 / 11 inchangé) ; relevé par équipe haute / basse des indicateurs cibles (`profile_tally`, `profile_gaps` : écart haut - bas par match, IC 95 % Student apparié), clé de rapport « profil : écart haut - bas par match (IC 95 %) ». Tests dans `tests/test_v2_indicators.py` (`test_profile_levels_…`, `test_profile_tally_…`).
- Table des courbes : `scripts/attribute_curves.py` (45 mécanismes, vraies fonctions du moteur, 50 à 99, parts 60→70 et 70→80 de l'écart 50→99, table des duels) ; tests `tests/test_attribute_curves.py`.
- Courbe : `v2engine/attributes.py`, `_s_curve` (remplace `_cubic_curve`), centre 62, demi-étendues 37 / 51, pente 2 (action) et 1 (duel). Tests de forme : `tests/test_v2engine_courbe_attributs.py`.
- 27 tests existants recalculés (point milieu 55 → 62, extrêmes inchangés ; scène de compensation : milieu défensif à 8,5 m au lieu de 9 ; scène de fatigue : B en (30 ; 4)). Aucun supprimé ni désélectionné.
- Suite complète (avant les dernières corrections) : 13 échecs, tous corrigés depuis et repassés en ciblé ; **suite complète à relancer**.
- Déterminisme : même empreinte sur deux matchs de 10 min à graine fixée (`e2de699205cf4d94`).
- Mesures dans `.scratch/v2-realisme/24-mesures/` : tables des courbes avant / A / B (`courbes_*.md|json`), banc 80 contre 70 **avant complet** (`banc_80_70_avant.json`, extraits « profil »), banc B partiel (3 attributs sur 14), `synthese_partielle.md`, scripts `banc.sh` et `agreger_bancs.py`.

**Résultats acquis :**
- Table des courbes, médiane des actions seules : avant 4 % / 14 %, A 10 % / 21 %, B 35 % / 24 % ; duel à 10 points d'écart : avant 50,6 %, A 55 %, B 62,9 %. A échoue à l'objectif révisé (≥ 25 % / ≥ 20 %), B le tient sauf : duels contre difficulté (passe courte, contrôle facile : plafond 0,97 de l'action), Strength / Balance (22 %, jugés au critère duel), Teamwork « suit son vis-à-vis » et Work Rate « repos » (butée sur les bornes de l'action) → à transmettre à la calibration 22a.
- Banc avant (80 contre 70, 20 matchs) : **1 attribut sur 14** a son indicateur principal significatif (Decisions, écart au meilleur choix −0,072 [−0,117 ; −0,028]) ; Passing ne change que le nombre de passes (+74 par match), pas leur réussite.

**Reste à faire, dans l'ordre :**
1. Banc B puis banc A (même commande, depuis une copie figée du code avec `_SHAPE = "B"` puis `"A"` dans `v2engine/attributes.py`) : `banc.sh <copie> <sortie>` ; environ 2 h 30 chacun sur 4 processus (115 s par match). Agréger avec `BANC24=<dossier contenant bench/ref, bench/B, bench/A> python3 agreger_bancs.py`.
2. Choix (B attendu) : plus d'attributs significatifs qu'avant, indicateurs globaux dans leur repère.
3. Retirer la variante A du code (`_SHAPE`, `_POWER_A`, branche `if _SHAPE == "A"`).
4. Série appariée 50 matchs avant / après : `uv run python -m scripts.bench_series 50 --processus 4 --json …` sur l'ancien code (commit `fc49ac9`) et le nouveau, puis `--comparer avant.json apres.json` ; écarts transmis à 22a, aucun recalage ici.
5. Suite complète (attendu : 2 962 + 18 nouveaux tests = environ 2 980 passés, 0 ignoré, 14 désélectionnés ; recompter), déterminisme à refaire après le retrait de A.
6. Documentation : section « Ticket 24 » dans `docs/INDICATEURS_V2.md` (tables avant / après, banc attribut par attribut, liste des attributs non significatifs), `docs/PLAN_V2.md`, ce ticket ; registre `docs/agents/suivi-estimations.md`.
7. Clôture `/valider-ticket-simulafoot` (expert + QC), puis commit des seuls hunks et push.

**Temps passé à la sauvegarde :** environ 2 h 30 de travail effectif (estimation 3 h 25) ; le recalcul des tests a pris plus que prévu, l'estimation sera dépassée (révision : environ 4 h 30).
