# 02: Vision — voir les passes que les autres ne voient pas

**What to build:** aujourd'hui `possession.choose_pass_target` traite tous les coéquipiers de la même façon. Vision détermine QUELLES passes le porteur envisage : un 90 voit la passe longue entre les lignes et le changement de jeu, un 30 ne voit que les partenaires proches et évidents (guide : Vision voit la passe, Passing la réussit, Decisions la choisit).

**Blocked by:** 01 (le choix entre options doit exister).

**Status:** ready-for-agent

- [ ] Un porteur à Vision haute joue mesurablement plus de passes vers l'avant et de passes longues qu'un porteur à Vision basse, à situation égale
- [ ] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [ ] Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [ ] Joueur sans cet attribut : repli neutre (60), sans erreur
- [ ] Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [ ] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [ ] Suite V2 verte ; V1 inchangée
