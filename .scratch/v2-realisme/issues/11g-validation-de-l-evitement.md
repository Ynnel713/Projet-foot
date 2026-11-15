# 11g: Validation de l'évitement entre coéquipiers en match

**Chantier :** `v2-realisme` (constat du ticket 11e, 15/11/2026). **Priorité :** P0 (suite du 11f, priorité absolue du propriétaire). **Catégorie :** validation.

**Constat vérifié :** voir 11f (337 contacts francs par match entre coéquipiers, 1 099 déséquilibres par match).

**What to build:** Série appariée de 50 matchs avant / après le 11f avec les indicateurs du 11e ; réglage des constantes du 11f si la cible n'est pas atteinte (nouvelle valeur proposée au propriétaire avant tout changement) ; vérifier que l'évitement ne casse ni le pressing à deux, ni les appels croisés, ni le soutien court (coéquipiers volontairement proches).

**Attributs :** aucun

**Blocked by:** 11f (Évitement entre coéquipiers).

**Bloque :** rien.

**Status:** à faire (diagnostic du 11f : contacts restants surtout entre coéquipiers qui visent la même place ou pressent le même adversaire ; pistes a, b, c à trancher par le propriétaire, voir 11f ; mesurer aussi les sorties du gardien, les réceptions réussies et les ballons libres récupérés (condition de l'expert, réserve A1 du 11f) ; réestimer au démarrage)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 20** |

Confiance : moyenne. Hypothèses : pas de réglage nécessaire ; un réglage ajoute environ 30 min et une série.
Temps machine, non compté : deux séries de 50 matchs (environ 35 min chacune sur 3 cœurs) ; suite complète.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs appariés : contacts francs entre coéquipiers, déséquilibres, rythme

## Acceptance criteria

- [ ] Contacts francs entre coéquipiers : de 337 à **30 par match au plus** (cible indicative à confirmer par le propriétaire avec les constantes du 11f)
- [ ] Déséquilibres (contacts perdus) en baisse d'au moins 300 par match
- [ ] Sans régression significative sur : buts, tirs, passes réussies, pressings déclenchés, appels, distance entre les lignes ; écarts de rythme (passes, temps de jeu effectif, km) rapportés et expliqués
- [ ] Contacts francs entre adversaires rapportés (attendu : peu changés)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
