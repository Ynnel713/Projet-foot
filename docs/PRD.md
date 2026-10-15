# PRD — Réalisme du mouvement collectif des joueurs

## Problème

Pendant une action rendue (but, occasion), les joueurs qui ne participent pas directement à l'action (coéquipiers et adversaires en arrière-plan) se tiennent alignés en rangées strictement régulières, comme figés dans une formation de défilé plutôt que dans un vrai match. Cet alignement persiste pendant toute la durée du clip, parce que les mouvements de ces joueurs pendant l'action restent trop faibles pour s'en écarter. Le propriétaire du projet l'a remarqué en relisant des clips fraîchement produits et le juge incompatible avec l'exigence de réalisme qu'il porte sur l'ensemble du projet. Ce défaut existe depuis l'origine du rendu animé ; il devient plus gênant à mesure que le rendu progresse en qualité ailleurs (physique du ballon, gestes, contrôles), ce qui le rend maintenant le point faible le plus visible à l'écran.

Au-delà du symptôme visuel, le mouvement des joueurs pendant l'action est aujourd'hui rudimentaire dans l'absolu : un joueur va d'un point A à un point B en ligne droite, sans à-coup ni relance, sans jamais sortir de son rôle scripté pour soutenir l'action, se replacer ou presser — alors qu'un vrai match est fait de ces mouvements permanents, influencés par le poste, les qualités du joueur et les consignes de l'entraîneur.

## Solution

Le mouvement de chaque joueur pendant une action rendue doit donner l'impression d'un joueur réel sur un terrain : jamais parfaitement aligné avec ses coéquipiers de la même ligne, en mouvement continu et crédible plutôt qu'en ligne droite figée, et capable d'initiatives qui reflètent son rôle et son profil — un latéral qui monte soutenir l'attaque, un attaquant qui vient prêter main-forte en replacement défensif, un mouvement de bloc qui respecte le dispositif choisi. Ces initiatives varient aussi selon le style de jeu de l'entraîneur (une équipe qui presse haut ne se comporte pas comme une équipe qui défend bas) et selon les qualités individuelles du joueur (endurance, sens du replacement, caractéristiques propres à son profil).

Le propriétaire doit pouvoir regarder n'importe quel clip, à n'importe quel moment de l'action, sans jamais retrouver cette impression de joueurs figés en rangs.

## Utilisateur cible

Le propriétaire du projet (Olivier), seul utilisateur à ce stade. Il consulte les clips produits par le moteur pour juger de leur réalisme avant de les considérer aboutis. Pas de boucle utilisateur externe : son propre jugement visuel, complété par des mesures chiffrées qu'il consulte, fait foi.

## User Stories

