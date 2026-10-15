# PLAN DÉTAILLÉ DES ÉTAPES RESTANTES — PROJET SIMULAFOOT

Document de planification architecte. Établi le 15/10/2026 à partir de l'état du dépôt au commit 44497d1 (HEAD). Tous les hashs cités sont lus dans `git log`. Il remplace entièrement la version établie à B6-c (commit 80f2bd0) : les parties B6-c à B8, closes, n'y figurent plus qu'en résumé.

---

## 1. PRÉAMBULE — ÉTAT ACTUEL

Depuis B6-c, le Bloc B (physique de balle) est clos (15 sous-étapes, B1 à B8-c1). Le Bloc A (mouvement des joueurs) est ouvert : l'étape 0 (assainissement de l'effectif affiché) est close, le chantier 1 (géométrie macro des gabarits) est en cours, avec 1a, 1b et 1c (famille A) validées. Prochaine sous-étape : 1d.

Faits mesurables à ce jour :

- Suite de tests : 1 648 passés à 44497d1 (les 5 "ignorés" de l'époque sont redevenus actifs depuis, dépendance NLG désormais installée, sans lien avec le chantier 1), 12 désélectionnés. 1 623 à ab92559, 1 637 après 1a.
- Chantier 1 : 1a et 1b sont neutres (aucun gabarit migré). 1c migre les 4 gabarits de la famille A (percee_individuelle, debordement_centre_tete, profondeur_1v1, decalage_enroulee) vers `Role.geometry` -- cible d'arrivée inchangée, seul le départ devient réaliste. Mesure pipeline réel (100 matchs, graine 20260923, 1 552 clips, moteur identique avant/après) : clips au-dessus de 1,05x vmax percee 192 -> 14, profondeur_1v1 108 -> 37, decalage_enroulee 180 -> 87, debordement 218 -> 23 (les 8 autres gabarits sont 100 % identiques clip à clip, aucun effet de bord hors périmètre). Écart du scorer à sa zone de tir ramené à 0,00 m médian sur les 4. Effet de bord identifié et documenté dans le code (commentaire du gabarit `profondeur_1v1`) : 14 clips sur 1552 où une passe dépasse 30 m/s (0 avant), à reprendre en 1g/1h (ticket 47), ne bloque pas la clôture de 1c (aucune exigence testée violée).
- Diagnostic du Bloc A avant 1c (100 matchs, 1 552 clips) : 67 % des clips contiennent un segment impossible (vitesse moyenne exigée supérieure à la vitesse max du poste), 70,7 % des acteurs rendus dépassent leur vmax, 49 % ont un saut brut de plus d'1 m en une image, le buteur fait 56,7 m de déplacement net en médiane, l'écart médian entre le buteur rendu et sa zone de tir est de 4,88 m.

Limite de méthode : l'audit utilise des compos synthétiques (4-2-3-1 des deux côtés, notes égales, sans entraîneur). Toutes les mesures du Bloc A sont à re-mesurer sur des compos réelles avant validation définitive.

---

## 2. BLOC B — PHYSIQUE DE BALLE : CLOS

Récapitulatif complet : `docs/phase6_block_b_audit.md`, section 19 (commit 3d17175). Audit initial : 4154584.

- B1 friction de l'air, c = 0,0033 : af6f493.
- B2 rebonds (sol, poteau, barre à 0,70, aléa de direction ±10° déterministe) : d09d9cf.
- B3 rotation visible du ballon, traînée d'arc : diagnostic b715092, implémentation f0f6383.
- B4 événements du ballon (but, parade, poteau, barre, corner, sortie de but, touche, dégagement) : c149422.
- B4-bis consommation canvas et biais du gardien : 8febf44, 783bc19 (formule recentrée sur la moyenne 74,7).
- B5 variétés de frappe (6 types) : diagnostic 45946b5, implémentation 6bb8e5e, recalibrage dbe65a9.
- B6-a point de penalty exact et élan du tireur : b812330, 798c616.
- B6-b types de penalty (fort 30 %, placé 50 %, contre-pied 20 %) : 815e7f7, b1f923c, 1ee9a89. Tickets 27 et 28 ouverts : 6d9c8c2.
- B6-c micro-variations par événement (décalages de départ et dérives, clé joueur|événement|sel) : 80f2bd0, 9965d63, 1f562e9, clôture f48e1ab (variété des dérives 99,9 %, plancher 0,2 à 0,5 m, déterminisme 100/100).
- B6-d réaction du gardien sur penalty (Option 2 : glissement renforcé) : e8bb99e, 626dbce, 90cae5b. Ticket 32 : 2ecb1b3.
- B6-e ticket 23, le NLG reçoit le type de frappe : 88497f1, f5ba202, 2674de0, 2bc31e7, clôture c3ff089.
- B7 coups francs et mur : b0bb60c (B7-a, point exact et ballon posé), ab826b6 et 396411b (B7-b, mur statique), 5582b96 et 71ac316 (B7-c, mur actif), eaac0df (B7-d, gardien et angle de déviation), clôture a6cf0cb.
- B8-a contrôles au sol (pied naturel 85 %, pied faible 10 %, semelle 5 %) : 250b71e, 927f470, récapitulatif b5bf0e7. Ticket 40 : 174dc71.
- B8-b modulation du contrôle par la pression et la qualité technique : 55bc0f1, c43b8b6, récapitulatif 7cc7cfe.
- B8-c1 contact aérien (tête et volée) sur corner et débordement : fa7a5d5, 5795235. Ticket 41 : e9bc472, 5f137a7.
- B8-c2 abandonné après diagnostic : aucun gabarit ne produit de vrai lob (0 segment `pass_lob` sur 5 858). Ticket 42 ouvert pour les vrais lobs (3d17175).

---

## 3. BLOC A — MOUVEMENT DES JOUEURS : EN COURS

Trois temps : étape 0 (close), chantier 1 (en cours), puis A1 et A2.

### 3.1 Étape 0 — assainissement de l'effectif affiché : CLOSE

- 0a, un seul gardien par équipe dans l'effectif affiché : a5176f0, 7c845b8. 33 clips avec deux gardiens côté équipe qui attaque, et 8 côté adverse, ramenés à 0 (41 clips modifiés). Ticket 43 ouvert à cette occasion : ead10dd.
- 0b-1, tireur et assist des occasions contraints par la présence à la minute : 8cb93fb, 87b3669. Tireur d'occasion absent 388 → 0, assist absent 225 → 0, 563 clips modifiés, moteur et buts réels identiques. Ticket 44 : 10ce4a5.
- 0b-2, effectif affiché = joueurs sur le terrain à la minute de l'événement : 2a731f2, 1d57be2. 0 joueur en trop ou manquant sur 1 552 clips, supports absents support1 86 → 0 et support2 36 → 0. Entrant placé à la ligne de son propre poste. Numéros de maillot stabilisés. Exception bornée sur `sequence_generator.py` (paramètre optionnel `en_jeu`). Ticket 45 : ab92559.
- 0b-3 abandonnée : jugée inutile au vu des mesures.

### 3.2 Chantier 1 — géométrie macro des gabarits : EN COURS

Objectif : positions de départ, ancrages et durées des gabarits. Préalable à A1.1 : régler l'inertie sur une géométrie qui exige 2,4 fois la vitesse max du joueur n'a pas de sens.

Décisions produit validées : pré-action généralisée (départ dérivé de la formation, décalé vers la zone d'action) ; ancrage réaliste du scorer (la zone de tir exacte, départ dérivé) ; durées modulables dans des bornes par nature de jeu ; supports tactiques déterministes ; ratio de vitesse inférieur ou égal à 0,5 sur chaque segment (limite de `motion.py` : 0,55) ; critère d'accélération D inférieur ou égal à 2,25 fois T au carré (D distance du segment, T sa durée). Constantes validées : `_RUN_RATIO_MAX` = 0,5, `_RUN_ACCEL_COEFF` = 2,25, `_BEHIND_MIN_M` = 6,0.

Modèle retenu : modèle A (géométrie, sans retiming des t_ratio). Le modèle B (retiming des t_ratio de passe) est écarté : il fait passer les clips en dépassement de 591 à 933. Les t_ratio actuels sont conservés. Le retiming est reporté après A1.1.

Validation sur pipeline réel (100 matchs, graine 20260923, 1 552 clips), modèle A contre HEAD : scorer à 0,27 m de sa zone en médiane (4,88 m à HEAD) ; acteurs au-dessus de 0,55 de ratio 0 sur 3 524 (2 587 à HEAD) ; passes supérieures à 30 m/s 0 en chemin (83 à HEAD) ; sauts bruts supérieurs à 1 m 57 clips (1 076) ; clips avec un acteur au-dessus de 1,05 fois vmax au rendu 591 (1 449). Le résiduel relève de trois mécanismes hors chantier 1 : l'évitement à 1,5 m (A1.5), les sous-keyframes des contrôles au sol B8-a, la contrainte d'accélération sur une courbe qui s'arrête à chaque keyframe (A1.1). Avec le critère D inférieur ou égal à 2,25 fois T au carré, le dépassement sans évitement ni contrôles tombe à 0 (30 matchs).

Sous-étapes :

**1a — moteur de géométrie de rôle. VALIDÉE. Commits 2d8f729 (code), 5feb4b5 (tests).**
- Objectif : champ optionnel `Role.geometry`, quatre cibles (zone de tir, zone d'assist, derrière la zone, vers le but), départ dérivé de la cible et de la position de formation, longueur de course limitée sur chaque segment par le ratio et par D inférieur ou égal à 2,25 fois T au carré. Harnais de mesure `scripts/measure_geometry.py` versionné.
- Périmètre : `src/ligue1sim/animation/templates.py`, `scripts/measure_geometry.py`, `tests/test_templates.py`.
- Résultat : images identiques à HEAD sur 1 552 clips, 14 tests ajoutés (1 623 → 1 637).
- Dépendances : aucune. Statut : validée.

**1b — supports tactiques. VALIDÉE (15/10/2026). Commits 078e886 (code), 44497d1 (tests).**
- Objectif : un support est tiré parmi les postes attendus (repli sur tous les joueurs de champ), le plus proche de sa cible d'après la position de formation, égalité par nom, support1 avant support2, jamais le tireur, le passeur, un gardien ni un joueur déjà tiré. Déterministe, sans hachage.
- Périmètre : `templates.py` (`_resolve_roles` reçoit les rôles et les positions), `tests/test_templates.py`. Aucun autre appelant de `_resolve_roles`.
- Résultat : images identiques sur 1 552 clips, 11 tests ajoutés (1 637 → 1 648). Les postes attendus par gabarit seront renseignés à la migration des gabarits.
- Dépendances : 1a. Statut : livrée.

**1c — famille A : percee_individuelle, profondeur_1v1, decalage_enroulee, debordement_centre_tete. VALIDÉE (15/10/2026).**
- Objectif : migrer la géométrie et les durées (7 → 8, 6 → 7, 6 → 7 ; debordement reste à 6).
- Périmètre : `templates.py` ; `tests/test_templates.py` (empreintes de ces 4 gabarits) ; `tests/test_narrative_player.py` (témoin percee_individuelle) ; `tests/test_sequence_generator.py` (commentaire corrigé, valeur finale inchangée donc test non réécrit).
- Gain mesuré (clips au-dessus de 1,05 fois vmax, pipeline réel, 100 matchs, graine 20260923, moteur identique) : percee 192 → 14 (prédit 20), profondeur 108 → 37 (prédit 37), decalage 180 → 87 (prédit 100), debordement 218 → 23 (prédit 50) — égal ou meilleur que prédit sur les 4. Écart d'arrivée du scorer médian ramené à 0,00 m sur les 4. Les 8 autres gabarits sont 100 % identiques clip à clip (aucun effet de bord hors périmètre).
- Effet de bord mesuré et documenté dans le code (`profondeur_1v1`) : 14 clips sur 1552 où la passe assist → scorer dépasse 30 m/s (0 avant 1c), causé par le rapprochement du départ du scorer. Aucune exigence testée n'est violée (EG-JOU-11 / ticket 47 restent "Planifié") ; à reprendre en 1g/1h, pas un blocage de 1c.
- Revue `simulafoot-reviewer` : aucun défaut majeur bloquant ; portée, déterminisme et décisions produit conformes.
- Commits (4, un par gabarit) : percee_individuelle f67fae5, debordement_centre_tete c35b9a4, profondeur_1v1 00f6c94, decalage_enroulee 4059400.
- Dépendances : 1a. Statut : validée.

**1d — famille B : une_deux, contre_attaque, construction_placee. À FAIRE.**
- Objectif : migrer la géométrie, durées 4 → 5 et 8 → 9 (construction reste à 14), support1 tactique (poste attendu : DC, LB, RB, MDC, MC).
- Périmètre : `templates.py` ; empreintes des 3 gabarits ; témoins contre_attaque et construction_placee.
- Gain attendu : clips au-dessus de 1,05 fois vmax une_deux 94 → 75, contre_attaque 213 → 61, construction_placee 144 → 34. Passes supérieures à 30 m/s sur une_deux 50 → 0. Support1 de contre_attaque : MC dans 175 clips sur 213 mesurés.
- Dépendances : 1a, 1b. Statut : à faire.

**1e-1 — famille C, géométrie des joueurs : recuperation_haute, but_gag. À FAIRE.**
- Objectif : course réduite pour respecter D inférieur ou égal à 2,25 fois T au carré (le critère ne mord que dans ces deux gabarits et le corner). Durée de recuperation 5 → 6. Postes attendus : MOC, MC, AG, AD, SA, ATT, BU pour recuperation ; BU, SA, ATT, MOC pour but_gag. Sans toucher au ballon.
- Périmètre : `templates.py` ; empreintes des 2 gabarits ; témoin but_gag.
- Gain attendu : passes supérieures à 30 m/s but_gag 27 → 0, recuperation 6 → 0 (chemin). Les clips au-dessus de 1,05 fois vmax (189 → 188 et 27 → 22 sans le critère) sont à mesurer avec le critère.
- Dépendances : 1a, 1b. Statut : à faire.

**1f — famille D : corner, penalty (supports). À FAIRE.**
- Objectif : corner avec durée 7,0 s et centre à 4,9 s conservés (contrainte B8-c1), course plafonnée à 15 m, tireur à 8 m du poteau de corner, plancher de 6 m entre la zone et le tireur, support1 de type aérien (DC, BU, SA, ATT). Penalty : supports au bord de la surface, tireur et durée inchangés. Coup franc inchangé.
- Périmètre : `templates.py` ; empreintes corner et penalty ; témoin corner ; tests de B6-a sur les supports du penalty.
- Gain attendu : clips au-dessus de 1,05 fois vmax du corner 85 → 4, écart d'arrivée 4,06 → 0,47 m.
- Dépendances : 1a, 1b, 1e-1 (critère d'accélération). Statut : à faire.

**1e-2 — ballon dynamique de recuperation_haute. À FAIRE.**
- Objectif : le `ball_position` figé (0,6 ; 0,5) à t_ratio 0,3 devient dynamique (milieu des deux presseurs). Diagnostic préalable contre `ball.py` (branche « ballon immobile ») et ticket 41.
- Périmètre : `templates.py` (builder par événement) ; test de ce gabarit. Exception sur `ball.py` à demander si le diagnostic l'exige.
- Dépendances : 1e-1. Risque : élevé (le ballon est touché). Statut : à faire.

**1g — test pipeline réel (ticket 46 refondu). À FAIRE.**
- Objectif : remplacer `TestSegmentSpeedHeadroom` (aveugle : géométrie synthétique) par un test à deux niveaux : analytique (matrice zones de base × postes DC, MC, BU) et pipeline (`build_clips` sur environ 10 matchs de la graine d'audit, vitesse image par image des rôles scriptés).
- Périmètre : `tests/test_templates.py`.
- Dépendances : 1c à 1f (seuils calibrés sur le résultat). Statut : à faire.

**1h — documentation. À FAIRE.**
- Objectif : fermer le ticket 47, refondre le ticket 46, ouvrir le ticket 48 (adversaires et nouveaux départs, A1.5), ajouter le récapitulatif de clôture du chantier 1.
- Périmètre : `docs/known_issues.md`, `docs/`. Les tickets 46 à 48 ne sont pas encore écrits dans `known_issues.md` (dernier ticket : 45).
- Dépendances : 1g. Statut : à faire.

Ordre du chantier : 1a → 1b → 1c → 1d → 1e-1 → 1f → 1e-2 → 1g → 1h. Chaque sous-étape est mesurée puis commitée séparément (code, tests, docs), isolation des hunks, vérification sur export de l'index, pas de push.

### 3.3 A1 — mouvement individuel et équipe : À FAIRE (après le chantier 1)

**A1.1 — inertie, accélération, décélération.**
- Objectif : trajectoire continue des joueurs, sans arrêt à chaque keyframe. C'est la cause du résiduel de 591 clips (contrainte d'accélération sur une courbe qui s'arrête à chaque keyframe). Rattaché : ticket 43 (images 0 et 1 jamais corrigées) et ticket 12 (sauts de trajectoire).
- Périmètre : `src/ligue1sim/animation/motion.py`, éventuellement `src/ligue1sim/animation/physics.py`.
- Gain attendu : clips au-dessus de 1,05 fois vmax et au-dessus de 10 m/s² (591 et 352 après le chantier 1) en forte baisse. Retiming des t_ratio de passe (proposition P-A) à reprendre ensuite : il fait passer les passes lentes (3,6 à 6,5 m/s en médiane) à environ 10 m/s.
- Dépendances : chantier 1. Statut : à faire.

**A1.2 — gardiens.**
- Objectif : déplacements sur la ligne, sorties, plongeons complets (Option 1 reportée de B6-d), replacements.
- Périmètre : `sequence_generator.py`, `templates.py`. Dépendances : A1.1. Statut : à faire.

**A1.3 — joueurs hors action.**
- Objectif : appels, replacements, soutien, courses croisées des partenaires du porteur.
- Périmètre : `templates.py`, `sequence_generator.py`. Dépendances : A1.1. Statut : à faire.

**A1.4 — pressing, couverture, repli, marquage, bloc équipe.**
- Reclassé en A2 : à rattacher à A2.1 (respect du dispositif) ou A2.3 (profil coach). Rattachement à trancher.

**A1.5 — évitement et placement adverse.**
- Objectif : l'évitement à 1,5 m (`motion._apply_avoidance`) provoque à lui seul 137 clips au-dessus de 1,05 fois vmax avant contrainte et les sauts bruts supérieurs à 1 m. Tickets 28 (adversaire à 1,5 m du départ du tireur de penalty) et 48 (nouveaux départs scriptés contre placement adverse d'`enrich_with_background`).
- Périmètre : `motion.py`, `sequence_generator.py`. Dépendances : chantier 1, A1.1. Statut : à faire.

**A1.6 — cohérence joueur-ballon.**
- Objectif : définir un contact réel (distance, pas d'accélération sans contact), ne pas se fier à `ball.owner_id`. Tickets 30 (priorité haute) et 41 (ballon figé quand le passeur est inconnu, y compris contre_attaque, construction_placee, une_deux). Ticket 42 (vrais lobs) : lieu de traitement à trancher à l'ouverture de A1.6 ou en B9 dédié.
- Périmètre : `ball.py`, `templates.py`, `sequence_generator.py`. Dépendances : A1.1. Statut : à faire.

### 3.4 A2 — comportement collectif et tactique contextuel : À FAIRE

Toute constante comportementale est à re-mesurer sur des compos réelles avant validation.

- A2.1 respect du dispositif (4-3-3, 4-2-3-1, 4-4-2 identifiables ; fluidité : latéral qui dédouble, ailier qui se replie). Dépendances : A1.1.
- A2.2 modulation par le score (mené et coach défensif : se découvre un peu ; mène et coach défensif : repli ; mène et coach offensif : continue ; mené et coach offensif : surenchère). Dépendances : A2.1.
- A2.3 modulation par le profil du coach (pressing, offensif, défensif, contre, possession pilotent la hauteur du bloc). Dépendances : A2.1.
- A2.4 remplacements contextuels (coach défensif qui mène : entre un défenseur ; coach offensif mené : entre un attaquant). Dépend du moteur Poisson : exception à valider avant toute modification. Rattachement possible du ticket 45 (gardien expulsé sans remplaçant).
- A2.5 arrêts de jeu (gardien d'une équipe menée qui monte sur corner). Dépendances : A1.2.

Vérification du Bloc A : déterminisme 100/100, mesure des comportements, captures.

---

## 4. BLOC C — COHÉRENCE DU RENDU : À FAIRE (après A)

- Continuité inter-clips : enchaînement fluide entre clips successifs.
- Ombres : cohérentes avec la position du ballon et des joueurs.
- État visuel : cohérence des positions de fin et de début de clip.
- Ticket 25 (clips de but dont la dernière image est avant la ligne) : résolution au Bloc C ou avant.
- Ticket 26 (divergence moteur et narration sur les penaltys ratés) : couplage au Bloc C ou traitement séparé, à trancher par le propriétaire.
- Vérification : déterminisme, captures, revue globale.

---

## 5. PHASE 7 — CARRIÈRE : À CADRER

À cadrer après clôture des Blocs A, B et C. Tickets à traiter avant : 3 (`SubstitutionEvent` identifié par nom et non par `player_id`), 24 (commentaire faux dans `engine/narrative.py`), 27 (tireur de penalty qui dépasse le ballon).

---

## 6. TICKETS OUVERTS PAR THÈME

Source : `docs/known_issues.md` (tickets 1 à 45). Fermés ou résolus : 1, 2, 5, 7, 8, 14, 23, 33. Les tickets 46 à 48 sont annoncés par l'Architecte et seront écrits en 1h.

Cohérence joueur, ballon et effectif (rattachement entre parenthèses) :
- 30 cohérence joueur-ballon (A1.6, priorité haute) ; 41 ballon figé, passeur inconnu (A1.6) ; 42 vrais lobs (A1.6 ou B9) ; 43 images 0 et 1 non corrigées (A1.1) ; 12 sauts de trajectoire en amont (A1.1) ; 28 adversaire à 1,5 m du tireur de penalty (A1.5) ; 48 départs scriptés contre placement adverse (A1.5) ; 44 rôles absents sur buts réels, 3 cas de frontière (à rattacher à A1.6 ou à rester ouvert) ; 45 et 17 gardien expulsé sans remplaçant (A1.6 ou A2.4) ; 27 tireur de penalty qui dépasse le ballon (avant Phase 7).

Physique du ballon :
- 21 spin binaire dans `templates.py` ; 22 courbure non perceptible à 6 px (accepté) ; 18 poteau et barre toujours attribués à l'attaquant ; 20 clips poteau coupés à 1,0 s ; 38 type dédié « mur » pour les coups francs bloqués.

Rendu et interface :
- 25 clips de but avant la ligne (Bloc C) ; 26 divergence moteur et narration sur les penaltys ratés (Bloc C ou séparé) ; 13 axe fixe de la barre de progression ; 15 bandes de tonte perpendiculaires dans `PitchField.jsx`.

NLG :
- 24 commentaire faux dans `narrative.py` (avant Phase 7) ; 34 lucarne sur penaltys bas ou à mi-hauteur ; 35 « au centre » pour une cible près d'un poteau ; 36 phrases de coup franc hors contexte ; 37 phrases de penalty contredisent B6-d ; 40 type de contrôle non exposé au NLG ; 31 tests d'intégration NLG non relancés ; 10 seuil de couverture NLG.

Payload, données et infrastructure :
- 4 latence et poids du payload (partiellement résolu) ; 16 point d'entrée de la graine (`np.random.seed` et `PYTHONHASHSEED=0`) ; 3 `SubstitutionEvent` par nom (avant Phase 7) ; 6 `continue` silencieux dans `build_clips` ; 19 imports privés entre modules.

Tests et environnement :
- 9 `pytest` nu échoue (duckdb absent) ; 11 `ConnectionResetError` Windows ; 29 tests d'intégration exclus de la suite standard (réintégration à décider) ; 32 cinq tests ignorés qui passent sous uv.

Chantier 1 (1g et 1h) :
- 46 test aveugle (`TestSegmentSpeedHeadroom`), refondu en test pipeline réel ; 47 passes supérieures à 30 m/s, fermé pour le modèle A (chemin 0, corde 2) ; 48 voir ci-dessus.

---

## 7. SYNTHÈSE DES DÉCISIONS EN ATTENTE

| Décision | Objet | Responsable | Statut |
|---|---|---|---|
| 1b | Validation de la livraison des supports tactiques | Architecte | Validée (15/10/2026) |
| Postes attendus | Ensembles de postes par gabarit (renseignés à 1d, 1e-1, 1f) | Architecte | Proposés, validés en conception |
| 1e-2 | Exception sur `ball.py` si le ballon dynamique l'exige | Architecte | À venir |
| A1.4 | Rattachement du pressing et du marquage à A2.1 ou A2.3 | Architecte | À trancher |
| Ticket 42 | Lieu de traitement des vrais lobs : A1.6 ou B9 dédié | Architecte | À trancher |
| Tickets 17 et 45 | Rattachement : A1.6 ou A2.4 | Architecte | À trancher |
| A2.4 | Exception sur le moteur Poisson pour les remplacements contextuels | Propriétaire | À venir |
| A2.2, A2.3 | Constantes comportementales (score, profil coach), à re-mesurer sur compos réelles | Propriétaire | À venir |
| Ticket 26 | Couplage au Bloc C ou traitement séparé | Propriétaire | À venir |
| Ticket 29 | Réintégration des tests d'intégration | Propriétaire | Reportée |
| Priorité 41 et 42 | Priorité à fixer pour les tickets 41 et 42 | Propriétaire | À venir |
| Compos réelles | Re-mesure du chantier 1 sur compos réelles | Architecte | Après le chantier 1 |
| D9.4.1 à D9.4.4 | Décisions citées par l'Architecte, introuvables dans les documents du dépôt | Architecte | À retrouver ou à écarter |

---

## 8. ORDRE D'EXÉCUTION RECOMMANDÉ

1. ~~Validation de 1b.~~ Faite (15/10/2026).
2. ~~1c (famille A).~~ Faite (15/10/2026).
3. 1d (famille B).
4. 1e-1 (famille C, géométrie).
5. 1f (famille D).
6. 1e-2 (ballon dynamique de recuperation_haute).
7. 1g (test pipeline réel, ticket 46).
8. 1h (documentation, tickets 46 à 48).
9. A1.1 (inertie, accélération), puis retiming des t_ratio de passe.
10. A1.5 (évitement et placement adverse), A1.2 (gardiens), A1.3 (joueurs hors action).
11. A1.6 (cohérence joueur-ballon, tickets 30 et 41 ; décision sur le ticket 42).
12. A2.1 à A2.5.
13. Bloc C (continuité, ombres, état visuel, tickets 25 et 26).
14. Tickets 3, 24 et 27, puis tickets transverses restants.
15. Phase 7 (carrière).

---

## 9. FOCUS RÉALISME — CE QUI SE VOIT À L'ÉCRAN

Par ordre d'impact visuel décroissant :

1. Le buteur arrive à sa zone de tir et les joueurs courent à une vitesse plausible (chantier 1) : aujourd'hui 70,7 % des acteurs dépassent leur vmax et le buteur s'arrête en médiane à 4,88 m de sa zone.
2. Des courses continues, sans arrêt ni saccade à chaque point clé (A1.1).
3. Un ballon cohérent avec le joueur qui le joue : contact réel, pas de ballon figé quand le passeur est inconnu (A1.6, tickets 30 et 41).
4. Des passes à un rythme crédible (retiming des t_ratio, après A1.1) : certaines passes courtes mettent aujourd'hui 3 à 5 secondes.
5. Les gardiens : sorties, plongeons complets (A1.2).
6. Des adversaires qui ne se superposent pas aux joueurs scriptés (A1.5, tickets 28 et 48).
7. De vrais lobs et des réceptions aériennes crédibles (ticket 42).
8. Des appels et un soutien visibles des partenaires (A1.3), puis un bloc qui respecte le dispositif et le contexte (A2).
9. Un enchaînement fluide entre clips, des ombres et un état visuel cohérents (Bloc C).

Déjà acquis au Bloc B : rebonds, friction de l'air, trajectoires enroulées, parades, penaltys variés, murs sur coups francs, contrôles au sol modulés, contact aérien sur corner et débordement.

---

Fin du plan.
