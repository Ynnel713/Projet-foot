# 30b: Voir et valoriser le joueur libre

**Chantier :** `v2-realisme` (constat du propriétaire du 21/11/2026, voir `30a`). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié :** voir `30a` (portée de Vision de 24,4 m à Vision 55, passe qui gagne 15 m envisagée 39 % du temps ; valeur d'une passe sans l'espace libre devant le receveur). Le chiffrage des causes vient du 30a.

**What to build (selon le diagnostic du 30a) :**
1. Portée et repérage : un coéquipier libre (définition du 30a) au-delà de la portée actuelle est envisagé avec une chance qui croît avec Vision, au lieu d'être exclu ; un pro moyen voit le côté opposé (portée et repérage recalés sur un chiffre réel de passes longues).
2. Valeur de l'espace : la valeur d'une passe vers un receveur libre ajoute l'espace qu'il peut attaquer (point libre devant lui, comme `decision.free_point` pour la conduite), pour que l'ailier seul vaille plus que le même ailier marqué, au-delà de la seule pression.
3. Zone fermée : la conduite ou la passe courte vers une zone saturée voit sa chance de perte relue, sans nouvelle pénalité arbitraire. La saturation (rayon et nombre d'adversaires perçus autour du point visé) est chiffrée par le 30a, proposée comme constante et partagée avec le `v2-collectif/15d` (une seule définition).

**Attributs :** Vision (rayon existant : voir et repérer la passe ; pas de double comptage avec Decisions, qui choisit), Decisions (inchangé). À vérifier dans `docs/CARTE_ATTRIBUTS_V2.md` (ADR 0002).

**Constantes à proposer avant le code :** nouvelle portée de Vision (`_VISION_RANGE_M`), chance de repérer un joueur libre hors portée, poids de l'espace devant le receveur, saturation d'une zone (rayon, nombre d'adversaires ; issue du 30a, partagée avec le 15d). Chiffres réels : passes de plus de 30 m par match et part des passes progressives (à sourcer, non trouvés à ce jour).

**Blocked by:** 30a ; à coordonner avec `v2-collectif/22a` (passes par match déjà au-dessus du repère : 1 091 contre 890 à 940).

**Bloque :** `v2-collectif/15d` (le renversement suppose de voir le côté opposé) ; `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés, profils Vision) | 35 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible (dépend du diagnostic du 30a ; découpage à examiner avant le code : portée et repérage, puis valeur de l'espace). Hypothèses : changements limités à `decision.visible_teammates` et `decision._pass_option` ; le banc de profils (`--profil Vision`) reste valable.
Temps machine, non compté : suite complète ; série appariée de 50 matchs ; profils Vision 99 contre 11 et 75 contre 40.

## Acceptance criteria

- [ ] Constantes et chiffres réels validés par le propriétaire avant le code ; découpage examiné
- [ ] Scène : ailier seul à 35 m, ligne ouverte, zone du ballon saturée : le porteur à Vision 70 le joue nettement plus souvent qu'aujourd'hui ; Vision 30 moins souvent que Vision 70
- [ ] Options évidentes ignorées par match (indicateur du 30a) : baisse chiffrée, cible fixée sur le rapport du 30a
- [ ] Signature de Vision (30a, banc de profils 75 / 40) : l'écart entre Vision 75 et Vision 40 sur les passes de plus de 30 m, les passes progressives et les changements de côté atteint la cible validée par le propriétaire ; à Vision 40, le joueur joue simple sans choix absurde (passes perdues et pertes dans les 5 s pas plus élevées qu'avant)
- [ ] Passes de plus de 30 m et passes en retrait par match rapportées, dans le repère réel retenu
- [ ] Pas de régression mesurée (50 matchs appariés) : passes réussies, pertes, buts, tirs avec intervalle ; profil Vision toujours dans le bon sens
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
