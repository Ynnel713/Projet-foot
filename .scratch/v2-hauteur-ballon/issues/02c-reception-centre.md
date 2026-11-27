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

**Status:** livré (27/11/2026), validé expert + QC

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

- [x] Réponse du propriétaire à la question du contrôle de première, avant le code (27/11/2026 : interdit à la première retombée, sans constante)
- [x] Test : un ballon reçu à sa première retombée est classé « centre » ; le même ballon reçu après un rebond est classé selon `_pass_kind`
- [x] Test : `_danger_origin` suit la même règle
- [x] Test : un ballon qui remonte au-dessus de 0,5 m après un rebond n'est touché par aucun joueur sur son trajet (filtre de la l.1019 préservé)
- [x] Test : joueur qui entre dans la portée du ballon avant l'impact du pas → « centre » ; après l'impact → passe ordinaire
- [x] Contrôle des réceptions « centre » sur la piste du ballon (même méthode qu'au 02a1) : **amendé**, il n'en reste que 4 sur 50 matchs (pas 20) ; 4 sur 4 reçues avant le premier contact au sol, toutes visées, 1,7 à 2,3 s après la frappe (fin du vol prévu)
- [x] 50 matchs (graines 0 à 49) : réceptions « centre » par match comparées à la référence d'avant le 02a1 (2,9 ± 0,82) et au 02a1 (11,4) ; part des tirs d'origine « centre » et contrôles de première comparés au 02a1 ; écarts hors bruit (bruit A contre B) documentés et soumis au propriétaire (écart accepté le 27/11/2026)
- [x] Mêmes empreintes de trace sur deux exécutions à graine fixée ; suite complète au compte attendu ; V1 inchangée
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)

## Comments

