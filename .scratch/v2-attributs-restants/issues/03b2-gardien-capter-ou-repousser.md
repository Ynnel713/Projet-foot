# 03b2: Gardien : capter ou repousser (Handling), boulettes

**Découpé du ticket `03b` le 22/11/2026** (décision du propriétaire). Gardien moyen : médiane des gardiens de Ligue 1 de la base (Reflexes 75, One on Ones 75, Handling 60) ; un gardien sans note (effectif synthétique, copie neutre de l'xG) vaut le gardien moyen.

**What to build:** Handling règle la part captée d'un arrêt (`shooting.save_shares`, aujourd'hui gardien neutre) : le haut capte, le bas repousse et offre une seconde occasion. Erreurs du gardien possibles même pour un très bon gardien (ballon relâché dans la surface), plus fréquentes pour un mauvais. Gardien noté 99 : boulettes rares mais présentes sur 500 matchs ; noté 40 : parade réflexe exceptionnelle présente.

**Attributs :** Handling. Centres : `03a` (Punching) reste à part.

**Blocked by:** `03b1`.

**Bloque :** `10b` ; `v2-collectif/22a`.

**Status:** livré (22/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Développement | 30 min |
| Tests | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Temps machine, non compté : suite complète ; 50 matchs appariés.

**Estimation révisée (22/11/2026, avant le code)** : 2 h (analyse 20 min, développement 40 min, tests 30 min, intégration 30 min) au lieu de 1 h 30 : la boulette demande une trajectoire de ballon nouvelle et la réserve A1 une mesure des corners issus d'arrêts. Confiance moyenne. Temps machine hors total : deux séries de 50 matchs (environ 1 h), suite complète (environ 16 min).

**Constantes** (proposées au propriétaire le 22/11/2026, délégation permanente « Je valide automatiquement toutes tes recommandations » ; choix explicite du propriétaire : « Oui, tous (Recommandé) — tout gardien, moyen compris, peut relâcher le ballon ») : Handling 60 = gardien moyen (médiane des 50 gardiens notés de Ligue 1 ; étendue 35 à 75) ; part captée + 0,005 par point, bornée à 10-90 % (99 : + 0,195 ; 40 : − 0,10) ; prises relâchées 4 % à 60, − 0,00075 par point, bornées à 0,5-10 % (99 : 1,1 % ; 40 : 5,5 %) ; ballon relâché à 1 à 2 m/s vers le terrain, à au plus 60° de la perpendiculaire à la ligne de but (arrêté à moins de 3 m du gardien), compté « repoussé », marqué `fumbled` dans la trace. Repères réels (part captée, ballons relâchés selon le niveau) : non trouvés, ordres de grandeur. Parade d'exception d'un gardien faible : part captée jamais sous 10 % (0,15 pour un 40 sur le tir le plus difficile).

## Acceptance criteria

- [x] Réserve A1 de l'expert au `03b1` : `shot_probability` ne lit plus les notes du gardien depuis le `03b1`, ce qui déplace la difficulté de l'arrêt (`save_shares`) ; mesurer avant / après la part captée / repoussée / claquée et la part des corners issus d'arrêts (repère du `28b` : environ 20 %), recaler `SAVE_HELD_SHARE` au besoin (au `03b1`, 50 matchs : capté 53,7 % → 53,0 %, repoussé 30,7 % → 32,1 %)

- [x] Constantes proposées au propriétaire avant le code
- [x] Moins de ballons relâchés avec Handling élevé (scène et 50 matchs) ; gardien moyen inchangé
- [x] Boulettes : rares mais présentes pour un 99 ; parade exceptionnelle présente pour un 40
- [x] Test de rayon et carte à jour ; Handling sort des exceptions de couverture (lu de nouveau) et rejoint la liste de transition comme Reflexes et One on Ones (un contexte)
- [x] Durée réelle relevée ; déterminisme ; suite V2 verte ; V1 inchangée

## Résultats (22/11/2026)

**Code** : `shooting.keeper_handling`, `save_shares(…, handling)` (part captée + 0,005 par point autour de 60, bornée à 10-90 %, reste réparti comme avant), `fumble_share`, `fumbles` (flux TIR), `fumble_velocity` ; `match._keeper_reaches` tire la prise relâchée sur une prise dans la surface, la range « repoussé » avec `ShotEvent.fumbled` ; `match._keeper_save` lâche le ballon à 1-2 m/s devant le gardien. Tests : `tests/test_v2engine_prise_de_balle.py` (7), garde probabiliste (« prise de balle », cas facile et difficile), garde des attributs (plan de tir), rayon (Handling en transition, sorti des exceptions de couverture) ; carte à jour.

**Série appariée** (`PYTHONPATH=. PYTHONHASHSEED=0 <python> .scratch/v2-attributs-restants/mesures/03b2-serie.py 50 4 <sortie.json>`, avant : `8dbe679` ; synthèse : `03b2-synthese.py avant.json apres.json`) :

| Par match | Avant | Après |
|---|---|---|
| Buts | 4,02 | 4,48 (écart apparié + 0,46 [− 0,07 ; + 0,99]) |
| Arrêts | 5,92 | 5,58 |
| Captés / repoussés (dont relâchés) / claqués | 53,0 / 32,1 (0) / 14,9 % | 49,1 / 32,6 (8) / 18,3 % |
| Corners | 3,52 | 4,42 |
| Corners issus d'un arrêt (dernier toucher gardien) | 25,6 % | 24,0 % |

Prises relâchées par Handling du gardien (relâchées / prises) : [0 ; 55[ 2 / 21 (9,5 %), [55 ; 65[ 4 / 65 (6,2 %), [65 ; 100[ 2 / 59 (3,4 %) : décroissant, effectifs faibles.

**Réserve A1** : la répartition des arrêts bouge peu depuis le `03b1` (capté 53,7 → 53,0 → 49,1 %, la baisse au `03b2` vient des prises relâchées, comptées « repoussé », et du gardien faible) ; corners issus d'arrêts 24-26 %, proches du repère du `28b` (environ 20 %) et stables avant / après : `SAVE_HELD_SHARE` n'est pas recalé.

**Lecture** : la hausse des buts (+ 0,46) reste dans l'intervalle du bruit (tous les tirages sont redistribués par le nouveau tirage de prise relâchée) ; à surveiller sur une série plus longue (`10b`). Gardien moyen : parts de `save_shares` à 60 identiques à l'ancienne loi (test) ; il relâche 4 % de ses prises (choix du propriétaire). 99 : 16 boulettes attendues sur 1 500 prises (test : 5 à 35) ; 40 : 0,15 capté sur le tir le plus difficile.

**Suite** : 3 531 passés, 0 ignoré, 14 désélectionnés (3 518 au `03b1` + 13 : 7 du nouveau fichier, le reste par les cas paramétrés des gardes). Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes (`85ca80a8…`, `4823e004…`).

**Durée réelle** : environ 2 h 15 (analyse 25 min, développement 40 min, tests 40 min, intégration 30 min) pour 2 h estimées (+ 13 %). Temps machine hors total : deux séries de 50 matchs (1 h), suite complète (15 min).

## Comments

- 22/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ (réserves acceptées).
  - A1 [réserve] : la carte des attributs, modifiée par le ticket, est hors empreinte ; à commiter avec le code (fait dans le même commit).
  - A2 [réserve] : buts + 0,46 [− 0,07 ; + 0,99] et corners + 0,9 par match sur 50 matchs, sans mécanisme suffisant (attendu ≈ + 0,05 but) ; à remesurer avec intervalle au `10b`, ticket ouvert si la hausse dépasse + 0,2 avec un intervalle qui exclut zéro.
  - Facultatifs : A3 (décroissance des boulettes en match sur 8 cas), A4 (gardien noté sans clé Handling non testé).
  - Réserves acceptées par le propriétaire : « J'accepte A1 et A2 (Recommandé) ».
