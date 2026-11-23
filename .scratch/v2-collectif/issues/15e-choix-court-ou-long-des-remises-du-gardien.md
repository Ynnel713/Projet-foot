# 15e: Choix court ou long des remises du gardien, jugé comme en jeu

**Créé le 23/11/2026** à l'implémentation de `v2-attributs-restants/03c1`. **Chantier :** `v2-collectif`. **Priorité :** P2. **Catégorie :** décision.

**Constat vérifié (23/11/2026, séries du `03c1`, `.scratch/v2-attributs-restants/mesures/03c1-*.json`) :** le receveur d'une sortie de but est choisi par `restart.restart_target`, qui juge toute remise comme une passe au sol (1,8 point de difficulté par mètre, coupe en vol comprise), alors qu'une remise longue vole (vol aérien du `v2-collectif/29`) et qu'en jeu la relance longue est jugée en l'air, retombée disputée comprise (`decision.LONG_BALL_WON`, ticket `15a`). Deux essais du `03c1` : jugée en l'air sans la retombée, 81 % de sorties de but longues (environ 62 % avec le choix actuel) ; avec la retombée comptée à 0,5, 30 % et des buts + 1,04 [+ 0,28 ; + 1,80] par match sur 50 matchs. Le moteur, sans duel aérien, garde 85 % de ses longs ballons du gardien : la valeur 0,5 est juste pour le réel mais pas pour le moteur actuel, et les relances courtes deviennent trop fréquentes.

**What to build:** juger le choix du receveur d'une remise du gardien comme la relance en jeu (passe en l'air au-delà de `restart.LONG_RESTART_M`, Kicking, retombée disputée), une fois que la retombée se dispute réellement (duel aérien). Mesurer la part longue des sorties de but (repère réel à sourcer : part des sorties de but jouées long en Ligue 1) et la part des longs ballons du gardien gardés par son équipe (repère : environ la moitié).

**Attributs :** aucun nouveau (Kicking, Decisions déjà lus).

**Blocked by:** `v2-realisme/15b` (duel aérien) ; `v2-attributs-restants/03c1`.

**Bloque :** `v2-collectif/22a`.

**Status:** à faire (critères à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 20 min |
| Développement | 20 min |
| Tests | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs appariés, suite complète.

## Acceptance criteria

- [ ] Repère réel sourcé (part des sorties de but longues) et critères chiffrés proposés au propriétaire avant le code
- [ ] Même jugement d'une remise longue du gardien au choix et à l'exécution qu'en jeu
- [ ] Part longue des sorties de but et part des longs ballons gardés dans leurs fourchettes ; buts par match avec intervalle
- [ ] Déterminisme ; suite V2 verte ; V1 inchangée

## Comments

- 23/11/2026 (réserve A2 du `v2-attributs-restants/03c1`) : décomposer l'écart de buts de − 1,03 [− 1,71 ; − 0,35] par match entre Kicking 40 et 80 (ballons perdus selon la zone, buts après une remise du gardien) et mesurer le profil Kicking ; le choix doit aussi tenir compte de la portée du gardien (réserve A4 : un faible frappeur peut viser un receveur hors de portée).
