# 03b1: Gardien : l'arrêt lit Reflexes et One on Ones (levée de la dérogation A8)

**Découpé du ticket `03b` le 22/11/2026** (décision du propriétaire). Gardien moyen : médiane des gardiens de Ligue 1 de la base (Reflexes 75, One on Ones 75, Handling 60) ; un gardien sans note (effectif synthétique, copie neutre de l'xG) vaut le gardien moyen.

**What to build:** Reflexes règle le temps de réaction du gardien sur tir (`shooting.KEEPER_REACTION_S`, aujourd'hui le même pour tous) : il compte surtout de près, où le ballon arrive avant le plongeon. One on Ones règle sa portée debout en face-à-face (`gardien.face_to_face` au moment du tir : couvrir, rester debout). La note mélangée du gardien (dérogation A8, `shooting._keeper_rating`) disparaît de `shot_probability`. Même loi à la résolution (`match._keeper_reaches`) et à l'évaluation (`physical_shot_chance`, décision et xG) ; l'xG neutre et l'xG après frappe gardent le gardien moyen. L'arrêt entre dans la garde probabiliste (`tests/test_v2engine_garde_probabiliste.py`, test d'écart connu retiré).

**Attributs :** Reflexes (temps de réaction sur tir), One on Ones (portée debout en face-à-face). Rayon : `docs/CARTE_ATTRIBUTS_V2.md`, test de rayon à jour.

**Blocked by:** `v2-realisme/03f` (livré le 22/11/2026).

**Bloque :** `03b2`, `v2-realisme/03l`.

**Status:** livré (22/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : une constante par attribut, centrée sur le gardien moyen ; l'arrêt reste jugé à la portée (pas de nouveau tirage).
Temps machine, non compté : suite complète (environ 17 min) ; 50 matchs appariés (environ 30 min).

## Acceptance criteria

- [x] Constantes proposées au propriétaire avant le code (chiffres réels sourcés ou « non trouvé »)
- [x] Scène contrôlée : même tir, gardien Reflexes 99 / 75 / 40 : chance d'arrêt décroissante, écart plus grand de près que de loin ; face-à-face, One on Ones 99 / 75 / 40 : idem ; gardien moyen identique au moteur d'avant (mêmes empreintes à graine fixée avec gardiens sans note)
- [x] Dérogation A8 levée : `_keeper_rating` supprimé, carte et test de rayon à jour, arrêt dans la garde probabiliste
- [x] 50 matchs appariés : buts et part des cadrés arrêtés, avant / après
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [x] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée ; compte de la suite comparé à l'attendu

## Résultats (22/11/2026)

**Constantes** (délégation permanente du propriétaire, « Je valide automatiquement toutes tes recommandations ») : gardien moyen 75 (médiane des gardiens de Ligue 1 de la base) ; Reflexes 0,004 s par point autour de 0,30 s, bornes 0,18 à 0,45 s (99 : 0,204 s ; 40 : 0,44 s) ; One on Ones 0,0085 m par point autour de 1,0 m de portée debout, bornes 0,6 à 1,25 m (99 : 1,204 m ; 40 : 0,70 m), en face-à-face seulement (tireur à 25 m au plus, aucun défenseur sur la ligne de tir). Repères réels (temps de réaction d'un gardien selon son niveau) : non trouvés ; pente choisie pour qu'un gardien à 99 plonge encore sur un tir de 8 m (première pente de 0,0025 s par point écartée : aucun effet à 8 m).

**Scène contrôlée** (`tests/test_v2engine_arret_notes_gardien.py`, 6 tests) : chance de but strictement décroissante avec Reflexes à 10, 12 et 16 m ; à 8 m seul le 99 diffère, à 6 m aucun ; écart à 12 m plus de 10 fois celui à 20 m, nul à 28 m. One on Ones : décroissant en face-à-face, sans effet avec un défenseur sur la ligne. Dans la boucle de match, même tir de 12 m : arrêté par Reflexes 99, but contre Reflexes 40.

**Gardien moyen inchangé** : deux matchs où aucun joueur n'a de note, moteur d'avant (`e323d41`) et d'après : mêmes scores et mêmes empreintes (`53cdf6a2…`, `48b58f6a…`).

**50 matchs appariés** (`.scratch/v2-attributs-restants/mesures/03b1-serie.py`, synthèse `03b1-synthese.py`) : buts 4,06 → 4,02 (écart apparié − 0,04 [− 0,68 ; + 0,60]) ; cadrés arrêtés 59,9 % → 59,6 % ; à moins de 10 m 47,6 % → 39,0 % (environ 1,3 écart-type, dans le bruit ; avant ce ticket les notes ne jouaient pas sur arrêté ou non, cause plausible : One on Ones sous 75 en face-à-face, gardiens affrontés à 71,6 en moyenne — explication corrigée après la réserve A2 de l'expert) ; répartition des arrêts capté / repoussé / claqué 53,7 / 30,7 / 15,7 % → 53,0 / 32,1 / 14,9 % (300 et 296 arrêts, réserve A1). Rejeu des 499 tirs jugés de la série après, notes réelles contre gardien moyen (élan et face-à-face ignorés) : 7 arrêts gagnés, 15 perdus ; Reflexes des gardiens affrontés : médiane 75, moyenne 71,6 (queue de gardiens à 55-65). Sur 50 matchs, l'écart entre gardiens forts et faibles ne se lit pas dans les taux bruts (bruit et sélection) ; l'effet est établi tir par tir.

**Déterminisme** : matchs 0 et 1 du banc rejoués deux fois, mêmes empreintes (`a58b8243…`, `371a48b7…`).

**Tests adaptés** : `test_v2engine_shooting.py` (le test des notes du gardien juge l'évaluation physique, gardien dans son but : `shot_probability` ne lit plus ses notes), bouchon de `keeper_reach_m` dans `test_v2engine_journal.py`, garde probabiliste (cas « arrêt »), rayon et garde des attributs (Handling en exception jusqu'au `03b2`).

**Suite complète** : 3 518 passés, 0 échec, 0 ignoré, 14 désélectionnés (3 509 au `03f` : + 6 tests d'arrêt, + 4 cas de garde « arrêt », − 1 test d'écart connu A8).

**Durée** : estimée 2 h (25/40/30/25), réelle environ 2 h 45 (30/55/45/35), + 38 %. Cause : pente de Reflexes recalibrée (aucun effet à 8 m), cas facile de la garde déplacé (25 → 16 m), deux tests oubliés révélés par la suite complète, vérification d'empreinte sans notes ajoutée. Temps machine hors total : deux séries de 50 matchs (1 h), deux suites complètes (32 min), vérifications (10 min).

## Comments

- **22/11/2026, passage 1.** Expert : `APPROVED_WITH_RESERVATIONS` (empreinte `06e3ea19…`). QC : `VALIDÉ`.
  - A1 [réserve] : la difficulté de l'arrêt (`shot_probability`, qui ne lit plus le gardien) déplace la part captée / repoussée / claquée sans mesure. Mesuré sur 50 matchs : 53,7 / 30,7 / 15,7 % → 53,0 / 32,1 / 14,9 %. Recontrôle et recalage reportés au `03b2` (critère ajouté). **Acceptée par le propriétaire** : « J'accepte A1 (Recommandé) — Clôture de 03b1 avec la réserve. La répartition capté / repoussé et les corners issus d'arrêts sont recontrôlés et recalés au 03b2. »
  - A2 [facultatif, corrigé] : explication de la baisse à moins de 10 m reformulée.
  - A3 [facultatif, vérifié] : aucun des 52 gardiens de Ligue 1 n'a de fiche partielle (2 sans fiche, qui valent le gardien moyen).
  - A4 [facultatif, corrigé] : carte précisée pour Reflexes (réaction aussi en face-à-face, portée debout par One on Ones).
  - Réserves QC non bloquantes : carte à indexer au commit (fait) ; baisse à moins de 10 m dans le bruit.
