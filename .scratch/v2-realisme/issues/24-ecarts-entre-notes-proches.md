# 24: Vrais écarts entre notes proches (70 contre 80) : banc, puis nouvelle forme de courbe

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026). **Priorité :** P1, avant la calibration finale (`v2-collectif/22a` à `22c`), qui repartira des nouvelles courbes. **Catégorie :** mesure et moteur.

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

**What to build:** deux étapes dans un même ticket (un seul ticket, décision du propriétaire du 14/11/2026, malgré une estimation au-delà de 2 h).

**1. Banc et mesure de référence (avant la nouvelle courbe).**
- `scripts/measure_v2.py --profil <Attribut> --niveaux 80 70` : même plan d'expérience que le test de profils actuel (affiche jouée deux fois, rôles inversés, une équipe à la note haute, l'autre à la note basse), mais avec deux niveaux choisis. Défaut inchangé : 99 contre 11.
- Pour chaque attribut lu par le moteur (liste de `docs/CARTE_ATTRIBUTS_V2.md`, colonne « branché »), un indicateur cible déjà au banc : celui que l'attribut doit faire bouger (Passing : passes réussies ; Tackling : tacles gagnés ; Finishing : conversion ; Dribbling : pertes en conduite ; First Touch : contrôles ratés et temps de possession ; Decisions : écart au meilleur choix ; Pace : course au-dessus de 25 km/h ; etc.), avec son écart haut / bas et son intervalle de confiance.
- Une table de scène (sans match) : pour chaque fonction du moteur qui lit un attribut, sa valeur à 50, 60, 70, 80 et 90 (le tableau ci-dessus, complété, généré par un script `scripts/attribute_curves.py`), qui servira d'avant / après à l'étape 2.
- Rapport : `docs/INDICATEURS_V2.md`, section nouvelle ; liste des attributs dont l'écart 70 / 80 n'est pas significatif en match.

