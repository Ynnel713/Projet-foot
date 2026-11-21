# 30a: Options offensives évidentes ignorées par le porteur : diagnostic

**Chantier :** `v2-realisme` (constat du propriétaire du 21/11/2026, à l'écran : « on insiste là où c'est verrouillé alors qu'un ailier est démarqué et seul, on privilégie une passe en retrait plutôt qu'un choix offensif évident »). **Priorité :** P1. **Catégorie :** mesure.

**Constat vérifié (21/11/2026, lecture du code) :** le porteur n'évalue que les coéquipiers qu'il « envisage » (`decision.visible_teammates`) :
- portée de Vision (`_VISION_RANGE_M`, `decision.vision_range_m`) : 15,5 m à Vision 40, 24,4 m à 55, 30 m à 62 (médiane), 38,5 m à 70, 45,6 m à 80 ; au-delà, un coéquipier n'est pas candidat, quel que soit son isolement (seul le plus proche est toujours vu, souvent derrière le ballon), **sauf** en zone de construction (`bloc.builds_up`), où la relance longue en l'air du `v2-collectif/15a` envisage les postes hauts (`LONG_BALL_POSTES`, AG et AD compris) au-delà de `possession.LONG_PASS_M`, même hors de portée de Vision (`decision.py:137-146`, `:410-414`) ;
- passe qui fait gagner au moins 15 m vers le but (`_KEY_PASS_GAIN_M`) : envisagée seulement avec la chance `key_pass_spot_probability`, 0,39 à Vision 55, 0,50 à 62, 0,81 à 80, tirée à chaque décision ;
- s'y ajoutent le champ de vision et la mémoire de perception (`08a`, `08b`, `08d`).
La valeur d'une passe est le danger de la case du receveur (grille xT, `danger.danger`) plus la meilleure suite (`_pass_option`) ; l'espace libre devant un receveur isolé n'entre que par la pression qu'il subit (`keep`). Le « meilleur choix factuel » du `v2-collectif/33` est calculé avec cette même valeur, sur les seules options envisagées : il ne peut pas voir ce défaut.

**What to build:**
1. Définition d'une **option offensive évidente**, mesurée sur le monde réel du pas (pas sur la perception) : coéquipier de champ « libre » au sens existant du bloc (`bloc.FREE_M`, 9 m, lu par l'API publique de `bloc` : une seule définition de « libre » dans le moteur), plus près du but adverse que le porteur ou dans un couloir extérieur (`09a`), ligne de passe au sol ouverte (`pass_success_probability` au-dessus du seuil `OPEN_LANE_PROBABILITY` existant), hors-jeu exclu.
2. À chaque décision du porteur où une telle option existe et n'est pas jouée, sa cause : hors portée de Vision ; relance longue en l'air envisagée (zone de construction, 15a) mais moins bien notée ; passe clé non repérée au tirage ; hors du champ de vision ou oubliée (08) ; envisagée mais moins bien notée (écart de valeur rapporté) ; choix perturbé par l'erreur de Decisions.
3. Ce qui est joué à la place : passe en retrait, passe latérale, conduite dans la zone fermée, tir ; et ce qu'il en advient (perte dans les 5 s).
4. Saturation de la zone visée par le choix joué : distribution du nombre d'adversaires perçus à moins de R m du point visé (R de 6 à 15 m), pour les actions perdues dans les 5 s et les autres ; elle fonde la constante de saturation du 30b, partagée avec le seuil de saturation du `v2-collectif/15d`.
5. **Signature de Vision** (demande du propriétaire du 21/11/2026 : « on doit sentir une réelle différence dans les choix entre un joueur créatif qui a une bonne vision (15+) et un autre qui a une vision médiocre ») : par tranche de Vision du porteur (notes du moteur sur 99 ; 15/20 ≈ 75, 8/20 ≈ 40 ; tranches ≤ 45, 46 à 64, ≥ 65 ; en match normal, chaque tranche est aussi découpée par poste et par zone du ballon, Vision étant corrélée au rôle : c'est le banc de profils qui isole l'effet de Vision), par décision de passe : part des passes de plus de 30 m, des passes progressives (au moins 10 m gagnés vers le but), des changements de côté (receveur de l'autre côté de l'axe, plus de 25 m en largeur), des passes entre les lignes (receveur entre milieux et défenseurs adverses, `09e`), et des options évidentes ignorées (point 2). Deux séries : match normal (notes réelles) et banc de profils `scripts/measure_v2.py --profil Vision --niveaux 75 40` (niveaux réalistes, pas 99 contre 11), les indicateurs ci-dessus ajoutés au relevé par équipe du banc (`profile_tally`). Croisement Vision × Flair rapporté à titre d'information (Flair ne règle aujourd'hui que l'idée de talonnade, `decision.backheel_idea_probability` ; le goût du risque est au `v2-attributs-contextes/05`, à faire).
6. Rapport par note de Vision et par zone, sur 50 matchs ; recommandation chiffrée pour le `30b`, dont l'écart cible entre Vision 75 et Vision 40 à soumettre au propriétaire (chiffre réel par note de Vision : non trouvé).

