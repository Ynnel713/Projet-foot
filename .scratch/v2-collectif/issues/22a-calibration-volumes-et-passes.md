# 22a: Calibration, lot 1 : volumes physiques, passes et rythme

**Découpé du ticket 22 le 04/11/2026** (audit de granularité) : la calibration reste **unique** (sur le moteur complet, une seule fois), mais en trois lots successifs, chacun clos par sa mesure. On règle d'abord ce qui fixe le volume des actions, puis la tactique, puis les tirs et les buts, qui dépendent des deux premiers. Bases de référence et réserves : `22-calibration-generale.md`.

**What to build:** régler, dans leurs fourchettes validées, les constantes de course, de passe et de duel, sur au moins 50 matchs. Chaque levier est proposé avant d'être appliqué.

**Attributs :** tous.

**Blocked by:** liste complète du ticket 22 : tickets 01 à 21 (18 : partie livrée ; ses critères restants sont clos par 22c) et 23 ; 28 (a, b, c) à 33 (32 : a et b) ; `v2-attributs-restants/01`, `02` (a, b), `03` (a, b, c), `07` (a, b) et `11` ; `v2-coach-et-gestion-de-match/03` ; `v2-realisme/20a`, `20b`, `20c`, `20d`, `20f`, `21c`, `19c` (ajouté le 10/11/2026, audit de la roadmap) ; `v2-realisme/26a` (ajouté le 14/11/2026).

**Bloque :** 22b.

**Status:** à faire (constantes à proposer avant le code)

**Calibration finale (05/11/2026, décision du propriétaire) :** 22a, 22b et 22c forment la calibration **finale**, après les principaux développements tactiques, physiques et collectifs (chantier `v2-realisme` : orientation et perception 07, 08 ; occupation 09 ; défense 10 ; contacts 11 ; déplacements 12 ; conduite et duel 04), en plus de la liste ci-dessus. Elle part des valeurs des calibrations **provisoires** `v2-realisme/18d` (volumes, rythme) et `18e` (tirs, gardien), marquées « provisoire », et peut toutes les revoir. Au moins 500 matchs (`v2-realisme/01e`).

## Acceptance criteria

