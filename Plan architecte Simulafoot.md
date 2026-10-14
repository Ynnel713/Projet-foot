# PLAN DÉTAILLÉ DES ÉTAPES RESTANTES — PROJET SIMULAFOOT

Document de planification architecte. Établi à partir de l'état au commit 80f2db8 (B6-c).

---

## PRÉAMBULE — ÉTAT ACTUEL AU 11/10

**Phase 6 — Réalisme avancé, Bloc B — Physique de balle**

| Sous-étape | Statut | Commit | Notes |
|---|---|---|---|
| B1 — Friction de l'air | TERMINÉ | — | c = 0,0033 |
| B2 — Rebonds | TERMINÉ | — | sol 0,70, poteau 0,70, barre 0,70 |
| B3 — Rotation visible | TERMINÉ | — | traînée d'arc, Option C |
| B4 — Événements ballon | TERMINÉ | — | parade, poteau, barre, corner |
| B4-bis — Consommation canvas | TERMINÉ | — | biais gardien recentré |
| B5 — Variétés de frappe | TERMINÉ | dbe65a9 | 6 types, distribution validée |
| B6-a — Point de penalty + élan | TERMINÉ | b812330, 798c616 | 34/34 exact, élan 6-9 m |
| B6-b — 3 types penaltys | TERMINÉ | b1f923c, 1ee9a89 | 34,1 / 50,3 / 15,6 % sur 1000 matchs |
| B6-c — Micro-variations clé événement | EN COURS | 80f2db8 | décalages 99,8 %, dérives 79,9 %, 2 décisions en attente |
| B6-d — Réaction gardien | À FAIRE | — | Option 2 validée |
| B6-e — Ticket 23 NLG | À FAIRE | — | commit séparé |
| B7 — Coups francs + mur | À FAIRE | — | — |
| B8 — Contrôles variés | À FAIRE | — | — |

**Bloc A — Mouvement des joueurs** : À FAIRE (après B)

**Bloc C — Cohérence du rendu** : À FAIRE (après A)

**Tickets ouverts** : 3, 4, 6, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28.

---

## PARTIE 1 — FINALISATION DE B6-c (EN COURS)

### 1.1 — Clarification des tests affectés

#### 1.1.1 — Liste nominative

- Produire la liste exhaustive des tests touchés : fichier, nom du test, statut (supprimé / désélectionné), raison en une ligne.
- Résoudre l'incohérence 13 vs 17 tests entre les deux rapports.
- Résultat attendu : tableau nominatif unique, vérifiable par git diff.

#### 1.1.2 — Lancement des 7 tests non exécutés sur HEAD

- Exécuter les 7 tests désélectionnés restants sur HEAD (80f2db8).
- Si passage : confirmer. Si échec : intégrer au plan de réécriture.
- Résultat attendu : rapport pytest nominatif, statut par test.

### 1.2 — Réécriture des 5 tests supprimés (test_narrative_player.py)

#### 1.2.1 — Validation de périmètre (DÉCISION B propriétaire)

- Le fichier tests/test_narrative_player.py est hors périmètre B6-c.
- Décision propriétaire : lever la règle pour ce fichier de tests, ou refuser.
- Résultat attendu : autorisation explicite ou refus documenté.

#### 1.2.2 — Réécriture

- Réécrire les 5 tests (bu_goal, construction_placee, contre_attaque, corner, percee_individuelle) sous la nouvelle signature.
- Commit dédié, message : « Réécriture des 5 tests narrative_player.py après changement de signature B6-c ».
- Résultat attendu : 5 tests adaptés, pytest vert, commit isolé.

### 1.3 — Décision A : dérives 79,9 % vs 90 %

#### 1.3.1 — Options à trancher par le propriétaire

- Option A1 : accepter 79,9 % (plancher 0,5 m conservé).
- Option A2 : élargir l'amplitude 0,5-1,0 m.
- Option A3 : élargir l'amplitude 0,1-0,5 m.
- Option A4 : plancher par événement (0,1 m minimum).
- Résultat attendu : décision explicite, constante produit documentée.

#### 1.3.2 — Application de la décision