**Hors de ce ticket :** toute modification du jeu.

**Attributs :** aucun (mesure de Vision et Decisions, sans changer leur effet).

**Constantes à proposer avant le code :** aucune nouvelle pour « libre » (`bloc.FREE_M`, 9 m, existant) ; rayons de lecture de la saturation (mesure seulement). Chiffre réel : passes de plus de 30 m et changements de jeu par match, à sourcer (non trouvé à ce jour).

**Lien avec l'existant :** relit la monnaie commune et le meilleur choix factuel du `v2-collectif/33` (livré, non modifié) ; le joueur « créatif » combine Vision (voir) et Flair (oser, `v2-attributs-contextes/05`, à faire) : la signature mesurée ici est celle de Vision seule.

**Blocked by:** 08f (livré).

**Bloque :** 30b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (détection, causes, signature de Vision, rapport) | 1 h 10 |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications (50 matchs, banc de profils 75 / 40) | 35 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : moyenne. Estimation portée de 2 h à 2 h 30 le 21/11/2026 (signature de Vision ajoutée) ; au-delà de 2 h : découpage à examiner avant le code (diagnostic des options ignorées, puis signature de Vision). Hypothèses : les options envisagées et leurs valeurs sont lisibles au point de décision (`decision.choose_action`, `trace.decisions`) sans changer le jeu ; la détection relit les fonctions de passe existantes.
Temps machine, non compté : suite complète ; banc de 50 matchs ; banc de profils Vision 75 / 40.

## Acceptance criteria

- [ ] Définition validée par le propriétaire avant le code ; « libre » lu par `bloc.FREE_M`, sans seconde constante
- [ ] Scène en zone de construction : un ailier hors de portée de Vision envisagé en relance longue n'est pas classé « hors portée de Vision »
- [ ] Scène fixe : ailier seul à 35 m, porteur à Vision 55 : l'option est détectée « évidente » et la cause « hors portée de Vision » est rapportée
- [ ] Rapport sur 50 matchs : nombre d'options évidentes ignorées par match, part de chaque cause, choix joué à la place, pertes dans les 5 s, par note de Vision
- [ ] Découpage examiné avant le code
- [ ] Signature de Vision : par tranche de Vision, parts de passes de plus de 30 m, progressives, changements de côté, entre les lignes et options évidentes ignorées, en match normal et au banc de profils 75 / 40 (écarts avec intervalle) ; croisement Vision × Flair rapporté
- [ ] Recommandation pour le 30b, chiffrée (dont l'écart cible entre Vision 75 et 40), soumise au propriétaire
- [ ] Jeu inchangé : mêmes empreintes à graine fixée avant / après
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
