# 07a: Orientation du corps : état propre et rotation bornée

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** physique.

**Constat vérifié :** `PlayerState` (`movement.py:72`) n'a aucun champ d'orientation ; la direction du corps n'existe nulle part dans `v2engine/` (recherche « orient », « facing », « heading » : seul `decision.free_point` emploie `heading`, pour une direction de conduite).

**What to build:** Ajouter à chaque joueur un cap (direction du corps), distinct de sa vitesse, qui tourne vers une direction voulue (intention) à une vitesse angulaire maximale commune (valeur sourcée ou « non trouvé »). Par défaut il regarde le ballon ; en course rapide il regarde dans le sens de course. Tracé et transmis à l'écran.

**Hors de ce ticket :** effet sur le déplacement (07b), Agility (07f).

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 04h, 07b, 07c, 07e, 07f, 08a, 11d, `v2-collectif/31`, 03l (ajouté le 10/11/2026, audit de la roadmap).

**Status:** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : champ ajouté à `PlayerState` et à la trace ; rendu : simple trait d'orientation.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs (temps de calcul).

## Tests

- **Unitaires (scène contrôlée) :** demi-tour demandé : durée égale à 180° divisé par la vitesse angulaire, à un pas près
- **Intégration :** trace et API : cap présent

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : vitesse de rotation 360°/s (valeur réelle non trouvée), seuil de course rapide 19,8 km/h, cap face au but adverse au coup d'envoi et à la reprise, cap gardé quand le ballon est à moins de 0,1 m (validé le 12/11/2026, « ok pour les constantes »)
- [x] Cap tracé et affiché : `PlayerSnapshot.facing`, `PlayerSnapshotOut.facing`, trait au bord du rond à l'écran (`V2Pitch.jsx`), interpolé par le plus court chemin et retourné en 2e période (`trace.js`) ; capture `.scratch/v2-realisme/mesures/07a-ecran.png`
- [x] Aucun effet sur le jeu : 20 matchs sur 20 identiques avant / après hors cap (positions, vitesses, réserve, ballon, buts, tirs, décisions ; `.scratch/v2-realisme/mesures/07a-empreintes.txt`) ; test de scène : cap de départ opposé, mêmes empreintes
- [x] Temps de calcul rapporté : 1 077 s avant ; 1 079 et 1 140 s au passage 1 (+ 0,1 % et + 5,9 %, bruit de 5,7 % entre deux exécutions identiques) ; 1 082 et 1 109 s après correctif A1 (+ 0,5 % et + 2,9 %)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes (jeu et cap) sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 768 passés, 14 désélectionnés (2 759 au 18h + 9 ajoutés), 7 min 36 (après correctif A1) (`.scratch/v2-realisme/mesures/07a-suite.txt`)

## Comments

**12/11/2026, implémentation.**
- `v2engine/orientation.py` : `TURN_RATE_RAD_S` (360°/s), `FAST_RUN_MPS` (19,8 km/h), `BALL_DEADZONE_M` (0,1 m) ; `desired_facing` (sens de course au-dessus du seuil, sinon direction du ballon, sinon cap gardé), `turn_towards` (plus court chemin, au plus 36° par pas de 0,1 s), `kickoff_facing`.
- `PlayerState.facing` (radians, 0 = vers x croissant), recopié par `movement.step` ; tourné dans `match._step_player` après le déplacement, avec la position du ballon avant son pas. `step` et la vitesse ne lisent pas le cap. Mi-temps : replacé face au but adverse avec la position.
- Écran : traces enregistrées avant le 07a (sans `facing`) affichées sans trait.
- Tests : `tests/test_v2engine_orientation.py`, 7 tests (9 après le correctif A1) (demi-tour en 0,5 s à un pas près, plus court chemin et borne par pas, direction voulue, coup d'envoi, rotation bornée en scène, aucun effet sur le jeu en scène, cap dans la trace et l'API avec borne vérifiée à chaque pas d'un match de 2 min, mi-temps exclue et vérifiée à part).
- UI : `npm run build` OK, `npm run lint` 0 erreur, 5 avertissements (inchangé).
- Hors périmètre, non traité : le commentaire de `match.py` qui demande de retirer le paramètre `minute` de `step` « au premier ticket qui touche `step` » (le 07a ne change pas `step`, il y ajoute seulement la recopie du champ).

**12/11/2026, passage 1.** Expert : REJECTED (rapport hors dépôt, `07a-expert-1.md`). QC : non lancé (rejet de l'expert d'abord). Clôture : non demandée.
- A1 [bloquant] : le porteur entre 1 et 5,5 m/s se tournait dos à sa course (ballon recopié sur sa position du pas précédent). Corrigé : le porteur regarde où il va et garde son cap à l'arrêt (`desired_facing(..., holding=True)`), sans constante nouvelle ; tests `test_the_holder_faces_where_he_carries_the_ball_never_backwards` et `test_a_still_holder_keeps_his_cap`.
- A2 [réserve] : pas d'hystérésis au seuil de 19,8 km/h (le trait peut basculer d'un pas à l'autre). Acceptée par le propriétaire (« ok pour garder A2 en réserve au 07b ») : à traiter au 07b, valeurs à proposer.
- A3 [facultatif] : `PlayerSnapshotOut.facing` optionnel (`None` = pas de trait). Corrigé ; l'écran teste `!= null`.

**12/11/2026, passage 2.** Expert : APPROVED_WITH_RESERVATIONS (`07a-expert-2.md`, hors dépôt). QC : VALIDÉ. Clôture : VALIDÉ.
- A1 et A3 du passage 1 : corrigés et vérifiés (test de conduite du porteur, champ optionnel).
- A2 [réserve] : hystérésis au seuil de 19,8 km/h, acceptée par le propriétaire (« ok pour garder A2 en réserve au 07b ») ; au 07b : deux seuils ou maintien minimal du mode, valeurs à proposer, test de vitesse oscillant autour du seuil.
- À surveiller au 07b : porteur à vitesse quasi nulle mais non nulle (direction instable, amortie par la borne de rotation) ; part du temps de possession entre 1 et 5,5 m/s à chiffrer.
- QC, réserves non bloquantes : fins de ligne non vérifiables par le diff (fichiers en LF, gardées) ; attendu de la suite dans `CLAUDE.md` à mettre à jour (2 768 passés, 14 désélectionnés), non modifié dans ce ticket.

**Durée.** Estimée 2 h 10. Réelle environ 2 h 50, non chronométrée (analyse 30 min, développement 40 min, tests 40 min, intégration et vérifications 60 min) : + 31 %. Cause : rejet de l'expert au passage 1 (cap du porteur inversé), correctif, nouvelle série de 20 matchs et deuxième passage. Temps machine hors total : 4 séries de 20 matchs (environ 5 min chacune sur 4 processus), suite complète deux fois (8 min 05 et 7 min 36).
