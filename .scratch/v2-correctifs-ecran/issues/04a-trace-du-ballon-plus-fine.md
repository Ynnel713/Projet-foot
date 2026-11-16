# 04a: Trace du ballon plus fine envoyée à l'écran (API et trace)

**Chantier :** `v2-correctifs-ecran` (audit du 16/11/2026, retour du propriétaire après un match à l'écran : « le ballon change de direction ou de vitesse sans avoir touché de joueur »). **Priorité :** P0 (immersion : défaut visible à chaque passe). **Catégorie :** affichage (moteur de jeu inchangé).

**Constat vérifié (16/11/2026, graine 20260923, 1re période de clubs[0] contre clubs[1]) :**
- Le moteur calcule à 0,1 s (`TICK_SECONDS`), mais l'API ne garde qu'une image sur 10 (`api/routers/v2.py:33`, `_RECORD_EVERY = 10`) : une image par seconde. L'écran trace une ligne droite entre deux images (`ui/src/components/match/trace.js`, `interpolatedTick`).
- Ballon libre en mouvement : virages de plus de 20° sans joueur à 1,5 m : **10 sur 6 423 pas au moteur** (0,2 %), mais **94 sur 589 images à l'écran** (16 %), sans joueur à 2 m de l'image où le ballon tourne. Le contact a eu lieu entre deux images : l'écran coupe le virage.
- Sauts de vitesse visibles (rapport de 1,6 ou plus entre deux secondes consécutives) : **413 sur 589 images**. Le ballon perd 40 % de sa vitesse par seconde (`BALL_FRICTION_PER_S = 0.6`), ce qui s'affiche en marches d'escalier.
- Poids mesuré d'un match de 90 min (ticks sérialisés par `_tick_out`, extrapolés depuis 10 min) : 1 im/s 17,2 Mo brut (2,8 Mo gzip) ; 2 im/s 34,4 (5,3) ; 5 im/s 86,1 (12,5) ; 10 im/s 172,3 (24,3). L'essentiel du poids vient des joueurs et de leurs intentions, pas du ballon.

**What to build:**
1. **Joueurs** : `_RECORD_EVERY` passe de 10 à **5** (2 images par seconde). Le poids double (34 Mo brut, 5 Mo gzip), ce qui reste acceptable. 5 im/s (`_RECORD_EVERY = 2`) coûterait 86 Mo brut : trop lourd pour le navigateur d'un téléphone.
2. **Ballon** : nouvelle piste `ball_track` dans `MatchTrace` (`v2engine/trace.py`), relevée à **chaque pas du moteur** (0,1 s) : minute, x, y, mode (sol ou aérien), porteur. Poids estimé : environ 2 Mo brut pour 90 min. Exposée par l'API (`MatchTraceOut`, et `match_progress` pour le rejeu en direct, à partir de `from_tick`).
3. Le rejeu en direct (`match_progress`, `tick_seconds = _TICK_SECONDS * _RECORD_EVERY`) et la règle du but entre deux images (`ui/src/utils/v2GoalBall.js`) restent justes avec le nouveau pas.
4. Le moteur ne change pas : seule la trace enregistrée s'enrichit. La valeur par défaut `record_every=10` de `simulate_match` reste inchangée pour les scripts et le banc de mesure.

**Hors de ce ticket :** interpolation courbe à l'écran (04b) ; physique du ballon (`v2-realisme/14a` à `14d`).

**Attributs :** aucun.

**Constantes validées par le propriétaire le 16/11/2026 (« je valide ») :** `_RECORD_EVERY` = **5** (directive du propriétaire : « 2 ou 5 ») ; piste du ballon à **chaque pas (0,1 s)**. Chiffre réel : sans objet (choix d'affichage).

**Blocked by:** aucun.

**Bloque :** 04b.

**Status:** livré (16/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : `MatchTrace.record` appelé à chaque pas pour la piste du ballon, sans toucher au sous-échantillonnage des joueurs ; schéma Pydantic étendu sans casser les champs existants ; tests d'API existants adaptables au nouveau pas.
Temps machine, non compté : suite complète ; une mesure du poids de la réponse sur un match.

## Acceptance criteria

- [x] `ball_track` présent dans la trace et dans la réponse de l'API, un point toutes les 0,1 s de match (écart maximal entre deux points 0,1 s, hors mi-temps)
- [x] Ticks des joueurs à 0,5 s d'intervalle (`tick_seconds` de la réponse = 0,5)
- [x] Poids d'un match de 90 min mesuré et rapporté : au plus 40 Mo brut et 7 Mo gzip
- [x] Rejeu en direct : `match_progress` renvoie la piste du ballon par tranches, sans trou ni doublon entre deux appels (test)
- [x] Le moteur ne change pas : mêmes empreintes de match qu'avant le ticket à graine fixée (score, événements), deux exécutions identiques
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (16/11/2026)

- `v2engine/trace.py` : `BallPoint` (minute, position, mode, porteur) et `MatchTrace.ball_track`, remplie par `record_ball`.
- `v2engine/match.py` : un `record_ball` à chaque pas, juste avant l'enregistrement sous-échantillonné des joueurs ; aucune lecture ni tirage aléatoire de plus. `record_every=10` reste la valeur par défaut de `simulate_match`.
- `api/routers/v2.py` : `_RECORD_EVERY` 10 → 5 ; `BallPointOut` et `ball_track` dans `MatchTraceOut` et `MatchProgressOut`. Rejeu en direct : curseur propre au ballon (`from_ball`, renvoyé en `first_ball`) plutôt qu'un découpage déduit de `from_tick` : les points du ballon d'une image pas encore enregistrée arriveraient sinon en double ou manqueraient. Positions arrondies au centimètre (ticks et piste du ballon) et minute du ballon à 1e-5 : sans arrondi, la réponse pesait 40,5 Mo brut, au-dessus du plafond.
- `ui/` : `getV2Match(id, fromTick, fromBall)` ; `V2Match.jsx` accumule `ball_track` (que l'écran lira au 04b) ; `START_BUFFER_TICKS` 60 → 120 pour garder une minute de match calculée avant le démarrage (même valeur produit, exprimée au nouveau pas) ; commentaire du pas dans `v2GoalBall.js` (règle inchangée, elle lit les minutes).

**Mesures (graine 20260923, clubs[0] contre clubs[1], 90 min, `record_every=5`) :**
- Empreintes du moteur identiques avant (HEAD `fc611ad`) et après, sur deux exécutions : score 2-0, buts 12,11 et 80,17 min, 1 449 événements (sha256 `665e4bcccb305f9b`), tirs (`6d391390d18cbe72`), positions des ticks (`b1f244c82a518251`), temps additionnel 3 et 4 min.
- Piste du ballon : 58 200 points, écart constant de 0,1 s ; 11 640 images des joueurs (0,5 s).
- Poids de `MatchTraceOut` : **33,9 Mo brut, 3,0 Mo gzip** (piste du ballon : 4,2 Mo brut, 0,4 Mo gzip).

**Tests ajoutés (`tests/test_v2engine_trace.py`) :** piste à chaque pas et cohérente avec les images (match de 2 min) ; rejeu en direct par tranches sans trou ni doublon, calcul arrêté au milieu d'une tranche ; arrondis de la piste et des ticks ; deux images par seconde. Adapté : `test_product_and_bench_use_the_same_step` (0,5 s).

**Suite complète :** 3 177 passés, 0 ignoré, 14 désélectionnés (attendu 3 172 + 5 tests ajoutés), 12 min 54. UI : `npm run build` OK, `npm run lint` 0 erreur, 5 avertissements (inchangé).

**À vérifier à l'écran :** démarrage du rejeu en direct (une minute calculée), lecture fluide à x8 et x16, but marqué entre deux images.

**Durée :** estimée 1 h 50 (20/40/30/20) ; réelle environ 20 min de travail effectif (analyse 5, développement 7, tests 4, intégration et vérifications 4), à l'horloge de la session, non chronométrée ; écart − 82 %. Cause : le changement est resté local (un appel dans la boucle, un champ de trace, deux schémas d'API), les tests existants n'ont presque pas eu à être adaptés (un seul) et le choix d'un curseur propre au ballon a évité tout découpage délicat du rejeu en direct ; l'estimation supposait une adaptation plus large de l'API et de ses tests. Temps machine hors total : trois matchs de 90 min pour les empreintes et le poids (environ 2 min chacun, deux en parallèle), suite complète 12 min 54.

## Comments

- **16/11/2026, passage 1** — Expert : `APPROVED`. QC : `VALIDÉ`. Clôture journalisée : `VALIDÉ` (expert APPROVED, QC VALIDÉ). Anomalies bloquantes : aucune. Points facultatifs de l'expert : A1, ligne du registre des durées absente → ajoutée à la clôture ; A2, `docs/PLAN_V2.md` → mis à jour (suivi documentaire, hors fichiers revus). Réserves non bloquantes du QC : critère 6 hors diff (traité ici) ; `record_every=5` en dur dans le test de piste. Note de l'expert pour le 04b : `BallPointOut` n'a pas de champ `dead`, à ajouter si l'écran doit atténuer le ballon entre deux images.