**26/11/2026, ouverture (clôture `projet/02c-et-compte`)** : expert `APPROVED_WITH_RESERVATIONS` au passage 1. Réserve A1 (hypothèse fausse : `airborne` est aussi lu l.1019, garde du filtre de contact) et point facultatif A2 (premier contact au sol pendant le pas d'un contact) corrigés dans le ticket : variable distincte, `airborne` préservé, comparaison `entry·dt` / `first_contact_s`, deux critères ajoutés.

Passage 2 : expert `APPROVED`. À surveiller à l'implémentation : mémoriser « a touché le sol » avant l'appel à `_ground` (l.1039), qui le remet à zéro ; même règle exactement pour `_danger_origin` et `_received_as`.

**27/11/2026, implémentation.**

*Code* : `v2engine/ball_state.py`, champ `landed` (le ballon a touché le sol depuis son lancement ; remis à faux par `_launch_aerial` et `_ground`) et propriété `first_drop` (ballon qui redescend, `vz < 0`, sans avoir encore touché le sol). `v2engine/match.py` : `landed` passe à vrai quand `hauteur.step_height` rend un premier contact dans le pas ; au contact, `caught_first_drop` = en vol et pas encore au sol au début du pas, joueur entré avant l'impact du pas (`entry·dt < first_contact_s`), ballon qui redescend à l'instant d'entrée ; lu avant `_ground`. Il remplace `airborne` dans `_received_as` et `first_time` ; `_danger_origin` lit `ball.first_drop`. `airborne` reste le filtre de contact en hauteur (réserve A1). Aucune constante nouvelle.

*Décisions du propriétaire (27/11/2026)* : (1) jeu de première interdit sur un ballon cueilli à sa première retombée, sans constante (question du ticket) ; (2) **« centre » réservé au ballon qui redescend** : la relecture de la première version (règle du ticket, montée comprise) a trouvé 2 réceptions « centre » sur 6 qui étaient un coéquipier non visé touchant le ballon au pas même de la frappe, à 0 m et en montée ; en montée, le ballon est maintenant reçu comme une passe ordinaire ; (3) écart des réceptions « centre » accepté.

*Tests* : `tests/test_v2_reception_centre.py`, 12 tests (première retombée, après rebond, en montée, au sol, impact dans le pas avant et après l'entrée du joueur, jeu de première, `_danger_origin`, filtre de contact au-dessus de 0,5 m après un rebond, état `landed` au lancement, au rebond et au ballon posé). Suite complète : **3 597 passés, 0 ignoré, 14 désélectionnés** (3 585 + 12), 17 min 31 s.

*Série de 50 matchs* (graines 0 à 49, `scripts.bench_series 50`) : avant = `14a2a-apres.json` (`.scratch/v2-realisme/mesures/`, moteur identique hors 02c), après = `02c-apres2.json` (règle de la redescente ; `02c-apres.json` : première version, règle du ticket) ; bruit = séries de référence A/B du 02a1 (`02c-tolerance.py`, `02c-tolerance.txt`). 2 821 indicateurs : 3,8 % hors bruit (3,2 % entre A et B).
- **Hors bruit, attendu** : réceptions contrôlées « centre » **10,3 → 0,08 par match** (4 sur 50 matchs ; 12,5 × le bruit ; 2,9 avant le 02a1, 11,4 au 02a1). Le seuil de contact de 0,5 m (02a1) ne laisse qu'environ 0,05 s pour cueillir un ballon à sa première retombée : sans tête ni poitrine (ticket 03), le centre reçu en l'air est quasi impossible. Les réceptions reclassées vont aux passes ordinaires, le total est dans le bruit.
- **Dans le bruit** : buts 4,22 → 4,98 par match (0,9×), tirs par équipe 13,26 → 13,86, passes de première 178,3 → 178,6 par match, passes réussies 82,3 → 82,2 %, possession d'équipe 20,5 s, grosses occasions d'origine « centre » 2,3 → 1,6 % (0,9× ; `_danger_origin` compte un ballon en vol vers un joueur, même trop haut pour être touché). Aucun tir d'origine « centre », avant comme après.
- Temps de calcul 156 → 181 s par match : série lancée en même temps que la suite complète (processeurs partagés) ; le 02c n'ajoute qu'un booléen par pas.
- **À noter pour `v2-collectif/22a` et le ticket 03** : jusqu'au 03, presque plus de centres reçus.

*Contrôle sur la piste du ballon* (`02c-controle-centres.py`, chute libre recalculée hors `hauteur.py`, sorties `02c-controle-centres*.txt`) : 4 sur 4 reçues avant le premier contact au sol, toutes visées, bas du ballon 0,07 à 0,52 m au début du pas, en descente (−8 à −11 m/s).

*Déterminisme* : empreintes complètes (`14a1-empreinte.py`, graines 0 et 1) identiques sur deux exécutions : `68ca83fe2fff7a48`, `802594b961fcf28a` (`02c-empreintes2-1.txt`, `-2.txt`). V1 : aucun fichier touché.

*Durée* : estimée 2 h, réelle environ 2 h 30 (+ 25 %), non chronométrée (horloge de la session hors attentes machine). Postes : analyse 15 min (15), développement 25 min (25), tests 30 min (25), intégration et vérifications 80 min (55). Cause : deuxième passage après la décision sur le ballon en montée (code, test, série, contrôle). Temps machine hors total : deux séries de 50 matchs (environ 50 min chacune), deux suites complètes (19 et 17,5 min), deux contrôles de centres, empreintes.

**27/11/2026, clôture (passage 1)** : expert `APPROVED` ; QC `VALIDÉ` ; clôture journalisée `VALIDÉ`. Aucune anomalie bloquante. A1 facultatif (expert) : le contrôle sur piste affiche l'instant d'impact sans le comparer à l'entrée du joueur (couvert par le test paramétré) ; à reprendre si le 03 réutilise ce contrôle. Non bloquants (QC) : `first_drop` de `_danger_origin` sans fenêtre d'impact (voulu) ; le test du filtre vérifie la hauteur en fin de pas. Points à surveiller : centres reçus quasi effacés jusqu'au 03 (à signaler au `v2-collectif/22a`) ; le 03 réutilise `first_drop` / `landed`, sans revenir à `z > 0 or vz != 0`.
