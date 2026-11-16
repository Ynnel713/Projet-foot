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

**Status:** à faire

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

- [ ] `ball_track` présent dans la trace et dans la réponse de l'API, un point toutes les 0,1 s de match (écart maximal entre deux points 0,1 s, hors mi-temps)
- [ ] Ticks des joueurs à 0,5 s d'intervalle (`tick_seconds` de la réponse = 0,5)
- [ ] Poids d'un match de 90 min mesuré et rapporté : au plus 40 Mo brut et 7 Mo gzip
- [ ] Rejeu en direct : `match_progress` renvoie la piste du ballon par tranches, sans trou ni doublon entre deux appels (test)
- [ ] Le moteur ne change pas : mêmes empreintes de match qu'avant le ticket à graine fixée (score, événements), deux exécutions identiques
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
