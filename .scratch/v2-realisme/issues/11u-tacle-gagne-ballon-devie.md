# 11u: Tacle gagné : possession propre ou ballon dévié

**Chantier :** `v2-realisme` (audit duels, protection de balle, jeu dos au but, 26/11/2026). **Priorité :** P1 (beaucoup de duels finissent en ballon qui traîne, pas en possession propre). **Catégorie :** exécution.

**Constat vérifié (26/11/2026) :** un tacle gagné donne toujours le ballon au tacleur, arrêté à ses pieds (`match.py`, branche `result.won` : `ball.holder = challenger.name`, `ball.velocity = Vec2(0, 0)`). Le 04b a déjà rendu la perte en conduite variable (dépossession ou ballon libre), pas le tacle. Le tacle glissé (04j) annonce une issue distincte sans dire où part le ballon.

**What to build:** l'issue d'un tacle gagné se partage entre **possession propre** (comme aujourd'hui) et **ballon touché, pas maîtrisé** : il part selon la déviation au contact (05d), à une vitesse et dans une direction qui dépendent de l'angle d'approche (11d) et du type de tacle (debout, glissé du 04j). Le ballon libre se dispute normalement (chasseur du 11l, duel au sol du 11t). Tackling relève la part de possession propre (« récupère proprement » selon la carte), sans changer la chance de gagner le ballon.

**Attributs :** Tackling (part de possession propre, à placer dans un contexte du registre `v2engine/contextes.py` : la réussite du tacle et sa propreté sont deux effets, à justifier contre R1).

**Constantes à proposer avant le code :** part de possession propre à Tackling 11, 55, 99 ; par type de tacle (le glissé déviant plus souvent). Chiffre réel : non trouvé à ce jour (part des tacles réussis où l'équipe du tacleur garde le ballon).

**Blocked by:** 05d, 11d (livrés) ; 04j pour le volet glissé.

**Bloque :** 04q (validation).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications (50 matchs appariés) | 25 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : seule la branche `result.won` du tacle change ; la déviation du 05d s'applique telle quelle.
Temps machine, non compté : suite complète ; série appariée de 50 matchs.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Scène : Tackling 90 contre 40, même tacle gagné : possession propre plus fréquente à 90, jamais 100 %
- [ ] Ballon dévié tracé ; part des tacles gagnés suivis d'une possession de l'équipe du tacleur à 3 s rapportée sur 50 matchs
- [ ] Rayon des attributs conforme à la carte ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