**2. Nouvelle forme de courbe : deux tests.** Remplacer la forme de la courbe partagée (une seule fonction, `_cubic_curve`, qui sert à `success_probability` et `duel_probability`), en comparant **deux variantes**, puis garder la meilleure :
- **Variante A, cubique recentrée et adoucie :** centre sur la médiane réelle des notes (environ 62, mesurée sur la base au moment du ticket), exposant 1,5 au lieu de 3 (signe gardé : `sign(t)·|t|^1,5`), mêmes bornes. Changement minimal de forme.
- **Variante B, logistique :** `baseline + amplitude · tanh(k · t)` (forme en S), pente maximale au centre, centre sur la médiane réelle ; `k` choisi pour que l'écart 70 → 80 soit au moins celui visé ci-dessous.
- **Objectif chiffré (à valider par le propriétaire avant le code) :** pour chaque mécanisme probabiliste, l'écart de 70 à 80 vaut au moins le tiers de l'écart de 50 à 99, et l'écart de 60 à 70 au moins le quart ; en duel, 10 points d'écart entre les deux joueurs donnent au moins 58 / 42 (contre 50,6 / 49,4 aujourd'hui).
- Les courbes linéaires des attributs physiques sont relues : elles restent ancrées sur des valeurs réelles mesurables (vitesse de pointe, temps d'accélération) ; on ne les rend plus raides entre 60 et 90 que si une source réelle le justifie (sinon : « non trouvé », et on garde).
- Les `baseline` et `amplitude` de chaque action ne bougent pas dans ce ticket : seule la forme change ; le recalage des niveaux (passes réussies, conversion, tacles…) revient à la calibration finale, qui repart de ces courbes.
- Choix entre A et B : sur la table des courbes de l'étape 1 (avant / après) et sur le banc de l'étape 1 (70 contre 80 en match, attribut par attribut), en retenant la variante qui fait le plus d'attributs significatifs entre 70 et 80 sans faire sortir les indicateurs globaux de leur repère (buts, passes réussies, tirs). Le propriétaire tranche s'ils sont proches.

**Attributs :** tous ceux qui passent par `success_probability` ou `duel_probability` (Passing, First Touch au contrôle, Tackling, Strength, Balance, Dribbling, Finishing, Long Shots, Decisions, Vision, Composure, Anticipation, Positioning, Marking, Teamwork, Off the Ball, Flair, Aggression, attributs du gardien…) ; aucun rayon ne change (`docs/CARTE_ATTRIBUTS_V2.md`).

**Blocked by:** rien.

**Bloque :** `v2-collectif/22a`, `22b`, `22c` (calibration finale : elle doit partir des nouvelles courbes).

**Status:** à faire (constantes à proposer avant le code de l'étape 2 : centre, exposant ou pente, objectif chiffré)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 1 h 05 (banc `--niveaux`, script des courbes ; deux variantes derrière un choix unique, puis la retenue seule) |
| Tests unitaires et comportementaux | 50 min |
| Intégration et vérifications | 1 h (mesure de référence, deux mesures A et B, choix, documentation) |
| **Total (travail effectif)** | **3 h 25** |

Confiance : moyenne. Hypothèses : le forçage d'attribut du banc (`_force_attribute`) accepte deux niveaux quelconques ; une seule fonction de forme à changer (`attributes._cubic_curve`) ; beaucoup de tests existants fixent des probabilités calculées avec la courbe actuelle et devront être recalculés (sans être supprimés ni affaiblis) : principal risque de dépassement. Au-delà de 2 h : découpage examiné (24a banc, 24b courbe), refusé par le propriétaire le 14/11/2026 (« Fais un seul ticket »).
Temps machine, non compté : banc 70 contre 80 à 20 matchs par attribut, trois fois (référence, variante A, variante B) : environ 10 à 12 h par passage pour une vingtaine d'attributs sur 4 processus, à limiter aux 14 attributs les plus lus (Passing, First Touch, Technique, Dribbling, Tackling, Finishing, Decisions, Composure, Anticipation, Positioning, Pace, Acceleration, Agility, Strength) si la durée est trop longue ; série appariée de 50 matchs pour les indicateurs globaux ; suite complète.

## Tests

- **Unitaires (banc) :** `--niveaux 80 70` force bien 80 et 70 (défaut inchangé, 99 / 11) ; la table des courbes reproduit `attributes.success_probability` et `duel_probability`.
- **Unitaires (courbe) :** variante retenue : écart 70 → 80 au moins le tiers de 50 → 99 ; 60 → 70 au moins le quart ; duel à 10 points d'écart au moins 58 % ; bornes jamais dépassées (jamais 0 ni 1) ; monotone ; symétrique en duel (p(a, b) + p(b, a) = 1).
- **Comportementaux (profils comparés) :** 70 contre 80, attribut par attribut, avant (courbe actuelle), variante A, variante B : plus d'attributs avec un écart significatif qu'avant.
- **Statistiques (séries de matchs) :** 50 matchs appariés avant / après la variante retenue : buts, xG, tirs, passes réussies, tacles, pertes rapportés, écarts expliqués.

## Acceptance criteria

- [ ] `--niveaux` ajouté au banc, défaut inchangé (99 / 11), testé
- [ ] Table des courbes à 50, 60, 70, 80, 90 pour chaque fonction qui lit un attribut, générée par script, avant et après
- [ ] Mesure de référence 70 contre 80 en match pour chaque attribut retenu, avec intervalle de confiance, rapportée dans `docs/INDICATEURS_V2.md`
- [ ] Constantes produit (centre, exposant ou pente ; objectif chiffré validé le 14/11/2026) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code de l'étape 2
- [ ] Variantes A et B mesurées sur la table des courbes et sur le banc 70 contre 80 ; choix argumenté (propriétaire s'ils sont proches)
- [ ] Variante retenue seule dans le code, objectif chiffré tenu (tests de courbe)
- [ ] Écart 70 / 80 significatif en match pour plus d'attributs qu'avant, rapporté attribut par attribut
- [ ] Indicateurs globaux mesurés avant / après (50 matchs appariés) ; écarts transmis à la calibration finale, aucun recalage de niveau ici
- [ ] Tests existants recalculés sur la nouvelle courbe, aucun supprimé ni désélectionné
- [ ] Rayon des attributs inchangé (`docs/CARTE_ATTRIBUTS_V2.md`), test de rayon vert
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**14/11/2026, objectif chiffré validé par le propriétaire** (« Je valide ») : pour chaque mécanisme probabiliste, écart de 70 à 80 au moins le tiers de l'écart de 50 à 99, écart de 60 à 70 au moins le quart ; en duel, 10 points d'écart donnent au moins 58 / 42 (50,6 / 49,4 aujourd'hui). Restent à proposer avant le code de l'étape 2 : centre (médiane réelle mesurée), exposant de la variante A, pente de la variante B. Ticket à réaliser dans une autre session.
