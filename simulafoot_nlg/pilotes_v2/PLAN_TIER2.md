# Plan d'ouverture Tier 2 — 01/10/2026

**Écriture seulement.** Aucune intégration dans `engine/` (le sélecteur n'existe
pas). Aucune phrase Tier 2 écrite tant que REMPLACEMENT et CARTON_JAUNE ne sont
pas validés (Tier 1 clos). Fiches d'origine : `data/seed/PLAN_V2_EDITORIAL.md`.

## Ordre proposé et justification

| # | Scénario | Fréq./match | Complexité | Volume cible | Verrou avant d'écrire |
|---|---|---|---|---|---|
| 1 | AMBIANCE | 3-5 | Simple (×1) | **24** pilote (brief : 20-25 ; formule : plancher 20) | D1 FAIT — pilote écrit, en attente de validation |
| 2 | HORS-JEU | 3-4 | Moyenne (×1,3) | **24** (fiche : 20) | Aucun — `score_context` abandonné |
| 3 | BLESSURE | 1-2 | Simple (×1) | **20** | Après validation REMPLACEMENT (cohérence « sortie sur blessure ») |
| 4 | MI_TEMPS_FIN_MATCH | 2 (garanti) | Simple mais dépend d'un slot à concevoir (×1) | **25** (15 + 10) | `score_display` + valence du résultat (voir D2) |

Total ≈ 99 phrases ≈ 106 unités d'effort (30×1 + 24×1,3 + 20×1 + 25×1).

**Pourquoi cet ordre.** On ouvre par ce qui est écrivable sans décision
technique et qui expose le plus (AMBIANCE, fréquence maximale du tier), puis par
le seul scénario Tier 2 à conditions joueur (HORS-JEU) tant que la méthode
Tier 1 est fraîche. BLESSURE attend REMPLACEMENT. MI_TEMPS_FIN_MATCH est dernier
parce que c'est le seul bloqué par une conception technique, bien que garanti
2×/match : à fréquence égale de lecture, un texte écrit avant `score_display`
sera réécrit.

## Volumes : formule

Pool minimal = fréquence max × cooldown (matchs) × 2 (marge, un pool qui ne
couvre qu'une rotation exacte se répète à vue) :
AMBIANCE 5×2×2 = 20, HORS-JEU 4×3×2 = 24, BLESSURE 2×4×2 = 16,
MI_TEMPS/FIN_MATCH 1×4×2 = 8 par variante. HORS-JEU passe de 20 à 24 (juste
au plancher) ; AMBIANCE de 25 à 30 pour couvrir ses sous-thèmes (chants, tifo,
sifflets, incidents) sans répétition thématique.

## Adaptations de méthode (la méthode Tier 1 ne s'applique pas telle quelle)

- **Pas de SURNOM** pour AMBIANCE, BLESSURE (essentiellement), MI_TEMPS_FIN_MATCH :
  pas de joueur porteur d'un surnom. Axe d'audit de diversité à la place :
  sous-thèmes (AMBIANCE), sous-cas (BLESSURE : contact / sans contact / usure),
  variantes MI_TEMPS vs FIN_MATCH.
- **Audits conservés tels quels** : n-grammes (plafond 2, garde-fou permanent),
  structurel, chutes de phrase, lecture en séquence (seeds 42-45), tic
  « l'arbitre »-like (un mot > 30 % des phrases est signalé), jouabilité
  (`scripts/audit_conditions_pilote.py` : 0 dominante > 50 %, 0 SURNOM < 20).
- **Un fichier de tests par pilote**, comme Tier 1.

## Données vérifiées (7563 joueurs)

- HORS-JEU : `Pace >= 88` = 24 joueurs (borderline) → utiliser `Pace >= 85`
  (109) ; `Off the Ball >= 75` (484 ; 7,3 %) / `>= 80` (179) ;
  `Pace >= 85` + `Off the Ball >= 75` = 24. `Anticipation <= 50` (17 %) pour le
  côté « se fait prendre ».
- BLESSURE : `age >= 30` = 1425 (17 %) ; `Natural Fitness <= 40` = 328,
  `<= 45` = 467 ; `age >= 30` + `Natural Fitness <= 50` = 157. Pas de donnée
  « blessure/retour » (`players.status`).
- AMBIANCE, MI_TEMPS_FIN_MATCH : aucune condition joueur.

## Décisions actées (01/10/2026)

- **D1 — `is_home` exposé aux conditions (AMBIANCE).** FAIT : `is_home` ajouté à
  `MATCH_CONTEXT_FIELDS` (`engine/conditions.py`). La seule liste ne suffisait
  pas : `_comparer` comparait le bool `True` au texte `"true"` (toujours faux, échec
  silencieux) et `is_home=None` + `!=` matchait. Corrigé (littéraux
  `true/vrai/false/faux`, valeur inconnue ⇒ jamais de match) et testé ; les 5
  nouveaux tests échouent sans le correctif. AMBIANCE peut écrire
  `is_home == true` / `== false` et reste libre d'écrire des phrases neutres.
- **D2 — MI_TEMPS_FIN_MATCH : option C.** Le sélecteur décidera mi-temps vs fin
  de match et la valence du résultat ; les phrases ne conditionnent que sur
  `minute` (45, 90). `score_display` n'existe pas : dette V2.1 (SPEC_ANTI_REPEAT.md,
  section 5). Risque assumé : sans `score_display`, un texte ne peut pas
  afficher le score ; seuls les textes sans score chiffré s'écrivent avant V2.1.
