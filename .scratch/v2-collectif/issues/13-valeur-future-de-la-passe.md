# 13: Valeur future d'une passe

**What to build:** Le porteur n'évalue plus une passe seulement par sa probabilité de réussite : il estime ce qu'elle **prépare** (solutions suivantes du receveur, progression, bloc adverse attiré). Une passe latérale peut être la meilleure parce qu'elle attire le bloc avant de trouver un joueur entre les lignes. Pas de ping-pong : l'orientation du contrôle, la pression, le temps disponible et la qualité des solutions comptent.

**Attributs :** Vision, Decisions, Passing.

**Blocked by:** 06.

**Status:** livré (02/11/2026), validé expert + QC (réserve A1 acceptée par le propriétaire)

## Constantes et critères validés par le propriétaire (01/11/2026, « Oui, valide tout »)

**Constantes**
- Valeur d'une passe = réussite × (60 % gain immédiat + 40 % valeur de la suite). Valeur de la suite : meilleure passe suivante du receveur, sa réussite (Passing et pression du receveur) × la progression qu'elle donne, sur les positions de l'instant (pas de prédiction ; inspiration Expected Threat, Karun Singh). *(Précisé en cours de code : progression comptée depuis le porteur, mêmes parts que le gain immédiat, au moins la position atteinte ; voir « Réalisation ».)*
- ~~A9 : le facteur d'ouverture du receveur (`1 - pression`, 5 m) est supprimé ; un receveur marqué reste pénalisé à la réception (2 m) et sur sa passe suivante (pressé, Composure), deux gestes distincts (à confirmer par l'expert).~~ *(Remplacé : facteur gardé, point 1 de « Réalisation ».)*
- Pas d'aller-retour : le passeur est exclu des suites du receveur.
- Vision : le porteur ne compte une suite que vers un coéquipier qu'il voit lui-même (portée et passe clé de Vision, ticket 02). Decisions et Passing inchangés. Aucune courbe nouvelle.
- ~~Mêmes règles dans tous les modes (contre-attaque : passes vers l'avant seulement, ticket 11).~~ *(Remplacé : pas de suite en contre-attaque, point 2.)*
- Non modélisés, renvoyés : bloc adverse attiré (ticket 14) ; orientation du contrôle (First Touch, contrôle orienté).

**Critères** (avant : 4 matchs, graine d'audit, `962913a`)
- C1 : deux receveurs latéraux identiques, un seul avec un coéquipier libre entre les lignes (Decisions 55, 2 000 tirages) : le premier choisi au moins 65 %, l'autre au plus 35 %.
- C2 : passe sans gain suivie par le receveur d'une passe qui casse une ligne ou gagne 10 m : 33,9 % → au moins 39 %.
- C3 : 15 à 17 passes par minute (15,7) ; passes par possession au moins 2,3 (2,38 ; fourchette 3-5 déjà manquée, ticket 22).
- C4 : retour au passeur en 3 s au plus 8,6 % (7,6 %).
- C5 : réussite des passes, recul de 2 points au plus (60,9 %).
- C6 : temps de calcul par match +25 % au plus.
- C7 : déterminisme, suite V2 verte, V1 inchangée.
- Indicateurs réels (pas des objectifs) : passes vers l'arrière 24-42 %, 36,5 % en Premier League (CIES) contre 17 % ; passes qui cassent une ligne, plus de 40 par équipe et par match en Premier League (StatsBomb, autre définition).

## Réalisation (01/11/2026)

**Décisions du propriétaire en cours de code (01/11/2026)**
- Point 1 (« Garder le facteur ») : sans le facteur d'ouverture, le porteur servait un coéquipier collé par un défenseur (à 0,5 m, à 3 m de lui) plutôt que le démarqué à 20 m (test existant `test_pass_prefers_open_teammate_closer_to_goal_over_nearest_marked_one`). Le facteur reste, comme « temps disponible » ; A9 est reclassé (`docs/CARTE_ATTRIBUTS_V2.md`), à confirmer par l'expert.
- Point 2 (« Pas de suite en contre ») : en contre-attaque, la valeur reste la progression seule (règle du ticket 11 intacte, test `test_pressed_holder_in_counter_can_still_play_back_but_after_any_forward_pass`).
- Variante C (« Oui, garde C à 40 % ») : la progression de la passe suivante est comptée depuis le porteur, donc là où le ballon arrive après les deux passes ; la suite vaut au moins la position déjà atteinte (il garde le ballon). C2 non atteint, renvoyé au ticket 14, remesure au ticket 22.

**Code**
- `v2engine/decision.py` : `_FOLLOW_UP_SHARE = 0.4`, suite dans `evaluate_options`, `_progress` extrait.
- Tests : `tests/test_v2engine_valeur_passe.py`, 5 tests (C1, valeur inchangée sans meilleure suite, Vision, Passing du receveur, pas de suite en contre-attaque). Aucun test existant modifié.

**Mesures (4 matchs, graine d'audit, banc `scripts/measure_v2` et diagnostic hors dépôt)**

| Variante | C2 | Arrière / latérales / avant | Retour au passeur en 3 s |
|---|---|---|---|
| Départ (`962913a`) | 33,9 % | 17,0 / 55,8 / 27,2 % | 7,6 % |
| A, comme proposé (gain depuis le receveur, sans facteur) | 22,3 % | 28,2 / 53,4 / 18,4 % | 5,6 % |
| B (gain depuis le porteur) | 26,8 % | 20,0 / 56,3 / 23,7 % | 6,6 % |
| **C, retenue** (B, au moins la position atteinte) | **35,1 %** | 17,2 / 55,3 / 27,5 % | 7,2 % |

| Critère | Avant | Après (C) | Verdict |
|---|---|---|---|
| C1, scène contrôlée (Decisions 55, 2 000 tirages) | — | A 70,3 %, B 0 % | ✅ |
| C2 | 33,9 % | 35,1 % | ❌ (au moins 39 %), renvoyé au ticket 14 |
| C3, passes par minute ; passes par possession | 15,7 ; 2,38 | 15,7 ; 2,35 | ✅ |
| C4, retour au passeur en 3 s | 7,6 % | 7,2 % | ✅ |
| C5, réussite des passes | 60,9 % | 60,4 % | ✅ |
| C6, temps de calcul (match de 15 min, deux fois chaque) | 43,8-56,0 s | 44,7-46,7 s | ✅ (bruité, au plus +7 %) |
| C7, déterminisme | — | `034b6b9648d0e3f9` deux fois (10 min, 212 décisions) | ✅ |
| C7, suite complète | — | 2 249 passés, 13 désélectionnés, 0 échec (01/11/2026, avant M1) ; 2 259 passés, 13 désélectionnés, 0 échec sur le code final (02/11/2026, l'arbre contient aussi le travail en cours du ticket 09 et ses tests) | ✅ |

Ce tableau date d'avant la correction M1 ; les chiffres du code final sont plus bas (« Mesures après M1 »).

Autres indicateurs (banc) : buts 2,5 → 2,75 ; tirs par équipe 10,5 → 12,0 ; tacles 44,5 → 47,5 ; hors-jeu 1,25 → 0,25 ; solutions ouvertes 1,92 → 2,00 ; possession d'équipe 9,1 → 8,9 s. Variation à graine égale déjà constatée (ticket 08 : écart-type des buts d'environ 0,4 sur 20 matchs).

**Pourquoi C2 bouge peu** : sur 20 minutes, la suite change le receveur choisi dans 5 % des décisions (11 % à 60 %, 10 % à 80 %). Le porteur prévoit la passe suivante, mais le receveur décide ensuite seul : la coordination relève du ticket 14.

**Revue `simulafoot-reviewer` (01/11/2026)** : aucun bloquant.
- M1, corrigé : le plancher et la suite étaient comptés en progression brute, sans les parts du mode. Hors transition, une passe sans suite valait 0,18 + 0,82 × progression au lieu de 0,3 + 0,7 ; en conservation, la sûreté était diluée (règle du ticket 11). La suite et le plancher sont maintenant dans l'échelle du gain immédiat : sans meilleure suite, la passe garde exactement sa valeur d'avant le ticket (test `test_without_a_better_next_pass_the_value_is_the_one_before_the_ticket`, hors transition et en conservation).
- M2, documenté : la pression sur le receveur entre trois fois (réussite, ouverture, passe suivante), à trancher par l'expert (ligne A9 de la carte).
- Mineurs traités : libellé de C1 (B à 0 par construction, la discrimination vient de la première assertion), test d'aller-retour renommé, test Vision qui vérifie la cible, lignes Passing et Composure de la carte, puces remplacées du ticket barrées, commentaires.

**Mesures après M1 (code final)**
- 4 matchs : C2 30,7 % ; arrière / latérales / avant 18,1 / 54,2 / 27,7 % ; retour au passeur 7,5 % ; réussite 60,7 % ; 15,8 passes par minute ; 2,37 passes par possession ; buts 2,5 → 1,0 ; tirs 10,5 → 10,1 ; hors-jeu 1,25 → 2,25 ; suite changeant le receveur dans 3,5 % des décisions (20 min) ; déterminisme `8ebaf8e20ccf0863` deux fois (228 décisions).
- 10 matchs, mêmes graines, suite à 0 (valeur exacte d'avant le ticket) contre suite à 0,4 :

| Indicateur | Sans la suite | Avec | Critère |
|---|---|---|---|
| C2 | 32,5 % (997/3 072) | 30,6 % (955/3 118) | ❌, écart dans le bruit (environ 1,2 point d'écart-type) |
| Passes par minute | 16,0 | 16,0 | ✅ |
| Réussite des passes | 61,3 % | 61,4 % | ✅ |
| Retour au passeur en 3 s | 8,1 % | 8,4 % | ✅ |
| Arrière / latérales / avant | 17,4 / 55,3 / 27,3 % | 18,0 / 54,9 / 27,1 % | — |
| Passes qui cassent une ligne, réussies par équipe et par match | 112,9 | 110,4 | — |
| Temps de calcul, 10 matchs | 2 815 s | 2 856 s (+1,5 %) | ✅ |

**Constat** : le mécanisme agit dans la scène contrôlée (C1), mais n'a pas d'effet mesurable en match, ni positif, ni négatif. Le porteur ne choisit autrement que dans 3,5 % des décisions, et le receveur ne joue pas forcément la passe prévue.

**Point de vigilance :** le ping-pong a été corrigé au ticket socle 06 par le temps de réception : ce ticket ne doit pas le réintroduire. Reprend aussi A9 (`docs/CARTE_ATTRIBUTS_V2.md`) : dans la valeur d'une passe, un receveur marqué est pénalisé deux fois (réussite de la passe et ouverture).

- [x] À situation égale, une passe qui ouvre une solution suivante est choisie mesurablement plus souvent qu'une passe sûre sans suite : rempli dans la scène contrôlée (C1 : 70,3 % contre 0 %) ; **pas d'effet mesurable en match** (C2 manqué : 30,6 % contre 32,5 % sans la suite, 10 matchs), réserve A1 acceptée par le propriétaire, critère repris au ticket 14
- [x] Les acquis du rythme tiennent (ticket socle 06 : 15-17 passes par minute, 3-5 passes par possession) : 16,0 passes par minute ; 2,37 passes par possession, inchangé (fourchette 3-5 déjà manquée avant ce ticket, ticket 22)
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18) : aucune courbe nouvelle ; A9 reclassé, à confirmer par l'expert
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée (voir `13-tests.txt` du dossier de revue)

## Comments

- 02/11/2026, passage 1 (base `316d2ef`, empreinte `68f61f71`) : expert APPROVED_WITH_RESERVATIONS ; QC REFUSÉ (C2 manqué sans acceptation du propriétaire sur le chiffre final, case 1 cochée). Réserves : A1, aucun effet mesurable en match (C2 30,6 % contre 32,5 % sans la suite, 10 matchs ; au moins 39 % demandé), report au ticket 14 ; A9 reclassé, confirmé par l'expert. Facultatifs laissés : A2, progression de la deuxième passe plafonnée à 20 m (piste pour le ticket 14 ou 22, constante à proposer) ; A3, distance de T dans les commentaires du test (17,0 m, non 15,6 m), sans effet sur les conclusions. **Réserve A1 acceptée par le propriétaire le 02/11/2026 : « Ok j'accepte »**, sur le chiffre post-M1 ; C2 inscrit au ticket 14. Case 1 reformulée, décompte de la suite aligné.
- 02/11/2026, passage 2 (même empreinte `68f61f71`) : QC VALIDÉ ; clôture VALIDÉ (expert APPROVED_WITH_RESERVATIONS, réserves acceptées, QC VALIDÉ).
