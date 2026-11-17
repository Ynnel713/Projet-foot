# 15b1: Chercher le troisième homme en construction (contexte « lecture du pressing »)

**Découpé du ticket 15b le 17/11/2026** (décision du propriétaire : « je valide »). **Chantier :** `v2-collectif`. **Priorité :** P1. **Catégorie :** décision.

**Constat avant le code (17/11/2026, 12 matchs de 90 min, script hors dépôt `constat.py`) :** le troisième homme existe déjà par la suite du receveur (ticket 13), le plan de passe (14) et le jeu de première (31a), sans être cherché. Par match : 93,3 passes de construction (gardien ou défenseur dans ses 35 m), dont 6,2 relances longues ; 31,1 % des passes courtes cassent directement la première ligne ; **troisième homme** (A → B → C, B devant la première ligne, C derrière, B rejoue en moins de 4 s, C contrôle) **8,3 par match, 9,6 % des passes courtes**, B en une touche dans 39 % des cas ; pertes dans son propre tiers 12,3 par match (4,9 % des changements de possession). Première ligne : le plus reculé des 3 adversaires de champ les plus avancés (approximation de mesure).

**What to build:** en construction (`bloc.builds_up`) sous pressing, le porteur lit la structure du pressing : il repère un coéquipier C libre derrière la première ligne, accessible par la remise d'un B situé devant. Cette lecture passe par un nouveau contexte du registre, « lecture du pressing » (perception) ; quand il la fait (tirage, flux décision), la suite du receveur vers ce C (`_pass_option`, valeur future du ticket 13) est majorée. Le plan de passe (14) transmet ensuite C à B, qui l'adopte selon son Teamwork (inchangé, pas de nouvelle lecture).

**Hors de ce ticket :** attirer le pressing (15b2) ; court ou long (15a) ; nouveau mécanisme de passe.

**Attributs (ADR 0002) :** contexte « lecture du pressing », perception, Vision 0,5 + Anticipation 0,3 + Decisions 0,2 (proposés, à valider), effet `decision.reads_third_man_probability`. Vision garde la portée des passes envisagées (`visible_teammates`, autre effet) ; Decisions garde l'erreur de perception de toutes les options (`perception_error`, autre effet) ; Teamwork reste dans l'adoption du plan (14), non relu ; Passing dans l'exécution. Un effet, un calcul.

**Blocked by:** `v2-attributs-contextes/02` et `02b` (livrés).

