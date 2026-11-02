# 01: Centres, jeu aérien et taille

**What to build:** Phase 7 du plan V2. Le porteur sur un côté peut centrer ; un ballon aérien (centre, dégagement long, corner plus tard) est disputé par les joueurs proches de son point de chute ; le duel aérien est résolu par un tirage pondéré (D-V03, pas de vraie trajectoire 3D) :

1. **Arriver au ballon** : Taille FM (`Taille FM (cm)`, repli sur `Taille (cm)`, puis neutre) + Jumping Reach, pondérés par Bravery (aller au contact) ; Strength pour le placement au contact.
2. **Bien le jouer** : Heading (direction, puissance) pour le joueur qui l'emporte.
3. Les frappes lointaines (> 20 m) sont résolues par Long Shots, distinct de Finishing.

**Attributs :** Crossing, Heading, Jumping Reach, Bravery, Long Shots, Taille.

**Blocked by:** v2-collectif/18 (règle anti double comptage).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** la taille ne doit pas tout écraser (un 1,75 m à grande détente gagne des duels contre un 1,90 m moyen). Ordre de grandeur de l'avantage de taille dans les duels aériens réels à sourcer ; « non trouvé » sinon.

- [ ] À autres attributs égaux, un joueur de 1,95 m gagne mesurablement plus de duels aériens qu'un joueur de 1,70 m, sans jamais 100 % ni 0 %
- [ ] Jumping Reach élevé compense une partie de l'écart de taille (mesuré)
- [ ] Le gagnant du duel cadre mieux sa tête avec un Heading élevé
- [ ] Crossing élevé : plus de centres atteignant un coéquipier
- [ ] Long Shots élevé : plus de frappes lointaines cadrées ; Decisions règle la tentative (pas de double comptage)
- [ ] Joueur sans taille renseignée : comportement neutre (taille moyenne du poste)
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