- **D3 — HORS-JEU : second axe joueur.** `minute >= 80` seule est retirée comme
  critère unique. Mesures (7563 joueurs ; « attaquants » = BU/AG/AD/SA, 2192) :

| Axe | Condition | Joueurs | % champ | % attaquants | Sous-texte |
|---|---|---|---|---|---|
| Anticipation de la ligne | `Off the Ball >= 75` | 484 | 7,3 % | 13,2 % | appel dans le dos, mal calé |
| Anticipation de la ligne | `Off the Ball >= 80` | 179 | 2,7 % | 4,7 % | idem, niche |
| Vitesse | `Pace >= 85` | 109 | 1,6 % | 3,5 % | parti trop tôt à pleine vitesse |
| Vitesse | `Pace >= 80` | 337 | 5,0 % | 9,4 % | idem, plus large |
| Joueur piégé | `Concentration <= 45` | 1385 | 18,3 % | 28,0 % | se laisse piéger par la ligne |
| Joueur piégé | `Anticipation <= 50` | 1375 | 16,9 % | 23,2 % | idem |
| Statut | `fm_rating >= 75` | 1609 | 22,1 % | 23,7 % | star surveillée par la défense |
| Contexte | `minute >= 80` | — | — | — | prise de risque en fin de match |

  Recommandation de répartition pour 24 phrases : ~7 sans condition, ~4 sur
  `Off the Ball >= 75` ou `Pace >= 80`, ~4 sur `Concentration <= 45` /
  `Anticipation <= 50`, ~3 sur `fm_rating >= 75`, ~3 sur `minute >= 80` (jamais
  seule dimension d'une famille), ~3 croisées (axe joueur ET `minute`). Aucune
  condition > 50 % ; `Pace >= 88` (24 joueurs) abandonnée.
  **`Position` EXPOSÉE (option A, FAIT le 01/10/2026)** : `position` ajouté à
  `PLAYER_FIELDS` après vérification de la couverture (7563/7563 = 100 %, bien
  au-dessus du seuil de 90 %). `position in [BU, AG, AD]` et `position == "BU"`
  sont utilisables ; valeurs : BU 936, AG 652, AD 572, SA 32 (attaquants 2192),
  MOC 498, MC 906, MDC 599, DC 1371, RB 576, LB 533, GK 888. Seul le poste
  principal est exposé (pas `secondary_positions`). Bénéficie aussi à DÉFENSE,
  CORNER, MI_TEMPS_FIN_MATCH. Option D (fallback décrit par l'architecte :
  fusion Off the Ball / off côté) conservée en dette, non retenue.
- **`fm_rating` exposé (FAIT, 01/10/2026)** : n'était pas dans `PLAYER_FIELDS`,
  donc `_resolve` levait `ValueError` sur REMPLACEMENT (phrase 6, joker) et sur
  toute condition `fm_rating`. Ajouté + test ; un garde-fou permanent
  (`test_pilotes_v2_garde_fous.py`) vérifie désormais que tout attribut
  conditionné par un pilote est résolvable.
