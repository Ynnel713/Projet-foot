# 25: Socle cinématique et contact du ballon

**What to build:** Rendre le mouvement des joueurs et le contact du ballon physiquement crédibles et **indépendants du pas de temps**, avant de construire la défense organisée. Aujourd'hui un joueur fonce vers sa cible sans freiner, la dépasse et oscille autour ; il s'arrête net quand son intensité baisse ; le ballon traverse un joueur placé sur sa trajectoire ; un contrôle raté ne coûte presque rien ; et l'écran de match ne calcule pas au même pas que le banc de mesure. Les tickets 06 à 10 mesurent des distances entre joueurs et des interceptions : ces défauts les fausseraient.

**Attributs :** Pace, Acceleration (capacité, règle R5) ; First Touch (contrôle raté). Aucun attribut nouveau : Agility (freiner, se retourner) reste à créer en phase 7, le freinage est donc **le même pour tous** ici.

**Blocked by:** 23 (stabilisation de sa deuxième passe : les deux tickets touchent `match._step_ball`). Numéro 24 laissé libre : il est réservé à « la passe dans l'espace » proposée dans le ticket 23.

**Bloque :** 06, 07, 08, 09, 10 (mesures de distances et d'interceptions) et 12 (qui ne porte plus la loi d'arrivée, voir plus bas).

**Status:** livré (30/10/2026), validé expert + QC

**Origine :** audit global du moteur V2 du 29/10/2026 (agent `expert` en mode audit, constats vérifiés dans le code et par exécution hors dépôt). Constats repris : A-01, A-02, B-02, B-03, B-06, B-08, B-10, C-01.

## Constats et mesures de départ (29/10/2026, état `e64780b` + deuxième passe du 23)

