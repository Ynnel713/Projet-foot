# 03b: Mains du gardien, un seul modèle de portée

**Ouvert le 27/11/2026**, découpage du ticket 03.

**What to build:** la tranche « mains » du gardien, isolée du code des joueurs de champ, et commune aux deux chemins où le gardien joue le ballon :
1. `portee.keeper_hands_ceiling(...)` : plafond des mains, bras levés (z + r ≤ 1,258 H + détente ; épaule 0,818 + bras 0,186 + avant-bras 0,146 + main 0,108, Winter), dans sa propre surface. Hors de sa surface, le gardien suit les tranches de champ (Lois du jeu).
2. **Tir en vol** (`_keeper_reaches`, code des arrêts) : portée latérale du 05b inchangée ; le tir n'est atteint que s'il passe sous ce plafond au point de passage (le tir capté à 1,01 m du 02b2 le reste ; un lob au-dessus de ses mains passe).
3. **Ballon libre** (`_step_loose_ball`) : même plafond, par un seul aiguillage (`gardien dans sa surface → mains, sinon tranches de champ`).
4. Aerial Reach reste au `v2-attributs-restants/03a`.

**Constantes** : validées par le propriétaire le 27/11/2026 (voir 03a), aucune nouvelle.

**Blocked by:** 03a.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 10 min |
| Développement | 25 min |
| Tests | 25 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Temps machine hors total : série de 50 matchs, suite complète.

## Acceptance criteria

- [ ] Scène fixe : le gardien capte dans sa surface un ballon libre hors de portée d'un joueur de champ de 1,83 m (Jumping Reach 60)
- [ ] Scène fixe : tir à 1,01 m capté par `_keeper_reaches` ; tir au-dessus du plafond des mains non atteint
- [ ] Test d'isolation : la tranche « mains » n'est lue que par l'aiguillage ; hors de sa surface, le gardien suit les tranches de champ
- [ ] 50 matchs avant/après : arrêts, buts, prises du gardien sur ballon libre, réceptions « centre » ; écarts expliqués
- [ ] Mêmes empreintes à graine fixée ; suite complète au compte attendu ; V1 inchangée

## Comments
