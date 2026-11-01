# 11: Transition défense-attaque

**What to build:** Après une récupération : première passe pour sortir de la zone de pression, appels immédiats dans la profondeur, choix entre contre-attaque rapide et conservation du ballon selon l'espace et le nombre d'adversaires derrière le ballon.

**Attributs :** Vision, Decisions, Off the Ball, Anticipation.

**Blocked by:** 03, 06.

**Status:** livré (01/11/2026), validé expert + QC

- [x] Part des contre-attaques après récupération dans une fourchette réelle (à sourcer) : fourchette réelle **non trouvée** (définitions différentes selon les études) ; moteur : contre-attaque choisie sur 36 % des récupérations (indicateur, voir plus bas)
- [x] Choix entre contre-attaque et conservation mesurablement lié à l'espace disponible : contre-attaque choisie à 65,5 % quand elle est jouable, 29,6 % sinon (voir réserve sur l'effet du critère en match)
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée (suite complète : 2 232 passés, 13 désélectionnés, 0 échec, 01/11/2026, après le correctif A2)

## Réalisation (01/11/2026)

**Diagnostic avant le code** (`e8114a0`, 6 matchs, graine d'audit) : la transition offensive était reconnue (ticket 03) mais ne changeait rien au jeu. Après une récupération dans son camp, tiers offensif atteint en 15 s dans 14 % des cas, tir dans 0,5 %. Un quasi-surnombre n'était pas mieux exploité (7 %).

**Constantes validées par le propriétaire (01/11/2026)** — part réelle des contre-attaques non trouvée ; indicateur seulement : 13 % des possessions après récupération finissent par un tir cadré (Silva et al. 2005, Coupe du monde 2002, autre définition) :
- contre-attaque jouable si les adversaires de champ derrière le ballon dépassent de 2 au plus les coéquipiers de champ devant lui ;
- choix du porteur réglé par Decisions, même courbe que ses autres choix (99 → 95 %, 55 → 70 %, 11 → 45 % de prendre le bon) ;
- contre-attaque : seule une passe qui fait avancer est envisagée, valeur selon la progression seule ; sous pression (adversaire à 5 m), la passe en retrait reste possible avec la même valeur, donc après toute passe vers l'avant (réserve A2 de l'expert, variante validée par le propriétaire : « Ok avec ta recommandation », 01/11/2026) ; conduite deux fois plus volontiers sans adversaire à 5 m ; les coéquipiers devant le ballon relancent un appel 15 m plus loin vers l'avant dès qu'ils ont perçu la récupération (délai de réaction d'Anticipation), ligne du hors-jeu respectée comme avant ;
- conservation : valeur d'une passe 0,7 + 0,3 × progression (sûreté d'abord) ;
- le choix dure la transition offensive (8 s), s'arrête au dernier tiers ou à la perte.

**Code**
- `v2engine/decision.py` : `counter_is_favorable`, `choose_transition` ; `evaluate_options` et `choose_action` prennent le mode de l'équipe.
- `v2engine/transition.py` (nouveau) : `TransitionPlay`, choix par récupération, mis à jour une fois par tick.
- `v2engine/cerveau.py` : appel dans la profondeur en contre-attaque ; `v2engine/off_ball.py` : `COUNTER_RUN_DEPTH_M`.
- `v2engine/match.py` : branchement (mode transmis à `choose_action`).
- Tests : `tests/test_v2engine_transition.py`, 10 tests.
- Aucun attribut nouveau ni double effet : Decisions choisit (son rayon), Vision et Off the Ball servent comme avant, Anticipation par le délai de réaction existant.

