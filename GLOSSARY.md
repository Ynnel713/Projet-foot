# Glossaire Simulafoot

Termes du domaine, tels qu'employés dans le code, les tickets et la documentation.

## Moteur V2 — cerveau du joueur (ADR 0001)

- **Perception** : ce qu'un joueur détecte à un instant (porteur, ballon, trajectoire, passe lue, coéquipiers vus). Attributs : Vision, Anticipation, Concentration.
- **Interprétation** : lecture de la situation qui donne au joueur son **rôle** à cet instant.
- **Rôle** : la fonction d'un joueur à un instant : porteur, appel, soutien, receveur visé, lecture de passe, ballon libre, presseur, replacement, tenir sa place (en possession, le joueur sans appel qui garde sa place de référence ; seuls 2 à 3 coéquipiers du porteur, choisis selon leur rôle et leur proximité du ballon, font un appel). Un rôle n'est pas un poste (le poste est fixe, le rôle change à chaque instant). **Gardien** (ticket v2-realisme/03a) : rôle propre du gardien, qui ne passe plus par la règle générale (ni presseur ni soutien) ; quatre états tracés dans la raison de son intention : placement (il tient sa place), sortie (ballon libre à sa portée, ou le plus proche de son équipe), intervention (passe pour lui ou passe lue), relance (il a le ballon).
- **Décision** : le choix de l'action, de la cible et de l'intensité. Attributs : Decisions, puis les tendances (Flair, Teamwork…).
- **Exécution** : la réalisation du geste ou du déplacement, avec sa qualité. Attributs techniques et physiques.
- **Intention** : la sortie du cerveau à chaque tick : rôle, action, cible, intensité, raison. Enregistrée dans la trace.
- **Intensité** : part de la vitesse maximale du joueur utilisée pour un déplacement (0 à 1).
- **Journal des décisions** : liste des décisions du porteur (instant, action, cible, options envisagées, meilleure option prise ou non). Les « options envisagées » sont les types d'action possibles (conduire, tirer, une passe vers le meilleur coéquipier vu), au plus trois.
