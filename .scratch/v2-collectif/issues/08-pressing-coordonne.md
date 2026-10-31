# 08: Pressing intelligent et coordonné

**What to build:** Le presseur ne court pas seulement vers le porteur : il **oriente sa course** pour fermer une ligne de passe et pousser vers une zone choisie. Le pressing se **déclenche collectivement** (passe en retrait, mauvais contrôle, joueur dos au jeu), et ses partenaires suivent pour ne pas laisser un adversaire libre derrière lui. Effort par à-coups : s'il échoue, il relâche, et un autre prend le relais.

**Attributs :** Work Rate, Aggression (engagement au contact), Anticipation, Teamwork.

**Blocked by:** 07.

**Status:** livré (31/10/2026), validé expert + QC (avec réserves acceptées, voir Comments ; suite au ticket 27)

**Point de vigilance :** le pressing par à-coups (5 s d'effort, puis 5 à 20 s pour souffler selon Work Rate) a été codé dans le travail sauvegardé dans `.scratch/v2-collectif/wip-socle-02-intensite.patch` du ticket socle 02. Le reprendre ici.

- [~] (réserve, ticket 27) Test de pressing : le pressing coordonné ferme mesurablement plus de solutions qu'un pressing individuel, sans rendre les récupérations automatiques
- [x] Récupérations dans les 5 à 6 s après un pressing dans une fourchette réelle (CMU, StatsBomb ; chiffre à sourcer)
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Base de référence après le ticket 25 (30/10/2026)

Depuis le ticket 25, le presseur rattrape vraiment le porteur en conduite, puisque la loi d'arrivée tient compte de la vitesse de la cible. Mesure de référence sur 20 matchs à 0,1 s : 87 tacles, 755 pertes de balle et 4,85 buts par match, et 9 % du temps en défense placée (contre 60 tacles, 581 pertes, 2,75 buts et 17 % avant). Deux défauts antérieurs, désormais visibles, sont à traiter ici. Tout adversaire à moins de 15 m du ballon devient presseur, ce qui forme un essaim. Un défenseur battu qui reste à moins de 3 m du porteur ne peut plus retenter de tacle (`CONFRONTATION_END_M`, revue expert du ticket 25, A4).

## Clôture (31/10/2026) : livré avec réserves, validées par le propriétaire

- Test unitaire du pressing coordonné vert, mais pas d'effet en match : solutions de passe faciles (≥ 80 %) 1,42 → 1,57, solutions ouvertes (≥ 0,5) 5,21 → 5,31. Suite au ticket 27.
- Récupération dans les 5 s après un pressing : 37 % avant, 39 % après. Tacles 68 → 53, pertes 545 → 578, buts 2,1 → 2,0 par match.
- Profils : Aggression 99 / 11, distance presseur-porteur 1,24 / 1,49 m. Work Rate presque sans effet (temps de pressing 1282 / 1261 s). Teamwork en sens inverse sur les solutions laissées (1,69 / 1,53).
- Rayon « marqué » testé à 3 m sans effet, puis annulé. La cause est la courbe de passe, plate autour d'un écart nul : marquage et pression ne font pas passer une passe courte sous 0,5. D'où le nouvel indicateur « solutions de passe faciles ».

## Comments

- 31/10/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC BLOQUÉ (validation du propriétaire non tracée, V1 non démontrée).
  - Clôture avec réserves validée par le propriétaire, ses mots : « Yes, close it ».
  - Réserves de l'expert acceptées, ses mots : « Accept A1–A5 ».
  - A1 : critère 1 non atteint en match, reporté au ticket 27.
  - A2 : le déclencheur « passe en retrait » n'a pas de seuil. Mesurer la fréquence des déclenchements au début du ticket 27.
  - A3 : la distance d'arrêt à Aggression 11 (1,6 m) dépasse le rayon de tacle (1,5 m). À surveiller au ticket 22.
  - A4 : l'effort peut dépasser 5 s si le presseur revient (facultatif).
  - A5 : Work Rate presque neutre en match, à voir au ticket 12 (facultatif).
  - Constantes validées avant le code (31/10/2026), mots du propriétaire : « Ok avec tes recommandations ». Seuil « solutions faciles » de 0,8 : « Ok avc ta recommandation ».
  - QC passage 2 : VALIDÉ.
  - V1 inchangée : aucun fichier V1 dans le diff (`git diff --stat 8043889`, voir le dossier de revue).
