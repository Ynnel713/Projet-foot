# 03a: Gardien dans les airs : sorties sur centres, capter ou boxer

**Découpé du ticket 03 le 04/11/2026** (audit de granularité). Détail : `03-gardien-complet.md`.

**What to build:** sorties sur centres (Command of Area décide, Aerial Reach + Taille règlent la portée, dans la tranche « mains » de `v2-hauteur-ballon/03`), capter ou boxer (Punching, tendance), effet sur le placement des défenseurs (Communication).

**Attributs :** Command of Area, Aerial Reach, Punching, Communication ; Taille.

**Blocked by:** 01, 02 (a, b), `v2-hauteur-ballon/03`.

**Bloque :** `v2-coach-et-gestion-de-match/04` ; `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Punching est une **tendance**, pas une qualité (`docs/TRD_V2.md`) : elle change le style, jamais le niveau.

## Acceptance criteria

- [ ] Command of Area élevé : plus de sorties sur centres ; Aerial Reach + Taille : plus de sorties réussies
- [ ] Punching élevé : plus de ballons boxés, moins captés, à réussite égale
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
