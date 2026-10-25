# 03: Un duel par confrontation, pas un tacle par tick

**What to build:** défaut T2 de la revue : un adversaire à portée tente un tacle avec une probabilité fixe toutes les 0,1 s (environ 5 tacles par seconde au contact), ce qui arrache des ballons en permanence. Remplacer par une confrontation : le défenseur temporise ou engage UNE fois (moment choisi), un tacle raté l'élimine quelques instants. Prépare la refonte Tackling/Aggression/Dribbling (étape « duels » de la revue).

**Blocked by:** None (indépendant de 01 et 02).

**Status:** livré (25/10/2026), validé QC

- [x] Au plus un tacle par défenseur et par confrontation (vérifiable en test)
- [x] Un défenseur dont le tacle échoue ne peut pas retenter immédiatement
- [x] Le nombre de tacles par match se rapproche de la réalité (chiffre réel à sourcer avant le code)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [x] Calibration remesurée après coup (tirs par équipe 8-15, buts par match 2-3,5, passes perdues) avec `scripts/measure_v2_decisions.py`
- [x] Suite V2 verte ; V1 inchangée

## Réalisé (25/10/2026)

- Le nombre de tacles a déjà été ramené dans le réel par le ticket 06 : taux de 0,03 tentative par seconde de contact, cible 30-40 tacles par match (Premier League ~33, premierleague.com).
- Une confrontation commence à moins de 1,5 m et se termine quand le défenseur s'éloigne à plus de 3 m, ou quand le ballon change de porteur. Le défenseur tente au plus un tacle par confrontation ; un autre défenseur, non engagé, peut encore tacler.
- Un tacle raté élimine le défenseur pendant 1,5 s, même dans une nouvelle confrontation. Durée réelle : non trouvée ; c'est un ordre de grandeur validé par le propriétaire.
- Mesures sur 20 matchs (après les correctifs de revue : fin de confrontation aussi quand le ballon devient libre) : 38,4 tacles, 15,1 passes/min, 2,04 s par joueur, possession d'équipe 14,8 s, 3,71 passes, 11,3 tirs par équipe, 3,65 buts. Sur 1 match : 74,5 % de passes réussies, 25,5 % chez l'adversaire (à surveiller au ticket 05).
- Écart accepté par le propriétaire (25/10/2026) : 3,65 buts par match pour une cible de 2-3,5, dans la marge de hasard sur 20 matchs (3,35 et 3,45 sur les mesures précédentes). Reporté au ticket 05.