- Si A1 : B6-c est clos en l'état.
- Si A2/A3/A4 : commit correctif, relance déterminisme 100 matchs, mesure variété.
- Résultat attendu : B6-c validé définitivement.

### 1.4 — Clôture B6-c

- Vérification sur git archive HEAD propre : pytest, npm build, npm lint.
- Rapport de clôture : variété décalages, variété dérives, déterminisme 100/100, hash.
- Résultat attendu : validation définitive, passage à B6-d.

---

## PARTIE 2 — B6-d : RÉACTION DU GARDIEN SUR PENALTY

### 2.1 — Cadrage

#### 2.1.1 — Décision architecte : Option 2

- Glissement latéral renforcé, pas de modification du contrat Sequence (types.py, serialize.py inchangés).
- Option 1 (plongeon complet) reportée au Bloc A.

#### 2.1.2 — Dépendance B6-b

- Le comportement du gardien dépend du type de penalty (fort, placé, contre-pied).
- Le côté du glissement dépend de l'issue (but, arrêt, hors cadre, poteau, barre).

### 2.2 — Implémentation

#### 2.2.1 — Délai de réaction

- Amplitude : 0,00 à 0,20 s, déterministe par sha256 sur event_ref.
- Fichier : src/ligue1sim/animation/sequence_generator.py.

#### 2.2.2 — Amplitude latérale

- Variation de ±0,3 m autour de la valeur actuelle.
- Fichier : src/ligue1sim/animation/sequence_generator.py.

#### 2.2.3 — Cohérence côté / issue

- Arrêt : gardien plonge du bon côté.
- But : gardien plonge du mauvais côté ou arrive trop tard.
- Hors cadre / poteau / barre : côté tiré.
- Fichier : src/ligue1sim/animation/sequence_generator.py.

### 2.3 — Vérification

#### 2.3.1 — Déterminisme

- 100 matchs, 100/100 sur scores, buts, cartons, remplacements, blessures, notes, 1586 événements narratifs.

#### 2.3.2 — Mesures

- Délai de réaction effectif par clip.
- Amplitude latérale effective par clip.
- Cohérence côté / issue sur les 34 penaltys des 100 matchs.

#### 2.3.3 — Captures

- Une capture par type (fort, placé, contre-pied), une par issue non-but (arrêt, hors cadre, poteau, barre).
- Résultat attendu : rapport B6-d, commit, validation.

### 2.4 — Ticket 27 : dépassement tireur

- Si la cause est identifiée dans B6-d, traiter. Sinon, laisser ouvert pour Bloc A.
- Résultat attendu : ticket 27 clos ou explicitement reporté.

---

## PARTIE 3 — B6-e : TICKET 23 NLG

### 3.1 — Cadrage

#### 3.1.1 — Autorisation explicite narrative.py

- Commit séparé, message : « Ticket 23 — NLG reçoit le type de frappe ».
- Périmètre étendu exceptionnellement à engine/narrative.py.

#### 3.1.2 — Contrainte B5

- Le NLG doit recevoir le type de frappe (shot_tendu, shot_enroule_fort, etc.).
- Ne plus dire « enroule sa frappe » pour un shot_tendu.

### 3.2 — Implémentation

#### 3.2.1 — Passage du type de frappe au NLG

- Modifier engine/narrative.py pour transmettre le type.

#### 3.2.2 — Adaptation du texte

- Table de correspondance type → texte NLG.
- Fichier : engine/narrative.py.

### 3.3 — Vérification

#### 3.3.1 — Cohérence texte / type

- Sur 100 matchs : tendu → pas « enroule », enroulé → « enroule ».

#### 3.3.2 — Déterminisme

- Résultat sportif inchangé 100/100.

#### 3.3.3 — Commit séparé

- Résultat attendu : ticket 23 clos, B6-e validé.

---

## PARTIE 4 — B7 : COUPS FRANCS + MUR

### 4.1 — Cadrage

#### 4.1.1 — Diagnostic

- État actuel des coups francs : gabarit, paramètres, absence de mur.
- Référentiel FM 2D pour la construction du mur.

