# 03: Off the Ball — appels et démarquage

**What to build:** aujourd'hui un joueur sans ballon retourne à sa position de formation (`home_target`), ou court vers le ballon s'il est proche. Off the Ball fait bouger les coéquipiers du porteur vers des espaces libres : démarquage entre les lignes, appel en profondeur dans le dos de la défense, arrivée dans la surface (guide, Off the Ball). Un 30 reste statique et facile à marquer.

**Blocked by:** None (indépendant de 01 : ne touche que le déplacement sans ballon).

**Status:** ready-for-agent

- [ ] Quand son équipe a le ballon, un joueur à Off the Ball haut est mesurablement plus loin de l'adversaire le plus proche qu'un joueur à note basse
- [ ] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [ ] Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [ ] Joueur sans cet attribut : repli neutre (60), sans erreur
- [ ] Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [ ] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [ ] Suite V2 verte ; V1 inchangée