- [ ] Rythme du ticket socle 06 : 15-17 passes par minute, 2-3 s par joueur, possessions de 11-16 s
- [ ] Passes : receveur visé au moins 50 %, passes de plus de 32 m (environ 47 % réussies, 10-19 % des passes), passes réussies 70-90 %, au plus 25 % chez l'adversaire
- [ ] Courses du ticket 12 (distance, course intense, baisse en fin de match) ; tacles 30-40 par match (réserves A2 du ticket 09 et A3 du ticket 08)
- [ ] Fautes 21-26 par match (CIES) : le ticket 30 ne les tire que sur les tacles (environ 30 % des tacles, une dizaine par match) ; décision du propriétaire du 04/11/2026, l'écart est réglé ici (fautes de contact sans tacle, ou autre levier, à proposer avec les tacles) ; avec elles, penaltys 0,15-0,5 par match (0,10 au ticket 30, réel environ 0,34 en Ligue 1 ; réserve acceptée le 04/11/2026)
- [ ] Effet des attributs probabiliste, jamais binaire ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md` (ticket 18)
- [ ] Leviers et critères validés par le propriétaire avant le code
- [ ] Repris du ticket 22 : courbes partagées de `attributes` ; chiffres réels sourcés, ou « non trouvé »
- [ ] Repris de la réserve A1 du ticket v2-collectif/28a (acceptée le 05/11/2026) : volume de tirs (37,5 par équipe, réel 12-15) et part dans la surface (22 %, réel environ 68 %). Traiter l'écart xG du tir contre xT moyen de la conservation (le tir l'emporte entre 12 et 27 m dans l'axe dès qu'il est démarqué) : valeur de suite au lieu du xT moyen, ou seuil de tir relatif, comparés. Aucune référence calibrée ne se fonde sur les 4,44 buts par match du 28a
- [ ] Repris de la réserve A2 du ticket 28a (si le 28b ne l'a pas traitée) : un tir manqué ne coûte rien dans la décision, une passe ou une conduite paie la perte ; scène contrôlée « tir à 25 m contre conservation » avant et après
- [ ] Série d'au moins 40 matchs avec dispersion rapportée ; suite V2 verte ; V1 inchangée

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. Calibrer seulement après les effets de la condition (20a à 20d, 20f) et après les fautes hors du tacle (21c) : l'écart de fautes (9,4 contre 21-26 par match) vient d'un mécanisme absent et ne doit pas être comblé par un réglage. La garde probabiliste (19c) est rejouée après chaque lot de calibration.

## Repris du ticket v2-realisme/18i (12/11/2026, réserves acceptées par le propriétaire)

- A1 : après la portée du receveur (1,0 m), passes par match 1 043 (repère 890 à 940), passes chez l'adversaire 11,6 % (15 à 20 %), passes par possession 5,11 (3 à 5), possession d'équipe 28,3 s (11 à 16). Les valeurs d'avant étaient en partie dans le repère grâce au défaut corrigé.
- A2 : passe longue trop réussie, 76,6 % contre 51,7 % dans le réel (passe précise longue : 90 %).
- Calibration de la passe : chance évaluée trop basse de 5,9 et 6,9 points sur [0,5 ; 0,6[ et [0,4 ; 0,5[ (2,2 % des passes), écart accepté le 12/11/2026.
- A4 (facultatif) : un contrôle jambe tendue à 1 m du corps a la même difficulté qu'un contrôle dans le corps.

## Repris du ticket v2-realisme/18j (12/11/2026, réserves acceptées par délégation du propriétaire)

- État après le 18j (portée du lecteur 1,0 m, table remesurée ; section 33 de `docs/INDICATEURS_V2.md`) : passes par match 998, chez l'adversaire 12,5 %, passes par possession 4,63, possession d'équipe 26,9 s, passe longue réussie 75,0 % ; les écarts de calibration du 18i sur [0,4 ; 0,6[ sont résorbés (− 2,7 et − 1,9).
- A1 : calibration de la passe à − 7,0 points sur [0,3 ; 0,4[ (3 passes par match), systématique (− 7,1 hors ligne). Piste de l'expert : une case « deux adversaires ou plus près de la ligne » dans la table (interaction non multiplicative) plutôt que des retouches isolées.
- A2 : évaluation légèrement pessimiste en jeu (biais pondéré environ − 1,4 point) : passeur un peu prudent, pertes en conduite 54,6 → 61,5 par match, solutions ouvertes 4,71 → 3,96. Remesurer la table une fois le choix du passeur stabilisé, par itération jusqu'au point fixe (ajustement en jeu plutôt que hors ligne).

## Comments

**13/11/2026, repris du `v2-collectif/31a` (réserves A1 et A2 acceptées par le propriétaire).** A1 : passes par match 1 054 → 1 115 après le jeu à une touche (repère 890 à 940, déjà dépassé avant) ; la part de passes de première est juste (9,4 % pour 7,4 à 9,3 % au réel) mais s'applique à un volume trop haut (102 par match contre 64 à 73) ; passes par minute de jeu effectif 14,9 (15 à 17 visés) : les deux repères tirent en sens contraire, à trancher ici. A2 : une-deux inchangés (1,59 → 1,58 par équipe et par match) alors que les retours au passeur montent (2,4 → 3,4 %) : le passeur ne repart pas en course après sa passe ; à suivre ici et au ticket qui traitera cette course (à créer).

**14/11/2026, dépendance ajoutée (demande du propriétaire).** Attendre `v2-realisme/24` (nouvelle forme de la courbe partagée des attributs, vrais écarts entre 60 et 90) : la calibration finale doit partir des nouvelles courbes.
