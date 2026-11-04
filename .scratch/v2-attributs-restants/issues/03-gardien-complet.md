# 03: Gardien complet

**What to build:** Phase 9 du plan V2. Sorties sur centres (Command of Area décide, Aerial Reach + Taille règlent la portée), capter ou boxer (Punching, tendance), placement et sorties hors de la surface (Rushing Out, tendance), relance au pied (Kicking) et à la main (Throwing), effet sur le placement des défenseurs (Communication), goût du risque (Eccentricity, tendance). Lève la dérogation A8 (note du gardien mélangée dans le tir, `docs/CARTE_ATTRIBUTS_V2.md`).

**Attributs :** Aerial Reach, Command of Area, Communication, Kicking, Throwing, Rushing Out, Punching, Eccentricity ; Taille.

**Blocked by:** 01, 02.

**Status:** découpé (04/11/2026, audit de granularité) en 03a (dans les airs), 03b (placement, sorties, arrêts) et 03c (relances). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Point de vigilance :** Rushing Out, Punching et Eccentricity sont des **tendances**, pas des qualités (`docs/TRD_V2.md`) : elles changent le style, jamais le niveau. Eccentricity alimente aussi la propension du gardien à monter (v2-coach-et-gestion-de-match/04).

- [ ] Command of Area élevé : plus de sorties sur centres ; Aerial Reach + Taille : plus de sorties réussies
- [ ] Punching élevé : plus de ballons boxés, moins captés, à réussite égale
- [ ] Rushing Out élevé : position moyenne plus haute ; plus de ballons interceptés derrière la défense ; plus de buts lobés
- [ ] Kicking/Throwing : distance et précision des relances mesurablement liées à l'attribut
- [ ] Dérogation A8 levée : Reflexes pour les tirs proches, One on Ones pour les face-à-face, Handling pour capter ou relâcher
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
