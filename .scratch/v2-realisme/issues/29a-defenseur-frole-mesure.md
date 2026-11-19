# 29a: Défenseur frôlé par une passe : temps, vitesse et orientation (mesure)

**Chantier :** `v2-realisme` (suite du ticket 28, réserve A2 de l'expert acceptée par le propriétaire le 19/11/2026 ; ordre des pistes validé par le propriétaire le 19/11/2026 : correction de l'interception d'abord). **Priorité :** P1. **Catégorie :** mesure (aucun changement de jeu).

**Constat (ticket 28, `docs/INDICATEURS_V2.md` section 55) :** 49 passes au sol par match passent, sur leur trajet, à moins de 1 m d'un défenseur qui ne les a pas lues, sans qu'il les touche : sa portée est `CONTROL_RADIUS_M` (0,41 m), contre 1 m pour le receveur et le lecteur (`match._ball_contacts`). Avant de choisir la correction (portée fixe, ou portée selon le temps de réaction et l'orientation), il manque ce que le 28 n'a pas relevé.

**What to build:** compléter `scripts/diag_passes_v2.py`, en lecture seule :
1. distance au ballon calculée en mouvement relatif, comme `match._contacts` (position de début de pas estimée par la vitesse ; facultatif A4 du 28), pour que les tranches soient celles que le moteur juge ;
2. pour chaque passe frôlée sur le trajet à moins de 1 m par un non-lecteur : temps écoulé depuis le départ de la passe quand le ballon passe au plus près (`reach_t`), vitesse du défenseur, angle entre son cap (`facing`, 07a) et la direction du ballon, Anticipation ; quantiles 10 / 25 / 50 / 75 / 90 %, par tranche 0,41-0,6 / 0,6-0,8 / 0,8-1 m ;
3. comptage de ce que donneraient les règles candidates du 29b (portée 0,8 ou 1 m ; temps de réaction minimal 0,2 / 0,25 / 0,3 s ; défenseur tourné vers le ballon ou non), sans les appliquer : nombre de passes que chaque règle rendrait touchables par match.

**Critères d'acceptation :**
- [ ] 50 matchs (graines du banc 0 à 49), moyennes par match avec IC 95 %.
- [ ] Les 5 « lecteurs à moins de 1 m sans contact » du 28 disparaissent avec la distance en mouvement relatif, ou leur cause restante est expliquée.
- [ ] Quantiles du point 2 et table des règles candidates du point 3 dans `docs/INDICATEURS_V2.md` (nouvelle section).
- [ ] Moteur inchangé : `tests/test_diag_passes_v2.py` passe toujours ; mêmes comptes que le 28 sur les indicateurs non touchés.
- [ ] Constantes du 29b proposées au propriétaire, chiffres à l'appui.

**Constantes de mesure :** tranches et seuils candidats ci-dessus (à valider avant le code ; aucune constante produit).

**Attributs :** aucun (mesure ; Anticipation seulement relevée).

**Blocked by:** 28 (livré).

**Bloque :** 29b.

**Status:** livré (19/11/2026), validé expert + QC (tranches et seuils candidats validés par le propriétaire le 19/11/2026 : « seuils validés »)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement (script) | 25 min |
| Tests | 10 min |
| Intégration et vérifications (rapport, proposition 29b) | 20 min |
| **Total (travail effectif)** | **1 h 05** |

Confiance : élevée. Hypothèses : le script du 28 se prolonge sans refonte ; `facing` et `velocity` sont lisibles dans l'observateur.
Temps machine, non compté : 50 matchs (environ 30 min sur 4 processus) ; suite complète (environ 15 min).

## Résultat (19/11/2026)

`scripts/diag_passes_v2.py` complété (distance du moteur en mouvement relatif, `_relative_closest`, testée contre `match._contacts` ; temps, vitesse, angle cap / ballon et Anticipation du défenseur frôlé ; règles candidates) ; rapport `docs/INDICATEURS_V2.md`, section 56 (50 matchs).

- Lecteurs frôlés à moins de 1 m sans contact : 5,0 → 0,04 par match (artefact du point de fin de pas, expliqué).
- Passes au sol frôlées sur le trajet à moins de 1 m par un non-lecteur : **36,0 par match** (49 au 28, avec l'ancienne distance).
- Trajet : temps depuis le départ médian 0,63 s, vitesse 2,8 m/s, angle cap / ballon 43°.
- Quantiles 10 / 25 / 50 / 75 / 90 % par partie et par tranche de distance (contrôle qualité, passage 1 : refusé faute des tranches ; corrigé).
- Règles candidates comptées sur tous les défenseurs non lecteurs de la passe (réserve A1 de l'expert, passage 1 : le seul plus proche donnait un minimum) : 0,8 m, 0,25 s, cap < 90° : 49,2 passes touchables par match (trajet 19,7, arrivée 29,9, départ 0,1) ; la portée pèse le plus (1 m : + 47 %), la réaction neutralise le presseur du départ.
- Proposition pour le 29b : 0,8 m, 0,25 s, cap < 90°, sur toute la passe au sol ; cible trajet 36 → 25 au plus, réussite des passes au-dessus de 80 %.
- Indicateurs non touchés identiques au 28.

## Comments

- 19/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (A1 : règles candidates comptées sur le seul défenseur le plus proche, un minimum présenté comme un maximum) ; QC REFUSÉ (quantiles demandés par tranche de distance, livrés par partie seulement). Corrigé : règles comptées sur tous les défenseurs non lecteurs (49,2 passes touchables par match contre 45,0), quantiles par partie et par tranche, rapport refait depuis la série (`--relire`).
- 19/11/2026, passage 2 : expert APPROVED ; QC REFUSÉ (section 56 limitée aux quantiles 25 / 50 / 75 %). Corrigé : tableau 10 / 25 / 50 / 75 / 90 % produit depuis la série par `_quantiles`.
- 19/11/2026, passage 3 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Facultatifs non faits : légende « non lecteur le plus proche » (le code exclut la passe si le plus proche est lecteur, 0,42 par match) ; règles évaluées à l'instant le plus proche de chaque défenseur (compte minimal) ; 0,42 lecteur frôlé non vérifié cas par cas.
- Durée : estimée 1 h 05 (10/25/10/20), réelle environ 1 h 50 (10/45/10/45), + 69 % : deux refus du contrôle qualité (quantiles par tranche, puis 10 et 90 % absents du document) et la réserve A1 de l'expert, qui a demandé une seconde série de 50 matchs ; cause : critère 3 du ticket lu trop vite à l'écriture du rapport.
