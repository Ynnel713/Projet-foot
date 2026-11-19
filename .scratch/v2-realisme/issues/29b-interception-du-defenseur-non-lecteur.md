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
- [ ] Passes au sol frôlées à moins de 1 m sur le trajet, non lecteur, sans contact (distance du moteur, 29a) : 36 par match avant ; cible proposée 25 au plus (toutes les passes touchées ne sont pas contrôlées), sur 100 matchs appariés.
- [ ] Réussite des passes dans le jeu : mesurée avant / après ; cible proposée au-dessus de 80 % ; sinon, écart noté pour le `v2-collectif/22a`, sans recalage ici.
- [ ] Buts, tirs, pertes de balle, passes par match : écart apparié avec IC 95 % ; tout écart significatif expliqué.
- [ ] Tests : scène où une passe passe à 0,7 m d'un défenseur tourné vers le ballon (touchée), du même défenseur dos au ballon (non touchée), et dans les 0,25 premières secondes (non touchée) ; passe aérienne inchangée.
- [ ] Déterminisme : mêmes empreintes sur deux exécutions à graine fixée.

**Blocked by:** 29a.

**Bloque :** `v2-realisme/23a` (ordre du propriétaire : la sanction physique d'une passe déviée change ici).

**Status:** à faire (constantes à proposer avant le code, après le 29a)

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
