# 03: Off the Ball — appels et démarquage

**What to build:** aujourd'hui un joueur sans ballon retourne à sa position de formation (`home_target`), ou court vers le ballon s'il est proche. Off the Ball fait bouger les coéquipiers du porteur vers des espaces libres : démarquage entre les lignes, appel en profondeur dans le dos de la défense, arrivée dans la surface (guide, Off the Ball). Un 30 reste statique et facile à marquer.

**Blocked by:** None (indépendant de 01 : ne touche que le déplacement sans ballon).

**Status:** livré (24/10/2026), validé QC — critère en match reporté à la phase 6 (décision du propriétaire)

- [ ] (REPORTÉ en phase 6, voir plus bas) Quand son équipe a le ballon, un joueur à Off the Ball haut est mesurablement plus loin de l'adversaire le plus proche qu'un joueur à note basse
- [x] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [x] (sans objet : pas de poids par poste dans ce ticket) Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [x] Joueur sans cet attribut : repli neutre (60), sans erreur
- [ ] (REPORTÉ en phase 6) Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [x] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [x] Suite V2 verte ; V1 inchangée

**Constantes (validées 24/10/2026)** : les coéquipiers du porteur ne vont plus au ballon ; recherche d'espace toutes les 1 s ; rayon 99 -> 15 m, 55 -> 8 m, 11 -> 2 m ; jusqu'à 2/3 du rayon vers l'avant, 1/3 en arrière ; meilleur espace choisi 99 -> 95 %, 55 -> 70 %, 11 -> 45 %. Critère : à 90, au moins 30 % plus loin de l'adversaire le plus proche qu'à 30.

**Mesures (24/10/2026, `scripts/measure_v2_decisions.py`)** : sur situation fixée avec adversaires proches, critère atteint (test `test_high_off_the_ball_finds_more_space_than_low`). En match, aucun écart : 20,9 m (Off the Ball 90) contre 21,6 m (30). Cause : sans défense organisée (marquage, bloc), les défenseurs restent à leur place et tout le monde a déjà plus de 20 m d'espace. **Critère en match reporté à la phase 6 (défense organisée)**, par décision du propriétaire : à remesurer une fois le marquage branché. Calibration inchangée et toujours dans les cibles : 10,8 tirs par équipe, 2,83 buts par match (6 matchs).
