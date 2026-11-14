# 24a: Banc : écart entre notes proches (70 contre 80), attribut par attribut

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026). **Priorité :** P1, avant la calibration finale (`v2-collectif/22a` à `22c`). **Catégorie :** mesure.

**Constat vérifié (14/11/2026, calcul sur les fonctions du moteur) :** les actions probabilistes passent par `attributes._cubic_curve` (forme t³). Elle est plate au centre et centrée sur 55, alors que la base est centrée sur 60 à 65 (485 joueurs de Ligue 1 : médiane 60, 80 % des notes entre 35 et 75 ; entre 60 et 90 pour les attributs du poste). Conséquence, sur un écart de 10 points :

| Mécanisme | 50 | 60 | 70 | 80 | 90 |
|---|---|---|---|---|---|
| Passing : passe précise (difficulté 60) | 49,3 % | 50,0 % | 50,7 % | 55,9 % | 69,8 % |
| Tackling : tacle gagné (porteur 60) | 49,4 % | 50,0 % | 50,6 % | 55,0 % | 66,9 % |
| Dribbling : garder le ballon au contact | 83,0 % | 83,0 % | 83,5 % | 85,2 % | 89,0 % |
| Decisions : meilleur choix | 70,0 % | 70,0 % | 71,0 % | 74,6 % | 82,6 % |
| Finishing : facteur d'exécution du tir | 0,994 | 1,000 | 1,006 | 1,049 | 1,157 |
| Pace : vitesse max (linéaire) | 30,0 | 31,3 | 32,7 | 34,0 | 35,3 km/h |
| First Touch : contrôle orienté (linéaire) | 47 % | 53 % | 59 % | 64 % | 70 % |

Entre 60 et 70, les attributs techniques, mentaux et de duel ne font presque aucune différence ; entre 70 et 80, très peu. Or c'est là que se trouvent presque tous les joueurs. Les tests de profils du banc ne comparent que 99 et 11 (`measure_v2.HIGH, LOW`) : l'effet en match de notes proches n'a jamais été mesuré.

**Exigence du propriétaire (14/11/2026) :** « J'aimerais qu'il y ait une réelle différence entre un joueur qui a 70 et un joueur qui a 80. Peu importe la caractéristique [...] La majorité, c'est entre 60 et 80, ou voire 90. Et du coup, c'est là que doivent se concentrer les différences pour le réalisme. »

**What to build:** Un banc qui mesure l'écart produit par deux notes proches, attribut par attribut, et la mesure de référence (avant le 24b).
- `scripts/measure_v2.py --profil <Attribut> --niveaux 80 70` : même plan d'expérience que le test de profils actuel (affiche jouée deux fois, rôles inversés, une équipe à la note haute, l'autre à la note basse), mais avec deux niveaux choisis. Défaut inchangé : 99 contre 11.
- Pour chaque attribut lu par le moteur (liste de `docs/CARTE_ATTRIBUTS_V2.md`, colonne « branché »), un indicateur cible déjà au banc : celui que l'attribut doit faire bouger (Passing : passes réussies ; Tackling : tacles gagnés ; Finishing : conversion ; Dribbling : pertes en conduite ; First Touch : contrôles ratés et temps de possession ; Decisions : écart au meilleur choix ; Pace : course au-dessus de 25 km/h ; etc.), avec son écart haut / bas et son intervalle de confiance.
- Une table de scène (sans match) : pour chaque fonction du moteur qui lit un attribut, sa valeur à 50, 60, 70, 80 et 90 (le tableau ci-dessus, complété, généré par un script `scripts/attribute_curves.py`), qui servira d'avant / après au 24b.
- Rapport : `docs/INDICATEURS_V2.md`, section nouvelle ; liste des attributs dont l'écart 70 / 80 n'est pas significatif en match.

**Attributs :** tous ceux lus par le moteur V2 (mesure seule).

**Blocked by:** rien.

**Bloque :** 24b.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : le forçage d'attribut du banc (`_force_attribute`) accepte deux niveaux quelconques sans autre changement ; une vingtaine d'attributs branchés.
Temps machine, non compté : un attribut = 20 matchs (10 affiches jouées deux fois) ; une vingtaine d'attributs, environ 10 à 12 h en tout sur 4 processus. À découper en lots, ou à limiter aux attributs les plus lus (Passing, First Touch, Technique, Dribbling, Tackling, Finishing, Decisions, Composure, Anticipation, Positioning, Pace, Acceleration, Agility, Strength) si la durée est trop longue : à décider au lancement.

## Tests

- **Unitaires :** `--niveaux 80 70` force bien 80 et 70 (et le défaut reste 99 / 11) ; la table des courbes reproduit les valeurs de `attributes.success_probability` et `duel_probability`.
- **Statistiques (séries de matchs) :** 20 matchs par attribut, écart haut / bas avec intervalle de confiance.

## Acceptance criteria

- [ ] `--niveaux` ajouté au banc, défaut inchangé (99 / 11), testé
- [ ] Table des courbes à 50, 60, 70, 80, 90 pour chaque fonction qui lit un attribut, générée par script
- [ ] Mesure 70 contre 80 en match pour chaque attribut retenu, avec intervalle de confiance, rapportée dans `docs/INDICATEURS_V2.md`
- [ ] Liste des attributs sans écart significatif entre 70 et 80, transmise au 24b
- [ ] Aucun effet sur le jeu (mesure seule) : suite complète inchangée hors tests ajoutés
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
