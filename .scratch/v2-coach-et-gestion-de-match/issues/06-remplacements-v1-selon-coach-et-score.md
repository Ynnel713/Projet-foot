# 06: Remplacements V1 selon le coach, le résultat et la fatigue

**What to build:** En V1, les remplacements tactiques choisissent le sortant au hasard (`events.py`, `random.shuffle(candidates_off)`) et l'entrant par meilleure note du même groupe.

**Constat (vérifié, revue expert du 02/11/2026) :** les remplacements sont tirés **avant** les buts (`_play_match_squad` l.348-349, puis `_generate_goals` l.351) ; la minute de chaque but est tirée ensuite selon la présence du buteur sur le terrain (l.599), et les buteurs sont pondérés sur l'effectif qui comprend les entrants. Au moment de tirer un remplacement, seul le **nombre** de buts de chaque équipe est connu, pas le score à la minute du changement.

Deux options à trancher par le propriétaire :

- **(b, recommandée)** Garder l'ordre actuel et utiliser le **résultat final** (gagnant, perdant, nul) comme tendance : l'équipe qui perdra fait plutôt entrer des profils offensifs ; celle qui gagnera, avec un coach Défensif ou Contre attaque, plutôt des profils défensifs en fin de match ; sinon poste pour poste. Changement local, faible écart de réalisme sur une feuille de match.
- (a) Réordonner : tirer d'abord les minutes des buts, puis les remplacements selon le score à la minute, puis attribuer les buteurs. Plus réaliste, mais réécriture plus lourde dans un fichier du moteur de résultats.

Dans les deux cas : le sortant est tiré avec une probabilité qui augmente quand sa Stamina est basse ; les nouveaux tirages utilisent un générateur dérivé (`_deterministic_rng`) pour ne pas décaler le flux `random` existant.

**Attributs :** Stamina (choix du sortant).

**Blocked by:** —

**Décision du propriétaire (02/11/2026) :** option (b) retenue ; modification de `events.py` autorisée pour ce ticket.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** changer l'entrant change la liste des buteurs possibles : les buteurs et les minutes de but peuvent changer pour une graine donnée. Feuille de match, animation et narration doivent rester cohérentes entre elles. Option (b) : la narration ne doit pas présenter le changement comme une réaction au score (l'équipe peut encore mener à ce moment). Retirer `random.shuffle` décale le flux `random` suivant (cartons des entrants) : garder le même nombre d'appels, ou accepter et noter ce décalage.

- [ ] Nombre de buts de chaque équipe identique avant/après pour un échantillon de matchs à graine fixe ; buteurs et minutes peuvent changer
- [ ] Équipe perdante : part d'entrants offensifs mesurablement supérieure à celle de l'équipe gagnante
- [ ] Sortants en moyenne de Stamina plus basse que les titulaires non remplacés
- [ ] Club sans coach ou sans style : comportement poste pour poste (neutre)
- [ ] Aucune divergence feuille de match / clip / narration
- [ ] Suite complète passée (compte comparé à l'attendu de `CLAUDE.md`)