**Status:** livré (17/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min (constat déjà fait) |
| Développement | 40 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : la suite du receveur (13) et le plan (14) portent le troisième homme, il suffit de majorer la suite lue ; un seul calage après la première série.
Temps machine, non compté : séries de 50 matchs avant et après ; suite complète.

## Acceptance criteria

- [x] Constantes produit validées par le propriétaire avant le code (chiffres réels sourcés ou « non trouvé »)
- [x] Contexte « lecture du pressing » dans le registre et dans la section « Contextes » de la carte ; Vision, Anticipation et Decisions mis à jour dans la liste de transition (garde de rayon verte)
- [x] Scène : sous pressing, avec un C libre derrière la première ligne et un B devant, le porteur à lecture 99 sert B plus souvent qu'à 11 ; sans pressing ou hors construction, aucun changement
- [x] Statistiques (50 matchs, avant et après) : part de troisièmes hommes dans les passes courtes de construction, pertes dans son propre tiers, buts et tirs (calibration)
- [x] Effet probabiliste, jamais binaire ; plafond d'écart 99 / 11 (`scripts/measure_v2.py --profil`)
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs (ticket 22)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md` ; durée réelle relevée

## Sources

- Repère réel du troisième homme en construction : **non trouvé**. Plus proches : Footballytics (Bundesliga 2023-24), attaques par troisième homme réussies et finies dans le dernier tiers, 1 à 2 par match pour les meilleures équipes, définition étroite (hors milieu et construction) : https://www.footballytics.ch/post/tactics-and-data-outplay-opponents-with-pass-combinations ; passes qui cassent une ligne, environ 117 par match sur 64 matchs (arXiv 2506.06666) : https://arxiv.org/html/2506.06666v1

## Constantes validées (17/11/2026, propriétaire : « je valide »)

| # | Constante | Valeur | Source |
|---|---|---|---|
| 1 | Contexte « lecture du pressing » (perception), `contextes.LECTURE_DU_PRESSING`, effet `decision.reads_third_man_probability` | Vision 0,5 ; Anticipation 0,3 ; Decisions 0,2 | non trouvé |
| 2 | Chance de lire le troisième homme par décision (`decision._READS_THIRD_MAN`), interpolée | 11 → 15 % ; 55 → 45 % ; 99 → 80 % | non trouvé, choix de modèle |
| 3 | Sous pressing (`bloc.build_up_pressed`) | construction et au moins `BUILD_UP_PRESS_COUNT[0]` = 2 adversaires de champ dans ses 35 m (constante du 25b, réutilisée) | constante existante |
| 4 | Première ligne (`decision.FIRST_LINE_RANK`) | 3ᵉ adversaire de champ le plus proche de son but ; B devant ou sur elle, C derrière | approximation du constat |
| 5 | Majoration de la suite vers C (`decision.THIRD_MAN_BONUS`) | × (1 + 0,5) | non trouvé, choix de modèle |

## Réalisation (17/11/2026)

- **Code** : contexte `LECTURE_DU_PRESSING` dans `v2engine/contextes.py` ; `bloc.build_up_rivals` (compte partagé avec le placement du 25b, calcul identique) et `bloc.build_up_pressed` ; dans `decision.py`, `reads_third_man_probability`, `first_pressing_line`, paramètre `pressed` de `choose_action` et `evaluate_options` (un tirage du flux décision, seulement sous pressing et s'il y a une suite à valoriser), paramètre `third_man` de `_pass_option` (passes au sol seulement : une relance longue vise un joueur déjà derrière la ligne) ; `match.py` transmet `build_up_pressed(holder, players)` à la décision normale du porteur (pas à la décision de première, 31a).
- **Rayon** : Vision, Anticipation et Decisions entrent dans un premier contexte ; ils restent dans `TRANSITION` (second contexte : Decisions au `v2-attributs-contextes/04a`, Vision et Anticipation au `08`). Vision garde la portée des passes envisagées et le repérage d'une passe qui fait gagner plus de 15 m (`visible_teammates`) ; Decisions l'erreur de perception de toutes les options ; Teamwork l'adoption du plan (14) : effets distincts, aucun relu. Carte : ligne du contexte, cellules Vision, Anticipation, Decisions, paragraphe de la garde.
- **Tests** : `tests/test_v2engine_troisieme_homme.py` (6 tests) : courbe de lecture aux trois repères et pour un profil mixte ; première ligne (gardien exclu, miroir, moins de trois adversaires) ; condition de pressing (zone, bâtisseur) ; suite vers C majorée et passe vers B relevée de plus de 20 %, rien pour une suite sans ligne cassée ; aucun changement sans pressing ni quand B est déjà derrière la ligne ; scène 99 contre 11 sur 1 000 décisions (part des passes vers B, avec moins sans lecture : environ + 15 points à 99, quasi nul à 11). `tests/test_v2engine_contextes.py` : registre à trois contextes.
- **Déterminisme** : deux exécutions à graine fixée (deux matchs de 15 min) donnent les mêmes empreintes (20260923 : `99230fa76330b7b0` ; 20261107 : `69a6d0f67c3951e4`).
- **Série de 50 matchs, avant (HEAD `3199301`) → après** (script hors dépôt `constat.py`, mêmes graines 20261117 + i, mêmes affiches) :

| Indicateur | Avant | Après |
|---|---|---|
| Passes de construction par match | 91,6 | 90,3 |
| Relances longues par match | 5,9 | 5,0 |
| Troisièmes hommes par match | 7,9 | 8,8 |
| Troisième homme / passes courtes de construction | 9,2 % (erreur type 0,4) | 10,4 % (erreur type 0,5) |
| … dont B en une touche | 33,6 % | 38,7 % |
| Ligne cassée directement | 31,4 % | 30,6 % |
| Pertes dans son propre tiers par match | 12,0 | 11,2 |
| Buts par match (deux équipes) | 4,44 | 4,72 |
| Tirs par match (deux équipes) | 40,3 | 38,7 |
| Passes par match | 1 225 | 1 219 |

  Effet modeste et dans le sens attendu (+ 1,1 point de troisièmes hommes, environ 1,8 erreur type ; − 0,8 perte dans son tiers) ; buts et tirs dans le bruit d'une série de 50 matchs. Chiffres réels : indicateurs de calibration, pas objectifs (repère non trouvé). Pas de recalage de `THIRD_MAN_BONUS`.
- **Banc de profils** (`scripts/measure_v2.py 10 --profil Vision`, avant → après, écart haut − bas par match) : passes + 261,8 → + 245,0 (significatif les deux fois) ; pertes en conduite − 22,5 → − 20,4 ; interceptions − 21,1 → − 24,4 ; tirs − 12,7 → − 17,7 (intervalles qui se recouvrent) ; scans par minute 29,8 / 5,5 → 30,0 / 5,5. Aucun écart nouveau ni emballé : plafond d'écart 99 / 11 inchangé. Le contexte combine trois attributs, le banc n'en force qu'un (Vision, poids 0,5) : l'écart propre à la lecture est mesuré par la scène (99 contre 11).
- **Suite complète** (17/11/2026) : 3 381 passés, 0 ignoré, 14 désélectionnés (14 min 26) ; 3 374 + 7 (6 tests de la scène, 1 cas paramétré du registre) ; `CLAUDE.md` mis à jour.
- **Critères** : constantes validées avant le code ; contexte dans le registre et la carte, transition à jour, garde verte ; scène 99 contre 11 et absence d'effet hors pressing ; statistiques avant/après sur 50 matchs ; effet probabiliste, plafond d'écart vérifié ; repère réel non trouvé, indicateur seulement ; déterminisme vérifié ; suite passée.
- **Durée** : estimée 2 h ; réelle environ 1 h 45 de travail effectif (− 12 %) : constat déjà fait au 15b, scène de test reprise deux fois (C d'abord soumis au tirage de repérage de la Vision, qui mélangeait deux effets) ; une importation circulaire évitée en calculant la condition dans `bloc.py`. Durée estimée à l'horloge de la session hors attentes machine et réponses du propriétaire, non chronométrée. Temps machine hors total : deux séries de 50 matchs (34 et 33 min), deux bancs de profils de 10 matchs, deux paires d'empreintes, suite complète (14 min 26).

## Comments

- **17/11/2026, passage 1** : expert APPROVED ; QC VALIDÉ ; clôture journalisée VALIDÉ (empreinte `5c8ef3b23949…`). Aucune anomalie bloquante. Améliorations facultatives de l'expert : A1, la condition de pressing est calculée sur les vraies positions alors que la ligne l'est sur les adversaires perçus (effet négligeable) ; A2, `decision._from_own_goal` double `bloc._progress` (exposer une fonction publique unique) ; A3, première ligne au 3ᵉ adversaire même quand 2 seulement pressent (sous-estime l'effet). À surveiller : cumul avec le 15b2 ; niveau de buts par match (4,4, antérieur au ticket). QC : seuils du test de scène empiriques (graine fixe).
