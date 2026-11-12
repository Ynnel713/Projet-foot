# 22a: Calibration, lot 1 : volumes physiques, passes et rythme

**Découpé du ticket 22 le 04/11/2026** (audit de granularité) : la calibration reste **unique** (sur le moteur complet, une seule fois), mais en trois lots successifs, chacun clos par sa mesure. On règle d'abord ce qui fixe le volume des actions, puis la tactique, puis les tirs et les buts, qui dépendent des deux premiers. Bases de référence et réserves : `22-calibration-generale.md`.

**What to build:** régler, dans leurs fourchettes validées, les constantes de course, de passe et de duel, sur au moins 50 matchs. Chaque levier est proposé avant d'être appliqué.

**Attributs :** tous.

**Blocked by:** liste complète du ticket 22 : tickets 01 à 21 (18 : partie livrée ; ses critères restants sont clos par 22c) et 23 ; 28 (a, b, c) à 33 (32 : a et b) ; `v2-attributs-restants/01`, `02` (a, b), `03` (a, b, c), `07` (a, b) et `11` ; `v2-coach-et-gestion-de-match/03` ; `v2-realisme/20a`, `20b`, `20c`, `20d`, `20f`, `21c`, `19c` (ajouté le 10/11/2026, audit de la roadmap).

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

## Repris de la réserve A1 du ticket v2-realisme/18i (acceptée le 12/11/2026)

Portée de jambe du receveur visé et des lecteurs (`match.LEG_REACH_M`, 1,0 m), correction mécanique sans réglage. Effets mesurés sur 50 matchs appariés (`.scratch/v2-realisme/mesures/18i-bench-synthese.txt`), à traiter ici :
- [ ] Passes par match 933 → 1 006 (repère 890 à 940, désormais dépassé)
- [ ] Passes chez l'adversaire 16,6 → 12,8 % (repère 15 à 20 %, désormais en dessous)
- [ ] Possession d'équipe 23,8 → 27,1 s (repère 11 à 16 s, déjà hors repère, plus loin) ; passes par possession 3,8 → 4,7
- [ ] Passe longue réussie 68,3 → 73,2 % (réel indicatif 51,7 %), surtout par les passes imprécises rattrapées à 1 m
- [ ] Réserve A2 du 18i (acceptée le 12/11/2026) : le contrôle jambe tendue réussit aussi souvent qu'un contrôle du corps (`attempt_control` ne reçoit pas la distance de contact) ; levier possible ici ou dans un ticket dédié : difficulté de contrôle croissante avec la distance de contact au-delà de `CONTROL_RADIUS_M` (constante à proposer au propriétaire)
- [ ] Tables de la chance évaluée (`possession.py`, 18g/18h/18i) à remesurer après tout réglage qui change le mouvement ou le contrôle

