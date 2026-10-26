# 04: Bloc de référence dynamique

**What to build:** Remplacer la place de formation fixe par une **position de référence** qui dépend du ballon, de la situation (ticket 03), du rôle et des partenaires. Le bloc coulisse vers le côté du ballon, réduit les espaces entre joueurs et protège les zones dangereuses ; le côté opposé se resserre sans perdre toute capacité à défendre un renversement. Teamwork : tenir et reprendre sa place dans ce bloc (partie « sans ballon » du ticket v2-cerveau-joueurs/06).

**Attributs :** Teamwork, Positioning.

**Blocked by:** 03.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** un décalage simple du bloc (`BLOCK_SHIFT`, 50 % en longueur, 30 % en largeur) a été codé dans le travail sauvegardé dans `.scratch/v2-collectif/wip-socle-02-intensite.patch` du ticket socle 02. Le reprendre ici comme point de départ, pas comme solution.

- [ ] Le centre de l'équipe suit le ballon, surtout dans la longueur (Frencken et al. 2012), avec des distances entre lignes dans des fourchettes réelles (à sourcer)
- [ ] Côté opposé resserré mais présent : un renversement ne trouve pas un côté vide
- [ ] Une équipe à Teamwork élevé reste mesurablement plus compacte qu'une équipe à Teamwork bas (critère du ticket cerveau 06)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
