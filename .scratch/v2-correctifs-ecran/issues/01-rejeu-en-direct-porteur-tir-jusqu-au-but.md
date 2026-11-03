# 01: Rejeu en direct, nom du porteur, tir qui va jusqu'au but

**What to build:** trois retours du propriétaire sur l'écran V2 (03/11/2026).

1. **Chargement trop long.** Un match V2 se calculait d'un bloc avant d'être affiché : environ 40 s de chargements à froid au premier match (fichier des joueurs ~30 s, entraîneurs ~9 s), puis 4 à 5 minutes de calcul.
   - Le match se calcule en tâche de fond (`POST /api/v2/matches/start`) et l'écran lit les images au fur et à mesure (`GET /api/v2/matches/{id}?from_tick=N`) : le rejeu démarre après 60 images (1 minute de match, quelques secondes de calcul). Le calcul va plus vite que le rejeu à x8 ; à x16 il peut être rattrapé, l'écran affiche alors « en attente… ». Intentions et décisions arrivent à la fin du calcul. La route d'origine `POST /api/v2/matches` est conservée.
   - Préchauffage des chargements à froid au démarrage de l'API (`api/main.py`, `v2.prewarm`).
   - Moteur 1,6 fois plus rapide sans changer le jeu : rejet rapide des paires éloignées dans `_resolve_player_collisions`, cache de `movement._lerp`, `Vec2.distance_to` sans vecteur intermédiaire. Même graine : mêmes positions et mêmes décisions qu'avant.
2. **But compté sans que le ballon arrive.** Le tir était résolu instantanément : le but comptait au départ du tir (jusqu'à 30 m), le ballon sautait au centre. Désormais un tir gagnant part vers le but à `SHOT_SPEED_MPS` (= `MAX_PASS_MPS`, 30 m/s, pas de constante nouvelle) et le but n'est compté qu'à l'arrivée sur la ligne. Les tirs ratés restent résolus comme avant (ballon au gardien) : leurs issues variées sont au ticket `v2-collectif/28`.
   - À l'écran (revue expert A1) : le moteur remet le ballon au centre dans le pas même où il franchit la ligne, et l'écran n'a qu'une image par seconde ; aucune image ne montrait donc le ballon dans le but. Entre les deux images qui encadrent un but, l'écran fait filer le ballon vers le but jusqu'à la minute du but (le score monte à cet instant), puis le laisse au fond jusqu'à l'image suivante (`ui/src/utils/v2GoalBall.js`). Moteur inchangé.
   - Relancer un match arrête le calcul du précédent (revue expert A2) au lieu d'empiler les calculs.
3. **Nom du porteur sous son rond.** La trace porte le porteur du ballon (`BallSnapshot.holder`) ; l'écran l'écrit sous son rond.

**Status:** livré (03/11/2026), validé expert + QC (réserves A1 et A2 du passage 2 acceptées par le propriétaire, voir Comments)

## Acceptance criteria

- [x] Rejeu démarré en moins de 10 s après le clic (vérifié à l'écran, AEK Athènes - Al-Ahli, API sur le port 8001)
- [x] Moteur : 4,2 à 5,2 → 2,8 à 3,5 ms par image de calcul (3 essais alternés, 3 minutes de match, graine 7), mêmes décisions (67) et même empreinte de positions
- [x] Test : un tir gagnant ne compte qu'à l'arrivée du ballon sur la ligne, 2 à 4 pas pour 8 m (`tests/test_v2engine_shooting.py`)
- [x] Test : l'API rend les images déjà calculées pendant le calcul, puis seulement les nouvelles (`tests/test_v2engine_trace.py`)
- [x] Nom du porteur affiché sous son rond (vérifié à l'écran)
- [x] `tests/test_v2*.py` + `tests/test_api_animation.py` : 429 passés ; `npm run lint` : 0 erreur, 5 avertissements (inchangé) ; `npm run build` OK
- [x] Suite complète, passage 1 : 2296 passés, 13 désélectionnés (03/11/2026)
- [x] Écran, but : le ballon affiché est sur la ligne de but à la minute du but, file vers le but avant, reste au fond après (contrôle `goalBall`, 6 cas, et match réel via l'API, voir Comments)
- [x] Test : relancer un match arrête le calcul du précédent (`error = "annulé"`, `tests/test_v2engine_trace.py`)
- [x] Suite complète, passage 2 (après corrections A1-A2) : 2297 passed, 13 deselected
- [x] Vu à l'écran par le propriétaire : ballon entrant dans le but, score affiché à son arrivée (réserve A1 du passage 2, acceptée par le propriétaire : « J'accepte A1 et A2 »)

**Point de vigilance :** les mesures de référence V2 qui comptent des buts sont décalées (le but arrive environ 1 s plus tard, et le jeu continue pendant le vol du ballon) ; à refaire avec le ticket 28, qui change de toute façon le tirage des tirs.

## Comments

- **03/11/2026, passage 1** (base hors branche `f060d7f`, empreinte `44b58f32`) : expert REJECTED, QC VALIDÉ ; clôture non validée.
  - A1 (bloquant) : le ballon n'était jamais montré dans le but à l'écran, le score montait pendant qu'il glissait vers le rond central. Corrigé côté écran (`ui/src/utils/v2GoalBall.js`).
  - A2 (réserve) : calculs en tâche de fond jamais annulés. Corrigé : un nouveau lancement arrête le précédent.
  - A3 (facultatif) : tir gagnant encore en vol au dernier tick non compté (≈ 1 s sur 5 400). Non traité, négligeable.
  - A4 (facultatif) : case « suite complète » à mettre à jour. Fait.
  - A5 (facultatif) : porteur retrouvé par son nom (homonymes entre équipes). Non traité, peu probable.
  - Conseils de l'expert appliqués d'office, selon la consigne du propriétaire (« je valide automatiquement les conseils des experts »).
  - Vérification A1 sur un match réel (AEK Athens - Al-Ahli SFC, 2-1, API du dépôt) : pour les 3 buts, l'image suivante place le ballon au rond central (52,5 ; 34) ; le ballon affiché est à mi-chemin du but avant la minute du but, sur la ligne (105 ; 34) ou (0 ; 34) à cette minute, et y reste jusqu'à l'image suivante.
- **03/11/2026, passage 2** (base `f060d7f`, empreinte `593b576d`) : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ ; suite complète 2297 passés, 13 désélectionnés.
  - A1 (réserve) : vérification visuelle d'un but par le propriétaire. Acceptée : « J'accepte A1 et A2 ».
  - A2 (réserve) : un nouveau lancement annule tous les calculs en cours (deux onglets : le premier échoue). Acceptée : « J'accepte A1 et A2 ». Correctif éventuel : l'écran envoie à `start` l'identifiant du match à annuler.
  - A3 (facultatif) : les 3 buts du match de contrôle tombent tous sur un instant d'image ; à examiner avec le ticket `v2-collectif/28`.
  - A4 (facultatif) : reliquats A3 et A5 du passage 1, négligeables.
- **03/11/2026, passage 3** (base HEAD `8824529`, empreinte `9cb50ad1`) : même code, revu sur HEAD pour un commit ne portant que ce ticket (tickets 10, 14, 16 mis de côté le temps du commit). Expert APPROVED_WITH_RESERVATIONS (A1-A2 du passage 2, déjà acceptées : « J'accepte A1 et A2 »), QC VALIDÉ ; suite complète sur HEAD + ticket 01 seul : 2267 passés, 13 désélectionnés, 0 échec. À la réintégration des tickets 10, 14 et 16 : suite complète, au moins 2297 passés attendus.
