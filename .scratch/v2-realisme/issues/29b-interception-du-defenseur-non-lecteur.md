# 29b: Interception par un défenseur qui n'a pas lu la passe

**Chantier :** `v2-realisme` (suite du ticket 28 ; ordre validé par le propriétaire le 19/11/2026 : cette correction, puis 23a, 26a, `v2-hauteur-ballon/03`). **Priorité :** P1. **Catégorie :** physique du contact.

**Constat vérifié (19/11/2026) :** `match._ball_contacts` donne au receveur visé et aux lecteurs de la passe (`ball.readers`) une portée de 1 m (`RECEIVER_REACH_M`, `READER_REACH_M`), à tous les autres `CONTROL_RADIUS_M` (rayon du ballon plus celui du joueur, 0,41 m). Un défenseur placé sur la trajectoire sans avoir lu la passe la laisse passer entre 0,41 et 1 m : 49 passes au sol par match (ticket 28, `docs/INDICATEURS_V2.md` section 55). Au réel, un joueur tend la jambe vers un ballon qui passe à sa portée s'il a le temps de réagir et le voit.

**What to build:** sur une passe au sol, un adversaire de champ non lecteur peut toucher le ballon à une portée de jambe tendue, au lieu de `CONTROL_RADIUS_M`, quand :
- le ballon est parti depuis au moins un temps de réaction minimal (il a vu partir la passe) ;
- il est tourné vers le ballon (cap `facing`, 07a), sinon il garde `CONTROL_RADIUS_M`.
Le contact passe ensuite par le mécanisme existant (`attempt_control` : contrôle, ou ballon dévié) ; pas de nouveau tirage, pas de nouveau flux. La forme exacte (portée fixe ou selon le temps disponible, part de l'orientation) est arrêtée sur les chiffres du 29a.

**Constantes à proposer avant le code (proposition après le 29a, `docs/INDICATEURS_V2.md` section 56) :**

| Constante | Indicatif | Raison |
|---|---|---|
| Portée du non-lecteur | 0,8 m | jambe tendue sans préparation, sous le 1 m du joueur qui attend le ballon (`RECEIVER_REACH_M`) ; la portée pèse le plus (1 m : + 47 % de passes touchables, 72 contre 49 par match) ; donnée réelle : non trouvée |
| Temps de réaction minimal | 0,25 s | réaction visuelle simple d'un athlète, environ 0,2 à 0,25 s (à sourcer) ; neutralise le presseur au départ (0,1 passe touchable par match) ; 0,20 à 0,30 s ne change le trajet que de 21 à 19 |
| Orientation | cap à moins de 90° de la direction du ballon | il voit le ballon venir (07a) ; retire environ 9 % des passes |
| Partie de la passe | toute la passe au sol | une seule loi physique ; touche plus l'arrivée (marqueur du receveur, 30 passes par match) que le trajet (20) ; au moins 49 passes touchables par match en tout : choix à valider |

**Attributs :** aucun nouveau. Si le temps de réaction dépend d'une note, Anticipation, par le registre des contextes (ADR 0002), contexte et poids à proposer ; sinon, aucun.

**Critères d'acceptation (cibles à confirmer au 29a) :**
- [x] Passes au sol frôlées à moins de 1 m sur le trajet, non lecteur, sans contact (distance du moteur, 29a) : 36 par match avant ; cible proposée 25 au plus (toutes les passes touchées ne sont pas contrôlées), sur 100 matchs appariés. **Mesuré : 35,8 → 17,0 ± 1,4.**
- [x] Réussite des passes dans le jeu : mesurée avant / après ; cible proposée au-dessus de 80 % ; sinon, écart noté pour le `v2-collectif/22a`, sans recalage ici. **Mesuré : 84,07 % → 81,40 % (− 2,67 ± 0,26 point).**
- [x] Buts, tirs, pertes de balle, passes par match : écart apparié avec IC 95 % ; tout écart significatif expliqué. **Voir `docs/INDICATEURS_V2.md` section 57** : passes prises par l'adversaire + 39,8 ± 3,8, buts − 0,75 ± 0,57, tirs − 3,3 ± 1,4, passes + 31 ± 13 (plus de pertes : possessions plus courtes, moins d'attaques au bout).
- [x] Tests : scène où une passe passe à 0,7 m d'un défenseur tourné vers le ballon (touchée), du même défenseur dos au ballon (non touchée), et dans les 0,25 premières secondes (non touchée) ; passe aérienne inchangée. **`tests/test_v2engine_non_lecteur.py`, 8 tests.**
- [x] Déterminisme : mêmes empreintes sur deux exécutions à graine fixée. **Match 3, 15 min, deux exécutions : empreinte des comptes `76b590189bc84a64` deux fois.**

**Blocked by:** 29a.

**Bloque :** `v2-realisme/23a` (ordre du propriétaire : la sanction physique d'une passe déviée change ici).

**Status:** livré (20/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications (100 matchs appariés, rapport) | 30 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : la règle tient dans `_ball_contacts` sans toucher au contrôle ; l'effet sur la réussite des passes reste dans un ordre de grandeur que le 22a recalera.
Temps machine, non compté : 100 matchs appariés (environ 1 h sur 4 processus) ; suite complète (environ 15 min).

## Comments

- 19/11/2026, constantes validées par le propriétaire (portée 0,8 m, réaction 0,25 s, cap < 90°, toute la passe au sol) : `match.NON_READER_REACH_M`, `NON_READER_REACTION_S` ; départ de la passe gardé dans `BallState.pass_started_s` (passe jouée et remise en jeu). Le gardien et les coéquipiers du passeur ne sont pas concernés ; une passe sans instant de départ garde l'ancienne règle.
- 20/11/2026, mesure : 100 matchs appariés (graines 0 à 99, `scripts/diag_passes_v2.py` par lots de 10, mémoire bornée par `max_tasks_per_child=1`, garde-fous buts et tirs ajoutés au script) ; suite complète 3 455 passés (3 447 + 8), 0 ignoré, 14 désélectionnés. Une première série de 100 matchs a été perdue au redémarrage du conteneur.

- 20/11/2026, clôture : expert APPROVED (empreinte 6f7c9749), QC VALIDÉ, clôture VALIDÉ. Améliorations facultatives de l'expert, non bloquantes : A1 (réaction jugée au début du pas, seuil réel 0,3 s au pas de 0,1 s ; effet 49,2 → 47,8 passes touchables), A2 (orientation jugée sur la position en fin de pas), A3 (`pass_started_s` jamais remis à `None`, sans effet). Points à surveiller : buts et tirs au `v2-collectif/22a`, réussite à 81,4 % proche du plancher ; 30,8 passes par match frôlées à l'arrivée.

## Durée réelle

Environ 1 h 55 de travail effectif pour 1 h 40 estimées (+ 15 %) : analyse 15 min, développement 30 min, tests 25 min, intégration et vérifications 45 min (série perdue au redémarrage relancée par lots, rapport). Durée estimée à l'horloge de la session hors attentes machine, non chronométrée ; temps machine hors total : deux fois 100 matchs appariés (2 h 40 perdues, puis 1 h 50), suite complète 14 min 40.

