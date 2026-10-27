# 23: Hors-jeu

**What to build:** La règle du hors-jeu (Lois du jeu, loi 11) dans le moteur V2. Au départ d'une passe vers l'avant, un attaquant plus proche de la ligne de but adverse que le ballon et que l'avant-dernier adversaire, dans la moitié adverse, est en position de hors-jeu ; s'il reçoit le ballon, coup franc indirect pour l'adversaire. Les joueurs en tiennent compte : les attaquants règlent leurs appels sur la ligne adverse (rester en jeu, partir au moment de la passe), la ligne défensive peut monter pour mettre hors-jeu, avec le risque d'être prise dans le dos.

**Attributs :** Off the Ball (timing de l'appel, rester en jeu) ; Positioning et Teamwork (tenir la ligne ensemble) ; Anticipation (sentir le moment de la passe). Concentration plus tard (oubli d'un défenseur qui couvre l'attaquant).

**Blocked by:** 05 (hauteur de ligne).

**Status:** ready-for-agent (constantes à proposer avant le code)

**Pourquoi (27/10/2026) :** sans hors-jeu, une ligne haute laisse dans son dos un espace que rien n'interdit d'exploiter ; le ticket 05 doit donc garder la ligne derrière l'attaquant adverse le plus avancé, et un attaquant qui reste haut fait reculer toute la ligne. Ajouté à la demande du propriétaire.

- [ ] Position de hors-jeu jugée au départ de la passe (ballon, avant-dernier adversaire, moitié adverse), coup franc indirect si l'attaquant hors-jeu reçoit
- [ ] Hors-jeu par match dans une fourchette réelle (à sourcer)
- [ ] Les appels partent au moment de la passe plutôt qu'en restant hors-jeu ; la ligne défensive ne recule plus systématiquement avec l'attaquant le plus avancé (garde-fou du ticket 05 à revoir)
- [ ] Trace et écran V2 : coup de sifflet et raison lisible
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée

**Reporté du ticket 05 (27/10/2026, décision du propriétaire) :** avec la ligne défensive à sa hauteur réelle, tirs et buts sortent des fourchettes (20 matchs : 18,1 tirs par équipe, 4,7 buts par match ; réel 8-15 et 2-3,5). Les tirs de contre-attaque après une récupération dans son camp doublent (4,8 → 9,5 par match) : les blocs se croisent plus haut et plus serrés, et personne ne se replace encore à la perte. Critère ajouté : mesurer l'effet du hors-jeu sur tirs et buts, et revoir le garde-fou « derrière l'attaquant le plus avancé » du ticket 05.
