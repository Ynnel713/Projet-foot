# 03: Mi-temps et temps additionnel

**What to build:** Le match V2 tourne aujourd'hui d'un seul bloc de 90 minutes (`v2engine/match.py` l.402-403) : ni mi-temps, ni temps additionnel. Ajouter :

1. **Une mi-temps** : pause, changement de côté, coup d'envoi de la seconde période par l'autre équipe, récupération d'énergie à la pause (amplitude à soumettre au propriétaire).
2. **Un temps additionnel** à chaque période, dérivé des arrêts de jeu réels du match : buts, remplacements (ticket 05), remises en jeu et coups de pied arrêtés (v2-attributs-restants/02), gestion du temps de l'équipe qui mène (ticket 02, geste Stops Play). Tirage déterministe (sha256 d'une clé stable).
3. **Fin de période réaliste** : l'arbitre ne siffle pas la fin pendant qu'un corner, un coup franc ou un penalty déjà accordé n'a pas été joué ; l'action qui en découle va à son terme.

La trace expose la minute affichée (`45+N'`, `90+N'`) pour le rendu et la narration.

**Attributs :** aucun (Stamina via la récupération à la pause).

**Blocked by:** v2-attributs-restants/02 (remises en jeu : sans elles, les arrêts de jeu sont trop rares pour un temps additionnel réaliste).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** ordre de grandeur réel à sourcer (environ 2-4 min en première période, 5-8 min en seconde depuis 2023, à confirmer). Avec seulement buts et remplacements, on n'atteindrait que 3-5 min par match. Les remises en jeu réduiront aussi le temps de jeu effectif (aujourd'hui 90 min de jeu continu contre environ 55-60 réelles) : à recalibrer dans v2-collectif/22. Prérequis du ticket 04.

- [ ] Deux périodes, changement de côté, coup d'envoi alterné, récupération à la pause mesurable
- [ ] Temps additionnel croissant avec le nombre d'arrêts de jeu ; distribution par période comparée à des données réelles sourcées (ou « non trouvé »), validée par le propriétaire
- [ ] Aucune période ne se termine avant l'exécution d'un coup de pied arrêté déjà accordé
- [ ] Même graine : même temps additionnel ; deux exécutions donnent la même empreinte de trace
- [ ] Minute affichée au format `45+N'` / `90+N'` dans la trace et l'UI V2
- [ ] Suite V2 verte ; V1 inchangée
