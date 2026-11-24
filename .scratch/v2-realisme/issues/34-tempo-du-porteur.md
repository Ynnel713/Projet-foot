# 34: Tempo du porteur : temporiser ou accélérer selon l'état du jeu

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur l'intelligence de jeu, point 1 « dicter le tempo »). **Priorité :** P2. **Catégorie :** décision.

**Constat vérifié (24/11/2026) :** le porteur choisit l'option qu'il croit la meilleure à chaque décision (`decision.choose_action`), à un rythme fixé par le délai de réception (`possession.reception_delay_s`, contrôle orienté `v2-collectif/31b`) et l'intervalle de décision ; après une récupération, son équipe choisit contre-attaque ou conservation (`v2-collectif/11`, livré). Il n'existe pas d'option « temporiser » qui vaille plus quand l'équipe est étirée ou exposée à une transition adverse, ni de raccourcissement du délai quand un espace s'ouvre, hors de la construction sous pressing (`v2-collectif/15b3`, à faire).

**What to build:**
- **Calmer le jeu** : quand son équipe est mal placée derrière le ballon (lignes étirées, peu de joueurs derrière le ballon, transition adverse dangereuse en cas de perte), garder le ballon, le protéger (`v2-realisme/04i`) et orienter le corps vaut plus qu'une passe forcée : la valeur d'une perte y est déjà plus chère (`danger.loss_cost`), ce ticket ajoute ce qu'une seconde de plus rapporte (équipe qui se replace), dans la monnaie commune.
- **Casser le rythme** : quand un espace s'ouvre entre les lignes ou qu'un partenaire attaque le dos adverse, il joue plus tôt (délai raccourci, prise de balle orientée), sur ce qu'il perçoit.
- **Contexte du match** (temps forts et faibles, score, fin de match) : relève du style d'équipe (`v2-realisme/13f`, tempo de la consigne) et de l'adaptation au score (`v2-collectif/21`) ; ce ticket fournit le mécanisme individuel qu'ils modulent.
Le cas de la construction sous pressing reste au `v2-collectif/15b3` (même mécanisme de délai) ; ce ticket le généralise hors de ce cas, sans le recouvrir.

**Attributs :** Decisions (choisir de temporiser ou d'accélérer, erreur de perception existante) ; Composure (sous pression, rôle existant) ; un contexte du registre (ADR 0002) si plusieurs se combinent, à proposer avant le code.

**Blocked by:** `v2-collectif/15b3` (mécanisme du délai après contrôle). **Bloque :** `v2-realisme/13f` (tempo de style, qui le module) ; `v2-realisme/35` (volet de la validation, souple).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : faible (au-delà de 2 h : découpage probable au lancement, calmer le jeu / casser le rythme). Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés avant le code ; découpage examiné
- [ ] Scène : porteur au milieu, équipe étirée et transition adverse dangereuse : il temporise plus souvent qu'avec une équipe en place ; espace qui s'ouvre entre les lignes : il joue plus tôt
- [ ] Série : durée des possessions, pertes en transition, buts encaissés sur contre, passes vers l'avant (avant / après)
- [ ] Rayon des attributs conforme à la carte ; déterminisme ; suite complète au compte attendu ; durée réelle relevée

## Comments
