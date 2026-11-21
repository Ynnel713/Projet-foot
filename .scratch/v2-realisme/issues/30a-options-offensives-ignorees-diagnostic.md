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
5. Rapport par note de Vision et par zone, sur 50 matchs ; recommandation chiffrée pour le `30b`.

**Hors de ce ticket :** toute modification du jeu.

**Attributs :** aucun (mesure de Vision et Decisions, sans changer leur effet).

**Constantes à proposer avant le code :** aucune nouvelle pour « libre » (`bloc.FREE_M`, 9 m, existant) ; rayons de lecture de la saturation (mesure seulement). Chiffre réel : passes de plus de 30 m et changements de jeu par match, à sourcer (non trouvé à ce jour).

**Lien avec l'existant :** relit la monnaie commune et le meilleur choix factuel du `v2-collectif/33` (livré, non modifié).

**Blocked by:** 08f (livré).

**Bloque :** 30b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (détection, causes, rapport) | 50 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications (50 matchs) | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : les options envisagées et leurs valeurs sont lisibles au point de décision (`decision.choose_action`, `trace.decisions`) sans changer le jeu ; la détection relit les fonctions de passe existantes.
Temps machine, non compté : suite complète ; banc de 50 matchs.

## Acceptance criteria

- [ ] Définition validée par le propriétaire avant le code ; « libre » lu par `bloc.FREE_M`, sans seconde constante
- [ ] Scène en zone de construction : un ailier hors de portée de Vision envisagé en relance longue n'est pas classé « hors portée de Vision »
- [ ] Scène fixe : ailier seul à 35 m, porteur à Vision 55 : l'option est détectée « évidente » et la cause « hors portée de Vision » est rapportée
- [ ] Rapport sur 50 matchs : nombre d'options évidentes ignorées par match, part de chaque cause, choix joué à la place, pertes dans les 5 s, par note de Vision
- [ ] Recommandation pour le 30b, chiffrée, soumise au propriétaire
- [ ] Jeu inchangé : mêmes empreintes à graine fixée avant / après
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
