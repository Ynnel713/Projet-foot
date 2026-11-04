# 02: Coups de pied arrêtés et ballon hors du terrain

**What to build:** Phase 8 du plan V2. Aujourd'hui un tir non converti donne le ballon au gardien et le ballon ne sort jamais. Ajouter : sortie du ballon (touche, corner, six mètres), fautes donnant coup franc ou penalty, et l'exécution de chaque coup de pied arrêté avec placement des deux équipes (joueurs grands dans la surface, marquage, mur, joueurs restés en couverture), duel aérien (ticket 01) et seconds ballons. Choix du tireur selon l'attribut concerné.

**Attributs :** Corners, Free Kick Taking, Long Throws, Penalty Taking ; Composure (penalty) ; Taille, Jumping Reach, Heading (via 01).

**Blocked by:** 01, `v2-collectif/29` (ballon mort) et `v2-collectif/30` (fautes sifflées).

**Mise à jour du 03/11/2026 (revue de réalisme) :** la sortie du ballon (touche, sortie de but, corner) et les remises en jeu simples sont désormais au ticket `v2-collectif/29`, les fautes sifflées et les coups francs simples au `v2-collectif/30`. Ce ticket se limite à l'**exécution travaillée** des coups de pied arrêtés (placement, mur, marquage, duel aérien, seconds ballons, choix du tireur par attribut) et aux penalties, s'ils n'ont pas été livrés au 30.

**Status:** découpé (04/11/2026, audit de granularité) en 02a (penalty) et 02b (corners, coups francs et touches longues travaillés). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Point de vigilance :** prérequis de v2-coach-et-gestion-de-match/04 (gardien qui monte sur corner). Le placement doit prévoir un nombre de joueurs montés variable, réglable par l'état du match.

- [ ] Nombre de corners, touches, coups francs et penalties par match dans des fourchettes réelles sourcées (ou « non trouvé »)
- [ ] Corners élevé : plus de corners atteignant un coéquipier ; Penalty Taking élevé : plus de penalties marqués
- [ ] Long Throws élevé : une touche dans le dernier tiers peut atteindre la surface
- [ ] Les joueurs les plus grands sont envoyés dans la surface sur corner ; au moins un joueur reste en couverture
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
