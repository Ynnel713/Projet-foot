# Conditions trop larges -- échantillon 14 matchs (ticket banque, 02/10/2026)

Mesure : `simulafoot_nlg/scripts/audit_conditions_larges.py` (part des événements d'un scénario pour lesquels toutes les conditions
de la phrase sont satisfaites, joueur et contexte). Seuil : > 30 %. **16 phrases au-dessus de 30 % avant, 3 après.**

## Restent au-dessus de 30 % (3, tolérées)

| Scénario | phrase_id | Part | Événements | Condition | Pourquoi on la laisse |
|---|---|---|---|---|---|
| ARRET_GARDIEN | 148 | 46 % | 32/69 | `score_context == "ouverture_score"` | Condition de **contexte** légitime : le premier but arrive à 0-0, donc pour beaucoup d'événements. Rien à resserrer sur le joueur. |
| BUT | 55 | 39 % | 14/36 | `score_context == "ouverture_score"` | Idem (« ouvre le score »). |
| REMPLACEMENT | 455 | 32 % | 36/114 | `minute <= 55` | « Changement précoce » : resserrer à `<= 50` (16 %) reporte ses tirages sur les 6 modèles sans condition, « Changement chez {club} » monte à 13 usages sur 114, au-dessus du plafond de 12 (poids du tirage verrouillés). Condition de contexte (minute), pas de ciblage joueur. |

## Resserrées (13 phrases)

Sources : `pilotes_v2/*.py` (v2) puis YAML régénéré par `scripts.convert_pilotes_to_yaml` ; v1 (CARTON_ROUGE) : classeur
`data/seed_source/banque_de_phrases_simulafoot.xlsx` (CHECKSUM mis à jour) puis `cli.py convert-commentary`. Couverture « base » = part des
joueurs de champ qui satisfont les conditions joueur (>= 0,5 % exigé) ; « échantillon » = part des événements du scénario (>= 1 %, <= 30 %).

| Scénario | phrase | Avant | Après | Échantillon (avant -> après) | Base |
|---|---|---|---|---|---|
| REMPLACEMENT | 451 « carte de poids » | `fm_rating >= 75` | `fm_rating >= 81` | 68 % -> 24 % | 3,6 % |
| CARTON_JAUNE | 307 « tacle par derrière » | `Aggression >= 70` | `Aggression >= 70` & `Tackling <= 60` | 39 % -> 8 % | 12,7 % |
| CARTON_JAUNE | 309 « jaune tactique » | `minute >= 60` | `minute >= 60` & `Anticipation >= 70` | 44 % -> 22 % | 19,4 % |
| CARTON_JAUNE | 320 « le ton monte » | `Aggression >= 70` | `Aggression >= 70` & `Composure <= 65` | 39 % -> 21 % | 23,4 % (paire) |
| CARTON_JAUNE | 321 « retarde la reprise » | `minute >= 70` | `minute >= 70` & `age >= 30` | 39 % -> 4 % | 16,9 % |
| DEFENSE | 374 « s'interpose » | `Strength >= 75` | `Strength >= 80` | 41 % -> 21 % | 5,0 % |
| TIR_NON_CADRE | 476 « enclenche trop vite » | `Technique >= 75` | `Technique >= 82` | 45 % -> 18 % | 1,6 % |
| TIR_NON_CADRE | 487 « vingt mètres » | `Technique >= 72` | `Technique >= 72` & `Long Shots >= 70` | 45 % -> 18 % | 3,2 % |
| CARTON_ROUGE | 5 « retardement inutile » | `Aggression >= 70` | `Aggression >= 70` & `Tackling <= 55` | 57 % -> 29 % | 8,8 % |
| CARTON_ROUGE | 11 « contact anodin » | `Aggression >= 75` | `Aggression >= 75` & `Determination >= 80` | 57 % -> 14 % | 5,8 % |
| CARTON_ROUGE | 19 « tacle désespéré » | `Aggression >= 70` | `Aggression >= 70` & `minute >= 60` | 57 % -> 29 % | 28,1 % |
| CARTON_ROUGE | 22 « but litigieux » | `Aggression >= 75` | `Aggression >= 75` & `Teamwork >= 80` | 57 % -> 14 % | 4,1 % |
| CARTON_ROUGE | 30 « tac au tac » | `Aggression >= 75` | `Aggression >= 75` & `Decisions <= 60` | 57 % -> 14 % | 11,2 % |

Déjà traitée au ticket précédent : REMPLACEMENT 466 « Le joker » `fm_rating >= 80` -> `>= 82` (28 % -> 17 %).

## Limites à garder en tête

- **CARTON_ROUGE : 7 événements seulement** sur les 14 matchs. Les parts (14 % = 1 événement, 29 % = 2) sont du bruit statistique ; les
  secondaires choisis (tacleur faible, minute avancée, détermination, esprit d'équipe, décisions) sont football-cohérents et couvrent 4 à 28 %
  de la base, mais à revalider sur un échantillon plus large. `Aggression >= 80` seul aurait donné 0/7.
- **Près de la limite (29-30 %)** : REMPLACEMENT 448 (30 %, 34/114), TIR_NON_CADRE 471 et 483 (30 %, 13/44), CARTON_JAUNE 310 et 325 (29 %),
  ARRET_GARDIEN 151 (29 %). Non touchées (au plus 30 %, hors du périmètre des 16).
- `fm_rating >= 85` reste exclu : 1 % des entrants, 0,6 % des joueurs de champ.
- Le plafond « modèle le plus servi <= 12 » est un seuil statistique : REMPLACEMENT a 6 modèles sans condition qui reçoivent 9 à 13 usages
  selon la graine ; resserrer plus d'une condition de REMPLACEMENT le fait déborder.