**Revue `simulafoot-reviewer` (01/11/2026)** : aucun bloquant ; trois majeurs corrigés :
- M1 : un ballon rendu au gardien était toujours classé « contre-attaque jouable » (gardiens exclus du comptage) ; plus de choix de transition pour le gardien ni sur le coup franc d'un hors-jeu (balle arrêtée, pas une récupération dans le jeu) ;
- M2 : en contre-attaque sans passe vers l'avant, toutes les passes valaient 0 et la cible devenait arbitraire ; l'option passe n'existe plus dans ce cas ;
- M3 : tests ajoutés (arrêt au dernier tiers et à la perte, pas de choix dans le dernier tiers, pour le gardien, après un hors-jeu, à l'engagement ; mode transmis par le match).
- Mineurs laissés en l'état : saut de valeur à gain nul (conforme à « seule une passe qui fait avancer compte ») ; ancre poussée au-delà de la ligne de but ramenée sur le terrain ; `measure_v2_decisions.py` déjà cassé avant ce ticket (signature de `_step_ball`).

**Mesures (code final, après le correctif A2, 4 matchs, graine d'audit)**

| Choix à la récupération | Contre-attaque choisie |
|---|---|
| Contre-attaque jouable (18 % des choix) | 65,5 % |
| Non jouable | 29,6 % |

| Effet en match (tiers offensif atteint en 15 s) | Contre-attaque | Conservation |
|---|---|---|
| Toutes récupérations | 40,6 % | 25,3 % |
| Récupération dans son camp | 31,8 % | 13,6 % |
| Récupération entre 20 et 40 m | 22-23 % | 6,7-6,8 % |

| Indicateur (banc, 4 matchs, mêmes graines) | Avant | Après | Réel |
|---|---|---|---|
| Tirs par équipe | 7,9 | 9,625 | 8-15 |
| Buts par match | 2,0 | 2,25 | 2-3,5 |
| Tirs de contre par match, récupération dans son camp | 1,75 | 3,5 | — |
| Tirs de contre par match, récupération dans le camp adverse | 10,25 | 11,25 | — |
| Tacles par match | 55,75 | 54,0 | 30-40 |
| Hors-jeu par match | 1,0 | 1,0 | 3,2-3,5 |
| Pertes en transition (part des récupérations) | 22,5 % | 23,4 % | — |

**Réserve A1 de l'expert, acceptée par le propriétaire (effet du critère en match).** À hauteur de récupération égale, une contre-attaque « non jouable » progresse autant qu'une « jouable » (20-40 m : 25,0 contre 26,0 % ; 40-60 m : 61,2 contre 60,8 %), et n'est reperdue en moins de 5 s qu'un peu plus souvent entre 40 et 60 m (25,7 contre 18,9 %), pas entre 20 et 40 m (20,3 contre 21,4 %). Le choix suit bien le critère, mais le moteur punit encore peu une contre-attaque lancée en infériorité : la défense ne la sanctionne pas assez (rôles défensifs, repli, ticket 10). À revoir aux tickets 10 et 22, sans réglage ici. Après le correctif A2 (01/11/2026), premier signe de sanction entre 20 et 40 m : une contre-attaque non jouable est reperdue en moins de 5 s dans 27,9 % des cas, contre 21,0 % pour une jouable (40-60 m : 26,0 contre 27,4 %).

**Déterminisme** : même empreinte de trace sur deux exécutions (10 minutes de match, graine d'audit), avant et après le correctif A2 (`56671ff232bd09ae`, 245 décisions).

## Comments

- 01/11/2026, passage 1 (base `e8114a0`, empreinte `3fa94572`) : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture non journalisée (code modifié ensuite). Réserves : A1, le critère d'espace décide du choix mais pas de l'issue en match (renvoi aux tickets 10 et 22) ; A2, le porteur pressé en contre-attaque n'avait plus de passe ; A3 (facultatif), décompte de la suite absent des preuves. QC : ligne Anticipation de `CARTE_ATTRIBUTS_V2.md` à compléter (fait).
- 01/11/2026, correctif A2 : le correctif proposé par l'expert (passe en retrait avec la valeur de conservation) annulait presque l'effet de la contre-attaque (tiers offensif en 15 s depuis son camp : 18 % au lieu de 38 %). Variante retenue par le propriétaire (« Ok avec ta recommandation ») : passe en retrait possible sous pression, avec la valeur de contre-attaque, donc après toute passe vers l'avant (31,8 %).
- 01/11/2026, passage 2 (base `e8114a0`, empreinte `96b0a637`) : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ. A2 du passage 1 levée. Réserve A1 acceptée par le propriétaire (« J'accepte A1 ») : au ticket 10 puis au ticket 22, remesurer sur au moins 10 matchs avec le même découpage par hauteur et par jouable / non jouable. Facultatif laissé : A2, porteur pressé en contre-attaque sans aucun coéquipier utile, toutes les passes valent 0 et la cible est arbitraire (rare : seulement si Decisions rate son meilleur choix). À surveiller : longueur d'équipe avec ballon (44,3 m) et hors-jeu (1,0 par match) à la recalibration du hors-jeu ; seuil de pression à 5 m à l'écran. QC : ancre ramenée sur le terrain non vérifiée (mineur), lignes vides en trop dans le test.
