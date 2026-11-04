# 09c: Échauffourées

**Découpé du ticket 09 le 04/11/2026** (audit de granularité). Détail : `09-discipline-fautes-cartons-blessures.md` (ajout du 03/11/2026, décision Q23).

**What to build:** après un tacle dur ou une faute, une échauffourée peut se déclencher : probabilité croissante avec l'Aggression des joueurs en présence, avec « Winds Up Opponents » de celui qui provoque (environ 1 % des joueurs, effet rare), avec l'enjeu du score et la minute. Conséquences : arrêt de jeu (ballon mort du ticket `v2-collectif/29`), attroupement visible (intentions de joueurs affichées par le rendu), carton éventuel (09a).

**Attributs :** Aggression ; geste « Winds Up Opponents ».

**Blocked by:** 09a, `v2-collectif/30` ; passe après `v2-collectif/22c`.

**Bloque :** aucun. Alimente `v2-mise-en-scene/03` (les échauffourées s'ajoutent au résumé à leur livraison) sans le bloquer.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Échauffourées plus fréquentes avec une Aggression élevée chez les joueurs en présence, à situation égale
- [ ] « Winds Up Opponents » augmente la fréquence et le risque de carton de la cible, sans effet sur la réussite des actions
- [ ] Attroupement visible à l'écran ; l'arrêt de jeu est compté dans le temps additionnel
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
