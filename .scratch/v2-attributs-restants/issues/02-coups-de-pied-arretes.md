# 02: Coups de pied arrêtés et ballon hors du terrain

**What to build:** Phase 8 du plan V2. Aujourd'hui un tir non converti donne le ballon au gardien et le ballon ne sort jamais. Ajouter : sortie du ballon (touche, corner, six mètres), fautes donnant coup franc ou penalty, et l'exécution de chaque coup de pied arrêté avec placement des deux équipes (joueurs grands dans la surface, marquage, mur, joueurs restés en couverture), duel aérien (ticket 01) et seconds ballons. Choix du tireur selon l'attribut concerné.

**Attributs :** Corners, Free Kick Taking, Long Throws, Penalty Taking ; Composure (penalty) ; Taille, Jumping Reach, Heading (via 01).

**Blocked by:** 01.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** prérequis de v2-coach-et-gestion-de-match/04 (gardien qui monte sur corner). Le placement doit prévoir un nombre de joueurs montés variable, réglable par l'état du match.

- [ ] Nombre de corners, touches, coups francs et penalties par match dans des fourchettes réelles sourcées (ou « non trouvé »)
- [ ] Corners élevé : plus de corners atteignant un coéquipier ; Penalty Taking élevé : plus de penalties marqués
- [ ] Long Throws élevé : une touche dans le dernier tiers peut atteindre la surface
- [ ] Les joueurs les plus grands sont envoyés dans la surface sur corner ; au moins un joueur reste en couverture
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
