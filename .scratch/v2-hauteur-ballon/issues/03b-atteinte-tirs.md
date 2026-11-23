# 03b: Interception selon la hauteur : tirs

**Découpé du ticket `03` le 23/11/2026** (décision du propriétaire). Référence : `03-interception-selon-hauteur.md` ; réserve A1 de l'expert au `02a2` (7 contres sur 348 au-dessus de 2,5 m, 2 arrêts sur 324 au-dessus de la barre, sur 50 matchs).

**What to build:** le contre (`match._blocked`) et l'arrêt par portée (`match._keeper_reaches`) lisent la hauteur réelle du tir au point de contact (`ShotEvent.block_z_m`, `keeper_z_m`, ticket `02a2`) avec l'atteinte du `03a` : un défenseur ne contre qu'un ballon à sa portée, le gardien n'arrête qu'un ballon à la portée de ses mains. L'issue des tirs peut changer (contres, arrêts) : mesurée.

**Attributs :** ceux du `03a` (taille, Jumping Reach) ; aucun nouveau.

**Blocked by:** `03a`.

**Bloque :** `02b` (recommandation de l'expert au `02a2` : aucun contre au-dessus de la tête à l'écran).

**Status:** livré (23/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h** |

Confiance : moyenne. Temps machine, non compté : deux séries de 50 matchs (environ 40 min chacune), suite complète (environ 17 min).

**Constantes :** celles du `03a` ; aucune nouvelle.

**Critères chiffrés** (posés avant le code) :
- scènes : tir au-dessus de l'atteinte d'un défenseur placé sur sa trajectoire : non contré, il va à la ligne ; même défenseur, tir bas : contré comme avant ; gardien hors de sa surface : tir au-dessus de sa tête non arrêté, tir bas arrêté ;
- 50 matchs mêmes graines : 0 contre et 0 arrêt au-dessus de l'atteinte du joueur (relevé : hauteur au contact, atteinte recalculée depuis la base pour le joueur du journal) ; contres, arrêts, buts, tirs au-dessus et à côté par match, écart apparié avec intervalle, écarts expliqués ;
- déterminisme à graine fixée ; suite complète au compte attendu.

## Acceptance criteria

- [x] Scènes : tir au-dessus de l'atteinte d'un défenseur sur sa ligne : non contré ; tir à portée : contré comme avant
- [x] 50 matchs : 0 contre et 0 arrêt au-dessus de l'atteinte du joueur ; contres, arrêts, buts avant/après, écarts expliqués
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [x] Déterminisme ; suite complète au compte attendu ; V1 inchangée

## Résultats (23/11/2026)

- **Périmètre élargi en cours de ticket** (annoncé : 1 h → 1 h 30, + 35 min de temps machine) : la première suite complète a donné 8 échecs dans `tests/test_v2engine_chance_tir.py` ; l'estimateur du tir (`shooting._flight_shares`, ticket `v2-realisme/05e` : la décision suit la résolution physique) ignorait la hauteur et surestimait les contres. Corrigé, série « après » refaite.
- Code :
  - `v2engine/match.py` : `_blocked` : un défenseur ne tente le contre que si le tir passe sous son atteinte à l'instant du contact (`atteinte.reach_m`), sinon le tir continue (pas de tentative comptée) ; `_keeper_reaches` : le gardien n'arrête que si le ballon passe sous son atteinte (mains dans sa surface, tête hors de sa surface) ; hauteurs toujours tracées ; commentaire périmé de la hauteur corrigé (remarque du QC au `03a`).
  - `v2engine/shooting.py` : `_under_reach_angle` (écart vertical sous lequel le tir passe sous l'atteinte d'un défenseur, avec la courbe du `02a2` : `z(t) = h·t/T + g·t·(T − t)/2`, rasant si `h ≤ 0`) ; `_height_pass` (chance de n'être contré par aucun défenseur, sur l'écart vertical commun, éventuellement sous la barre) ; `_block_covers` porte le seuil de chaque défenseur ; `_flight_shares` juge ensemble contre et barre sur le même écart vertical (un tir qui passe au-dessus d'un défenseur est un tir haut). Sans défenseur, ou tous à portée, l'ancienne règle est retrouvée (testé). Aucune constante nouvelle.
- Scènes (`tests/test_v2engine_hauteur_tirs.py`, 6 cas ajoutés) : tir à 6 m sur la ligne au-dessus d'un défenseur à 4 m du but : non contré, « au-dessus » ; même défenseur, tir à 1 m : contré sous son atteinte ; gardien sorti hors de sa surface (portée au sol forcée) : tir à 2,4 m sur la ligne au-dessus de sa tête, but ; tir à 0,5 m : arrêté ; estimateur : seuil vertical cohérent avec la courbe du tir ; ancienne règle retrouvée quand tout tir est à portée. `test_v2engine_chance_tir.py` (estimateur contre trajectoire, 28 cas) repasse sans changement du test.
- Série (50 matchs mêmes graines, avant : `4631752`, `.scratch/v2-hauteur-ballon/mesures/03b-serie.py`, synthèse `03b-synthese.py`), détail `docs/INDICATEURS_V2.md` § 74 : contres au-dessus de l'atteinte 5 sur 351 avant (jusqu'à 3,56 m), **0 sur 363 après** (max 2,33 m) ; arrêts au-dessus des mains 0 sur 340 avant, 0 sur 338 après. Par match, tous dans le bruit : buts 5,20 → 5,18 (− 0,02 [− 0,29 ; + 0,25]), tirs 30,96 → 31,28 (+ 0,32 [− 0,40 ; + 1,04]), contrés 7,02 → 7,26, arrêts 6,84 → 6,80, au-dessus 4,42 → 4,58, à côté 6,80 → 6,74. Hauteur jamais négative, 0 mode incohérent. (Première série « après », sans l'estimateur corrigé : tirs + 0,50 [+ 0,03 ; + 1,04], écart disparu avec l'estimateur.)
- Déterminisme : matchs 0 et 1 rejoués sur le code final, mêmes empreintes complètes.
- Suite complète : 3 618 passés, 0 ignoré, 14 désélectionnés (3 612 + 6) ; V1 non touchée.
- Durée réelle : environ 1 h 35 (analyse 15, développement 35, tests 25, intégration et vérifications 20), + 6 % sur l'estimation révisée de 1 h 30 (+ 58 % sur la première, 1 h : estimateur du tir hors du périmètre prévu, révélé par la suite complète). À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : trois séries de 50 matchs (environ 30 min chacune), deux rejeux de 2 matchs, deux suites complètes (17 min chacune).

## Comments

- 23/11/2026, passage 1 : expert APPROVED (empreinte `6acd10d0…`), aucune action obligatoire ; facultatifs A1 (contrôle des arrêts de la série trop indulgent : mains supposées pour tout arrêt, note brute, association par ordre non vérifiée pour les arrêts ; tracer l'atteinte effective au moment de l'arrêt), A2 (approximations de l'estimateur : ligne dans l'axe du but, temps de vol continu). QC VALIDÉ (réserves non bloquantes : seuil de l'estimateur approché ; durée non chronométrée). Clôture VALIDÉ. À surveiller (expert) : à l'écran (`02b`), les contres de la tête vers 2,2 à 2,4 m doivent montrer un défenseur en saut.
