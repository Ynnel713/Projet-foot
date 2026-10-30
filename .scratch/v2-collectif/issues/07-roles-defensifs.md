# 07: Rôles défensifs : presser, couvrir, marquer, fermer l'axe

**What to build:** En défense, l'équipe attribue des rôles : **un presseur** sur le porteur, **une couverture** derrière lui (entre le ballon et le but), des **marquages** sur les adversaires dangereux et la **protection de l'axe**. Les autres tiennent le bloc (ticket 04). C'est ce qui manque aujourd'hui : avec un seul presseur et personne pour couvrir, la mesure du 26/10 donnait 59 tirs par équipe et 17,8 buts par match.

**Attributs :** Marking (adversaire désigné), Positioning (zone), Work Rate (envie de presser), Anticipation.

**Blocked by:** 04, 25 (socle cinématique et contact).

**Status:** livré (30/10/2026), validé expert + QC

**Point de vigilance :** le presseur unique a été codé dans le travail sauvegardé dans `.scratch/v2-collectif/wip-socle-02-intensite.patch` du ticket socle 02. Le reprendre comme rôle « presseur » parmi les autres.

- [x] Tirs par équipe et buts par match revenus à des ordres de grandeur réels sans réglage générique (à confirmer au ticket 22)  : 11,25 tirs, 1,4 but (sous la fourchette réelle de 2-3,5, à revoir au ticket 22)
- [x] Un presseur a une couverture quand le danger le justifie (test tactique)
- [x] Un attaquant dangereux est marqué mesurablement plus près par un bon marqueur  : 4,21 m contre 5,74 m (médianes, code final)
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée : suite complète, 2 110 passés, 13 désélectionnés, 0 échec

**Reporté du ticket 04 (27/10/2026) :** critère « une équipe à Teamwork élevé reste mesurablement plus compacte qu'une équipe à Teamwork bas ». Au ticket 04, Teamwork ne règle que les joueurs qui se replacent (écart 0,5 % du stretch index) ; il doit aussi agir sur qui quitte le bloc pour aller au ballon. À surveiller aussi : tacles montés à 52 par match avec le bloc (fourchette réelle 30-40).

## Réalisation (30/10/2026)

**Diagnostic avant le code** (état `4d71418`, 10 matchs) : tout défenseur à moins de 15 m du porteur fonçait sur lui. En moyenne 2,95 défenseurs à moins de 3 m du porteur, 6 ou plus dans 25 % des cas : un essaim. Résultats : 17,75 tirs par équipe, 5,3 buts et 86 tacles par match.

**Décisions du propriétaire (30/10/2026)**
- Trois rôles : presseur, couverture, marquage. La couverture se place sur la ligne porteur-but : elle ferme l'axe, donc pas de 4ᵉ rôle.
- Le presseur est celui qui arrive le premier sur le porteur. Ce temps d'arrivée dépend de Pace et Acceleration (capacité, règle R5).
- Work Rate (envie de presser) est laissé au ticket 08, pour ne pas régler deux fois le même effet (R1).
- Anticipation n'est pas ajoutée : elle agit déjà par le délai de réaction à la situation de jeu.

**Constantes validées (30/10/2026)** — ordres de grandeur, valeurs réelles non trouvées :
- couverture à 6 m derrière le porteur, seulement quand il est dans la moitié défendue ; sa place porte l'erreur de Positioning du ticket 04 ;
- attaquant dangereux : hors porteur, à 25 m ou moins du but ;
- distance de marquage, côté but : Marking 99 → 1 m, 55 → 2,5 m, 11 → 4 m ;
- un joueur sans rôle quitte le bloc pour aller au ballon : Teamwork 99 → 0 %, 55 → 15 %, 11 → 35 %, tiré toutes les 5 s.

**Code**
- `v2engine/defense.py` : nouveau module, `DefensiveRoles` mis à jour une fois par tick.
- `cerveau.interpret` et `cerveau.decide` : rôles attribués ; sans rôle, le joueur tient le bloc.
- `Bloc.placement_error` : extraite de `Bloc.target`, pour une seule erreur de Positioning par joueur.
- `match.simulate_match` : les rôles sont calculés après `bloc.update`.
- Garde du rayon des attributs étendue : Marking et Teamwork dans `defense` ; Pace et Acceleration en capacité dans `defense`.
- Tests : `tests/test_v2engine_defense.py`, 11 tests.

