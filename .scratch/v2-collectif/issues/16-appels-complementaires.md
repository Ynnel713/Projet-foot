# 16: Déplacements offensifs complémentaires

**What to build:** Les attaquants ne convergent pas tous vers le ballon : appels **non redondants** (pas deux joueurs sur la même profondeur), décrochage pour **libérer une zone** même sans recevoir, **appels leurres**, permutations (l'ailier rentre, le milieu occupe la zone libérée). L'appel dépend de la capacité du porteur à l'exploiter : avec un excellent Off the Ball mais un porteur sans Vision ni qualité de passe, l'appel est ignoré ou avorté. Comprend le dernier tiers hors centres (les centres arrivent en phase 7).

**Attributs :** Off the Ball, Teamwork, Anticipation ; Vision et Passing du porteur.

**Blocked by:** 06, 13.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** Off the Ball mesuré à l'envers le 26/10 (784 appels vers l'avant à 99 contre 946 à 11) : à expliquer ici.

- [ ] Off the Ball 99 contre 11 : plus d'appels, et plus intenses (le sens est inversé dans la mesure du 26/10)
- [ ] Pas deux appels sur la même zone au même moment (test)
- [ ] Reprend le critère en match reporté du ticket cerveau 03 (espace des coéquipiers du porteur)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée

## Comments

- 01/11/2026, diagnostic du hors-jeu après le ticket 26 (8 matchs, graine d'audit, `c379ba6` + correctif du 26) : l'arbitrage fonctionne (50 % des passes vers un receveur hors-jeu sont sifflées, 41 % avant le ticket 25), mais les attaquants ne jouent pas sur la ligne. L'attaquant le plus avancé est à 8,6 m derrière la ligne en médiane, à moins de 2 m lors de 5,5 % des passes seulement (12,6 % avant le 25) ; receveur hors-jeu : 15 passes en 8 matchs ; passes en profondeur : 0,2 % des passes ; hors-jeu : 0,6 à 0,75 par match (3 à 4 dans le football réel). Ce ticket (appels à l'épaule du dernier défenseur, profondeur non redondante) est l'un des leviers, avec les tickets 11 et 13 ; le propriétaire a écarté le 01/11/2026 une recalibration de la règle du hors-jeu, qui gonflerait le chiffre sans corriger le jeu. Détail : `.scratch/v2-collectif/diagnostic-hors-jeu-30-10-2026.md`.
