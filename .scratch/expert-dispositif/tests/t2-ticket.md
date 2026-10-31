# 91: Joueurs plus réactifs aux changements de direction

**What to build:** Les joueurs réagissent plus vite quand leur cible change (ballon, place dans le bloc), sans dépasser leur vitesse maximale (Pace) ni perdre la différence entre bonne et mauvaise Acceleration.

**Status:** implémenté (29/10/2026) — en attente de /valider-ticket-simulafoot

- [x] Réaction plus rapide au changement de cible
- [x] Vitesse jamais au-dessus de max_speed_mps(Pace) × fatigue
- [x] Acceleration garde son effet : un joueur à 99 atteint sa pointe plus vite qu'un joueur à 11
- [x] Résultat indépendant du pas de simulation dt
