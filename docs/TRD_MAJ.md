# TRD — mises à jour postérieures à la v1.1

Complète `docs/TRD_SIMULAFOOT.pdf` (v1.1, 14/10/2026, état B6-c). Le PDF reste la référence de rédaction ; ce fichier porte les changements de statut depuis. Les commits sont cités par préfixe lu dans `git log`. Seuls les statuts vérifiés dans l'historique Git sont modifiés ; les chiffres sont ceux des documents du dépôt (`Plan architecte Simulafoot.md`, `docs/phase6_block_b_audit.md`, `docs/known_issues.md`).

## v1.2 — 15/10/2026 (état du dépôt : 44497d1)

### Statuts d'exigences modifiés

| ID | Statut v1.1 | Statut v1.2 | Preuve |
|---|---|---|---|
| EG-BAL-09 (B7 coups francs et mur) | Planifié | Implémenté | b0bb60c, ab826b6, 396411b, 5582b96, 71ac316, eaac0df ; clôture a6cf0cb |
| EG-BAL-10 (B8 contrôles variés) | Planifié | Implémenté (contrôles au sol B8-a, modulation B8-b, contact aérien corner et débordement B8-c1) | 250b71e, 927f470, 55bc0f1, c43b8b6, fa7a5d5, 5795235 |
| EG-VAR-03 (B6-d réaction du gardien sur penalty) | Planifié | Implémenté (Option 2 : glissement renforcé ; plongeons complets reportés à A1.2) | e8bb99e, 626dbce, 90cae5b |
| EG-VAR-05 / EF-LIV-04 (B6-e type de frappe au NLG, ticket 23) | Planifié | Implémenté (contradictions texte/type 157 → 0) | 88497f1, f5ba202, 2674de0, 2bc31e7 ; clôture c3ff089 |
| EG-JOU-05 (Bloc A) | Planifié | Partiel : étape 0 close, chantier 1 en cours (1a validé, 1b livré) | voir ci-dessous |
| EG-JOU-08 (couplage joueur-ballon, ticket 30) | Planifié | Planifié (A1.6) ; B7-a a posé le ballon immobile jusqu'à la frappe | d1614fa |

### Bloc B — clos
Récapitulatif complet : `docs/phase6_block_b_audit.md` section 19 (3d17175). Vrais lobs : ticket 42 (B8-c2 sans objet, aucun segment `pass_lob` sur 5 858). Ballon figé quand le passeur est inconnu : ticket 41 (étendu à `contre_attaque`, `construction_placee`, `une_deux`).

### Bloc A — nouvelles exigences vérifiées dans le code
| ID | Exigence | Prio. | Statut | Preuve |
|---|---|---|---|---|
| EG-JOU-09 | L'effectif affiché d'un clip est exactement l'ensemble des joueurs sur le terrain à la minute de l'événement ; un seul gardien par équipe ; tireur et assist des occasions présents à la minute | O | Implémenté | a5176f0, 7c845b8, 8cb93fb, 87b3669, 2a731f2, 1d57be2 : 0 joueur en trop ou manquant sur 1 552 clips |
| EG-JOU-10 | Géométrie de rôle : départ dérivé de la formation, course limitée par un ratio de vitesse ≤ 0,5 et par D ≤ 2,25·T² (constantes `_RUN_RATIO_MAX`, `_RUN_ACCEL_COEFF`, `_BEHIND_MIN_M`) ; supports tactiques déterministes | O | Partiel : moteur livré, neutre (aucun gabarit migré) ; migration 1c à 1f | 2d8f729, 5feb4b5, 078e886, 44497d1 |
| EG-JOU-11 | Sur les 100 matchs de la graine d'audit, le buteur rendu arrive à sa zone de tir (médiane ≤ 0,5 m) ; aucun segment de passe > 30 m/s sur le chemin ; clips dépassant 1,05 × vmax en forte baisse | O | Planifié (cibles du modèle A : écart 4,88 → 0,27 m ; dépassements 1 449 → 591 clips ; résiduel renvoyé à A1.1 et A1.5) | `Plan architecte Simulafoot.md` §3.2 |

### Suite de tests (indicateurs)
| Indicateur | v1.1 | v1.2 |
|---|---|---|
| pytest (suite principale) | 1 493 passés, 5 ignorés, 12 désélectionnés | 1 648 passés, 5 ignorés, 12 désélectionnés (44497d1, selon le plan ; suite relancée le 15/10 sans échec) |
| `npm run build` / `lint` | OK ; 0 erreur, 5 avertissements | non relancés en v1.2 |

