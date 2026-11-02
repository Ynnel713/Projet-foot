# 09: Discipline : fautes, cartons et blessures

**What to build:** La V2 n'a ni fautes sanctionnées, ni cartons, ni blessures. Plusieurs caractéristiques ne peuvent donc pas exprimer leur **contrepartie** :

- **Aggression** : plus de duels engagés (déjà prévu) mais aussi plus de fautes et de cartons (carte des attributs).
- **Bravery** : va au contact dangereux, avec un risque de blessure.
- Gestes **Dives Into Tackles** (tacle glissé : plus de ballons gagnés, plus de fautes), **Does Not Dive Into Tackles**, **Argues With Officials** et **Winds Up Opponents** (plus de cartons pour soi ou pour l'adversaire provoqué).

Ajouter : une faute possible sur un duel perdu ou mal engagé, sa sanction (coup franc ou penalty selon le lieu, via le ticket 02), un carton selon la gravité et l'historique du joueur, l'expulsion (équipe à 10) et une blessure rare, qui force un remplacement (v2-coach-et-gestion-de-match/05).

**Attributs :** Aggression, Bravery, Tackling (qualité du tacle, pour séparer faute et réussite) ; gestes ci-dessus.

**Blocked by:** 02 (coups francs et penalties), 07 (duels).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** la réussite du tacle dépend uniquement de Tackling (correction A1 de v2-collectif/18) ; Aggression règle l'envie d'engager et le risque de faute, pas la réussite.

- [ ] Fautes, cartons jaunes, rouges et blessures par match dans des fourchettes réelles sourcées (ou « non trouvé »)
- [ ] Aggression élevée : plus de duels engagés **et** plus de cartons, à Tackling égal
- [ ] Dives Into Tackles : plus de tacles glissés et plus de fautes qu'un joueur aux mêmes attributs sans ce geste
- [ ] Une équipe à 10 se réorganise sans téléportation
- [ ] Déterministe pour une graine donnée
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
