# 02g: Qui fait un appel, et quand

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les appels doivent être rares, utiles et différenciés). **Catégorie :** décision.

**Constat vérifié :** avant 02f, tous les joueurs de champ appellent ; les tickets livrés `v2-cerveau-joueurs/03` (Off the Ball) et `v2-collectif/16` (appels complémentaires) règlent OÙ appeler, pas QUI appelle.

**What to build:** Choisir les appelants à chaque décision du porteur : rôle autorisé à appeler dans cette situation (avant-centre de profondeur, ailier, latéral offensif, relayeur), espace exploitable par une passe du porteur, nombre maximal d'appels simultanés par situation de jeu. Off the Ball règle le moment (déclenchement plus ou moins tôt) ; aucun autre attribut.

**Attributs :** Off the Ball (moment de l'appel)

**Lien avec l'existant :** complète les tickets livrés `v2-cerveau-joueurs/03` et `v2-collectif/16`, sans les modifier.

**Blocked by:** 02f (Tenir sa position en possession).

**Bloque :** 02h, 13c, 13d.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** (relevée à **2 h 30** le 06/11/2026 : réserves A1 à A3 du 02f ajoutées ; ticket gardé entier sur décision du propriétaire) |

Confiance : moyenne. Hypothèses : la règle provisoire du 02f est remplacée, pas superposée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** dernier tiers : au plus N appels simultanés ; un défenseur central n'appelle pas en possession installée
- **Comportementaux (profils comparés) :** Off the Ball 99 contre 11 : appels déclenchés plus tôt, à nombre égal
- **Statistiques (séries de matchs) :** 50 matchs : appels par joueur et par poste (repère 5,5 à 19,2 selon le poste, à confirmer au 01c)

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Nombre d'appels simultanés borné par situation (valeurs validées)
- [x] Effet d'Off the Ball mesurable sur le moment, pas sur le volume
- [x] Appels par poste rapportés ; l'ordre réel (défenseurs centraux les moins nombreux) est respecté, les volumes restent très au-dessus du repère (voir commentaire, non corrigé ici)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 06/11/2026 (réserves de l'expert au 02f, à traiter ici) : **A1** la contre-attaque qui atteint le dernier tiers garde ses appels (`DERNIER_TIERS` prime sur `TRANSITION_OFFENSIVE`) ; **A2** hystérésis : un appelant garde son appel tant que son espace n'est pas atteint, pas d'alternance APPEL / TENIR ; mesurer le taux d'alternance par joueur ; **A3** le joueur désigné par `ball.plan` reste appelant. Test de scène pour chacune. La règle provisoire `PROVISIONAL_RUNNERS` / `HOLD_SITUATIONS` de `cerveau.py` est remplacée, pas superposée.
- 06/11/2026 : **Critères chiffrés posés avant le code** : (1) possession installée au plus 2 appelants, dernier tiers et transition offensive au plus 3, choisis par rôle (projection avant intermédiaire) puis proximité du ballon ; (2) défenseur central, sentinelle, récupérateur, regista, latéral défensif n'appellent jamais en possession ; (3) A1 (contre-attaque au dernier tiers : 3 appelants au lieu de 2), A2 (pas d'alternance), A3 (plan de passe) ; (4) Off the Ball : délai avant l'appel de 0,3 s (99) à 1,0 s (11) ; (5) 50 matchs, tirs et solutions de passe sans chute non expliquée ; deux exécutions, même empreinte.
- 06/11/2026 : **Réalisé** (`cerveau.py` : `CALLER_CAP`, `CALLER_ROLES`, `CALLER_IF_FREE`, `_call_rank`, `_runs_or_holds` remplacent `PROVISIONAL_RUNNERS` / `HOLD_SITUATIONS` ; `off_ball.call_delay_s` ; `BallState.callers`). Constantes proposées par Claude et validées par délégation (règle permanente du 05/11/2026), chiffres réels non trouvés sauf le repère de 5,5 à 19,2 appels par 90 min (CIES 2023). Précisions décidées en cours de route, toutes mesurées : (a) hystérésis stricte : un appelant choisi garde sa place, sans nouveau délai, tant qu'il est éligible (`CALLER_MEMORY_S` = 1 s, `CALLER_BEHIND_M` = 3 m derrière le ballon avant éviction) ; sans elle, 925 passages APPEL / TENIR en 10 min contre 297 avec elle (diagnostic, 1 match) ; (b) situation perçue en retard (« défense placée » ou « transition défensive » alors que l'équipe a le ballon) : règle de la transition offensive, ce qui supprime 250 passages de 401 de moins de 1,5 s ; (c) le délai d'Off the Ball ne joue qu'en possession installée et au dernier tiers (la contre-attaque reste réglée par le délai de réaction, ticket 11) ; (d) **non réalisé** : le filtre « espace exploitable, passe à 0,7 ou plus » comme condition de sélection (coût : un calcul de passe par candidat à chaque tick) ; le seuil de 0,7 reste appliqué au choix de l'espace par `choose_space`, comme avant. A1 : la contre-attaque au dernier tiers garde 3 appelants (cap du dernier tiers), sans prolonger le mode contre-attaque du ticket 11 (qui s'arrête au dernier tiers par décision). Le garde-fou de rayon des attributs a imposé de lire Off the Ball dans `off_ball.py` (`player_call_delay_s`).
- Mesure 50 matchs (graine d'audit 20260923, `scripts/bench_series.py`, 4 processus ; avant = 02f, `.scratch/v2-realisme/mesures/02f-apres.json`, après = `02g-apres.json`) : appels par joueur et par 90 min 48,5 → 45,4 (−6 %) ; par poste : défenseur central 22,3 → 19,8, latéraux 28,5 / 27,6 → 27,5 / 25,0, milieu défensif 48,0 → 41,2, milieu central 53,9 → 47,0, milieu offensif 88,0 → 80,7, ailiers 55,7 / 55,1 → 53,5 / 54,2, avant-centre 97,2 → 99,1. km par joueur de champ 15,8 → 14,6 (−7 %). Tirs par équipe 25,06 → 25,55, buts par match 3,46 → 3,88 (écart-type d'un match 2,1 : +0,42 est dans le bruit, environ 1,4 écart-type de la moyenne), corners 11,6 → 12,5, hors-jeu 1,24 → 1,00, passes 1 025 → 1 044. Solutions de passe ouvertes 2,106 → 2,105, faciles 1,678 → 1,672 : pas de chute. Alternances APPEL / TENIR : 136 par joueur et par match (un passage environ toutes les 40 s) ; diagnostic d'un match de 10 minutes : 297 passages dont 24 % de moins de 1,5 s. Le 02f n'a pas mesuré ce taux : pas d'avant chiffré, seulement le diagnostic de 925 passages avant le correctif (a).
- **Écart au réel, à dire sans l'arrondir** : les volumes d'appels restent 2 à 10 fois au-dessus du repère (5,5 à 19,2). Le banc compte comme appel toute course de plus de 0,7 s à plus de 15 km/h d'un coéquipier du porteur, quel que soit le rôle de l'intention : un joueur en `TENIR` qui rejoint sa place à pleine vitesse est compté. Hypothèse non vérifiée (aucune mesure de la part de ces courses dans ce ticket) : le gros des appels mesurés vient du replacement à pleine intensité, qui relève de 12d (intensité selon le rôle) et de 09 (occupation), pas de la sélection. L'ordre des postes est en revanche cohérent (défenseurs centraux les moins nombreux, milieux offensifs et avant-centres les plus nombreux).
- Déterminisme : deux exécutions à graine fixée (15 minutes, graine 20260923), même empreinte `2c219a7d1bd244a0`. Tests : 12 nouveaux ou réécrits dans `tests/test_v2engine_cerveau.py` (plafonds par situation et situation perçue en retard, rôles exclus, latéral et côté du ballon, délai d'Off the Ball de 99 et de 11, hystérésis et appelant en course, plan de passe A3, passe en vol, miroir de l'équipe visiteuse, mémoire de l'appelant) ; test d'équilibre de Teamwork adapté (le joueur testé est un box to box : un défenseur central n'appelle plus en possession). Suite complète : 2 464 passés, 14 désélectionnés, 13 min 32 s (attendu 2 458 + 6 tests nets ; un premier passage avait relevé 1 échec du garde-fou de rayon des attributs, corrigé en déplaçant la lecture d'Off the Ball dans `off_ball.py`).
- Durée : estimée 2 h 30, réelle environ 2 h 45 (non chronométrée), écart environ + 10 % : deux boucles de diagnostic de l'alternance (mémoire de l'appelant, situation perçue en retard) non prévues, compensées par une sélection écrite d'un seul jet. Temps machine, hors total : suite complète 28 min (deux fois), série de 50 matchs environ 25 min en parallèle de la suite.
- 06/11/2026 : **Clôture.** Expert `APPROVED_WITH_RESERVATIONS` (empreinte `58a59dd6`), QC `VALIDÉ`, clôture `VALIDÉ` (journal). Aucune anomalie bloquante. Réserves acceptées d'office, règle permanente du propriétaire (03/11/2026 : « Considère que je valide automatiquement toutes les reco d'experts », étendue le 05/11/2026 à « toutes tes recommandations et celles des experts ») ; aucune acceptation réserve par réserve dans cette conversation. **A1** : le banc compte toute course rapide d'un coéquipier du porteur, quel que soit son rôle (un défenseur central, jamais `APPEL`, affiche 19,8 appels par 90 min) : « −6 % d'appels » et « ordre des postes » ne prouvent presque rien sur la sélection, dont le plafond n'est prouvé que par les tests de scène ; à traiter au 02h (nombre d'épisodes `APPEL` par poste et par 90 min, maximum d'appelants simultanés par équipe et par situation, via `Collector.on_role`) avant de s'appuyer sur les volumes (12d, 09). **A2** : les 136 alternances par joueur et par match mélangent les possessions successives ; à traiter au 02h (compter les passages à l'intérieur d'une possession, part de moins de 1,5 s, à comparer aux 24 % du diagnostic). **A3** : le filtre « espace exploitable par une passe du porteur » de « What to build » n'est pas réalisé ; reporté au 02h pour mesure puis, si l'appelant retenu est souvent couvert, ticket dédié après lui. Facultatifs : A4 (le latéral côté ballon n'appelle pas, à regarder à l'écran), A5 (profil Off the Ball 99 contre 11 en série à nombre d'appelants égal), A6 (`data/joueurs.xlsx` modifié dans l'arbre, à ne pas indexer). À surveiller : une-deux 6,26 → 5,39 (environ 1,7 écart-type de la différence), contre-attaque limitée à 3 appelants.
- QC : `VALIDÉ`. Son seul point non tranché, une dépendance possible à l'ordre d'évaluation des joueurs (la sélection met à jour `ball.callers` joueur après joueur dans un même tick), a été vérifié hors dépôt après coup : 300 scènes aléatoires (plafond, rôles, mémoire d'appelants) évaluées dans 12 ordres différents chacune, 0 scène dont le résultat change. Script de vérification dans le répertoire temporaire de la session, non versionné.
