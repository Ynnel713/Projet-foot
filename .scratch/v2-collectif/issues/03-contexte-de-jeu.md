# 03: Reconnaître la situation de jeu

**What to build:** Chaque équipe identifie à chaque instant le **type de problème tactique** auquel elle fait face : possession installée, défense placée, transition offensive, transition défensive, dernier tiers (la surface y est comprise jusqu'à la phase 7 ; les coups de pied arrêtés viennent en phase 8). Pas de séquence scriptée par situation : la situation oriente les rôles et les priorités, puis les joueurs choisissent leur réponse.

**Attributs :** Aucun pour la situation d'équipe (lecture collective) ; Anticipation règle le délai de réaction de chaque joueur (rayon de la carte : « délai de réaction »). Concentration (trous d'attention) n'est pas branchée ici : ce serait un double comptage du délai (règle R1) ; elle vient au ticket 09.

**Blocked by:** 02.

**Status:** livré (26/10/2026), validé QC

- [x] La situation de chaque équipe est calculée et enregistrée dans la trace
- [x] Sur scénario, une perte de balle fait basculer en transition défensive en moins d'un temps de réaction réaliste (chiffre à sourcer)
- [x] Les seuils de bascule entre situations sont proposés et validés avant le code
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Réalisé (26/10/2026)

- `v2engine/situation.py` : situation de chaque équipe (possession installée, défense placée, transition offensive, transition défensive, dernier tiers). Seuils validés : transition pendant 8 s après un changement de possession ; dernier tiers au-delà de 70 m de son but, prioritaire sur la transition offensive ; l'engagement après un but n'est pas une transition.
- Délai de perception par joueur (`anticipation.reaction_delay_s`) : 99 -> 0,4 s, 55 -> 0,7 s, 11 -> 1,0 s (réf. Unravel Sports, 0,7 s). La situation perçue est portée par l'intention.
- Trace : changements de situation et délais de réaction. API : situations par équipe, délai de réaction par joueur (la situation perçue se déduit côté écran, pour ne pas alourdir les segments). Réponse API : 15,9 Mo (15,1 avant). Écran V2 : situation des deux équipes sous le score, situation perçue du joueur sélectionné (vérifié dans le navigateur).
- Banc de mesure : découpage par situation et part du temps par situation. Sur 20 matchs : possession installée 29 %, défense placée 30 %, transition défensive 20 %, transition offensive 19 %, dernier tiers 2 % (valeur réelle comparable : non trouvée).
- L'engagement après un but n'est pas une transition, même quand l'équipe qui a marqué reprend le ballon la première (l'engagement n'est pas encore modélisé : cas mesuré 5 fois sur 6 par la revue).
- Jeu inchangé : empreintes de 3 matchs et mesure de 20 matchs identiques au commit 4205ab9. Temps de calcul : +3 à 6 % (34,0 s contre 32,1-33,1 s, meilleur de 2), après suppression d'une copie de l'intention à chaque tick.
- Taille de la réponse API : la liste des situations pèse environ 0,1 Mo ; l'écart 15,1 -> 15,9 Mo mesuré plus tôt compare deux matchs différents (le tacle a changé au ticket 18).
