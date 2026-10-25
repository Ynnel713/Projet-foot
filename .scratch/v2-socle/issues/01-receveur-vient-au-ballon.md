# 01: Le receveur vient au-devant de la passe

**What to build:** aujourd'hui, une fois la passe partie, le coéquipier visé continue sa course vers son espace (Off the Ball) ou retourne à sa place : le ballon arrive là où il ÉTAIT et le premier joueur venu le ramasse. Diagnostic du 25/10/2026 (2 matchs, 3 661 passes) : le receveur visé ne récupère le ballon que dans 17 % des cas, 54 % vont à un autre coéquipier, 29 % à l'adversaire. Correction validée par le propriétaire le 25/10/2026 : le receveur visé court vers le point d'arrivée de la passe, même mécanisme que l'adversaire qui lit la passe (`ball.readers`, ticket v2-cerveau-joueurs/04).

**Blocked by:** None (correction validée, premier ticket du socle).

**Status:** livré (25/10/2026), validé QC — critères chiffrés et recalibration reportés au ticket 04 (décision du propriétaire)

- [x] Le receveur visé vise le point d'arrivée de la passe tant que le ballon est en route, puis reprend son comportement normal dès qu'un joueur contrôle le ballon
- [x] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [ ] (REPORTÉ au ticket 04) Calibration remesurée après coup (tirs par équipe 8-15, buts par match 2-3,5, passes perdues) avec `scripts/measure_v2_decisions.py`
- [x] Suite V2 verte ; V1 inchangée

**Constantes et critères (validés 25/10/2026)** : le receveur vise le point de la trajectoire réelle du ballon qu'il atteint le plus tôt, à sa course normale ; il suit le vrai ballon si la passe est déviée. Critères : receveur visé au moins 50 % (17 % avant), passes perdues chez l'adversaire au plus 25 % (29 % avant).

**Règles ajoutées pendant le code** (signalées au propriétaire, conservées par sa décision du 25/10/2026) :
- une passe morte (ballon à moins de 0,5 m/s) ou un contrôle raté libère le receveur : sans cela le jeu se bloquait (20 passes en 2 matchs) ;
- sur un ballon libre, le joueur le plus proche de chaque équipe y va toujours, même au-delà de 15 m : sans cela un ballon mort loin de tous n'était plus disputé.
Règle essayée puis RETIRÉE : les autres coéquipiers laissent la passe au receveur (ils s'écartaient tous, 75 % des passes ratées finissaient chez l'adversaire).

**Mesures (2 matchs, diagnostic de passes ; 6 matchs pour la calibration)** : receveur visé 17 % -> 30 % ; passe chez l'adversaire 29 % -> 26 % ; tirs 18,7 par équipe et 4,0 buts par match (hors cibles).
**Critères 50 % / 25 % et recalibration REPORTÉS au ticket 04** (décision du propriétaire) : 39 % des passes partent encore de travers (précision moyenne 61 %, phase 2), ce qu'un receveur ne peut pas compenser ; la recalibration se fera une seule fois, en fin de socle.
