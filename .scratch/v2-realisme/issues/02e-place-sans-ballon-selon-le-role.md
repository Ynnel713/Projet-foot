# 02e: Place de référence sans ballon selon le rôle

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le repli défensif dépend du rôle (ailier qui défend ou reste haut)). **Catégorie :** placement.

**Constat vérifié :** sans ballon, le bloc se cale sur la hauteur de la dernière ligne et se resserre à 32 × 40 m pour tous (`bloc.py:193-199`) ; rien ne distingue un ailier qui suit son latéral d'un ailier qui reste prêt pour la contre-attaque.

**What to build:** Décalage propre au rôle sans ballon : ailier de couloir qui redescend sur la ligne du milieu, ailier ou avant-centre qui reste haut (voir aussi 09f), milieu récupérateur devant la défense. Même mécanisme que 02d, situation sans ballon.

**Attributs :** aucun

**Blocked by:** 02b (Largeur de référence propre à chaque poste); 02c (Rôle de poste par défaut, porté par le joueur et tracé).

**Bloque :** 02h, 09d, 09f, 10a, 10d, 10f.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : réutilise le décalage du 02d.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ailier de couloir contre ailier qui reste haut : écart de hauteur sans ballon d'au moins la valeur validée
- **Statistiques (séries de matchs) :** 20 matchs : hauteur moyenne sans ballon par rôle

## Acceptance criteria

**Critères chiffrés posés avant le code (06/11/2026)** : (1) même joueur, rôle ailier de couloir contre avant-centre, sans ballon : au moins 8 m d'écart de hauteur (11 m de décalage de départ, un peu comprimés par le bloc) ; (2) piston (placé au milieu) au moins 8 m plus bas que le latéral défensif ; (3) forme sans ballon toujours 32 × 40 m, centre du bloc conservé (somme des x inchangée) ; (4) personne plus bas que la dernière ligne de la forme de départ (les rôles ne font pas redescendre un milieu derrière les défenseurs ni ne changent la ligne défensive), équipe visiteuse en miroir ; (5) rôle absent ou vide : place identique à avant 02e, et le jeu avec ballon (02d) inchangé ; (6) 20 matchs à graines égales, hauteur moyenne réelle sans ballon, table active contre table vide : ailier de couloir au moins 4 m plus bas, piston au moins 5 m plus bas, avant-centre et buteur axial pas plus bas (écart ≥ −1 m) ; tirs et buts par match relevés (sans seuil, repris en 05 et 06) ; (7) deux exécutions à graine fixée, même empreinte.

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (proposées par Claude, validées par délégation ; chiffres réels non trouvés, ordres de grandeur tactiques)
- [x] Décalages sans ballon par rôle documentés (`ROLE_PLACE_WITHOUT_BALL` et docstring de `v2engine/bloc.py`)
- [x] Hauteurs moyennes sans ballon différentes selon le rôle (20 matchs) — **sauf le piston, voir Comments**
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 06/11/2026 : `ROLE_PLACE_WITHOUT_BALL` (20 rôles, un test vérifie qu'aucun n'est oublié), même mécanisme que `ROLE_PLACE_WITH_BALL` : décalage appliqué à la forme de départ avant la mise à l'échelle 32 x 40 m, forme mesurée sur les places décalées (`Bloc.shapes_low`), centre du bloc conservé. **Règle ajoutée** : personne ne passe derrière la dernière ligne de la forme de départ (`without_ball_place`), pour que la ligne défensive reste celle des défenseurs (`Bloc.update` ne change pas). Avec ballon (02d) inchangé ; test « la place sans ballon ne dépend pas du rôle » remplacé par « un rôle sans place ne change rien » (le comportement qu'il affirmait est celui que ce ticket change).
- Critères 1 à 5 tenus par des tests de scène (`tests/test_v2engine_bloc.py`, 33 passés) : ailier de couloir contre avant-centre ≥ 8 m ; piston du milieu contre latéral défensif ≥ 8 m sans passer derrière les défenseurs ; forme 32 x 40 m et centre conservés ; dernière ligne = défenseurs pour les deux équipes.
- Critère 6, 20 matchs (graine d'audit 20260923, `scripts/measure_roles_v2.py --sans-ballon`, table active contre `--sans-role-sans-ballon`), hauteur moyenne réelle de l'équipe sans ballon : ailier de couloir −5,7 m (AD) et −5,9 m (AG) **tenu** ; avant-centre +0,8 m **tenu** ; buteur axial −0,7 m **tenu** (seuil −1 m) ; défenseur central +0,5 m ; récupérateur −2,4 m ; sentinelle −1,8 m ; ailier intérieur −2,0 m (AD) et −1,1 m (AG). **Piston : +0,6 m (arrière droit) et −0,9 m (arrière gauche), critère « au moins 5 m plus bas » NON TENU.** Cause : dans les données le piston est toujours un arrière droit ou gauche, donc dans la bande des défenseurs ; la règle de la dernière ligne le garde sur leur ligne, et sa constante (−10 m) ne joue que pour un piston parti du milieu (cas du test unitaire). Le critère a été posé avant d'avoir vu ce lien entre poste et bande ; il n'est pas modifié ici, l'expert tranche si le comportement (piston sur la ligne des défenseurs sans ballon) est le bon.
- Les décalages mesurés sont plus faibles que les constantes (récupérateur −5 m posé, −2,4 m mesuré) : le bloc est remis à l'échelle 32 x 40 m après le décalage, et la hauteur réelle subit aussi Positioning, Teamwork et le pressing.
- Effet sur le jeu (`measure_v2`, 20 matchs) : tirs par équipe 26,6 → 24,3 (−9 %), buts par match 4,05 → 3,35, corners 12,85 par match. Relevé sans seuil : calibration reprise aux tickets 05, 06 et 18d.
- Déterminisme : deux exécutions à graine fixée (2 matchs), même empreinte `e1492f0941c4ab61`. Suite complète : 2 452 passés, 14 désélectionnés, 24 min 29 s (attendu 2 446 de CLAUDE.md + le test d'API de la caméra, qui est dans l'arbre de travail, + 5 tests ajoutés ici).
- Durée : estimée 1 h 50, réelle environ 1 h 40 (non chronométrée), écart environ −9 %. Temps machine, hors total : suite complète 24 min, trois mesures de 20 matchs en parallèle.
- 06/11/2026 : passage 1 de l'expert `APPROVED_WITH_RESERVATIONS`, QC `VALIDÉ`, clôture `VALIDÉ` (journal, base `75c2558`, empreinte `5ab7ea0f`). Réserves acceptées d'office, règle permanente du propriétaire (« Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026). **A1** : le critère 6 « piston au moins 5 m plus bas » est **amendé** : le piston des données est toujours un arrière, il se tient sur la ligne des défenseurs sans ballon (+0,6 m et −0,9 m, 38 à 39 m comme le latéral, contre 34,3 m pour le défenseur central) ; c'est le comportement voulu, et la constante −10 m du piston ne s'exerce que pour un piston parti de la bande du milieu, vérifié par le test de scène. **A2** : `data/joueurs.xlsx` est une modification d'un autre chantier, présente avant ce ticket, non commitée avec lui. A3 : les +3 et +5 des attaquants et le −10 m du piston n'ont pas d'effet absolu mesurable dans un bloc fixé à 32 m ; à revoir en 09f et 10. A4 : sans objet. QC : VALIDÉ ; réserve sur le piston identique, signalée à l'expert.