| Constat | Où | Mesure ou calcul |
|---|---|---|
| Pas d'arrivée : vitesse max jusqu'à 0,1 m de la cible (C-01) | `movement.py:86-99` | Cible fixe à 20 m (Pace/Acceleration 60) : pointe à 25,2-26,1 m, puis oscillation entre 14 et 26 m sur les 10 dernières secondes, quel que soit le pas (0,05 / 0,1 / 0,15 s) |
| Arrêt net quand l'intensité baisse (B-02) | `movement.py:101-103` | 8,7 → 3,48 m/s en un pas : 52 m/s² à 0,1 s, 35 m/s² à 0,15 s |
| Accélérations trop fortes (B-10) | `movement.py:20` (`_ACCEL_POINTS`, « à dire d'expert ») | Jusqu'à 20 m/s² (Acceleration et Pace 99), 6,7 m/s² au milieu de l'échelle |
| Le ballon traverse les joueurs (A-02) | `match.py:251-259` (test au point final du pas, rayon 0,41 m) | Contact détecté, joueur immobile sur la trajectoire : 30 m/s → 32 % (pas 0,1 s), 18 % (0,15 s) ; 16 m/s → 61 % / 34 % |
| Priorité domicile sur un ballon disputé (B-06) | `match.py:257-290` (premier de la liste, puis `break`) | Ampleur non mesurée |
| Contrôle raté presque gratuit (B-03) | `match.py:279-289` | Ballon replacé à 0,41 m devant le joueur, à sa vitesse : environ 89 % de réussite en 3 tentatives (0,3 s) pour First Touch 30 |
| Lecteurs de passe jamais oubliés (B-08) | `match.py:253-255`, `279-281` | Ils courent vers le point d'une passe qui n'existe plus |
| Pas du produit différent du pas calibré (A-01) | `api/routers/v2.py:24` (0,15 s) contre `scripts/measure_v2.py:31` (0,1 s) | Les chiffres du banc décrivent un autre match que celui regardé |

## Constantes proposées (soumises à validation du propriétaire)

**Recommandation en tête :** un modèle physique simple et standard, qui ne dépend pas du pas et qui ajoute **une seule** constante produit par mécanisme. Les valeurs réelles ci-dessous sont des ordres de grandeur **à vérifier dans les sources citées avant validation** : je ne les ai pas relues dans le texte.

1. **Montée en vitesse : modèle exponentiel au lieu d'une accélération constante.** La vitesse rejoint la vitesse visée selon `v(t) = v_max·(1 − e^(−t/τ))`, le modèle classique du sprint (Furusawa 1927 ; Samozino et Morin, profil force-vitesse). Forme exacte en pas discret : `v ← v_visée + (v − v_visée)·e^(−dt/τ)`. Ce calcul est exact quel que soit `dt`. L'accélération est maximale au départ (`v_max/τ`), puis décroît naturellement.
   - `τ` selon Acceleration, avec la courbe partagée : **proposition 99 → 0,8 s, 55 → 1,1 s, 11 → 1,4 s**. Accélération au départ, Pace 60 et Acceleration 55 : 8,7 / 1,1 ≈ 7,9 m/s². Ordre de grandeur réel à sourcer (revue de Harper, Carling et Kiely, 2019, *Sports Medicine*, accélérations en match).
   - Remplace `_ACCEL_POINTS` (temps jusqu'à la vitesse max), qui disparaît.
2. **Freinage borné, le même pour tous : `DECEL_MAX_MPS2`.** **Proposition 7 m/s².** Ordre de grandeur réel des fortes décélérations en match : à sourcer (même revue). Il s'applique à l'approche d'une cible et à toute baisse d'intensité : la vitesse visée change d'un coup, la vitesse réelle non. Il sera modulé par Agility en phase 7.
3. **Loi d'arrivée sans nouvelle constante.** Vitesse visée = `min(v_max_effective, √(2·DECEL_MAX·d))`, où `d` est la distance à la cible : le joueur commence à freiner pile à sa distance d'arrêt. On garde la zone morte actuelle de 0,1 m.
4. **Contrôle raté : le ballon s'échappe vraiment.**
   - Direction : celle du ballon reçu, déviée d'un angle tiré dans ±`MISS_DEVIATION_MAX_DEG`, qui grandit avec la difficulté du contrôle (déjà calculée par `attempt_control`). **Proposition : 20° pour un contrôle facile, 60° pour le plus difficile.**
   - Vitesse : `MISS_SPEED_SHARE` de la vitesse reçue. **Proposition : 50 %.**
   - Délai avant que le même joueur puisse retenter : `MISS_RETRY_S`. **Proposition : 0,5 s.**
   - Données réelles : non trouvé.
5. **Pas de temps du produit.** **Recommandation : l'API passe à 0,1 s** (un seul moteur mesuré, un seul moteur regardé), avec `record_every` = 10 pour garder une image par seconde. Coût : environ +50 % de calcul par match. Variante : rester à 0,15 s et calibrer le banc à 0,15 s.

Sans constante : le contact sur le trajet du ballon, le premier contact prioritaire, et l'oubli des lecteurs de passe.

## Constantes validées par le propriétaire (29/10/2026)

Validées avec deux corrections, après vérification des sources :

| Constante | Valeur validée | Source |
|---|---|---|
| `τ` selon Acceleration (`movement._TAU_POINTS`) | 99 → 1,0 s · 55 → 1,2 s · 11 → 1,5 s (au lieu de 0,8 / 1,1 / 1,4) | Footballeurs pros : F0 = 5,18 N/kg, V0 = 10,29 m/s, soit τ ≈ 2 s (PMC9819841, premier sprint). Avec 0,8 s, un joueur noté 99 démarrait à 12,7 m/s², plus qu'un sprinteur olympique ; désormais 10,1 m/s² au mieux, 7,3 m/s² pour un joueur moyen |
| `DECEL_MAX_MPS2` | 7 m/s² | Harper, Carling et Kiely 2019 : freinages au-dessus de 3,5 m/s² fréquents en match, plus que les accélérations ; valeur maximale non trouvée |
| `MISS_DEVIATION_MIN_DEG` / `MISS_DEVIATION_MAX_DEG` | 20° / 60° | non trouvé |
| `MISS_SPEED_SHARE` | 50 % | non trouvé |
| `MISS_RETRY_S` | 0,5 s | non trouvé |
| Pas du produit (`match.TICK_SECONDS`) | 0,1 s, une image enregistrée toutes les 10 étapes | API et banc au même pas |

## Ce qu'on livre

- **Contact sur le trajet** : distance minimale entre le joueur et le segment parcouru par le ballon pendant le pas (en mouvement relatif). Les contacts sont traités dans l'ordre où ils se produisent : le premier joueur touché tente le premier, quelle que soit son équipe. Fin du biais domicile.
- **Montée en vitesse exponentielle, freinage borné, loi d'arrivée** dans `movement.step`, avec la même signature : les appelants (`cerveau`, `match`) ne changent pas.
- **Contrôle raté** : déviation, vitesse résiduelle et délai de reprise ; les lecteurs de passe sont oubliés quand la passe meurt ou qu'un contrôle est raté.
- **Pas aligné** : API et banc au même pas (point 5), et une nouvelle mesure de référence sur 20 matchs.
- **Hors périmètre** : ordre latéral de la formation (B-04, prérequis des tickets 06 et 09, ticket séparé) ; engagement après un but (B-05) ; Agility (phase 7) ; intensité selon le rôle (ticket 12). Le ticket 12 garde l'intensité et l'énergie ; la loi d'arrivée du patch `wip-socle-02-intensite.patch` (`ARRIVAL_RADIUS_M`) est remplacée par celle-ci, et ce patch vise un `_step_player` antérieur à `cerveau.py`.

## Critères d'acceptation

- [ ] Contact : un ballon à 6, 10, 16, 21 et 30 m/s qui traverse un joueur immobile (contrôle forcé à « réussi ») donne **100 % de contact** aux pas 0,05, 0,1 et 0,15 s (100 positions de départ décalées par pas)
- [ ] Premier contact : deux joueurs d'équipes différentes sur la trajectoire, le plus proche de l'arrivée du ballon tente en premier, **dans les deux sens** (test miroir domicile/extérieur)
- [ ] Arrivée : cible fixe à 20 m (Pace/Acceleration 60), **dépassement ≤ 0,5 m**, vitesse < 0,2 m/s en moins de 6 s, amplitude < 0,3 m sur les 10 dernières secondes, aux trois pas ; position finale identique à 0,1 m près entre les pas
- [ ] Freinage : sur tout scénario (baisse d'intensité, arrivée, demi-tour), la décélération mesurée par pas ne dépasse jamais `DECEL_MAX_MPS2` (+1 % de marge numérique), aux trois pas
- [ ] Accélération : l'accélération au départ suit `v_max/τ`, et Acceleration 99 contre 11 donne un écart de temps mesurable et dans le bon sens sur 10 m (TEST-V01)
- [ ] Contrôle raté : le même joueur ne retente pas avant `MISS_RETRY_S` ; la direction du ballon reste dans ±`MISS_DEVIATION_MAX_DEG` autour de la direction reçue ; First Touch 99 contre 11 donne un écart mesurable et dans le bon sens sur le taux de ballons gardés
- [ ] Lecteurs : après une passe morte ou un contrôle raté, `ball.readers` est vide (test unitaire)
- [ ] Pas : l'API et `scripts/measure_v2.py` utilisent le même pas ; sur 20 matchs (graines 20260923 à 20260942), les indicateurs à 0,1 et à 0,15 s restent dans **2 erreurs-types** l'un de l'autre, ou l'écart est documenté et le pas du produit est tranché
- [ ] Mesure de référence avant/après sur 20 matchs, consignée dans ce ticket (tirs, buts, tacles, hors-jeu, passes chez l'adversaire, receveur visé, km par joueur, part au-dessus de 25 km/h, appels, temps de calcul par match) : chiffres d'observation, **pas d'objectif** ; pas de réglage générique avant le ticket 22
- [ ] Temps de calcul par match mesuré avant/après, sur machine non chargée (NFR-V01)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18) ; aucun import privé ajouté entre modules
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée

## Implémentation (29/10/2026)

- `movement.step` : montée en vitesse exponentielle exacte en pas discret, freinage borné à `DECEL_MAX_MPS2` dès que la vitesse visée ferait ralentir (baisse d'intensité, arrivée, changement de direction), loi d'arrivée `√(2·a·d)` sous sa forme en pas discret (la vitesse de fin de pas tient compte du chemin parcouru pendant le pas), position par la vitesse moyenne du pas. Même signature. `accel_time_s` devient `accel_tau_s`.
- `match._step_ball` : contact sur le segment parcouru par le ballon pendant le pas, en mouvement relatif, contacts traités dans l'ordre d'entrée dans le rayon (fin de la priorité domicile). Le passeur ne touche pas sa propre passe tant qu'elle s'éloigne de lui (`BallState.released_by`). Sans cette exclusion, le passeur recontrôlait sa passe dès son départ, et un premier jet donnait 69 buts par match.
- Contrôle raté : `possession.missed_control_velocity`, déviation selon la difficulté déjà calculée par `control_difficulty`, et délai `BallState.control_ban_until_s`. Les lecteurs de passe sont oubliés quand la passe meurt ou qu'un contrôle est tenté.
- `api/routers/v2.py` et `scripts/measure_v2.py` lisent `match.TICK_SECONDS`. Le banc gagne `--pas` et le temps de calcul par match.
- Cible mobile (correctif A1 de la revue expert) : `movement.step(..., target_velocity)` applique la loi d'arrivée à la vitesse de rapprochement ; `cerveau` passe la vitesse du porteur au presseur et au soutien (`Intention.target_velocity`). Sans cible mobile, le comportement est inchangé.
- `released_by` est oublié dès qu'un joueur tient ou touche le ballon (A3). Deux joueurs déjà au contact au début du pas sont départagés par la distance (A4).
- Tests : `tests/test_v2engine_cinematique.py` (43 tests : un par critère aux trois pas, plus la poursuite aux trois pas, les intentions du presseur, `released_by` et l'égalité de contact) ; `tests/test_v2engine_movement.py` adapté (`accel_tau_s`).

## Mesures (20 matchs, graines 20260923 à 20260942, après le correctif A1)

Chiffres d'observation, pas d'objectif ; pas de réglage générique avant le ticket 22. « Avant » : état `b4a7264`, sortie de `scripts.measure_v2`. « Après » : même boucle, un collecteur par match (moyenne ± erreur-type).

| Indicateur | Avant, 0,15 s (ancien produit) | Avant, 0,1 s (ancien banc) | Après, 0,1 s (produit et banc) | Après, 0,15 s |
|---|---|---|---|---|
| Tirs par équipe | 13,9 | 15,0 | 17,8 ± 0,5 | 13,8 ± 0,7 |
| Buts par match | 3,4 | 2,75 | 4,85 ± 0,47 | 3,7 ± 0,47 |
| Tacles par match | 62,3 | 59,9 | 87,0 ± 2,2 | 81,7 ± 2,1 |
| Hors-jeu par match | 3,05 | 2,6 | 1,25 ± 0,25 | 1,15 ± 0,24 |
| Passes chez l'adversaire | 36,5 % | 34,3 % | 35,4 % | 39,3 % |
| Receveur visé | 33,7 % | 41,1 % | 31,9 % | 35,9 % |
| Passes par minute | 16,0 | 17,3 | 21,8 ± 0,2 | 19,5 ± 0,1 |
| Pertes de balle par match | 571 | 581 | 755 ± 6 | 743 ± 5 |
| km par joueur de champ | 30,7 | 30,5 | 23,1 | 23,3 |
| Distance au-dessus de 25 km/h | 60,3 % | 59,3 % | 23,4 % | 23,6 % |
| Temps au-dessus de 19,8 km/h | 54,2 % | 53,5 % | 32,4 % | 33,0 % |
| Appels par match | 4 093 | 3 975 | 2 669 ± 48 | 2 715 ± 53 |
| Latence de repli | 1,99 s | 2,07 s | 2,91 s | 2,96 s |

- **Lecture** : les joueurs ne foncent plus à pleine vitesse jusqu'à leur cible. La course intense chute (de 59 % à 23 % de la distance au-dessus de 25 km/h, de 30,5 à 23 km par joueur ; encore loin du réel, réglage au ticket 22). Depuis le correctif A1, le presseur rattrape vraiment le porteur en conduite : les tacles passent de 60 à 87 par match et les pertes de balle de 581 à 755. Le jeu se hache davantage (21,8 passes par minute, 4,85 buts par match). Le premier passage, sans le correctif, donnait 58 tacles et 3,6 buts.
- **Pas de calcul** : à 0,1 et à 0,15 s, 64 indicateurs sur 81 restent dans 2 erreurs-types l'un de l'autre. Les autres s'écartent de quelques pour cent à 10 %, par exemple 21,8 passes par minute contre 19,5 et 64,6 % de passes réussies contre 60,6 %. L'écart restant vient de ce qui n'est pas encore indépendant du pas : frottement du ballon (2,6 % de distance en trop à 0,1 s, 4 % à 0,15 s, d'après l'expert) et cadence des décisions. Le pas du produit est tranché : 0,1 s, validé par le propriétaire.
- **Temps de calcul (NFR-V01)** : chronométrage alterné avant/après, même match (graine 20260923, 30 minutes extrapolées à 90), 3 essais, médiane. Machine encore chargée d'environ 30 % par d'autres processus, inévitable ici ; l'alternance rend la comparaison équitable.

  | | 0,15 s | 0,1 s |
  |---|---|---|
  | Avant (`b4a7264`) | 87 s (109 ; 85 ; 87) | 170 s (175 ; 145 ; 170) |
  | Après | 141 s (155 ; 128 ; 141) | 169 s (234 ; 164 ; 169) |

  Ces essais sont bruités : jusqu'à 40 % d'écart entre deux essais identiques. À 0,1 s, l'ancien et le nouveau code donnent la même médiane (169 s contre 170 s), mais à 0,15 s le nouveau est nettement plus lent (141 s contre 87 s). Trois essais sur machine chargée ne permettent donc pas de chiffrer le surcoût propre au code. Pour un match regardé, le coût du ticket se situe entre 1,5 fois (banc sur 20 matchs : 94 s avant à 0,15 s, 143 s après à 0,1 s, autre méthode : match complet avec le collecteur de mesures) et 1,9 fois (chronométrage alterné : 87 s puis 169 s). Le ticket prévoyait environ 1,5 fois. Le critère « machine non chargée » n'a pas pu être tenu : d'autres sessions occupaient le processeur. Une mesure au repos reste à faire. L'appel à l'API est synchrone et le client n'a pas de délai d'expiration : l'attente avant de voir un match approche 3 minutes.
- **Déterminisme** : mêmes empreintes (score, nombre de décisions, hors-jeu, position finale du ballon au micromètre) sur deux exécutions des deux premiers matchs.

## Comments

- **29/10/2026, passage 1.** Expert : REJECTED. Bloquant A1 : la loi d'arrivée ignorait la vitesse d'une cible mobile, donc un presseur restait à environ 5 m derrière un porteur en conduite, sans tacle possible. Réserve A2 : temps de calcul mesuré sur machine chargée. Facultatifs : A3 (`released_by` jamais remis à zéro), A4 (égalité de contact départagée par l'ordre de la liste), A5 (frottement du ballon dépendant du pas, hors périmètre). QC : REFUSÉ (temps de calcul non mesuré proprement ; km « après » non sourcés). Clôture : non validée. Corrections : A1 (`movement.step` reçoit `target_velocity`, que `cerveau` renseigne pour le presseur et le soutien, avec des tests de poursuite aux trois pas), A3, A4, chronométrage alterné, nouvelle mesure. `v2engine/cerveau.py` ajouté aux fichiers du ticket. A5 laissé à un ticket dédié.
- **29-30/10/2026, passage 2.** Expert : APPROVED_WITH_RESERVATIONS. A1 du passage 1 levé (poursuite exacte, testée aux trois pas) ; A3 et A4 corrigés. Réserves : A1 (dérive des indicateurs : 4,85 buts, 87 tacles, 755 pertes par match à 0,1 s ; réglage renvoyé au ticket 22) ; A2 (coût de calcul 1,5 à 1,9 fois, environ 3 minutes par match regardé, mesuré sur machine chargée). Facultatifs non traités : A3 (zone morte et cible mobile, à-coup léger), A4 (défenseur battu sans seconde chance, ticket 08), A5 (frottement du ballon dépendant du pas), A6 (corrigé dans la table). QC : REFUSÉ (chronométrage sur machine chargée ; conclusion sur le surcoût du code non démontrée, reformulée depuis). Réserves acceptées par le propriétaire le 30/10/2026, dans ces mots : « Oui, j'accepte tout », en réponse à la proposition d'accepter la réserve A1 (dérive buts/tacles/pertes, réglage au ticket 22, base à consigner dans les tickets 08 et 22), la réserve A2 (coût de calcul de 1,5 à 1,9 fois, environ 3 minutes par match regardé) et l'écart au critère « machine non chargée » (mesure au repos à refaire plus tard).
- **30/10/2026, passage 3 (QC seul, code inchangé).** QC : VALIDÉ (écart au critère « machine non chargée » accepté par le propriétaire). Décision de clôture journalisée (`/valider-ticket-simulafoot`) : **VALIDÉ** (expert APPROVED_WITH_RESERVATIONS, réserves acceptées ; QC VALIDÉ), empreinte `3a4b1a6a`. Restent à faire, hors ticket : mesure du temps de calcul sur machine au repos ; A3 (zone morte et cible mobile) ; A5 (frottement du ballon indépendant du pas) ; A4 et l'essaim de presseurs au ticket 08 ; réglage des buts et des tacles au ticket 22.
