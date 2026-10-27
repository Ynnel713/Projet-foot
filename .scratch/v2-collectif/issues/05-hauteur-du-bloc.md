# 05: Hauteur et profondeur du bloc

**What to build:** La ligne défensive ajuste sa hauteur selon la position du ballon, la **pression exercée sur le passeur** (passeur pressé : la ligne peut monter ; passeur libre : elle recule), la menace des appels adverses et les capacités des défenseurs (un défenseur lent a intérêt à défendre plus bas). L'espace laissé dans le dos est un choix collectif, pas un effet de la vitesse brute.

**Attributs :** Positioning ; Pace + Acceleration + Positioning (repli préventif) ; Anticipation (lecture de la passe en profondeur).

**Blocked by:** 04.

**Status:** livré (27/10/2026)

- [x] Ligne défensive mesurablement plus basse avec des défenseurs lents : profil Pace 99 contre 11, 38,9 contre 27,1 m (le profil force Pace pour toute l'équipe, pas seulement les défenseurs) ; règle testée à situation égale (`test_the_margin_uses_the_slowest_defender_of_the_last_line_only`)
- [x] Passeur pressé contre passeur libre : écart de hauteur de ligne mesurable. À zone du ballon égale, ligne plus haute porteur pressé : tiers défensif 40,1 contre 36,7 m, milieu 31,9 contre 26,0 m, tiers offensif 23,0 contre 11,6 m (zone vue de l'équipe en possession). Sans découpage, la comparaison est biaisée par la position du ballon (31,5 contre 34,1 m)
- [ ] Passes en profondeur réussies dans une fourchette réelle : valeur réelle **non trouvée** (StatsBomb ne publie que des modèles par passe). Mesuré : 4,1 % des passes, réussies à 66 % ; indicateur suivi
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Livraison (27/10/2026)

- `v2engine/bloc.py`, `Bloc.update` : sans ballon, la dernière ligne se place à la plus basse de deux hauteurs, jamais à moins de 5 m de son but : 35 m ballon au centre, suivant le ballon à 50 %, ± 5 m selon la pression sur le porteur (pressé sous 3 m, libre à 9 m ou plus) ; et derrière l'attaquant adverse le plus avancé, d'une marge de 2 m plus ce qu'il gagne sur 30 m sur le défenseur le plus lent de la dernière ligne (Pace, capacité). Le bloc se cale sur cette ligne ; avec ballon, rien ne change.
- Acceleration n'est pas utilisée (ajout si la mesure le justifie) ; Anticipation n'a pas de nouvel effet (règle R1 : elle lit déjà les passes) ; Positioning garde son effet du ticket 04.
- Mesure sur 20 matchs (ticket 04 → ticket 05) : hauteur de ligne sans ballon 16,7 → 32,7 m (réel : médiane 45 m, arXiv 2511.06191) ; écart ligne-ballon 35,5 → 18,8 m (réel : médiane 27,6 m, la moitié des cas entre 18 et 37 m) ; défense-milieu / milieu-attaque 16,7 / 18,8 → 13,0 / 13,4 m (réel 10,2 / 13,3) ; longueur sans ballon 40,9 → 30,1 m ; compacité autour du ballon 13,7 → 7,5 m ; passes chez l'adversaire 30,6 → 33,8 % ; **tirs 13,7 → 18,1 par équipe, buts 3,0 → 4,7** (hors fourchettes : reporté aux tickets 10 et 23, décision du propriétaire) ; tirs de contre après récupération dans son camp 4,8 → 9,5 ; tacles 52 → 58 ; km par joueur 25,8 → 30,6.
- Limites des indicateurs : la passe en profondeur se juge sur la position du receveur (pas sur le point visé) avec les défenseurs du tick précédent ; la « hauteur du bloc » mesurée est la moyenne de la ligne défensive, le moteur cale le joueur le plus bas ; sans hors-jeu (ticket 23), un attaquant posté près du but colle la ligne au plancher.
