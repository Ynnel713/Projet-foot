# 04: Anticipation — réagir avant l'action

**What to build:** aujourd'hui un joueur ne réagit au ballon libre que lorsqu'il est déjà proche (`CHASE_RADIUS_M`). Anticipation le fait partir plus tôt vers l'endroit où le ballon VA arriver (passe adverse, rebond, ballon perdu), et permet d'intercepter une passe sur sa trajectoire, ce qui n'existe pas encore (guide, Anticipation).

**Blocked by:** None.

**Status:** livré (24/10/2026), validé QC

- [x] Les interceptions de passe existent, et un joueur à Anticipation haute en réussit mesurablement plus
- [x] Sur ballon libre, un joueur à Anticipation haute court vers le point d'arrivée du ballon, pas vers sa position actuelle
- [x] Effet probabiliste, jamais binaire ; courbe partagée `attributes.success_probability`/`duel_probability` (neutre entre 45 et 55), pas de courbe propre
- [x] (sans objet : pas de poids par poste dans ce ticket) Poids par poste déclaré via `attributes.register_weights` quand l'importance dépend du poste (guide, §2)
- [x] Joueur sans cet attribut : repli neutre (60), sans erreur
- [x] Mesure sur matchs simulés : écart observable entre note haute et note basse, à situation égale (critère chiffré proposé au propriétaire avant le code)
- [x] Constantes produit (seuils, amplitudes) proposées et validées par le propriétaire avant implémentation
- [x] Suite V2 verte ; V1 inchangée

**Constantes (validées 24/10/2026)** : lecture d'une passe 99 -> 80 %, 55 -> 40 %, 11 -> 10 % ; couloir de lecture 8 m autour de la trajectoire (et seulement s'il peut y être avant le ballon) ; avance sur le ballon libre 99 -> 100 %, 55 -> 50 %, 11 -> 0 % du chemin vers son point d'arrêt. Critère : Anticipation 90 au moins 1,5 fois plus d'interceptions que 30, en match.

**Mesures (24/10/2026, `scripts/measure_v2_decisions.py`)** : interceptions par match, Anticipation 90 -> 631,8, Anticipation 30 -> 393,0 (x1,6, critère atteint ; 4 matchs par config). Calibration sans retouche : 13,8 tirs par équipe, 2,17 buts par match (6 matchs).

**Constat hors périmètre** : le volume de ballons perdus est irréaliste (~27 % des passes), mais il existait AVANT ce ticket (427 par match avec l'anticipation désactivée, 3 matchs) : passes imprécises et adversaires qui foncent sur tout ballon à moins de 15 m. À traiter à part (phase 6, défense organisée, ou réglage de la précision des passes).