### Tickets (section 11)
Ouverts depuis la v1.1 : 31 à 38 (NLG, rendu), 40 (type de contrôle au NLG), 41 (ballon figé), 42 (vrais lobs), 43 (images 0 et 1 non corrigées), 44 (rôles absents sur buts réels), 45 (gardien expulsé sans remplaçant, rattaché au ticket 17). Annoncés, non encore écrits : 46 (test aveugle `TestSegmentSpeedHeadroom`), 47 (passes > 30 m/s), 48 (départs scriptés contre placement adverse). Fermés ou résolus : 23, 33.

### Points ouverts ajoutés
- D-14 : D9.4.1 à D9.4.4, citées par l'Architecte, introuvables dans le dépôt : à retrouver ou à écarter.
- D-15 : validation de 1b ; lieu de traitement du ticket 42 (A1.6 ou B9) ; priorité des tickets 41 et 42.
- D-16 : exception sur `templates.py` pour chaque sous-étape du chantier 1 (périmètre explicitement inscrit au plan).

## v1.3 — 15/10/2026 (état du dépôt : d0a3411)

Les sous-étapes 1c, 1d et 1e-1 du chantier 1 (`Plan architecte Simulafoot.md` §3.2) ont été validées et commitées depuis la v1.2
(qui ne les reflétait pas encore). Statuts mis à jour en conséquence :

| ID | Statut v1.2 | Statut v1.3 | Preuve |
|---|---|---|---|
| EG-JOU-05 (Bloc A) | Partiel : étape 0 close, chantier 1 en cours (1a validé, 1b livré) | Partiel : 1a à 1e-1 validées (familles A, B, C migrées) ; 1f, 1e-2, 1g, 1h restantes | voir ci-dessous |
| EG-JOU-10 (géométrie de rôle) | Partiel : moteur livré, neutre (aucun gabarit migré) | Partiel : 8 gabarits sur 12 migrés (percee_individuelle, debordement_centre_tete, profondeur_1v1, decalage_enroulee, une_deux, contre_attaque, construction_placee, recuperation_haute, but_gag) ; corner, coup_franc, penalty restants (1f) | f67fae5, c35b9a4, 00f6c94, 4059400 (1c) ; cb436f4, 3c05319, d44547b (1d) ; 078b457, d0a3411 (1e-1) |
| EG-JOU-11 (buteur à sa zone, 0 passe > 30 m/s, baisse des dépassements 1,05× vmax) | Planifié (cibles du modèle A : écart 4,88 → 0,27 m ; dépassements 1 449 → 591 clips) | Planifié, mesure réelle cumulée après 1d (582 clips > 1,05× vmax) puis après 1e-1 (421 clips, -27,7 %) ; résiduel renvoyé à A1.1/A1.5 (`profondeur_1v1`, `une_deux`, `but_gag`, tous documentés dans le code) | `Plan architecte Simulafoot.md` §3.2, §3.1 ; mesure pipeline réel 100 matchs, graine 20260923 |

### Suite de tests (indicateurs)
| Indicateur | v1.2 | v1.3 |
|---|---|---|
| pytest (suite principale) | 1 648 passés, 5 ignorés, 12 désélectionnés | 1 657 passés, 12 désélectionnés (les 5 anciens « ignorés » sont redevenus actifs, dépendance NLG installée, sans lien avec le chantier 1) |

## v1.4 — 15/10/2026 (état du dépôt : 624606a)

La sous-étape 1f du chantier 1 a été validée et commitée.

| ID | Statut v1.3 | Statut v1.4 | Preuve |
|---|---|---|---|
| EG-JOU-05 (Bloc A) | Partiel : 1a à 1e-1 validées (familles A, B, C migrées) ; 1f, 1e-2, 1g, 1h restantes | Partiel : 1a à 1f validées (familles A à D migrées) ; 1e-2, 1g, 1h restantes | voir ci-dessous |
| EG-JOU-10 (géométrie de rôle) | Partiel : 8 gabarits sur 12 migrés ; corner, coup_franc, penalty restants (1f) | Partiel : 9 gabarits sur 12 migrés via `Role.geometry` (+ corner) ; `penalty` corrigé par un mécanisme différent (position de départ remplacée dans `build_penalty`, pas `Role.geometry`, incompatible avec son ancrage `ANCHOR_LATERAL_SHIFT`) ; seuls coup_franc et penalty (au sens strict de `Role.geometry`) restent hors géométrie, aucun autre gabarit prévu en 1g/1h | 9a19a19, 624606a (1f) |
| EG-JOU-11 (buteur à sa zone, 0 passe > 30 m/s, baisse des dépassements 1,05× vmax) | Planifié, mesure réelle cumulée 421 clips > 1,05× vmax après 1e-1 | Planifié, mesure réelle cumulée 348 clips > 1,05× vmax après 1f (-17,3 % vs 1e-1, -76 % vs avant chantier 1) ; sauts bruts > 1 m ramenés à 0 sur l'échantillon (100 matchs) | `Plan architecte Simulafoot.md` §3.2 ; mesure pipeline réel 100 matchs, graine 20260923 |

