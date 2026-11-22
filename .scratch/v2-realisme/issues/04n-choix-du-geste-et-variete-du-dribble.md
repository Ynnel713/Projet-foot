# 04n: Choix du geste de dribble selon la situation, et validation de la variété

**Chantier :** `v2-realisme` (complément de l'audit du dribble, 17/11/2026, demande du propriétaire). **Priorité :** P2. **Catégorie :** décision et validation.

**Constat vérifié (17/11/2026) :** le ticket d'origine `v2-attributs-restants/07a` prévoyait des gestes « choisis par la situation (jamais par un tirage libre) ; Decisions choisit, Flair ajoute les gestes risqués ». Au découpage, chaque geste est devenu un ticket (04g contournement, 04h crochet, 04i protection, 04k feinte, 04l changement de rythme, 04m gestes techniques) sans point unique qui choisit entre eux.

**What to build:** un seul endroit où le porteur face à un défenseur choisit son geste, dans la monnaie commune de la décision (`decision.py`, ticket 33) : chaque geste ouvert par la situation (distance et orientation du défenseur, espace latéral, vitesse relative, pression, position sur le terrain) reçoit sa valeur (chance de réussite, gain, coût de la perte) ; le porteur prend celui qu'il croit le meilleur, avec l'erreur de perception de Decisions, le goût du risque de Flair (`v2-attributs-contextes/05`) et les gestes préférés en penchants de fréquence (« Knocks Ball Past Opponent », « Tries Tricks », « Cuts Inside », « Likes To Beat Opponent Repeatedly », « Moves Ball To Left/Right Foot Before Dribble Attempt », ticket 05). Puis la **validation de la variété** : répartition des gestes par match, réussite et issue par geste, profils 99 / 11 de Dribbling, Flair et Technique, comparés aux repères réels s'ils sont trouvés (dribbles tentés et réussis par match).

**Attributs (ADR 0002) :** aucun effet nouveau dans ce ticket : il assemble les contextes des tickets 04g à 04m ; Decisions (perception), Flair (goût du risque), gestes préférés (fréquence).

**Lien avec l'existant :** remplace le « choix du geste » de `v2-attributs-restants/07a` ; à livrer avant la calibration (`v2-collectif/22a`), comme le prévoyait 07a.

**Blocked by:** 04g, 04h, 04i, 04k, 04l, 04m ; `v2-attributs-contextes/05` (Flair) ; `v2-attributs-restants/05a` pour les penchants (05 découpé le 22/11/2026 : la ligne « Conduite et dribble » passe avant la calibration, levée de l'incohérence avec le 05 qui passait après).

**Bloque :** `v2-collectif/22a` (calibration des volumes).

**Status:** à faire (constantes et chiffres réels à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible. Hypothèses : chaque geste expose déjà sa chance de réussite et son effet (tickets 04g à 04m) ; le choix réutilise `choose_action` (une option par geste ouvert). Au-dessus du seuil de 2 h : découpage à examiner (choix, puis validation de la variété).
Temps machine, non compté : suite complète ; séries de 50 matchs ; banc de profils (`scripts/measure_v2.py --profil`).

## Tests

- **Scènes :** même porteur, trois situations (défenseur de face immobile, défenseur lancé de côté, défenseur au contact dans le dos) : le geste le plus choisi diffère selon la situation ; à Flair 99, les gestes risqués sont plus fréquents qu'à 11 ; un geste préféré augmente sa fréquence sans changer sa réussite.
- **Statistiques (50 matchs) :** au moins quatre gestes différents chacun au-dessus d'une part minimale validée ; aucun geste au-dessus d'une part maximale validée ; dribbles tentés et réussis par match comparés au repère réel s'il est trouvé.

## Acceptance criteria

- [ ] Constantes produit (parts minimale et maximale par geste) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Un seul point de choix du geste, tracé au journal des décisions (geste, options envisagées, raison)
- [ ] Scènes et statistiques ci-dessus ; profils 99 / 11 dans le plafond d'écart de la carte
- [ ] Effets des attributs probabilistes, jamais binaires ; pas de double comptage (R1)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
