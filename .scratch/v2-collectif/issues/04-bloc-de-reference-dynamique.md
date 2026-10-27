# 04: Bloc de référence dynamique

**What to build:** Remplacer la place de formation fixe par une **position de référence** qui dépend du ballon, de la situation (ticket 03), du rôle et des partenaires. Le bloc coulisse vers le côté du ballon, réduit les espaces entre joueurs et protège les zones dangereuses ; le côté opposé se resserre sans perdre toute capacité à défendre un renversement. Teamwork : tenir et reprendre sa place dans ce bloc (partie « sans ballon » du ticket v2-cerveau-joueurs/06).

**Attributs :** Teamwork, Positioning.

**Blocked by:** 03.

**Status:** livré (27/10/2026)

**Point de vigilance :** un décalage simple du bloc (`BLOCK_SHIFT`, 50 % en longueur, 30 % en largeur) a été codé dans le travail sauvegardé dans `.scratch/v2-collectif/wip-socle-02-intensite.patch` du ticket socle 02. Le reprendre ici comme point de départ, pas comme solution.

- [x] Le centre de l'équipe suit le ballon, surtout dans la longueur (Frencken et al. 2012) : pente 0,54 en longueur contre 0,40 en largeur (avant : 0,15 et 0,16). Distances entre lignes : milieu-attaque 23,3 → 18,8 m, défense-milieu inchangée (16,7 m) ; réel 13,3 et 10,2 m, écart laissé aux tickets 07 et 22
- [x] Côté opposé resserré mais présent : un renversement ne trouve pas un côté vide (test `test_the_far_side_tightens_but_stays_occupied`)
- [ ] Une équipe à Teamwork élevé reste mesurablement plus compacte qu'une équipe à Teamwork bas (critère du ticket cerveau 06) : **reporté au ticket 07** (décision du propriétaire, 27/10/2026). Mesuré : stretch index 19,85 contre 19,94 m (0,5 %, seuil proposé 10 %) ; Teamwork ne règle que les joueurs qui se replacent, pas encore ceux qui vont au ballon
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Livraison (27/10/2026)

- `v2engine/bloc.py` : position de référence dans le bloc (forme selon la situation perçue, suivi du ballon, montée avec ballon), Positioning (erreur de placement sans ballon), Teamwork (écart toléré, puis retour jusqu'à sa place). Les appels partent de la place dans le bloc.
- Montée du bloc avec ballon : validée à 15 m « ajustable par mesure », retenue à **8 m** (20 matchs ; 5 / 8 / 11 / 15 m : 8,5 / 13,7 / 18,9 / 25,7 tirs par équipe).
- Positioning 99 contre 11 : écart-type de la distance défense-milieu 4,68 contre 5,01 m (lignes plus régulières).
- Mesure sur 20 matchs (avant → après) : passes 15,1 → 16,8 par minute ; passes chez l'adversaire 24,6 → 30,6 % ; tirs 11,1 → 13,7 par équipe ; buts 3,45 → 3,0 ; **tacles 39,5 → 52,0** (au-dessus de la fourchette 30-40, blocs plus serrés autour du ballon : à suivre aux tickets 07 et 22) ; bloc sans ballon 45,0 × 35,9 → 40,9 × 41,2 m ; compacité autour du ballon 19,6 → 13,7 m ; km par joueur 24,3 → 25,8.
- La pente de suivi mélange les deux équipes, avec et sans ballon, et les joueurs qui chassent le ballon : c'est un indicateur de comportement, pas une vérification de `BLOCK_SHIFT`.
- Règle R1 : Anticipation n'a toujours qu'un effet (délai de perception de la situation) ; ce délai règle désormais aussi le moment où la forme du bloc change, sans nouvel effet.
