# 02: Intensité de course selon la situation et le mental du joueur (fin du sprint permanent)

**What to build:** défaut T1 de la revue : `movement.step` vise toujours la vitesse max, donc tout le monde sprinte en permanence. Introduire une **intensité de course** (trot, course soutenue, sprint) choisie à chaque instant selon la situation ET le profil mental du joueur.

**Principe validé par le propriétaire (25/10/2026) : la capacité physique et l'envie sont deux choses distinctes.**
- **Les attributs physiques ne donnent que la capacité.** Pace = vitesse maximale, et rien d'autre. Acceleration = temps pour l'atteindre. Stamina = réserve d'énergie.
- **Les attributs mentaux décident du volume et de l'intensité des efforts**, c'est-à-dire quand et combien le joueur utilise cette capacité :
  - **Work Rate** : les efforts sans ballon (pressing, repli, couverture). Un joueur bas sprinte peu, il est surtout actif quand il a le ballon, il fait « semblant » de presser (il approche sans engager, à l'économie). Un joueur haut ne compte pas ses efforts. La contrepartie du guide : un Work Rate haut avec une Stamina basse épuise le joueur avant la 60e.
  - **Off the Ball** : le volume et l'intensité des appels de balle (combien d'appels, au trot ou en sprint). Il complète le ticket v2-cerveau-joueurs/03, qui ne règle aujourd'hui que le choix de l'espace.
  - **Teamwork** : l'effort pour tenir et reprendre sa place dans le bloc (repli à sa position).
  - **Determination** : garder l'intensité quand le score est défavorable ou en fin de match.
  - **Aggression** : l'engagement du pressing une fois arrivé au contact (lien avec le ticket socle 03).
- **Avec le ballon, tout le monde est actif.** L'intensité du porteur dépend de l'action (conduite, accélération), pas de Work Rate.

Réalité (Biology of Sport 2024, Di Mascio & Bradley 2013) : 9 à 14 km par match, 2 à 3 % de la distance au-dessus de 25 km/h, environ 3 % du temps au-dessus de 19,8 km/h.

**Blocked by:** 01 (le receveur doit déjà venir au ballon, sinon la mesure des sprints est faussée).

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Distance totale par joueur et par match dans la fourchette réelle 9-14 km
- [ ] Part de la distance au-dessus de 25 km/h dans la fourchette réelle 2-3 %
- [ ] Pace n'agit QUE sur la vitesse maximale (vérifiable : à Work Rate et situation égaux, deux joueurs de Pace différente courent la même distance, seul le plus rapide va plus vite en sprint)
- [ ] À situation égale, un joueur à Work Rate haut sprinte et presse mesurablement plus qu'un joueur à Work Rate bas (écart chiffré sur données réelles, à sourcer : distance des joueurs « box-to-box » contre celle des joueurs économes)
- [ ] À situation égale, un joueur à Off the Ball haut fait mesurablement plus d'appels, et plus intenses, qu'un joueur à note basse
- [ ] Un joueur à Work Rate haut et Stamina basse décroche plus tôt en fin de match qu'un joueur à Work Rate haut et Stamina haute
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [ ] Calibration remesurée après coup (tirs par équipe 8-15, buts par match 2-3,5, passes perdues) avec `scripts/measure_v2_decisions.py`
- [ ] Suite V2 verte ; V1 inchangée
