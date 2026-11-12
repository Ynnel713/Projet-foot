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

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : `movement.TURN_RATE_RAD_S` = 360°/s (demi-tour en 0,5 s ; vitesse angulaire réelle du corps : non trouvée), `movement.FACING_RUN_SPEED_MPS` = 19,8 km/h (seuil de course rapide du banc) ; validées par délégation (voir Comments)
- [x] Cap tracé et affiché : `PlayerState.facing`, `trace.PlayerSnapshot.facing`, API `PlayerSnapshotOut.facing` (degrés), écran : trait blanc du rond vers l'avant (`ui/src/components/match/V2Pitch.jsx`), interpolé par le plus court côté et retourné en 2e période (`trace.js`)
- [x] Aucun effet sur le jeu (mesures identiques à graine fixée, hors nouveaux champs) : `measure_v2 2` identique au 18j hors temps de calcul (`07a-det1.txt` contre `18j-det1.txt`)
- [x] Temps de calcul rapporté : 60,2 → 62,8 s par match (moyenne de deux exécutions, deux processus en parallèle ; + 4 %)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`07a-det1`, `07a-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (voir Comments)

## Comments

**12/11/2026, lancement.** Estimation annoncée : 2 h 10, confiance moyenne ; découpage écarté (la spec le déclare indissociable : un mécanisme et son test). Délégation du propriétaire (« enchaine les les uns après les autres. Je valide automatiquement toutes tes recommandations et les conseils d'experts ainsi que les commits si les conditions le permettent donc ne me sollicite pas »).

**12/11/2026, constantes (recommandées et validées par délégation).** Vitesse angulaire maximale du corps 360°/s, commune à tous en attendant Agility (07f) : ordre de grandeur (demi-tour en 0,5 s), vitesse réelle non trouvée. Le corps regarde le sens de course au-dessus de 19,8 km/h (seuil de course rapide des indicateurs), le ballon sinon. Cap de départ : vers le rond central (au point central, vers le but adverse).

**12/11/2026, implémentation.** `movement.turn_toward` (rotation bornée par le plus court côté), `movement.desired_facing`, `step(..., look_at=)` (le ballon, passé par `match._step_player`) ; `match._facing_at_kickoff` ; champ `facing` dans `PlayerState` et `PlayerSnapshot` ; API en degrés ; écran : trait d'orientation. Aucun module ne lit le cap (07b, 07c, 07e le brancheront). Non fait : retrait du paramètre `minute` inutilisé de `step` (note « ponytail » de `match._step_player`), 38 appels dans les tests, hors périmètre.

**12/11/2026, mesures.** Jeu identique au 18j à graine fixée (`measure_v2 2`, toutes les lignes hors temps de calcul) ; déterminisme sur deux exécutions ; temps de calcul + 4 %. UI : `npm run build` OK, `npm run lint` 0 erreur, 5 avertissements (inchangé). Tests : 10 ajoutés (`tests/test_v2engine_orientation.py` : demi-tour en 180° / vitesse angulaire à un pas près, rotation bornée et côté court, ballon ou sens de course, déplacement inchangé, cap de départ, trace et API, match simulé).

**12/11/2026, suite et écran.** Suite complète : 2 785 passés, 0 ignoré, 14 désélectionnés (2 775 + 10 ; `.scratch/v2-realisme/mesures/07a-suite.txt`) ; `CLAUDE.md` mis à jour. Capture de l'écran V2 (`.scratch/v2-realisme/mesures/07a-ecran.png`, Al-Ahli contre Al-Hilal, début de match) : trait d'orientation sur les 22 joueurs, la plupart tournés vers le ballon. Reste à vérifier à l'écran par le propriétaire : lisibilité du trait, rotation fluide en lecture (interpolation par le plus court côté), retournement en 2e période.

**12/11/2026, passage 1.** Expert : APPROVED (facultatifs : A1, seuil de 19,8 km/h sans hystérésis, flottement visuel possible, à traiter quand le cap sera branché au 07b ou au 07c ; A2, cap visé avec la position du ballon d'avant le pas, décalage d'un pas sans conséquence). QC : VALIDÉ. Clôture : VALIDÉ. A1 reportée en commentaire au 07b et au 07c.

**Durée.** Estimée 2 h 10. Réelle environ 1 h 50, non chronométrée (analyse 20 min, développement 35 min, tests 20 min, intégration et vérifications 35 min, dont la capture d'écran) : − 15 %. Temps machine hors total : 2 x 2 matchs (déterminisme et temps de calcul), suite complète (7 min), match V2 à l'écran.
