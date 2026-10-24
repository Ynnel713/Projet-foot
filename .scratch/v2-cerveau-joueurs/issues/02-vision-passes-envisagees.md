# 02: Vision — voir les passes que les autres ne voient pas

**What to build:** aujourd'hui `possession.choose_pass_target` traite tous les coéquipiers de la même façon. Vision détermine QUELLES passes le porteur envisage : un 90 voit la passe longue entre les lignes et le changement de jeu, un 30 ne voit que les partenaires proches et évidents (guide : Vision voit la passe, Passing la réussit, Decisions la choisit).

**Blocked by:** 01 (le choix entre options doit exister).

**Status:** livré (24/10/2026), validé QC

- [x] Un porteur à Vision haute joue mesurablement plus de passes vers l'avant et de passes longues qu'un porteur à Vision basse, à situation égale
- [x] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [x] (sans objet : bien voir le jeu compte à tous les postes, voir `decision.py`) Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [x] Joueur sans cet attribut : repli neutre (60), sans erreur
- [x] Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [x] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [x] Suite V2 verte ; V1 inchangée

**Constantes (validées 24/10/2026)** : portée 99 -> 50 m, 55 -> 30 m, 11 -> 10 m ; passe qui gagne au moins 15 m repérée 99 -> 90 %, 55 -> 50 %, 11 -> 10 % ; coéquipier le plus proche toujours vu.

**Mesure en match** (`scripts/measure_v2_decisions.py 4 attr:Vision=..`) : passes de plus de 25 m, Vision 90 -> 20,8 %, Vision 30 -> 5,1 % (critère : au moins 2 fois plus). Recalibration validée : SHOT 0,1 / DRIBBLE 0,04 -> 13,0 tirs par équipe, 2,67 buts par match sur 6 matchs.
