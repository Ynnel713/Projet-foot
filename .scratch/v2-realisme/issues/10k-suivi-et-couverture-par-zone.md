# 10k: Suivi du pressing d'équipe et couverture selon la zone

**Chantier :** `v2-realisme`. **Priorité :** P1 (un latéral ne doit pas abandonner son couloir pour un joueur central quand un central ou un milieu est libre). **Catégorie :** décision.

**Constat vérifié (21/11/2026, état `a8cecf5`)** : remarqué à l'écran par le propriétaire (latéral gauche qui rentre dans l'axe quand le porteur adverse est au milieu, ailier laissé libre, centraux bien placés). Mesure sur 8 matchs (graines du banc, porteur adverse à moins de 10 m de l'axe dans le tiers médian, 131 667 ticks-latéral) : le latéral tient son bloc 78 % du temps (à 1,5 m de sa place), marque 15 %, couvre 4 %, presse 2 %. Le marquage passe à 99,9 % par le suivi du pressing d'équipe (`defense.py`, ticket `v2-collectif/08`) : 20 111 ticks contre 22 par la règle des 25 m. Il y suit surtout des joueurs centraux (MC, MDC, MOC, BU : 73 %), alors qu'un central est libre dans 93 % des cas. Couvreur, il est à 7 m de l'axe. Cause : suiveurs et couvreur sont choisis au plus proche (suivi) ou au premier arrivé (couverture), sans la zone de responsabilité que le 10a a donnée au seul presseur.

**What to build:** Appliquer la zone du 10a aux deux autres choix au plus proche : (1) suivi du pressing d'équipe, règle stricte (choix du propriétaire du 21/11/2026, option 1, voir Réalisation) : seuls les suiveurs dont la zone contient le receveur le suivent, le plus proche tel qu'il le perçoit (08e) comme avant ; personne de sa zone : il n'est pas suivi ; le suiveur en place garde son receveur tant qu'il reste dans sa zone, le lâche sinon ; (2) couverture : parmi ceux dont la zone contient le point de couverture et qui arrivent au plus `PRESS_ZONE_MARGIN_S` après le plus rapide, le premier arrivé ; aucun : tous, comme avant ; `HOLD_MARGIN_S` du titulaire conservée. Sans bloc (scènes de test) : comportement d'avant.

**Attributs :** aucun nouveau (règle sans constante nouvelle).

**Constantes :** aucune nouvelle ; zone (`ZONE_DEPTH_M` 8 m, `ZONE_WIDTH_M` 10 m) et marge `PRESS_ZONE_MARGIN_S` = 1 s validées par le propriétaire au 10a (18/11/2026). Ticket lancé par le propriétaire le 21/11/2026 (« Lance le sans découpage »).

**Lien avec l'existant :** étend `10a` (livré) ; respecte `10b`/`10b2` (le central sans couverture ne sort pas, réservations).

**Blocked by:** 10a.

**Bloque :** 10j.

**Status:** livré (21/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **2 h 20** |

**Estimation révisée (21/11/2026, en cours de route)** : 2 h 20 → 3 h, après l'échec de C1 à la première mesure (correction du suiveur gardé et nouvelle série) ; puis + 30 min annoncées pour l'option 1.

Confiance : moyenne. Hypothèses : réutiliser `in_zone` et `_press_pool` du 10a sans constante nouvelle ; pas de découpage (décision du propriétaire du 21/11/2026, total au-dessus du seuil indicatif de 2 h).
Temps machine, non compté : suite complète (environ 10 min) ; deux séries de 24 matchs (environ 20 min chacune).

## Tests

- **Unitaires (scène contrôlée) :** pressing d'équipe, receveur dans l'axe, latéral plus proche que le milieu dont la zone le contient : le milieu suit, même plus lent (règle stricte, pas de marge) ; personne dont la zone contient le receveur : il n'est pas suivi ; receveur pris dans le couloir du latéral puis rentré dans l'axe : le latéral le cède au milieu de la zone, ou le lâche si personne ne l'a dans sa zone. Couverture : porteur dans l'axe, latéral premier arrivé, milieu de la zone dans la marge : le milieu couvre. Sans bloc : comme avant.
- **Statistiques (séries de matchs) :** 24 matchs appariés (graines `AUDIT_SEED + k`, pas 0,1 s), sonde `.scratch/v2-realisme/mesures/10k-lateraux.py`.

## Acceptance criteria

Critères chiffrés posés avant le code (21/11/2026), même contexte que le constat (porteur adverse dans l'axe, tiers médian) :

- [x] C1 : temps où un latéral suit un receveur central (à moins de 10 m de l'axe) pendant un pressing d'équipe en baisse d'au moins 50 % (− 88 %)
- [x] C2 : part du temps où le latéral est à moins de 8 m de l'axe en baisse (9,5 % → 2,4 %)
- [x] C3 : temps où un latéral couvre en baisse (− 68 %)
- [x] C4 : buts, tirs, pertes, fautes par match dans ± 10 % — buts − 4 %, tirs − 9 %, fautes − 1 % ; **pertes − 12 %, hors critère, accepté par le propriétaire le 21/11/2026** (« j'accepte » : effet attendu d'un pressing d'équipe qui suit moins, volume à recaler à la calibration)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (3 448 passés, 0 ignoré, 14 désélectionnés = 3 441 + 7)

## Réalisation (21/11/2026)

**Code** (`v2engine/defense.py`) : `DefensiveRoles._zone_pool` (candidats de la zone dans la marge du 10a, `_press_pool` s'appuie dessus, comportement du presseur inchangé) ; couverture : premier arrivé parmi `_zone_pool(covers, point de couverture)` ; suivi du pressing d'équipe : règle stricte (zone seule, pas de repli), suiveur en place qui lâche le receveur sorti de sa zone. Aucune constante nouvelle. Sans bloc : comme avant. Tests : `tests/test_v2engine_suivi_zone.py` (7 tests : milieu de la zone plutôt que latéral, suiveur de la zone plus lent qui suit quand même, receveur sans suiveur de sa zone non suivi, couvreur de la zone, latéral qui cède puis lâche un receveur rentré dans l'axe, déterminisme d'un match de 2 min).

**Trois versions mesurées** (24 matchs appariés, graines `AUDIT_SEED + k`, pas 0,1 s ; sonde `.scratch/v2-realisme/mesures/10k-lateraux.py`, sorties `10k-avant.*`, `10k-repli.txt`, `10k-apres.*` ; « avant » rejoué depuis un worktree de `a8cecf5`, empreintes identiques à la première série : moteur d'origine déterministe) :
1. Filtre de zone avec repli sur les seules nouvelles prises : C1 − 6 % seulement. Diagnostic (4 matchs) : 94 % du suivi central du latéral venait d'un receveur pris dans son couloir puis gardé jusqu'à la fin du pressing (5 s) après être rentré dans l'axe.
2. Suiveur qui cède son receveur sorti de sa zone, repli « personne de la zone : le plus proche » : C1 − 18 %, va-et-vient des suiveurs + 93 %, buts + 19 %. Diagnostic : dans 89 % des cas restants, aucun suiveur de la zone disponible (tous déjà affectés 64 %, tirage Teamwork négatif 25 %), le repli renvoyait au latéral.
3. Règle stricte, sans repli (option 1, choisie par le propriétaire le 21/11/2026) : retenue.

| Porteur adverse dans l'axe du tiers médian (ticks-latéral) | avant | après (règle stricte) |
|---|---|---|
| latéral suivant un receveur central (C1) | 44 278 | 5 137 (− 88 %) |
| latéral à moins de 8 m de l'axe (C2) | 9,5 % | 2,4 % |
| latéral en couverture (C3) | 13 759 | 4 453 (− 68 %) |
| écart du latéral à sa place de bloc | 1,6 m | 0,2 m |
| écart en largeur latéral-ailier | 7,1 m | 5,9 m |
| suivi (tous receveurs) | 66 337 | 12 284 |
| changements de suiveur ; va-et-vient (A → B → A en moins de 1 s) | 31 456 ; 2 229 | 11 078 ; 969 |

| Par match | avant | après |
|---|---|---|
| buts | 4,92 | 4,71 (− 4 %) |
| tirs | 40,5 | 36,9 (− 9 %) |
| pertes de balle | 216,9 | 190,3 (− 12 %, accepté) |
| fautes | 19,5 | 19,3 |
| passes | 1 232 | 1 286 (+ 4 %) |
| duels d'épaule | 22,3 | 18,3 (− 18 %) |
| hors-jeu | 3,58 | 3,62 |

Effet secondaire : le pressing d'équipe suit cinq fois moins de receveurs, donc récupère moins (pertes − 12 %) ; passes par match et durée des possessions, déjà au-dessus du repère, montent un peu. À recaler à la calibration (`10j`, `v2-collectif/22a`), pas en rendant le couloir au latéral.

**Suite complète** : premier passage 2 échecs, 3 446 passés : `test_v2engine_central_couvert.py::test_the_covering_centre_back_keeps_the_holder_margin` (deux paramètres) ; le point de couverture de la scène était dans la zone du milieu défensif, qui prenait donc la couverture (comportement voulu du 10k). Scène adaptée (place du milieu hors de cette zone), le test vérifie toujours la marge `HOLD_MARGIN_S` du central. Second passage : 3 448 passés, 0 ignoré, 14 désélectionnés.

**Durée** : estimée 140 min (révisée à 210 en cours de route), réelle environ 190 min (+ 36 % sur l'estimation initiale) : C1 manqué à la première mesure (− 6 %), deux diagnostics et deux versions supplémentaires, option tranchée par le propriétaire, test du 10b2 à adapter. Temps machine hors total : cinq séries de 24 matchs, deux diagnostics de 4 matchs, deux suites complètes (19 min 53 et 20 min 35). Une série « après » perdue (processus lancé hors tâche de fond, tué), relancée.

## Comments

- 21/11/2026, passage 1 : expert `APPROVED` ; QC `VALIDÉ` (réserves de forme : test central_couvert adapté, écart des pertes) ; clôture journalisée `VALIDÉ`. Écart C4 (pertes − 12 %) accepté par le propriétaire avant la revue : « j'accepte ». Améliorations facultatives de l'expert : A1 (docstring de `tests/test_v2engine_suivi_zone.py` qui décrit encore la marge et le repli pour le suivi : non traité, modifier le fichier rouvrirait la revue), A2 (section Tests du ticket : alignée sur la règle stricte). À surveiller à la calibration (`10j`, `v2-collectif/22a`) : volume de récupération du pressing d'équipe, passes et durée des possessions ; à l'écran, receveur qui longe une frontière de zone sans recouvrement.

