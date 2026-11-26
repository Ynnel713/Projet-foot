# 04o: Se retourner au contact : seulement quand l'angle, l'espace et le défenseur le permettent

**Chantier :** `v2-realisme` (audit duels, protection de balle, jeu dos au but, 26/11/2026). **Priorité :** P1 (évite le retournement systématique). **Catégorie :** exécution et décision.

**Constat vérifié (26/11/2026) :** dos au jeu, le retournement coûte un délai de rotation (07d, 07e, Agility du 07f) et un risque de perte sur ce délai (`decision.rotation_keep_probability`), qui reprend la loi de la conduite : Dribbling et distance de l'adversaire le plus proche (`possession.pressure`). Ni la force du contact (Strength des deux joueurs), ni le côté du défenseur, ni son engagement (il pousse fort, il contourne, il anticipe devant) ne comptent. Un attaquant collé par un défenseur solide se retourne donc aussi facilement qu'un attaquant marqué à 3 m.

**What to build:** au contact d'un défenseur dans son dos, le risque du retournement dépend :
- du **côté** : tourner du côté opposé au défenseur est jouable, tourner vers lui ne l'est presque pas ;
- de l'**engagement perçu du défenseur** (08b) : un défenseur lancé pour passer devant ou en déséquilibre (contact perdu du 12c, rotation en cours) laisse un retournement dans son dos ; un défenseur collé et stable le ferme ;
- du **rapport de force au contact** (Strength, part du `duel.contact_share` du 11b), pour garder le ballon pendant la rotation.
La valeur de l'option (décision) lit ce même risque : un joueur collé à un défenseur solide choisit la remise (31a), la protection (04i) ou l'ouverture, et ne se retourne que si l'occasion se présente. Retournement réussi : il fait face au jeu avec le défenseur battu derrière lui pendant un court temps (comme le crochet du 04h).

**Hors de ce ticket :** les gestes techniques de retournement (roulette, contrôle orienté dans le dos : 04m, 31b) ; la faute du défenseur battu (21c4).

**Attributs :** aucun effet nouveau : Agility (rotation, 07f), Strength (tenir le contact, 11b), Dribbling (garder en conduite serrée, 04a), Decisions (choisir, rayon existant). Cumul à justifier dans la carte (R1).

**Constantes à proposer avant le code :** facteur de risque par côté, effet de l'engagement du défenseur, durée de l'avantage gagné. Chiffre réel : non trouvé à ce jour (part des retournements réussis sous contact).

**Blocked by:** 04i (protection), 10l (marqueur collé).

**Bloque :** 04q (validation), 04n (le choix des gestes l'inclut).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne (légèrement au-dessus de 2 h : découpage examiné, non retenu, risque et décision lisent la même fonction). Hypothèses : le risque passe par `decision.rotation_keep_probability` (une seule fonction pour l'évaluation et la résolution, principe du 04a) ; l'engagement du défenseur se lit sur son état existant (cap, vitesse, contact perdu).

Temps machine, non compté : suite complète ; série appariée de 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** attaquant dos au jeu, défenseur collé et stable : retournement rare, remise ou protection choisies ; même scène, défenseur lancé pour passer devant : retournement fréquent et souvent réussi ; défenseur à gauche : rotation par la droite nettement plus réussie.
- **Comportementaux (profils comparés) :** Strength 90 contre 40 (porteur), défenseur identique : ballon gardé plus souvent pendant la rotation.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Une seule fonction de risque pour l'évaluation et la résolution du retournement
- [ ] Scènes ci-dessus dans le bon sens, jamais à 0 % ni 100 % (garde du 19c)
- [ ] En match (50 matchs) : part des réceptions dos au jeu sous contact suivies d'un retournement tenté, sous la cible validée ; issues (réussi, perdu, faute subie) rapportées
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
