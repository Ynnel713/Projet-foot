# 02b: Corners, coups francs et touches longues travaillés

**Découpé du ticket 02 le 04/11/2026** (audit de granularité). La sortie du ballon et les remises en jeu simples sont au ticket `v2-collectif/29`, les coups francs simples au `v2-collectif/30`. Détail : `02-coups-de-pied-arretes.md`.

**What to build:** exécution travaillée des coups de pied arrêtés : placement des deux équipes (joueurs grands dans la surface, marquage, mur, joueurs restés en couverture), duel aérien (ticket 01), seconds ballons, choix du tireur selon l'attribut (Corners, Free Kick Taking, Long Throws). Le placement prévoit un nombre de joueurs montés variable, réglable par l'état du match (prérequis du gardien qui monte, `v2-coach-et-gestion-de-match/04`).

**Attributs :** Corners, Free Kick Taking, Long Throws ; Taille, Jumping Reach, Heading (via 01).

**Blocked by:** 01, `v2-collectif/29` (livré), `v2-collectif/30`.

**Bloque :** 03 (a, b, c) ; `v2-coach-et-gestion-de-match/04` et `05a` ; `v2-collectif/22a`. Alimente le temps additionnel (`v2-coach-et-gestion-de-match/03`) sans le bloquer (décision Q14 du 03/11/2026).

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Nombre de corners, touches et coups francs par match dans des fourchettes réelles sourcées (ou « non trouvé »)
- [ ] Corners élevé : plus de corners atteignant un coéquipier
- [ ] Réserve du ticket `v2-collectif/30` (acceptée par le propriétaire le 04/11/2026) : coups francs du dernier tiers frappés au but 10-25 % (réel environ 19 %, Opta) ; 5 % au ticket 30, où le preneur est le joueur le plus proche ; ici, preneur désigné par Free Kick Taking et délai de 74,5 s quand il frappe (The Analyst)
- [ ] Long Throws élevé : une touche dans le dernier tiers peut atteindre la surface
- [ ] Les joueurs les plus grands sont envoyés dans la surface sur corner ; au moins un joueur reste en couverture
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
