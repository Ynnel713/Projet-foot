# 22: Calibration générale

**What to build:** Calibration **unique** une fois la structure collective en place, sur au moins 50 matchs. Reprend le ticket v2-socle/05 et tous les critères reportés. Les chiffres réels restent la boussole, mais servent ici d'indicateurs : on règle les constantes déjà validées dans leurs fourchettes, chaque levier proposé avant d'être appliqué.

**Attributs :** Tous.

**Blocked by:** Tickets 01 à 21 et 23 ; 28 à 33 ; `v2-attributs-restants/01`, `02`, `03`, `07` et `11` ; `v2-coach-et-gestion-de-match/03` (revue de réalisme du 03/11/2026 : tout ce qui change le nombre ou la forme des actions passe avant la calibration, qui ne se fait qu'une fois, sur le moteur complet). Passent après elle : `v2-attributs-restants/10`, `05`, `04`, `09` (avec un simple contrôle de non-régression).

**Critères repris le 03/11/2026 :** C2 du ticket 14 (une passe sans gain suivie d'une passe qui fait avancer, 39 % visé contre 30 à 32 % mesurés), échelle de progression de la deuxième passe au-delà de 20 m (A2 du ticket 13), nouveaux indicateurs des tickets 28 à 32 (touches, sorties de but, corners, fautes, tirs par zone, passes à une touche, grosses occasions) et temps de jeu effectif.

**Status:** découpé (04/11/2026, audit de granularité) en trois lots successifs : 22a (volumes, passes, rythme), 22b (tactique), 22c (tirs, buts, arrêts de jeu). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux. La calibration reste unique, sur le moteur complet.

**Point de vigilance :** le ticket v2-socle/05 est absorbé ici.

**Reporté du ticket 09 (réserve A2 de l'expert, acceptée par le propriétaire le 02/11/2026 : « J'accepte ») :** les tacles passent de 44,75 à 51,15 par match (+14 %, 20 matchs, graine d'audit, `7a94d64` puis ticket 09), au-dessus de la fourchette réelle de 30 à 40. Cause probable : le presseur envoyé au point de réception pendant une passe adverse en vol (passe en vol seule : 55,6). À reprendre dans la calibration des tacles.

- [ ] Reprise du ticket socle 05 : tirs 8-15 par équipe, buts 2-3,5 par match, receveur visé au moins 50 %, passes de plus de 32 m (environ 47 % réussies, 10-19 % des passes), passes réussies 70-90 %, au plus 25 % chez l'adversaire
- [ ] Rythme du ticket socle 06 (15-17 passes par minute, 2-3 s par joueur, possessions de 11-16 s), tacles 30-40, courses du ticket 12
- [ ] Indicateurs tactiques du ticket 01 dans leurs fourchettes
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
- [ ] Repris du ticket 29 (réserve A2 acceptée le 03/11/2026) : temps de jeu effectif 65 à 80 % tant que fautes et remplacements manquent, sinon 53 à 56 % (réel, CIES) ; au ticket 29 : 86,6 %

## Base de référence après le ticket 25 (30/10/2026)

Le ticket 25 (socle cinématique et contact) a déplacé les indicateurs. Chiffres sur 20 matchs, graines 20260923 et suivantes, au pas du produit de 0,1 s : 4,85 buts, 17,8 tirs par équipe, 87 tacles et 755 pertes de balle par match ; 23 km par joueur de champ et 23 % de la distance au-dessus de 25 km/h. Avant ce ticket : 2,75 buts, 60 tacles, 30,5 km. Le propriétaire a accepté cette dérive le 30/10/2026 (réserve A1 de l'expert) : le réglage revient à ce ticket. Détail : `25-socle-cinematique-et-contact.md`, section « Mesures ».

## Base de référence après le ticket 26 (01/11/2026)

Les chiffres ci-dessus (ticket 25) sont faussés : une passe sur deux revenait au passeur et comptait comme réussie (ticket 26). Nouvelle base, 20 matchs, mêmes graines, `c379ba6` + correctif : passes chez l'adversaire 35,6 % (15 à 20 % au haut niveau), passes réussies 64,3 %, tirs 8,2 par équipe, buts 1,75 par match, hors-jeu 0,75 par match. Hors-jeu (diagnostic de 8 matchs) : la règle fonctionne (50 % des passes vers un receveur hors-jeu sifflées) ; le déficit vient des attaquants, trop loin de la ligne (8,6 m en médiane) et de passes en profondeur presque absentes (0,2 %). Leviers : tickets 16, 11 et 13 ; pas de recalibration de la règle du hors-jeu (décision du propriétaire, 01/11/2026). Détail : `INDICATEURS_V2.md` et `.scratch/v2-collectif/diagnostic-hors-jeu-30-10-2026.md`.

## À surveiller depuis le ticket 08 (01/11/2026)

Réserve A3 de l'expert : la distance d'arrêt du presseur à Aggression 11 (1,6 m) dépasse le rayon de tacle (1,5 m). Un presseur peu agressif ne tacle que si le porteur vient vers lui. C'est voulu (il laisse le porteur se retourner), mais cela pèse sur le nombre de tacles à régler ici.

## À surveiller depuis le ticket 10 (03/11/2026, réserves A1 à A3 acceptées par le propriétaire)

Série d'au moins 40 matchs avec dispersion (16 matchs donnent des buts de 2,94 ou 3,56 pour le même état) :
- latence du repli (2,53 s) : pas de valeur réelle trouvée ; ordre de grandeur Bundesliga 2010/11, meilleures équipes : ballon récupéré en environ 1 s (temps de récupération, pas de réaction) ;
- tirs de contre après récupération dans son camp (4,8 → 4,75) : remesurer aussi les réserves 09 C3 et 09 A1 et 11 A1 (contre-attaque « non jouable » mieux sanctionnée ?) ;
- hors-jeu (1,6 par match) et recul du bloc (centre d'équipe à −0,76 m/s après la perte) : la règle « pas de montée en transition défensive » fait reculer l'équipe (+0,22 m/s) mais fait tomber le hors-jeu à 0,69 et monte les tirs de contre à 6,2 ; une règle plus fine (par exemple après les premières secondes) reste à essayer ici. Rouvrir si le hors-jeu reste sous 2 par match.
