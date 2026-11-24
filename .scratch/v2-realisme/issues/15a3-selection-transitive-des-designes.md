# 15a3: Sélection transitive des joueurs désignés sur un ballon aérien

**Chantier :** `v2-realisme` (réserve A1 de l'expert au ticket `15a2`, 24/11/2026, acceptée par le propriétaire : « Accepter, corriger en ticket »). **Priorité :** P3. **Catégorie :** décision.

**Constat vérifié (15a2) :** `jeu_aerien._compare` (règle double du maintien) n'est pas un ordre total dès que trois coéquipiers de seniorités différentes sont en concurrence. Exemple de l'expert : S premier désigné (contact 1,0 s, arrivée 1,0 s), J1 nouveau (0,9 s, 0,8 s), J2 nouveau (1,0 s, 0,5 s) : J1 avant J2, S avant J1, J2 avant S. Le tri rend alors un ordre qui dépend de l'ordre de la liste des joueurs (déterministe, mais pouvant contredire la règle).

**What to build:** sélection en deux temps (correctif proposé par l'expert) : classer les non-désignés par la clé neutre (contact arrondi, arrivée, nom) ; pour chaque place, premier puis second, le titulaire du pas précédent la garde sauf si le meilleur prétendant qui le déplace selon la règle double le déplace. Mêmes résultats sur les cas à deux joueurs.

**Attributs :** aucun. **Constantes :** aucune.

**Blocked by:** `15a2` (livré). **À faire avant ou avec :** `15b`.

**Status:** livré (24/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 05** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs appariée (environ 48 min), suite complète (environ 22 min).

**Critères chiffrés** (posés avant le code, 24/11/2026) : scène S, J1, J2 de l'expert : même résultat sur les 6 ordres, J2 premier, S second, J1 écarté ; scènes du `15a` et du `15a2` inchangées ; 50 matchs appariés (avant : série retenue du `15a2`, sur le code de `a4cfe9a`, mêmes graines) : changements rapides du premier pas significativement au-dessus de 7,4 %, jeu aérien non dégradé ; déterminisme à graine fixée ; suite complète à 3 645 passés, 0 ignoré, 14 désélectionnés.

## Tests

- Scène S, J1, J2 ci-dessus : même résultat pour les 6 permutations de la liste des joueurs, conforme à la règle double.
- Scènes du `15a` et du `15a2` inchangées.
- Série : changements rapides du premier non dégradés (7,4 % au `15a2`) ; premier contrôle du corps après un centre surveillé (+ 4 points au `15a2`).

## Acceptance criteria

- [x] Scène à trois joueurs indépendante de l'ordre des joueurs
- [x] Scènes à deux joueurs inchangées
- [x] 50 matchs appariés sans dégradation ; déterminisme à graine fixée ; suite complète au compte attendu
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %

## Résultats (24/11/2026)

- Code : `v2engine/jeu_aerien.py` : `fill_places` attribue les places de premier puis de second une par une : le titulaire (plus ancien désigné encore candidat) garde la place sauf si un coéquipier le déplace (`_displaces`, règle double du `15a2` : receveur visé, puis à temps, puis contact plus de 0,3 s plus tôt, ou au plus tard au même instant avec une arrivée plus de 0,3 s plus tôt) ; le mieux classé hors maintien (`_neutral_key` : receveur, à temps, contact arrondi, arrivée, nom) parmi ceux qui le déplacent la prend ; sans titulaire, le mieux classé hors maintien. Le comparateur deux à deux `_compare` et le tri `cmp_to_key` sont retirés. Écart du second inchangé.
- Scènes (`tests/test_v2engine_jeu_aerien.py`, 1 cas ajouté, 17 au total) : S, J1, J2 de l'expert : (J2, S) pour les 6 ordres ; sans désigné, (J1, J2) pour les 6 ordres. Contrôle sur l'ancien code (`a4cfe9a`) : trois résultats selon l'ordre, (J1, J2), (S, J1), (J2, S). Scènes du `15a` et du `15a2` inchangées.
- Série (50 matchs appariés, avant : série retenue du `15a2`, code identique à `a4cfe9a`), `docs/INDICATEURS_V2.md` § 78 : aucun écart significatif sur 2 884 indicateurs ; désignations par équipe 31,64 → 31,61 (environ 3 relevés sur la série) ; changements rapides du premier 7,4 → 7,2 % ; buts, tirs, centres, têtes, ballon libre, contacts identiques.
- Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes de la trace complète (`5b3136f9…`, `7646a6a6…`, identiques au `15a2` : pas de cycle dans ces deux matchs).
- Suite complète : 3 645 passés, 0 ignoré, 14 désélectionnés (3 644 + 1 cas) ; V1 non touchée.
- Durée réelle : environ 55 min (analyse 10, développement 20, tests 10, intégration et vérifications 15), − 15 % sur l'estimation de 1 h 05 (série « avant » reprise du `15a2`). À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : une série de 50 matchs (48 min), suite complète (22 min), rejeu de 2 matchs.

## Comments

- 24/11/2026, passage 1 : expert APPROVED (empreinte `390ebe6e…`, code et tests seuls ; équivalence à deux joueurs vérifiée à la main, indépendance à l'ordre par construction) ; QC VALIDÉ. Clôture VALIDÉ.
- Facultatif (expert A1, remarque QC) : une ligne de la docstring de `select_attackers` dépasse la largeur habituelle ; non corrigée (rouvrirait la revue), à reprendre au prochain ticket qui touche ce fichier.
- Remarque QC : critère de série à lire comme « pas de remontée significative au-dessus de 7,4 % » (non-dégradation).
- À surveiller (expert) au `15b` : premier contrôle du corps après un centre (+ 4 points au `15a2`).
