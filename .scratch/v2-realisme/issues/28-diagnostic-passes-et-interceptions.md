# 28: Diagnostic des passes et des interceptions, comparé au réel

**Chantier :** `v2-realisme` (demande du propriétaire du 19/11/2026, avant le 10i). **Priorité :** P1. **Catégorie :** mesure (aucun changement de jeu).

**Constat de départ (19/11/2026, lu dans le code) :** un adversaire qui n'a pas lu la passe (`ball.readers`) ne touche le ballon qu'à `CONTROL_RADIUS_M` (rayon du ballon plus rayon du joueur, environ 0,4 m) ; le receveur visé et les lecteurs le touchent à 1 m (`RECEIVER_REACH_M`, `READER_REACH_M`, `match._ball_contacts`). Une passe peut donc frôler un adversaire à 0,5 à 1 m sans qu'il la touche. La passe ratée est décalée de 25 à 50 % de sa longueur dans une direction au hasard (`possession._MISS_SHARE`) ; personne ne mesure aujourd'hui combien de ces passes ratées le receveur récupère quand même.

**What to build:** un script de mesure (`scripts/diag_passes_v2.py`), sans modifier le moteur, qui relève sur une série de matchs :
1. **Passes réussies** : taux par équipe et par match (passes au sol, aériennes, total), comparé au repère Ligue 1.
2. **Interceptions et pertes** par équipe et par match : interceptions (passe touchée d'abord par un adversaire), pertes de balle (toutes causes, puis par cause : passe interceptée, passe hors du terrain, conduite, contrôle raté), comparées au réel.
3. **Passes frôlées** : passes au sol dont la trajectoire passe à moins de 1 m, puis de 1 à 2 m, d'un adversaire de champ, sans qu'il touche le ballon ; avec, pour chaque cas, s'il l'avait lue (lecteur) ou non, sa vitesse et son orientation vers le ballon (07a), et le temps dont il disposait.
4. **Passes imprécises récupérées** : part des passes ratées au tirage (`pass_aim`, `miss`) que le receveur visé contrôle quand même ; puis que son équipe garde dans les 3 s.
5. **Écart moteur / écran** sur les cas suspects (passes frôlées à moins de 1 m) : position du ballon et de l'adversaire dans le moteur (pas de 0,1 s) contre leur position affichée (piste du ballon, joueurs à 2 images par seconde, courbe de Catmull-Rom du `v2-correctifs-ecran/04b`, recalculée en Python sur la même formule que `ui/src/utils/v2Spline.js`) ; part des cas où l'écart affiché diffère de plus de la marge proposée de l'écart réel.

**Règle de décision (sortie du ticket) :**
- beaucoup de passes frôlées à moins de 1 m sans contact, adversaire non lecteur et en situation de jouer le ballon : **correction de l'interception** en premier (portée des non-lecteurs, à proposer) ;
- passes frôlées surtout aériennes ou passant au-dessus d'un joueur : **`v2-hauteur-ballon/03`** ;
- part élevée de passes ratées récupérées par le receveur, taux de réussite trop haut : **23a** (erreur continue de la passe) ;
- passes précises mais contrôles trop sûrs (pertes au contrôle sous le réel) : **26a** ;
- écart d'affichage fréquent sur les cas suspects : l'impression vient du rendu, ticket écran à créer.
Le rapport classe les quatre pistes avec les chiffres qui justifient l'ordre ; le propriétaire décide.

## Critères d'acceptation

- [ ] Série de 50 matchs (graines d'audit, `scripts/measure_v2.run`), chaque indicateur avec moyenne par match et IC 95 % (`bench_series.summary`).
- [ ] Chaque indicateur 1 à 4 placé face à un repère réel sourcé, ou marqué « non trouvé ».
- [ ] Passes frôlées : comptes par tranche (< 1 m, 1 à 2 m), part des cas où l'adversaire était lecteur, part au sol / en l'air.
- [ ] Écart moteur / écran mesuré sur au moins 200 cas suspects, ou sur tous s'il y en a moins.
- [ ] Moteur inchangé : mêmes empreintes à graine fixée avant et après (le script ne fait que lire).
- [ ] Rapport dans `docs/INDICATEURS_V2.md` (nouvelle section), avec l'ordre recommandé des quatre pistes.

## Constantes (validées par le propriétaire le 19/11/2026)

| Constante | Proposée | Raison |
|---|---|---|
| Tranches des passes frôlées | < 1 m et 1 à 2 m (distance entre le centre du ballon et le centre du joueur) | demande du propriétaire ; 1 m = portée du receveur et des lecteurs |
| « Adversaire en situation de jouer le ballon » | il atteint le point le plus proche de la trajectoire avant le ballon (`arrival_time_s`) | même règle que la lecture de passe, sans délai de réaction |
| Passe imprécise | passe ratée au tirage (`miss`) | seule définition dans le code actuel (tout ou rien, 23a) |
| Fenêtre « équipe garde le ballon » | 3 s | même fenêtre que le porteur bousculé (11i) |
| Écart d'affichage significatif | 0,5 m | moitié de la portée de 1 m : en deçà, le rendu ne peut pas changer la lecture du cas |

Repères réels à confirmer (ordre de grandeur, à sourcer dans le rapport) : passes réussies en Ligue 1 80 à 85 % (indiqué par le propriétaire) ; interceptions environ 8 à 12 par équipe et par match (statistiques publiques de type Opta / FBref, définition à vérifier) ; pertes de balle : définition très variable selon les sources, à fixer dans le rapport avant la comparaison.

**Attributs :** aucun (mesure).

**Blocked by:** aucun.

**Bloque :** l'ordre entre 23a, 26a, `v2-hauteur-ballon/03` et une correction de l'interception ; passe avant le 10i (décision du propriétaire du 19/11/2026).

**Status:** livré (19/11/2026), validé expert + QC (réserves A1 à A3 acceptées par le propriétaire : « j'accepte A1, A2 et A3 » ; constantes validées le 19/11/2026, comparaison écran gardée)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement (script, courbe de l'écran en Python) | 40 min |
| Tests (moteur inchangé, script sur une scène connue) | 15 min |
| Intégration et vérifications (rapport, comparaison au réel) | 25 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : moyenne. Hypothèses : les passes, leurs ratés au tirage et les contacts sont lisibles par crochet dans le banc sans toucher au moteur ; l'écart moteur / écran est le poste le plus incertain (+ 20 min s'il faut reconstituer la piste du ballon hors de `MatchTrace`).
Temps machine, non compté : série de 50 matchs (environ 25 à 30 min sur 4 processus) ; suite complète (environ 10 min).

## Résultat (19/11/2026)

Script `scripts/diag_passes_v2.py`, garde `tests/test_diag_passes_v2.py` (courbe identique à `v2Spline.js`, match identique avec et sans crochets) ; rapport complet : `docs/INDICATEURS_V2.md`, section 55 (50 matchs). Constante de mesure ajoutée en cours de ticket, à valider : `ENDS_M` = 2 m (extrémités de la passe : presseur du passeur, marqueur du receveur), sans laquelle un tiers des passes paraissaient « frôlées ».

- Passes réussies 84,1 % ± 0,3 (repère 80-85 %) ; volume 1 227 par match (trop haut, déjà au 22a).
- Passes prises par l'adversaire 91,6 par équipe ; « passe interceptée » du moteur non comparable aux 8-9 interceptions Opta par équipe (elle compte aussi les ballons ramassés).
- **Passes frôlées sur le trajet, au sol, à moins de 1 m d'un défenseur non lecteur : 49 par match, réussies à 94 %** (portée du non-lecteur 0,4 m contre 1 m pour receveur et lecteur).
- Passes ratées au tirage : 10,7 % ; le receveur les prend quand même dans 67,5 % des cas (précises : 85,7 % pour l'équipe).
- Écart écran / moteur : médiane + 0,04 m, 1,6 % au-delà de 0,5 m : le rendu n'est pas en cause.

Ordre recommandé : correction de l'interception (non lecteurs), puis 23a, puis 26a, puis `v2-hauteur-ballon/03`. Décision du propriétaire attendue.

## Comments

- 19/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ.
  - A1 : `ENDS_M` = 2 m ajoutée en cours de ticket sans validation préalable (fonde les 49 passes par match sur le trajet).
  - A2 : point 3 partiel (vitesse, orientation, temps disponible du défenseur frôlé non relevés) ; à mesurer au début du ticket de correction de l'interception (quantiles de `reach_t`, vitesse du défenseur), pour choisir entre portée fixe et portée selon le temps de réaction.
  - A3 : taux « 94 % réussies » biaisé par construction (le défenseur qui touche est exclu) ; règle « non lecteur et en situation de jouer » : 4,1 cas par match seulement (`accel_tau_s` pénalise le défenseur immobile).
  - Réserves acceptées par le propriétaire : « j'accepte A1, A2 et A3 ».
  - Facultatif A4 (non fait) : distance en mouvement relatif comme `_contacts` ; importer `bench_series.summary`.
  - Constat hors pistes (expert) : 310 passes par match partent à moins de 1 m d'un presseur sans contre possible.
  - Durée : estimée 1 h 35 (15/40/15/25), réelle environ 1 h 35 (15/45/10/25), écart sous 30 %.
