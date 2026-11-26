# 04p: Pression cumulée : un deuxième adversaire au contact

**Chantier :** `v2-realisme` (audit duels, protection de balle, jeu dos au but, 26/11/2026). **Priorité :** P1 (personne ne garde un ballon éternellement entouré). **Catégorie :** exécution.

**Constat vérifié (26/11/2026) :** la gêne du porteur ne lit que l'adversaire le plus proche (`possession.pressure` : `min` des distances) ; elle sert au risque de perte en conduite (`decision.keep_ball_probability`), au retournement (`rotation_keep_probability`) et à la difficulté du contrôle. Un porteur au contact d'un adversaire et entouré de deux autres court donc le même risque qu'avec un seul adversaire. Le `v2-collectif/20` (« un excellent dribbleur attire deux adversaires mais doit savoir lâcher le ballon ») porte sur la décision, pas sur ce risque.

**What to build:** `possession.pressure` reste entre 0 et 1 (douze appelants dans cinq modules le supposent : `restart.py`, `scan.py`, `decision.py`, `cerveau.py`, `possession.py`). Une **seconde composante**, « adversaires supplémentaires » (chaque adversaire au-delà du plus proche, dans le rayon, ajoute une part décroissante, bornée), est lue **seulement** par le risque de perte en conduite, la protection (04i), le retournement (`decision.rotation_keep_probability`) et la faute subie ; le scan, les coups de pied arrêtés et la vitesse de conduite n'en tiennent pas compte. Elle relève le risque de perte en conduite, pendant la protection (04i) et pendant le retournement, ainsi que la chance de faute subie (deux défenseurs qui serrent). La décision lit la même gêne : le porteur pris à deux lâche plus tôt le ballon (passe, remise) au lieu de forcer.

**Point de vigilance :** une seule définition de la gêne, partagée par l'évaluation et la résolution (principe du 04a) ; remesurer la saturation du `30b` (adversaires autour du point visé), qui ne doit pas recompter ce même effet.

**Attributs :** aucun nouveau (Dribbling, Strength gardent leurs rayons).

**Constantes à proposer avant le code :** part de gêne par adversaire supplémentaire, borne. Chiffre réel : non trouvé à ce jour (taux de perte selon le nombre de défenseurs engagés, à chercher dans les données de suivi `27a` à `27c`).

**Blocked by:** 04a (livré) ; 04i (pour la protection).

**Bloque :** 04q (validation).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : nouvelle fonction à côté de `possession.pressure`, inchangée ; appelants concernés listés avant le code (réserve A1 de l'expert, 26/11/2026) ; la difficulté du contrôle n'est pas touchée.
Temps machine, non compté : suite complète ; série appariée de 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même porteur, un adversaire au contact, puis un deuxième à 2 m, puis un troisième : risque de perte strictement croissant, jamais 100 %.
- **Comportementaux :** Strength 99 et Dribbling 99, trois adversaires au contact : le ballon est perdu ou lâché dans une majorité des tirages (pas d'invincibilité).

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Une seule définition de la gêne pour l'évaluation et la résolution ; test : `0 ≤ pressure ≤ 1` avec trois adversaires au contact, appelants hors périmètre inchangés
- [ ] Scènes ci-dessus dans le bon sens ; garde du 19c tenue
- [ ] 50 matchs appariés : pertes en conduite, passes sous pression, fautes subies rapportées ; écart expliqué
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