### Suite de tests (indicateurs)
| Indicateur | v1.3 | v1.4 |
|---|---|---|
| pytest (suite principale) | 1 657 passés, 12 désélectionnés | 1 659 passés, 12 désélectionnés |

## v1.5 — 15/10/2026 (état du dépôt : 939e2c1)

La sous-étape 1e-2 du chantier 1 a été validée et commitée (ticket 41 non fermé : famille apparentée, pas le même cas exact).

| ID | Statut v1.4 | Statut v1.5 | Preuve |
|---|---|---|---|
| EG-JOU-05 (Bloc A) | Partiel : 1a à 1f validées (familles A à D migrées) ; 1e-2, 1g, 1h restantes | Partiel : 1a à 1f et 1e-2 validées ; 1g, 1h restantes | voir ci-dessous |
| EG-JOU-10 (géométrie de rôle) | Partiel : 9 gabarits sur 12 migrés via `Role.geometry` ; penalty corrigé par un mécanisme différent | Inchangé (1e-2 ne migre pas de rôle, corrige une position de ballon fixe via le nouveau champ `Template.dynamic_ball_position`) | 939e2c1 |
| Dette « ball_position fixe » (voir DETTE en tête de `templates.py`) | 2 gabarits concernés (corner, recuperation_haute), tous deux avec une position fixe approximative posée le 23/09/2026 | 1 gabarit restant (`corner`, hors périmètre de 1e-2) ; `recuperation_haute` corrigé : ballon au milieu réel de support1/support2 | 939e2c1 |

### Suite de tests (indicateurs)
| Indicateur | v1.4 | v1.5 |
|---|---|---|
| pytest (suite principale) | 1 659 passés, 12 désélectionnés | 1 662 passés, 12 désélectionnés |

## v1.6 — 15/10/2026 (état du dépôt : c5cefb0)

La sous-étape 1g du chantier 1 a été validée et commitée (ticket 46 refondu, pas encore écrit dans `known_issues.md` --
prévu en 1h).

| ID | Statut v1.5 | Statut v1.6 | Preuve |
|---|---|---|---|
| EG-JOU-05 (Bloc A) | Partiel : 1a à 1f et 1e-2 validées ; 1g, 1h restantes | Partiel : 1a à 1g validées (chantier 1 entièrement migré) ; seule 1h (documentation de clôture) restante | voir ci-dessous |
| Ticket 46 (test aveugle `TestSegmentSpeedHeadroom`) | Annoncé, non écrit | Refondu en trois classes de test (analytique sur `role_run_limit_m`, rôles sans géométrie, pipeline réel ~10 matchs) ; fermeture formelle du ticket (texte dans `known_issues.md`) reportée à 1h | c5cefb0 |

### Suite de tests (indicateurs)
| Indicateur | v1.5 | v1.6 |
|---|---|---|
| pytest (suite principale) | 1 662 passés, 12 désélectionnés | 1 691 passés, 13 désélectionnés (nouveau test marqué `integration`, hors suite par défaut) |

## v1.7 — 15/10/2026 (état du dépôt : documentation uniquement, pas de nouveau commit de code)

**Chantier 1 (géométrie macro des gabarits) entièrement clos** (1a à 1h). EG-JOU-10 (géométrie de rôle) et EG-JOU-05 (Bloc A, volet chantier 1) passent de « Partiel » à leur état final pour ce chantier :

