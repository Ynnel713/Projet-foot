# 09: Discipline : fautes, cartons et blessures

**What to build:** La V2 n'a ni fautes sanctionnées, ni cartons, ni blessures. Plusieurs caractéristiques ne peuvent donc pas exprimer leur **contrepartie** :

- **Aggression** : plus de duels engagés (déjà prévu) mais aussi plus de fautes et de cartons (carte des attributs).
- **Bravery** : va au contact dangereux, avec un risque de blessure.
- Gestes **Dives Into Tackles** (tacle glissé : plus de ballons gagnés, plus de fautes), **Does Not Dive Into Tackles**, **Argues With Officials** et **Winds Up Opponents** (plus de cartons pour soi ou pour l'adversaire provoqué).

Ajouter : une faute possible sur un duel perdu ou mal engagé, sa sanction (coup franc ou penalty selon le lieu, via le ticket 02), un carton selon la gravité et l'historique du joueur, l'expulsion (équipe à 10) et une blessure rare, qui force un remplacement (v2-coach-et-gestion-de-match/05).

**Échauffourées (ajout du 03/11/2026, décision Q23).** Après un tacle dur ou une faute, une échauffourée peut se déclencher : probabilité croissante avec l'Aggression des joueurs en présence, avec « Winds Up Opponents » de celui qui provoque (environ 1 % des joueurs, effet rare), avec l'enjeu du score et la minute. Conséquences : arrêt de jeu, attroupement visible (intentions de joueurs affichées par le rendu), carton éventuel. Avant ce ticket, il n'y en a pas. Elle utilise le ballon mort du ticket `v2-collectif/29`.

**Attributs :** Aggression, Bravery, Tackling (qualité du tacle, pour séparer faute et réussite) ; gestes ci-dessus.

**Blocked by:** 02 (coups francs et penalties), 07 (duels), `v2-collectif/29` (ballon mort) et `v2-collectif/30` (fautes sifflées).

**Status:** découpé (04/11/2026, audit de granularité) en 09a (fautes graves, cartons, expulsions), 09b (blessures) et 09c (échauffourées). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Point de vigilance :** la réussite du tacle dépend uniquement de Tackling (correction A1 de v2-collectif/18) ; Aggression règle l'envie d'engager et le risque de faute, pas la réussite.

- [ ] Fautes, cartons jaunes, rouges et blessures par match dans des fourchettes réelles sourcées (ou « non trouvé »)
- [ ] Aggression élevée : plus de duels engagés **et** plus de cartons, à Tackling égal
- [ ] Dives Into Tackles : plus de tacles glissés et plus de fautes qu'un joueur aux mêmes attributs sans ce geste
- [ ] Une équipe à 10 se réorganise sans téléportation
- [ ] Échauffourées : plus fréquentes avec une Aggression élevée chez les joueurs en présence, à situation égale ; « Winds Up Opponents » augmente la fréquence et le risque de carton de la cible, sans effet sur la réussite des actions ; l'arrêt de jeu est compté dans le temps additionnel
- [ ] Déterministe pour une graine donnée
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