**Critères du ticket**

| Critère | Avant | Après |
|---|---|---|
| Défenseurs à moins de 3 m du porteur (moyenne ; cible 1,5 au plus) | 2,95 | **1,45** |
| 3 défenseurs ou plus à moins de 3 m (cible 15 % au plus) | 49 % | **13 %** |
| Profil Marking 99 contre 11 : distance réelle marqueur-attaquant (médiane ; écart cible 1 m au moins) | — | **4,21 contre 5,74 m** |
| Profil Teamwork 99 contre 11 : stretch index | 19,85 contre 19,94 m (ticket 04) | plus compact sur 5 affiches sur 5 : Δ moyen +0,26 m, erreur type 0,06 m |

Mesures sur le code final, après la correction A1 : défenseurs près du porteur sur 3 matchs ; profil Marking sur 4 matchs ; profil Teamwork sur 5 affiches jouées dans les deux sens (10 matchs).

**Indicateurs, sans réglage avant le ticket 22** (10 matchs, mêmes graines)

| Indicateur | Avant | Après | Réel |
|---|---|---|---|
| Tirs par équipe | 17,75 | 11,25 | 8-15 |
| Buts par match | 5,3 | 1,4 | 2-3,5 |
| Tacles par match | 86 | 72,4 | 30-40 |
| Passes réussies | 64,3 % | 70,5 % | 70-90 % |
| Hors-jeu par match | 1,1 | 0,9 | 3,2-3,5 |
| Couverture du presseur (toutes zones) | 79,5 % | 70,4 % | — |
| km par joueur de champ | 23,2 | 20,7 | 9-14 |

**Points ouverts**
- La couverture n'existe plus dans la moitié adverse : c'est voulu. L'indicateur de couverture, mesuré sur tout le terrain, baisse donc.
- Le marqueur reste plus loin que sa distance visée (3,7 m pour une cible de 1 m) : il suit un attaquant qui bouge et arrive avec retard. Ce suivi pourra relever d'Anticipation, au ticket 09.
- Les tacles restent au-dessus du réel (réserve déjà transmise au ticket 22).
- Le hors-jeu tombe à 0,3 par match avant la correction A1, à 0,9 après : **réserve acceptée par le propriétaire** (voir plus bas).

## Revue et décision sur le hors-jeu (30/10/2026)

**Revue `simulafoot-reviewer`.** Aucun défaut bloquant.
- Trois défauts mineurs, corrigés et testés :
  - le gardien qui sort sur le porteur n'est plus affiché « quitte le bloc » ;
  - un attaquant qui recule après un hors-jeu sifflé n'est plus marqué ;
  - un porteur pile sur le but ne reçoit plus de couverture.
- Test de la couverture renforcé : sa place égale la place théorique plus l'erreur de Positioning du joueur, et cette erreur est la même que dans le bloc.
- Constat majeur M1 : le marqueur, placé côté but, remet en jeu l'attaquant qu'il marque et casse le piège du hors-jeu.

**Trois versions mesurées** (10 matchs, mêmes graines) :

| | Marquage côté but (retenu) | Tenir la ligne | Ligne, et seuls les attaquants en jeu sont marqués |
|---|---|---|---|
| Hors-jeu par match | 0,3 | 0,5 | 0,7 |
| Buts par match | 1,8 | 3,0 | 1,6 |
| Tirs par équipe | 12,35 | 10,1 | 10,3 |
| Marking 99 contre 11 (médianes) | 3,66 contre 5,57 m ✓ | 4,43 contre 4,29 m ✗ | 7,77 contre 4,25 m ✗ (échantillon de 260 instants) |

**Décision du propriétaire (30/10/2026) : marquage côté but, sans tenir la ligne.**
- Dans les 25 derniers mètres, autour de la surface, les défenseurs réels défendent côté but. Le piège du hors-jeu se joue plus haut.
- Tenir la ligne ne faisait gagner que 0,2 hors-jeu par match, et annulait l'effet de Marking.

