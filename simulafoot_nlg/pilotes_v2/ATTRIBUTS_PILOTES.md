# Attributs conditionnés par les pilotes V2 — couverture ET sélectivité

Régénérer : `uv run python -m scripts.audit_conditions_pilote --attributs`
(base `data/simulafoot.db`, 7563 joueurs, 6675 joueurs de champ hors GK).

**Deux mesures différentes, ne pas les confondre :**
- **Couverture attribut** = part des joueurs ayant une valeur non NULL. Dit si
  l'attribut est *exploitable* (ex. Aggression 93,0 %).
- **Sélectivité du seuil** = part des joueurs de champ qui *matchent* la
  condition réellement utilisée. Dit combien la condition *filtre* (ex.
  `Aggression >= 60` : 57,4 % — l'attribut est à 93 % mais le seuil retient
  plus de la moitié des joueurs ; ce n'est pas « tous les joueurs »).

Lecture : une condition seule dont la sélectivité dépasse 50 % est dominante
(elle ne discrimine pas) ; sous 20 joueurs en base, un SURNOM est un fantôme.
Les valeurs FM sont quantifiées par pas de 5 : `>= 78` et `>= 80` sont
équivalents (cosmétique, pas de perte). `preferred_moves` : couverture 9,3 %
(703/7563 renseignés) — les effectifs de moves sont des planchers.

| Attribut | Seuil utilisé | Pilotes | Couverture attribut | Sélectivité du seuil (% joueurs de champ) | Matchent (base) |
|---|---|---|---|---|---|
| Aggression | `<= 50` | defense, faute_simple | 93.0% | 26.0% | 2232 |
| Aggression | `<= 55` | defense, faute_simple | 93.0% | 35.3% | 2938 |
| Aggression | `<= 60` | faute_simple | 93.0% | 49.6% | 3997 |
| Aggression | `<= 65` | faute_simple | 93.0% | 64.7% | 5081 |
| Aggression | `<= 70` | faute_simple | 93.0% | 75.3% | 5829 |
| Aggression | `<= 75` | faute_simple | 93.0% | 83.8% | 6426 |
| Aggression | `<= 78` | faute_simple | 93.0% | 83.8% | 6426 |
| Aggression | `>= 45` | faute_simple | 93.0% | 80.2% | 5894 |
| Aggression | `>= 50` | faute_simple | 93.0% | 74.8% | 5441 |
| Aggression | `>= 55` | faute_simple | 93.0% | 66.8% | 4805 |
| Aggression | `>= 60` | defense, faute_simple | 93.0% | 57.4% | 4099 |
| Aggression | `>= 65` | carton_jaune | 93.0% | 43.2% | 3040 |
| Aggression | `>= 70` | carton_jaune, faute_simple | 93.0% | 28.1% | 1955 |
| Aggression | `>= 75` | carton_jaune | 93.0% | 17.4% | 1208 |
| Aggression | `>= 80` | carton_jaune | 93.0% | 9.0% | 611 |
| Aggression | `>= 85` | carton_jaune | 93.0% | 3.4% | 226 |
| Anticipation | `<= 50` | carton_jaune | 93.0% | 16.9% | 1375 |
| Composure | `<= 45` | carton_jaune | 93.0% | 13.1% | 1124 |
| Composure | `<= 55` | tir_non_cadre | 93.0% | 39.5% | 3123 |
| Decisions | `<= 45` | carton_jaune | 93.0% | 12.7% | 941 |
| Determination | `>= 80` | carton_jaune | 93.0% | 13.5% | 1001 |
| Finishing | `<= 40` | tir_non_cadre | 81.9% | 39.2% | 2619 |
| Finishing | `<= 60` | tir_non_cadre | 81.9% | 77.0% | 5137 |
| Finishing | `<= 65` | tir_non_cadre | 81.9% | 84.5% | 5640 |
| Finishing | `<= 70` | tir_non_cadre | 81.9% | 89.4% | 5965 |
| Finishing | `>= 78` | tir_non_cadre | 81.9% | 1.1% | 76 |
| Finishing | `>= 80` | tir_non_cadre | 81.9% | 1.1% | 76 |
| Finishing | `>= 85` | tir_non_cadre | 81.9% | 0.3% | 22 |
| First Touch | `<= 55` | tir_non_cadre | 93.0% | 31.0% | 2831 |
| Flair | `>= 75` | carton_jaune | 93.0% | 12.0% | 805 |
| Heading | `>= 75` | corner | 81.9% | 7.4% | 496 |
| Heading | `>= 78` | corner | 81.9% | 3.0% | 199 |
| Heading | `>= 80` | corner, defense | 81.9% | 3.0% | 199 |
| Heading | `>= 82` | corner, defense | 81.9% | 0.9% | 59 |
| Heading | `>= 85` | corner | 81.9% | 0.9% | 59 |
| Heading | `>= 88` | corner, defense | 81.9% | 0.2% | 15 |
| Leadership | `>= 80` | carton_jaune | 93.0% | 2.5% | 195 |
| Long Shots | `>= 60` | tir_non_cadre | 81.9% | 25.9% | 1730 |
| Pace | `<= 55` | faute_simple | 93.0% | 16.8% | 1758 |
| Pace | `<= 60` | faute_simple | 93.0% | 37.6% | 3281 |
| Pace | `<= 65` | faute_simple | 93.0% | 60.8% | 4882 |
| Pace | `>= 75` | defense | 93.0% | 13.9% | 932 |
| Pace | `>= 78` | remplacement | 93.0% | 5.0% | 337 |
| Pace | `>= 82` | defense, tir_non_cadre | 93.0% | 1.6% | 110 |
| Pace | `>= 85` | defense, tir_non_cadre | 93.0% | 1.6% | 109 |
| Pace | `>= 86` | defense | 93.0% | 0.4% | 24 |
| Pace | `>= 88` | defense | 93.0% | 0.4% | 24 |
| Pace | `>= 90` | defense, remplacement, tir_non_cadre | 93.0% | 0.4% | 24 |
| Stamina | `>= 75` | remplacement | 93.0% | 14.7% | 1005 |
| Stamina | `>= 85` | remplacement | 93.0% | 1.7% | 112 |
| Strength | `>= 70` | faute_simple | 93.0% | 21.2% | 1575 |
| Strength | `>= 75` | corner, defense, faute_simple | 93.0% | 11.6% | 845 |
| Strength | `>= 80` | defense | 93.0% | 5.0% | 365 |
| Strength | `>= 85` | corner, defense | 93.0% | 1.6% | 111 |
| Strength | `>= 88` | defense | 93.0% | 0.5% | 39 |
| Tackling | `<= 50` | faute_simple | 81.9% | 42.3% | 2826 |
| Tackling | `<= 55` | faute_simple | 81.9% | 50.2% | 3350 |
| Tackling | `<= 58` | faute_simple | 81.9% | 50.2% | 3350 |
| Tackling | `<= 60` | faute_simple | 81.9% | 62.4% | 4167 |
| Tackling | `<= 62` | faute_simple | 81.9% | 62.4% | 4167 |
| Tackling | `<= 65` | faute_simple | 81.9% | 75.6% | 5046 |
| Tackling | `>= 70` | carton_jaune | 81.9% | 17.2% | 1147 |
| Tackling | `>= 75` | carton_jaune, defense | 81.9% | 7.4% | 492 |
| Tackling | `>= 78` | defense | 81.9% | 2.6% | 172 |
| Tackling | `>= 80` | defense | 81.9% | 2.6% | 172 |
| Tackling | `>= 82` | defense | 81.9% | 0.6% | 40 |
| Tackling | `>= 85` | defense | 81.9% | 0.6% | 40 |
| Tackling | `>= 88` | defense | 81.9% | 0.1% | 8 |
| Tackling | `>= 90` | defense | 81.9% | 0.1% | 8 |
| Technique | `<= 55` | tir_non_cadre | 93.0% | 27.4% | 2575 |
| Technique | `<= 60` | faute_simple | 93.0% | 47.7% | 3989 |
| Technique | `>= 70` | corner, defense, faute_simple | 93.0% | 25.7% | 1732 |
| Technique | `>= 72` | corner, defense, tir_non_cadre | 93.0% | 11.8% | 793 |
| Technique | `>= 75` | corner, tir_non_cadre | 93.0% | 11.8% | 793 |
| Technique | `>= 76` | corner | 93.0% | 4.9% | 328 |
| Technique | `>= 78` | corner, remplacement, tir_non_cadre | 93.0% | 4.9% | 328 |
| Technique | `>= 80` | corner | 93.0% | 4.9% | 327 |
| Technique | `>= 85` | corner, defense | 93.0% | 1.6% | 107 |
| Technique | `>= 88` | corner | 93.0% | 0.4% | 26 |
| Technique | `>= 90` | tir_non_cadre | 93.0% | 0.4% | 26 |
| Vision | `<= 58` | faute_simple | 93.0% | 47.3% | 3889 |
| Vision | `<= 60` | faute_simple | 93.0% | 66.3% | 5226 |
| Vision | `<= 65` | faute_simple | 93.0% | 79.6% | 6140 |
| Vision | `>= 75` | defense, faute_simple | 93.0% | 5.3% | 360 |
| Vision | `>= 78` | corner, defense | 93.0% | 2.1% | 138 |
| Vision | `>= 80` | corner, defense, faute_simple, tir_non_cadre | 93.0% | 2.1% | 138 |
| Vision | `>= 82` | corner, defense, faute_simple | 93.0% | 0.7% | 46 |
| Vision | `>= 85` | defense, tir_non_cadre | 93.0% | 0.7% | 46 |
| Work Rate | `>= 80` | remplacement | 93.0% | 11.0% | 749 |
| age | `<= 18` | carton_jaune, remplacement | 100.0% | 3.4% | 250 |
| age | `<= 21` | remplacement | 100.0% | 22.3% | 1619 |
| age | `>= 32` | faute_simple | 100.0% | 9.3% | 834 |
| age | `>= 33` | defense, remplacement | 100.0% | 6.4% | 596 |
| age | `>= 34` | carton_jaune, remplacement | 100.0% | 4.0% | 395 |
| fm_rating | `>= 75` | remplacement | 100.0% | 22.1% | 1609 |
| fm_rating | `>= 80` | remplacement | 100.0% | 5.1% | 384 |
| height_cm | `<= 172` | corner | 93.4% | 7.6% | 510 |
| height_cm | `>= 185` | corner | 93.4% | 34.7% | 3089 |
| height_cm | `>= 188` | corner | 93.4% | 19.7% | 1935 |
| height_cm | `>= 190` | corner | 93.4% | 12.3% | 1288 |
| preferred_moves | `contient Dives Into Tackles` | carton_jaune | 9.3% | 1.6% | 105 |
| preferred_moves | `contient Shoots With Power` | tir_non_cadre | 9.3% | 0.5% | 35 |
| preferred_moves | `contient Winds Up Opponents` | carton_jaune | 9.3% | 0.4% | 29 |

## Constat sur les pilotes déjà validés (01/10/2026, à décider — non modifiés)

Mesure phrase par phrase avec `scripts/audit_conditions_pilote.py` :

- **FAUTE_SIMPLE : 12 phrases sur 26 entre 50 et 76 %, aucune à 80 %+, 2 au-dessus de 70 %** (règle universelle du 01/10/2026 : alerte à 3 phrases > 70 % ; ce pilote ne la déclenche pas, voir SPEC_ANTI_REPEAT.md) — #1, 2, 3, 4, 5, 7, 9,
  11, 12, 13, 15, 16 (ex. `Tackling <= 65` : 75,6 % ; `Vision <= 60` : 66 % ;
  `Aggression >= 55` : 67 %). Même défaut que Finishing sur TIR_NON_CADRÉ ; le
  seuil de « plus de 3 » est dépassé.
- **DÉFENSE : 3 SURNOM fantômes** — #24 `Tackling >= 90` (8 joueurs), #25
  `Pace >= 90` + `Tackling >= 75` (1), #27 `Heading >= 88` + `Strength >= 85` (7) ;
  4 DEFAUT de niche (< 20 joueurs : #10, #12, #13, #17).
- **CORNER : 2 SURNOM fantômes** — « dominateur » #22 (`Heading >= 88` +
  `height_cm >= 190` : 9 joueurs) et « lutin » #23 (`height_cm <= 172` +
  `Heading >= 75` : **3 joueurs** — le correctif `height_cm` ne l'a pas rendu
  jouable).
- TIR_NON_CADRÉ, REMPLACEMENT, CARTON_JAUNE : 0 dominante, 0 SURNOM fantôme.
