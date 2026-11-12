# 18j: Revue du réalisme et réordonnancement de la P1

**Chantier :** `v2-realisme`. **Priorité :** P0 (organisation du chantier). **Catégorie :** documentation.

**Origine :** demande du propriétaire (12/11/2026) : « analyse les tickets qui ont été fait et ceux qu'il reste à faire et dis moi si le futur réalisme du jeu te semble en bonne voie […] Repère et dis moi si tu vois des manques ou des lacunes », puis « ok crée les tickets et réordonne la P1 ».

**What to build :** Consigner la revue (constats vérifiés dans le code) ; créer les tickets manquants (12h, `v2-hauteur-ballon/04`) ; ajouter aux tickets qui changent le mouvement le critère « table de passe du 18g remesurée » ; réordonner la vague P1 (socle physique, puis gestes, perception, tactique, fatigue et arbitrage) et la fin de la P0 dans `spec.md` ; donner sa priorité au 18i (P0) et son cadrage (cause mécanique, aucune constante réglée pour un chiffre).

**Blocked by :** 18h.

**Status :** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Rédaction | 20 min |
| Vérifications | 10 min |
| **Total (travail effectif)** | **45 min** |

Confiance : élevée. Hypothèse : documentation seule, aucun code. Temps machine : aucun.

## Acceptance criteria

- [x] Section 13 de `spec.md` : constats vérifiés, ordre revu, ordre d'origine conservé, table des tickets ajoutés
- [x] Section 6 de `spec.md` : fin de la P0 et vague P1 réordonnées, dépendances déclarées respectées : contrôle automatique `.scratch/v2-realisme/mesures/18j-ordre-check.py` (lit l'ordre dans la spec et le « Blocked by » de chaque ticket ; chaque prérequis livré ou placé avant), 81 tickets, aucune violation (`18j-ordre-check.txt`)
- [x] Tickets créés : 12h, `v2-hauteur-ballon/04` (format du chantier, estimation, critères)
- [x] Critère « table de passe remesurée » ajouté à 07g, 08f, 10j, 11e, 12g ; 12h ajouté aux dépendances de 12g
- [x] 18i : priorité P0 et cadrage (cause mécanique)
- [x] Tickets dont un prérequis est hors de la P1 placés après lui : 03l (`v2-attributs-restants/03b`), 23b (`v2-attributs-restants/01`), 21e et 21i (16h, Vague 3), 20e (13b, point 5)
- [x] Aucun code modifié ; suite non concernée (dernière suite : 2 759 passés, ticket 18h)

## Comments

**12/11/2026, passage 1.** Expert : REJECTED. Constats de la revue, tickets créés, critère de remesure et cadrage du 18i jugés justes ; mais six placements contredisaient des dépendances déclarées, alors que le critère « dépendances respectées » était coché sans contrôle systématique : `v2-hauteur-ballon/04` avant `v2-collectif/31` (A1) ; 20e, 21e, 21i, 23b et 03l avant des prérequis placés plus tard ou nulle part (A2). Réserve A3 : rayon de Balance dans 12h. Facultatif A4 : dépendance de 18j dans la table, « Bloque » de 12c. Pas de QC lancé.

**Corrections (option (a) de l'expert, sans changer de priorité).** `v2-hauteur-ballon/04` après `v2-collectif/31` (bloc 2) ; 03l, 23b, 21e, 21i et 20e placés après leurs prérequis (ligne « Après leurs prérequis hors de la P1 » ; 16h ajouté à la Vague 3) ; contrôle automatique écrit, qui a trouvé en plus 09h placé avant son prérequis 09i (corrigé) et les tickets de gestes `v2-collectif` 34a à 36b écrits sans préfixe (préfixés) ; `v2-collectif/15` placé avec 32a (« à livrer avec le 15 »). A3 : 12h précise que Balance ne module que la part due au contact. A4 : corrigé.

**12/11/2026, passage 2.** Expert : APPROVED (dépendances des 81 tickets reprises à la main, conformes au script). QC : VALIDÉ. Clôture : VALIDÉ. Facultatif (non traité) : table de la section 11 de la spec à aligner sur le ticket 21e (16h) ; code mort et chemin relatif dans `18j-ordre-check.py` (à lancer depuis la racine du dépôt) ; 16i, 16j, 16k absents de la Vague 3. À surveiller : relancer `18j-ordre-check.py` à chaque modification de l'ordre ou d'un « Blocked by » ; prévoir un créneau pour `v2-attributs-restants/03b` et `/01` (prérequis de 03l et 23b).

**Durée.** Estimée 45 min, réelle environ 1 h 30, non chronométrée (revue du code et des tickets 45 min, rédaction 20 min, reprise après le refus de l'expert et contrôle automatique 25 min) : + 100 %. Causes : estimation posée après la revue sans compter celle-ci ; dépendances d'abord vérifiées à l'œil, six violations relevées par l'expert, d'où le script de contrôle. Temps machine : aucun.
