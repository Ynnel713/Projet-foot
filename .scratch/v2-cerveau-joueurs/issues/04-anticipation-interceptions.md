# 04: Anticipation — réagir avant l'action

**What to build:** aujourd'hui un joueur ne réagit au ballon libre que lorsqu'il est déjà proche (`CHASE_RADIUS_M`). Anticipation le fait partir plus tôt vers l'endroit où le ballon VA arriver (passe adverse, rebond, ballon perdu), et permet d'intercepter une passe sur sa trajectoire, ce qui n'existe pas encore (guide, Anticipation).

**Blocked by:** None.

**Status:** ready-for-agent

- [ ] Les interceptions de passe existent, et un joueur à Anticipation haute en réussit mesurablement plus
- [ ] Sur ballon libre, un joueur à Anticipation haute court vers le point d'arrivée du ballon, pas vers sa position actuelle
- [ ] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [ ] Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [ ] Joueur sans cet attribut : repli neutre (60), sans erreur
- [ ] Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [ ] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [ ] Suite V2 verte ; V1 inchangée
