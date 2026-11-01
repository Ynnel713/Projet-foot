# 14: Combinaisons collectives

**What to build:** Reconnaître des **séquences possibles** comme des opportunités, jamais comme des scripts : remise, troisième homme, une-deux, dédoublement, renversement, passe dans la course, changement de position. Évaluer la faisabilité de la séquence entière (joueurs accessibles, interception possible) et l'abandonner si le défenseur ferme la ligne.

**Attributs :** Vision, Decisions, Off the Ball, Teamwork, Anticipation.

**Blocked by:** 13.

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Test de circulation : les joueurs créent mesurablement des triangles et des solutions de soutien
- [ ] Une combinaison démarrée est abandonnée quand la ligne se ferme (test)
- [ ] Fréquence des une-deux et du troisième homme dans une fourchette réelle (à sourcer)
- [ ] Repris du ticket 13 (réserve A1, acceptée le 02/11/2026) : en match, une passe sans gain suivie par le receveur d'une passe qui casse une ligne ou gagne 10 m augmente mesurablement (32,5 % sans la suite du ticket 13, 30,6 % avec, 10 matchs ; critère d'origine : au moins 39 %), le receveur jouant la passe que le porteur a préparée ; échelle de progression de la deuxième passe au-delà de 20 m à proposer (A2 de l'expert, facultatif)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
