# 09a: Fautes graves, cartons et expulsions

**Découpé du ticket 09 le 04/11/2026** (audit de granularité). Détail : `09-discipline-fautes-cartons-blessures.md`.

**What to build:** à partir de la gravité enregistrée par `v2-collectif/30`, un carton selon la gravité et l'historique du joueur (second jaune), l'expulsion et l'équipe à 10 qui se réorganise. Expression de la **contrepartie** des caractéristiques :
- **Aggression** : plus de duels engagés mais aussi plus de fautes et de cartons ;
- gestes **Dives Into Tackles** (plus de tacles glissés, ballons gagnés et fautes), **Does Not Dive Into Tackles**, **Argues With Officials** (plus de cartons pour soi).

**Attributs :** Aggression, Tackling (réussite, pour séparer faute et réussite) ; gestes ci-dessus.

**Blocked by:** 02a (penalty), 07a (duels), `v2-collectif/29` (livré), `v2-collectif/30` ; passe après `v2-collectif/22c` (contrôle de non-régression).

**Bloque :** 09b, 09c ; `v2-coach-et-gestion-de-match/05b` (remplacement après un carton). Alimente `v2-mise-en-scene/02` (cartons rouges, ajoutés à leur livraison) sans le bloquer.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** la réussite du tacle dépend uniquement de Tackling (correction A1 de v2-collectif/18) ; Aggression règle l'envie d'engager et le risque de faute, pas la réussite.

## Acceptance criteria

- [ ] Cartons jaunes et rouges par match dans des fourchettes réelles sourcées (ou « non trouvé »)
- [ ] Aggression élevée : plus de duels engagés **et** plus de cartons, à Tackling égal
- [ ] Dives Into Tackles : plus de tacles glissés et plus de fautes qu'un joueur aux mêmes attributs sans ce geste ; Does Not Dive Into Tackles : moins de tacles glissés et moins de fautes ; réussite du tacle inchangée dans les deux cas (repris du ticket 05)
- [ ] Une équipe à 10 se réorganise sans téléportation
- [ ] Cartons tracés et affichés à l'écran
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
