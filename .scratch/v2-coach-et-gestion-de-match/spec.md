# Coach et gestion de match (V2)

Créé le 02/11/2026 à la demande du propriétaire, après analyse des tickets existants.

## Demande

1. Les styles des entraîneurs (Contre attaque, Pressing, Défensif, Offensif, Possession, colonnes de `data/Coachs-Simulafoot.xlsx`) influencent le comportement de leurs équipes et leurs remplacements.
2. Adaptation tactique en cours de match selon le score : l'équipe menée se découvre ; l'équipe qui mène continue d'attaquer ou protège son score selon le style du coach.
3. Dans le temps additionnel, une équipe menée d'un but prend de vrais risques, jusqu'à faire monter son gardien sur les coups de pied arrêtés.

## Constat (code vérifié le 02/11/2026)

- **V1 (Poisson)** : les styles modulent les lambdas (`simulation.py`, `STYLE_*`, ±15 % cumulés) et la possession affichée (`match_stats.py`). Les remplacements tactiques sont tirés au hasard (`events.py`, `random.shuffle(candidates_off)`), sans lien avec le coach, le score ni la fatigue.
- **V2 (moteur physique)** : seul le dispositif préférentiel du coach est utilisé (`pick_best_formation`). Aucun style, aucun remplacement, pas de temps additionnel (90 minutes fixes, `v2engine/match.py`), pas de coups de pied arrêtés. L'influence des coachs était différée (D-V10, `docs/TRD_V2.md`) ; **levée par le propriétaire le 02/11/2026**.
- `v2-collectif/21` couvre l'adaptation au score de façon générique (hauteur du bloc, prise de risque, Determination), sans style du coach, sans temps additionnel, sans gardien qui monte.

Revue expert du 02/11/2026 : REJECTED (A1 à A11), tickets corrigés le jour même puis resoumis.

## Tickets

| # | Titre | Bloqué par |
|---|---|---|
| 01 | Styles du coach traduits en consignes d'équipe | v2-collectif/05, 08, 10, 11, 12, 13, 15, 16, 17 |
| 02 | Gestion du score selon le style du coach | 01 ; v2-collectif/21 |
| 03 | Temps additionnel (mi-temps déplacée au 07) | 07 ; v2-attributs-restants/02 |
| 04 | Tout pour égaliser : risques et gardien qui monte | 02, 03 ; v2-attributs-restants/01, 02, 03 |
| 05 | Remplacements en V2 | 01, 02, 03, 07 ; v2-collectif/12 ; v2-attributs-restants/02, 04 |
| 06 | Remplacements V1 selon le coach, le résultat et la fatigue | — (option b et modification de `events.py` validées le 02/11/2026) |
| 07 | Mi-temps dans le moteur : arrêt, replacement, coup d'envoi | — |

## Règles communes

- Le style du coach donne des **tendances** (décalage de seuils ou de probabilités), jamais un ordre ni un comportement binaire.
- Un club sans coach ou sans style se comporte de façon neutre (PRD US-11).
- Chaque effet de style passe par un mécanisme déjà existant (hauteur du bloc, déclencheurs du pressing, valeur de la passe, etc.), jamais par une seconde mécanique parallèle (règle anti double comptage, v2-collectif/18).
- Déterminisme : toute variabilité dérive de sha256 d'une clé stable.
- Constantes produit proposées au propriétaire avant le code.

## Complément : audit des remplacements (26/11/2026)

Audit des remplacements contre cinq tickets proposés par le propriétaire (S1 à S5). Constat vérifié : aucun banc ni remplacement dans `v2engine/` ; le fond du temps additionnel (`added_time.BACKGROUND_S`) compte encore les remplacements.

- **S1, fenêtres et règle** : couvert par 05a (5 remplacements, 3 fenêtres hors mi-temps) ; complété par un critère qui teste la règle (Loi 3) et trace les fenêtres.
- **S2, décision de remplacer** : 05a (fatigue seule) et 05b (entrant selon le score, expulsion, blessure) ne combinent pas les raisons ; ni l'averti ni le joueur en difficulté ne sont traités, et le moteur n'a aucune mesure de la performance pendant le match → **05c**.
- **S3, choix du remplaçant** : couvert par 05b (poste, D-V07, profil selon le score) ; la fraîcheur ne départage pas les remplaçants (tous entrent frais) ; complété par le rôle de l'entrant (02c, 13h).
- **S4, effet du remplaçant** : fraîcheur couverte (05a, réserve pleine ; `v2-realisme/20d`). Rien ne modélise l'adaptation de l'entrant (la mémoire de perception du 08b le voit exactement dès son entrée, sur 2 s seulement). Complété au 05a : malus de cohésion temporaire, borné et décroissant, par la façade des notes (`v2-realisme/19a`), **soumis à la décision du propriétaire** (chiffre réel non trouvé, à chercher) ; mesure des 5 premières minutes de l'entrant.
- **S5, validation** : mesures éparpillées (05a, 05b, 20d) → **05d**.

| # | Titre | Estimation | Confiance | Bloqué par |
|---|---|---|---|---|
| 05c | Décision de remplacer : qui sort, selon la fatigue, le carton, la performance et la consigne | 2 h 10 | faible | 05a, 05b, 02 ; 09a et `v2-realisme/20b` pour leurs termes |
| 05d | Validation des remplacements : volume, minute, raisons, effet et cohérence avec le score | 1 h 40 | moyenne | 05a, 05b, 05c |

Total : 2 tickets, 3 h 50. Dépendances réciproques ajoutées : 02, 05a, 05b, `v2-attributs-restants/09a`, `v2-realisme/20b`. Ordre : 05a avant la calibration ; 05b, 05c puis 05d après `v2-collectif/22c` (contrôle de non-régression).

