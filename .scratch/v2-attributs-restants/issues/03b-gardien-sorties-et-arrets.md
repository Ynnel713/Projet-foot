# 03b: Gardien : placement, sorties et arrêts

**Découpé du ticket 03 le 04/11/2026** (audit de granularité). Détail : `03-gardien-complet.md`.

**What to build:** placement et sorties hors de la surface (Rushing Out, tendance), goût du risque (Eccentricity, tendance), et levée de la dérogation A8 sur les tirs : Reflexes pour les tirs proches, One on Ones pour les face-à-face, Handling pour capter ou relâcher, y compris sur centre (la part neutre du ticket `v2-collectif/28b` est remplacée).

**Attributs :** Rushing Out, Eccentricity, Reflexes, One on Ones, Handling.

**Blocked by:** 01, 02 (a, b) (dépendances d'origine du ticket 03, sans doute levables) ; `v2-collectif/28b`.

**Bloque :** 10b (lob et dribble du gardien) ; `v2-coach-et-gestion-de-match/04` (Eccentricity alimente la montée du gardien) ; `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Rushing Out et Eccentricity sont des **tendances** : elles changent le style, jamais le niveau.

## Acceptance criteria

- [ ] Rushing Out élevé : position moyenne plus haute ; plus de ballons interceptés derrière la défense (le troisième volet du ticket 03, « plus de buts lobés », est mesuré au 10b, qui crée le lob)
- [ ] Dérogation A8 levée : Reflexes pour les tirs proches, One on Ones pour les face-à-face, Handling pour capter ou relâcher (moins de ballons relâchés quand il est élevé) (test de rayon des attributs, carte à jour)
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