1. En tant que propriétaire, je veux que les joueurs d'une même ligne tactique ne soient jamais parfaitement alignés à l'image, afin que la scène ne ressemble plus à un défilé figé.
2. En tant que propriétaire, je veux que tous les joueurs (actifs dans l'action ou non) se déplacent de façon continue et fluide pendant tout le clip, sans à-coup ni arrêt net, afin que leur course paraisse humaine.
3. En tant que propriétaire, je veux que des joueurs non directement impliqués dans l'action puissent initier des mouvements de soutien (un latéral qui monte, un attaquant qui redescend aider), afin que l'action paraisse collective et pas seulement centrée sur les 2-3 protagonistes scriptés.
4. En tant que propriétaire, je veux que ces mouvements de soutien varient selon le poste et les qualités propres de chaque joueur, afin qu'un joueur rapide et endurant se comporte différemment d'un joueur lent ou peu impliqué défensivement.
5. En tant que propriétaire, je veux que le style de jeu de l'entraîneur de chaque équipe influence la hauteur du bloc et l'intensité de ces mouvements, afin qu'une équipe qui presse ne se comporte pas comme une équipe qui se replie.
6. En tant que propriétaire, je veux que deux lectures d'un même clip produisent exactement les mêmes positions, afin de conserver la garantie de reproductibilité déjà en place sur tout le reste du projet.
7. En tant que propriétaire, je veux que le résultat sportif de l'action (qui marque, qui est averti, qui sort) reste strictement identique à ce qu'il est aujourd'hui, afin que ce chantier ne touche qu'à ce qui se voit, jamais à ce qui compte pour le score.
8. En tant que propriétaire, je veux que l'affichage de la feuille de match avant le coup d'envoi continue de montrer une formation bien rangée et lisible, afin de ne pas perdre la lisibilité d'un schéma tactique au profit d'un réalisme qui n'a de sens que pendant le jeu.
9. En tant que propriétaire, je veux recevoir, pour chaque sous-partie de ce chantier, une mesure chiffrée du changement (avant/après) en plus de pouvoir le constater moi-même sur des clips, afin de juger objectivement qu'une sous-partie est terminée.
10. En tant que propriétaire, je veux être consulté avant que soit figée toute nouvelle valeur qui pilote ce comportement (seuils, amplitudes, profils d'entraîneur), afin de garder la main sur les choix qui définissent le style de jeu simulé.

## Critères de succès

- Pour un même échantillon de clips, une mesure chiffrée de la dispersion des joueurs d'une même ligne tactique est produite avant et après le chantier, et montre une dispersion strictement supérieure après.
- Sur ce même échantillon, aucun segment de déplacement d'un joueur ne présente plus d'arrêt net/saut de position d'une image à l'autre qu'aujourd'hui (mesure déjà suivie ailleurs dans le projet).
- Le propriétaire visionne un échantillon de clips après chaque sous-partie et valide explicitement qu'il ne perçoit plus l'effet "file indienne" sur cet échantillon.
- Rejoué deux fois, un même clip produit exactement les mêmes positions, image par image.
- Sur un échantillon de matchs rejoués avant/après, le score, les buts, les cartons et les remplacements restent identiques à l'image près.
- La feuille de match affichée avant le coup d'envoi n'est, à l'œil, pas modifiée par ce chantier.

## Hors périmètre

- Le chantier de géométrie macro des gabarits en cours ("chantier 1") : il continue sans changement jusqu'à sa fin, ce PRD ne le modifie pas et ne démarre qu'une fois celui-ci terminé.
- Le moteur qui détermine le résultat sportif du match (scores, buts, cartons, remplacements).
- Le rendu et la physique du ballon.
- L'interface (API, PWA) et l'affichage de la feuille de match avant le coup d'envoi — qui reste une formation bien rangée, volontairement non concernée par ce chantier.
- Les remplacements tactiques décidés par l'entraîneur en cours de match (rattachés à une décision produit distincte, déjà identifiée ailleurs dans le projet).
- Toute mesure comportementale validée sur des compositions synthétiques dans ce chantier n'est qu'une étape intermédiaire : la validation définitive sur des compositions réelles est hors périmètre de ce PRD et suivra séparément.

## Décisions d'implémentation

- Aucun comportement de ce chantier ne modifie le résultat sportif de l'action : but, passeur, cartons, remplacements restent décidés exactement comme aujourd'hui.
- Deux lectures d'un même clip produisent toujours exactement le même résultat : aucune variation n'est laissée au hasard d'une lecture à l'autre.
- Chaque équipe se voit attribuer un style de jeu d'entraîneur (par exemple pressing, offensif, défensif, contre-attaque, possession) qui influence la hauteur du bloc et l'intensité des mouvements de soutien ; ce style est déterminé de façon stable pour un même club, jamais tiré différemment d'un match à l'autre pour une même équipe dans les mêmes conditions.
- L'intensité et la fréquence des mouvements de soutien d'un joueur dépendent de son poste et de ses qualités individuelles déjà connues du projet (endurance, sens défensif, etc.) plutôt que d'être uniformes pour tous les joueurs d'un même poste.
- Un joueur en mouvement de soutien reste reconnaissable dans son secteur de jeu : son déplacement ne le fait pas apparaître à un endroit tactiquement absurde (un défenseur central ne se retrouve jamais mêlé aux attaquants adverses), même si l'amplitude de ses initiatives (dédoublement, repli) n'est pas bridée à une zone figée.
- Chaque sous-partie de ce chantier est livrée et validée séparément (mesure chiffrée + relecture visuelle), dans l'ordre : mouvement continu d'abord, puis initiatives de soutien, puis comportement collectif/profil d'entraîneur — jamais livrée en un seul bloc.
- Toute valeur chiffrée qui pilote ces comportements (seuils, amplitudes, définition des profils d'entraîneur) est proposée au propriétaire avant d'être figée dans le projet.

## Notes complémentaires

- Dépendance d'ordre : les initiatives de soutien et le comportement collectif n'ont de sens visuel que si le mouvement continu (sans à-coup) est traité en premier ; les sous-parties sont donc dépendantes entre elles dans cet ordre, pas interchangeables.
- Le concept de "style de jeu d'entraîneur" n'existe pas encore dans le projet aujourd'hui : sa définition (quelles valeurs possibles, comment chaque club en reçoit un) est elle-même un livrable de ce chantier, pas un prérequis déjà acquis.
- Risque de périmètre : la richesse souhaitée (initiatives fluides, influence du profil d'entraîneur et du joueur) est ambitieuse et peut révéler, une fois commencée, des sous-décisions supplémentaires à trancher avec le propriétaire — à traiter au fil de l'eau plutôt qu'à anticiper ici.
- Hypothèse : les compositions synthétiques utilisées pour mesurer ce chantier au fil de l'eau sont suffisantes pour juger du principe ; une validation définitive sur des compositions réelles de joueurs est supposée nécessaire avant de considérer l'ensemble du Bloc A terminé, mais n'est pas un blocage pour avancer sous-partie par sous-partie.
- Ce chantier consomme et remplace les points A1.1, A1.3 et A2 esquissés dans le plan d'architecture existant du projet, jusqu'ici non détaillés.
