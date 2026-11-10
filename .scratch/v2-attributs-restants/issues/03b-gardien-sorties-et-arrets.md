# 03b: Gardien : placement, sorties et arrêts

**Découpé du ticket 03 le 04/11/2026** (audit de granularité). Détail : `03-gardien-complet.md`.

**What to build:** placement et sorties hors de la surface (Rushing Out, tendance), goût du risque (Eccentricity, tendance), et levée de la dérogation A8 sur les tirs : Reflexes pour les tirs proches, One on Ones pour les face-à-face, Handling pour capter ou relâcher, y compris sur centre (la part neutre du ticket `v2-collectif/28b` est remplacée).

**Attributs :** Rushing Out, Eccentricity, Reflexes, One on Ones, Handling.

**Blocked by:** 01, 02 (a, b) (dépendances d'origine du ticket 03, sans doute levables) ; `v2-collectif/28b` ; `v2-realisme/18e` (calibration provisoire du gardien neutre) (ajouté le 10/11/2026, audit de la roadmap).

**Bloque :** 10b (lob et dribble du gardien) ; `v2-coach-et-gestion-de-match/04` (Eccentricity alimente la montée du gardien) ; `v2-collectif/22a` ; `v2-realisme/03l` (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Rushing Out et Eccentricity sont des **tendances** : elles changent le style, jamais le niveau.

## Acceptance criteria

- [ ] Rushing Out élevé : position moyenne plus haute ; plus de ballons interceptés derrière la défense (le troisième volet du ticket 03, « plus de buts lobés », est mesuré au 10b, qui crée le lob)
- [ ] Dérogation A8 levée : Reflexes pour les tirs proches, One on Ones pour les face-à-face, Handling pour capter ou relâcher (moins de ballons relâchés quand il est élevé) (test de rayon des attributs, carte à jour)
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. Constat du 06b et du 06c : depuis le tir physique (`v2-realisme/05h`), l'arrêt est déterministe à position donnée et les notes du gardien n'agissent pas (`shooting.py`, commentaire du 28b). Précisions : (1) Reflexes, One on Ones et Handling agissent sur la portée physique (réaction, plongeon, prise), centrés sur le gardien neutre calibré au 18e : un gardien moyen garde le taux d'arrêt calibré ; (2) les erreurs du gardien sont des issues possibles même pour un très bon gardien (ballon relâché dans la surface, mauvaise appréciation de la trajectoire, sortie mal calibrée) ; (3) la garde probabiliste `v2-realisme/19c` doit passer sur l'arrêt.

- [ ] Gardien noté 99 : boulettes rares mais présentes sur 500 matchs ; gardien noté 40 : parade réflexe exceptionnelle présente

## Renvoi de la garde probabiliste (10/11/2026, ticket `v2-realisme/19c`)

L'arrêt ne lit aucune note du gardien : chance de but identique avec un gardien noté 11 ou 99 (portée physique seule, `shooting.keeper_reach_m`). Test d'écart connu : `test_known_gap_keeper_ratings_do_not_change_the_save` (`tests/test_v2engine_garde_probabiliste.py`). Quand ce ticket branchera les notes, retirer ce test et ajouter l'arrêt aux résolutions gardées (plancher 1 %, hiérarchie des notes).