#### 4.1.2 — Constantes produit à proposer

- Distance du mur (9,15 m réglementaire).
- Nombre de joueurs dans le mur (2-5 selon distance).
- Placement du ballon.
- Vitesse, spin, trajectoire (direct / indirect / enroulé / frappé).
- Comportement du gardien.

### 4.2 — Implémentation

#### 4.2.1 — Construction du mur

- Placement des joueurs adverses en ligne, à 9,15 m du ballon.
- Fichier : src/ligue1sim/animation/sequence_generator.py.

#### 4.2.2 — Trajectoires par-dessus / autour

- Contournement du mur (par-dessus ou autour).
- Fichier : src/ligue1sim/animation/templates.py.

#### 4.2.3 — Types de CF

- Direct enroulé, direct frappé, indirect.
- Fichier : src/ligue1sim/animation/templates.py.

### 4.3 — Vérification

- Distribution des types, déterminisme 100/100, captures, pytest.

---

## PARTIE 5 — B8 : CONTRÔLES VARIÉS

### 5.1 — Cadrage

#### 5.1.1 — Diagnostic

- État actuel : un seul type de contrôle.
- Référentiel D8 : pied droit, pied gauche, poitrine, tête, semelle.

#### 5.1.2 — Constantes produit

- Résultats dépendant de la qualité technique et de la pression.
- Amplitude de l'aléa borné ±10°, déterministe.

### 5.2 — Implémentation

- Ajout du type de contrôle dans templates.py.
- Impact sur le premier segment de possession.

### 5.3 — Vérification

- Distribution, déterminisme, captures, pytest.

---

## PARTIE 6 — CLÔTURE BLOC B

### 6.1 — Revue globale

- Toutes les sous-étapes B1 à B8 validées.
- Tickets B clos (B1-B8).

### 6.2 — Bilan Bloc B

- Mesures avant / après sur 100 matchs et 1000 matchs.
- Captures comparatives.
- Bilan des gains perceptibles.

### 6.3 — Documentation

- Mise à jour docs/phase6_block_b_audit.md.
- Clôture Phase 6 Bloc B.

---

## PARTIE 7 — BLOC A : MOUVEMENT DES JOUEURS

### 7.1 — A1 : Mouvement individuel

#### 7.1.1 — Inertie et accélération

- Accélération crédible, décélération, inertie.
- Fichier : src/ligue1sim/animation/motion.py.

#### 7.1.2 — Gardiens

- Déplacements sur la ligne, sorties, plongeons complets (Option 1 reportée de B6-d), replacements.
- Fichier : src/ligue1sim/animation/sequence_generator.py.

#### 7.1.3 — Joueurs hors action

- Appels, replacements, soutien.
- Comportement des partenaires du porteur (courses croisées).

#### 7.1.4 — Défense adverse

- Pressing, couverture, repli, marquage.
- Bloc équipe : ligne défensive monte / descend ensemble, transitions.

#### 7.1.5 — Résolution ticket 28

- Remesure du placement des décors. Placement formé pour éviter les 1,5 m.

### 7.2 — A2 : Comportement collectif et tactique contextuel (D7)

#### 7.2.1 — Respect du dispositif

- 4-3-3, 4-2-3-1, 4-4-2, etc. restent identifiables.
- Fluidité autorisée : latéral qui dédouble, ailier qui se replie.

#### 7.2.2 — Modulation par le score

- Mené + coach défensif → se découvre un peu.
- Mène + coach défensif → repli.
- Mène + coach offensif → continue d'attaquer.
- Mené + coach offensif → surenchère.

#### 7.2.3 — Modulation par le profil coach

- Pressing, offensif, défensif, contre, possession pilotent la hauteur du bloc.

#### 7.2.4 — Remplacements contextuels

- Coach défensif qui mène → entre un défenseur.
- Coach offensif qui est mené → entre un attaquant.

#### 7.2.5 — Arrêts de jeu

- Gardien d'équipe menée peut monter sur corner.

### 7.3 — Vérification Bloc A

- Déterminisme 100/100, mesure des comportements, captures.

---

## PARTIE 8 — BLOC C : COHÉRENCE DU RENDU

