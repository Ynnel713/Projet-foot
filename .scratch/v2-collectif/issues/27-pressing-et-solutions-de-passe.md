# 27: Effet du pressing sur les solutions de passe

**What to build:** comprendre puis corriger pourquoi le pressing coordonné du ticket 08 laisse au porteur un peu plus de solutions de passe faciles (≥ 80 % de réussite, ≤ 40 m) au lieu d'en fermer. Le bloc doit rester compact pendant le pressing, de façon que suiveurs et presseur ne libèrent pas d'autres receveurs.

**Attributs :** Teamwork, Work Rate et Anticipation (déjà branchés au ticket 08). Pas de nouvel attribut.

**Blocked by:** 08.

**Status:** à faire

**Pourquoi (31/10/2026) :** mesures du ticket 08 sur 20 matchs : 1,42 → 1,57 solutions faciles. L'ablation sur 10 mi-temps (`.scratch/v2-collectif/mesures-08/`, note de session) montre un effet réparti entre déclencheurs collectifs, course orientée, relais, arrêt et intensité (environ +0,05 chacun), sans coupable unique. Profils : Teamwork 99 laisse 1,69 solutions faciles contre 1,53 à 11 (sens inverse). Work Rate n'a presque aucun effet : une possession individuelle dure environ 1,9 s, moins que la fenêtre d'effort de 5 s.

## Acceptance criteria

- [ ] Commencer par la fréquence des déclenchements collectifs par match (réserve A2 du ticket 08). Base du 01/11/2026, seuil de recul de 3 m : 692 par match sur 20 matchs ; sur 2 matchs, environ 200 passes en retrait, 340 réceptions en reculant (`BACKWARD_MPS`) et 114 contrôles ratés. La réception en reculant est la cause principale

- [ ] Le pressing coordonné laisse moins de solutions faciles que l'absence de pressing coordonné (même graine, 20 matchs)
- [ ] Teamwork haut laisse moins de solutions faciles que Teamwork bas
- [ ] Work Rate a un effet mesurable sur le pressing (temps, distance ou relais)
- [ ] Constantes validées par le propriétaire avant le code ; suite V2 verte
