# Chantier v2-realisme : audit final et backlog de réalisme du moteur V2

> 05/11/2026. Mission du propriétaire : à partir de l'audit de réalisme du même jour, vérifier chaque constat dans le code, les tickets, les tests et les indicateurs, puis construire un backlog très granulaire (environ 2 h par ticket), estimé et ordonné. **Aucun code moteur n'a été modifié pendant cette mission.**
> Référence : moteur à `924b350` plus l'arbre de travail du 05/11/2026 (ticket `v2-collectif/28b` implémenté, en attente de clôture).

## 1. Règles appliquées

- **Aucun ticket livré n'est modifié.** Une amélioration d'un mécanisme livré est un nouveau ticket qui cite l'original (« Lien avec l'existant »).
- **Aucun ticket ouvert n'est modifié sans décision du propriétaire.** Quand un ticket ouvert est trop gros, ce chantier propose une **découpe** en tickets complémentaires (section 5). Le propriétaire décide s'il marque l'original « découpé (chapeau) », comme lors de l'audit de granularité du 04/11/2026.
- Une fonctionnalité déjà prévue correctement par un ticket ouvert n'est pas dupliquée. Exemples : xG neutre (`v2-collectif/28c`, étape 0), cadrage (`35b`), puissance (`35a`), poteaux (`35c`), hauteur du ballon (`v2-hauteur-ballon/02a`), adaptation au score (`v2-collectif/21`, coach `02`), contrôle orienté (`31`).
- Chaque ticket comporte : constat vérifié (fichier et ligne, ou absence vérifiée par recherche), comportement observable, tests (unitaires, comportementaux, intégration, statistiques), critères vérifiables, dépendances, et une estimation en temps de travail effectif.
- Les repères statistiques (section 8) **ne sont pas des cibles** avant leur vérification (01c). Deux calibrations **provisoires** suivent les fondations P0 (18d, 18e) ; la calibration **finale** (`v2-collectif/22a` à `22c`) vient après les principaux développements tactiques, physiques et collectifs (section 6 bis). Les tickets de mécanisme rapportent les chiffres sans les régler. Par exemple, le gardien se place correctement (03) avant toute calibration du taux d'arrêt.
- Numérotation : un numéro par domaine, une lettre par ticket (`02d`), comme les découpes existantes (`34a`, `28b`). Identifiant complet : `v2-realisme/02d`.

**Priorités.** P0 : sans lui, un match ne peut pas être crédible (structure, gardien, cohérence entre décision et résolution, tir, xG, mesure). P1 : intelligence et réalisme footballistique. P2 : approfondissement.

## 2. Matrice des fonctionnalités (état vérifié le 05/11/2026)

