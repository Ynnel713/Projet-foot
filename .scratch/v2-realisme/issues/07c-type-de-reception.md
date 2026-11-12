# 07c: Réception de face, de profil ou dos au jeu

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** la réception ne tient compte que de la vitesse du ballon et de la pression (`possession.control_difficulty`) ; pendant la réception le joueur avance toujours vers le but adverse (`cerveau.py:151-153`).

**What to build:** Classer chaque réception selon le cap du receveur, la direction d'arrivée du ballon et la direction du but adverse : de face, de profil (ouvert), dos au jeu. Le type est tracé ; le receveur qui a le temps se met de profil avant l'arrivée du ballon (rotation du 07a).

**Hors de ce ticket :** effet sur le temps de contrôle (07d).

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 04i, 07d, 07g, 08c, `v2-collectif/31`.

**Status:** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : seuils d'angle : valeurs proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** trois scènes (ballon venant de derrière, de côté, de face) : trois types attendus
- **Statistiques (séries de matchs) :** 20 matchs : répartition des types par poste

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : `reception.FACE_MAX_DEG` 60°, `BACK_MIN_DEG` 120° (trois secteurs égaux), `OPEN_CONE_DEG` 90° (ballon gardé dans le demi-plan avant) ; réel non trouvé ; validées par délégation (voir Comments)
- [x] Type de réception tracé : `trace.receptions` (`ReceptionEvent` : type, angle cap / but, angle cap / ballon, origine, receveur visé), à chaque contrôle réussi
- [x] Répartition par poste rapportée : 20 matchs (`.scratch/v2-realisme/mesures/07c-receptions.txt`)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`07c-det1`, `07c-det2`) ; jeu identique au 18j hors temps de calcul
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (voir Comments)

## Comments

**12/11/2026, reprise du 07a (réserve facultative A1 de l'expert).** Le cap vise le sens de course au-dessus de `movement.FACING_RUN_SPEED_MPS` (19,8 km/h) et le ballon en dessous, sans hystérésis : quand ce ticket fera lire le cap au jeu, prévoir une bande de quelques dixièmes de m/s ou une pondération continue entre les deux directions (test : vitesse oscillant de ± 0,1 m/s autour du seuil, variation de cap bornée).

**12/11/2026, lancement.** Estimation annoncée : 1 h 50, confiance élevée. Délégation du propriétaire (« enchaine les les uns après les autres. Je valide automatiquement toutes tes recommandations et les conseils d'experts ainsi que les commits si les conditions le permettent donc ne me sollicite pas »).

**12/11/2026, constantes (recommandées et validées par délégation).** Classement par l'angle entre le cap du receveur et la direction du but adverse : de face jusqu'à 60°, de profil de 60 à 120°, dos au jeu au-delà (trois secteurs égaux ; seuils réels non trouvés). Cap ouvert du receveur visé d'une passe en vol : la direction la plus proche du but adverse qui garde le ballon à 90° au plus de son cap (demi-plan avant) ; ballon pile à l'opposé du but, il s'ouvre du côté de son cap. « Il a le temps » n'est pas une constante : la rotation bornée du 07a (360°/s) décide s'il s'ouvre avant l'arrivée du ballon. Au-dessus de 19,8 km/h, il regarde toujours le sens de course (07a).

**12/11/2026, implémentation.** Module `v2engine/reception.py` (`reception_type`, `open_facing`, `attacking_goal`, `facing_to_goal_deg`) ; `match._step_player` : cap ouvert pour le receveur visé ; `match._step_ball` : `ReceptionEvent` à chaque contrôle réussi (`trace.receptions`) ; angle d'arrivée du ballon `match._ball_facing_deg`. Aucun module ne lit le type (07d le branchera). L'hystérésis du seuil de course (réserve facultative A1 du 07a) reste sans objet tant que le cap ne joue pas : à reprendre au 07d.

**12/11/2026, mesures.**
- Jeu identique au 18j à graine fixée (`measure_v2 2`, hors temps de calcul) ; déterminisme sur deux exécutions ; temps de calcul 63,0 s par match (62,8 au 07a, 60,2 au 18j).
- Répartition (20 matchs, graines d'audit 0 à 19, 19 917 réceptions ; `07c-receptions.py`, sortie `07c-receptions.txt`) : passes reçues par le receveur visé (804 par match) de face 87,4 %, de profil 12,1 %, dos au jeu 0,5 % ; autres réceptions (récupération, rebond ; 192 par match) 27,0 / 33,1 / 39,9 %. Par poste (passes reçues) : défenseurs et gardien environ 95 % de face ; MC 88,9 / 10,4 / 0,8 ; MOC 82,1 / 17,6 / 0,3 ; ailiers environ 93 / 6 / 0,5 ; BU 69,7 / 29,9 / 0,4.
- Lecture : le receveur visé a presque toujours le temps de s'ouvrir (un quart de tour en 0,25 s) ; le dos au jeu réel de l'avant-centre vient surtout d'un marqueur collé dans son dos qui l'empêche de se tourner, mécanisme absent ici (protection du ballon `04i`, scan avant la réception `08c`, temps de contrôle `07d`). Repère réel de la répartition : non trouvé. Le vocabulaire d'origine (« passe en retrait » : toute passe qui recule, 497 par match) vient du ticket `v2-collectif/28b`.
- Tests : 12 ajoutés (`tests/test_v2engine_reception.py` : trois arrivées du ballon et trois types, bornes des secteurs, cap ouvert, s'ouvrir avec ou sans le temps, trace d'un contrôle, contrôle raté non tracé, match simulé).
- Suite complète : 2 797 passés, 0 ignoré, 14 désélectionnés (2 785 + 12 ; `.scratch/v2-realisme/mesures/07c-suite.txt`) ; `CLAUDE.md` mis à jour.

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. Réserves :
- A1 [réserve] : le type ne dépend que de l'angle cap / but ; un joueur tourné vers le but qui reçoit un ballon arrivant dans son dos (réception non visée, `ball_facing_deg` proche de 180°) est classé « de face » alors qu'il contrôle à l'aveugle. Condition : le 07d combine le type et `ball_facing_deg` avant de lire le type.
- A2 [facultatif] : `_ball_facing_deg` vaut 0° pour un ballon arrêté ; une valeur neutre serait plus juste pour les récupérations.
- A3 [facultatif] : hystérésis du seuil de course (A1 du 07a) à reprendre impérativement au 07d.

**12/11/2026, décision par délégation du propriétaire** (« Je valide automatiquement toutes tes recommandations et les conseils d'experts ») : A1 acceptée, inscrite au 07d avec A2 et A3 (code inchangé, le type n'est lu par aucun module).

**12/11/2026, clôture.** QC : VALIDÉ. Clôture : VALIDÉ (expert APPROVED_WITH_RESERVATIONS, réserve A1 acceptée par délégation, reportée au 07d avec A2 et A3).

**Durée.** Estimée 1 h 50. Réelle environ 1 h 20, non chronométrée (analyse 15 min, développement 30 min, tests 20 min, intégration et vérifications 15 min) : − 27 %. Temps machine hors total : 2 x 2 matchs, 20 matchs de réceptions (10 min), suite complète (7 min).
