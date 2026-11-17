# 0002 — Attributs multidimensionnels : un attribut, plusieurs contextes pondérés

- **Statut** : accepté (17/11/2026, propriétaire : « tout est validé »)
- **Amende** : ADR 0001, point 3 (« chaque attribut est rattaché à un seul temps »)
- **Chantier** : `.scratch/v2-attributs-contextes/`

## Contexte

Le moteur V2 lit 27 attributs. L'audit du 17/11/2026 montre que 11 d'entre eux ne servent qu'à un seul effet : Work Rate (pressing seulement), Positioning (erreur de placement dans le bloc), Decisions (choix du porteur et des remises, jamais en défense), Flair (idée de talonnade), Marking, Balance, Strength (duels seulement), Tackling, et la note du gardien qui agrège Reflexes, One on Ones et Handling. Seuls Anticipation, Off the Ball, Teamwork, Technique et Composure ont un rayon systémique.

Ce cloisonnement vient de l'outillage plus que d'un choix de jeu :
- la règle R1 de `docs/CARTE_ATTRIBUTS_V2.md` (« un effet, un attribut responsable ») et le point 3 de l'ADR 0001 rattachent chaque attribut à un seul temps du cerveau ;
- le test `tests/test_v2engine_rayon_attributs.py` tient une liste blanche de modules par attribut (`ALLOWED`) et refuse par défaut tout calcul qui combine plusieurs attributs (`TOLERATED_MIXES`, quatre dérogations) ;
- les poids des cumuls autorisés sont dispersés dans le code (Dribbling 0,6 + Technique 0,4 au ticket 08c, moyenne First Touch / Technique au 31a).

La règle R2 révisée du 13/11/2026 autorisait déjà le cumul de plusieurs attributs dans un geste ; l'outillage ne l'a pas suivie.

Dans un jeu de type Football Manager, un attribut a un rayon systémique : la Vision sert à la passe longue, à la lecture du pressing et, par la perception, à l'anticipation défensive ; le Work Rate au pressing, au repli et au soutien ; la détente à tout le jeu aérien.

## Décision

1. **Un attribut sert à plusieurs effets.** Un attribut non spécialiste intervient dans au moins deux contextes de jeu. Les spécialités (Finishing, Long Shots, Penalty Taking, Corners, Free Kick Taking, Long Throws, Kicking, Throwing…) peuvent rester dans un seul contexte : elles sont listées comme telles.
2. **Un contexte est une situation de jeu qui combine des attributs avec des poids.** Exemple : « lecture du pressing » = Vision 0,5, Anticipation 0,3, Decisions 0,2. Les poids d'un contexte somment à 1 ; ce sont des constantes produit, proposées au propriétaire avant d'être codées.
3. **Registre central.** Les contextes et leurs poids sont déclarés dans un seul module (`v2engine/contextes.py`), avec une fonction `contextual_rating(player, contexte)` qui lit chaque note par la façade `condition.effective_rating` (R6 : la fatigue et la forme s'appliquent partout, une seule fois). Aucun poids d'attribut n'est écrit ailleurs dans le moteur.
4. **R1 devient « un effet, un calcul ».** Un même effet (même situation, même changement mesurable) n'est calculé qu'une fois, par un seul contexte : le double comptage reste interdit. Un attribut présent dans plusieurs contextes n'est pas un double comptage.
5. **Les temps du cerveau restent** (ADR 0001) : un contexte appartient à un temps (perception, décision, exécution). Un attribut peut désormais apparaître dans plusieurs temps, par des contextes différents (Vision en perception pour scanner, en décision pour voir la passe).
6. **Garde automatique transformée** : le test de rayon ne refuse plus un mélange ; il vérifie le registre (chaque contexte documenté dans la carte, poids sommant à 1, aucune lecture d'attribut hors du registre et de la façade, pas deux contextes pour un même effet, chaque attribut non spécialiste dans au moins deux contextes).
7. **Introduction sans changement de jeu** : la création du registre reprend les poids existants à l'identique (mêmes empreintes à graine fixée). Chaque nouveau branchement d'un attribut dans un contexte est un ticket à part, avec constantes validées et mesure avant/après sur 50 matchs.

## Conséquences

- La carte des attributs gagne une section « Contextes » (contexte, temps du cerveau, attributs et poids, source ou « non trouvé », ticket) ; les règles R1 et R2 sont réécrites.
- Chaque ticket qui touche un attribut indique, dans sa ligne « Attributs », le contexte concerné et ses poids proposés.
- Ordre de déploiement validé le 17/11/2026 : registre (neutre), test de rayon transformé, puis contexte « lecture du pressing » au ticket `v2-collectif/15b` ; ensuite les lots Work Rate offensif, Decisions et Positioning en défense, Flair et goût du risque, Balance après contact ; séparation de la note du gardien au ticket existant `v2-attributs-restants/03b`.
- Risque : chaque branchement change le jeu et peut déplacer la calibration (buts, tirs, passes) ; la mesure avant/après et le banc de profils (`scripts/measure_v2.py --profil`) restent obligatoires. Le plafond d'écart entre 99 et 11 de la carte continue de s'appliquer.
