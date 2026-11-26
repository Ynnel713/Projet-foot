# 04q: Validation : jeu dos au but, protection et duels selon le profil

**Chantier :** `v2-realisme` (audit duels, protection de balle, jeu dos au but, 26/11/2026). **Priorité :** P1. **Catégorie :** validation.

**Constat vérifié (26/11/2026) :** chaque mécanisme a son ticket (04i, 04o, 04p, 10l, 11c, 11n, 11t, 11u, 31a), mais aucun contrôle ne vérifie l'ensemble : qu'un pivot costaud, un joueur technique, un défenseur dur sur l'homme et un joueur vif se reconnaissent en match, et que les trois pièges ne réapparaissent pas.

**What to build:** banc seulement, moteur inchangé.
1. **Indicateurs** (`scripts/v2_indicators.py`, définis dans `docs/INDICATEURS_V2.md`) : pour chaque réception dos au jeu sous contact, l'issue (remise ou déviation, retournement, protection puis passe, ouverture longue, perte, faute subie) et la durée de possession ; pertes sans contact réel (adversaire à moins de 1 m sans collision, tacle ni duel dans la fenêtre) ; part des retournements tentés quand le défenseur est collé ; issue des duels (gain net, contré, perte, faute) ; ballon gardé selon le nombre d'adversaires à moins de 2 m.
2. **Profils** (banc de profils existant) : pivot (Strength, First Touch, Teamwork hauts), joueur technique léger (Technique, Agility, First Touch hauts, Strength basse), défenseur dur (Marking, Aggression, Strength hauts), joueur vif (Agility, Acceleration, Anticipation hauts), comparés à un profil moyen.
3. **Pièges contrôlés** : aimant sans contact, retournement systématique, invincibilité physique.

**Attributs :** aucun.

**Blocked by:** 04i, 04o, 04p, 10l, 11t, 11u (et 11n pour le volet Balance).

**Bloque :** `v2-collectif/22a` (calibration des duels).

**Status:** à faire (cibles chiffrées à proposer au propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (indicateurs, profils) | 45 min |
| Tests (indicateurs sur données connues) | 25 min |
| Intégration et rapport | 25 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : le banc de profils existant accepte des profils à plusieurs attributs.
Temps machine, non compté : 50 matchs par profil ; suite complète.

## Acceptance criteria

- [ ] Cibles validées par le propriétaire avant le code (chiffres réels sourcés ou « non trouvé »)
- [ ] Pivot contre profil moyen : moins de pertes sur contact, plus de remises réussies sous pression, durée de protection plus longue
- [ ] Joueur technique : plus de retournements réussis quand le défenseur n'est pas collé, moins de protection longue que le pivot
- [ ] Défenseur dur : moins de retournements adverses réussis, plus de duels gagnés, plus de fautes que le profil moyen
- [ ] Joueur vif : plus de duels au sol gagnés par l'avance à l'arrivée que par le contact
- [ ] Aimant : pertes sans contact réel sous le plafond validé
- [ ] Retournement systématique : part de retournements tentés quand le défenseur est collé sous le plafond validé, plus basse que lorsqu'il ne l'est pas
- [ ] Invincibilité : profil Strength 99, trois adversaires à moins de 2 m : ballon perdu ou lâché dans une part au moins égale au plancher validé
- [ ] Écarts non atteints renvoyés chacun à un ticket, sans correction ici
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
