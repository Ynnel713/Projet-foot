# 03b2: Gardien : capter ou repousser (Handling), boulettes

**Découpé du ticket `03b` le 22/11/2026** (décision du propriétaire). Gardien moyen : médiane des gardiens de Ligue 1 de la base (Reflexes 75, One on Ones 75, Handling 60) ; un gardien sans note (effectif synthétique, copie neutre de l'xG) vaut le gardien moyen.

**What to build:** Handling règle la part captée d'un arrêt (`shooting.save_shares`, aujourd'hui gardien neutre) : le haut capte, le bas repousse et offre une seconde occasion. Erreurs du gardien possibles même pour un très bon gardien (ballon relâché dans la surface), plus fréquentes pour un mauvais. Gardien noté 99 : boulettes rares mais présentes sur 500 matchs ; noté 40 : parade réflexe exceptionnelle présente.

**Attributs :** Handling. Centres : `03a` (Punching) reste à part.

**Blocked by:** `03b1`.

**Bloque :** `10b` ; `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 15 min |
| Développement | 30 min |
| Tests | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Temps machine, non compté : suite complète ; 50 matchs appariés.

## Acceptance criteria

- [ ] Réserve A1 de l'expert au `03b1` : `shot_probability` ne lit plus les notes du gardien depuis le `03b1`, ce qui déplace la difficulté de l'arrêt (`save_shares`) ; mesurer avant / après la part captée / repoussée / claquée et la part des corners issus d'arrêts (repère du `28b` : environ 20 %), recaler `SAVE_HELD_SHARE` au besoin (au `03b1`, 50 matchs : capté 53,7 % → 53,0 %, repoussé 30,7 % → 32,1 %)

- [ ] Constantes proposées au propriétaire avant le code
- [ ] Moins de ballons relâchés avec Handling élevé (scène et 50 matchs) ; gardien moyen inchangé
- [ ] Boulettes : rares mais présentes pour un 99 ; parade exceptionnelle présente pour un 40
- [ ] Test de rayon et carte à jour ; Handling sort de la liste de transition
- [ ] Durée réelle relevée ; déterminisme ; suite V2 verte ; V1 inchangée
