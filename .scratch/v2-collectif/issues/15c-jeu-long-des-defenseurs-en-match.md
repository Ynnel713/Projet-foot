# 15c: Jeu long des défenseurs en match : après une récupération, et face à un pressing mesuré par les solutions couvertes

**Créé le 17/11/2026** à la clôture de `15a` (décision du propriétaire : « option A »). **Chantier :** `v2-collectif`. **Priorité :** P2. **Catégorie :** décision et mesure.

**Constat vérifié (17/11/2026, ticket 15a, séries hors dépôt `serie_15a_strat.py` et `diag_match.py`) :** quand une relance longue est envisagée, la part longue des passes d'un défenseur en match baisse avec le nombre d'adversaires dans ses 35 m (9,8 / 5,8 / 3,3 %, 50 matchs), alors qu'à situation égale (scène du 15a) elle monte de 0,9 à 45,5 %. Par mode (30 matchs) :
- construction normale (aucun mode de transition) : 9,6 / 7,1 / 8,3 %, stable ;
- contre-attaque après récupération : 12,5 / 5,4 / 3,1 % ;
- conservation après récupération : 0 / 1,7 / 0 % (le poids des pertes du ticket 11 écarte le jeu long).
Sous « pressing haut » (4 adversaires et plus), 81 % des décisions d'un défenseur sont des transitions après récupération, pas de la construction face à un pressing organisé.

**What to build:** à préciser avec le propriétaire avant le code :
1. une mesure du pressing par les solutions courtes réellement couvertes (et non par le nombre d'adversaires dans les 35 m), pour juger le critère du 15a en match ;
2. le jeu long en contre-attaque après une récupération dans son tiers (la valeur de la relance longue en mode contre-attaque, ticket 11) ;
3. si nécessaire, la place de la relance longue en mode conservation.

**Attributs (ADR 0002, 17/11/2026) :** réintroduire la Vision dans la relance longue, écartée au 15a (« schéma d'équipe connu ») : contexte « repérer la cible longue sous pression » (Vision, Decisions, poids à proposer) ; Passing reste l'exécution.

**Hors de ce ticket :** duel aérien à la retombée (`v2-realisme/15b`) ; attirer le pressing, troisième homme (`15b`).

**Blocked by:** 15a, `v2-attributs-contextes/01` et `02`.

**Status:** à faire (périmètre et constantes à valider par le propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 40 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible. Hypothèses : la mesure du pressing par les solutions couvertes réutilise `possession.pass_success_probability` ; aucun changement des transitions du ticket 11 hors de la valeur de la relance longue. Au-dessus du seuil de 2 h : découpage à examiner avant le code (mesure, puis décision).
Temps machine, non compté : séries de 50 matchs avant et après ; suite complète.

## Acceptance criteria

- [ ] Périmètre et constantes validés par le propriétaire avant le code
- [ ] Part longue des défenseurs plus forte sous pressing mesuré par les solutions couvertes, en match (50 matchs), au-delà de deux erreurs types
- [ ] Effet des attributs probabiliste ; rayon conforme à `docs/CARTE_ATTRIBUTS_V2.md`
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
