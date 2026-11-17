# 09e: Distances entre les lignes en possession

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (des lignes trop écartées coupent l'équipe en deux). **Catégorie :** placement.

**Constat vérifié :** les distances défense-milieu et milieu-attaque découlent de la mise à l'échelle de la forme de départ (`bloc.py`) ; mesurées 13,0 / 13,4 m sans ballon (ticket 05), aucune règle avec ballon.

**What to build:** Avec ballon, les écarts entre lignes restent dans des bornes validées (contrainte sur la mise à l'échelle par bande) ; les rôles de 02d gardent leurs décalages à l'intérieur.

**Attributs :** aucun

**Blocked by:** 02d (Place de référence avec ballon selon le rôle), 09j (hauteur de la dernière ligne avec ballon, ajouté le 16/11/2026).

**Bloque :** 09h.

**Constantes validées par le propriétaire le 16/11/2026 :**
- Lignes : défense = moyenne des défenseurs centraux (DC) ; milieu = moyenne des milieux axiaux (MDC, MC, MOC) ; attaque = moyenne des avant-centres (BU) ; définition du constat du 09j.
- Écart défense-milieu avec ballon : bornes **10 à 15 m** (cible 12 m, directive du 16/11/2026) ; hors bornes, ramené à **la borne la plus proche** (« Borne la plus proche (Recommandé) »).
- Écart milieu-attaque avec ballon : bornes **10 à 20 m** (« 10 à 20 m (Recommandé) »).
- La dernière ligne reste sur `H` (09j) ; les lignes de devant reculent ou avancent, les joueurs entre deux lignes sont étirés proportionnellement (décalages des rôles du 02d conservés) ; **le bloc avec ballon raccourcit** (« Le bloc raccourcit (Recommandé) »), il n'est plus remis à 42 m.
- Chiffres réels : avec ballon, SkillCorner « toutes positions » (`docs/INDICATEURS_V2.md`, tableau « Forme des équipes ») : défense-milieu **13,7 m** (Q1-Q3 11,1-16,6), milieu-attaque **14,3 m** (11,5-17,2), longueur 33,9 m (30,1-38,0) ; à la relance (build_up) défense-milieu 15,3 m. Sans ballon : 10,2 / 13,3 m (Forcher et al. 2023). Correction du 17/11/2026 (réserve A3 de l'expert) : la mention initiale « non trouvé » était inexacte, ce tableau existait déjà dans le dépôt.
- Forme de référence avant le ticket (18 clubs de Ligue 1, ballon au centre) : défense-milieu 17,6 m en médiane (6,0 à 22,0), milieu-attaque 21,7 m (12,9 à 36,0), longueur 42 m.

**Status:** livré (17/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : bornes à sourcer (repères existants : 10,2 / 13,3 m sans ballon, `docs/INDICATEURS_V2.md`).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** forme très étirée : écarts ramenés dans les bornes
- **Statistiques (séries de matchs) :** 50 matchs : écarts entre lignes avec ballon

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Écarts avec ballon dans les bornes validées (50 matchs)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (16/11/2026)

- `v2engine/bloc.py` : `GAP_DEF_MID_M` (10, 15), `GAP_MID_ATT_M` (10, 20), postes des lignes `_LINE_POSTES` ; `line_gap_knots` (une fois par équipe, dans `Bloc.from_players` : niveau de chaque ligne dans la forme avec ballon mise à l'échelle, et niveau corrigé, borne la plus proche) ; `remap_depth` : un joueur d'une ligne suit sa ligne d'un bloc (la moyenne de la ligne tombe sur la borne) ; les autres (latéraux, ailiers) sont interpolés entre deux lignes, inchangés derrière la dernière, décalés comme la ligne la plus haute au-delà. `Bloc.reference` applique la correction avec ballon seulement, après le calage sur `H` (09j) : la dernière ligne ne bouge pas. Sans ballon : inchangé.
- Une première version interpolait tous les joueurs entre les lignes : un MDC et un MOC de part et d'autre du niveau du milieu ne suivaient pas la même échelle et la moyenne de la ligne sortait des bornes (jusqu'à 16,8 m) ; corrigé avant les tests.
- Tests : 4 ajoutés (`tests/test_v2engine_bloc.py` : forme étirée ramenée à la borne haute, forme compacte ouverte à la borne basse et écart dans les bornes inchangé, latéraux entre deux lignes et symétrie de l'équipe à l'extérieur, équipe sans avant-centre) ; 2 adaptés :
  - `test_the_shape_follows_the_situation` : avec ballon, la longueur n'est plus 42 m mais 42 m moins le resserrement (décision « Le bloc raccourcit ») ;
  - `tests/test_v2engine_issues_tir.py::test_in_a_match_every_framed_shot_was_judged_by_the_keeper` (garde du 05h) : la graine 20260923 ne donne plus de tir cadré en 30 min ; le test essaie les graines suivantes (au plus 4) jusqu'à en trouver, l'assertion reste la même (tout tir cadré jugé par le gardien).

**Mesures :**
- Forme de référence avec ballon, 18 clubs de Ligue 1, domicile et extérieur, ballon à 30, 52,5 et 80 m : défense-milieu 10,0 à 15,0 m (médiane 15,0 ; avant 6,0 à 22,0, médiane 17,6), milieu-attaque 12,9 à 20,0 m (médiane 20,0 ; avant 12,9 à 36,0), longueur 30 à 41 m (médiane 35 ; avant 42), dernière ligne exactement sur `H`.
- Banc, 50 matchs (`scripts.bench_series 50`, indicateur « distance … avec ballon », lignes regroupées sur tous les joueurs de champ) : défense-milieu **14,63 m** [14,43 ; 14,82], milieu-attaque **14,79 m** [14,59 ; 14,99], dans les bornes ; sans ballon 14,02 / 14,27 m. Avant (état du 09j, 20 matchs) : 15,69 / 15,99 m avec ballon.
- Lignes par poste, 1re période des deux matchs du constat (centraux, milieux axiaux) : défense-milieu avec ballon 13,0 / 12,2 / 12,7 / 14,6 / 15,6 / 15,7 m selon la tranche du ballon (10-25 à 85-105 m), contre 13,4 / 14,2 / 14,4 / 16,5 / 18,2 / 18,5 m avant ; le léger dépassement des tranches hautes est dynamique (tolérance de Teamwork : un joueur ne repart vers sa place qu'au-delà de 2 à 9 m).
- Volumes, 20 matchs appariés (09j contre 09e, mêmes graines) : buts 6,8 → **4,85** par match (− 29 %), xG neutre 6,45 → 4,67, tirs par équipe 22,2 → 20,05 (− 10 %), tirs de près 7,25 → 4,45, hors-jeu 4,1 → 4,1, tirs après récupération dans le camp adverse 12,75 → 11,9, passes 1 280 → 1 269, pertes 259 → 257. Écarts de plus de 10 % signalés au propriétaire (rapport de clôture) ; ils vont vers le réel et réduisent l'écart que traite le 18l.
- Déterminisme : deux exécutions à graine fixée (30 min de jeu) : mêmes empreintes (événements `941f75db44414634`, ticks `ddba6a6caa9e418d`).

**Durée :** estimée 1 h 45 ; réelle environ 1 h 15 de travail effectif (analyse 20, développement 20, tests 15, intégration et vérifications 20), à l'horloge de la session, non chronométrée ; écart − 29 %. Temps machine hors total : séries de 50 matchs (une série « avant » perdue faute de mémoire, puis les deux perdues au redémarrage du processus de travail ; relancée seule, environ 35 min), suites complètes (deux), mesures de forme et de lignes.

## Comments

- 16/11/2026 : **directive du propriétaire** (audit des centraux trop bas avec ballon, ticket 09j) : écart défense-milieu avec ballon tenu entre **10 et 15 m, cible 12 m**. Bornes validées par le propriétaire le 16/11/2026 (« je valide ») ; écart milieu-attaque toujours à proposer. Mesuré le 16/11/2026 (deux 1res périodes, graines 20260923 et 20260924) : défense-milieu 15 à 19 m avec ballon, au-dessus de la borne haute. À traiter après 09j : la contrainte s'applique au bloc remonté (09j ajouté au `Blocked by`).
- **16/11/2026, passage 1** — Expert : `APPROVED_WITH_RESERVATIONS`. QC : `VALIDÉ`. Réserves : A1 (écart défense-milieu par poste, mesuré sur 2 mi-temps, au-dessus de 15 m de 0,6 à 0,7 m quand le ballon est entre 70 et 105 m ; dynamique, tolérance de Teamwork ; banc de 50 matchs dans les bornes) ; A2 (buts − 29 %, 6,8 → 4,85 par match ; xG neutre − 28 % ; tirs de près − 39 %) ; A3 (« chiffres réels non trouvés » inexact : repère SkillCorner avec ballon dans `docs/INDICATEURS_V2.md`) ; A4 facultatif (annotation de `gap_knots`) ; A5 facultatif (garde du 05h sur 4 graines au plus). **Décision du propriétaire (16/11/2026) : « Accepter A1 et A2, corriger A3 (Recommandé) ».**
- **17/11/2026, passage 2** — A3 et A4 corrigés (commentaire de `bloc.py`, annotation, ce ticket ; aucune logique modifiée). Expert : `APPROVED_WITH_RESERVATIONS` (A3 et A4 levées ; A1 et A2 maintenues, déjà acceptées par le propriétaire). QC : `VALIDÉ`. Clôture journalisée : `VALIDÉ`. À surveiller (expert) : longueur médiane avec ballon 35 m contre 33,9 m réels, au 27c.
