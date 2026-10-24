# 06: Teamwork — jouer pour le collectif

**What to build:** Teamwork pèse sur deux choses : (1) le porteur préfère la passe au partenaire mieux placé plutôt que l'action personnelle (choix du ticket 01) ; (2) sans ballon, le joueur tient sa zone de formation plutôt que de l'abandonner, ce qui garde le bloc compact (guide, Teamwork).

**Blocked by:** 01 et 03 (ajuste les deux mécanismes).

**Status:** ready-for-agent

- [ ] À situation égale, un porteur à Teamwork haut passe mesurablement plus souvent au partenaire mieux placé
- [ ] Une équipe à Teamwork élevé reste mesurablement plus compacte (écart moyen entre ses joueurs) qu'une équipe à Teamwork bas
- [ ] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [ ] Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [ ] Joueur sans cet attribut : repli neutre (60), sans erreur
- [ ] Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [ ] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [ ] Suite V2 verte ; V1 inchangée