**Réserve acceptée : hors-jeu à 0,3 par match** (réel 3,2-3,5).
- L'essentiel de la chute précède ce ticket : 3,1 par match au ticket 23 (mesure du 29/10/2026), puis 1,1 dès le ticket 25 (`4d71418`).
- Elle relève d'un diagnostic à part ; ce ticket ne la corrigera pas par réglage.

## Comments

**30/10/2026, passage 1 de `/valider-ticket-simulafoot`**
- Expert : APPROVED_WITH_RESERVATIONS (empreinte `d706d641…`), après trois vérifications qu'il a demandées. Le critère Teamwork est démontré : plus compact sur 5 affiches sur 5.
- QC : VALIDÉ.
- Clôture : non journalisée, deux réserves étant à trancher par le propriétaire.
- Réserve A1, rôles sans mémoire : le presseur changeait de main puis revenait en moins de 1 s dans 14,2 % des changements (environ 100 fois par match). **Le propriétaire a choisi de la corriger** (« Corriger A1, A2 au 09 », 30/10/2026).
- Réserve A2, aucun rôle pendant une passe en vol (36 % du temps de jeu) : **rattachée au ticket 09 par le propriétaire** (même réponse). Le ticket 09 reprend le constat et deux critères.
- Réserve A3, facultative : l'effet de Teamwork est réel mais faible. À revoir au ticket 22.

**Correction A1 (30/10/2026)**
- Le presseur et la couverture restent à leur titulaire, pour le même porteur, tant qu'un autre ne peut pas arriver au moins 0,3 s avant lui (`HOLD_MARGIN_S`, marge proposée par l'expert et retenue par le propriétaire en choisissant de corriger A1).
- Le marqueur n'a pas de mémoire. Avec elle, le marqueur attitré décrochait de son attaquant et l'effet de Marking disparaissait. Mesuré sur 4 matchs :

| | Sans mémoire (passage 1) | Mémoire partout | Retenu : presseur et couverture seulement |
|---|---|---|---|
| Ping-pong du presseur | 14,2 % | 0,3 % | **0 %** |
| Ping-pong du marqueur | 15,4 % | 0 % | **3,7 %** |
| Rôles tenus 0,3 s ou moins (presseur / couverture / marquage) | 14,8 / 21,0 / 33,0 % | 0,6 / 5,5 / 18,4 % | **0,7 / 5,5 / 22,9 %** |
| Marking 99 contre 11 (médianes) | 3,66 contre 5,57 m | 5,50 contre 5,32 m ✗ | **4,21 contre 5,74 m** |

- Les marquages courts (22,9 % de rôles tenus 0,3 s ou moins) viennent surtout des passes en vol, qui coupent les rôles : c'est la réserve A2, rattachée au ticket 09.
- Test ajouté : `test_roles_stay_with_their_holder_unless_another_arrives_clearly_sooner`.
- Suite complète : 2 111 passés, 13 désélectionnés, 0 échec.

**30/10/2026, passage 2 de `/valider-ticket-simulafoot`** (empreinte `ea07160c…`, après la correction A1)
- Expert : APPROVED. Les réserves du passage 1 sont traitées : A1 corrigée, A2 rattachée au ticket 09, A3 facultative (ticket 22). Anomalie facultative : le ticket annonçait 8 tests au lieu de 11, corrigé.
- QC : VALIDÉ.
- Clôture : **VALIDÉ**, journalisée dans `.claude/qc/journal.jsonl`.
- À surveiller au ticket 22, sans réglage d'ici là : 1,4 but par match (réel 2-3,5), 72,4 tacles (réel 30-40), 20,7 km par joueur de champ (réel 9-14), 0,9 hors-jeu par match (réel 3,2-3,5).
- À traiter au ticket 09, avec A2 : mesurer la relève du presseur après élimination. Le temps d'arrivée ne tient pas compte de la direction, donc un défenseur battu mais encore proche peut rester presseur.
