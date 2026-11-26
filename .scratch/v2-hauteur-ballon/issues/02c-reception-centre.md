# 02c: Réception « centre » réservée au ballon reçu en l'air

**Ouvert le 26/11/2026** (demande du propriétaire), suite du contrôle fait à la clôture du `02a1` (Comments du 02a1, passage 2).

**Constat (02a1, 20 réceptions « centre » relues sur la piste du ballon, graines 0 à 2)** : les 20 sont des ballons en fin de petits rebonds, reçus 4,7 à 10 s après la frappe, à 0,1 à 1,5 m/s, le bas du ballon entre 0 et 0,46 m au point précédent ; 16 après 1 à 3 rebonds ; 3 non visés, issus de vols plafonnés. Aucune n'est une réception en l'air au sens du football (tête, poitrine, volée, ballon cueilli à sa première retombée). Réceptions « centre » : 2,9 par match avant le 02a1, 11,4 après (10,4 × le bruit) ; le total des réceptions est inchangé.

**Cause** (`v2engine/match.py`) : `airborne = z0 > 0.0 or vz0 != 0.0` au début du pas du ballon libre (`_step_loose_ball`, l.995), et la même condition dans `_danger_origin` (l.419). Tout ballon qui sautille encore, même de quelques centimètres, est « en l'air ». Effets :
- origine « centre » des réceptions, des tirs (`ShotEvent.origin`) et des situations dangereuses (`_danger_origin`) surévaluée ;
- contrôle de première interdit sur ces ballons (`first_time = intended and not airborne`, l.1050).

**What to build:**
1. **État du ballon** (`ball_state.py`) : savoir si le ballon a déjà touché le sol depuis son lancement (un booléen, remis à zéro par `_launch_aerial` et `_ground`, mis à vrai au premier contact au sol rendu par `hauteur.step_height` : `first_contact_s` non nul).
2. **Classement** : un ballon est « reçu en l'air » s'il est en vol **et n'a pas encore touché le sol** depuis son lancement (première retombée). Le contact n'étant permis que sous 0,5 m (02a1), c'est un ballon cueilli à sa première retombée, comme l'ancienne règle « 3 m avant le point de chute ». Après un rebond, le ballon est reçu comme une passe ordinaire (`_pass_kind` : au sol, en profondeur, en retrait).
3. Même règle aux trois lectures du classement, par une variable **distincte** de `airborne` (par exemple `first_drop` : en vol et pas encore touché le sol) : `_received_as` (l.1038), `_danger_origin` (l.419), `first_time` (l.1050).
4. **`airborne` reste inchangé** à la l.1019 : il garde le filtre de contact en hauteur (un ballon dont le bas est au-dessus de 0,5 m n'est pas touché). Redéfinir `airborne` rendrait touchable un ballon qui remonte au-dessus de 0,5 m après un rebond (réserve A1 de l'expert à l'ouverture du ticket).
5. Premier contact au sol dans le pas même où un joueur touche le ballon : comparer l'instant d'entrée du joueur (`entry·dt`) à `first_contact_s` du pas ; avant l'impact, le ballon est reçu à sa première retombée, après, il a rebondi.
6. Aucune constante nouvelle : pas de seuil de hauteur, pas de nombre de rebonds.

**Question au propriétaire, avant le code** : le contrôle de première reste-t-il interdit sur un ballon reçu à sa première retombée (comportement actuel du 02a1 et d'avant), ou seulement sur un ballon au-dessus d'une hauteur (constante nouvelle) ? Proposition : garder l'interdiction sur la première retombée, sans constante (le 03 traitera les tranches de hauteur).

**Hors périmètre** : tranches de hauteur et têtes (ticket 03) ; loi de freinage et vols plafonnés (`v2-realisme/14a`) ; hauteur des tirs (02a2).

**Blocked by:** 02a1 (livré le 26/11/2026).

**Bloque :** 03 (lit la même notion de ballon en l'air) ; `v2-collectif/22a` (change les origines des tirs et le jeu de première).

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Développement | 25 min |
| Tests | 25 min |
| Intégration et vérifications (série, contrôle de 20 réceptions, documentation, revues) | 55 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : le premier contact au sol est déjà calculé par `hauteur.step_height` (`first_contact_s`), il suffit de le mémoriser ; quatre sites lisent `airborne` (l.1019 filtre de contact, à préserver ; l.1038 et l.1050 et, par sa propre condition, `_danger_origin` l.419, à basculer sur la nouvelle variable). Intégration relevée selon le registre (`docs/agents/suivi-estimations.md` : intégration sous-estimée d'un facteur 1,5 à 1,9 ; × 4 au 02a1). À 2 h, pas de découpage : le changement est d'un seul tenant (un état, un classement, trois lectures).
Temps machine, non compté : une série de 50 matchs (graines 0 à 49, comparée à `02a1-apres2-A` et aux références `02a1-ref-A2` / `02a1-ref-B`, environ 75 min), suite complète (environ 15 min).

## Acceptance criteria

- [ ] Réponse du propriétaire à la question du contrôle de première, avant le code
- [ ] Test : un ballon reçu à sa première retombée est classé « centre » ; le même ballon reçu après un rebond est classé selon `_pass_kind`
- [ ] Test : `_danger_origin` suit la même règle
- [ ] Test : un ballon qui remonte au-dessus de 0,5 m après un rebond n'est touché par aucun joueur sur son trajet (filtre de la l.1019 préservé)
- [ ] Test : joueur qui entre dans la portée du ballon avant l'impact du pas → « centre » ; après l'impact → passe ordinaire
- [ ] Contrôle de 20 réceptions « centre » sur la piste du ballon (même méthode qu'au 02a1) : 20 sur 20 reçues avant le premier contact au sol
- [ ] 50 matchs (graines 0 à 49) : réceptions « centre » par match comparées à la référence d'avant le 02a1 (2,9 ± 0,82) et au 02a1 (11,4) ; part des tirs d'origine « centre » et contrôles de première comparés au 02a1 ; écarts hors bruit (bruit A contre B) documentés et soumis au propriétaire
- [ ] Mêmes empreintes de trace sur deux exécutions à graine fixée ; suite complète au compte attendu ; V1 inchangée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)

## Comments

**26/11/2026, ouverture (clôture `projet/02c-et-compte`)** : expert `APPROVED_WITH_RESERVATIONS` au passage 1. Réserve A1 (hypothèse fausse : `airborne` est aussi lu l.1019, garde du filtre de contact) et point facultatif A2 (premier contact au sol pendant le pas d'un contact) corrigés dans le ticket : variable distincte, `airborne` préservé, comparaison `entry·dt` / `first_contact_s`, deux critères ajoutés.

Passage 2 : expert `APPROVED`. À surveiller à l'implémentation : mémoriser « a touché le sol » avant l'appel à `_ground` (l.1039), qui le remet à zéro ; même règle exactement pour `_danger_origin` et `_received_as`.
