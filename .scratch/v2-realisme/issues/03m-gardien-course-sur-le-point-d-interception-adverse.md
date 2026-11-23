# 03m: Gardien : course au ballon libre jugée sur le point d'interception de l'adversaire

**Chantier :** `v2-realisme`. **Priorité :** P1 (le gardien sort sur des ballons qu'il croit gagner et les perd). **Catégorie :** décision.

**Constat vérifié (23/11/2026, ticket `v2-attributs-restants/03b3b`, sonde `.scratch/v2-attributs-restants/mesures/03b3b-sonde.py`) :** `gardien.race` compare le temps d'arrivée du gardien et celui de l'adversaire de champ le plus rapide **au même point**, celui que vise le gardien (`anticipation.loose_ball_target` pour le gardien). Or un ballon en mouvement est souvent pris plus tôt, sur sa trajectoire, par l'attaquant qui vient à sa rencontre. Sur 18 sorties inattendues avec une avance estimée du gardien de − 0,04 à + 0,59 s, l'adversaire a eu le ballon 10 fois, le gardien 2 fois, et 5 buts ont été encaissés dans les 15 s. Les sorties normales en souffrent aussi : 13,8 % des sorties disputées gagnées (`v2-realisme/03k`).

**What to build:** dans `gardien.race`, le temps de l'adversaire est pris à son propre point d'interception (`loose_ball_target` pour lui), et le gardien ne sort que s'il arrive avant l'adversaire à l'endroit où celui-ci toucherait le ballon (ou que ce point est derrière le sien sur la trajectoire). Mesurer : part des sorties disputées gagnées, buts encaissés après une sortie, sorties par match.

**Attributs :** aucun nouveau (Pace, Acceleration par `defense.arrival_time_s` ; Rushing Out et Eccentricity règlent déjà la marge et la fenêtre).

**Blocked by:** —

**Bloque :** `v2-attributs-restants/10b` (lob : un gardien sorti à tort) ; `v2-collectif/22a`.

**Status:** à faire (critères à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 20 min |
| Développement | 25 min |
| Tests | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs appariés, suite complète.

## Acceptance criteria

- [ ] Critères chiffrés proposés au propriétaire avant le code
- [ ] Scène : ballon qui roule vers un attaquant, gardien plus près du point final mais attaquant sur la trajectoire : pas de sortie
- [ ] Série de 50 matchs : part des sorties disputées gagnées en hausse, buts encaissés dans les 15 s après une sortie en baisse
- [ ] Déterminisme ; suite V2 verte ; V1 inchangée
