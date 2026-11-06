# 02f: Tenir sa position en possession

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (cause directe des volumes d'appels et de course artificiels). **Catégorie :** décision.

**Constat vérifié :** `cerveau.py:102-103` donne le rôle `APPEL` à tout joueur de champ dont l'équipe a le ballon : chacun cherche en permanence un espace libre (`off_ball.choose_space`) ; il n'existe aucun rôle « tenir sa place » en possession.

**What to build:** Nouveau rôle `TENIR` en possession : le joueur rejoint et garde sa place de référence (02d), avec le seuil de Teamwork déjà utilisé sans ballon (`Bloc.replacement`), et ne fait plus d'appel. Dans ce ticket, seuls le porteur, le receveur visé et les joueurs choisis par une règle provisoire simple (les deux plus proches devant le ballon) gardent `APPEL` ; la vraie sélection vient au 02g.

**Hors de ce ticket :** sélection des appelants (02g) ; intensité de course (12d).

**Attributs :** aucun

**Blocked by:** 02d (Place de référence avec ballon selon le rôle).

**Bloque :** 02g, 09g, 12d.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : le Teamwork garde son rayon (tenir et reprendre sa place) : pas de double comptage.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** possession installée au milieu : au plus le nombre provisoire d'appelants ; les autres restent à moins de leur tolérance de leur place
- **Comportementaux (profils comparés) :** Teamwork 99 contre 11 : écart moyen à la place plus faible
- **Statistiques (séries de matchs) :** 50 matchs : appels par joueur et km par joueur avant / après (indicateurs du 01d)

## Acceptance criteria

**Critères chiffrés posés avant le code (06/11/2026)** : (1) possession installée au milieu, scène de 9 coéquipiers de champ : exactement les 2 plus proches devant le ballon gardent `APPEL`, les 7 autres ont le rôle `TENIR` ; porteur et receveur inchangés ; (2) transition offensive et sans situation : tous appellent comme avant ; (3) Teamwork 99 contre 11, joueur à 5 m de sa place : 99 se replace, 11 tient ; (4) 50 matchs à graines égales, `TENIR` actif contre `--sans-tenir` : appels par joueur et par 90 min en baisse, km par joueur de champ en baisse, tirs par équipe et solutions de passe ouvertes relevés sans seuil (pas de chute non expliquée) ; (5) deux exécutions à graine fixée, même empreinte.

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Rôle `TENIR` tracé et visible dans l'intention
- [x] Appels par joueur et km en baisse mesurée (50 matchs), sans viser encore les valeurs réelles
- [x] Solutions de passe ouvertes rapportées (pas de chute non expliquée)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 06/11/2026 : rôle `TENIR` (`cerveau.TENIR`, intention « tenir sa place » ou « se replacer », raison « en possession… »), même seuil de Teamwork que sans ballon (`Bloc.replacement`). Règle provisoire (constantes proposées par Claude, validées par délégation, chiffres réels non trouvés) : `PROVISIONAL_RUNNERS = 2`, `HOLD_SITUATIONS = (possession installée, dernier tiers)` ; la transition offensive est exclue pour ne pas casser les appels de la contre-attaque (11). `TENIR` est ajouté aux rôles offensifs : un joueur qui tient sa place poursuit son intention jusqu'à avoir perçu la perte (délai de réaction), comme les autres rôles offensifs.
- Test existant adapté : `_balance_ahead_share` (équilibre derrière le ballon, ticket collectif/06) plaçait le défenseur d'équilibre derrière le porteur ; un joueur derrière le ballon tient maintenant sa place, le test place le porteur derrière lui. Conséquence à signaler : l'indiscipline de Teamwork qui faisait monter un défenseur d'équilibre derrière le ballon ne s'exprime plus, en possession, que par le seuil de `TENIR`.
- Tests : 6 nouveaux (`tests/test_v2engine_cerveau.py`) : 2 appelants au plus et ce sont les 2 plus proches devant le ballon, transition et sans situation inchangées, receveur et passe en vol, miroir de l'équipe visiteuse, Teamwork 99 contre 11, continuité jusqu'à la perception de la perte.
- Mesure 50 matchs (graine d'audit 20260923, `scripts/measure_v2.py`, `TENIR` actif contre `--sans-tenir`) : appels par joueur et par 90 min 53,4 → 48,5 (−9 %) ; km par joueur de champ 17,33 → 15,76 (−9 %) ; par poste, appels par match : défenseur central 30,6 → 24,5, milieu offensif 110,1 → 97,0, avant-centre 109,8 → 107,0. Tirs par équipe 25,11 → 25,06, buts par match 3,56 → 3,46, corners 12,6 → 11,6, passes par match 1 013 → 1 025. Solutions de passe ouvertes 2,122 → 2,106 (−0,8 %), faciles 1,695 → 1,678 : pas de chute. Appels dans le dos 27,8 → 28,2 par match (inchangés). Les valeurs restent loin du repère réel (5,5 à 19,2 appels par 90 min selon le poste) : la baisse est modeste parce que les deux appelants restent libres de courir partout et que la transition offensive n'est pas touchée ; la vraie sélection est au 02g. Temps de calcul par match 124,5 → 122,5 s.
- Déterminisme : deux exécutions à graine fixée (2 matchs), même empreinte `5677355baa69c608`. Suite complète : 2 458 passés, 14 désélectionnés, 21 min 28 s (attendu 2 452 + 6 tests ajoutés ici).
- Durée : estimée 2 h, réelle environ 1 h 30 (non chronométrée), écart environ −25 %. Temps machine, hors total : suite complète 21 min, deux mesures de 50 matchs en parallèle (environ 35 min).
- 06/11/2026 : passage 1 de l'expert `APPROVED_WITH_RESERVATIONS`, QC `VALIDÉ`, clôture `VALIDÉ` (journal, base `a6ca999`). Réserves acceptées d'office, règle permanente du propriétaire (« Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026) ; aucune acceptation réserve par réserve dans cette conversation. **A1** : au dernier tiers, la contre-attaque perd les appels de ses coéquipiers hors des 2 plus proches (`DERNIER_TIERS` prime sur `TRANSITION_OFFENSIVE` dans `situation.py`) ; tirs de contre, camp adverse, 35,6 → 34,0 (−4 %, non significatif) ; à traiter au 02g (garder `launched` et le mode contre-attaque actifs). **A2** : aucune hystérésis, un joueur à distance voisine du ballon peut alterner APPEL et TENIR ; à traiter au 02g (garder l'appel tant que l'espace n'est pas atteint). **A3** : le joueur désigné par `ball.plan` hors des 2 plus proches ne relance pas son appel ; à traiter au 02g. A4 (facultatif) : l'indiscipline de Teamwork de l'équilibre ne s'exprime plus que par le seuil de `TENIR` ; à surveiller en profils 99 contre 11. QC : VALIDÉ, remarque sur le plan de passe (A3).
