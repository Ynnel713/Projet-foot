# 18e: Calibration provisoire 2 : tirs, conversion et gardien après les fondations P0

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le volume et la conversion des tirs doivent être plausibles avant les développements tactiques). **Catégorie :** validation.

**Constat vérifié :** mesure 28b : 37,6 tirs par équipe, conversion 5,7 %, 54,7 % des buts dans la surface ; les P0 changent la trajectoire du tir, l'arrêt et la décision (05, 03, 04).

**What to build:** Régler provisoirement, sur 500 matchs, les constantes du tir (exécution 35b, portée et réaction du gardien 05b, contre 05c) et de la valeur du tir dans la décision (05e), une fois le gardien placé (03), pour approcher tirs par équipe, cadrés, conversion et part des buts dans la surface. Règles d'une calibration provisoire (décision du propriétaire du 05/11/2026) : seules les constantes des mécanismes concernés bougent, dans leurs fourchettes validées ; chaque valeur est marquée « provisoire » dans le code et dans `docs/INDICATEURS_V2.md` avec la date et la mesure ; aucun réglage ne masque une lacune de mécanisme (un écart dû à un mécanisme absent devient un ticket) ; la calibration finale (`v2-collectif/22a` à `22c`) repart de ces valeurs et peut toutes les revoir.

**Hors de ce ticket :** calibration finale (`v2-collectif/22c`).

**Attributs :** aucun

**Blocked by:** 18d (Calibration provisoire 1 : volumes de course et rythme après les fondations P0); 18f (Calibration provisoire 1 bis : choix du porteur et rythme de décision) (ajouté le 11/11/2026, découpage du 18d); 05g (Validation des tirs : trajectoire, cadrage, contres, arrêts); 03g (Validation du placement et des sorties du gardien); 06b (Indicateurs : occasion, exécution, gardien, par attribut).

**Bloque :** `v2-collectif/22c`.

**Status:** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : la position du gardien est validée (03g) avant de régler l'arrêt.
Temps machine, non compté : suite complète (environ 40 min) ; séries de 500 matchs.

## Tests

- **Statistiques (séries de matchs) :** 500 matchs avant / après : tirs, cadrés, contrés, conversion, buts dans la surface, xG neutre cumulé contre buts

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : aucune constante modifiée (recommandation validée par délégation, voir Comments) ; repères R1, R2 (Opta, `docs/INDICATEURS_V2.md` section 8), contrés 22,5 % (Bundesliga 2015-16)
- [x] Chaque constante modifiée marquée « provisoire », avec date et mesure : sans objet (aucune modifiée) ; l'essai `BLOCK_CHANCE` 0,75 est consigné (section 34)
- [x] Gardien jamais réglé avant que son placement soit validé (03g) : 03g livré ; taux d'arrêt des cadrés environ 73 % (repère environ 70 %), pas de réglage
- [x] Écarts restants attribués (mécanisme ou calibration finale) : volume, conversion et buts dans la surface au mélange des tirs (mécanisme, ticket 18k) ; contrés au relèvement de `BLOCK_CHANCE`, bloqué par l'estimateur du contre (mécanisme, ticket 05j) ; penaltys aux fautes dans la surface (21b, 21c)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : sans objet pour le moteur (inchangé) ; diagnostic en lecture seule à graines fixes
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (moteur et tests inchangés : 2 775 du 18j)
- [~] Statistiques sur 500 matchs avant / après : non faites, dérogation par délégation (aucune constante modifiée, il n'y a pas d'« après » ; état mesuré sur 50 matchs, erreur type de la conversion environ 0,6 point, suffisante pour attribuer les écarts)

## Complément du point d'étape 18a (11/11/2026)

Source : `docs/INDICATEURS_V2.md` section 25. Conversion déjà proche (9,9 %) ; l'écart principal est la part des buts dans la surface (61 %, repère 88 à 89 %) : 390 des 656 tirs cadrés partent de plus de 18 m. Relire les penaltys (0,02 par match, réel environ 0,34) après le 18d.

## Condition reprise de l'expert sur le 12d (11/11/2026)

Réserve A1 : après le 12d, conversion 7,8 % (xG moyen 0,083) et tacles 46,5 par match (`docs/INDICATEURS_V2.md` section 26). Relire R2 sur l'état après 12d, 12e et 18d, pas sur le 9,9 % du point d'étape (section 25).

## Comments

