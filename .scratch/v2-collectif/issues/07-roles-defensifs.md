# 07: Rôles défensifs : presser, couvrir, marquer, fermer l'axe

**What to build:** En défense, l'équipe attribue des rôles : **un presseur** sur le porteur, **une couverture** derrière lui (entre le ballon et le but), des **marquages** sur les adversaires dangereux et la **protection de l'axe**. Les autres tiennent le bloc (ticket 04). C'est ce qui manque aujourd'hui : avec un seul presseur et personne pour couvrir, la mesure du 26/10 donnait 59 tirs par équipe et 17,8 buts par match.

**Attributs :** Marking (adversaire désigné), Positioning (zone), Work Rate (envie de presser), Anticipation.

**Blocked by:** 04.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** le presseur unique a été codé dans le travail sauvegardé dans `.scratch/v2-collectif/wip-socle-02-intensite.patch` du ticket socle 02. Le reprendre comme rôle « presseur » parmi les autres.

- [ ] Tirs par équipe et buts par match revenus à des ordres de grandeur réels sans réglage générique (à confirmer au ticket 22)
- [ ] Un presseur a une couverture quand le danger le justifie (test tactique)
- [ ] Un attaquant dangereux est marqué mesurablement plus près par un bon marqueur
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée

**Reporté du ticket 04 (27/10/2026) :** critère « une équipe à Teamwork élevé reste mesurablement plus compacte qu'une équipe à Teamwork bas ». Au ticket 04, Teamwork ne règle que les joueurs qui se replacent (écart 0,5 % du stretch index) ; il doit aussi agir sur qui quitte le bloc pour aller au ballon. À surveiller aussi : tacles montés à 52 par match avec le bloc (fourchette réelle 30-40).
