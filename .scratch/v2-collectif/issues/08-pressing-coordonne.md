# 08: Pressing intelligent et coordonné

**What to build:** Le presseur ne court pas seulement vers le porteur : il **oriente sa course** pour fermer une ligne de passe et pousser vers une zone choisie. Le pressing se **déclenche collectivement** (passe en retrait, mauvais contrôle, joueur dos au jeu), et ses partenaires suivent pour ne pas laisser un adversaire libre derrière lui. Effort par à-coups : s'il échoue, il relâche, et un autre prend le relais.

**Attributs :** Work Rate, Aggression (engagement au contact), Anticipation, Teamwork.

**Blocked by:** 07.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** le pressing par à-coups (5 s d'effort, puis 5 à 20 s pour souffler selon Work Rate) a été codé dans le travail sauvegardé dans `.scratch/v2-collectif/wip-socle-02-intensite.patch` du ticket socle 02. Le reprendre ici.

- [ ] Test de pressing : le pressing coordonné ferme mesurablement plus de solutions qu'un pressing individuel, sans rendre les récupérations automatiques
- [ ] Récupérations dans les 5 à 6 s après un pressing dans une fourchette réelle (CMU, StatsBomb ; chiffre à sourcer)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
