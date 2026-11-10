# 21: Adaptation au score, au temps et à la fatigue

**What to build:** Une équipe qui mène à la 85e ne prend plus les mêmes risques qu'à 0-0 ; une équipe menée avance son bloc et envoie plus de joueurs dans la surface. La fatigue modifie aussi les choix et la capacité à répéter les efforts. Reprend Determination (garder l'intensité quand le score est défavorable), reportée du ticket socle 02.

**Attributs :** Determination, Leadership (indirect), Stamina, Concentration.

**Blocked by:** 04, 12 ; `v2-realisme/20b` (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Determination et Leadership étaient prévus en phase 10 : ce ticket en avance la partie collective. L'adaptation au score doit être exposée comme des paramètres (minute de début, amplitude) que `.scratch/v2-coach-et-gestion-de-match/issues/02-gestion-du-score-selon-le-coach.md` module par le style du coach, sans seconde mécanique.

- [ ] Hauteur du bloc et prise de risque mesurablement différentes selon le score et la minute
- [ ] Mené 0-2 à la 80e, un joueur à Determination haute garde mesurablement plus d'intensité
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. La partie « la fatigue modifie les choix » est reprise par `v2-realisme/20b` (lucidité, Concentration dans sa condition de fatigue). Ce ticket garde le score, la minute, Determination et les trous de vigilance après un but. La capacité à répéter les efforts relève de `v2-realisme/12f` ; le bloc qui recule avec la fatigue, de `v2-realisme/20e`.
