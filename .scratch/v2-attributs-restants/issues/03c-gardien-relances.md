# 03c: Gardien : relances au pied et à la main

**Découpé du ticket 03 le 04/11/2026** (audit de granularité). Détail : `03-gardien-complet.md`.

**What to build:** relance au pied (Kicking : sortie de but, dégagement) et à la main (Throwing), dont le geste préféré « Uses Long Throw To Start Counter Attacks » (relance longue à la main, ticket 05).

**Attributs :** Kicking, Throwing.

**Blocked by:** 01, 02 (a, b) (dépendances d'origine du ticket 03, sans doute levables : les sorties de but existent depuis `v2-collectif/29`).

**Bloque :** `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Kicking / Throwing : distance et précision des relances mesurablement liées à l'attribut
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
