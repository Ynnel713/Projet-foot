# Diagnostic : effondrement du hors-jeu V2 (30/10/2026)

Aucun code du dépôt modifié, aucun commit. Mesures hors dépôt (`C:\t`), `uv`-less : python du `.venv`,
`python -m scripts.measure_v2 10`, graine d'audit 20260923, même banc (pas 0,1 s partout).

## Recommandation (en tête)
La cause principale est la **nouvelle loi d'arrivée / freinage de `movement.step`** (ticket 25). Elle fait passer le
hors-jeu de 4,0 à 1,1 à elle seule. Je recommande de la **garder** (elle rend le mouvement réaliste) et de
**rouvrir la calibration du hors-jeu** (piste A ci-dessous) plutôt que de défaire le ticket 25.

## Chiffres mesurés (hors-jeu par match, 10 matchs)
| Configuration | Hors-jeu / match | Tirs / équipe |
|---|---|---|
| `b4a7264` (avant ticket 25) | 2,5 | 12,9 |
| `4d71418` (ticket 25) | 1,1 | 17,8 |
| `4d71418` + ancien `step` seul | **4,0** | 26,6 |
| `4d71418` + ancien contact du ballon seul | 1,8 | – |
| `4d71418` + ancien contrôle raté seul | 1,4 | – |
| `4d71418` + les trois anciens mécanismes | 3,4 | – |

## Lecture
- **`movement.step`** : gros effet (+2,9 en le remettant). C'est le coupable principal.
- **Contact du ballon sur le trajet** (`_contacts`) : effet moyen (+0,7). Plus de joueurs touchent la passe en
  chemin, donc moins de passes arrivent jusqu'à un joueur signalé.
- **Contrôle raté** : effet faible (+0,3), à la limite du bruit.
- **Pas 0,1 s / 0,15 s** : écarté, le banc et le moteur étaient déjà à 0,1 s à `b4a7264`.
- Les trois remis ensemble donnent 3,4, soit le niveau d'avant : le diagnostic est cohérent.

## Réserves
- 10 matchs : bruit de l'ordre de ±0,4 (loi de Poisson sur ~11 à 40 hors-jeu). Les effets de `step` (≈ ×3,6) sont
  nets ; ceux du contact et du contrôle raté sont indicatifs.
- Ma mesure de `b4a7264` est 2,5, pas 3,1 (mesure du ticket 23) : écart dû à l'échantillon ou au banc ; l'ordre de
  grandeur reste le bon.
- Variantes approximatives : le « contrôle raté » ancien est reconstitué (vitesse du joueur, sans délai) ; le tout
  est un monkeypatch, pas le code historique exact.
- Le tir par équipe monte fortement avec l'ancien `step` (26,6) : le hors-jeu y est lié à un jeu plus direct.
- **Mécanisme non vérifié** (hypothèse) : avec l'ancien `step` les joueurs dépassent leur cible et la ligne
  défensive/les appels des attaquants oscillent, donc plus d'attaquants se retrouvent derrière la ligne au
  moment de la passe. Le freinage borné les stabilise, donc le piège ne se déclenche presque plus. À confirmer en
  mesurant la position des attaquants par rapport à la ligne au départ des passes.
- Le ticket 07 (0,3) n'a pas été mesuré ici.

## Pistes à soumettre au propriétaire
A. **Recalibrer les appels en profondeur / le calage sur la ligne** (`PASS_OFFSIDE_MARGIN_M`, marge de prise
   de risque des attaquants) pour retrouver 3,2 à 3,5 avec le nouveau mouvement. Recommandée.
B. **Mesurer d'abord** l'écart attaquants/ligne au départ des passes (confirme l'hypothèse, 1 run).
C. Alléger le freinage (`DECEL_MAX_MPS2`) : déconseillé, c'est une constante validée du ticket 25 et l'effet
   sur le reste est large.
D. Défaire le contact sur trajet : déconseillé (effet faible, perte de réalisme).
Toute constante est à valider par le propriétaire.

## Mise à jour du 01/11/2026 : après le ticket 26

L'hypothèse « mécanisme non vérifié » ci-dessus est remplacée. La cause principale de l'effondrement mesuré après le ticket 25 était un bug : le passeur reprenait sa propre passe une fois sur deux (ticket 26, corrigé dans `ca5920a`), donc une passe vers un receveur hors-jeu n'arrivait presque jamais à lui.

Diagnostic refait sur 8 matchs (graine d'audit, `c379ba6` + correctif du 26, mêmes données que les mesures précédentes) :

| Passe vers un receveur hors-jeu | `b4a7264` (avant 25) | `c379ba6` (bug) | Corrigé |
|---|---|---|---|
| Sifflée | 41 % | 3 % | 50 % |
| Coupée par un adversaire | 23 % | 17 % | 50 % |
| Reprise par un coéquipier en jeu (avec le bug : surtout le passeur) | 32 % | 78 % | 0 % |

Position des attaquants au départ des passes (corrigé, contre `b4a7264`) : attaquant le plus avancé à 8,6 m derrière la ligne en médiane (8,7 m) ; à moins de 2 m de la ligne lors de 5,5 % des passes (12,6 %) ; au moins un attaquant hors-jeu lors de 1,6 % des passes (4,3 %) ; receveur hors-jeu 0,1 % des passes (15 en 8 matchs). Hors-jeu : 0,6 par match sur ce diagnostic, 0,75 sur les 20 matchs du ticket 26.

**Conclusion.** La règle et l'arbitrage fonctionnent ; les attaquants jouent rarement sur la ligne et les passes en profondeur sont presque absentes (0,2 %). Piste A (recalibrer la règle) écartée par le propriétaire le 01/11/2026 : elle gonflerait le chiffre sans rendre le jeu plus réaliste. Leviers : tickets 16 (appels complémentaires), 11 (transition offensive), 13 (valeur future de la passe) ; contrôle final au ticket 22.
