# 05: Flair — options risquées et imprévisibles

**What to build:** Flair est une TENDANCE, pas une qualité (guide : « NOTE HAUTE / BASSE ») : un 90 tente plus souvent l'option inattendue (passe risquée, dribble au lieu de la passe simple), qui peut déstabiliser une défense, au prix de plus de pertes de balle dans les zones dangereuses. Un 30 joue simple et sûr. Se branche sur le choix d'options du ticket 01.

**Blocked by:** 01.

**Status:** ready-for-agent

- [ ] Un joueur à Flair haut tente mesurablement plus d'options risquées ET perd plus de ballons qu'un joueur à Flair bas : les deux effets doivent apparaître
- [ ] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [ ] Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [ ] Joueur sans cet attribut : repli neutre (60), sans erreur
- [ ] Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [ ] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [ ] Suite V2 verte ; V1 inchangée
