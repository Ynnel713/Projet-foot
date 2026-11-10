# 01: Centres, jeu aérien et taille

**What to build:** Phase 7 du plan V2. Le porteur sur un côté peut centrer ; un ballon aérien (centre, dégagement long, corner plus tard) est disputé par les joueurs proches de son point de chute ; le duel aérien est résolu par un tirage pondéré (D-V03, pas de vraie trajectoire 3D) :

1. **Arriver au ballon** : Taille FM (`Taille FM (cm)`, repli sur `Taille (cm)`, puis neutre) + Jumping Reach, pondérés par Bravery (aller au contact) ; Strength pour le placement au contact.
2. **Bien le jouer** : Heading (direction, puissance) pour le joueur qui l'emporte.
3. ~~Frappes lointaines par Long Shots~~ : déplacé au ticket `v2-collectif/28` (même calcul de tir, frontière Finishing / Long Shots tranchée là-bas ; recommandation de l'expert acceptée le 03/11/2026). L'issue d'une tête passe par le calcul de tir du 28.

**Attributs :** Crossing, Heading, Jumping Reach, Bravery, Taille (Long Shots : ticket `v2-collectif/28`). Les types de centres (enroulé, tendu, en retrait, au ras du sol) sont au ticket 11.

**Complément (03/11/2026, D-V03 révisée, `docs/ETUDE_HAUTEUR_V2.md`) :** le ballon a désormais une vraie hauteur (`v2-hauteur-ballon/02`) et chaque joueur une tranche de hauteur accessible (`v2-hauteur-ballon/03`). Le tirage pondéré ne réunit que les joueurs capables d'atteindre le ballon à temps (bonne position au bon instant, hauteur dans leur portée de tête). Le moteur trace un événement « saut » (joueur, instant, hauteur de pointe) ; l'écran remonte le rond du sauteur, son ombre restant au sol. Les joueurs restent à plat dans le moteur.

**Blocked by:** v2-collectif/18 (règle anti double comptage), v2-collectif/28a (calcul du tir, pour la tête), v2-hauteur-ballon/03 (hauteur du ballon et portée des joueurs).

**Bloque :** 11 ; `v2-realisme/23b` (ajouté le 10/11/2026).

**Status:** à faire, périmètre réduit (05/11/2026, chantier `v2-realisme`, validé par le propriétaire) : ce ticket garde le **centre** (Crossing : le porteur sur un côté centre, précision, centres atteignant un coéquipier). Le jeu aérien est découpé en `v2-realisme/15a` (qui attaque la trajectoire), `15b` (duel aérien : taille, Jumping Reach, Strength), `15c` (tête, Heading), `15d` (dégagement de la tête), `15e` (seconds ballons), `15f` (validation) ; les critères aériens ci-dessous y sont repris. Constantes à proposer avant le code.

**Point de vigilance :** la taille ne doit pas tout écraser (un 1,75 m à grande détente gagne des duels contre un 1,90 m moyen). Ordre de grandeur de l'avantage de taille dans les duels aériens réels à sourcer ; « non trouvé » sinon.

- [ ] À autres attributs égaux, un joueur de 1,95 m gagne mesurablement plus de duels aériens qu'un joueur de 1,70 m, sans jamais 100 % ni 0 %
- [ ] Jumping Reach élevé compense une partie de l'écart de taille (mesuré)
- [ ] Le gagnant du duel cadre mieux sa tête avec un Heading élevé
- [ ] Crossing élevé : plus de centres atteignant un coéquipier
- [ ] Joueur sans taille renseignée : comportement neutre (taille moyenne du poste)
- [ ] Seuls les joueurs capables d'atteindre le ballon à temps disputent le duel (scène fixe : un joueur trop loin ou trop petit n'y figure pas)
- [ ] Chaque duel aérien trace un saut, visible à l'écran (rond remonté, ombre au sol)
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
