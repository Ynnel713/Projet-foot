# 01: Décision du porteur (Decisions)

**What to build:** remplacer la règle provisoire actuelle (« je tire si je suis à moins de 20 m, sinon je passe », `match._step_ball`, D-V08) par un vrai choix entre trois options : tirer, passer, conduire le ballon. Chaque option reçoit une valeur selon la situation réelle (distance et angle au but, pression d'un adversaire proche, coéquipier démarqué). Decisions règle la probabilité de choisir la MEILLEURE option : un 90 la prend presque toujours, un 30 tire souvent alors qu'un partenaire est seul (guide, Decisions). Ticket racine de la phase 5 : introduit la conduite de balle, qui n'existe pas aujourd'hui (le porteur s'arrête ou passe).

**Blocked by:** None (ticket racine de la phase 5).

**Status:** livré (24/10/2026), validé QC — revue simulafoot-reviewer : accepter avec réserves ; reste ouvert le critère « écart mesuré sur matchs simulés »

- [x] Le porteur peut conduire le ballon (avancer avec), pas seulement passer ou tirer
- [x] Plus de seuil fixe de 20 m : un tir de 25 m reste possible, un tir à 15 m sous forte pression peut être évité
- [x] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [x] (sans objet : Decisions compte autant à tous les postes, voir `decision.py`) Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [x] Joueur sans cet attribut : repli neutre (60), sans erreur
- [ ] Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [x] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [x] Suite V2 verte ; V1 inchangée

**Mesure (24/10/2026)** : `scripts/measure_v2_decisions.py`, 6 matchs de Ligue 1 : 11,0 tirs par équipe, 2,17 buts par match (cibles 8-15 et 2-3,5). Poids de calibration SHOT 0,2 / PASS 0,25 / DRIBBLE 0,06, actés par le propriétaire le 24/10/2026.