Légende : **V** validé (livré, validé expert + QC) · **P** partiel · **A** absent (absence vérifiée par recherche dans `v2engine/`) · **NV** non vérifié (dépend d'une mesure non refaite).

| Domaine | Mécanisme | État | Où | Suite |
|---|---|---|---|---|
| Structure | Positions de départ par bande | P | `formation.py` (côté selon l'ordre alphabétique, ligne 50) | 02a, 02b |
| Structure | Bloc avec ou sans ballon, hauteur de ligne, piège du hors-jeu | V | `bloc.py` (tickets 04, 05, 23) | 02d, 02e, 10e |
| Structure | Rôles de poste | A | — | 02c, 02d, 02e, 13h |
| Structure | Tenir sa position en possession | A | `cerveau.py:102-103` (tout le monde appelle) | 02f, 02g |
| Structure | Couloirs, demi-espaces, asymétrie | A | — | 09a à 09d |
| Structure | Défense préventive | P | `REST_DEFENDERS = 2` fixe (`defense.py:111`) | 09g |
| Défense | Presseur, couverture, marquage, pressing coordonné, compensations, contre-pressing, repli | V | `defense.py` (tickets 07 à 10) | 10a à 10i |
| Défense | Presseur selon la zone | A | `defense.py:316-317` (premier arrivé) | 10a, 10b |
| Défense | Défense de la surface | A | — | 10f à 10h |
| Gardien | Placement, sorties, face-à-face | A | place fixe (`bloc.py:184`) ; presseur générique (`cerveau.py:123-128`) | 03a à 03g |
| Gardien | Issues de l'arrêt (capté, repoussé, claqué) | P | `shooting.py` (28b implémenté, non clôturé) | 05b |
| Gardien | Notes du gardien dans le tir | P | `shooting._keeper_rating` (Reflexes, One on Ones, Handling lus, part neutre A8) | `v2-attributs-restants/03b` |
| Orientation | Cap du corps, réception de face ou de dos, scan | A | `PlayerState` sans orientation | 07a à 07g, 08a à 08f |
| Perception | Délai de réaction, lecture des passes, Vision, perception brouillée du porteur | V | `anticipation.py`, `decision.py` (ticket 33) | 08 (perception non omnisciente) |
| Décision | Valeur réelle et perception du porteur | V | `decision.py` (ticket 33) | 05e, 08d |
| Conduite | Risque de perte évalué | P | `decision.keep_ball_probability`, jamais utilisé pour la résolution | 04a à 04c |
| Conduite | Ballon distinct du porteur | A | `match.py:383` | 04e, 04f |
| Duels | Tacle debout, faute, avantage | V | `duel.py`, tickets 30 et `v2-socle/03` | 04g à 04j, 11d |
| Contacts | Collisions | P | `match.py:114` (position seule, symétrique) | 11a à 11c |
| Physique | Montée en vitesse, loi d'arrivée | V | `movement.py` (ticket 25) | — |
| Physique | Freinage, virage, Agility | A | `DECEL_MAX_MPS2` commun (`movement.py:27`) | 12a, 12b, 07f |
| Physique | Intensité de course, énergie, sprints répétés | P | presseur et repli seulement ; fatigue par la minute | 12d à 12f |
| Tir | Qualité de l'occasion, décision de tirer | V | `shooting.py` (ticket 28a) | 05e |
| Tir | Trajectoire, cadrage, contre, arrêt physiques | A | but tiré au départ (`match.py:479`), part à côté fixe (`match.py:54`), contreur tiré d'avance (`match.py:461`) | 05a à 05f, `35a` à `35c` |
| xG | xG neutre, xG après frappe, décomposition | A | prévu au `28c` (étape 0) pour le neutre | 06a à 06c |
| Ballon | Freinage au sol | P | exponentiel, non calibré (`possession.py:19`) | 14a |
| Ballon | Hauteur, rebond, effet, rotation | A | — | `v2-hauteur-ballon/02a`, 14b, 14c |
| Aérien, CPA | Duel aérien, corners, coups francs travaillés | A | coups francs simples seulement (ticket 30) | 15, 16 |
| Identité | Styles et consignes d'équipe | A | — | 13a à 13i |
| Mesure | Banc d'indicateurs | V | `scripts/measure_v2.py`, `v2_indicators.py` | 01c à 01e |
| Mesure | Flux aléatoires indépendants | A | 45 tirages dans le flux global, 13 fichiers | 01a, 01b |
| Mesure | Volumes physiques au niveau réel | NV | dernières mesures publiées 20,7 km (30/10) ; 37 % du temps au-dessus de 19,8 km/h (26/10) | 01d, 12g |

## 3. Problèmes confirmés dans le code

| Code | Constat | Preuve | Tickets |
|---|---|---|---|
| C1 | Côté gauche ou droit des joueurs donné par l'ordre alphabétique de leur nom | `formation.py:50` | 02a |
| C2 | Le gardien presse tout porteur adverse à moins de 15 m et ne suit jamais le ballon | `cerveau.py:123-128`, `bloc.py:184` et `224` | 03a, 03b |
| C3 | Risque de conduite évalué (Dribbling) mais jamais résolu ; la perte réelle passe par un tacle rare (0,03/s) | `decision.py:233`, `duel.py:21` | 04a |
| C4 | Le but est tiré au départ du tir ; le ballon est ensuite intouchable ; les tirs à côté sont une part fixe | `match.py:479`, `557`, `54`, `492` | 05a, 05b |
| C5 | Le contreur est tiré avant le départ du tir | `match.py:461` | 05c |
| C6 | Tous les joueurs de champ ont le rôle d'appel quand leur équipe a le ballon | `cerveau.py:102-103` | 02f, 02g |
| C7 | Aucune orientation du corps ; perception omnisciente des positions | `movement.py:72` ; `decision.evaluate_options` | 07, 08 |
| C8 | Collisions symétriques, sans vitesse ni Strength | `match.py:114-132` | 11a, 11b |
| C9 | Freinage commun à tous (Agility non lue) | `movement.py:27` | 12a, 12b |
| C10 | Ballon collé au porteur pendant la conduite | `match.py:383` | 04e |
| C11 | Presseur choisi parmi tous les joueurs de champ, sans zone | `defense.py:316-317` | 10a |
| C12 | Tirages aléatoires dans un seul flux : comparaisons de profils non attribuables | 45 appels dans 13 fichiers ; `docs/INDICATEURS_V2.md` | 01a, 01b |
| C13 | La carte des attributs annonce Technique « branché » ; aucun appel dans le code | `docs/CARTE_ATTRIBUTS_V2.md` ; recherche dans `v2engine/` | 17a |

**Constats de l'audit nuancés après vérification**
- « Attributs de gardien inutilisés » : Reflexes, One on Ones et Handling **sont lus** (`shooting._keeper_rating`), avec une part neutre assumée (A8) jusqu'à `v2-attributs-restants/03b`. Les autres attributs de gardien ne sont pas lus.
- « xG non séparé » : vrai dans le code, mais **déjà prévu** par `v2-collectif/28c` (étape 0, D-V12). Ce chantier ajoute seulement l'xG après frappe et la décomposition (06).
- « Volumes de course » : les chiffres de l'audit (20,7 km, 156 à 507 appels) datent du 26 au 30/10/2026, avant plusieurs tickets. Ils sont marqués **NV** et seront remesurés au 01d avant d'être utilisés.
- « 37,6 tirs par équipe » (mesure 28b) : chiffre confirmé dans le ticket. Sa cause (conduite sans risque réel, bruit de perception à chaque réévaluation) reste une **hypothèse**, testée par 04c et 18a.

## 4. Audit des attributs non exploités ou mal exploités

| Attribut | Fonction footballistique | Situations | Effet prévu | Ticket |
|---|---|---|---|---|
| Agility | Se retourner, freiner, changer de direction | Crochet, défenseur qui se retourne, réception dos au jeu | Vitesse de rotation (07f), freinage (12a), virage (12b) : trois effets distincts d'une même capacité | 07f, 12a, 12b |
| Balance | Continuer l'action après un contact | Après une collision, un duel d'épaule, un tacle subi | Délai et perte de vitesse après contact (retiré du tacle sur décision du propriétaire) | 12c |
| Strength | Gagner le contact | Collision, épaule contre épaule, protection, duel aérien | Poids de contact | 11b, 11c, 04i, 15b |
| Dribbling | Conduite serrée et élimination | Conduite sous pression, duel | Risque réel de perte (04a), vitesse balle au pied (04d), longueur de touche (04e), gestes (04g à 04i) | 04 |
| Technique | Gestes difficiles | Une touche, volée, première intention | Déjà prévu : `v2-collectif/31`, `34a`, `34b`, `36a` ; carte à corriger | 17a |
| Flair | Tendance à l'inattendu | Choix d'options risquées | Déjà prévu : `v2-collectif/19` | — |
| Bravery | Accepter le contact risqué | Contre de tir, plongeon du gardien, duel aérien | Portée de contre, plongeon dans les pieds | 17b ; `v2-attributs-restants/01`, `09b` |
| Determination, Concentration | Intensité quand le score est défavorable ; trous de vigilance | Fin de match, après un but | Déjà prévu : `v2-collectif/21` | — |
| Leadership | Effet sur les coéquipiers | Après un but encaissé | Amortit la baisse collective | 17c |
| Jumping Reach, Heading, taille | Hauteur atteinte, qualité de la tête | Duel aérien, tête au but, dégagement | Duel (15b), tête (15c, 15d) | 15 |
| Crossing | Qualité du centre | Centres | Déjà prévu : `v2-attributs-restants/01`, `11` | — |
| Corners, Free Kick Taking, Long Throws | Coups de pied arrêtés | Corner, coup franc, touche longue | Précision et zone | 16d, 16e, 16f |
| Penalty Taking | Penalty | Penalty | Déjà prévu : `v2-attributs-restants/02a` | — |
| Natural Fitness | Récupération entre les matchs | Hors du match (D-V10) | Aucun effet pendant un match : non branché à raison | — |
| Aerial Reach, Command of Area, Communication, Punching, Kicking, Throwing, Rushing Out, Eccentricity | Gardien | Centres, relances, sorties | Déjà prévu : `v2-attributs-restants/03a`, `03b`, `03c` (sur les mécanismes neutres du domaine 03) | — |
| Vision | Options vues | Scan avant réception | Fréquence des scans, à trancher (recommandation : Vision) | 08c |
| Anticipation | Lire l'action | Mémoire de perception | Qualité de l'extrapolation (rayon existant) | 08b |

Garde générale : 17d (un attribut annoncé branché doit être lu et changer une scène A/B).

## 5. Découpes de tickets ouverts

**Décision du propriétaire (05/11/2026) :** les six découpes ci-dessous (07a, 07b, 01, 02b, `v2-collectif/12`, coach `01`) sont validées. Le statut des six tickets d'origine est mis à jour : chapeau, sauf `v2-attributs-restants/01` qui garde le centre (Crossing). Les deux dernières lignes (03b, 22a) restent des recommandations ; pour 22a, la section 6 bis la remplace (décision du propriétaire).

| Ticket ouvert (non modifié) | Découpe proposée dans ce chantier | Recommandation |
|---|---|---|
| `v2-attributs-restants/07a` (duel un contre un) | 04a (fondation du risque), 04g contournement, 04h crochet, 04i protection, 04j tacle glissé | 07a devient chapeau : 4 gestes et une fondation dépassent largement 2 h. |
| `v2-attributs-restants/07b` (Agility et Balance) | 12a freinage, 12b virage, 12c Balance ; 07f rotation | 07b devient chapeau. |
| `v2-collectif/12` (intensité et énergie) | 12d intensité par rôle, 12e réserve d'énergie, 12f sprints répétés | 12 devient chapeau. |
| `v2-coach-et-gestion-de-match/01` (styles) | 13a fondation, 13b à 13f un style chacun, 13g largeur, 13i validation | coach/01 devient chapeau ; ses critères sont repris en 13i. |
| `v2-attributs-restants/01` (centres, jeu aérien) | 15a à 15f (sélection, duel, tête, dégagement, seconds ballons) | 01 garde le centre (Crossing) ; jeu aérien découpé. |
| `v2-attributs-restants/02b` (coups de pied arrêtés travaillés) | 16a à 16g | 02b devient chapeau. |
| `v2-attributs-restants/03b` (gardien) | Les mécanismes neutres du domaine 03 précèdent 03b, qui ne garde que les notes et tendances | 03b dépendra de 03b à 03e de ce chantier. |
| `v2-collectif/22a` (calibration) | Doit attendre les P0 de ce chantier (point d'étape 18a) | Ajouter `v2-realisme/18a` à ses dépendances. |

## 6. Ordre de réalisation

Les dépendances détaillées sont dans chaque ticket. L'ordre ci-dessous les respecte et place la mesure avant les mécanismes.

1. **Vague 0, indépendants (parallélisables, aucun fichier moteur commun)** : 01c (repères), 01f (fabrique de scènes), 17a (carte), puis 01d (indicateurs physiques), 01a puis 01b (flux aléatoires), 01e (séries longues, nécessaire aux calibrations provisoires).
2. **Vague 1, P0** :
   - Structure : 02a → 02b → 02c → 02d, 02e → 02f → 02g → 02h.
   - Gardien : 03a → 03b → 03c → 03d, puis 03e → 03g.
   - Conduite : 04a → 04b → 04c.
   - Tir (après la clôture de `v2-collectif/28b`, puis `35b` et `28c`, tickets existants à réaliser d'abord) : 05a → 05b → 05c → 05d → 05e → 05g ; 06a → 06b.
   - **Orientation et prise d'information, avancées le 05/11/2026 (décision du propriétaire)** : 07a → 07c, 07e, 07f ; 08a → 08b → 08c. Elles forment la base du contrôle orienté et du jeu à une touche : **`v2-collectif/31` les attend** (son « Blocked by » est complété), et donc 34a, 34b, 36a et 07d après lui.
   - **18a, point d'étape P0** (aucun réglage), puis **18d et 18e, calibrations provisoires** (section 6 bis). Aucun P1 ne démarre avant leur rapport.
3. **Vague 2, P1** (ordre recommandé) : `v2-collectif/31` → 34a → 34b → 36a, puis 07d → 07b → 07g ; 08d, 08e → 08f ; 12d → 12e → 12f, 12a → 12b ; 11a → 11b → 11c, 12c, 11d → 11e ; 04d → 04e → 04f, 04g → 04h, 04i, 04j ; 09a → 09b → 09c, 09d, 09e, 09f → 09g → 09h ; 10a → 10b → 10c, 10d → 10i, 10e, 10f → 10g, 10h → 10j ; 03f, 05f, 06c, 17d, 18b ; 13a.
4. **Vague 3, P2** : 14a → 14b → 14c → 14d ; 15a → 15f ; 16a → 16g ; 17b, 17c ; 01g dès 20 à 30 tickets clôturés.
5. **Calibration finale et validation** : `v2-collectif/22a`, `22b`, `22c` (existants), puis 18c sur graines réservées ; styles d'équipe (13b à 13i) selon le point ouvert du plan.

## 6 bis. Calibrations : provisoires puis finale (décision du propriétaire du 05/11/2026)

| Calibration | Quand | Ce qui est réglé | Statut des valeurs |
|---|---|---|---|
| Point d'étape 18a | après les P0 | rien : écarts attribués | — |
| **Provisoire 1 (18d)** | après 18a | volumes de course, intensité, réception, rythme (km, haute intensité, appels, passes par minute) | « provisoire », datée, mesurée |
| **Provisoire 2 (18e)** | après 18d, gardien validé (03g) | tir, arrêt, contre, valeur du tir dans la décision | « provisoire », datée, mesurée |
| **Finale** (`v2-collectif/22a` → `22b` → `22c`) | après les principaux développements tactiques, physiques et collectifs : orientation et perception (07, 08), occupation (09), défense (10), contacts (11), déplacements (12), conduite et duel (04), passes, hauteur, jeu aérien et coups de pied arrêtés | toutes les constantes, dans leurs fourchettes, sur au moins 500 matchs | définitives ; validation indépendante 18c |

Règles d'une calibration provisoire : seules les constantes des mécanismes concernés bougent ; chaque valeur est marquée « provisoire » dans le code et dans `docs/INDICATEURS_V2.md` ; aucun réglage ne masque une lacune de mécanisme ; la calibration finale repart de ces valeurs et peut toutes les revoir.

**Parallélisation.** La plupart des tickets moteur touchent `cerveau.py`, `match.py` ou `decision.py`. Deux sessions de code ne doivent donc travailler en même temps que sur des fichiers disjoints. Pistes vraiment parallèles : banc et documentation (01c, 01d, 01e, 17a, indicateurs des tickets de validation) ; module gardien (03, nouveau fichier `gardien.py`, après 03a) ; physique des déplacements (12a, 12b dans `movement.py`). Le reste est séquentiel.

## 7. Estimation globale

| Priorité | Tickets | Travail effectif |
|---|---|---|
| P0 | 42 | 79 h 45 |
| P1 | 58 | 101 h 55 |
| P2 | 20 | 34 h 45 |
| **Total** | **120** | **216 h 25** |

Par domaine : 01 mesure 13 h 45 · 02 structure 14 h 40 · 03 gardien 13 h · 04 conduite 19 h 35 · 05 tirs 14 h 25 · 06 xG 5 h 15 · 07 orientation 12 h 45 · 08 perception 11 h 25 · 09 occupation 13 h 10 · 10 défense 18 h 25 · 11 contacts 8 h 20 · 12 déplacements 12 h 25 · 13 identité 14 h 50 · 14 ballon 7 h 05 · 15 aérien 10 h 25 · 16 coups de pied arrêtés 12 h 30 · 17 attributs 6 h 25 · 18 validation 8 h 00. Orientation (07a, 07c, 07e, 07f) et prise d'information (08a à 08c) sont passées en P0 le 05/11/2026 (avancées avant le contrôle orienté), ainsi que 01e (séries longues), dont dépendent les calibrations provisoires.

- **Hors de ces totaux** : les tickets existants dont dépend ce chantier (`28b` clôture, `35a`, `35b`, `28c`, `31`, `v2-hauteur-ballon/02a` et `03`, `v2-attributs-restants/11`, `v2-collectif/21`, calibrations `22a` à `22c`) ; le temps machine (suite complète d'environ 40 min par ticket, séries de 50 à 2 000 matchs).
- **Chemin critique interne** (plus longue chaîne de dépendances) : 01f → 03a → 03b → 05b → 06a → 05e → 05g → 18a → 18d → 18e, soit environ 19 h de travail. La durée réelle sera dictée par la séquence imposée par les fichiers partagés, pas par ce chemin.
- **Tickets au-dessus de 2 h** (2 h 10 à 2 h 20) : 01a, 01b, 01e, 04a, 04e, 05a, 05b, 05c, 05e, 07a. Leur partie développement est indissociable (un mécanisme et son test de cohérence) ; le dépassement vient de l'intégration (mesure, clôture). 04e est à confiance faible : à redécouper après l'analyse si besoin.
- **Fiabilité** : chaque ticket porte un niveau de confiance. Les catégories « exécution » et « physique » sont les plus incertaines (interactions avec la trace et l'écran). Le ticket 01g compare estimations et durées réelles après 20 à 30 tickets.

## 8. Repères statistiques (provisoires jusqu'au 01c)

| Repère | Valeur proposée | Indicateur du banc | Statut avant 01c |
|---|---|---|---|
| Tirs par équipe | 8 à 15 | tirs tracés par équipe (contrés compris, 28b) | indicatif |
| Conversion | 10 à 11 % | buts / tirs | indicatif |
| Buts dans la surface | 80 à 90 % | buts dans la surface (28b) | indicatif |
| Km par joueur de champ | 9 à 14 | km par joueur | indicatif, définition à vérifier |
| Appels par joueur | 5 à 20 (5,5 à 19,2 selon le poste) | appels (plus de 0,7 s au-dessus de 15 km/h) | **à redéfinir** : la définition de la source est peut-être différente |
| Haute intensité | 2 à 5 % au-dessus de 19,8 km/h | temps au-dessus de 19,8 km/h | **à redéfinir** : temps ou distance |
| Passes par minute | 15 à 17 | passes par minute | indicatif |

Tailles d'échantillon : 50 matchs pour l'exploration (tickets de mécanisme), au moins 500 pour la calibration (`22a` à `22c`, avec 01e), 1 000 à 2 000 sur graines réservées pour la validation indépendante (18b, 18c).

## 9. Décisions prises et incertitudes

**Décisions**
- Nouveau chantier dédié plutôt que dispersion dans les chantiers existants : la traçabilité de l'audit reste lisible, et les liens vers l'existant sont explicites.
- Aucune modification de ticket existant, même ouvert ; les découpes sont proposées (section 5).
- Les mécanismes du gardien sont **neutres** (aucun attribut) et précèdent `v2-attributs-restants/03b` : la position doit être juste avant de calibrer les arrêts.
- Résolution du tir par la trajectoire (05a, 05b), avec un estimateur de décision recalé dessus (05e) : même principe que la conduite (04a), une seule vérité entre décision et résolution.
- Orientation et scan avancés avant `v2-collectif/31` (décision du propriétaire du 05/11/2026) : ils sont la base du contrôle orienté et du jeu à une touche.
- Calibrations provisoires après les P0 (18d, 18e), distinctes de la calibration finale (`22a` à `22c`) placée après les développements tactiques, physiques et collectifs (décision du propriétaire du 05/11/2026).
- La règle d'estimation est inscrite dans `CLAUDE.md` et `docs/agents/validation-tickets.md` ; le registre `docs/agents/suivi-estimations.md` en fait une donnée exploitable (01g).

**Incertitudes à trancher par le propriétaire**
- 02a : l'ordre des places de l'onglet « Dispositifs tactiques » est-il récupérable en lecture seule ? Sinon, repli sur le poste seul (les MC d'un 4-4-2 n'ont pas de côté dans la base).
- 04a et 04f : partage entre perte tirée au contact et interception physique entre deux touches.
- 08c : attribut de la fréquence des scans (recommandation : Vision, avec garde contre le double comptage).
- 12c : retirer Balance de la résistance au tacle (mécanisme livré `v2-socle/03`) pour respecter son rayon.
- 05a : livraison couplée avec 05b, ou interrupteur de configuration, pour ne pas laisser un moteur sans arrêts entre deux tickets.
- Temps de calcul : orientation (07a) et champ de vision (08a) ajoutent des calculs à chaque pas ; mesure obligatoire dans ces tickets.

## 10. Liste des tickets

| Ticket | Titre | Prio | Catégorie | Estimation | Confiance | Dépend de |
|---|---|---|---|---|---|---|
| 01a | Flux aléatoires par sous-système : fondation, perception et décision | P0 | mesure | 2 h 15 | moyenne | 01f |
| 01b | Flux aléatoires : duels, passes, tirs, placement, arbitrage | P0 | mesure | 2 h 10 | moyenne | 01a |
| 01c | Repères de calibration : sources, définitions, compatibilité avec le banc | P0 | documentation | 1 h 50 | moyenne | — |
| 01d | Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée | P0 | mesure | 2 h | élevée | 01c |
| 01e | Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance | P0 | mesure | 2 h 10 | moyenne | 01b |
| 01f | Fabrique de scènes de test partagée | P0 | mesure | 1 h 50 | élevée | — |
| 01g | Analyse des écarts entre durées estimées et réelles par catégorie | P2 | mesure | 1 h 30 | élevée | 01f |
| 02a | Côté gauche ou droit selon le poste, et non selon le nom | P0 | placement | 1 h 45 | élevée | 01f |
| 02b | Largeur de référence propre à chaque poste | P0 | placement | 1 h 50 | moyenne | 02a |
| 02c | Rôle de poste par défaut, porté par le joueur et tracé | P0 | données | 1 h 40 | élevée | 02a |
| 02d | Place de référence avec ballon selon le rôle | P0 | placement | 2 h | moyenne | 02b, 02c |
| 02e | Place de référence sans ballon selon le rôle | P0 | placement | 1 h 50 | moyenne | 02b, 02c |
| 02f | Tenir sa position en possession | P0 | décision | 2 h | moyenne | 02d |
| 02g | Qui fait un appel, et quand | P0 | décision | 2 h 05 | moyenne | 02f |
| 02h | Validation de la structure : côtés, rôles, appels, distances | P0 | validation | 1 h 30 | élevée | 02a, 02b, 02d, 02e, 02g, 01d |
| 03a | Gardien : sous-système propre, fin du presseur générique | P0 | placement | 1 h 50 | élevée | 01f |
| 03b | Gardien : placement sur la bissectrice ballon-poteaux | P0 | placement | 2 h | moyenne | 03a |
| 03c | Gardien : hauteur selon le ballon et la ligne défensive (couverture de la profondeur) | P0 | placement | 1 h 45 | moyenne | 03b |
| 03d | Gardien : sortie sur un ballon dans la profondeur | P0 | décision | 2 h 05 | moyenne | 03c |
| 03e | Gardien : fermer l'angle dans un face-à-face | P0 | décision | 2 h | moyenne | 03b |
| 03f | Gardien : en mouvement ou sur ses appuis au moment du tir | P1 | exécution | 1 h 45 | moyenne | 03b, 05b |
| 03g | Validation du placement et des sorties du gardien | P0 | validation | 1 h 35 | élevée | 03b, 03c, 03d, 03e, 01d |
| 04a | Conduite : même risque de perte à l'évaluation et à la résolution | P0 | exécution | 2 h 20 | moyenne | 01f |
| 04b | Conduite : où va le ballon perdu | P0 | exécution | 1 h 45 | moyenne | 04a |
| 04c | Validation : risque annoncé, probabilité calculée, résultat observé | P0 | validation | 1 h 35 | élevée | 04a, 04b, 01d |
| 04d | Vitesse de conduite selon Dribbling et la pression | P1 | physique | 1 h 30 | élevée | 04a |
| 04e | Le ballon n'est plus collé au porteur | P1 | physique | 2 h 15 | faible | 04d |
| 04f | Ballon jouable par un adversaire entre deux touches | P1 | exécution | 2 h 05 | faible | 04e |
| 04g | Duel un contre un : le contournement | P1 | exécution | 2 h 05 | moyenne | 04a |
| 04h | Duel un contre un : le crochet | P1 | exécution | 2 h | moyenne | 04g, 07a, 07f |
| 04i | Duel : protection du ballon dos au défenseur | P1 | exécution | 2 h | moyenne | 04a, 07c, 11b |
| 04j | Le tacle glissé | P1 | exécution | 2 h | moyenne | 04g |
| 05a | Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ | P0 | exécution | 2 h 15 | moyenne | v2-collectif/35b |
| 05b | Arrêt : le gardien atteint ou non le ballon | P0 | exécution | 2 h 20 | moyenne | 05a, 03b |
| 05c | Contre : le défenseur touche réellement le tir | P0 | exécution | 2 h 10 | moyenne | 05a |
| 05d | Déviation du ballon au contact d'un corps | P0 | physique | 1 h 55 | moyenne | 05c |
| 05e | La valeur du tir dans la décision suit la résolution physique | P0 | décision | 2 h 10 | faible | 05b, 05c, 06a |
| 05f | Tir au-dessus de la barre par la vraie hauteur | P1 | exécution | 2 h | moyenne | 05b, v2-hauteur-ballon/02a, v2-collectif/35b |
| 05g | Validation des tirs : trajectoire, cadrage, contres, arrêts | P0 | validation | 1 h 35 | élevée | 05a, 05b, 05c, 05d, 05e, 01d |
| 06a | xG après frappe : la qualité d'exécution mesurée | P0 | mesure | 2 h | moyenne | 05b, v2-collectif/28c |
| 06b | Indicateurs : occasion, exécution, gardien, par attribut | P0 | mesure | 1 h 50 | élevée | 06a |
| 06c | Contrôle de calibration de l'xG neutre sur 500 matchs | P1 | validation | 1 h 25 | élevée | 06b, 01e, 05e |
| 07a | Orientation du corps : état propre et rotation bornée | P0 | physique | 2 h 10 | moyenne | 01f |
| 07b | Se déplacer de face, de côté ou à reculons | P1 | physique | 1 h 55 | moyenne | 07a |
| 07c | Réception de face, de profil ou dos au jeu | P0 | perception | 1 h 50 | élevée | 07a |
| 07d | Temps de contrôle et enchaînement selon l'orientation | P1 | exécution | 1 h 55 | moyenne | 07c, v2-collectif/31 |
| 07e | Se réorienter avant une passe, un tir ou une conduite | P0 | exécution | 2 h | moyenne | 07a |
| 07f | Agility : vitesse de rotation du corps | P0 | physique | 1 h 25 | élevée | 07a |
| 07g | Validation de l'orientation | P1 | validation | 1 h 30 | élevée | 07b, 07c, 07d, 07e, 07f, 01d |
| 08a | Champ de vision : ce qui est dans le dos n'est pas vu | P0 | perception | 1 h 50 | élevée | 07a |
| 08b | Mémoire de perception : positions vues, datées et vieillissantes | P0 | perception | 2 h | moyenne | 08a |
| 08c | Scan visuel avant la réception | P0 | perception | 2 h | moyenne | 08b, 07c |
| 08d | Le porteur décide sur ce qu'il perçoit | P1 | décision | 2 h 05 | moyenne | 08b |
| 08e | Le défenseur ne voit pas toujours l'appel dans son dos | P1 | perception | 2 h | moyenne | 08b, 08c |
| 08f | Validation de la perception | P1 | validation | 1 h 30 | élevée | 08d, 08e, 01d |
| 09a | Couloirs et demi-espaces : définition et mesure | P1 | mesure | 1 h 35 | élevée | 01d |
| 09b | Occuper la largeur en possession | P1 | placement | 1 h 55 | moyenne | 02d, 09a |
| 09c | Occuper les demi-espaces selon le rôle | P1 | placement | 1 h 40 | moyenne | 09b, 02c |
| 09d | Formations asymétriques | P1 | placement | 1 h 30 | élevée | 02d, 02e |
| 09e | Distances entre les lignes en possession | P1 | placement | 1 h 45 | moyenne | 02d |
| 09f | Un attaquant reste haut quand l'équipe défend | P1 | placement | 1 h 30 | élevée | 02e |
| 09g | Défense préventive : un défenseur de plus que les attaquants restés haut | P1 | décision | 2 h | moyenne | 02f, 09f |
| 09h | Validation de l'occupation tactique | P1 | validation | 1 h 15 | élevée | 09b, 09c, 09d, 09e, 09g |
| 10a | Choix du presseur selon la zone et la responsabilité | P1 | décision | 2 h | moyenne | 02e |
| 10b | Le défenseur central ne quitte sa ligne que couvert | P1 | décision | 1 h 55 | moyenne | 10a |
| 10c | Couverture de la profondeur derrière la ligne | P1 | placement | 2 h | moyenne | 10b |
| 10d | Protection de l'axe : le milieu récupérateur fait écran | P1 | placement | 1 h 40 | moyenne | 02e |
| 10e | Coulissement : côté ballon serré, côté opposé resserré vers l'axe | P1 | placement | 1 h 45 | moyenne | 01f |
| 10f | Défense de la surface : premier poteau, second poteau, point de penalty, retrait | P1 | placement | 2 h | moyenne | 02e |
| 10g | Marquage dans la surface : homme ou zone | P1 | décision | 2 h | moyenne | 10f |
| 10h | Défendre le centre en retrait | P1 | placement | 1 h 40 | moyenne | 10f |
| 10i | Compensation d'un trou au milieu | P1 | décision | 1 h 50 | moyenne | 10d |
| 10j | Validation de la défense collective | P1 | validation | 1 h 35 | élevée | 10a, 10b, 10c, 10d, 10e, 10g, 10h, 10i |
| 11a | Collision : la vitesse change aussi, pas seulement la position | P1 | physique | 1 h 35 | élevée | 01f |
| 11b | Collision asymétrique : Strength | P1 | physique | 1 h 25 | élevée | 11a |
| 11c | Duel épaule contre épaule à la course | P1 | exécution | 2 h | moyenne | 11b |
| 11d | Le tacle selon l'angle d'approche et la vitesse relative | P1 | exécution | 1 h 55 | moyenne | 07a |
| 11e | Validation des contacts physiques | P1 | validation | 1 h 25 | élevée | 11c, 11d, 12c |
| 12a | Freinage individualisé : Agility | P1 | physique | 1 h 25 | élevée | 01f |
| 12b | Perte de vitesse en virage | P1 | physique | 1 h 55 | moyenne | 12a |
| 12c | Balance : rester debout et continuer après un contact | P1 | physique | 1 h 55 | moyenne | 11b |
| 12d | Intensité de course selon le rôle | P1 | physique | 2 h | moyenne | 02f |
| 12e | Réserve d'énergie qui dépend de l'effort | P1 | physique | 2 h | moyenne | 12d |
| 12f | Répéter les sprints et récupérer | P1 | physique | 1 h 55 | moyenne | 12e |
| 12g | Validation de la physique des déplacements | P1 | validation | 1 h 15 | élevée | 12a, 12b, 12c, 12d, 12e, 12f, 01d |
| 13a | Consignes d'équipe : lecture des styles et structure neutre | P1 | données | 1 h 50 | élevée | 01f |
| 13b | Style Pressing | P1 | décision | 1 h 50 | moyenne | 13a, 12e |
| 13c | Style Défensif | P1 | décision | 1 h 35 | moyenne | 13a, 02g, 09g |
| 13d | Style Offensif | P1 | décision | 1 h 35 | moyenne | 13a, 02g, 09g |
| 13e | Style Contre-attaque | P1 | décision | 1 h 35 | moyenne | 13a, 09f |
| 13f | Style Possession et tempo | P1 | décision | 1 h 40 | moyenne | 13a |
| 13g | Consigne de largeur | P1 | placement | 1 h 25 | élevée | 13a, 09b |
| 13h | Rôles cohérents avec la formation | P1 | données | 1 h 40 | moyenne | 02c, 13a |
| 13i | Validation des styles : des équipes différentes, pas meilleures | P1 | validation | 1 h 40 | moyenne | 13b, 13c, 13d, 13e, 13f, 13g, 13h, 01e |
| 14a | Freinage du ballon au sol : roulement et air | P2 | physique | 2 h 05 | moyenne | 01c |
| 14b | Effet latéral du ballon (enroulé) | P2 | physique | 2 h | faible | 14a, v2-hauteur-ballon/02a |
| 14c | Rotation et rebond | P2 | physique | 1 h 45 | faible | 14b |
| 14d | Validation de la physique du ballon | P2 | validation | 1 h 15 | élevée | 14a, 14b, 14c |
| 15a | Qui attaque la trajectoire aérienne | P2 | décision | 2 h | moyenne | v2-hauteur-ballon/03 |
| 15b | Duel aérien : taille, Jumping Reach, Strength au contact | P2 | exécution | 2 h | moyenne | 15a, 11b |
| 15c | Qualité de la tête : Heading | P2 | exécution | 1 h 55 | moyenne | 15b, 05a |
| 15d | Dégagement défensif de la tête | P2 | décision | 1 h 35 | moyenne | 15c |
| 15e | Seconds ballons après un duel aérien | P2 | placement | 1 h 40 | moyenne | 15a, 05d |
| 15f | Validation du jeu aérien | P2 | validation | 1 h 15 | élevée | 15b, 15c, 15d, 15e |
| 16a | Corner : placement offensif | P2 | placement | 1 h 50 | moyenne | 15a |
| 16b | Corner : défense en zone, individuelle ou mixte | P2 | placement | 1 h 55 | moyenne | 16a, 10f, 13a |
| 16c | Corner : appels et écrans | P2 | décision | 1 h 55 | faible | 16b, 11b |
| 16d | Corner : exécution (Corners) | P2 | exécution | 1 h 55 | moyenne | 16a, 14b, v2-attributs-restants/11 |
| 16e | Coup franc direct et mur | P2 | exécution | 2 h 05 | faible | 05b, 14b, v2-collectif/35a |
| 16f | Touche longue (Long Throws) | P2 | exécution | 1 h 35 | moyenne | 15a |
| 16g | Validation des coups de pied arrêtés | P2 | validation | 1 h 15 | élevée | 16b, 16c, 16d, 16e, 16f |
| 17a | Carte des attributs : état réel de branchement | P0 | documentation | 1 h 15 | élevée | — |
| 17b | Bravery : se jeter pour contrer, plonger dans les pieds | P2 | décision | 1 h 35 | moyenne | 05c, 03e |
| 17c | Leadership : amortir la baisse collective après un but encaissé | P2 | décision | 1 h 40 | faible | v2-collectif/21 |
| 17d | Test de garde : attribut annoncé branché = attribut lu avec effet | P1 | validation | 1 h 55 | moyenne | 17a, 01f |
| 18a | Point d'étape après les fondations P0 | P0 | validation | 1 h 30 | élevée | 02h, 03g, 04c, 05g, 06b, 17a |
| 18b | Protocole de validation indépendante | P1 | validation | 1 h 30 | élevée | 01e, 01c |
| 18c | Validation indépendante sur 1 000 à 2 000 matchs | P1 | validation | 1 h 20 | moyenne | 18b, v2-collectif/22c |
| 18d | Calibration provisoire 1 : volumes de course et rythme après les fondations P0 | P0 | validation | 1 h 50 | moyenne | 18a, 01e |
| 18e | Calibration provisoire 2 : tirs, conversion et gardien après les fondations P0 | P0 | validation | 1 h 50 | moyenne | 18d, 05g, 03g, 06b |

P0 : 42 tickets, 79 h 45
P1 : 58 tickets, 101 h 55
P2 : 20 tickets, 34 h 45
Total : 120 tickets, 216 h 25
Chemin critique interne : 01f → 03a → 03b → 05b → 06a → 05e → 05g → 18a → 18d → 18e (18 h 55)

## 11. Complément de l'audit de la roadmap (10/11/2026)

Rapport : `docs/AUDIT_ROADMAP_V2.md`. Aucun code modifié, aucun ticket livré modifié, aucun ticket supprimé.

**Nouveaux domaines**
- **19, fondations transverses (P0, avant 18a)** : 19a façade des notes (performance momentanée), 19b journal des événements et chaîne de causes, 19c garde probabiliste, 19d banc du rendement selon la minute. 7 h 40.
- **20, condition physique (P1, 20g en P2)** : 20a technique, 20b lucidité, 20c récupération, 20d validation fatigue et remplacements, 20e bloc et pressing selon la capacité restante, 20f forme du jour, 20g blessures sans contact. 12 h 45.
- **21, arbitrage et lois du jeu (P1 et P2)** : 21a arbitre qui perçoit, 21b gravité selon l'action, 21c fautes hors du tacle, 21d main, 21e passe en retrait au gardien, 21f simulation, 21g et 21h VAR. 15 h.
- **09i** appels en arc et temporisés (P1, 1 h 45) ; `v2-mise-en-scene/05` et `06` (P3, 4 h).

**Ordre modifié** : `05e` → `05g` ; `19d` en parallèle ; `19a` → `19c` → `19b` ; **18a** ; `12d` → `12e` (promus P0) ; **18d** → **18e**. 18a, 18d, 12d, 12e, `v2-collectif/21`, `22a`, coach `05a`, `v2-attributs-restants/03b`, `09a`, `09b` et `v2-mise-en-scene/02` portent une section « Complément de l'audit de la roadmap (10/11/2026) ».

| Ticket | Titre | Prio | Catégorie | Estimation | Confiance | Dépend de |
|---|---|---|---|---|---|---|
| 19a | Performance momentanée : un seul point d'entrée pour lire une note | P0 | architecture | 2 h 20 | élevée | 05e |
| 19b | Journal des événements et chaîne de causes | P0 | architecture | 2 h 05 | moyenne | 05e |
| 19c | Garde probabiliste : jamais infaillible, jamais incapable | P0 | validation | 1 h 30 | élevée | 05e |
| 19d | Banc : rendement selon la minute et la fatigue | P0 | mesure | 1 h 45 | élevée | 01d, 01e |
| 20a | La fatigue dégrade l'exécution technique | P1 | exécution | 2 h | moyenne | 19a, 12e |
| 20b | La fatigue dégrade la lucidité | P1 | décision | 2 h | moyenne | 19a, 12e |
| 20c | Récupération pendant les arrêts de jeu et à la mi-temps | P1 | physique | 1 h 30 | moyenne | 12e |
| 20d | Validation de la fatigue et des remplacements | P1 | validation | 1 h 30 | élevée | 19b, 19d, 20a, 20b, 20c, 12f |
| 20e | Le bloc et le pressing suivent la capacité restante | P1 | décision | 2 h | moyenne | 12e, 10a, 10c, 13b |
| 20f | Forme du jour | P1 | exécution | 1 h 45 | moyenne | 19a, 01e |
| 20g | Blessures sans contact, coups et crampes | P2 | physique | 2 h | faible | v2-attributs-restants/09b, 12f, 19a |
| 21a | L'arbitre décide sur ce qu'il voit | P1 | arbitrage | 2 h 05 | moyenne | 19b |
| 21b | Gravité de la faute selon l'action | P1 | arbitrage | 2 h | moyenne | 11d, 04j |
| 21c | Fautes hors du tacle | P1 | arbitrage | 2 h | moyenne | 11c, 04g, 04i, 21b |
| 21d | La main | P2 | arbitrage | 2 h | faible | v2-hauteur-ballon/02a, 07a, 21a |
| 21e | Passe en retrait au gardien | P1 | arbitrage | 1 h 30 | moyenne | v2-attributs-restants/03c ou v2-collectif/32a |
| 21f | Simulation | P2 | arbitrage | 1 h 45 | faible | 21a, v2-attributs-restants/09a |
| 21g | VAR : buts et penalties | P2 | arbitrage | 2 h 10 | moyenne | 21a, 21d, 21f, 19b, v2-attributs-restants/09a |
| 21h | VAR : rouge direct et erreur d'identité | P2 | arbitrage | 1 h 30 | moyenne | 21g, 21b, v2-attributs-restants/09a |
| 09i | Appels en arc et appels temporisés | P1 | décision | 1 h 45 | moyenne | 07e, 08e, 02g |

Hors de ce tableau : `v2-mise-en-scene/05` (gestes visibles, P3, 2 h) et `06` (réactions des joueurs, P3, 2 h).
Total du complément : 22 tickets, 41 h 10 (P0 7 h 40 ; P1 20 h 05 ; P2 9 h 25 ; P3 4 h).

## 12. Complément : hors-jeu et coups de pied arrêtés (10/11/2026)

Rapport : `docs/AUDIT_ROADMAP_V2.md` §12. 5 tickets, 9 h 25.

| Ticket | Titre | Prio | Catégorie | Estimation | Confiance | Dépend de |
|---|---|---|---|---|---|---|
| 21i | Hors-jeu : rebond après un tir, déviation contre jeu volontaire, gêne d'un adversaire | P1 | arbitrage | 2 h | moyenne | 19b, 21a, 16h |
| 16h | Coup franc indirect : distinguer direct et indirect, hors-jeu en vraie remise en jeu | P2 | arbitrage | 2 h 10 | moyenne | v2-collectif/30 (livré) |
| 16i | Coup franc centré : placement des deux équipes, ligne défensive et hors-jeu | P2 | placement | 2 h | moyenne | 16a, 16b, 16e, 16h |
| 16j | Tireurs désignés : une table par équipe | P2 | données | 1 h 30 | élevée | v2-collectif/29 (livré) |
| 16k | Touche ordinaire : appels, marquage et remise rapide | P2 | placement | 1 h 45 | moyenne | v2-collectif/29, 02g (livrés) |
| 03l | Gardien : anticiper le côté, être pris à contre-pied, rester figé sur un tir imparable | P1 | décision | 2 h | moyenne | 03f, 07a, v2-attributs-restants/03b |

03l vient du §13 de l'audit (complément gardien). Total des compléments du 10/11/2026 : 28 tickets, 52 h 35 (P0 7 h 40 ; P1 24 h 05 ; P2 16 h 50 ; P3 4 h).