| ID | Statut v1.6 | Statut v1.7 | Preuve |
|---|---|---|---|
| EG-JOU-05 (Bloc A) | Partiel : 1a à 1g validées ; 1h restante | Partiel : chantier 1 entièrement clos (1a-1h) ; A1, A2 et Bloc C restent à faire avant que le Bloc A soit complet | `Plan architecte Simulafoot.md` §3.2, récapitulatif de clôture |
| EG-JOU-10 (géométrie de rôle) | 9 gabarits sur 12 migrés via `Role.geometry` (+ corner) ; penalty et coup_franc hors `Role.geometry` | Inchangé -- état final du chantier 1 : coup_franc seul gabarit totalement hors géométrie/mécanisme dédié (aucun rôle générique) | voir récapitulatif de clôture |
| EG-JOU-11 (buteur à sa zone, 0 passe > 30 m/s, baisse des dépassements 1,05× vmax) | Mesure cumulée 351/1552 clips > 1,05× vmax après 1e-2 | État final chantier 1 : 351/1552 (22,6 %), contre 1449/1552 (93,3 %) avant le chantier -- baisse de 76 points. Passes > 30 m/s : 20/1757, ticket 47 fermé pour le modèle A (résidu accepté, reporté à A1.1). Sauts bruts > 1 m : 0 (contre 1076 avant le chantier) | `Plan architecte Simulafoot.md`, récapitulatif de clôture du chantier 1 |

### Tickets (section 11)
Fermés en 1h : 46 (test aveugle, refondu en 1g), 47 (passes > 30 m/s, fermé pour le modèle A). Ouvert en 1h : 48 (adversaires non repositionnés face aux nouveaux départs scriptés, rattaché à A1.5).

### Points ouverts
- Limite de méthode non levée : compos synthétiques de l'audit (4-2-3-1, notes égales, sans entraîneur) -- re-mesure sur compos réelles désormais actionnable (chantier 1 clos), voir §7 du Plan.
- Prochaine étape du Bloc A : A1.1 (inertie, accélération, décélération continue).

### Écarts à corriger au prochain remaniement du PDF
- Section 9 : B6-d, B6-e, B7, B8 passent à « Implémenté » ; le Bloc A passe à « En cours » (chantier 1 clos, A1/A2/Bloc C restants).
- Section 5.2 : B7 et B8 passent à « Implémenté ».
- Glossaire : ajouter « géométrie de rôle », « support tactique », « modèle A ».
- Ce fichier est mis à jour à chaque sous-étape terminée (règle de `CLAUDE.md`).

## v1.8 — 16/10/2026 (état du dépôt : `bb748dc` ; Phase 5 codée, testée, pas encore commitée)

Chantier "mouvement collectif" (joueurs de décor, A1.3/A2.1/A2.3, umbrella EG-JOU-05 Bloc A) : Phases 1 à 4 commitées (`e16b2c8`, `bb748dc`, poussées sur `origin/main`), Phase 5 codée et mesurée mais pas encore commitée — rattrapage de ce fichier resté à l'état v1.7 (avant le début de ce chantier).

| ID | Statut v1.7 | Statut v1.8 | Preuve |
|---|---|---|---|
| EG-JOU-05 (Bloc A) | Partiel : chantier 1 entièrement clos (1a-1h) ; A1, A2 et Bloc C restent à faire | Partiel : A1.3 couverte à ~5/5 phases (Phases 1-4 commitées, Phase 5 codée/testée/mesurée, en attente de démo visuelle et commit) ; A2.1 et A2.3 partiellement couverts par la Phase 3 (dédoublement/repli par poste) et la Phase 5 (style de coach) respectivement ; A1.1, A1.2, A1.4-1.6, A2.2, A2.4, A2.5 et Bloc C restent à faire | `Plan architecte Simulafoot.md` §3.2bis, §3.3, §3.4 |

### Tickets (section 11)
Aucun nouveau ticket ouvert par ce chantier. Limite déjà connue (compos synthétiques de l'audit sans attributs ni style de coach renseignés) : confirmée inchangée pour la Phase 5 (pipeline 100 matchs 100 % identique à la Phase 4 sur ces compos).

### Points ouverts
- Démo visuelle de la Phase 5 (styles de coach contrastés) à envoyer au propriétaire avant commit.
- Une fois la Phase 5 commitée, le chantier "mouvement collectif" sera entièrement clos (5/5 phases du PLAN) ; reste alors A1 (hors A1.3), A2 (hors A2.1/A2.3 partiels) et le Bloc C.

### Écarts à corriger au prochain remaniement du PDF
- Section 9 / Bloc A : nuancer « En cours » avec l'avancement détaillé de A1.3/A2.1/A2.3 ci-dessus une fois la Phase 5 commitée.
- Ce fichier est mis à jour à chaque sous-étape terminée (règle de `CLAUDE.md`).
