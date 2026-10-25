# 03: Un duel par confrontation, pas un tacle par tick

**What to build:** défaut T2 de la revue : un adversaire à portée tente un tacle avec une probabilité fixe toutes les 0,1 s (environ 5 tacles par seconde au contact), ce qui arrache des ballons en permanence. Remplacer par une confrontation : le défenseur temporise ou engage UNE fois (moment choisi), un tacle raté l'élimine quelques instants. Prépare la refonte Tackling/Aggression/Dribbling (étape « duels » de la revue).

**Blocked by:** None (indépendant de 01 et 02).

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Au plus un tacle par défenseur et par confrontation (vérifiable en test)
- [ ] Un défenseur dont le tacle échoue ne peut pas retenter immédiatement
- [ ] Le nombre de tacles par match se rapproche de la réalité (chiffre réel à sourcer avant le code)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [ ] Calibration remesurée après coup (tirs par équipe 8-15, buts par match 2-3,5, passes perdues) avec `scripts/measure_v2_decisions.py`
- [ ] Suite V2 verte ; V1 inchangée
