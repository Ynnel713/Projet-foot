# 09a: Fautes graves, cartons et expulsions

**Découpé du ticket 09 le 04/11/2026** (audit de granularité). Détail : `09-discipline-fautes-cartons-blessures.md`.

**What to build:** à partir de la gravité enregistrée par `v2-collectif/30`, un carton selon la gravité et l'historique du joueur (second jaune), l'expulsion et l'équipe à 10 qui se réorganise. Expression de la **contrepartie** des caractéristiques :
- **Aggression** : plus de duels engagés mais aussi plus de fautes et de cartons ;
- gestes **Dives Into Tackles** (plus de tacles glissés, ballons gagnés et fautes), **Does Not Dive Into Tackles**, **Argues With Officials** (plus de cartons pour soi).

**Attributs :** Aggression, Tackling (réussite, pour séparer faute et réussite) ; gestes ci-dessus.

**Blocked by:** 02a (penalty), 07a (duels), `v2-collectif/29` (livré), `v2-collectif/30` ; passe après `v2-collectif/22c` (contrôle de non-régression) ; `v2-realisme/21b` (gravité selon l'action) ; `v2-realisme/21a` recommandé (décision de l'arbitre) (ajouté le 10/11/2026, audit de la roadmap) ; `v2-coach-et-gestion-de-match/09` (règle commune du fond du temps additionnel, ajouté le 26/11/2026, audit de la gestion de match).

**Bloque :** 09b, 09c ; `v2-realisme/11o` (prudence au tacle selon le risque de carton, ajouté le 16/11/2026) ; `v2-realisme/21f`, `21g`, `21h` (ajouté le 10/11/2026, audit de la roadmap) ; `v2-coach-et-gestion-de-match/05b` (remplacement après un carton) ; `v2-coach-et-gestion-de-match/05c` (sortie d'un averti, terme « carton », ajouté le 26/11/2026, audit des remplacements) ; `v2-coach-et-gestion-de-match/08` (jouer à dix, ajouté le 26/11/2026, audit de la gestion de match). Alimente `v2-mise-en-scene/01b` et `02` (carton rouge en Tier 1, carton jaune en surimpression Tier 3, ajoutés à sa livraison ; 26/11/2026) sans les bloquer.

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

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. La gravité tirée dans des parts fixes (`duel.foul_severity`) est remplacée par la gravité de l'action (`v2-realisme/21b`), avec les cas de la loi 12 (occasion manifeste annulée, attaque prometteuse arrêtée). Le carton s'applique à la **décision** de l'arbitre (`v2-realisme/21a`), pas au fait réel, pour que la VAR (`21g`, `21h`) puisse corriger. Contestations : l'effet « Argues With Officials » reste ici ; l'animation va à `v2-mise-en-scene/06`.

## Complément de l'audit de la gestion de match (26/11/2026)

Un carton fait perdre du temps (arrêt, sanction, contestation) : la directive IFAB 2023 le range parmi les causes rattrapées. Ce ticket ne le comptait pas. Il est compté par la règle commune du `v2-coach-et-gestion-de-match/09`, qui retire la part « cartons » du fond. La façon dont l'équipe joue à dix (resserrer, protéger l'axe, couverture d'abord) va au `v2-coach-et-gestion-de-match/08` ; ce ticket garde la réorganisation sans téléportation.

- [ ] Temps perdu par un carton compté dans le temps additionnel, part « cartons » du fond retirée sans double comptage (test)