### 8.1 — Continuité inter-clips

- Enchaînement fluide entre clips successifs.

### 8.2 — Ombres

- Ombres cohérentes avec la position du ballon et des joueurs.

### 8.3 — État visuel

- Cohérence des positions de fin / début de clip.

### 8.4 — Ticket 26 : divergence moteur / narration sur penaltys ratés

- Couplage possible au Bloc C. À trancher par le propriétaire.

### 8.5 — Ticket 25 : clips de but avant la ligne

- Résolution au Bloc C ou avant.

### 8.6 — Vérification Bloc C

- Déterminisme, captures, revue globale.

---

## PARTIE 9 — TICKETS TRANSVERSES

### 9.1 — Tickets à traiter avant Phase 7 (carrière)

#### 9.1.1 — Ticket 3

- SubstitutionEvent identifie par nom, pas player_id. Priorité moyenne.

#### 9.1.2 — Ticket 24

- Commentaire faux dans engine/narrative.py. Basse priorité.

#### 9.1.3 — Ticket 27

- Dépassement tireur penalty. Basse à moyenne.

### 9.2 — Tickets à traiter pendant les blocs

#### 9.2.1 — Ticket 4

- Latence et poids du payload. Vectorisation apply_avoidance.

#### 9.2.2 — Ticket 16

- Point d'entrée seed manquant : np.random.seed + PYTHONHASHSEED=0.

#### 9.2.3 — Ticket 19

- Imports privés entre modules.

### 9.3 — Tickets basse priorité (post-Phase 7)

#### 9.3.1 — Tickets 6, 9, 10, 11, 12, 13, 15, 17, 18, 20, 21, 22

- Bruit, cas rares, limites acceptées.

### 9.4 — Ticket 26 (divergence moteur / narration)

- À trancher par le propriétaire : couplage Bloc C ou traitement séparé.

---

## PARTIE 10 — LIVRABLES FINAUX

### 10.1 — Moteur de simulation

- Moteur Poisson stable, déterministe, toutes décisions D6 / D7 / D8 appliquées.

### 10.2 — Moteur graphique 2D

- Rendu FM classic crédible.
- 12 gabarits, physique de balle, mouvement des joueurs, cohérence inter-clips.

### 10.3 — PWA et API

- FastAPI, React, iframe canvas, LineupSnapshot persisté.

### 10.4 — NLG

- Commentaire live cohérent avec le rendu.

### 10.5 — Documentation

- docs/phase6_block_b_audit.md, docs/known_issues.md, docs/DECISIONS.md.

### 10.6 — Phase 7 (carrière)

- À cadrer après clôture des Blocs A, B, C.

---

## SYNTHÈSE DES DÉCISIONS EN ATTENTE

| Décision | Objet | Responsable | Statut |
|---|---|---|---|
| B6-c — A | Dérives 79,9 % : accepter ou élargir | Propriétaire | En attente |
| B6-c — B | Autoriser modification test_narrative_player.py | Propriétaire | En attente |
| B6-d — B | Option 2 (glissement) vs Option 1 (plongeon) | Déjà tranché (Option 2) | Validé |
| B6-d — C | Spin sur penalty placé (traînée) | Déjà tranché (oui) | Validé |
| B6-e | Autorisation narrative.py | Propriétaire | À venir |
| B7 | Constantes produit coups francs | Propriétaire | À venir |
| B8 | Constantes produit contrôles | Propriétaire | À venir |
| A2 | D7 : constantes comportementales | Propriétaire | À venir |
| Ticket 26 | Couplage Bloc C | Propriétaire | À venir |

---

## ORDRE D'EXÉCUTION RECOMMANDÉ

1. B6-c finalisation (décisions A et B, tests, clôture).
2. B6-d (réaction gardien).
3. B6-e (ticket 23 NLG, commit séparé).
4. B7 (coups francs + mur).
5. B8 (contrôles variés).
6. Clôture Bloc B.
7. Bloc A (A1 puis A2).
8. Bloc C.
9. Tickets transverses.
10. Phase 7 (carrière).

---

Fin du plan.