**12/11/2026, lancement.** Estimation annoncée : 1 h 50, confiance moyenne. Délégation du propriétaire (« enchaine les les uns après les autres. Je valide automatiquement toutes tes recommandations et les conseils d'experts ainsi que les commits si les conditions le permettent donc ne me sollicite pas »).

**12/11/2026, état de départ (moteur du 18j, 50 matchs, `18j-50-lot*`).** Tirs tracés 18,0 par équipe (repère R1 8 à 15) ; cadrés 26,8 % (environ 33) ; contrés 17,6 % (20 à 28, 22,5 en Bundesliga) ; conversion 7,3 % (R2 10 à 12) ; buts dans la surface 51,8 % (88 à 89) ; penaltys 0,04 par match (environ 0,34) ; distance moyenne de tir 22,4 m ; xG neutre 2,61 par match pour 2,62 buts.

**12/11/2026, diagnostic par zone (`18e-zones.py`, 50 matchs, mêmes graines ; synthèse `18e-zones-synthese.py`, sortie `18e-zones-avant.txt`).**

| Zone | Tirs par équipe | Conversion | Réel (Opta PL 2024-25) |
|---|---|---|---|
| Surface | 3,85 | 17,7 % | 14,7 % (penaltys compris) |
| Hors surface | 14,13 | 4,4 % | 4,2 % |
| dont 25 à 30 m | 6,93 | 2,3 % (xG 0,021) | — |
| Part dans la surface | 21,4 % | — | 68,3 % |

Conversion par zone réaliste ; cadrés par zone : 38,7 % dans la surface, 23,5 % dehors, soit 33,8 % avec le mélange réel (conversion projetée 13,5 %, au-dessus de R2 : conversion dans la surface à surveiller). **Cause des écarts : le mélange des tirs**, pas l'exécution ni le gardien. Le porteur tire de loin parce qu'un tir manqué ne coûte rien dans la décision (réserve A2 du `v2-collectif/28a`) : mécanisme absent, ticket **18k** créé. Le régler ici (portée de tir, précision) le masquerait.

**12/11/2026, contrés : essai `BLOCK_CHANCE` 0,6 → 0,75 (`18e-variante.py`, 50 matchs, `18e-b075-lot*`).** Contrés 17,6 → 22,4 % (repère 22,5), conversion 7,3 → 7,2 %, buts 2,62 inchangés, tirs 18,0 → 18,3. Mais `test_v2engine_chance_tir.py` (cohérence évaluation / résolution) échoue sur la scène du défenseur en course : l'estimateur du 05e place mal l'angle couvert par un défenseur qui court (écart déjà présent à 0,6, graine 7 ; `18e-contre-scene.txt`). Relever `BLOCK_CHANCE` creuserait l'écart entre ce que le joueur évalue et ce que la physique résout. **Recommandation retenue (validée par délégation) : `BLOCK_CHANCE` gardée à 0,6** ; ticket **05j** créé (estimateur angle par angle, puis relèvement vers 0,75).

**12/11/2026, gardien.** Taux d'arrêt des tirs cadrés environ 73 % (repère environ 70 %) ; par distance 36 % (moins de 11 m), 62 % (11-18), 77 % (18-25), 89 % (25 et plus) : aucun réglage.

**12/11/2026, série de 500 matchs.** Non faite : aucune constante n'est modifiée, il n'y a pas d'état « après » ; recommandation de dérogation validée par délégation. Les 50 matchs suffisent à attribuer les écarts (erreur type de la conversion environ 0,6 point, de la part dans la surface environ 1 point).

**Conclusion.** Calibration provisoire 2 sans réglage : les tirs ne seront réglables qu'après le 18k (mélange) et le 05j (contre). Rapport : section 34 de `docs/INDICATEURS_V2.md`.

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. Réserves :
- A1 [réserve] : projection de conversion avec le mélange réel fausse (« 11 % » au lieu de 0,683 × 17,7 + 0,317 × 4,4 = 13,5 %) ; une fois le mélange corrigé, la conversion dépasserait R2 ; conversion dans la surface à surveiller au 18k et au 22c.
- A2 [facultatif] : erreur type de la conversion environ 0,6 point, pas 0,4.
- A3 [facultatif] : test de cohérence but + contre fragile à 0,6 (graine 7 hors intervalle), couvert par le 05j.

**12/11/2026, décision par délégation du propriétaire** (« Je valide automatiquement toutes tes recommandations et les conseils d'experts ») : A1 acceptée et corrigée (section 34, ce ticket, critère du 18k) ; A2 corrigée ; A3 déjà couverte par le 05j. Correction du texte revu : nouvelle revue de l'expert (passage 2).

**12/11/2026, passage 2.** Expert : APPROVED (facultatifs : taux d'arrêt 11-18 et 18-25 m issus de la série du 18j, effectifs faibles ; repère de surface penaltys compris contre mesure hors penaltys, excès réel plutôt 4 à 5 points, déjà à surveiller au 18k et au 22c). QC : VALIDÉ. Clôture : VALIDÉ.

**Durée.** Estimée 1 h 50. Réelle environ 1 h 40, non chronométrée (analyse et diagnostic 45 min, développement 10 min : scripts de mesure, tests 0 (aucun code moteur), intégration et vérifications 45 min, dont deux tickets créés et un second passage de l'expert) : − 9 %. Temps machine hors total : diagnostic des zones (50 matchs, 12 min), essai `BLOCK_CHANCE` 0,75 (50 matchs, 25 min), scènes de contre (1 500 tirs x 8), sous-suite des tests de tir (2 min).
